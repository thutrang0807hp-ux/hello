import json
import os
from pathlib import Path
import random
import subprocess
import unittest
from unittest.mock import patch

import services
from job_notification import customer_stars,render


class TelegramJobNotificationTests(unittest.TestCase):
    def job(self):
        return services.normalize_job({'id':'~notice','title':'Build <Dashboard> & CRM','url':'https://www.upwork.com/jobs/~notice','description':'Long details do not belong in the compact notification.','budget':'$500','skills':['Python'],'client':{'rating':4.9,'country':'United States','totalHires':25,'hireRate':80,'paymentVerified':True}})

    def test_compact_title_stars_and_safe_clickable_source_without_ai(self):
        job=self.job()
        with patch.dict(os.environ,{'FREELANCE_TELEGRAM_TOKEN':'test-only','FREELANCE_TELEGRAM_CHAT_ID':'fixture'}),patch('services.post_json',return_value={'ok':True}) as send,patch('services.ai_request',side_effect=AssertionError('AI must not run')):
            services.send_notification('telegram',job)
        payload=send.call_args.args[1]
        self.assertEqual(payload['parse_mode'],'HTML')
        self.assertIn('★★★★★',payload['text'])
        self.assertIn('Build &lt;Dashboard&gt; &amp; CRM',payload['text'])
        self.assertIn('Xem đầy đủ trên Upwork',payload['text'])
        self.assertIn(job['url'],payload['text'])
        self.assertNotIn(job['notes'],payload['text'])
        self.assertEqual(payload['text'].count('\n'),2)
        self.assertTrue(payload['link_preview_options']['is_disabled'])
        self.assertEqual(send.call_count,1)

    def test_missing_client_data_does_not_invent_stars(self):
        message=render({'name':'New job','url':'https://www.upwork.com/jobs/~x'})
        self.assertIn('Chưa đủ dữ liệu chấm sao',message)
        self.assertNotIn('★',message)

    def test_source_link_cannot_inject_markup_or_use_other_schemes(self):
        for url in ['javascript:alert(1)','https://evil.example/x','https://upwork.com@evil.example/x']:
            message=render(dict(self.job(),url=url))
            self.assertNotIn('<a ',message)
        message=render(dict(self.job(),url='https://www.upwork.com/jobs/~x?q="<&'))
        self.assertIn('&quot;&lt;&amp;',message)

    def test_long_unicode_title_stays_short_and_retains_full_source(self):
        job=dict(self.job(),name='😀'*1000,url='https://www.upwork.com/jobs/~x?query='+'a'*1500)
        message=render(job)
        self.assertLessEqual(len(message.encode('utf-16-le'))//2,4096)
        self.assertIn(job['url'],message)
        self.assertIn('…',message)

    def test_customer_stars_match_existing_javascript_rules(self):
        random.seed(17)
        cases=[{}, {'rating':5,'paymentVerified':True},{'totalHires':0,'paymentVerified':False}]
        for _ in range(60):
            cases.append({'rating':random.choice([None,0,3.5,4.9,5,6,'4.5']), 'totalHires':random.choice([None,0,1,5,20,50]),'totalJobsPosted':random.choice([None,0,10,100]), 'hireRate':random.choice([None,0,20,60,80,101]),'paymentVerified':random.choice([None,False,True])})
        jobs=[{'clientInfo':c} for c in cases]
        root=Path(__file__).resolve().parents[1]
        code="const f=require('./public/job-filters.js');let s='';process.stdin.on('data',d=>s+=d);process.stdin.on('end',()=>process.stdout.write(JSON.stringify(JSON.parse(s).map(j=>f.customerStars(j).stars))));"
        result=subprocess.run(['node','-e',code],input=json.dumps(jobs),text=True,capture_output=True,cwd=root,check=True)
        self.assertEqual([customer_stars(j) for j in jobs],json.loads(result.stdout))

import concurrent.futures
import http.cookiejar
import io
import json
import os
import secrets
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

TEST_DATA = tempfile.TemporaryDirectory()
os.environ['FREELANCE_DATA_DIR'] = TEST_DATA.name
os.environ['FREELANCE_PASSWORD'] = secrets.token_urlsafe(24)
for variable in ['FREELANCE_AI_KEY', 'FREELANCE_SLACK_TOKEN', 'FREELANCE_SLACK_CHANNEL', 'FREELANCE_TELEGRAM_TOKEN', 'FREELANCE_TELEGRAM_CHAT_ID']:
    os.environ.pop(variable, None)
import server
import services


def job(identifier='~job1'):
    return {'id': identifier, 'title': 'Build a customer dashboard', 'url': 'https://www.upwork.com/jobs/' + identifier, 'type': 'Fixed', 'budget': '$500', 'description': 'Customer dashboard with search and export.', 'skills': ['Python', 'SQLite'], 'client': {'country': 'United States', 'rating': 4.9, 'totalSpent': 2000, 'paymentVerified': True}, 'postedAt': '2026-10-11T00:00:00Z'}


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.base = 'http://127.0.0.1:' + str(cls.http.server_port)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        TEST_DATA.cleanup()

    def test_new_lead_autoarchive_is_persisted(self):
        from datetime import timedelta
        from zoneinfo import ZoneInfo
        from datetime import datetime
        today=datetime.now(ZoneInfo('Asia/Bangkok')).date()
        self.call('/api/records', {'kind':'client','name':'Unanswered new lead','clientGroup':'talk','clientStage':'new','clientInquiryDate':(today-timedelta(days=14)).isoformat()})
        clients=self.call('/api/records')
        c=next(c for c in clients if c['name']=='Unanswered new lead')
        self.assertEqual(c['clientGroup'],'archive')
        with server.connect() as db:
            saved=json.loads(db.execute('SELECT body FROM records WHERE id=?',(c['id'],)).fetchone()['body'])
        self.assertEqual(saved['clientStage'],'closed-no-contract')

    def setUp(self):
        with server.connect() as db:
            for table in ['records', 'settings', 'imported_jobs', 'outbox', 'job_interest', 'job_reviews']:
                db.execute('DELETE FROM ' + table)
        server.SESSIONS.clear()
        server.LOGIN_ATTEMPTS.clear()
        self.client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.call('/api/login', {'password': server.PASSWORD})

    def call(self, path, data=None, method=None, opener=None, headers=None):
        request = urllib.request.Request(self.base + path, data=json.dumps(data).encode() if data is not None else None, method=method, headers={'Content-Type': 'application/json', **(headers or {})})
        with (opener or self.client).open(request) as response:
            return json.load(response)

    def test_interest_expires_without_removing_job_or_extending_save(self):
        raw = job(); raw['proposalsTier'] = 'Less than 5'
        server.import_jobs({'event':'new_jobs','jobs':[raw]})
        record = self.call('/api/records')[0]
        self.assertEqual(record['proposalsTier'],'Less than 5')
        self.assertEqual(record['jobAssessment']['state'],'unconfigured')
        self.call('/api/jobs/interest',{'id':record['id'],'interested':True})
        saved = self.call('/api/records')[0]
        self.assertTrue(saved['interested'])
        self.call('/api/jobs/interest',{'id':record['id'],'interested':True})
        self.assertEqual(saved['interestExpiresAt'],self.call('/api/records')[0]['interestExpiresAt'])
        with server.connect() as db:
            db.execute('UPDATE job_interest SET expires=?',(time.time()-1,))
        expired = self.call('/api/records')[0]
        self.assertFalse(expired['interested'])
        self.assertEqual(expired['name'],record['name'])

    def test_radar_unknowns_do_not_get_green_and_cache_invalidates(self):
        import job_radar
        from datetime import datetime, timezone
        j = services.normalize_job(job())
        j['postedAt']=datetime.now(timezone.utc).isoformat(); j['proposalsTier']='Less than 5'
        review=dict(summary='Tóm tắt',priceComment='Phù hợp',clarityComment='Rõ',riskComment='Chưa thấy dấu hiệu',warnings=[],budgetScore=25,clarityScore=20,safetyScore=15)
        self.assertEqual(job_radar.present(j,review)['color'],'green')
        j['proposalsTier']=''
        self.assertEqual(job_radar.present(j,review)['color'],'yellow')
        review['safetyScore']=2
        self.assertEqual(job_radar.present(j,review)['color'],'red')
        server.import_jobs({'event':'new_jobs','jobs':[job()]})
        stored=server.records()[0]
        with server.connect() as db:
            db.execute('INSERT INTO job_reviews VALUES (?,?,?)',(stored['id'],server.job_signature(stored),json.dumps(review)))
        self.assertEqual(server.records()[0]['jobAssessment']['state'],'completed')
        self.call('/api/records',dict(stored,notes='Changed scope'))
        self.assertEqual(server.records()[0]['jobAssessment']['state'],'unconfigured')

    def test_job_ai_schema_and_missing_data_limits(self):
        import job_radar
        result=dict(summary='Viết app',priceComment='Chưa có giá',clarityComment='Thiếu mô tả',riskComment='Chưa đủ dữ liệu',warnings=[],budgetScore=25,clarityScore=20,safetyScore=15)
        response={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(result)}]}]}
        with patch.dict(os.environ,{'FREELANCE_AI_KEY':'test-only'}), patch('job_radar.post_json',return_value=response) as provider:
            review=job_radar.evaluate({'name':'Job'})
            self.assertEqual((review['budgetScore'],review['clarityScore'],review['safetyScore']),(10,5,7))
            self.assertEqual(job_radar.present({'name':'Job'},review)['color'],'yellow')
            self.assertFalse(provider.call_args.args[1]['store'])
            result['budgetScore']=True
            response['output'][0]['content'][0]['text']=json.dumps(result)
            with self.assertRaises(services.ServiceError): job_radar.evaluate({'name':'Job'})

    def test_client_activity_updates_history_without_duplicate_notifications(self):
        from datetime import datetime, timezone, timedelta
        now=datetime.now(timezone.utc)
        raw=job(); raw['clientActivity']={'lastViewedAt':(now-timedelta(hours=6)).isoformat()}
        server.import_jobs({'event':'new_jobs','jobs':[raw]})
        saved=self.call('/api/records')[0]
        self.assertEqual(saved['jobAssessment']['activity']['state'],'quiet')
        self.assertEqual(len(saved['clientActivityHistory']),1)
        self.call('/api/records',{'id':saved['id'],'kind':'job','name':saved['name'],'notes':'My full description'})
        raw['clientActivity']['lastViewedAt']=(now-timedelta(minutes=10)).isoformat()
        result=server.import_jobs({'event':'new_jobs','jobs':[raw]})
        self.assertEqual(result,{'created':0,'duplicates':1})
        current=self.call('/api/records')[0]
        self.assertEqual(current['notes'],'My full description')
        self.assertEqual(current['jobAssessment']['activity']['state'],'recent')
        self.assertEqual(len(current['clientActivityHistory']),2)
        server.import_jobs({'event':'new_jobs','jobs':[raw]})
        self.assertEqual(len(self.call('/api/records')[0]['clientActivityHistory']),2)
        self.call('/api/jobs/activity',{'id':saved['id'],'lastViewedAt':now.isoformat()})
        current=self.call('/api/records')[0]
        self.assertEqual(current['clientActivityHistory'][-1]['source'],'manual')
        self.assertEqual(len(current['clientActivityHistory']),3)
        with self.assertRaises(urllib.error.HTTPError):
            self.call('/api/jobs/activity',{'id':saved['id'],'lastViewedAt':(now+timedelta(days=1)).isoformat()})

    def test_activity_quiet_penalty_requires_a_fresh_observation(self):
        import job_activity, job_radar
        from datetime import datetime, timezone, timedelta
        now=datetime.now(timezone.utc)
        j=services.normalize_job(job())
        j['postedAt']=(now-timedelta(hours=5)).isoformat();j['proposalsTier']='Less than 5'
        self.assertEqual(job_activity.status(j)['state'],'unknown')
        review=dict(summary='Tóm tắt',priceComment='Phù hợp',clarityComment='Rõ',riskComment='Chưa thấy dấu hiệu',warnings=[],budgetScore=25,clarityScore=20,safetyScore=15)
        original=job_radar.present(j,review)
        job_activity.merge(j,{'lastViewedAt':(now-timedelta(hours=5)).isoformat()})
        quiet=job_radar.present(j,review)
        self.assertEqual(quiet['color'],'yellow')
        self.assertEqual(quiet['score'],original['score']-10)
        j['clientActivity']['observedAt']=(now-timedelta(hours=2)).isoformat()
        stale=job_radar.present(j,review)
        self.assertEqual(stale['activity']['state'],'outdated')
        self.assertEqual(stale['score'],original['score'])
        j2=services.normalize_job(dict(job(),clientActivity={'lastBuyerActivity':(now-timedelta(minutes=5)).isoformat()}))
        self.assertNotIn('lastViewedAt',j2['clientActivity'])
        self.assertEqual(job_activity.status(j2)['state'],'recent')
        with self.assertRaises(services.ServiceError):
            services.normalize_job(dict(job(),clientActivity={'lastViewedAt':'5 hours ago'}))

    def test_sent_marker_persists_is_reversible_and_does_not_create_a_letter(self):
        server.import_jobs({'event':'new_jobs','jobs':[job()]})
        original=next(r for r in self.call('/api/records') if r['kind']=='job')
        self.assertFalse(original.get('proposalSent',False))
        payload={'id':original['id'],'sent':True}
        first=self.call('/api/jobs/proposal-sent',payload)
        again=self.call('/api/jobs/proposal-sent',payload)
        self.assertEqual(first['proposalSentAt'],again['proposalSentAt'])
        marked=next(r for r in self.call('/api/records') if r['kind']=='job')
        self.assertTrue(marked['proposalSent'])
        self.assertEqual(marked['notes'],original['notes'])
        self.assertEqual(len(self.call('/api/records')),2)
        self.assertFalse(any(r['kind']=='sentproposal' for r in self.call('/api/records')))
        self.call('/api/records',{'id':original['id'],'kind':'job','name':original['name'],'notes':'Edited scope','proposalSent':False})
        self.assertTrue(next(r for r in self.call('/api/records') if r['kind']=='job')['proposalSent'])
        server.import_jobs({'event':'new_jobs','jobs':[job()]})
        self.assertTrue(next(r for r in self.call('/api/records') if r['kind']=='job')['proposalSent'])
        self.call('/api/jobs/interest',{'id':original['id'],'interested':True})
        with server.connect() as db: db.execute('UPDATE job_interest SET expires=?',(time.time()-1,))
        after_expiry=next(r for r in self.call('/api/records') if r['kind']=='job')
        self.assertFalse(after_expiry['interested'])
        self.assertTrue(after_expiry['proposalSent'])
        self.call('/api/jobs/proposal-sent',{'id':original['id'],'sent':False})
        unmarked=next(r for r in self.call('/api/records') if r['kind']=='job')
        self.assertFalse(unmarked['proposalSent'])
        self.assertIsNone(unmarked['proposalSentAt'])
        with self.assertRaises(urllib.error.HTTPError):
            self.call('/api/jobs/proposal-sent',{'id':original['id'],'sent':'true'})
        with self.assertRaises(urllib.error.HTTPError):
            self.call('/api/jobs/proposal-sent',{'id':9999,'sent':True})

    def test_project_tracking_keeps_history_and_contract_date(self):
        server.import_jobs({'event':'new_jobs','jobs':[job()]})
        original=self.call('/api/records')[0]
        for _ in range(2): self.call('/api/jobs/proposal-sent',{'id':original['id'],'sent':True})
        projects=[r for r in self.call('/api/records') if r['kind']=='project']
        self.assertEqual(len(projects),1)
        project=projects[0];sent_at=project['sentAt']
        self.call('/api/projects/contract',{'id':project['id'],'won':True})
        won=next(r for r in self.call('/api/records') if r['kind']=='project')
        self.assertTrue(won['won']);self.assertTrue(won['wonAt'])
        self.call('/api/projects/contract',{'id':project['id'],'won':True})
        self.assertEqual(next(r for r in self.call('/api/records') if r['kind']=='project')['wonAt'],won['wonAt'])
        self.call('/api/jobs/proposal-sent',{'id':original['id'],'sent':False})
        self.call('/api/jobs/proposal-sent',{'id':original['id'],'sent':True})
        projects=[r for r in self.call('/api/records') if r['kind']=='project']
        self.assertEqual(len(projects),1);self.assertEqual(projects[0]['sentAt'],sent_at)
        self.call('/api/projects/contract',{'id':project['id'],'won':False})
        self.assertIsNone(next(r for r in self.call('/api/records') if r['kind']=='project')['wonAt'])
        with self.assertRaises(urllib.error.HTTPError): self.call('/api/projects/contract',{'id':project['id'],'won':'yes'})

    def test_login_and_session_protect_data_and_settings(self):
        guest = urllib.request.build_opener()
        self.assertFalse(self.call('/api/auth', opener=guest)['authenticated'])
        for path in ['/api/records', '/api/settings']:
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.call(path, opener=guest)
            self.assertEqual(error.exception.code, 401)
        self.call('/api/logout', {})
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.call('/api/records')
        self.assertEqual(error.exception.code, 401)

    def test_crud_and_metadata_preservation(self):
        c = self.call('/api/records', {'kind': 'client', 'name': 'Test client'})
        self.call('/api/records', {**c, 'notes': 'Discussed scope'})
        server.import_jobs({'event': 'new_jobs', 'jobs': [job()]})
        record = next(r for r in self.call('/api/records') if r['kind'] == 'job')
        self.call('/api/records', {'id': record['id'], 'kind': 'job', 'name': record['name'], 'status': 'Phỏng vấn', 'unread': False})
        saved = next(r for r in self.call('/api/records') if r['kind'] == 'job')
        self.assertEqual(saved['externalId'], '~job1')
        self.assertEqual(saved['status'], 'Phỏng vấn')
        self.assertFalse(saved['unread'])
        self.call('/api/records/' + str(c['id']), method='DELETE')
        self.assertEqual(len(self.call('/api/records')), 1)

    def test_webhook_authorization_and_duplicate_delivery(self):
        guest = urllib.request.build_opener()
        payload = {'event': 'new_jobs', 'count': 1, 'jobs': [job()]}
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.call('/api/webhook/wrong', payload, opener=guest)
        self.assertEqual(error.exception.code, 403)
        path = '/api/webhook/' + server.WEBHOOK_TOKEN
        self.assertEqual(self.call(path, payload, opener=guest)['created'], 1)
        self.assertEqual(self.call(path, payload, opener=guest)['duplicates'], 1)
        self.assertEqual(len(self.call('/api/records')), 1)

    def test_concurrent_duplicate_webhooks(self):
        payload = {'event': 'new_jobs', 'jobs': [job()]}
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda _: server.import_jobs(payload), range(6)))
        self.assertEqual(sum(r['created'] for r in results), 1)
        self.assertEqual(len(server.records()), 1)

    def test_invalid_batch_is_atomic(self):
        for invalid in [dict(job('~bad'), url='https://evil.example/job'), dict(job('~bad'), url='https://['), dict(job('~bad'), skills='Python')]:
            with self.assertRaises(services.ServiceError):
                server.import_jobs({'event': 'new_jobs', 'jobs': [job(), invalid]})
            self.assertEqual(server.records(), [])

    def test_cross_origin_edit_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.call('/api/records', {'kind': 'client', 'name': 'Bad origin'}, headers={'Origin': 'https://evil.example'})
        self.assertEqual(error.exception.code, 403)
        self.assertEqual(server.records(), [])

    def test_profile_and_missing_ai_key(self):
        self.call('/api/settings', {'name': 'Trang', 'services': 'Web development', 'experience': 'Portfolio project'})
        self.assertEqual(self.call('/api/settings')['profile']['name'], 'Trang')
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.call('/api/ai/proposal', {'requirements': 'Build a website'})
        self.assertEqual(error.exception.code, 503)

    def test_ai_payload_and_response(self):
        response = {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': 'Hi, I can help with your dashboard.'}]}]}
        with patch.dict(os.environ, {'FREELANCE_AI_KEY': 'test-placeholder'}), patch('services.post_json', return_value=response) as send:
            result = services.generate_proposal({'requirements': 'Build a dashboard', 'budget': '$500', 'language': 'English'}, {'experience': 'My supplied experience'}, {'name': 'Dashboard', 'notes': 'Search and export'})
        self.assertIn('dashboard', result['body'])
        url, payload, headers = send.call_args.args
        self.assertEqual(url, 'https://api.openai.com/v1/responses')
        self.assertFalse(payload['store'])
        context = json.loads(payload['input'])
        self.assertEqual(context['freelancer_profile']['experience'], 'My supplied experience')
        self.assertEqual(context['draft']['budget'], '$500')
        self.assertNotIn('test-placeholder', payload['input'])

    def test_ai_failure_and_partial_output(self):
        with patch.dict(os.environ, {'FREELANCE_AI_KEY': 'test-placeholder'}):
            for response in [{'status': 'incomplete', 'output': []}, {'status': 'completed', 'output': []}]:
                with patch('services.post_json', return_value=response), self.assertRaises(services.ServiceError):
                    services.generate_proposal({'requirements': 'Website'}, {})
            with patch('services.post_json', side_effect=urllib.error.HTTPError('https://api.openai.com', 429, 'Quota', {}, io.BytesIO())), self.assertRaises(services.ServiceError) as error:
                services.generate_proposal({'requirements': 'Website'}, {})
            self.assertEqual(error.exception.status, 502)

    def test_outbox_retries_and_deduplication(self):
        with patch('server.channels', return_value={'slack': True, 'telegram': True}):
            server.import_jobs({'event': 'new_jobs', 'jobs': [job()]})
            server.import_jobs({'event': 'new_jobs', 'jobs': [job()]})
        with server.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM outbox').fetchone()[0], 2)
        with patch('server.send_notification', side_effect=services.ServiceError('Test failure')):
            server.process_outbox()
        with server.connect() as db:
            first = db.execute('SELECT * FROM outbox ORDER BY id').fetchone()
            self.assertEqual(first['attempts'], 1)
            self.assertEqual(first['status'], 'pending')
            self.assertGreater(first['next_try'], time.time())
            db.execute('UPDATE outbox SET next_try=0')
        with patch('server.send_notification') as send:
            while server.process_outbox():
                pass
            self.assertEqual(send.call_count, 2)
        with server.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM outbox WHERE status='sent'").fetchone()[0], 2)

    def test_notification_provider_payloads(self):
        item = services.normalize_job(job())
        env = {'FREELANCE_SLACK_TOKEN': 'dummy-slack', 'FREELANCE_SLACK_CHANNEL': 'test-channel', 'FREELANCE_TELEGRAM_TOKEN': 'dummy-telegram', 'FREELANCE_TELEGRAM_CHAT_ID': 'test-chat'}
        with patch.dict(os.environ, env), patch('services.post_json', return_value={'ok': True}) as send:
            services.send_notification('slack', item)
            self.assertEqual(send.call_args.args[1]['channel'], 'test-channel')
            self.assertFalse(send.call_args.args[1]['mrkdwn'])
            services.send_notification('telegram', item)
            self.assertEqual(send.call_args.args[1]['chat_id'], 'test-chat')
            self.assertIn(item['url'], send.call_args.args[1]['text'])
        with patch.dict(os.environ, env), patch('services.post_json', return_value={'ok': False}), self.assertRaises(services.ServiceError):
            services.send_notification('slack', item)

    def test_graph_validation_and_sent_snapshot(self):
        graph = {'version': 1, 'nodes': [
            {'id':'job','type':'job','x':40,'y':60,'title':'Job','content':'Build a dashboard'},
            {'id':'draft','type':'draft','x':380,'y':170,'title':'Draft','content':'Draft v1'},
            {'id':'review','type':'review','x':720,'y':60,'title':'Review','content':''},
            {'id':'final','type':'final','x':720,'y':350,'title':'Final','content':'Final sent letter'},
        ], 'edges':[{'from':'job','to':'draft'},{'from':'draft','to':'review'},{'from':'draft','to':'final'},{'from':'review','to':'final'}]}
        linked_job = self.call('/api/records', {'kind':'job','name':'Dashboard job','notes':'Build a dashboard'})
        proposal = self.call('/api/records', {'kind':'proposal','name':'Dashboard proposal','workspace':graph,'body':'Final sent letter','jobId':linked_job['id']})
        self.assertEqual(self.call('/api/records')[0]['workspace']['nodes'][1]['x'], 380)
        sent = self.call('/api/proposals/send', {'id':proposal['id'],'finalNodeId':'final'})
        self.assertFalse(sent['duplicate'])
        self.assertTrue(self.call('/api/proposals/send', {'id':proposal['id'],'finalNodeId':'final'})['duplicate'])
        archive = next(r for r in self.call('/api/records') if r['kind']=='sentproposal')
        marked_job = next(r for r in self.call('/api/records') if r['kind']=='job')
        self.assertTrue(marked_job['proposalSent'])
        self.assertEqual(marked_job['proposalSentAt'],archive['sentAt'])
        graph['nodes'][-1]['content']='Edited after sending'
        self.call('/api/records', {**proposal,'workspace':graph,'body':'Edited after sending'})
        self.call('/api/records', {**archive,'body':'Attempted overwrite','name':'Different name','outcome':'won','outcomeNotes':'Contract accepted','interaction':'replied'})
        saved = next(r for r in self.call('/api/records') if r['kind']=='sentproposal')
        self.assertEqual(saved['body'],'Final sent letter')
        self.assertEqual(saved['name'],'Dashboard proposal')
        self.assertEqual(saved['outcome'],'won')
        self.assertEqual(saved['interaction'],'replied')
        self.assertTrue(saved['interactionAt'])
        self.assertEqual(saved['finalNodeId'],'final')
        self.assertEqual(saved['workspaceSnapshot']['nodes'][-1]['content'],'Final sent letter')
        graph['edges'].append({'from':'final','to':'review'})
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.call('/api/records', {**proposal,'workspace':graph})
        self.assertEqual(error.exception.code,400)

    def test_review_structured_output_and_invalid_score(self):
        review = {'score':82,'summary':'Clear proposal','strengths':['Specific approach'],'weaknesses':['Timeline missing'],'suggestions':['Confirm milestones'],'criteria':[{'name':str(i),'score':80,'reason':'Evidence from draft'} for i in range(4)]}
        def response(value):
            return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(value)}]}]}
        with patch.dict(os.environ, {'FREELANCE_AI_KEY':'test-placeholder'}), patch('services.post_json',return_value=response(review)) as send:
            result=services.evaluate_proposal({'body':'My letter','requirements':'Build a dashboard'}, {'experience':'Verified project'})
            self.assertEqual(result['review']['score'],82)
            payload=send.call_args.args[1]
            self.assertEqual(payload['text']['format']['type'],'json_schema')
            self.assertIn('not a probability',payload['instructions'])
        for score in [101,-1,True]:
            with patch.dict(os.environ, {'FREELANCE_AI_KEY':'test-placeholder'}), patch('services.post_json',return_value=response({**review,'score':score})), self.assertRaises(services.ServiceError):
                services.evaluate_proposal({'body':'Letter','requirements':'Job'}, {})

    def test_templates_reach_ai_as_references(self):
        reply={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'Customized letter'}]}]}
        with patch.dict(os.environ, {'FREELANCE_AI_KEY':'test-placeholder'}), patch('services.post_json',return_value=reply) as send:
            services.generate_proposal({'requirements':'New job','templates':['Won contract sample','Another sample'],'existingDraft':'My draft','feedback':'Clarify scope'}, {})
            context=json.loads(send.call_args.args[1]['input'])
            self.assertEqual(context['reference_templates'],['Won contract sample','Another sample'])
            self.assertEqual(context['existing_draft'],'My draft')
            self.assertEqual(context['review_feedback'],'Clarify scope')


if __name__ == '__main__':
    unittest.main()

import os
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from html.parser import HTMLParser

import services
import telegram_details as details
from job_notification import render


class TelegramDetailsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'db.sqlite3'
        class Closing(sqlite3.Connection):
            def __exit__(self,*args):
                try:return super().__exit__(*args)
                finally:self.close()
        def connect():
            db=sqlite3.connect(self.path,factory=Closing);db.row_factory=sqlite3.Row;return db
        self.connect=connect
        with connect() as db:db.execute('CREATE TABLE outbox(id INTEGER PRIMARY KEY,body TEXT NOT NULL)')
        details.init(connect)
        self.env=patch.dict(os.environ,{'FREELANCE_TELEGRAM_TOKEN':'test-only','FREELANCE_TELEGRAM_CHAT_ID':'123'});self.env.start()
        self.job=services.normalize_job({'id':'~details','title':'Full <job>','url':'https://www.upwork.com/jobs/~details','description':'A long description with <markup> & real detail.','client':{'rating':4.5,'totalHires':20,'paymentVerified':True}})
        self.job['_telegramDetails']='abcdefghijklmnop'
        with connect() as db:db.execute('INSERT INTO outbox VALUES(1,?)',(json.dumps(self.job),))
        details.register(connect,self.job,1,{'ok':True,'result':{'message_id':77,'chat':{'id':123}}})

    def tearDown(self):self.env.stop();self.tmp.cleanup()

    def click(self,page=0,chat=123,message=77):
        return {'id':'callback-fixture','data':f'fd:abcdefghijklmnop:{page}','message':{'message_id':message,'chat':{'id':chat}}}

    def test_compact_initial_message_has_real_expand_and_upwork_buttons(self):
        with patch('services.post_json',return_value={'ok':True,'result':{'message_id':77,'chat':{'id':123}}}) as send,patch('services.ai_request',side_effect=AssertionError('No AI')):
            services.send_notification('telegram',self.job)
        payload=send.call_args.args[1]
        self.assertNotIn(self.job['notes'],payload['text'])
        rows=payload['reply_markup']['inline_keyboard']
        self.assertIn('Xem mô tả đầy đủ',rows[0][0]['text'])
        self.assertEqual(rows[1][0]['url'],self.job['url'])
        self.assertEqual(rows[0][0]['callback_data'],'fd:abcdefghijklmnop:0')

    def test_click_opens_full_description_then_collapses_same_message(self):
        with patch('telegram_details.api',return_value={'ok':True}) as api:
            details.process_callback(self.connect,self.click())
            edit=api.call_args_list[0]
            self.assertEqual(edit.args[0],'editMessageText')
            self.assertIn('&lt;markup&gt; &amp; real detail.',edit.args[1]['text'])
            self.assertEqual(edit.args[1]['message_id'],77)
            self.assertIn('Thu gọn',edit.args[1]['reply_markup']['inline_keyboard'][0][0]['text'])
            details.process_callback(self.connect,self.click(-1))
            self.assertEqual(api.call_args_list[2].args[1]['text'],render(self.job))

    def test_long_unicode_description_has_no_missing_or_duplicate_text(self):
        description=('😀 Vietnamese <&>\n'*2000)[:20000]
        parts=details.chunks(description)
        self.assertEqual(''.join(parts),description)
        job=dict(self.job,notes=description)
        class Plain(HTMLParser):
            def __init__(self):super().__init__();self.parts=[]
            def handle_data(self,value):self.parts.append(value)
        for page in range(len(parts)):
            text,buttons=details.expanded(job,page);plain=Plain();plain.feed(text)
            self.assertLessEqual(len(''.join(plain.parts).encode('utf-16-le'))//2,4096)
            self.assertIn('inline_keyboard',buttons)
        self.assertGreater(len(parts),1)

    def test_wrong_chat_or_message_or_new_bot_cannot_read_job(self):
        for callback in [self.click(chat=999),self.click(message=999)]:
            with patch('telegram_details.api',return_value={'ok':True}) as api:
                details.process_callback(self.connect,callback)
                self.assertNotIn('editMessageText',[c.args[0] for c in api.call_args_list])
        with patch.dict(os.environ,{'FREELANCE_TELEGRAM_TOKEN':'another-bot'}),patch('telegram_details.api',return_value={'ok':True}) as api:
            details.process_callback(self.connect,self.click())
            self.assertNotIn('editMessageText',[c.args[0] for c in api.call_args_list])

    def test_get_updates_offset_is_persistent_and_callback_only(self):
        replies=[{'ok':True,'result':[{'update_id':501,'callback_query':self.click()}]},{'ok':True},{'ok':True}]
        with patch('telegram_details.api',side_effect=replies) as api:
            self.assertTrue(details.poll_once(self.connect))
            self.assertEqual(api.call_args_list[0].args[1]['allowed_updates'],['callback_query'])
        with patch('telegram_details.api',return_value={'ok':True,'result':[]}) as api:
            details.poll_once(self.connect)
            self.assertEqual(api.call_args.args[1]['offset'],502)

    def test_invalid_page_is_acknowledged_without_edit(self):
        with patch('telegram_details.api',return_value={'ok':True}) as api:
            details.process_callback(self.connect,self.click(999))
            self.assertEqual([c.args[0] for c in api.call_args_list],['answerCallbackQuery'])

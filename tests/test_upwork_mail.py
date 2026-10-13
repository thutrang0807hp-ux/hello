import base64
import json
import os
import sqlite3
import tempfile
import unittest
from email.message import EmailMessage
from pathlib import Path
from unittest.mock import patch
import upwork_mail as mail
from services import ServiceError


def sample(sender='room_abc123@email.upwork.com', subject='John L. sent you a message', body=None):
    m=EmailMessage();m['From']='John L. via Upwork <'+sender+'>';m['Subject']=subject;m['Date']='Sat, 10 Oct 2026 02:02:00 +0700';m['Message-ID']='<sample@email.upwork.com>'
    m['Authentication-Results']='mx.google.com; dkim=pass header.i=@email.upwork.com; spf=pass'
    m.set_content(body or '<div>Unread message from <a>John L.</a> about <a>Video Editing</a>.</div><div>John L.</div><div>1:54 AM ICT, 10 Oct 2026</div><p>Hey Trang, I have a new project.</p><a href="https://www.upwork.com/messages/rooms/abc">View on Upwork</a><p>Or, you can respond by replying to this email.</p>', subtype='html')
    return m.as_bytes()


class MailTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.env=patch.dict(os.environ,{'FREELANCE_DATA_DIR':self.tmp.name});self.env.start()
        self.db=Path(self.tmp.name)/'test.db'
        with self.connect() as db:
            db.execute('CREATE TABLE records(id INTEGER PRIMARY KEY,kind TEXT,body TEXT)')
            db.execute('INSERT INTO records VALUES (1,\'client\',?)',(json.dumps({'name':'John L.','clientGroup':'archive','clientStage':'closed-no-contract','lastReplyDate':'2026-10-11'}),))
        mail.init(self.connect)
    def tearDown(self):self.env.stop();self.tmp.cleanup();mail.PENDING.clear()
    def connect(self):
        db=sqlite3.connect(self.db);db.row_factory=sqlite3.Row;return db
    def test_overview_summary_bounds_previews_and_uses_vietnam_day(self):
        from datetime import datetime
        times=['2026-10-12T16:59:59+00:00','2026-10-12T17:00:00+00:00','2026-10-13T12:00:00+07:00']
        for i in range(7):
            item={'id':'overview-'+str(i),'room':'overview-room-'+str(i),'sender':'Client '+str(i),'project':'Editing','text':'X'*250,'receivedAt':times[i%3],'source':'eml'}
            mail.store(self.connect,item)
        with patch.object(mail,'datetime') as clock:
            clock.now.return_value=datetime(2026,10,13,9,0,tzinfo=mail.LOCAL_ZONE)
            result=mail.pending_summary(self.connect)
        self.assertEqual(result['todayCount'],4);self.assertEqual(result['attentionCount'],7);self.assertEqual(len(result['previews']),5)
        self.assertTrue(all(len(m['preview'])==180 for m in result['previews']));self.assertTrue(all(not m['seen'] for m in result['previews']))
        self.assertNotIn('room',result['previews'][0])
    def test_read_pending_still_shows_but_read_linked_does_not(self):
        first=mail.parse(sample());second=dict(first,id='other',room='other-room',messageId='<other@example.test>')
        mail.store(self.connect,first);mail.store(self.connect,second)
        mail.link(self.connect,{'id':first['id'],'clientId':1})
        mail.seen(self.connect,first['id']);mail.seen(self.connect,second['id'])
        result=mail.pending_summary(self.connect);self.assertEqual(result['unreadCount'],0);self.assertEqual(result['attentionCount'],1);self.assertEqual([m['id'] for m in result['previews']],['other'])
    def test_extract_only_message_and_safe_link(self):
        m=mail.parse(sample());self.assertEqual(m['sender'],'John L.');self.assertEqual(m['project'],'Video Editing');self.assertEqual(m['text'],'Hey Trang, I have a new project.');self.assertEqual(m['room'],'room_abc123');self.assertTrue(m['authenticated']);self.assertTrue(m['url'].startswith('https://www.upwork.com/messages/'))
    def test_ignore_ads_and_lookalike_domains(self):
        self.assertIsNone(mail.parse(sample(subject='New jobs for you')))
        self.assertIsNone(mail.parse(sample(sender='room_abc123@email.upwork.com.evil.example')))
        m=mail.parse(sample(body='<p>No message content here</p>'));self.assertTrue(m['previewOnly']);self.assertEqual(m['text'],'')
    def test_room_link_dedup_and_no_date_or_stage_regression(self):
        m=mail.parse(sample());self.assertTrue(mail.store(self.connect,m));self.assertFalse(mail.store(self.connect,m));self.assertIsNone(mail.inbox(self.connect)[0]['clientId'])
        mail.link(self.connect,{'id':m['id'],'clientId':1})
        newer=mail.parse(sample().replace(b'<sample@',b'<newer@'),'gmail2',1791694800000);mail.store(self.connect,newer)
        self.assertEqual(mail.inbox(self.connect)[0]['clientId'],1)
        with self.connect() as db:c=json.loads(db.execute('SELECT body FROM records WHERE id=1').fetchone()[0])
        self.assertEqual(c['lastReplyDate'],'2026-10-11');self.assertEqual(c['clientGroup'],'archive');self.assertTrue(c['upworkMailUnread'])
        for m in mail.inbox(self.connect):mail.seen(self.connect,m['id'])
        with self.connect() as db:c=json.loads(db.execute('SELECT body FROM records WHERE id=1').fetchone()[0])
        self.assertFalse(c['upworkMailUnread'])
    def test_unverified_sender_never_auto_links(self):
        m=mail.parse(sample());mail.store(self.connect,m);mail.link(self.connect,{'id':m['id'],'clientId':1})
        raw=sample().replace(b'<sample@',b'<unverified@').replace(b'dkim=pass',b'dkim=fail');mail.store(self.connect,mail.parse(raw,'gmail3'))
        self.assertIsNone(next(m for m in mail.inbox(self.connect) if m['id']=='gmail3')['clientId'])
    def test_oauth_pkce_state_and_secrets(self):
        mail.configure({'clientId':'test.apps.googleusercontent.com','clientSecret':'secret'})
        redirect='http://127.0.0.1:8000/api/mail/callback';flow=mail.begin(redirect)
        from urllib.parse import parse_qs,urlsplit
        query=parse_qs(urlsplit(flow['url']).query)
        self.assertEqual(query['scope'],[mail.SCOPE]);self.assertEqual(query['code_challenge_method'],['S256']);self.assertNotIn('secret',flow['url'])
        with self.assertRaises(ServiceError):mail.callback(dict(query,code=['code']),'wrong-cookie')
        with patch.object(mail,'google',return_value={'refresh_token':'private-token','scope':mail.SCOPE}) as request:
            mail.callback({'state':query['state'],'code':['code']},flow['cookie'])
        self.assertEqual(request.call_args.args[1]['redirect_uri'],redirect);self.assertIn('code_verifier',request.call_args.args[1]);self.assertTrue(mail.status()['connected']);self.assertNotIn('private-token',json.dumps(mail.status()))
        with self.assertRaises(ServiceError):mail.callback({'state':query['state'],'code':['code']},flow['cookie'])
        mail.disconnect();self.assertFalse(mail.status()['connected'])
    def test_sync_continues_next_page_on_next_run(self):
        mail.save({'clientId':'test.apps.googleusercontent.com','clientSecret':'secret','refreshToken':'token'})
        seen=[]
        def google(url,data=None,token=None):
            if 'oauth2' in url:return {'access_token':'access'}
            from urllib.parse import parse_qs,urlsplit
            page=parse_qs(urlsplit(url).query).get('pageToken',[''])[0];seen.append(page)
            return {'messages':[],**({'nextPageToken':{'':'one','one':'two'}[page]} if page in ('','one') else {})}
        with patch.object(mail,'google',side_effect=google):
            self.assertTrue(mail.sync(self.connect)['limited']);self.assertEqual(mail.private()['pageToken'],'two')
            self.assertFalse(mail.sync(self.connect)['limited']);self.assertEqual(seen,['','one','two'])
    def test_spoofed_dkim_domain_is_not_verified(self):
        raw=sample().replace(b'header.i=@email.upwork.com;',b'header.i=@email.upwork.com.evil.example;')
        self.assertFalse(mail.parse(raw)['authenticated'])
    def test_sync_fixed_filter_and_duplicate(self):
        mail.save({'clientId':'test.apps.googleusercontent.com','clientSecret':'secret','refreshToken':'token'})
        raw=base64.urlsafe_b64encode(sample()).decode().rstrip('=')
        def google(url,data=None,token=None):
            if 'oauth2' in url:return {'access_token':'access'}
            if '?format=raw' in url:return {'raw':raw,'internalDate':'1791572520000'}
            self.assertIn('sent+you+a+message',url);return {'messages':[{'id':'gmail1'}]}
        with patch.object(mail,'google',side_effect=google):
            self.assertEqual(mail.sync(self.connect)['added'],1);self.assertEqual(mail.sync(self.connect)['added'],0)
        self.assertTrue(mail.status()['lastSync'])

if __name__=='__main__':unittest.main()

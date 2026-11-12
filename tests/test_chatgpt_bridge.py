import unittest
import json
import test_review_fixes as fixture
server=fixture.server
import chatgpt_bridge


class ChatGPTBridgeTests(unittest.TestCase):
    setUpClass=classmethod(fixture.ReviewFixTests.setUpClass.__func__)
    tearDownClass=classmethod(fixture.ReviewFixTests.tearDownClass.__func__)
    raw=fixture.ReviewFixTests.raw
    call=fixture.ReviewFixTests.call

    def setUp(self):
        fixture.ReviewFixTests.setUp(self)
        with server.connect() as db:db.execute('DELETE FROM chatgpt_tasks')
        self.record=self.call('/api/records',{'kind':'proposal','name':'Bridge fixture','workspace':{'version':1,'nodes':[{'id':'job','type':'job','x':0,'y':0,'title':'Job','content':'Build a dashboard'},{'id':'draft','type':'draft','x':10,'y':10,'title':'Draft','content':'Keep my draft','language':'English'}],'edges':[{'from':'job','to':'draft'}]}})

    def create(self):
        return self.call('/api/chatgpt/tasks',{'proposalId':self.record['id'],'nodeId':'draft','revision':'Make it concise'})

    def test_saved_graph_context_and_only_safe_profile_fields(self):
        with server.connect() as db:db.execute("INSERT OR REPLACE INTO settings VALUES(1,?)",(json.dumps({'name':'Trang','experience':'Real experience','api_key':'private-value'}),))
        task=self.create()
        self.assertIn('Build a dashboard',task['prompt'])
        self.assertIn('Keep my draft',task['prompt'])
        self.assertIn('Real experience',task['prompt'])
        self.assertNotIn('private-value',task['prompt'])
        self.assertEqual(task['baseContent'],'Keep my draft')
        self.assertEqual(self.call('/api/chatgpt/tasks/'+task['id'])['status'],'pending')

    def test_only_extension_origin_with_secret_can_read_and_complete(self):
        task=self.create()
        import urllib.request,urllib.error
        def bridge(token,origin,body=None):
            req=urllib.request.Request(self.base+'/api/chatgpt-bridge/'+token,headers={'Origin':origin,'Content-Type':'application/json'},data=json.dumps(body).encode() if body else None)
            try:
                with urllib.request.urlopen(req) as r:return r.status,json.load(r)
            except urllib.error.HTTPError as error:return error.code,json.load(error)
        self.assertEqual(bridge('wrong','chrome-extension://'+'a'*32)[0],403)
        self.assertEqual(bridge(server.WEBHOOK_TOKEN,'https://evil.example')[0],403)
        status,payload=bridge(server.WEBHOOK_TOKEN,'chrome-extension://'+'a'*32)
        self.assertEqual(status,200);self.assertEqual(payload['tasks'][0]['id'],task['id'])
        status,_=bridge(server.WEBHOOK_TOKEN,'chrome-extension://'+'a'*32,{'id':task['id'],'answer':'A new proposal'})
        self.assertEqual(status,200)
        result=self.call('/api/chatgpt/tasks/'+task['id']);self.assertEqual(result['answer'],'A new proposal')
        with server.connect() as db:body=json.loads(db.execute('SELECT body FROM records WHERE id=?',(self.record['id'],)).fetchone()[0])
        self.assertEqual(body['workspace']['nodes'][1]['content'],'Keep my draft')

    def test_superseded_and_disconnected_requests_cannot_overwrite(self):
        old=self.create();new=self.create()
        with self.assertRaises(server.ServiceError):chatgpt_bridge.complete(server.connect,{'id':old['id'],'answer':'stale'})
        self.call('/api/chatgpt/disconnect',{})
        with self.assertRaises(server.ServiceError):chatgpt_bridge.get(server.connect,new['id'])
        self.assertTrue(server.records(self.record['id']))

    def test_invalid_target_and_missing_job_are_rejected(self):
        status,_,_=self.raw('/api/chatgpt/tasks',{'proposalId':self.record['id'],'nodeId':'job'})
        self.assertEqual(status,400)
        with server.connect() as db:
            saved=json.loads(db.execute('SELECT body FROM records WHERE id=?',(self.record['id'],)).fetchone()[0]);saved['workspace']['edges']=[]
            db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(saved),self.record['id']))
        self.assertEqual(self.raw('/api/chatgpt/tasks',{'proposalId':self.record['id'],'nodeId':'draft'})[0],400)

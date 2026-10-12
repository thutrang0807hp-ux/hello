import json,os,sqlite3,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import mail_actions
from services import ServiceError

class MailActionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'db';self.env=patch.dict(os.environ,{'FREELANCE_AI_KEY':'fake'},clear=True);self.env.start()
  with self.connect() as db:
   db.execute('CREATE TABLE records(id INTEGER PRIMARY KEY,kind TEXT,body TEXT)');db.execute('CREATE TABLE upwork_mail(id TEXT PRIMARY KEY,body TEXT,client_id INTEGER)')
   db.execute("INSERT INTO records VALUES (1,'client',?)",(json.dumps({'name':'John','clientGroup':'active','clientStage':'working'}),))
  mail_actions.init(self.connect);self.add('1','I have a smaller project.','2026-10-10T02:00:00+07:00');self.add('2','Thanks. I will send examples Monday.','2026-10-10T04:00:00+07:00')
 def tearDown(self):self.env.stop();self.tmp.cleanup()
 def connect(self):
  db=sqlite3.connect(self.path);db.row_factory=sqlite3.Row;return db
 def add(self,ident,text,date):
  with self.connect() as db:db.execute('INSERT INTO upwork_mail VALUES (?,?,1)',(ident,json.dumps({'id':ident,'project':'Editing','receivedAt':date,'text':text})))
 def client(self):
  with self.connect() as db:return json.loads(db.execute('SELECT body FROM records WHERE id=1').fetchone()[0])
 def test_whole_context_auto_saved_once_group_preserved(self):
  result={'decision':'update','action':'Chờ khách gửi mẫu vào thứ Hai, rồi xem yêu cầu dự án.','reason':'Khách có dự án và sẽ gửi mẫu.'}
  with patch.object(mail_actions,'evaluate',return_value=result) as call:
   mail_actions.run_once(self.connect);mail_actions.run_once(self.connect)
  self.assertEqual(call.call_count,1);self.assertEqual(len(call.call_args.args[1]['messages']),2);self.assertEqual(self.client()['nextAction'],result['action']);self.assertEqual(self.client()['clientGroup'],'active')
 def test_thanks_none_cannot_erase_existing_task(self):
  with self.connect() as db:db.execute('UPDATE records SET body=? WHERE id=1',(json.dumps({'name':'John','nextAction':'Gửi bản sửa','nextActionSource':'mail-ai'}),))
  with patch.object(mail_actions,'evaluate',return_value={'decision':'none','action':'','reason':'Cảm ơn.'}):mail_actions.run_once(self.connect)
  self.assertEqual(self.client()['nextAction'],'Gửi bản sửa')
 def test_manual_edit_preserved(self):
  with self.connect() as db:db.execute('UPDATE records SET body=? WHERE id=1',(json.dumps({'name':'John','nextAction':'Việc tôi đã tự ghi'}),))
  with patch.object(mail_actions,'evaluate',return_value={'decision':'update','action':'Gợi ý khác','reason':'Tin mới'}):mail_actions.run_once(self.connect)
  self.assertEqual(self.client()['nextAction'],'Việc tôi đã tự ghi');self.assertEqual(self.client()['mailNextAction'],'Gợi ý khác')
 def test_off_does_not_call_ai(self):
  mail_actions.set_enabled(self.connect,False)
  with patch.object(mail_actions,'evaluate') as call:mail_actions.run_once(self.connect)
  call.assert_not_called()
 def test_failure_no_auto_retry_and_new_mail_reprocesses(self):
  with patch.object(mail_actions,'evaluate',side_effect=ServiceError('Quota hết')) as call:
   mail_actions.run_once(self.connect);mail_actions.run_once(self.connect);self.assertEqual(call.call_count,1)
   self.add('3','New request','2026-10-11T04:00:00+07:00');mail_actions.run_once(self.connect);self.assertEqual(call.call_count,2)
 def test_missing_key_waits_then_resumes(self):
  os.environ.pop('FREELANCE_AI_KEY')
  with patch.object(mail_actions,'evaluate') as call:mail_actions.run_once(self.connect)
  call.assert_not_called();os.environ['FREELANCE_AI_KEY']='fake'
  with patch.object(mail_actions,'evaluate',return_value={'decision':'update','action':'Xem mẫu','reason':'Có mẫu'}) as call:mail_actions.run_once(self.connect)
  self.assertEqual(call.call_count,1)
 def test_provider_payload_structured_and_uses_previous_context(self):
  with self.connect() as db:client,ctx=mail_actions.context(db,1)
  response={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps({'decision':'update','action':'Chờ mẫu','reason':'Khách sẽ gửi mẫu.'})}]}]}
  with patch.object(mail_actions,'ai_request',return_value=response) as send:
   result=mail_actions.evaluate(client,ctx)
  self.assertEqual(result['action'],'Chờ mẫu');payload=send.call_args.args[0];self.assertFalse(payload['store']);self.assertEqual(len(json.loads(payload['input'])['messages']),2)
  self.assertEqual(payload['text']['format']['schema']['properties']['decision']['enum'],['update','keep','none'])
 def test_new_manual_edit_during_ai_is_not_overwritten(self):
  def compute(client,ctx):
   with self.connect() as db:
    client['nextAction']='Việc mới do tôi ghi';client['nextActionSource']='manual';db.execute('UPDATE records SET body=? WHERE id=1',(json.dumps(client),))
   return {'decision':'update','action':'Gợi ý AI','reason':'Tin mới'}
  with patch.object(mail_actions,'evaluate',side_effect=compute):mail_actions.run_once(self.connect)
  self.assertEqual(self.client()['nextAction'],'Việc mới do tôi ghi')
 def test_restart_recovers_interrupted_processing(self):
  with self.connect() as db:_,ctx=mail_actions.context(db,1);db.execute('INSERT INTO mail_action_reviews VALUES (?,?,?)',(1,ctx['signature'],json.dumps({'state':'processing'})))
  mail_actions.init(self.connect)
  with patch.object(mail_actions,'evaluate',return_value={'decision':'update','action':'Xem mẫu','reason':'Tin mới'}) as call:mail_actions.run_once(self.connect)
  self.assertEqual(call.call_count,1)

if __name__=='__main__':unittest.main()

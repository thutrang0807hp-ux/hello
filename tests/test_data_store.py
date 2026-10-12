import json,os,sqlite3,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from data_store import data_directory,copy_data,choose_directory
import upwork_mail

class DataStoreTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.root=self.base/'install';self.root.mkdir()
  self.env=patch.dict(os.environ,{'LOCALAPPDATA':str(self.base/'profile')},clear=True);self.env.start()
 def tearDown(self):self.env.stop();self.tmp.cleanup()
 def test_windows_location_independent_of_install(self):
  self.assertEqual(data_directory(self.root,True),data_directory(self.base/'other',True))
 def test_relative_override_is_relative_to_install_not_cwd(self):
  with patch.dict(os.environ,{'FREELANCE_DATA_DIR':'custom'}):self.assertEqual(data_directory(self.root,True),self.root/'custom')
 def test_migrates_database_config_and_oauth_without_deleting_old(self):
  old=self.root/'data';old.mkdir();(old/'local-config.json').write_text('{"saved":"fake"}');(old/'gmail-private.json').write_text('{"refreshToken":"fake"}')
  with sqlite3.connect(old/'workspace.sqlite3') as db:db.execute('CREATE TABLE sample(value TEXT)');db.execute("INSERT INTO sample VALUES ('kept')")
  target=data_directory(self.root,True)
  self.assertEqual((target/'local-config.json').read_text(),(old/'local-config.json').read_text());self.assertTrue((old/'gmail-private.json').exists())
  with sqlite3.connect(target/'workspace.sqlite3') as db:self.assertEqual(db.execute('SELECT value FROM sample').fetchone()[0],'kept')
  (old/'local-config.json').write_text('new-but-not-authoritative');self.assertEqual(data_directory(self.root,True),target);self.assertIn('fake',(target/'local-config.json').read_text())
 def test_failure_keeps_original_and_does_not_publish_partial_copy(self):
  old=self.root/'data';old.mkdir();(old/'local-config.json').write_text('{}');(old/'workspace.sqlite3').write_text('not a sqlite database')
  with self.assertRaises(sqlite3.Error):data_directory(self.root,True)
  self.assertTrue((old/'local-config.json').exists());self.assertFalse((self.base/'profile'/'FreelanceDesk'/'data').exists())
 def test_all_sqlite_handles_closed_before_folder_rename(self):
  old=self.root/'data';old.mkdir()
  with sqlite3.connect(old/'workspace.sqlite3') as db:db.execute('CREATE TABLE sample(value TEXT)')
  original_connect=sqlite3.connect;original_rename=Path.rename;handles=[]
  class Tracked:
   def __init__(self,*args,**kwargs):self.db=original_connect(*args,**kwargs);self.closed=False;handles.append(self)
   def __enter__(self):self.db.__enter__();return self
   def __exit__(self,*args):return self.db.__exit__(*args)
   def backup(self,destination):return self.db.backup(destination.db)
   def close(self):self.db.close();self.closed=True
  def rename(path,target):
   self.assertTrue(handles);self.assertTrue(all(h.closed for h in handles));return original_rename(path,target)
  with patch('data_store.sqlite3.connect',side_effect=Tracked),patch.object(Path,'rename',rename):copy_data(old,self.base/'destination')
 def test_permission_failure_uses_original_data(self):
  old=self.root/'data';old.mkdir();(old/'local-config.json').write_text('{}')
  with patch('data_store.copy_data',side_effect=PermissionError('blocked')):self.assertEqual(data_directory(self.root,True),old)
 def test_selected_drive_saved_across_install_folders(self):
  old=self.root/'data';old.mkdir();(old/'local-config.json').write_text('{"saved":"fake"}')
  target=self.base/'drive-d'/'FreelanceDeskData';choose_directory(target,self.root,True,source=old)
  self.assertEqual(data_directory(self.root,True),target);self.assertEqual(data_directory(self.base/'another-install',True),target)
  self.assertEqual((target/'local-config.json').read_text(),(old/'local-config.json').read_text())
 def test_nested_target_rejected_and_original_preserved(self):
  old=self.root/'data';old.mkdir();(old/'file').write_text('kept')
  with self.assertRaises(RuntimeError):copy_data(old,old/'nested')
  self.assertEqual((old/'file').read_text(),'kept')
 def test_same_google_credentials_keep_saved_session(self):
  with patch.dict(os.environ,{'FREELANCE_DATA_DIR':str(self.base/'gmail')}):
   upwork_mail.save({'clientId':'test.apps.googleusercontent.com','clientSecret':'fake','refreshToken':'saved-fake','lastSync':'kept'})
   upwork_mail.configure({'clientId':'test.apps.googleusercontent.com','clientSecret':'fake'})
   self.assertTrue(upwork_mail.status()['connected']);self.assertEqual(upwork_mail.private()['lastSync'],'kept')
   upwork_mail.configure({'clientId':'other.apps.googleusercontent.com','clientSecret':'fake'})
   self.assertFalse(upwork_mail.status()['connected'])

if __name__=='__main__':unittest.main()

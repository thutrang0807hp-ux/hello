import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import uninstall_desk as uninstall

class UninstallTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'app';self.root.mkdir();self.env=patch.dict(os.environ,{},clear=True);self.env.start()
  (self.root/'uninstall-files.json').write_text(json.dumps({'files':['server.py','uninstall-files.json']}));(self.root/'server.py').write_text('app');(self.root/'personal-notes.txt').write_text('keep')
  self.data=self.root/'data';self.data.mkdir();(self.data/'local-config.json').write_text(json.dumps({'FREELANCE_AI_KEY':'fake'}));(self.data/'own-document.txt').write_text('keep')
 def tearDown(self):self.env.stop();self.tmp.cleanup()
 def test_preview_does_not_delete_and_known_only_removal_keeps_other_files(self):
  preview=uninstall.plan(self.root);self.assertTrue((self.root/'server.py').exists());self.assertIn(self.data/'local-config.json',preview['files'])
  with patch.object(uninstall,'stop_instances'):self.assertEqual(uninstall.remove(preview),[])
  self.assertFalse((self.data/'local-config.json').exists());self.assertEqual((self.data/'own-document.txt').read_text(),'keep');self.assertEqual((self.root/'personal-notes.txt').read_text(),'keep')
 def test_must_stop_server_before_any_file_deletion(self):
  preview=uninstall.plan(self.root)
  with patch.object(uninstall,'stop_instances',side_effect=RuntimeError('running')):
   with self.assertRaises(RuntimeError):uninstall.remove(preview)
  self.assertTrue((self.root/'server.py').exists());self.assertTrue((self.data/'local-config.json').exists())
 def test_path_traversal_rejected(self):
  (self.root/'uninstall-files.json').write_text(json.dumps({'files':['../outside.txt']}))
  with self.assertRaises(RuntimeError):uninstall.plan(self.root)
 def test_unknown_selected_folder_not_deleted(self):
  other=Path(self.tmp.name)/'other';other.mkdir();(other/'local-config.json').write_text('{"otherApp":"keep"}')
  (self.root/'.storage-location.json').write_text(json.dumps({'directory':str(other)}));preview=uninstall.plan(self.root)
  self.assertNotIn(other/'local-config.json',preview['files']);self.assertTrue(preview['notes'])
 def test_symlink_to_other_files_not_selected(self):
  other=Path(self.tmp.name)/'other.py';other.write_text('keep');(self.root/'server.py').unlink();(self.root/'server.py').symlink_to(other)
  self.assertNotIn(self.root/'server.py',uninstall.plan(self.root)['files'])

if __name__=='__main__':unittest.main()

import tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from install_desktop import ensure_environment

class DesktopInstallTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.env=self.root/'.desktop-venv';self.python=self.env/'Scripts'/'python.exe';self.pythonw=self.env/'Scripts'/'pythonw.exe'
 def tearDown(self):self.tmp.cleanup()
 def existing(self):
  self.python.parent.mkdir(parents=True);self.python.write_text('existing');self.pythonw.write_text('running executable - keep')
 def test_healthy_environment_never_recreates_running_pythonw(self):
  self.existing();run=Mock(return_value=SimpleNamespace(returncode=0));self.assertEqual(ensure_environment(self.root,run),self.python)
  self.assertEqual(run.call_count,1);self.assertNotIn('venv',run.call_args.args[0]);self.assertEqual(self.pythonw.read_text(),'running executable - keep')
 def test_first_install_creates_environment_once(self):
  run=Mock();self.assertEqual(ensure_environment(self.root,run),self.python);self.assertIn('venv',run.call_args.args[0]);self.assertEqual(run.call_count,1)
 def test_invalid_environment_is_not_overwritten(self):
  self.existing();run=Mock(return_value=SimpleNamespace(returncode=1))
  with self.assertRaisesRegex(RuntimeError,'không chạy được'):ensure_environment(self.root,run)
  self.assertEqual(self.pythonw.read_text(),'running executable - keep');self.assertEqual(run.call_count,1)
 def test_partial_install_preserves_files_and_never_recreates(self):
  self.env.mkdir();(self.env/'partial').write_text('keep');run=Mock()
  with self.assertRaisesRegex(RuntimeError,'cài dở'):ensure_environment(self.root,run)
  run.assert_not_called();self.assertEqual((self.env/'partial').read_text(),'keep')
 def test_linked_environment_not_modified(self):
  other=self.root/'other';other.mkdir();self.env.symlink_to(other,target_is_directory=True);run=Mock()
  with self.assertRaisesRegex(RuntimeError,'liên kết'):ensure_environment(self.root,run)
  run.assert_not_called()

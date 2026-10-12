import json,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
import desktop_background as desktop

class DesktopServerIdentityTests(unittest.TestCase):
 def setUp(self):self.item={'pid':100,'launcherPid':100,'port':8000,'token':'fake-private-control-token'}
 def test_windows_redirector_pid_differs_and_actual_pid_is_saved(self):
  with patch.object(desktop,'request',return_value={'ok':True,'pid':200}):
   self.assertFalse(desktop.alive(self.item));self.assertTrue(desktop.adopt_server_pid(self.item));self.assertTrue(desktop.alive(self.item))
  self.assertEqual(self.item['pid'],200);self.assertEqual(self.item['launcherPid'],100)
 def test_unauthenticated_or_malformed_response_cannot_adopt_pid(self):
  for value in [{'pid':200},{'ok':False,'pid':200},{'ok':True,'pid':True},{'ok':True,'pid':-1},{'ok':True,'pid':'200'},None]:
   with patch.object(desktop,'request',return_value=value):self.assertFalse(desktop.adopt_server_pid(self.item))
   self.assertEqual(self.item['pid'],100)
 def test_bad_token_does_not_authorize_any_instance(self):
  with patch.object(desktop,'request',side_effect=OSError('403')):self.assertFalse(desktop.adopt_server_pid(self.item));self.assertFalse(desktop.alive(self.item))
 def test_saved_identity_still_requires_actual_pid_match(self):
  with patch.object(desktop,'request',return_value={'ok':True,'pid':201}):self.assertFalse(desktop.alive(self.item))
 def test_start_publishes_actual_pid_and_reuses_authenticated_instance(self):
  with tempfile.TemporaryDirectory() as tmp:
   folder=Path(tmp);process=Mock(pid=100);process.poll.return_value=None
   def request(port,path,token='',body=None):
    if path=='/api/auth':raise OSError('no server before launch')
    self.assertTrue(token);return {'ok':True,'pid':200}
   with patch.object(desktop,'load'),patch.object(desktop,'data_directory',return_value=folder),patch.object(desktop,'request',side_effect=request),patch.object(desktop.subprocess,'Popen',return_value=process) as popen:
    item=desktop.start(open_browser=False);again=desktop.start(open_browser=False)
    self.assertEqual(item['pid'],200);self.assertEqual(item['launcherPid'],100);self.assertEqual(again,item);popen.assert_called_once();process.terminate.assert_not_called()
    self.assertEqual(json.loads((folder/'desktop-server.json').read_text())['pid'],200)

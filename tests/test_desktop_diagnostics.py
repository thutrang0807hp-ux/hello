import unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
from desktop_diagnostics import require_runtime,MissingWebView,MissingNet,windows_runtime,safe_error
from desktop_app import DesktopController

class DesktopDiagnosticsTests(unittest.TestCase):
 def test_missing_webview_has_specific_repair(self):
  with self.assertRaisesRegex(MissingWebView,'repair-webview2'):require_runtime({'webview2':None,'netRelease':528040})
 def test_missing_net_not_mislabeled_as_port_conflict(self):
  with self.assertRaisesRegex(MissingNet,'NET Framework'):require_runtime({'webview2':'130.0.1.0','netRelease':None})
 def test_runtime_sufficient(self):require_runtime({'webview2':'130.0.1.0','netRelease':528040})
 def test_failed_initialization_does_not_call_uninitialized_window_destroy(self):
  window=Mock();stop=Mock();app=DesktopController(window,stop,ready=False);app.tray=Mock();app.quit();stop.assert_called_once();app.tray.stop.assert_called_once();window.destroy.assert_not_called()
 def test_report_redacts_credentials(self):
  secret='sk-proj-'+'a'*40
  result=safe_error(RuntimeError(secret+' Bearer hiddenaccess token=private refresh_secret=hidden'))
  self.assertNotIn(secret,result);self.assertNotIn('hiddenaccess',result);self.assertNotIn('private',result);self.assertNotIn('hidden',result)
 def test_registry_checks_both_views_and_user_machine(self):
  class Key:
   def __init__(self,hive,path,view):self.hive,self.path,self.view=hive,path,view
   def __enter__(self):return self
   def __exit__(self,*_):pass
  def open_key(hive,path,reserved,access):
   if 'EdgeUpdate' in path and (hive,access)!=(1,34):raise FileNotFoundError()
   return Key(hive,path,access)
  def query(key,name):return ('130.0.1.0',1) if name=='pv' else (528040,1)
  registry=SimpleNamespace(HKEY_CURRENT_USER=1,HKEY_LOCAL_MACHINE=2,KEY_WOW64_32KEY=32,KEY_WOW64_64KEY=64,KEY_READ=2,OpenKey=Mock(side_effect=open_key),QueryValueEx=query)
  self.assertEqual(windows_runtime(registry),{'webview2':'130.0.1.0','netRelease':528040});self.assertEqual(registry.OpenKey.call_count,6)

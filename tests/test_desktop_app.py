import unittest
from unittest.mock import Mock, patch
from desktop_app import DesktopController, DesktopAPI


class DesktopLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.window=Mock();self.stop=Mock();self.app=DesktopController(self.window,self.stop)
    def test_close_hides_without_stopping(self):
        self.app.tray=Mock()
        self.assertFalse(self.app.closing());self.window.hide.assert_called_once();self.stop.assert_not_called();self.window.destroy.assert_not_called()
    def test_reopen_restores_window(self):
        self.app.show();self.window.show.assert_called_once();self.window.restore.assert_called_once()
    def test_explicit_exit_stops_once(self):
        self.app.tray=Mock();self.app.quit();self.app.quit()
        self.stop.assert_called_once();self.app.tray.stop.assert_called_once();self.window.destroy.assert_called_once();self.assertTrue(self.app.closing())
    def test_missing_tray_exits_instead_of_hiding_forever(self):
        self.assertTrue(self.app.closing());self.stop.assert_called_once();self.window.hide.assert_not_called();self.window.destroy.assert_called_once()
    def test_stop_failure_still_releases_ui(self):
        self.stop.side_effect=OSError('test');self.app.tray=Mock()
        with patch('desktop_background.message') as message:self.app.quit();message.assert_called_once()
        self.app.tray.stop.assert_called_once();self.window.destroy.assert_called_once()
    def test_google_opens_local_browser_no_arbitrary_url(self):
        with patch('desktop_app.webbrowser.open') as browser:
            self.assertEqual(DesktopAPI(8000).open_mail_browser(),{'ok':True})
            browser.assert_called_once_with('http://127.0.0.1:8000/?openMail=1')

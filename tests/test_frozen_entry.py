import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import desktop_background as background
import frozen_entry


class FrozenEntryTests(unittest.TestCase):
    def test_server_mode_does_not_start_desktop(self):
        with patch.object(sys, 'argv', ['FreelanceDesk.exe', '--server']), \
             patch.object(frozen_entry.runpy, 'run_module') as run:
            self.assertEqual(frozen_entry.main(), 0)
            run.assert_called_once_with('server', run_name='__main__')

    def test_frozen_background_relaunches_executable_without_python_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            process = Mock(pid=42)
            process.poll.return_value = None
            def request(port, path, token='', body=None):
                if path == '/api/auth':
                    raise OSError('not running')
                return {'ok': True, 'pid': 42}
            with patch.object(sys, 'frozen', True, create=True), \
                 patch.object(background, 'load'), \
                 patch.object(background, 'data_directory', return_value=Path(tmp)), \
                 patch.object(background, 'request', side_effect=request), \
                 patch.object(background.subprocess, 'Popen', return_value=process) as popen:
                background.start(open_browser=False)
                self.assertEqual(popen.call_args.args[0], [sys.executable, '--server'])

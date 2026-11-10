"""Exercise the actual bundle (Windows CI) or source entry with --source."""
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request


def main():
    root = Path(__file__).resolve().parents[1]
    command = ([sys.executable, str(root / 'frozen_entry.py')]
               if sys.argv[1:] == ['--source'] else [str(Path(sys.argv[1]).resolve())])
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    token = secrets.token_urlsafe(32)
    base = f'http://127.0.0.1:{port}'

    def request(path, body=None, authenticated=False):
        headers = {'Content-Type': 'application/json', 'Origin': base}
        if authenticated:
            headers['X-Desktop-Token'] = token
        req = urllib.request.Request(base + path,
            data=json.dumps(body).encode() if body is not None else None, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as response:
            return response.read()

    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, FREELANCE_DATA_DIR=tmp, FREELANCE_PASSWORD='',
                   FREELANCE_BIND='127.0.0.1', PORT=str(port),
                   FREELANCE_DESKTOP_CONTROL_TOKEN=token)
        for key in ('FREELANCE_AI_KEY', 'FREELANCE_SLACK_TOKEN', 'FREELANCE_TELEGRAM_TOKEN'):
            env.pop(key, None)
        for iteration in range(2):
            process = subprocess.Popen(command + ['--server'], cwd=tmp, env=env,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                for _ in range(200):
                    if process.poll() is not None:
                        raise RuntimeError('Backend exited before readiness')
                    try:
                        status = json.loads(request('/api/desktop/status', authenticated=True))
                        if status.get('ok') and status.get('pid') == process.pid:
                            break
                    except OSError:
                        pass
                    time.sleep(.1)
                else:
                    raise RuntimeError('Backend readiness timed out')
                assert b'<html' in request('/').lower()
                assert b'changeView' in request('/app.js')
                assert request('/style.css')
                try:
                    request('/api/desktop/stop', {}, authenticated=False)
                except urllib.error.HTTPError as error:
                    assert error.code == 403
                else:
                    raise AssertionError('Unauthenticated stop accepted')
                if iteration == 0:
                    record = json.loads(request('/api/records', {'kind': 'client', 'name': 'Bundle smoke'}))
                    assert record['id']
                else:
                    assert b'Bundle smoke' in request('/api/records')
                request('/api/desktop/stop', {}, authenticated=True)
                assert process.wait(timeout=15) == 0
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=10)
        assert (Path(tmp) / 'workspace.sqlite3').is_file()
    print('PASS backend launch, static assets, private-token stop, restart and persisted data.')


if __name__ == '__main__':
    main()

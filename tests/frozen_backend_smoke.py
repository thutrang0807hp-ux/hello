"""Exercise the actual bundle (Windows CI) or source entry with --source."""
import json
from datetime import datetime, timezone
import os
from pathlib import Path
import secrets
import socket
import sqlite3
from contextlib import closing
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

    def request(path, body=None, authenticated=False, extension=False):
        headers = {'Content-Type': 'application/json', 'Origin': base}
        if extension:
            headers['Origin']='chrome-extension://'+'a'*32
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
                    old_date = datetime.fromtimestamp(time.time()-60*86400,timezone.utc).isoformat()
                    old = json.loads(request('/api/records', {'kind':'job','name':'Cleanup fixture','receivedAt':old_date,'status':'Đã lưu'}))
                    protected = json.loads(request('/api/records', {'kind':'job','name':'Keep sent job','receivedAt':old_date,'status':'Đã lưu'}))
                    request('/api/jobs/proposal-sent', {'id':protected['id'],'sent':True})
                    usage = json.loads(request('/api/storage'))
                    assert usage['jobs']['count'] == 2 and usage['databaseBytes'] > 0
                    plan = json.loads(request('/api/storage/preview', {}))
                    assert plan['count'] == 1
                    result = json.loads(request('/api/storage/cleanup', {'confirm':True,'token':plan['token']}))
                    assert result['removed'] == 1 and result['usage']['backupBytes'] > 0
                    assert result['usage']['jobs']['count'] == 1
                    remaining = json.loads(request('/api/records'))
                    assert not any(r['id']==old['id'] for r in remaining)
                    assert any(r['id']==protected['id'] for r in remaining)
                    proposal=json.loads(request('/api/records',{'kind':'proposal','name':'Bridge smoke','workspace':{'version':1,'nodes':[{'id':'job','type':'job','title':'Job','content':'Build dashboard','x':0,'y':0},{'id':'draft','type':'draft','title':'Draft','content':'Original letter','x':100,'y':0}],'edges':[{'from':'job','to':'draft'}]}}))
                    task=json.loads(request('/api/chatgpt/tasks',{'proposalId':proposal['id'],'nodeId':'draft'}))
                    settings=json.loads(request('/api/settings'))
                    bridge='/api/chatgpt-bridge/'+settings['webhookPath'].split('/')[-1]
                    queue=json.loads(request(bridge,extension=True));assert queue['tasks'][0]['id']==task['id']
                    request(bridge,{'id':task['id'],'answer':'Selected letter from fixture'},extension=True)
                    assert json.loads(request('/api/chatgpt/tasks/'+task['id']))['status']=='ready'


                else:
                    assert b'Bundle smoke' in request('/api/records')
                    assert json.loads(request('/api/storage'))['jobs']['count'] == 1
                    assert len(json.loads(request('/api/jobs/history'))) == 1
                    assert json.loads(request('/api/chatgpt/tasks/'+task['id']))['answer']=='Selected letter from fixture'
                request('/api/desktop/stop', {}, authenticated=True)
                assert process.wait(timeout=15) == 0
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=10)
        assert (Path(tmp) / 'workspace.sqlite3').is_file()
        with closing(sqlite3.connect(Path(tmp)/'workspace.sqlite3')) as db:
            tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            assert {'telegram_delivery','telegram_poll'}<=tables
    print('PASS backend launch, assets, storage counts, manual cleanup, safety backup, protected sent job, history, ChatGPT bridge context/result persistence, private-token stop and restart persistence.')


if __name__ == '__main__':
    main()

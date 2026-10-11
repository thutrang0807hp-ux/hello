"""Verify local launcher, private configuration and restart persistence."""
import http.cookiejar
import json
import os
import secrets
import signal
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as data:
    password = secrets.token_urlsafe(24)
    Path(data, 'local-config.json').write_text(json.dumps({'FREELANCE_PASSWORD': password}), encoding='utf-8')
    env = dict(os.environ, FREELANCE_DATA_DIR=data, PORT='8767', BROWSER='/bin/true')
    for key in ['FREELANCE_PASSWORD', 'FREELANCE_AI_KEY', 'FREELANCE_SLACK_TOKEN', 'FREELANCE_TELEGRAM_TOKEN']:
        env.pop(key, None)
    base = 'http://127.0.0.1:8767'
    def start():
        process = subprocess.Popen(['python3', 'run.py'], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(60):
            if process.poll() is not None:
                raise AssertionError('Launcher exited before readiness')
            try:
                with urllib.request.urlopen(base + '/api/auth', timeout=1) as response:
                    assert json.load(response)['required']
                time.sleep(.3)
                return process
            except OSError:
                time.sleep(.1)
        process.terminate()
        raise AssertionError('Launcher not ready')
    def stop(process):
        process.send_signal(signal.SIGINT)
        process.wait(timeout=10)
    def client():
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        def request(path, data=None):
            req = urllib.request.Request(base + path, data=json.dumps(data).encode() if data is not None else None, headers={'Content-Type': 'application/json'})
            with opener.open(req) as response:
                return json.load(response)
        request('/api/login', {'password': password})
        return request
    process = start()
    try:
        request = client()
        created = request('/api/records', {'kind':'client', 'name':'Persistent local customer'})
        webhook_path = request('/api/settings')['webhookPath']
    finally:
        stop(process)
    process = start()
    try:
        request = client()
        assert request('/api/records')[0]['id'] == created['id']
        assert request('/api/records')[0]['name'] == 'Persistent local customer'
        assert request('/api/settings')['webhookPath'] == webhook_path
        print('PASS: desktop launcher starts, reads private local password, cleans up on exit, preserves records and webhook token after restart')
    finally:
        stop(process)

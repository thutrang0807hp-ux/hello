"""Check local bridge + actual app importer without Upwork, AI or notification credentials."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(dir='/tmp') as data:
    env = dict(os.environ, FREELANCE_DATA_DIR=data, FREELANCE_PASSWORD='', FREELANCE_BIND='127.0.0.1', PORT='8771')
    for key in ['FREELANCE_AI_KEY', 'FREELANCE_SLACK_TOKEN', 'FREELANCE_TELEGRAM_TOKEN']:
        env.pop(key, None)
    process = subprocess.Popen(['python', 'server.py'], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                with urllib.request.urlopen('http://127.0.0.1:8771/api/auth', timeout=1) as response:
                    assert response.status == 200
                break
            except OSError:
                if process.poll() is not None: raise RuntimeError('App startup failed')
                time.sleep(.1)
        else: raise RuntimeError('App not ready')
        token = (Path(data)/'webhook-token').read_text().strip()
        test_env = dict(env, TOOLKIT_TEST_WEBHOOK='http://127.0.0.1:8771/api/webhook/'+token)
        subprocess.run(['node','tests/toolkit_bridge_smoke.mjs'], cwd=ROOT, env=test_env, check=True)
        with urllib.request.urlopen('http://127.0.0.1:8771/api/records') as response:
            result = json.load(response)
        rows = result if isinstance(result,list) else result['records']
        jobs = [row for row in rows if row['kind']=='job']
        assert len(jobs)==1, len(jobs)
        assert jobs[0]['externalId']=='~0123456789abcdef'
        assert jobs[0]['budget']=='$25–$40/hr'
        assert len(jobs[0]['notes'])>2000
        assert jobs[0]['clientInfo']['totalHires']==5
        assert jobs[0]['postedAt']=='2026-10-10T15:30:00.000Z'
        print('PASS normalized full description, hourly budget, client info and source timestamp persisted')
    finally:
        process.terminate()
        process.wait(timeout=10)

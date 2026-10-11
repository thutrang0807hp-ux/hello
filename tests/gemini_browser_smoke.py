"""Gemini settings and on-demand scoring in the real UI; provider responses are mocked."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import urllib.request
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CODE = '''
import json
import services, job_radar
assessment = {'summary':'Design a dashboard','priceComment':'Confirm scope','clarityComment':'Clear goal','riskComment':'No guarantees',
              'warnings':[],'budgetScore':20,'clarityScore':15,'safetyScore':12}
def fake(url, payload, headers):
    assert url.startswith('https://generativelanguage.googleapis.com/')
    assert 'responseJsonSchema' in payload['generationConfig']
    return {'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(assessment)}]}}]}
job_radar.post_json = fake
import server
import threading
threading.Thread(target=server.job_worker,daemon=True).start()
server.ThreadingHTTPServer((server.BIND,8772),server.Handler).serve_forever()
'''

def navigate(page, name):
    page.locator('#appSidebar').hover()
    page.wait_for_function("()=>document.querySelector('#appSidebar').getBoundingClientRect().width>=244")
    page.locator('[data-view='+name+']').click()
    page.mouse.move(1000, 100)

with tempfile.TemporaryDirectory(dir='/tmp') as data:
    env = dict(os.environ, FREELANCE_DATA_DIR=data, PORT='8772', FREELANCE_BIND='127.0.0.1', FREELANCE_PASSWORD='',
               FREELANCE_AI_PROVIDER='gemini', FREELANCE_AI_KEY='mock-key', FREELANCE_AI_MODEL='', FREELANCE_AI_AUTO_JOBS='')
    for key in ['FREELANCE_SLACK_TOKEN','FREELANCE_TELEGRAM_TOKEN']:
        env.pop(key,None)
    process=subprocess.Popen(['python','-c',CODE],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                urllib.request.urlopen('http://127.0.0.1:8772/api/auth',timeout=1).close();break
            except OSError:
                if process.poll() is not None:raise RuntimeError('Server stopped')
                time.sleep(.1)
        else:raise RuntimeError('Server not ready')
        token=(Path(data)/'webhook-token').read_text().strip()
        body=json.dumps({'event':'new_jobs','jobs':[{'id':'gemini-ui-test','title':'UI dashboard','url':'https://www.upwork.com/jobs/~123','description':'Design a dashboard','budget':'$800'}]}).encode()
        req=urllib.request.Request('http://127.0.0.1:8772/api/webhook/'+token,data=body,headers={'Content-Type':'application/json'})
        urllib.request.urlopen(req).close()
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1000})
            page.goto('http://127.0.0.1:8772')
            navigate(page,'settings')
            page.get_by_text('AI · Gemini · gemini-2.5-flash',exact=True).wait_for()
            page.get_by_text('Đã cấu hình · chấm job khi bấm Đánh giá',exact=True).wait_for()
            navigate(page,'job')
            page.locator('[data-job-detail]').first.click()
            page.get_by_role('button',name='Đánh giá bằng AI',exact=True).click()
            page.locator('[data-job-detail]').first.click()
            page.locator('.job-popover').get_by_text('Design a dashboard',exact=True).wait_for()
            assert 'mock-key' not in page.locator('body').inner_text()
            print('PASS Gemini provider/model shown, on-demand scoring button completes in real UI, key hidden')
            browser.close()
    finally:
        process.terminate();process.wait(timeout=10)

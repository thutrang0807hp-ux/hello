"""Verify tab counts and actual read persistence; no external services used."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import urllib.request
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(dir='/tmp') as data:
    env=dict(os.environ,FREELANCE_DATA_DIR=data,FREELANCE_PASSWORD='',FREELANCE_BIND='127.0.0.1',PORT='8774')
    for key in ['FREELANCE_AI_KEY','FREELANCE_SLACK_TOKEN','FREELANCE_TELEGRAM_TOKEN']:env.pop(key,None)
    process=subprocess.Popen(['python','server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:urllib.request.urlopen('http://127.0.0.1:8774/api/auth',timeout=1).close();break
            except OSError:
                if process.poll() is not None:raise RuntimeError('Server stopped')
                time.sleep(.1)
        token=Path(data,'webhook-token').read_text().strip()
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1000});page.goto('http://127.0.0.1:8774')
            page.wait_for_function("()=>initialized")
            assert page.title()=='Freelance Desk'
            body=json.dumps({'event':'new_jobs','jobs':[{'id':'tab-'+str(i),'title':'Job '+str(i),'url':'https://www.upwork.com/jobs/~test','description':'Description'} for i in range(3)]}).encode()
            req=urllib.request.Request('http://127.0.0.1:8774/api/webhook/'+token,data=body,headers={'Content-Type':'application/json'})
            urllib.request.urlopen(req).close()
            page.evaluate('refresh()')
            assert page.title()=='(3) Freelance Desk'
            assert page.locator('#unreadTabIcon').get_attribute('href').endswith('unread=3')
            with urllib.request.urlopen('http://127.0.0.1:8774/favicon.svg?unread=3') as r:
                svg=r.read().decode();assert '#e53935' in svg and '>3</text>' in svg
            page.locator('#appSidebar').hover();page.wait_for_function("()=>document.querySelector('#appSidebar').getBoundingClientRect().width>=244")
            page.locator('[data-view=job]').click();page.mouse.move(1000,100)
            page.wait_for_function('()=>tabUnread===0')
            assert page.title()=='Freelance Desk'
            page.reload();page.wait_for_function('()=>initialized');assert page.title()=='Freelance Desk'
            body=json.dumps({'event':'new_jobs','jobs':[{'id':'tab-later','title':'Later job','url':'https://www.upwork.com/jobs/~later','description':'New arrival'}]}).encode()
            urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8774/api/webhook/'+token,data=body,headers={'Content-Type':'application/json'})).close()
            page.evaluate('refresh()');page.wait_for_function('()=>tabUnread===1')
            page.evaluate("changeView('job')");page.wait_for_function('()=>tabUnread===0')
            with urllib.request.urlopen('http://127.0.0.1:8774/favicon.svg?unread=120') as r:assert '>99+</text>' in r.read().decode()
            with urllib.request.urlopen('http://127.0.0.1:8774/favicon.svg?unread=%3Cscript%3E') as r:assert '#e53935' not in r.read().decode()
            print('PASS red tab icon/count, opening job feed clears existing unread jobs, persists after reload, 99+ and invalid input')
            browser.close()
    finally:process.terminate();process.wait(timeout=10)

"""Real settings UI: storage counters, preview, cancel and confirmed cleanup with temp data."""
import os
import sys
import json
import tempfile
import threading
import time
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright

with tempfile.TemporaryDirectory() as tmp:
    os.environ.update(FREELANCE_DATA_DIR=tmp,FREELANCE_PASSWORD='')
    for key in ('FREELANCE_AI_KEY','FREELANCE_SLACK_TOKEN','FREELANCE_TELEGRAM_TOKEN'):
        os.environ.pop(key,None)
    import server
    with server.connect() as db:
        for name,sent in [('Old unneeded job',False),('Sent proposal job',True)]:
            job={'name':name,'receivedAt':datetime.fromtimestamp(time.time()-60*86400,timezone.utc).isoformat(),'proposalSent':sent,'status':'Đã lưu'}
            db.execute("INSERT INTO records(kind,body) VALUES('job',?)",(json.dumps(job),))
        db.execute("INSERT INTO records(kind,body) VALUES('sentproposal',?)",(json.dumps({'name':'Keep proposal','body':'A real fixture'}),))
        db.execute("INSERT INTO upwork_mail(id,body) VALUES('smoke-mail',?)",(json.dumps({'subject':'Keep mail'}),))
    http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
    threading.Thread(target=http.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{http.server_port}'
    try:
        with sync_playwright() as p:
            b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
            page=b.new_page(viewport={'width':1440,'height':1100})
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(base);page.wait_for_function('()=>initialized')
            page.evaluate("changeView('settings')")
            page.locator('#storagePanel summary').click()
            page.wait_for_selector('[data-storage-preview]')
            assert '2 ·' in page.locator('[data-storage-usage]').inner_text()
            page.locator('[data-storage-preview]').click()
            page.wait_for_selector('[data-storage-confirm]')
            assert '1 job quá hạn' in page.locator('[data-storage-plan]').inner_text()
            assert page.request.get(base+'/api/storage').json()['jobs']['count']==2
            page.locator('[data-storage-cancel]').click()
            assert page.request.get(base+'/api/storage').json()['jobs']['count']==2
            page.locator('[data-storage-preview]').click();page.wait_for_selector('[data-storage-confirm]')
            page.locator('[data-storage-confirm]').click()
            page.wait_for_function("()=>document.querySelector('[data-storage-plan]').textContent.includes('Đã dọn 1 job')")
            usage=page.request.get(base+'/api/storage').json()
            assert usage['jobs']['count']==1 and usage['letters']['count']==1 and usage['mail']['count']==1
            assert usage['backupBytes']>0
            Path('/workspace/exports').mkdir(exist_ok=True)
            page.locator('#storagePanel').screenshot(path='/workspace/exports/storage-settings.png')
            page.reload();page.wait_for_function('()=>initialized');page.evaluate("changeView('settings')")
            page.locator('#storagePanel summary').click()
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            assert '1 ·' in page.locator('[data-storage-usage]').inner_text()
            assert not errors,errors
            b.close()
        print('PASS storage settings, counts, actual file sizes, preview/cancel/confirm, backup, protected job/mail/proposal, reload/mobile.')
    finally:http.shutdown();http.server_close()

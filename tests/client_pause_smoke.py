import os,sys,tempfile,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as tmp:
 os.environ.update(FREELANCE_DATA_DIR=tmp,FREELANCE_PASSWORD='')
 import server
 with server.connect() as db:db.execute("INSERT INTO records(kind,body) VALUES ('client',?)",(json.dumps({'name':'Nick','clientGroup':'active','clientStage':'working','lastReplyDate':'2026-09-23'}),))
 http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);threading.Thread(target=http.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{http.server_port}'
 try:
  with sync_playwright() as p:
   b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1400,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base);page.wait_for_function('()=>initialized');page.evaluate("changeView('client')")
   page.locator('[data-client-stage]').select_option('paused');page.wait_for_selector('[data-client-pause-note]');page.locator('[data-client-pause-reason]').select_option('unresponsive');page.locator('[data-client-pause-note]').fill('Đã nhắc hai lần, giữ hợp đồng mở.');page.locator('[data-client-pause-save]').click();page.wait_for_function("()=>records[0].clientPauseNote==='Đã nhắc hai lần, giữ hợp đồng mở.'")
   row=page.request.get(base+'/api/records').json()[0];paused_at=row['clientPausedAt'];assert row['clientGroup']=='active';assert row['clientPauseReason']=='unresponsive'
   page.reload();page.wait_for_function('()=>initialized');page.evaluate("changeView('client')");page.wait_for_selector('.client-pause-box');assert page.locator('[data-client-pause-note]').input_value()=='Đã nhắc hai lần, giữ hợp đồng mở.'
   server.upwork_mail.store(server.connect,{'id':'new-message','room':'room_nick','sender':'Nick','project':'Editing','text':'Hello again','receivedAt':'2026-10-12T10:00:00+07:00','source':'eml'})
   page.request.post(base+'/api/mail/link',data={'id':'new-message','clientId':row['id']});page.evaluate('refresh()');page.wait_for_timeout(200);assert page.locator('[data-client-stage]').input_value()=='paused';assert page.locator('[data-client-pause-reason]').input_value()=='unresponsive'
   page.screenshot(path='/workspace/exports/client-pause-preview.png');page.evaluate("document.documentElement.dataset.theme='dark'");page.screenshot(path='/workspace/exports/client-pause-dark-preview.png')
   page.locator('[data-client-stage]').select_option('working');page.wait_for_function("()=>records[0].clientStage==='working'");assert page.locator('.client-pause-box').count()==0
   row=page.request.get(base+'/api/records').json()[0];assert row['clientGroup']=='active';assert row['clientPausedAt']==paused_at;assert row['clientResumedAt'];assert not errors,errors
   b.close();print('PASS pause reason/note saved, reload persists, active group retained after mail, resume hides controls and keeps history, light/dark.')
 finally:http.shutdown();http.server_close()

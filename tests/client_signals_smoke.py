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
   assert page.locator('.client-signal.green').count()==1
   page.locator('[data-client-stage]').select_option('paused');page.wait_for_selector('.client-signal.red')
   with server.connect() as db:db.execute("INSERT INTO records(kind,body) VALUES ('client',?)",(json.dumps({'name':'Test Client','clientGroup':'talk','clientStage':'chatting'}),))
   page.evaluate('refresh()');page.wait_for_selector('.talk .client-signal.red')
   page.locator('.talk [data-client-stage]').select_option('testing');page.wait_for_selector('[data-client-test-today]');assert page.locator('.talk .client-signal.yellow').count()==1
   page.locator('[data-client-test-today]').click();page.wait_for_function("()=>records.some(c=>c.clientTestSentDate===Clients.day())")
   page.reload();page.wait_for_function('()=>initialized');page.evaluate("changeView('client')");page.wait_for_selector('[data-client-test-date]');assert page.locator('[data-client-test-date]').input_value()
   row=next(c for c in page.request.get(base+'/api/records').json() if c['name']=='Test Client')
   from datetime import datetime,timedelta
   from client_lifecycle import LOCAL_ZONE
   old=(datetime.now(LOCAL_ZONE).date()-timedelta(days=14)).isoformat()
   page.request.post(base+'/api/records',data={'id':row['id'],'kind':'client','name':row['name'],'clientTestSentDate':old})
   page.evaluate('refresh()');page.wait_for_selector('.archive [data-client-reopen]');assert page.locator('.archive .client-archive-reason').inner_text()=='Đã gửi test nhưng khách chưa phản hồi sau 14 ngày.'
   assert page.locator('.active .client-signal.red').count()==1
   page.locator('[data-client-reopen]').click();page.wait_for_selector('.talk [data-client-stage]');row=next(c for c in page.request.get(base+'/api/records').json() if c['name']=='Test Client');assert row['clientTestSentDate']=='';assert row['clientGroup']=='talk'
   assert not errors,errors
   b.close();print('PASS stage color labels, test sent date persists after reload, 14-day archive, active pause retained, reopening clears old timer.')
 finally:http.shutdown();http.server_close()

import os,sys,tempfile,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as tmp:
 os.environ.update(FREELANCE_DATA_DIR=tmp,FREELANCE_PASSWORD='')
 import server
 with server.connect() as db:
  ident=db.execute("INSERT INTO records(kind,body) VALUES('client',?)",(json.dumps({'name':'John L.','clientGroup':'active','clientStage':'working','mailNextAction':'Dựng hai video từ footage khách gửi.','nextAction':'Dựng hai video từ footage khách gửi.','nextActionSource':'mail-ai','mailTaskSignature':'first'}),)).lastrowid
  db.execute('INSERT INTO mail_action_reviews VALUES (?,?,?)',(ident,'first',json.dumps({'state':'completed','decision':'update','action':'Dựng hai video từ footage khách gửi.'})))
 http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);threading.Thread(target=http.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{http.server_port}'
 try:
  with sync_playwright() as p:
   b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1500,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base);page.wait_for_function('()=>initialized');page.evaluate("changeView('overview')")
   page.wait_for_selector('[data-overview-ai-done]');assert page.locator('.dashboard-focus').bounding_box()['y']<page.locator('#overviewTasks').bounding_box()['y'];assert page.locator('.overview-daily-mail').count()==0
   assert 'Chưa gán hạn' in page.locator('.today-action-row').inner_text()
   Path('/workspace/exports').mkdir(exist_ok=True);page.locator('.overview-action-column').screenshot(path='/workspace/exports/overview-actions-preview.png')
   page.locator('[data-overview-ai-done]').click();page.wait_for_selector('[data-overview-ai-done]',state='detached');page.reload();page.wait_for_function('()=>initialized');page.evaluate("changeView('overview')");assert page.locator('[data-overview-ai-done]').count()==0
   with server.connect() as db:db.execute('UPDATE mail_action_reviews SET signature=?,body=? WHERE client_id=?',('thanks',json.dumps({'state':'completed','decision':'keep'}),ident))
   page.evaluate('refresh()');page.wait_for_timeout(100);assert page.locator('[data-overview-ai-done]').count()==0
   page.request.post(base+'/api/records',data={'id':ident,'kind':'client','name':'John L.','mailTaskSignature':'new-request'});page.evaluate('refresh()');page.wait_for_selector('[data-overview-ai-done]')
   page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors;b.close();print('PASS weekly first, compact AI task, no invented date, completion persists, thanks stays completed, new request appears, mobile.')
 finally:http.shutdown();http.server_close()

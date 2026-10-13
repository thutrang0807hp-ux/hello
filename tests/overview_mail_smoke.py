import os,sys,tempfile,threading,json
from pathlib import Path
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as tmp:
 os.environ.update(FREELANCE_DATA_DIR=tmp,FREELANCE_PASSWORD='')
 import server
 from client_lifecycle import LOCAL_ZONE
 now=datetime.now(LOCAL_ZONE).isoformat()
 with server.connect() as db:client_id=db.execute("INSERT INTO records(kind,body) VALUES('client',?)",(json.dumps({'name':'John L.','clientGroup':'active','clientStage':'working'}),)).lastrowid
 def mail(ident,sender,text):return {'id':ident,'room':'room_'+ident,'sender':sender,'project':'Video Editing','text':text,'receivedAt':now,'source':'eml'}
 server.upwork_mail.store(server.connect,mail('one','John L.','Please edit two new videos.'))
 server.upwork_mail.link(server.connect,{'id':'one','clientId':client_id})
 http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);threading.Thread(target=http.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{http.server_port}'
 try:
  with sync_playwright() as p:
   b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1450,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base);page.wait_for_function('()=>initialized');page.evaluate("changeView('overview')")
   page.wait_for_selector('[data-overview-message="one"]');assert page.locator('#weeklyFocusTitle').is_visible();assert page.locator('[data-overview-message="one"]').inner_text().find('John L.')>=0
   summary=page.request.get(base+'/api/mail/summary').json();assert summary['unreadCount']==1 and summary['todayCount']==1
   assert page.locator('.overview-daily-mail').bounding_box()['y']<page.locator('.dashboard-focus').bounding_box()['y']
   server.upwork_mail.store(server.connect,mail('two','Emma K.','Can you do a test?'))
   page.evaluate('refresh(true)');page.wait_for_selector('[data-overview-message="two"]')
   page.locator('[data-overview-message="one"]').click();page.wait_for_selector('[data-mail-read="one"][open]');page.wait_for_function("()=>pendingMail.unreadCount===1");assert page.locator('#upworkMailDialog').is_visible()
   page.locator('#closeUpworkMail').click();page.wait_for_selector('[data-overview-message="one"]',state='detached')
   page.locator('[data-overview-message="two"]').click();page.wait_for_function("()=>pendingMail.unreadCount===0");assert page.request.get(base+'/api/mail/summary').json()['count']==1
   page.locator('#closeUpworkMail').click();assert page.locator('[data-overview-message="two"]').count()==1
   page.locator('[data-overview-mail-filter="pending"]').click();page.wait_for_selector('[data-mail-filter="pending"].selected');page.locator('#closeUpworkMail').click()
   Path('/workspace/exports').mkdir(exist_ok=True);page.locator('.overview-action-column').screenshot(path='/workspace/exports/overview-today-preview.png');page.evaluate("document.documentElement.dataset.theme='dark'");page.locator('.overview-action-column').screenshot(path='/workspace/exports/overview-today-dark-preview.png')
   page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors
   b.close();print('PASS overview daily/weekly, unread preview without auto-read, live unlinked refresh, direct message opening, pending stays after read, filters, mobile.')
 finally:http.shutdown();http.server_close()

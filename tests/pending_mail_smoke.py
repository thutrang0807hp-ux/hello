import os,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as tmp:
 os.environ.update(FREELANCE_DATA_DIR=tmp,FREELANCE_PASSWORD='')
 import server
 server.upwork_mail.store(server.connect,{'id':'pending1','room':'room_1','sender':'John','project':'Editing','text':'Message','receivedAt':'2026-10-12T09:00:00+07:00','source':'eml'})
 http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);threading.Thread(target=http.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.add_init_script("window.notificationCalls=[];window.Notification=class {static permission='granted';constructor(title,options){window.notificationCalls.push({title,options})}close(){}}")
   page.goto(f'http://127.0.0.1:{http.server_port}');page.wait_for_function('()=>initialized');assert page.locator('#pendingMailJump').count()==1;assert page.evaluate('notificationCalls.length')==1
   page.evaluate('refresh(true)');page.wait_for_timeout(200);assert page.evaluate('notificationCalls.length')==1
   page.locator('#pendingMailJump').click();page.wait_for_selector('#upworkMailDialog[open]');assert page.locator('[data-mail-filter=pending]').get_attribute('aria-pressed')=='true'
   page.locator('[data-mail-read] summary').click();page.wait_for_timeout(200);assert page.locator('#pendingMailJump').count()==1 # Reading isn't linking.
   page.locator('[data-mail-client]').select_option('new');page.locator('[data-mail-link]').click();page.wait_for_function("()=>!document.querySelector('#pendingMailJump')")
   assert page.locator('.pending-mail-nav-count').count()==0;assert not errors,errors;browser.close();print('PASS pending alert and notification once, jump to pending, reading keeps warning, linking clears count.')
 finally:http.shutdown();http.server_close()

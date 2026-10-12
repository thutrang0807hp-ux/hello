import os,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as tmp:
 os.environ.update(FREELANCE_DATA_DIR=tmp,FREELANCE_PASSWORD='')
 import server
 server.import_jobs({'event':'new_jobs','jobs':[{'id':'one','title':'Job','url':'https://www.upwork.com/jobs/~one','description':'Description'}]})
 server.upwork_mail.store(server.connect,{'id':'mail1','room':'room_one','sender':'John','project':'Editing','text':'New project','receivedAt':'2026-10-12T09:00:00+07:00','source':'eml'})
 http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);threading.Thread(target=http.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as p:
   b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1400,'height':950});page.goto(f'http://127.0.0.1:{http.server_port}');page.wait_for_function('()=>initialized')
   assert page.title()=='(1 job · 1 tin) Freelance Desk';assert page.locator('#unreadTabIcon').get_attribute('href').endswith('unread=2')
   page.locator('#unreadMailJump').click();page.wait_for_selector('#upworkMailDialog[open]');assert page.locator('[data-mail-filter=new]').get_attribute('aria-pressed')=='true'
   page.locator('[data-mail-read] summary').click();page.wait_for_timeout(200);assert page.title()=='(1 job · 1 tin) Freelance Desk' # Pending remains after reading.
   page.locator('[data-mail-client]').select_option('new');page.locator('[data-mail-link]').click();page.wait_for_function("()=>document.title==='(1 job) Freelance Desk'")
   page.keyboard.press('Escape');page.evaluate("changeView('job')");page.wait_for_function("()=>document.title==='Freelance Desk'")
   # Linked but unread mail still contributes, without needing pending status.
   server.upwork_mail.store(server.connect,{'id':'mail2','room':'room_one','sender':'John','project':'Editing','text':'A new request','receivedAt':'2026-10-12T10:00:00+07:00','source':'eml'})
   page.evaluate('refresh()');page.wait_for_function("()=>document.title==='(1 tin) Freelance Desk'");assert page.locator('#pendingMailJump').count()==0
   page.locator('#unreadMailJump').click();page.locator('[data-mail-read] summary').click();page.wait_for_function("()=>document.title==='Freelance Desk'")
   b.close();print('PASS combined job/mail favicon total, separate title, no double count, pending read remains, linked unread counts, clear independently.')
 finally:http.shutdown();http.server_close()

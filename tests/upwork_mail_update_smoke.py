import os,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as tmp:
 os.environ.update(FREELANCE_DATA_DIR=tmp,FREELANCE_PASSWORD='')
 import server
 http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);threading.Thread(target=http.serve_forever,daemon=True).start();root=f'http://127.0.0.1:{http.server_port}'
 try:
  with sync_playwright() as p:
   b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   for missing in ('script','endpoint'):
    page=b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    target='/upwork-mail.js' if missing=='script' else '/api/mail'
    page.route('**'+target,lambda r:r.fulfill(status=404,content_type='application/json',body='{"error":"Không tìm thấy."}'))
    page.goto(root);page.wait_for_function('()=>initialized');page.evaluate("changeView('client')");page.locator('#clientGmail').click();page.wait_for_selector('dialog[open]');assert 'Ctrl + C' in page.locator('dialog[open]').inner_text();assert not errors,errors;page.close()
   b.close();print('PASS missing script and old Gmail endpoint show restart instructions; no silent button failure')
 finally:http.shutdown();http.server_close()

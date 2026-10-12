"""Exercise the native bridge/browser OAuth handoff without connecting Google."""
import os,sys,tempfile,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as tmp:
 os.environ.update(FREELANCE_DATA_DIR=tmp,FREELANCE_PASSWORD='')
 import server
 http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);threading.Thread(target=http.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{http.server_port}'
 try:
  with sync_playwright() as p:
   b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   status={'connected':False,'configured':True,'messages':[],'autoActions':False,'aiConfigured':False,'redirectUri':base+'/api/mail/callback'}
   page.route('**/api/mail',lambda route:route.fulfill(json=status))
   calls=[];page.expose_function('nativeOpenMail',lambda:calls.append('opened'))
   page.add_init_script("window.pywebview={api:{open_mail_browser:()=>window.nativeOpenMail()}}")
   page.goto(base+'/?openMail=1');page.wait_for_selector('#connectUpworkMail');assert page.locator('#connectUpworkMail').is_visible()
   page.locator('#connectUpworkMail').click();page.wait_for_function("()=>document.querySelector('#upworkMailStatus').textContent.includes('trình duyệt vừa mở')");assert calls==['opened'];assert page.url==base+'/';assert not errors,errors
   b.close();print('PASS browser handoff opens mail view; native bridge keeps Google out of embedded window; no provider calls.')
 finally:http.shutdown();http.server_close()

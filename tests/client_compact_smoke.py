import os,sys,tempfile,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as tmp:
 os.environ.update(FREELANCE_DATA_DIR=tmp,FREELANCE_PASSWORD='')
 import server
 clients=[{'name':'John L.','clientGroup':'active','clientStage':'working','nextAction':'Dựng 3 video theo tài liệu khách gửi.','lastReplyDate':'2026-10-11'}, {'name':'Nick D.','clientGroup':'active','clientStage':'paused','clientPauseReason':'unresponsive','lastReplyDate':'2026-09-23'}, {'name':'Maya R.','clientGroup':'talk','clientStage':'testing'}, {'name':'Alex M.','clientGroup':'talk','clientStage':'chatting'}, {'name':'Sepi B.','clientGroup':'archive','clientStage':'closed-no-contract'}]
 with server.connect() as db:
  for c in clients:db.execute("INSERT INTO records(kind,body) VALUES ('client',?)",(json.dumps(c),))
 http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);threading.Thread(target=http.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{http.server_port}'
 try:
  with sync_playwright() as p:
   b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1550,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base);page.wait_for_function('()=>initialized');page.evaluate("changeView('client')")
   assert page.locator('.client-disclosure[open]').count()==0
   assert page.locator('[data-client-stage]:visible').count()==0
   card=page.locator('[data-client-card="2"]');assert card.bounding_box()['height']<180
   card.locator('.client-summary').focus();page.keyboard.press('Enter');page.wait_for_selector('[data-client-pause-expand]:visible');card.locator('[data-client-pause-expand]>summary').click();page.wait_for_selector('[data-client-pause-note]:visible');assert card.locator('[data-client-pause-reason]').input_value()=='unresponsive'
   page.evaluate('refresh()');page.wait_for_selector('[data-client-pause-note]:visible');assert page.locator('.client-disclosure[open]').count()==1
   card.locator('.client-summary').click();page.wait_for_timeout(100);assert page.locator('.client-disclosure[open]').count()==0
   Path('/workspace/exports').mkdir(exist_ok=True);page.locator('.client-board').screenshot(path='/workspace/exports/client-compact-preview.png')
   page.locator('[data-client-card="1"] .client-summary').click();page.wait_for_selector('[data-client-card="1"] [data-client-stage]:visible');page.locator('.client-board').screenshot(path='/workspace/exports/client-compact-expanded-preview.png')
   page.evaluate("document.documentElement.dataset.theme='dark'");page.locator('.client-board').screenshot(path='/workspace/exports/client-compact-dark-preview.png')
   page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(100);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   assert not errors,errors;b.close();print('PASS compact default, keyboard disclosure, independent cards, refresh retains expansion, light/dark/mobile without horizontal overflow.')
 finally:http.shutdown();http.server_close()

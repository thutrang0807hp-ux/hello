import base64, os, tempfile, threading, sys, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
from unittest.mock import patch
import mail_actions
from email.message import EmailMessage
with tempfile.TemporaryDirectory() as tmp:
 os.environ.update(FREELANCE_DATA_DIR=tmp,FREELANCE_PASSWORD='',FREELANCE_AI_KEY='fake-test-key')
 import server
 http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);threading.Thread(target=http.serve_forever,daemon=True).start()
 root=f'http://127.0.0.1:{http.server_port}'
 raw=EmailMessage();raw['From']='John L. via Upwork <room_abc123@email.upwork.com>';raw['Subject']='John L. sent you a message';raw['Date']='Sat, 10 Oct 2026 02:02:00 +0700';raw.set_content('<div>Unread message from John L. about Video Editing.</div><p>1:54 AM ICT, 10 Oct 2026</p><p>Hey Trang, I have a new project.</p><p>View on Upwork</p>',subtype='html')
 try:
  with sync_playwright() as p:
   b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1400,'height':950});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(root);page.wait_for_function('()=>initialized');page.evaluate("changeView('client')");page.locator('#clientGmail').click();page.wait_for_selector('#upworkMailDialog[open]');assert not page.locator('#mailSetupPanel').get_attribute('open');assert not page.locator('#mailImportPanel').get_attribute('open');page.locator('#mailImportToggle').click()
   page.locator('#importUpworkMail').set_input_files({'name':'sample.eml','mimeType':'message/rfc822','buffer':raw.as_bytes()});page.wait_for_selector('.upwork-mail-item');assert page.locator('#pendingMailJump').count()==1;assert page.locator('#resolvePendingMail').count()==1;assert 'Hey Trang' in page.locator('.upwork-mail-text').text_content()
   page.locator('[data-mail-client]').select_option('new');page.locator('[data-mail-link]').click();page.wait_for_function("()=>document.querySelector('.upwork-mail-link').textContent.includes('Đã liên kết · John L.')");assert page.locator('.client-card').count()==1;assert page.locator('.client-card .mail-new-badge').count()==1;assert page.locator('#pendingMailJump').count()==0;assert page.locator('#resolvePendingMail').count()==0
   with patch.object(mail_actions,'evaluate',return_value={'decision':'update','action':'Chờ khách gửi mẫu, rồi xác nhận yêu cầu dự án.','reason':'Khách đề cập dự án mới.'}) as ai:
    mail_actions.run_once(server.connect);mail_actions.run_once(server.connect);assert ai.call_count==1
   page.evaluate('refresh()');page.wait_for_function("()=>document.querySelector('.client-next').textContent.includes('Chờ khách gửi mẫu')")
   page.locator('[data-mail-reassign]').click();assert page.locator('.mail-link-controls').is_visible();page.locator('[data-mail-reassign]').click();assert page.locator('.mail-link-controls').is_hidden();page.locator('[data-mail-read] summary').click();page.wait_for_function("()=>!document.querySelector('.client-card .mail-new-badge')")
   page.locator('#importUpworkMail').set_input_files({'name':'same.eml','mimeType':'message/rfc822','buffer':raw.as_bytes()});page.wait_for_function("()=>document.querySelector('#upworkMailStatus').textContent.includes('không nhập trùng')");assert page.locator('.upwork-mail-item').count()==1;page.locator('[data-mail-filter=pending]').click();assert page.locator('.upwork-mail-item').count()==0;page.locator('[data-mail-filter=all]').click()
   page.locator('#connectUpworkMail').click();page.wait_for_selector('#mailSetupPanel[open]');page.locator('input[name=clientId]').fill('test.apps.googleusercontent.com');page.locator('input[name=clientSecret]').fill('test-secret');page.locator('#upworkMailConfig button').click();page.wait_for_function("()=>!document.querySelector('#connectUpworkMail').disabled")
   data=page.request.get(root+'/api/mail').json();assert 'test-secret' not in json.dumps(data);assert data['configured'];assert len(data['messages'])==1
   page.screenshot(path='/workspace/exports/upwork-mail-preview.png');page.evaluate("document.documentElement.dataset.theme='dark'");page.screenshot(path='/workspace/exports/upwork-mail-dark-preview.png');page.set_viewport_size({'width':390,'height':844});assert page.locator('#upworkMailDialog').evaluate('(d)=>d.scrollWidth<=d.clientWidth');assert not errors,errors
   b.close();print('PASS .eml import, extraction, linking/new client, reply update, unread clearing, duplicate rejection, OAuth config secrecy, light/dark and mobile')
 finally:http.shutdown();http.server_close()

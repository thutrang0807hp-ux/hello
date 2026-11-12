"""Local fixtures only: Studio handoff and DOM adapter, never a real ChatGPT account."""
import json,os,tempfile,threading,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 os.environ.update(FREELANCE_DATA_DIR=tmp,FREELANCE_PASSWORD='')
 for name in ('FREELANCE_AI_KEY','FREELANCE_TELEGRAM_TOKEN','FREELANCE_SLACK_TOKEN'):os.environ.pop(name,None)
 import server
 with server.connect() as db:
  workspace={'version':1,'nodes':[{'id':'job','type':'job','x':0,'y':0,'title':'Job','content':'Build dashboard'},{'id':'draft','type':'draft','x':400,'y':0,'title':'My draft','content':'Original draft','language':'English'}],'edges':[{'from':'job','to':'draft'}]}
  ident=db.execute("INSERT INTO records(kind,body) VALUES('proposal',?)",(json.dumps({'name':'ChatGPT fixture','body':'Original draft','workspace':workspace}),)).lastrowid
 http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);threading.Thread(target=http.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{http.server_port}'
 try:
  with sync_playwright() as p:
   b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   page=b.new_page(viewport={'width':1500,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(base);page.wait_for_function('()=>initialized');page.evaluate(f"Studio.open(records.find(r=>r.id==={ident}))")
   page.locator('[data-node="draft"]').click();page.locator('#chatgptControls summary').click()
   page.locator('#nodeChatGPTRevision').fill('Make it shorter');page.locator('#prepareChatGPT').click()
   page.wait_for_function("()=>!document.querySelector('#receiveChatGPT').disabled")
   import chatgpt_bridge
   task=chatgpt_bridge.pending(server.connect)[0];assert 'Make it shorter' in task['prompt']
   chatgpt_bridge.complete(server.connect,{'id':task['id'],'answer':'New letter from fixture'})
   page.locator('#receiveChatGPT').click();page.wait_for_selector('[data-chat-apply]')
   assert page.locator('[aria-label="Thư từ ChatGPT"]').input_value()=='New letter from fixture'
   page.locator('[data-chat-apply]').click();page.wait_for_function("()=>document.querySelector('[name=nodeContent]').value==='New letter from fixture'")
   with server.connect() as db:
    record=json.loads(db.execute('SELECT body FROM records WHERE id=?',(ident,)).fetchone()[0]);node=record['workspace']['nodes'][1]
    assert node['content']=='New letter from fixture' and node['versions'][-1]['content']=='Original draft'
   # DOM adapter on intercepted fixture origin: no actual ChatGPT request is made.
   chat=b.new_page()
   chat.route('https://chatgpt.com/**',lambda route:route.fulfill(status=200,content_type='text/html',body='<div id="prompt-textarea" contenteditable="true"></div><button id="send">Send</button><main id="messages"></main>'))
   chat.goto('https://chatgpt.com/')
   chat.evaluate("()=>{window.chrome={runtime:{id:'fixture',onMessage:{addListener:f=>window.listener=f}}};window.sendClicks=0;document.querySelector('#send').onclick=()=>window.sendClicks++;}")
   chat.add_script_tag(content=(ROOT/'toolkit-bridge/desk-bridge-chatgpt-content.js').read_text())
   def command(action,**extra):return chat.evaluate("m=>new Promise(resolve=>window.listener({target:'freelance-desk-chatgpt-page',...m},{id:'fixture'},resolve))",dict(action=action,**extra))
   assert command('prepare',prompt='fixture prompt')['ok']
   assert chat.evaluate('sendClicks')==0
   assert not command('prepare',prompt='do not overwrite')['ok']
   marker='[Freelance Desk task: fixture-task]'
   chat.evaluate("marker=>document.querySelector('#messages').innerHTML='<div data-message-author-role=assistant>Unrelated answer</div><div data-message-author-role=user>'+marker+'</div><div data-message-author-role=assistant><div class=markdown>My proposal</div></div>'",marker)
   assert not command('answers',id='wrong-task')['ok']
   result=command('answers',id='fixture-task');assert len(result['answers'])==1
   assert command('take',id='fixture-task',index=0)['answer']=='My proposal'
   chat.locator('.markdown').evaluate("e=>e.textContent='Changed answer'")
   assert not command('take',id='fixture-task',index=0)['ok']
   chat.evaluate("document.body.insertAdjacentHTML('beforeend','<button data-testid=stop-button>Stop</button>')")
   assert not command('answers',id='fixture-task')['ok']
   assert not errors,errors
   b.close()
  print('PASS Studio create/preview/apply/version preservation; DOM fixture compose without send, no overwrite, task binding, answer selection, stale/streaming rejection.')
 finally:http.shutdown();http.server_close()

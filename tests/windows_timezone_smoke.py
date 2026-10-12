"""No site-packages or timezone database, as on a stock Windows Python install."""
import base64,json,os,socket,subprocess,sys,tempfile,time,urllib.request
from email.message import EmailMessage
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 env={k:v for k,v in os.environ.items() if not k.startswith('FREELANCE_')}
 with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 env.update(FREELANCE_DATA_DIR=tmp,PORT=str(port),PYTHONTZPATH=str(Path(tmp)/'missing-tzdata'))
 process=subprocess.Popen([sys.executable,'-S',str(ROOT/'server.py')],env=env,cwd=tmp,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 def call(path,payload=None):
  data=json.dumps(payload).encode() if payload is not None else None
  req=urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=data,headers={'Content-Type':'application/json'} if data is not None else {})
  with urllib.request.urlopen(req,timeout=3) as response:return json.load(response)
 try:
  for _ in range(100):
   if process.poll() is not None:raise AssertionError('Server failed')
   try:call('/api/auth');break
   except OSError:time.sleep(.1)
  m=EmailMessage();m['From']='John via Upwork <room_abc123@email.upwork.com>';m['Subject']='John sent you a message';m['Date']='Mon, 12 Oct 2026 02:00:00 +0700';m.set_content('<p>Unread message from John about Editing.</p><p>1:54 AM ICT, 12 Oct 2026</p><p>A new project.</p><p>View on Upwork</p>',subtype='html')
  call('/api/mail/import',{'raw':base64.b64encode(m.as_bytes()).decode()});mail=call('/api/mail')['messages'][0]
  for _ in range(2):call('/api/mail/link',{'id':mail['id'],'clientId':'new'})
  clients=[r for r in call('/api/records') if r['kind']=='client'];assert len(clients)==1;assert clients[0]['lastReplyDate']=='2026-10-12';assert clients[0]['clientGroup']=='talk';assert clients[0]['upworkMailUnread']
  assert call('/api/mail')['messages'][0]['clientId']==clients[0]['id'];assert clients[0]['clientCreatedAt'].endswith('+07:00')
  print('PASS no tzdata/site-packages: email creates and links one client atomically, UTC+7 reply appears in talk group; repeat creates no duplicate.')
 finally:process.terminate();process.wait(timeout=5)

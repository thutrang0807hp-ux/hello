"""Save via real HTTP, stop/restart in another cwd; no live provider requests."""
import json,os,socket,subprocess,sys,tempfile,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def call(port,path,body=None):
 data=json.dumps(body).encode() if body is not None else None
 req=urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=data,headers={'Content-Type':'application/json'} if data is not None else {})
 with urllib.request.urlopen(req,timeout=3) as r:return json.load(r)

def start(env,cwd):
 with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 process=subprocess.Popen([sys.executable,str(ROOT/'server.py')],cwd=cwd,env=dict(env,PORT=str(port)),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  for _ in range(100):
   if process.poll() is not None:raise AssertionError('Server startup failed')
   try:call(port,'/api/auth');return process,port
   except OSError:time.sleep(.1)
  raise AssertionError('Startup timed out')
 except Exception:process.terminate();process.wait(timeout=5);raise

def stop(process):process.terminate();process.wait(timeout=5)

with tempfile.TemporaryDirectory() as tmp:
 data=Path(tmp)/'private-data';env={k:v for k,v in os.environ.items() if not k.startswith('FREELANCE_')};env['FREELANCE_DATA_DIR']=str(data)
 process,port=start(env,ROOT)
 try:
  call(port,'/api/ai/configure',{'provider':'openai','key':'fake-restart-key'})
  call(port,'/api/channels/configure',{'channel':'telegram','token':'fake-telegram-token','target':'12345'})
  call(port,'/api/mail/configure',{'clientId':'test.apps.googleusercontent.com','clientSecret':'fake-secret'})
  call(port,'/api/records',{'kind':'client','name':'Khách thử khởi động lại'})
  private=data/'gmail-private.json';gmail=json.loads(private.read_text());gmail['refreshToken']='fake-refresh-token';private.write_text(json.dumps(gmail))
  before=call(port,'/api/settings');token=(data/'webhook-token').read_text()
 finally:stop(process)
 process,port=start(env,Path(tmp))
 try:
  after=call(port,'/api/settings');mail=call(port,'/api/mail');rows=call(port,'/api/records')
  assert after['aiConfigured'] and after['aiProvider']=='openai'
  assert after['channelTargets']['telegram']=='12345' and after['channels']==before['channels']
  assert mail['configured'] and mail['connected']
  assert any(r['name']=='Khách thử khởi động lại' for r in rows)
  assert (data/'webhook-token').read_text()==token
  serialized=json.dumps([after,mail]);assert all(x not in serialized for x in ('fake-restart-key','fake-telegram-token','fake-refresh-token','fake-secret'))
  print('PASS AI/Telegram/Gmail session, client records and webhook identity survive server restart in another cwd; no secret values returned.')
 finally:stop(process)

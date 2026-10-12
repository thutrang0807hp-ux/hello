"""Real detached child survives launcher exit; private-token stop, password preserved."""
import json,os,socket,subprocess,sys,tempfile,time,urllib.error,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from desktop_background import request

with tempfile.TemporaryDirectory() as tmp:
 env={k:v for k,v in os.environ.items() if not k.startswith('FREELANCE_')}
 with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 env.update(FREELANCE_DATA_DIR=tmp,FREELANCE_PASSWORD='fake-local-password',PORT=str(port))
 descriptor=Path(tmp)/'desktop-server.json'
 try:
  code='from desktop_background import start; start(open_browser=False)'
  subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,check=True,timeout=20)
  item=json.loads(descriptor.read_text());time.sleep(.2)
  assert request(port,'/api/desktop/status',item['token'])['pid']==item['pid']
  assert request(port,'/api/auth')['authenticated'] is False
  for endpoint,body in (('/api/desktop/status',None),('/api/desktop/stop',{})):
   try:request(port,endpoint,'wrong-token',body);raise AssertionError('Wrong token accepted')
   except urllib.error.HTTPError as e:assert e.code==403
  subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,check=True,timeout=20)
  assert json.loads(descriptor.read_text())['pid']==item['pid']
  subprocess.run([sys.executable,'-c','from desktop_background import stop; assert stop()'],cwd=ROOT,env=env,check=True,timeout=15)
  assert not descriptor.exists();assert (Path(tmp)/'workspace.sqlite3').exists()
  try:request(port,'/api/auth');raise AssertionError('Server still running')
  except OSError:pass
  print('PASS background server survives launcher exit; repeated start reuses it; password stays required; wrong stop token rejected; stop retains data.')
 finally:
  if descriptor.exists():
   item=json.loads(descriptor.read_text())
   try:request(port,'/api/desktop/stop',item['token'],{})
   except OSError:pass

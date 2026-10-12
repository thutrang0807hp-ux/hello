"""Real wrapper process reproduces Windows venv PID indirection on Linux."""
import os,sys,socket,tempfile,json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import desktop_background as desktop

with tempfile.TemporaryDirectory() as tmp:
 folder=Path(tmp)
 wrapper=folder/'test-launcher.py'
 wrapper.write_text('''import subprocess,sys,signal
child=subprocess.Popen(sys.argv[1:])
def stop(*_):
    if child.poll() is None:child.terminate()
signal.signal(signal.SIGTERM,stop)
raise SystemExit(child.wait())
''')
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 env={k:v for k,v in os.environ.items() if not k.startswith('FREELANCE_')};env.update(FREELANCE_DATA_DIR=tmp,FREELANCE_PASSWORD='',PORT=str(port))
 real_popen=desktop.subprocess.Popen;launched=[]
 def launch(args,**kwargs):
  child=real_popen([sys.executable,str(wrapper),*args],**kwargs);launched.append(child);return child
 try:
  with patch.dict(os.environ,env,clear=True),patch.object(desktop.subprocess,'Popen',side_effect=launch):
   item=desktop.start(open_browser=False)
   assert item['launcherPid']==launched[0].pid and item['pid']!=item['launcherPid']
   assert desktop.request(port,'/api/desktop/status',item['token'])['pid']==item['pid']
   assert desktop.alive(item)
   assert desktop.start(open_browser=False)==item and len(launched)==1
   assert desktop.stop();launched[0].wait(timeout=10);assert (folder/'workspace.sqlite3').exists();assert not (folder/'desktop-server.json').exists()
  print('PASS real redirector/server have different PIDs; authenticated readiness succeeds, repeat start reuses, stop ends both processes and retains data.')
 finally:
  for child in launched:
   if child.poll() is None:child.terminate();child.wait(timeout=10)

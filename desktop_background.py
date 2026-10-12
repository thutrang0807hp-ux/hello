"""Start an independent local server; stop only the instance matching our private token."""
import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
import urllib.request
import webbrowser
from pathlib import Path
from data_store import data_directory, ROOT
from local_config import load


def request(port,path,token='',body=None):
    data=json.dumps(body).encode() if body is not None else None
    headers={'X-Desktop-Token':token}
    if data is not None:headers['Content-Type']='application/json'
    req=urllib.request.Request(f'http://127.0.0.1:{int(port)}'+path,data=data,headers=headers)
    with urllib.request.urlopen(req,timeout=1) as r:return json.load(r)


def state_file():return data_directory()/'desktop-server.json'


def saved():
    try:
        item=json.loads(state_file().read_text(encoding='utf-8'))
        if not isinstance(item.get('token'),str) or len(item['token'])<24 or not isinstance(item.get('port'),int):return None
        return item
    except (OSError,ValueError,TypeError):return None


def authenticated_status(item):
    if not item:return None
    try:
        status=request(item['port'],'/api/desktop/status',item['token'])
        pid=status.get('pid')
        if status.get('ok') is True and isinstance(pid,int) and not isinstance(pid,bool) and pid>0:
            return status
    except (OSError,ValueError,KeyError,AttributeError,TypeError):pass
    return None


def alive(item):
    status=authenticated_status(item)
    return bool(status and status['pid']==item.get('pid'))


def adopt_server_pid(item):
    """A Windows venv redirector PID is not the authenticated Python server PID."""
    status=authenticated_status(item)
    if not status:return False
    item['pid']=status['pid']
    return True


def start(open_browser=True):
    load();data=data_directory();data.mkdir(parents=True,exist_ok=True)
    previous=saved()
    if alive(previous):
        if open_browser:webbrowser.open(f"http://127.0.0.1:{previous['port']}")
        return previous
    port=int(os.environ.get('PORT','8000'))
    try:
        request(port,'/api/auth')
    except OSError:pass
    else:raise RuntimeError('App đang chạy ở cổng này. Dừng CMD cũ bằng Ctrl+C rồi mở start-background-windows.bat.')
    token=secrets.token_urlsafe(32)
    env=dict(os.environ,FREELANCE_DESKTOP_CONTROL_TOKEN=token,FREELANCE_BIND='127.0.0.1',FREELANCE_DATA_DIR=str(data),PORT=str(port),PYTHONUTF8='1')
    flags={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {'start_new_session':True}
    log=data/'background-server.log'
    if log.exists() and log.stat().st_size>2*1024*1024:log.replace(log.with_suffix('.log.1'))
    with log.open('ab') as output:
        process=subprocess.Popen([sys.executable,str(ROOT/'server.py')],cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=output,stderr=output,**flags)
    item={'pid':process.pid,'launcherPid':process.pid,'port':port,'token':token}
    try:
        for _ in range(100):
            if process.poll() is not None:raise RuntimeError('Web chưa chạy được. Xem background-server.log trong thư mục dữ liệu.')
            if adopt_server_pid(item):break
            time.sleep(.1)
        else:raise RuntimeError('Web khởi động quá lâu. Mở lại sau khi kiểm tra background-server.log.')
        path=state_file();fd,temp=tempfile.mkstemp(prefix='.desktop-',dir=data)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(item,f)
            Path(temp).replace(path)
        finally:Path(temp).unlink(missing_ok=True)
        if open_browser:webbrowser.open(f'http://127.0.0.1:{port}')
        return item
    except Exception:
        if process.poll() is None:process.terminate();process.wait(timeout=5)
        raise


def stop():
    item=saved()
    if not alive(item):return False
    request(item['port'],'/api/desktop/stop',item['token'],{})
    for _ in range(60):
        if not alive(item):
            if saved()==item:state_file().unlink(missing_ok=True)
            return True
        time.sleep(.1)
    raise RuntimeError('Web chưa dừng xong. Thử lại sau vài giây.')


def message(text,error=False):
    if os.name=='nt':
        import ctypes
        ctypes.windll.user32.MessageBoxW(None,text,'Freelance Desk',0x10 if error else 0x40)
    else:print(text)


def main():
    try:
        if len(sys.argv)>1 and sys.argv[1]=='stop':
            message('Đã dừng web chạy nền. Dữ liệu vẫn được giữ.' if stop() else 'Không có web chạy nền do công cụ này mở. Không dừng các chương trình khác.')
        else:start()
        return 0
    except Exception as error:message(str(error),True);return 1


if __name__=='__main__':raise SystemExit(main())

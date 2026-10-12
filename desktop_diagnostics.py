"""Desktop prerequisite checks and a shareable report without reading private config."""
import importlib.metadata
import json
import os
import platform
import re
import sys
from pathlib import Path

WEBVIEW_GUID='{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'
NET_KEY=r'SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full'
REPORT=Path(__file__).resolve().parent/'desktop-diagnostic.txt'


class MissingWebView(RuntimeError):
    pass


class MissingNet(RuntimeError):
    pass


def windows_runtime(registry=None):
    if registry is None:
        if os.name!='nt':return {'webview2':None,'netRelease':None}
        import winreg as registry
    result={'webview2':None,'netRelease':None}
    for hive in (registry.HKEY_CURRENT_USER,registry.HKEY_LOCAL_MACHINE):
        for view in (registry.KEY_WOW64_32KEY,registry.KEY_WOW64_64KEY):
            try:
                with registry.OpenKey(hive,rf'SOFTWARE\Microsoft\EdgeUpdate\Clients\{WEBVIEW_GUID}',0,registry.KEY_READ|view) as key:
                    value=str(registry.QueryValueEx(key,'pv')[0])
                    if re.fullmatch(r'\d+(?:\.\d+)+',value) and int(value.split('.')[0])>=86:result['webview2']=value
            except OSError:pass
    for view in (registry.KEY_WOW64_32KEY,registry.KEY_WOW64_64KEY):
        try:
            with registry.OpenKey(registry.HKEY_LOCAL_MACHINE,NET_KEY,0,registry.KEY_READ|view) as key:
                release=int(registry.QueryValueEx(key,'Release')[0])
                result['netRelease']=max(result['netRelease'] or 0,release)
        except (OSError,ValueError,TypeError):pass
    return result


def require_runtime(runtime=None):
    runtime=runtime if runtime is not None else windows_runtime()
    if not runtime.get('webview2'):
        raise MissingWebView('Chưa tìm thấy Microsoft Edge WebView2 Runtime. Chạy repair-webview2-windows.bat để cài, rồi mở lại app.')
    if (runtime.get('netRelease') or 0)<394802:
        raise MissingNet('Thiếu .NET Framework 4.6.2 trở lên. Cài .NET Framework 4.8 từ Microsoft, rồi mở lại app. https://dotnet.microsoft.com/download/dotnet-framework/net48')


def safe_error(error):
    text=str(error)
    text=re.sub(r'(?i)(?:sk-(?:proj-)?[A-Za-z0-9_-]+|xox[baprs]-[A-Za-z0-9-]+|AIza[A-Za-z0-9_-]+|\d{8,12}:[A-Za-z0-9_-]{20,})','[ĐÃ ẨN]',text)
    text=re.sub(r'(?i)(Bearer\s+)[^\s]+',r'\1[ĐÃ ẨN]',text)
    text=re.sub(r'(?i)((?:token|secret|api_key|code|state)=)[^\s&]+',r'\1[ĐÃ ẨN]',text)
    return text[:1000]


def report(stage='diagnostic',error=None):
    packages={}
    for name in ('pywebview','pystray','Pillow','pythonnet','clr_loader'):
        try:packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:packages[name]='NOT INSTALLED'
    result={'stage':stage,'python':platform.python_version(),'architecture':platform.machine(),'packages':packages,'runtime':windows_runtime()}
    if error:result.update(errorType=type(error).__name__,error=safe_error(error))
    try:REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    except OSError:pass
    return result


if __name__=='__main__':
    print(json.dumps(report(),ensure_ascii=False,indent=2))
    print('Bao cao: '+str(REPORT))

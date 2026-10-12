"""Reviewable Windows removal: explicit file allowlist, no recursive user-folder deletion."""
import json
import os
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from desktop_background import request, alive
from local_config import NAMES

ROOT=Path(__file__).resolve().parent
DATA_FILES=('workspace.sqlite3','workspace.sqlite3-wal','workspace.sqlite3-shm','local-config.json','gmail-private.json','webhook-token','desktop-server.json','background-server.log','background-server.log.1')


def read_json(path):
    try:
        value=json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value,dict) else {}
    except (OSError,ValueError):return {}


def safe(path,scope):
    try:parts=path.relative_to(scope).parts
    except ValueError:return False
    cursor=scope
    if cursor.is_symlink():return False
    for part in parts:
        cursor=cursor/part
        if cursor.is_symlink():return False
    return True


def data_owned(folder):
    if folder.is_symlink():return False
    config=read_json(folder/'local-config.json')
    if any(k in NAMES for k in config):return True
    mail=read_json(folder/'gmail-private.json')
    if 'clientId' in mail or 'refreshToken' in mail:return True
    db=folder/'workspace.sqlite3'
    if db.is_file() and not db.is_symlink():
        try:
            with closing(sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True)) as connection:
                tables={r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            return {'records','settings'}.issubset(tables)
        except sqlite3.Error:return False
    return False


def plan(root=None,include_data=True):
    root=Path(root or ROOT).resolve();items=[];folders=[];descriptors=[];notes=[]
    manifest=read_json(root/'uninstall-files.json')
    for name in manifest.get('files',[]):
        if not isinstance(name,str):raise RuntimeError('Danh sách gỡ không hợp lệ.')
        relative=Path(name)
        if relative.is_absolute() or '..' in relative.parts:raise RuntimeError('Danh sách gỡ chứa đường dẫn không an toàn.')
        file=root/relative
        if file.is_file() and safe(file,root):items.append(file)
    if not manifest:raise RuntimeError('Thiếu uninstall-files.json. Chép đầy đủ bản cập nhật trước khi gỡ.')
    for file in root.glob('__pycache__/*.pyc'):
        stem=file.name.split('.')[0]
        if stem+'.py' in manifest.get('files',[]) and safe(file,root):items.append(file)
    candidates=[root/'data'];pointers=[root/'.storage-location.json']
    base=os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA')
    if base:
        profile=Path(base)/'FreelanceDesk';candidates.append(profile/'data');pointers.append(profile/'storage-location.json')
    for pointer in pointers:
        directory=read_json(pointer).get('directory')
        if isinstance(directory,str) and Path(directory).is_absolute():candidates.append(Path(directory))
    explicit=os.environ.get('FREELANCE_DATA_DIR')
    if explicit:
        directory=Path(explicit).expanduser();candidates.append(directory if directory.is_absolute() else root/directory)
    for folder in dict.fromkeys(candidates):
        if folder.exists() and data_owned(folder):
            folders.append(folder)
            descriptor=read_json(folder/'desktop-server.json')
            if descriptor:descriptors.append(descriptor)
            if include_data:
                for name in DATA_FILES:
                    file=folder/name
                    if file.is_file() and safe(file,folder):items.append(file)
        elif folder.exists() and any(folder.iterdir()):notes.append('Giữ thư mục chưa xác định chắc là dữ liệu app: '+str(folder))
    if include_data:
        for file in pointers:
            if read_json(file).get('directory') and file.is_file() and not file.is_symlink():items.append(file)
    return {'root':root,'files':list(dict.fromkeys(items)),'folders':folders,'descriptors':descriptors,'notes':notes,'resolved':{str(p):str(p.resolve()) for p in items}}


def stop_instances(preview):
    ports={int(os.environ.get('PORT','8000'))}
    for item in preview['descriptors']:
        if not isinstance(item.get('port'),int) or not isinstance(item.get('token'),str):continue
        ports.add(item['port'])
        if alive(item):
            request(item['port'],'/api/desktop/stop',item['token'],{})
            for _ in range(60):
                if not alive(item):break
                time.sleep(.1)
            else:raise RuntimeError('Web chưa dừng xong. Chưa xóa tệp nào; thử lại sau.')
    for port in ports:
        try:status=request(port,'/api/auth')
        except (OSError,ValueError):continue
        if isinstance(status,dict) and isinstance(status.get('required'),bool):
            raise RuntimeError('Web vẫn chạy trong CMD. Nhấn Ctrl+C ở CMD đó rồi mở công cụ gỡ lại. Chưa xóa tệp nào.')


def remove(preview):
    stop_instances(preview)
    failed=[];deleted=[]
    for file in preview['files']:
        try:
            # Recheck links immediately before deleting; no rmtree or wildcard removal.
            if file.is_symlink() or str(file.resolve())!=preview['resolved'].get(str(file)):raise OSError('Đường dẫn đã đổi, giữ lại để kiểm tra.')
            file.unlink(missing_ok=True);deleted.append(file)
        except OSError:failed.append(str(file))
    # Only remove empty directories. Unrelated files always survive.
    directories=set()
    for file in deleted:
        parent=file.parent
        while parent!=parent.parent:
            directories.add(parent)
            if parent==preview['root'] or parent in preview['folders']:break
            if preview['root'] not in parent.parents and not any(f==parent or f in parent.parents for f in preview['folders']):break
            parent=parent.parent
    for folder in sorted(directories,key=lambda p:len(p.parts),reverse=True):
        try:folder.rmdir()
        except OSError:pass
    return failed


def main():
    import tkinter as tk
    from tkinter import ttk,messagebox
    window=tk.Tk();window.title('Freelance Desk — gỡ ứng dụng');window.geometry('760x600')
    try:preview=plan()
    except Exception as error:messagebox.showerror('Chưa chuẩn bị gỡ được',str(error));window.destroy();return
    frame=ttk.Frame(window,padding=20);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='Gỡ Freelance Desk và dữ liệu đã lưu',font=('Segoe UI',15,'bold')).pack(anchor='w')
    ttk.Label(frame,text='Danh sách dưới đây sẽ bị xóa. Bao gồm job, khách, thư và khóa/token đã lưu.\nKhông có thùng rác/khôi phục từ công cụ này.',wraplength=700).pack(anchor='w',pady=12)
    text=tk.Text(frame,wrap='word',height=16);text.pack(fill='both',expand=True)
    text.insert('1.0','\n'.join(str(p) for p in preview['files'])+'\n\n'+'\n'.join(preview['notes']));text.configure(state='disabled')
    ttk.Label(frame,text='Quyền Gmail trên Google và extension Chrome cần gỡ riêng.\nFile/tài liệu không thuộc danh sách trên sẽ được giữ.',wraplength=700).pack(anchor='w',pady=12)
    entry=ttk.Entry(frame);entry.pack(fill='x');ttk.Label(frame,text='Nhập XOA để xác nhận xóa các tệp đã liệt kê.').pack(anchor='w',pady=6)
    def perform():
        if entry.get().strip()!='XOA':messagebox.showwarning('Chưa xác nhận','Nhập XOA rồi bấm Gỡ và xóa dữ liệu.');return
        button.configure(state='disabled')
        try:
            failed=remove(preview)
            if failed:messagebox.showwarning('Còn tệp chưa xóa được','Các tệp này còn nguyên, kiểm tra app đã dừng:\n'+'\n'.join(failed))
            else:messagebox.showinfo('Đã gỡ tệp đã liệt kê','Đã dừng web và xóa các tệp đã liệt kê.\nNếu còn tài liệu riêng, thư mục sẽ được giữ.\nThu hồi quyền Gmail tại myaccount.google.com/connections; gỡ extension trong chrome://extensions.')
            window.destroy()
        except Exception as error:messagebox.showerror('Chưa gỡ được',str(error));button.configure(state='normal')
    buttons=ttk.Frame(frame);buttons.pack(fill='x',pady=10)
    ttk.Button(buttons,text='Hủy',command=window.destroy).pack(side='right')
    button=ttk.Button(buttons,text='Gỡ và xóa dữ liệu',command=perform);button.pack(side='right',padx=10)
    window.mainloop()


if __name__=='__main__':main()

"""Shared persistent storage, safe migration, and an optional saved location."""
import json
import os
import shutil
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def location_files(root,windows):
    local=Path(root)/'.storage-location.json'
    base=os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA')
    return [local]+([Path(base)/'FreelanceDesk'/'storage-location.json'] if windows and base else [])


def selected_directory(root,windows):
    for file in location_files(root,windows):
        if file.exists():
            try:
                value=json.loads(file.read_text(encoding='utf-8'))['directory']
                if not isinstance(value,str) or not Path(value).is_absolute():raise ValueError()
                return Path(value)
            except (ValueError,KeyError,OSError):
                raise RuntimeError('Không đọc được vị trí dữ liệu đã chọn. Mở choose-data-windows.bat để chọn lại.') from None
    return None


def copy_data(source,target):
    """Publish a full snapshot only after closing every SQLite handle (Windows)."""
    source,target=Path(source),Path(target)
    if source.resolve()==target.resolve():return
    if source.resolve() in target.resolve().parents:
        raise RuntimeError('Chọn nơi lưu nằm ngoài thư mục dữ liệu cũ để tránh sao chép lặp.')
    if target.exists() and any(target.iterdir()):return  # Never merge/overwrite a dataset.
    if not source.exists() or not any(source.iterdir()):
        target.mkdir(parents=True,exist_ok=True);return
    target.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.data-migration-',dir=target.parent))
    try:
        for entry in source.iterdir():
            if entry.name in ('workspace.sqlite3','workspace.sqlite3-wal','workspace.sqlite3-shm'):continue
            if entry.is_symlink():raise RuntimeError('Thư mục dữ liệu có liên kết tệp; cần kiểm tra trước khi sao chép.')
            if entry.is_dir():shutil.copytree(entry,staging/entry.name)
            else:shutil.copy2(entry,staging/entry.name)
        database=source/'workspace.sqlite3'
        if database.exists():
            # Connection context managers commit/rollback but do NOT close handles.
            with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db_source:
                with closing(sqlite3.connect(staging/database.name)) as db_destination:
                    with db_destination:db_source.backup(db_destination)
        if target.exists():target.rmdir()
        staging.rename(target)
    except Exception:
        shutil.rmtree(staging,ignore_errors=True);raise


def data_directory(root=None,windows=None):
    root=Path(root or ROOT).resolve()
    explicit=os.environ.get('FREELANCE_DATA_DIR')
    if explicit:
        path=Path(explicit).expanduser()
        return path.resolve() if path.is_absolute() else (root/path).resolve()
    windows=os.name=='nt' if windows is None else windows
    selected=selected_directory(root,windows)
    if selected:return selected
    base=os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA')
    legacy=root/'data'
    if not windows or not base:return legacy
    target=Path(base)/'FreelanceDesk'/'data'
    if target.exists() and any(target.iterdir()):return target
    try:copy_data(legacy,target)
    except PermissionError:
        # Permission/antivirus failures must not make the original install unusable.
        if legacy.exists() and any(legacy.iterdir()):return legacy
        raise RuntimeError('Không ghi được AppData. Mở choose-data-windows.bat để chọn nơi lưu khác.') from None
    return target


def choose_directory(destination,root=None,windows=None,source=None):
    root=Path(root or ROOT).resolve();windows=os.name=='nt' if windows is None else windows
    target=Path(destination).expanduser().resolve()
    if source is None:
        try:source=data_directory(root,windows)
        except (RuntimeError,PermissionError):source=root/'data'
    copy_data(source,target)
    target.mkdir(parents=True,exist_ok=True)
    # Probe access before saving the selection. No existing files are replaced.
    fd,probe=tempfile.mkstemp(prefix='.write-check-',dir=target);os.close(fd);Path(probe).unlink()
    saved=False;errors=[]
    for file in reversed(location_files(root,windows)):
        try:
            file.parent.mkdir(parents=True,exist_ok=True)
            fd,temporary=tempfile.mkstemp(prefix='.location-',dir=file.parent)
            try:
                with os.fdopen(fd,'w',encoding='utf-8') as stream:json.dump({'directory':str(target)},stream,ensure_ascii=False)
                Path(temporary).replace(file)
            finally:
                Path(temporary).unlink(missing_ok=True)
            saved=True
        except OSError as error:errors.append(error)
    if not saved:raise RuntimeError('Đã sao chép dữ liệu nhưng không lưu được vị trí. Kiểm tra quyền ghi thư mục app.') from None
    return target

"""One persistent data location for config, SQLite and OAuth; preserve old installs."""
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def data_directory(root=None, windows=None):
    root=Path(root or ROOT).resolve()
    explicit=os.environ.get('FREELANCE_DATA_DIR')
    if explicit:
        path=Path(explicit).expanduser()
        return path.resolve() if path.is_absolute() else (root/path).resolve()
    windows=os.name=='nt' if windows is None else windows
    base=os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA')
    legacy=root/'data'
    if not windows or not base:return legacy
    target=Path(base)/'FreelanceDesk'/'data'
    if target.exists() and any(target.iterdir()):return target
    if not legacy.exists() or not any(legacy.iterdir()):return target
    # Stage a complete copy, then rename. Originals remain available for rollback.
    target.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.data-migration-',dir=target.parent))
    try:
        for entry in legacy.iterdir():
            if entry.name in ('workspace.sqlite3','workspace.sqlite3-wal','workspace.sqlite3-shm'):continue
            if entry.is_symlink():raise RuntimeError('Dữ liệu cũ có liên kết tệp. Giữ FREELANCE_DATA_DIR trỏ vào thư mục cũ để kiểm tra trước.')
            if entry.is_dir():shutil.copytree(entry,staging/entry.name)
            else:shutil.copy2(entry,staging/entry.name)
        database=legacy/'workspace.sqlite3'
        if database.exists():
            with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True) as source, sqlite3.connect(staging/database.name) as destination:
                source.backup(destination)
        if target.exists():target.rmdir()  # Only empty targets reach this branch.
        staging.rename(target)
    except Exception:
        shutil.rmtree(staging,ignore_errors=True)
        raise
    return target

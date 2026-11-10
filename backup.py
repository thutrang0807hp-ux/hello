"""Daily SQLite snapshots in <data>/backups. Reads the live database only; keeps the newest KEEP copies."""
import os
import sqlite3
import time
import threading
from contextlib import closing
from datetime import datetime
from pathlib import Path

KEEP = 7
INTERVAL = 86400
PATTERN = 'workspace-*.sqlite3'
BACKUP_LOCK = threading.RLock()


def snapshots(folder):
    return sorted(Path(folder).glob(PATTERN))


def listing(folder):
    """Newest first, for the settings page."""
    items = []
    for path in reversed(snapshots(folder)):
        try:
            stat = path.stat()
        except OSError:
            continue
        items.append({'name': path.name, 'size': stat.st_size, 'modifiedAt': datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat()})
    return items


def run_once(db_path, folder, keep=KEEP, now=None, force=False):
    with BACKUP_LOCK:
        return _run_once(db_path, folder, keep, now, force)


def _run_once(db_path, folder, keep=KEEP, now=None, force=False):
    """Write one snapshot if the newest is older than INTERVAL (or `force`); returns its path or None."""
    now = time.time() if now is None else now
    db_path, folder = Path(db_path), Path(folder)
    if not db_path.is_file():
        return None
    existing = snapshots(folder)
    if existing and not force and now - existing[-1].stat().st_mtime < INTERVAL:
        return None
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.fromtimestamp(now).strftime('%Y%m%d-%H%M%S-%f')
    serial = 0
    target = folder / f'workspace-{stamp}-{serial:06d}.sqlite3'
    while target.exists():
        serial += 1
        target = folder / f'workspace-{stamp}-{serial:06d}.sqlite3'
    partial = target.with_name(target.name + '.partial')
    try:
        with closing(sqlite3.connect(db_path.resolve().as_uri() + '?mode=ro', uri=True, timeout=15)) as source, closing(sqlite3.connect(partial)) as copy:
            source.backup(copy)
        os.chmod(partial, 0o600)
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)
    for old in snapshots(folder)[:-keep]:
        old.unlink(missing_ok=True)
    return target


class RestoreError(Exception):
    pass


def restore(db_path, folder, name, keep=KEEP):
    """Replace the live database with snapshot `name`; the current data is snapshotted first.

    The chosen file is checked and loaded into memory before anything changes, so a bad file or a
    failed safety snapshot leaves the live database untouched. Returns the safety snapshot path.
    """
    chosen = {path.name: path for path in snapshots(folder)}.get(name) if isinstance(name, str) else None
    if not chosen:
        raise RestoreError('Không tìm thấy bản sao lưu này.')
    with closing(sqlite3.connect(':memory:')) as memory:
        try:
            with closing(sqlite3.connect(chosen.resolve().as_uri() + '?mode=ro', uri=True, timeout=15)) as source:
                if source.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise RestoreError('Bản sao lưu này bị hỏng, hãy chọn bản khác.')
                tables = {row[0] for row in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if not {'records', 'settings'} <= tables:
                    raise RestoreError('Tệp này không phải dữ liệu Freelance Desk.')
                source.backup(memory)
        except sqlite3.Error:
            raise RestoreError('Bản sao lưu này bị hỏng, hãy chọn bản khác.') from None
        safety = run_once(db_path, folder, keep=keep, force=True)
        with closing(sqlite3.connect(db_path, timeout=30)) as live:
            memory.backup(live)
    return safety


def worker(db_path, folder):
    while True:
        try:
            run_once(db_path, folder)
        except Exception:
            # Never log paths or contents; retry next hour.
            print('Backup skipped after an internal error.', flush=True)
        time.sleep(3600)

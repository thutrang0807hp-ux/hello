"""Settings storage counters: real file sizes, separate from estimated record payloads."""
import os
from pathlib import Path
import shutil
import sqlite3


def summary(connect, data):
    data = Path(data)
    groups = {'databaseBytes': 0, 'backupBytes': 0, 'otherBytes': 0}
    unreadable = 0
    def onerror(error):
        nonlocal unreadable
        unreadable += 1
    for folder, dirs, files in os.walk(data, followlinks=False, onerror=onerror):
        dirs[:] = [name for name in dirs if not (Path(folder) / name).is_symlink()]
        for name in files:
            path = Path(folder) / name
            if path.is_symlink():
                continue
            try:
                if not path.is_file():
                    continue
                size = path.stat().st_size
            except OSError:
                unreadable += 1
                continue
            relative = path.relative_to(data)
            category = ('databaseBytes' if len(relative.parts) == 1 and name in
                        ('workspace.sqlite3', 'workspace.sqlite3-wal', 'workspace.sqlite3-shm')
                        else 'backupBytes' if relative.parts[0] == 'backups' else 'otherBytes')
            groups[category] += size
    with connect() as db:
        records = {row['kind']: {'count': row['count'], 'contentBytes': row['bytes']}
                   for row in db.execute('SELECT kind, COUNT(*) AS count, COALESCE(SUM(LENGTH(CAST(body AS BLOB))),0) AS bytes FROM records GROUP BY kind')}
        mail = db.execute('SELECT COUNT(*) AS count, COALESCE(SUM(LENGTH(CAST(body AS BLOB))),0) AS bytes FROM upwork_mail').fetchone()
        jobs = records.get('job', {'count': 0, 'contentBytes': 0})
        letters = [records.get(kind, {'count': 0, 'contentBytes': 0}) for kind in ('proposal', 'sentproposal')]
    free = shutil.disk_usage(data).free
    return dict(groups, totalBytes=sum(groups.values()), freeBytes=free, incomplete=bool(unreadable),
                jobs=jobs, letters={'count': sum(r['count'] for r in letters), 'contentBytes': sum(r['contentBytes'] for r in letters)},
                mail={'count': mail['count'], 'contentBytes': mail['bytes']})


def compact(connect):
    try:
        with connect() as db:
            db.execute('VACUUM')
        return True
    except sqlite3.OperationalError:
        # Deletion has committed; keep the freed pages reusable when another connection is busy.
        return False

import json
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

import test_review_fixes as fixture
server = fixture.server
import backup
import job_cleanup
import storage_usage


class StorageApiTests(unittest.TestCase):
    setUpClass = classmethod(fixture.ReviewFixTests.setUpClass.__func__)
    tearDownClass = classmethod(fixture.ReviewFixTests.tearDownClass.__func__)
    raw = fixture.ReviewFixTests.raw
    call = fixture.ReviewFixTests.call

    def setUp(self):
        fixture.ReviewFixTests.setUp(self)
        with server.connect() as db:
            for table in ('job_history', 'job_interest_ever', 'upwork_mail'):
                db.execute('DELETE FROM '+table)

    def job(self, old=8, **fields):
        body = dict(name='Storage fixture', status='Đã lưu', receivedAt=datetime.fromtimestamp(time.time()-old*86400,timezone.utc).isoformat(), **fields)
        with server.connect() as db:
            return db.execute("INSERT INTO records(kind,body) VALUES('job',?)",(json.dumps(body),)).lastrowid

    def test_counts_and_preview_are_read_only(self):
        self.job()
        self.job(old=60, proposalSent=True)
        self.call('/api/records',{'kind':'proposal','name':'Draft'})
        usage = self.call('/api/storage')
        self.assertEqual(usage['jobs']['count'],2)
        self.assertEqual(usage['letters']['count'],1)
        self.assertGreater(usage['databaseBytes'],0)
        preview=self.call('/api/storage/preview',{})
        self.assertEqual(preview['count'],1)
        self.assertNotIn('ids',preview)
        self.assertEqual(len([r for r in server.records() if r['kind']=='job']),2)

    def test_confirmation_and_unchanged_preview_required(self):
        self.job()
        self.assertEqual(self.raw('/api/storage/cleanup',{})[0],400)
        preview=self.call('/api/storage/preview',{})
        self.job()
        status,_,_=self.raw('/api/storage/cleanup',{'confirm':True,'token':preview['token']})
        self.assertEqual(status,409)
        self.assertEqual(len([r for r in server.records() if r['kind']=='job']),2)

    def test_cleanup_snapshots_then_preserves_sent_and_mail(self):
        self.job()
        sent=self.job(old=60,proposalSent=True)
        with server.connect() as db:
            db.execute("INSERT INTO upwork_mail(id,body) VALUES('storage-mail',?)",(json.dumps({'subject':'Keep'}),))
        preview=self.call('/api/storage/preview',{})
        result=self.call('/api/storage/cleanup',{'confirm':True,'token':preview['token']})
        self.assertEqual(result['removed'],1)
        self.assertEqual(result['usage']['jobs']['count'],1)
        self.assertEqual(result['usage']['mail']['count'],1)
        self.assertEqual(server.records(sent)[0]['proposalSent'],True)
        self.assertEqual(len(job_cleanup.history(server.connect)),1)
        latest=backup.snapshots(server.DATA/'backups')[-1]
        with sqlite3.connect(latest) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM records WHERE kind='job'").fetchone()[0],2)

    def test_backup_failure_prevents_deletion(self):
        self.job()
        preview=self.call('/api/storage/preview',{})
        with patch.object(server.backup,'run_once',side_effect=OSError('fixture')):
            self.assertEqual(self.raw('/api/storage/cleanup',{'confirm':True,'token':preview['token']})[0],500)
        self.assertEqual(len([r for r in server.records() if r['kind']=='job']),1)

    def test_fresh_job_does_not_reuse_compact_history_identity(self):
        ident=self.job()
        job_cleanup.run_once(server.connect,server.cleanup_assessment)
        result=server.import_jobs({'event':'new_jobs','jobs':[{'id':'~new-after-cleanup','title':'Fresh','url':'https://www.upwork.com/jobs/~new-after-cleanup','description':'new'}]})
        self.assertEqual(result['created'],1)
        fresh=[r for r in server.records() if r['kind']=='job'][0]
        self.assertGreater(fresh['id'],ident)
        self.assertEqual(len(job_cleanup.history(server.connect)),1)

    def test_newly_protected_job_is_not_deleted_with_old_approval(self):
        ident=self.job()
        plan=job_cleanup.preview(server.connect)
        with server.connect() as db:
            db.execute("INSERT INTO records(kind,body) VALUES('proposal',?)",(json.dumps({'jobId':ident}),))
        self.assertEqual(job_cleanup.run_once(server.connect,server.cleanup_assessment,approved_ids=set(plan['ids'])),0)


class StorageFileTests(unittest.TestCase):
    def test_snapshot_forced_twice_in_same_instant_keeps_new_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);db=root/'workspace.sqlite3'
            with sqlite3.connect(db) as con:
                con.execute('CREATE TABLE records(id INTEGER PRIMARY KEY)')
            one=backup.run_once(db,root/'backups',now=1234567890,force=True)
            with sqlite3.connect(db) as con:
                con.execute('INSERT INTO records VALUES(1)')
            two=backup.run_once(db,root/'backups',now=1234567890,force=True)
            self.assertNotEqual(one,two)
            with sqlite3.connect(two) as con:
                self.assertEqual(con.execute('SELECT COUNT(*) FROM records').fetchone()[0],1)

    def test_file_sizes_match_and_symlinks_outside_data_are_not_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);data=root/'data';data.mkdir();(data/'backups').mkdir()
            (data/'backups/a.sqlite3').write_bytes(b'x'*30)
            (data/'other.log').write_bytes(b'x'*10)
            (root/'outside').write_bytes(b'x'*1000)
            try:(data/'outside-link').symlink_to(root/'outside')
            except OSError:pass
            db=data/'workspace.sqlite3'
            with sqlite3.connect(db) as con:
                con.execute('CREATE TABLE records(kind TEXT,body TEXT)')
                con.execute('CREATE TABLE upwork_mail(body TEXT)')
            class Closing(sqlite3.Connection):
                def __exit__(self,*args):
                    try:return super().__exit__(*args)
                    finally:self.close()
            def connect():
                con=sqlite3.connect(db,factory=Closing);con.row_factory=sqlite3.Row;return con
            info=storage_usage.summary(connect,data)
            self.assertEqual(info['backupBytes'],30)
            self.assertEqual(info['otherBytes'],10)
            self.assertEqual(info['totalBytes'],db.stat().st_size+40)

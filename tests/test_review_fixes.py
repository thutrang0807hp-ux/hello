import http.cookiejar
import json
import os
import secrets
import sqlite3
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

if 'server' not in __import__('sys').modules:
    TEST_DATA = tempfile.TemporaryDirectory()
    os.environ['FREELANCE_DATA_DIR'] = TEST_DATA.name
    os.environ['FREELANCE_PASSWORD'] = secrets.token_urlsafe(24)
    for variable in ['FREELANCE_AI_KEY', 'FREELANCE_SLACK_TOKEN', 'FREELANCE_SLACK_CHANNEL', 'FREELANCE_TELEGRAM_TOKEN', 'FREELANCE_TELEGRAM_CHAT_ID']:
        os.environ.pop(variable, None)
import server
import backup
import job_cleanup
from datetime import datetime, timezone


class ReviewFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.base = 'http://127.0.0.1:' + str(cls.http.server_port)
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()

    def setUp(self):
        with server.connect() as db:
            for table in ['records', 'settings', 'imported_jobs', 'outbox', 'job_interest', 'job_reviews']:
                db.execute('DELETE FROM ' + table)
        server.SESSIONS.clear()
        server.LOGIN_ATTEMPTS.clear()
        self.client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        if server.PASSWORD:
            self.call('/api/login', {'password': server.PASSWORD})

    def raw(self, path, data=None):
        request = urllib.request.Request(self.base + path, data=json.dumps(data).encode() if data is not None else None, headers={'Content-Type': 'application/json'})
        try:
            with self.client.open(request) as response:
                return response.status, dict(response.headers), json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, dict(error.headers), json.load(error)

    def call(self, path, data=None):
        status, _, body = self.raw(path, data)
        self.assertEqual(status, 200, body)
        return body

    def test_poll_skips_unchanged_records_and_sees_writes(self):
        self.call('/api/records', {'kind': 'client', 'name': 'Anna'})
        _, headers, first = self.raw('/api/records')
        version = headers['X-Records-Version']
        self.assertEqual([r['name'] for r in first], ['Anna'])
        _, headers, again = self.raw('/api/records?since=' + version)
        self.assertEqual(again, {'unchanged': True})
        self.assertEqual(headers['X-Records-Version'], version)
        self.call('/api/records', {'kind': 'client', 'name': 'Ben'})
        _, headers, changed = self.raw('/api/records?since=' + version)
        self.assertEqual([r['name'] for r in changed], ['Ben', 'Anna'])
        self.assertNotEqual(headers['X-Records-Version'], version)

    def test_single_record_lookup_matches_full_list(self):
        ident = self.call('/api/records', {'kind': 'client', 'name': 'Anna'})['id']
        self.call('/api/records', {'kind': 'client', 'name': 'Ben'})
        self.assertEqual(server.records(ident), [r for r in server.records() if r['id'] == ident])

    def test_invalid_daily_tasks_rejected_on_create_and_corrupt_saved_value_tolerated(self):
        status, _, body = self.raw('/api/records', {'kind': 'client', 'name': 'Anna', 'dailyTasks': 'abc'})
        self.assertEqual(status, 400, body)
        with server.connect() as db:
            ident = db.execute("INSERT INTO records(kind,body) VALUES ('client',?)", (json.dumps({'name': 'Old', 'dailyTasks': 'abc'}),)).lastrowid
        task = {'id': 't1', 'title': 'Gửi bản nháp', 'done': False}
        saved = self.call('/api/records', {'kind': 'client', 'id': ident, 'name': 'Old', 'dailyTasks': [task]})
        self.assertEqual(saved['dailyTasks'], [task])

    def test_unexpected_error_answers_json_500(self):
        with patch.object(server, 'settings', side_effect=RuntimeError('boom')):
            status, _, body = self.raw('/api/settings')
        self.assertEqual(status, 500)
        self.assertIn('error', body)
        self.assertNotIn('boom', body['error'])

    def job(self):
        server.import_jobs({'event': 'new_jobs', 'jobs': [{'id': '~fix1', 'title': 'Edit videos', 'url': 'https://www.upwork.com/jobs/~fix1', 'description': 'Edit two videos.'}]})
        return next(r for r in server.records() if r['kind'] == 'job')['id']

    def projects(self):
        return [r for r in server.records() if r['kind'] == 'project']

    def test_unmarking_sent_removes_unwon_project_only(self):
        ident = self.job()
        self.call('/api/jobs/proposal-sent', {'id': ident, 'sent': True})
        self.assertEqual(len(self.projects()), 1)
        self.call('/api/jobs/proposal-sent', {'id': ident, 'sent': False})
        self.assertEqual(self.projects(), [])
        self.call('/api/jobs/proposal-sent', {'id': ident, 'sent': True})
        self.call('/api/projects/contract', {'id': self.projects()[0]['id'], 'won': True})
        self.call('/api/jobs/proposal-sent', {'id': ident, 'sent': False})
        self.assertEqual(len(self.projects()), 1)

    def test_clearing_contract_keeps_lost_outcome(self):
        ident = self.job()
        self.call('/api/jobs/proposal-sent', {'id': ident, 'sent': True})
        with server.connect() as db:
            lost = db.execute("INSERT INTO records(kind,body) VALUES ('sentproposal',?)", (json.dumps({'name': 'A', 'jobId': ident, 'outcome': 'lost'}),)).lastrowid
            won = db.execute("INSERT INTO records(kind,body) VALUES ('sentproposal',?)", (json.dumps({'name': 'B', 'jobId': ident, 'outcome': 'won'}),)).lastrowid
        self.call('/api/projects/contract', {'id': self.projects()[0]['id'], 'won': False})
        outcomes = {r['id']: r['outcome'] for r in server.records() if r['kind'] == 'sentproposal'}
        self.assertEqual(outcomes, {lost: 'lost', won: 'pending'})

    def test_backup_now_listed_in_settings_and_open_uses_fixed_folder(self):
        self.call('/api/records', {'kind': 'client', 'name': 'Anna'})
        result = self.call('/api/backups/now', {})
        self.assertTrue(result['items'][0]['name'].startswith('workspace-'))
        info = self.call('/api/settings')['backups']
        self.assertEqual(info['folder'], str(server.DATA / 'backups'))
        self.assertEqual(info['items'][0]['name'], result['items'][0]['name'])
        with patch('os.startfile', create=True) as start, patch('subprocess.Popen') as popen:
            self.call('/api/backups/open', {'folder': '/etc'})
        opened = start.call_args[0][0] if start.called else popen.call_args[0][0][1]
        self.assertEqual(str(opened), str(server.DATA / 'backups'))

    def test_restore_endpoint_brings_back_snapshot_and_keeps_current_copy(self):
        for name in [p.name for p in backup.snapshots(server.DATA / 'backups')]:
            (server.DATA / 'backups' / name).unlink()
        self.call('/api/records', {'kind': 'client', 'name': 'Anna'})
        first = self.call('/api/backups/now', {})['items'][0]['name']
        time.sleep(1.1)
        self.call('/api/records', {'kind': 'client', 'name': 'Ben'})
        result = self.call('/api/backups/restore', {'name': first})
        self.assertEqual([r['name'] for r in server.records()], ['Anna'])
        safety = sqlite3.connect(server.DATA / 'backups' / result['safety'])
        self.assertEqual(sorted(json.loads(r[0])['name'] for r in safety.execute("SELECT body FROM records")), ['Anna', 'Ben'])
        safety.close()
        # Tables added after the snapshot was taken exist again and the app keeps working.
        self.call('/api/records', {'kind': 'client', 'name': 'Chi'})
        self.call('/api/jobs/history')

    def test_restore_rejects_unknown_name(self):
        for name in ['../workspace.sqlite3', 'missing.sqlite3', None]:
            status, _, body = self.raw('/api/backups/restore', {'name': name})
            self.assertEqual(status, 400, body)

    def test_connection_closed_after_block(self):
        with server.connect() as db:
            db.execute('SELECT 1')
        with self.assertRaises(sqlite3.ProgrammingError):
            db.execute('SELECT 1')


class JobCleanupTests(unittest.TestCase):
    def setUp(self):
        with server.connect() as db:
            for table in ['records', 'imported_jobs', 'job_interest', 'job_reviews', 'job_history', 'job_interest_ever']:
                db.execute('DELETE FROM ' + table)

    def add(self, days_old, external, **extra):
        server.import_jobs({'event': 'new_jobs', 'jobs': [{'id': external, 'title': 'Job ' + external, 'url': 'https://www.upwork.com/jobs/' + external, 'description': 'd'}]})
        with server.connect() as db:
            row = db.execute("SELECT r.id,r.body FROM imported_jobs i JOIN records r ON r.id=i.record_id WHERE i.external_id=?", (external,)).fetchone()
            body = dict(json.loads(row['body']), receivedAt=datetime.fromtimestamp(time.time() - days_old * 86400, timezone.utc).isoformat(), **extra)
            db.execute('UPDATE records SET body=? WHERE id=?', (json.dumps(body), row['id']))
        return row['id']

    def names(self):
        return sorted(r['name'] for r in server.records() if r['kind'] == 'job')

    def run_cleanup(self):
        return job_cleanup.run_once(server.connect, server.cleanup_assessment)

    def test_normal_after_7_days_saved_after_14(self):
        self.add(6, '~fresh')
        self.add(8, '~old')
        saved = self.add(8, '~saved')
        older_saved = self.add(15, '~oldsaved')
        with server.connect() as db:
            job_cleanup.mark_interest(db, saved)
            job_cleanup.mark_interest(db, older_saved)
        self.assertEqual(self.run_cleanup(), 2)
        self.assertEqual(self.names(), ['Job ~fresh', 'Job ~saved'])

    def test_interest_expiry_does_not_shorten_saved_window(self):
        ident = self.add(10, '~expired')
        with server.connect() as db:
            db.execute('INSERT INTO job_interest VALUES (?,?)', (ident, time.time() - 1))
        job_cleanup.init(server.connect)
        server.records()  # drops the expired interest row, as every poll does
        with server.connect() as db:
            job_cleanup.mark_interest(db, ident)
        self.run_cleanup()
        self.assertEqual(self.names(), ['Job ~expired'])

    def test_protected_jobs_never_removed(self):
        self.add(60, '~sent', proposalSent=True)
        self.add(60, '~status', status='Phỏng vấn')
        drafted = self.add(60, '~draft')
        with server.connect() as db:
            db.execute("INSERT INTO records(kind,body) VALUES ('proposal',?)", (json.dumps({'name': 'W', 'jobId': drafted}),))
        self.assertEqual(self.run_cleanup(), 0)
        self.assertEqual(len(self.names()), 3)

    def test_removed_job_kept_in_history_and_not_reimported(self):
        self.add(9, '~gone')
        self.run_cleanup()
        history = job_cleanup.history(server.connect)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['kind'], 'jobstat')
        self.assertIn('receivedAt', history[0])
        self.assertNotIn('notes', history[0])
        result = server.import_jobs({'event': 'new_jobs', 'jobs': [{'id': '~gone', 'title': 'Job ~gone', 'url': 'https://www.upwork.com/jobs/~gone', 'description': 'd'}]})
        self.assertEqual(result, {'created': 0, 'duplicates': 1})
        self.assertEqual(self.names(), [])


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / 'workspace.sqlite3'
        self.folder = Path(self.tmp.name) / 'backups'
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE records (id INTEGER PRIMARY KEY, body TEXT)')
            db.execute("INSERT INTO records(body) VALUES ('khách A')")
        db.close()

    def tearDown(self):
        self.tmp.cleanup()

    def test_daily_snapshot_is_readable_and_skipped_within_a_day(self):
        now = time.time()
        first = backup.run_once(self.db, self.folder, now=now)
        copy = sqlite3.connect(first)
        self.assertEqual(copy.execute('SELECT body FROM records').fetchone()[0], 'khách A')
        copy.close()
        self.assertIsNone(backup.run_once(self.db, self.folder, now=now + 3600))
        self.assertEqual(list(self.folder.glob('*.partial')), [])

    def test_keeps_only_newest_snapshots(self):
        start = time.time()
        for day in range(10):
            path = backup.run_once(self.db, self.folder, keep=3, now=start + day * 86400)
            os.utime(path, (start + day * 86400,) * 2)
        names = [p.name for p in backup.snapshots(self.folder)]
        self.assertEqual(len(names), 3)
        self.assertEqual(names[-1], path.name)

    def live_names(self):
        with closing(sqlite3.connect(self.db)) as db:
            return [r[0] for r in db.execute('SELECT body FROM records ORDER BY id')]

    def add_settings(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, body TEXT)')

    def test_restore_oldest_snapshot_even_if_safety_copy_prunes_it(self):
        self.add_settings()
        start = time.time()
        oldest = backup.run_once(self.db, self.folder, keep=3, now=start).name
        for day in (1, 2):
            backup.run_once(self.db, self.folder, keep=3, now=start + day * 86400)
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("INSERT INTO records(body) VALUES ('khách B')")
        backup.restore(self.db, self.folder, oldest, keep=3)
        self.assertEqual(self.live_names(), ['khách A'])

    def test_corrupt_or_foreign_snapshot_leaves_live_data_untouched(self):
        self.add_settings()
        self.folder.mkdir()
        (self.folder / 'workspace-20260101-000000.sqlite3').write_bytes(b'not a database' * 100)
        with closing(sqlite3.connect(self.folder / 'workspace-20260102-000000.sqlite3')) as other, other:
            other.execute('CREATE TABLE notes (x)')
        for name in ('workspace-20260101-000000.sqlite3', 'workspace-20260102-000000.sqlite3'):
            with self.assertRaises(backup.RestoreError):
                backup.restore(self.db, self.folder, name)
        self.assertEqual(self.live_names(), ['khách A'])
        self.assertEqual(len(backup.snapshots(self.folder)), 2)  # no safety copy made for a rejected file

    def test_missing_database_does_nothing(self):
        self.assertIsNone(backup.run_once(Path(self.tmp.name) / 'none.sqlite3', self.folder))
        self.assertFalse(self.folder.exists())


if __name__ == '__main__':
    unittest.main()

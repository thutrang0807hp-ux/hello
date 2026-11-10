"""Remove old feed jobs so the database stays small.

Normal jobs: 7 days after receivedAt. Jobs ever marked "Quan tâm" or analysed by AI: 14 days.
Never removed: proposal sent, status changed by the user, or referenced by a proposal/sent letter/project.
A tiny row (dates + assessment colour) is kept in job_history so long-range analytics stay correct;
imported_jobs is kept so a removed job never comes back from the feed.
"""
import json
import time
from datetime import datetime

NORMAL_DAYS = 7
SAVED_DAYS = 14
DEFAULT_STATUS = 'Đã lưu'


def init(connect):
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS job_history (record_id INTEGER PRIMARY KEY, body TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS job_interest_ever (record_id INTEGER PRIMARY KEY)')
        # Jobs marked before this table existed still count as saved.
        db.execute('INSERT OR IGNORE INTO job_interest_ever SELECT record_id FROM job_interest')


def mark_interest(db, ident):
    db.execute('INSERT OR IGNORE INTO job_interest_ever VALUES (?)', (ident,))


def received(job):
    try:
        stamp = datetime.fromisoformat(str(job.get('receivedAt', '')).replace('Z', '+00:00'))
        return stamp.timestamp() if stamp.tzinfo else None
    except ValueError:
        return None


def candidates(db, now):
    """Compute eligibility inside the caller's transaction; never rely on UI state."""
    referenced = set()
    for row in db.execute("SELECT body FROM records WHERE kind IN ('proposal','sentproposal','project')"):
        ident = json.loads(row['body']).get('jobId')
        if ident not in (None, ''):
            referenced.add(str(ident))
    saved = {r[0] for r in db.execute('SELECT record_id FROM job_interest_ever')}
    saved |= {r[0] for r in db.execute('SELECT record_id FROM job_interest')}
    reviews = {r['record_id']: r for r in db.execute('SELECT record_id,signature,body FROM job_reviews')}
    saved |= {ident for ident, row in reviews.items() if not json.loads(row['body']).get('error')}
    result = []
    for row in db.execute("SELECT id,body FROM records WHERE kind='job'").fetchall():
        job = json.loads(row['body'])
        stamp = received(job)
        if stamp is None or job.get('proposalSent') or job.get('status', DEFAULT_STATUS) != DEFAULT_STATUS or str(row['id']) in referenced:
            continue
        days = SAVED_DAYS if row['id'] in saved else NORMAL_DAYS
        if now - stamp >= days * 86400:
            result.append((row['id'], job, reviews.get(row['id']), len(row['body'].encode('utf-8'))))
    return result


def preview(connect, now=None):
    import hashlib
    with connect() as db:
        rows = candidates(db, time.time() if now is None else now)
    ids = sorted(row[0] for row in rows)
    token = hashlib.sha256(json.dumps(ids).encode()).hexdigest()
    return {'count': len(ids), 'contentBytes': sum(row[3] for row in rows), 'token': token, 'ids': ids}


def run_once(connect, present, now=None, approved_ids=None):
    """Delete eligible jobs, preserving compact history and the imported ID tombstones."""
    now = time.time() if now is None else now
    removed = 0
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        for ident, job, review, _ in candidates(db, now):
            if approved_ids is not None and ident not in approved_ids:
                continue
            assessment = present(dict(job, id=ident, kind='job'), review) or {}
            history = {'receivedAt': job.get('receivedAt'), 'postedAt': job.get('postedAt'), 'jobAssessment': {'state': assessment.get('state'), 'color': assessment.get('color')}}
            db.execute('INSERT OR REPLACE INTO job_history VALUES (?,?)', (ident, json.dumps(history, ensure_ascii=False)))
            for statement in ('DELETE FROM records WHERE id=?', 'DELETE FROM job_interest WHERE record_id=?', 'DELETE FROM job_reviews WHERE record_id=?', 'DELETE FROM job_interest_ever WHERE record_id=?'):
                db.execute(statement, (ident,))
            removed += 1
    return removed


def history(connect):
    """Compact entries for analytics charts; kind 'jobstat' never appears in job lists."""
    with connect() as db:
        return [dict(json.loads(r['body']), kind='jobstat') for r in db.execute('SELECT body FROM job_history ORDER BY record_id DESC')]


def worker(connect, present):
    while True:
        try:
            run_once(connect, present)
        except Exception:
            print('Job cleanup skipped after an internal error.', flush=True)
        time.sleep(3600)

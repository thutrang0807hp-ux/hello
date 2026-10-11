import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import threading
import time
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from reference_synthesis import library_pool
import job_radar
import job_activity
from client_lifecycle import archive_unanswered, record_client_events
from local_config import load
from services import ServiceError, channels, evaluate_proposal, generate_proposal, normalize_job, send_notification, text
from workflow import validate_workspace

load()
ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('FREELANCE_DATA_DIR', ROOT / 'data'))
DATA.mkdir(parents=True, exist_ok=True)
DB = DATA / 'workspace.sqlite3'
PASSWORD = os.environ.get('FREELANCE_PASSWORD', '')
BIND = os.environ.get('FREELANCE_BIND', '127.0.0.1')
if BIND not in ('127.0.0.1', 'localhost', '::1') and not PASSWORD:
    raise RuntimeError('FREELANCE_PASSWORD is required when binding outside loopback.')
TOKEN_FILE = DATA / 'webhook-token'
if os.environ.get('FREELANCE_WEBHOOK_TOKEN'):
    WEBHOOK_TOKEN = os.environ['FREELANCE_WEBHOOK_TOKEN']
else:
    try:
        with TOKEN_FILE.open('x') as token_file:
            token_file.write(secrets.token_urlsafe(32))
        TOKEN_FILE.chmod(0o600)
    except FileExistsError:
        pass
    WEBHOOK_TOKEN = TOKEN_FILE.read_text().strip()
if len(WEBHOOK_TOKEN) < 24:
    raise RuntimeError('Webhook token must contain at least 24 characters.')
SESSIONS = {}
LOGIN_ATTEMPTS = {}
LOCK = threading.Lock()


def connect():
    db = sqlite3.connect(DB, timeout=15)
    db.row_factory = sqlite3.Row
    return db


with connect() as db:
    db.execute('CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS imported_jobs (external_id TEXT PRIMARY KEY, record_id INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS outbox (id INTEGER PRIMARY KEY, channel TEXT NOT NULL, body TEXT NOT NULL, status TEXT NOT NULL DEFAULT \'pending\', attempts INTEGER NOT NULL DEFAULT 0, next_try REAL NOT NULL DEFAULT 0, error TEXT)')


with connect() as db:
    db.execute('CREATE TABLE IF NOT EXISTS job_interest (record_id INTEGER PRIMARY KEY, expires REAL NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS job_reviews (record_id INTEGER PRIMARY KEY, signature TEXT NOT NULL, body TEXT NOT NULL)')


def job_signature(job):
    return hashlib.sha256(json.dumps(job_radar.context(job), sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def job_worker():
    while True:
        try:
            if os.environ.get('FREELANCE_AI_KEY'):
                for job in records():
                    if job['kind'] != 'job': continue
                    signature = job_signature(job)
                    with connect() as db:
                        old = db.execute('SELECT signature FROM job_reviews WHERE record_id=?',(job['id'],)).fetchone()
                    if old and old['signature'] == signature: continue
                    try: review = job_radar.evaluate(job)
                    except ServiceError as error: review = {'error':str(error)}
                    with connect() as db:
                        db.execute('INSERT OR REPLACE INTO job_reviews VALUES (?,?,?)',(job['id'],signature,json.dumps(review,ensure_ascii=False)))
            time.sleep(3)
        except Exception:
            time.sleep(5)


def settings():
    with connect() as db:
        row = db.execute('SELECT body FROM settings WHERE id=1').fetchone()
        return json.loads(row['body']) if row else {}


def ensure_project(db, job_id, job):
    for row in db.execute("SELECT body FROM records WHERE kind='project'"):
        if json.loads(row['body']).get('jobId') == job_id:
            return
    project = {key: job.get(key) for key in ('name','budget','url','clientInfo','notes')}
    project.update(jobId=job_id, sentAt=job.get('proposalSentAt') or datetime.now(timezone.utc).isoformat(), won=False, wonAt=None)
    db.execute("INSERT INTO records(kind,body) VALUES ('project',?)", (json.dumps(project,ensure_ascii=False),))

with connect() as db:
    for row in db.execute("SELECT id,body FROM records WHERE kind='job'").fetchall():
        job=json.loads(row['body'])
        if job.get('proposalSent'): ensure_project(db,row['id'],job)


def records():
    with connect() as db:
        db.execute('DELETE FROM job_interest WHERE expires<=?', (time.time(),))
        for row in db.execute("SELECT id,body FROM records WHERE kind='client'").fetchall():
            archived = archive_unanswered(json.loads(row['body']))
            if archived:
                db.execute('UPDATE records SET body=? WHERE id=?', (json.dumps(archived,ensure_ascii=False),row['id']))
        interests = {r['record_id']:r['expires'] for r in db.execute('SELECT * FROM job_interest')}
        reviews = {r['record_id']:r for r in db.execute('SELECT * FROM job_reviews')}
        items = [dict(json.loads(row['body']), id=row['id'], kind=row['kind']) for row in db.execute('SELECT * FROM records ORDER BY id DESC')]
    for job in items:
        if job['kind'] != 'job': continue
        expiry = interests.get(job['id'])
        job['interested'] = bool(expiry)
        job['interestExpiresAt'] = datetime.fromtimestamp(expiry,timezone.utc).isoformat() if expiry else None
        cached = reviews.get(job['id'])
        review = json.loads(cached['body']) if cached and cached['signature']==job_signature(job) else None
        job['jobAssessment'] = job_radar.present(job,review)
    return items


def import_jobs(payload):
    if not isinstance(payload, dict) or payload.get('event') != 'new_jobs' or not isinstance(payload.get('jobs'), list) or len(payload['jobs']) > 100:
        raise ServiceError('Webhook cần event new_jobs và tối đa 100 job.')
    jobs = [normalize_job(raw) for raw in payload['jobs']]
    created, duplicate = 0, 0
    enabled = channels()
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        for job in jobs:
            old = db.execute("SELECT r.id,r.body FROM imported_jobs i LEFT JOIN records r ON r.id=i.record_id AND r.kind='job' WHERE i.external_id=?", (job['externalId'],)).fetchone()
            if old:
                duplicate += 1
                if old['body'] and json.loads(old['body']).get('externalId') == job['externalId'] and job.get('clientActivity'):
                    saved = job_activity.merge(json.loads(old['body']),job['clientActivity'])
                    db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(saved,ensure_ascii=False),old['id']))
                continue
            ident = db.execute('INSERT INTO records(kind,body) VALUES (?,?)', ('job', json.dumps(job, ensure_ascii=False))).lastrowid
            db.execute('INSERT INTO imported_jobs VALUES (?,?)', (job['externalId'], ident))
            created += 1
            for channel, active in enabled.items():
                if active:
                    db.execute('INSERT INTO outbox(channel,body) VALUES (?,?)', (channel, json.dumps(job, ensure_ascii=False)))
    return {'created': created, 'duplicates': duplicate}


def process_outbox():
    with connect() as db:
        row = db.execute("SELECT * FROM outbox WHERE status='pending' AND next_try<=? ORDER BY id LIMIT 1", (time.time(),)).fetchone()
    if not row:
        return False
    try:
        send_notification(row['channel'], json.loads(row['body']))
        with connect() as db:
            db.execute("UPDATE outbox SET status='sent', error=NULL, attempts=attempts+1 WHERE id=?", (row['id'],))
    except ServiceError as error:
        attempts = row['attempts'] + 1
        with connect() as db:
            db.execute('UPDATE outbox SET status=?, error=?, attempts=?, next_try=? WHERE id=?', ('failed' if attempts >= 5 else 'pending', str(error), attempts, time.time() + min(900, 30 * 2 ** attempts), row['id']))
    return True


def notification_worker():
    while True:
        try:
            if not process_outbox():
                time.sleep(2)
        except Exception:
            # Never log URLs or provider exceptions; they can contain secrets.
            print('Notification worker waiting after an internal error.', flush=True)
            time.sleep(5)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f'{self.command} {self.route} request', flush=True)

    @property
    def route(self):
        path = urlsplit(self.path).path
        return '/api/webhook/[redacted]' if path.startswith('/api/webhook/') else path

    def reply(self, status, body, headers=None):
        raw = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(raw)

    def authorized(self):
        if not PASSWORD:
            return True
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie', ''))
        except Exception:
            return False
        session = cookie.get('freelance_session')
        if not session:
            return False
        with LOCK:
            return SESSIONS.get(session.value, 0) > time.time()

    def same_origin(self):
        origin = self.headers.get('Origin')
        if not origin:
            return True
        parsed = urlsplit(origin)
        return parsed.scheme in ('http', 'https') and parsed.netloc == self.headers.get('Host', '')

    def read_json(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 1048576:
                raise ServiceError('Dữ liệu không hợp lệ hoặc quá lớn.')
            if self.headers.get_content_type() != 'application/json':
                raise ServiceError('Yêu cầu cần Content-Type application/json.', 415)
            return json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError):
            raise ServiceError('JSON không hợp lệ.') from None

    def guard(self):
        if not PASSWORD:
            try:
                host = urlsplit('http://' + self.headers.get('Host', '')).hostname
            except ValueError:
                host = None
            if host not in ('127.0.0.1', 'localhost', '::1'):
                self.reply(403, {'error': 'Truy cập nội bộ cần địa chỉ localhost.'})
                return False
        if not self.authorized():
            self.reply(401, {'error': 'Vui lòng đăng nhập.'})
            return False
        if self.command != 'GET' and not self.same_origin():
            self.reply(403, {'error': 'Nguồn yêu cầu không hợp lệ.'})
            return False
        return True

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/auth':
            return self.reply(200, {'required': bool(PASSWORD), 'authenticated': self.authorized()})
        if path.startswith('/api/'):
            if not self.guard():
                return
            if path == '/api/records':
                return self.reply(200, records())
            if path == '/api/settings':
                with connect() as db:
                    delivery = [dict(row) for row in db.execute('SELECT id,channel,status,attempts,error FROM outbox ORDER BY id DESC LIMIT 20')]
                return self.reply(200, {'profile': settings(), 'aiConfigured': bool(os.environ.get('FREELANCE_AI_KEY')), 'aiModel': os.environ.get('FREELANCE_AI_MODEL', 'gpt-4.1-mini'), 'passwordConfigured': bool(PASSWORD), 'webhookPath': '/api/webhook/' + WEBHOOK_TOKEN, 'channels': channels(), 'deliveries': delivery})
            return self.reply(404, {'error': 'Không tìm thấy.'})
        files = {'/theme.js': 'theme.js', '/message-templates.js': 'message-templates.js', '/': 'index.html', '/app.js': 'app.js', '/focus.js': 'focus.js', '/analytics.js': 'analytics.js', '/excel.js': 'excel.js', '/us-context.js': 'us-context.js', '/studio.js': 'studio.js', '/template-library.js': 'template-library.js', '/jobs.js': 'jobs.js', '/job-filters.js': 'job-filters.js', '/style.css': 'style.css'}
        if path in files:
            file = ROOT / 'public' / files[path]
            raw = file.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', {'html': 'text/html; charset=utf-8', 'js': 'text/javascript; charset=utf-8', 'css': 'text/css; charset=utf-8'}[file.suffix[1:]])
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(raw)
            return
        self.reply(404, {'error': 'Không tìm thấy.'})

    def do_POST(self):
        path = urlsplit(self.path).path
        try:
            if path.startswith('/api/webhook/'):
                token = path.removeprefix('/api/webhook/')
                if not hmac.compare_digest(token.encode(), WEBHOOK_TOKEN.encode()):
                    return self.reply(403, {'error': 'Webhook không được phép.'})
                return self.reply(200, import_jobs(self.read_json()))
            if path == '/api/login':
                if not self.same_origin():
                    return self.reply(403, {'error': 'Nguồn yêu cầu không hợp lệ.'})
                payload = self.read_json()
                password = payload.get('password', '') if isinstance(payload, dict) else ''
                if not isinstance(password, str) or len(password) > 1000:
                    raise ServiceError('Mật khẩu không hợp lệ.')
                address = self.client_address[0]
                now = time.time()
                with LOCK:
                    attempts = [stamp for stamp in LOGIN_ATTEMPTS.get(address, []) if stamp > now - 60]
                    if len(attempts) >= 10:
                        return self.reply(429, {'error': 'Quá nhiều lần đăng nhập. Thử lại sau một phút.'})
                    LOGIN_ATTEMPTS[address] = attempts + [now]
                if not PASSWORD or not hmac.compare_digest(hashlib.sha256(password.encode()).digest(), hashlib.sha256(PASSWORD.encode()).digest()):
                    return self.reply(401, {'error': 'Mật khẩu chưa đúng.'})
                session = secrets.token_urlsafe(32)
                with LOCK:
                    for expired in [key for key, expiry in SESSIONS.items() if expiry <= now]:
                        del SESSIONS[expired]
                    SESSIONS[session] = now + 86400
                    LOGIN_ATTEMPTS.pop(address, None)
                secure = '; Secure' if os.environ.get('FREELANCE_COOKIE_SECURE') == '1' else ''
                return self.reply(200, {'ok': True}, {'Set-Cookie': f'freelance_session={session}; HttpOnly; SameSite=Strict; Path=/; Max-Age=86400{secure}'})
            if not self.guard():
                return
            if path == '/api/logout':
                cookie = SimpleCookie(self.headers.get('Cookie', ''))
                if cookie.get('freelance_session'):
                    with LOCK:
                        SESSIONS.pop(cookie['freelance_session'].value, None)
                return self.reply(200, {'ok': True}, {'Set-Cookie': 'freelance_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'})
            if path == '/api/notifications/retry':
                with connect() as db:
                    db.execute("UPDATE outbox SET status='pending', attempts=0, next_try=0, error=NULL WHERE status='failed'")
                return self.reply(200, {'ok': True})
            item = self.read_json()
            if not isinstance(item, dict):
                raise ServiceError('Dữ liệu phải là đối tượng JSON.')
            if path == '/api/proposals/send':
                ident = item.get('id')
                if type(ident) is not int:
                    raise ServiceError('Workspace chưa được lưu.')
                with connect() as db:
                    db.execute('BEGIN IMMEDIATE')
                    row = db.execute("SELECT body FROM records WHERE id=? AND kind='proposal'", (ident,)).fetchone()
                    if not row:
                        raise ServiceError('Không tìm thấy workspace.', 404)
                    proposal = json.loads(row['body'])
                    nodes = proposal.get('workspace', {}).get('nodes', [])
                    final = next((n for n in nodes if n.get('id') == item.get('finalNodeId') and n.get('type') == 'final'), None)
                    if not final or not text(final.get('content')):
                        raise ServiceError('Node thư cuối đang trống hoặc không tồn tại.')
                    body = final['content']
                    old = db.execute("SELECT id,body FROM records WHERE kind='sentproposal'").fetchall()
                    duplicate = next((r for r in old if json.loads(r['body']).get('sourceProposalId') == ident and json.loads(r['body']).get('body') == body), None)
                    if duplicate:
                        return self.reply(200, {'duplicate': True, 'id': duplicate['id']})
                    job = db.execute("SELECT body FROM records WHERE id=? AND kind='job'", (proposal.get('jobId'),)).fetchone()
                    review = None
                    node_by_id = {n['id']: n for n in nodes}
                    edges = proposal.get('workspace', {}).get('edges', [])
                    def upstream(node_id, seen=None):
                        seen = set() if seen is None else seen
                        found = []
                        for edge in edges:
                            if edge.get('to') == node_id and edge.get('from') not in seen:
                                seen.add(edge.get('from'))
                                source = node_by_id.get(edge.get('from'))
                                if source:
                                    found.append(source)
                                    found.extend(upstream(source['id'], seen))
                        return found
                    for node in nodes:
                        try:
                            signature = json.loads(node.get('inputSignature', '{}'))
                            inputs = upstream(node['id'])
                            requirements = '\n\n'.join(n.get('content', '') for n in inputs if n.get('type') == 'job')
                            reviewed = next((n for n in inputs if n.get('type') in ('draft', 'final')), {})
                            source_job = next((n for n in inputs if n.get('type') == 'job'), {})
                            drafting = next((n for n in inputs if n.get('type') == 'draft'), {})
                            budget = reviewed.get('budget') or drafting.get('budget') or source_job.get('budget') or ''
                            if node.get('type') == 'review' and node.get('evaluation') and signature.get('body') == body == reviewed.get('content') and signature.get('requirements') == requirements and signature.get('budget') == budget and signature.get('profile') == settings():
                                review = node['evaluation']
                        except (ValueError, TypeError):
                            pass
                    snapshot = {'name': proposal['name'], 'body': body, 'sourceProposalId': ident, 'jobId': proposal.get('jobId'), 'clientId': proposal.get('clientId'), 'jobName': json.loads(job['body'])['name'] if job else '', 'sentAt': datetime.now(timezone.utc).isoformat(), 'outcome': 'pending', 'outcomeNotes': '', 'reviewAtSend': review, 'workspaceSnapshot': proposal.get('workspace'), 'finalNodeId': final['id']}
                    sent_id = db.execute("INSERT INTO records(kind,body) VALUES ('sentproposal',?)", (json.dumps(snapshot, ensure_ascii=False),)).lastrowid
                    if job:
                        job_body=json.loads(job['body'])
                        job_body['proposalSent']=True
                        job_body['proposalSentAt']=job_body.get('proposalSentAt') or snapshot['sentAt']
                        db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(job_body,ensure_ascii=False),proposal.get('jobId')))
                        ensure_project(db,proposal.get('jobId'),job_body)
                    proposal['status'] = 'Đã gửi'
                    db.execute('UPDATE records SET body=? WHERE id=?', (json.dumps(proposal, ensure_ascii=False), ident))
                return self.reply(200, {'id': sent_id, 'duplicate': False})
            if path == '/api/settings':
                profile = {key: text(item.get(key)) for key in ('name', 'services', 'experience', 'portfolio', 'tone')}
                with connect() as db:
                    db.execute('INSERT INTO settings(id,body) VALUES (1,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body', (json.dumps(profile, ensure_ascii=False),))
                return self.reply(200, {'ok': True})
            if path == '/api/jobs/proposal-sent':
                ident=item.get('id')
                sent=item.get('sent')
                if type(ident) is not int or type(sent) is not bool:
                    raise ServiceError('ID job và trạng thái đã gửi không hợp lệ.')
                with connect() as db:
                    db.execute('BEGIN IMMEDIATE')
                    row=db.execute("SELECT body FROM records WHERE id=? AND kind='job'",(ident,)).fetchone()
                    if not row: raise ServiceError('Không tìm thấy job.',404)
                    saved=json.loads(row['body'])
                    saved['proposalSentAt']=(saved.get('proposalSentAt') or datetime.now(timezone.utc).isoformat()) if sent else None
                    saved['proposalSent']=sent
                    if sent: ensure_project(db,ident,saved)
                    db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(saved,ensure_ascii=False),ident))
                return self.reply(200,{'ok':True,'proposalSent':sent,'proposalSentAt':saved['proposalSentAt']})
            if path == '/api/projects/contract':
                ident=item.get('id'); won=item.get('won')
                if type(ident) is not int or type(won) is not bool: raise ServiceError('Trạng thái hợp đồng không hợp lệ.')
                with connect() as db:
                    db.execute('BEGIN IMMEDIATE')
                    row=db.execute("SELECT body FROM records WHERE id=? AND kind='project'",(ident,)).fetchone()
                    if not row: raise ServiceError('Không tìm thấy dự án.',404)
                    project=json.loads(row['body']);project['won']=won
                    project['wonAt']=(project.get('wonAt') or datetime.now(timezone.utc).isoformat()) if won else None
                    db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(project,ensure_ascii=False),ident))
                    for letter in db.execute("SELECT id,body FROM records WHERE kind='sentproposal'").fetchall():
                        body=json.loads(letter['body'])
                        if body.get('jobId')==project.get('jobId'):
                            body['outcome']='won' if won else 'pending'
                            db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(body,ensure_ascii=False),letter['id']))
                return self.reply(200,{'ok':True})
            if path == '/api/jobs/activity':
                try: ident = int(item.get('id'))
                except (ValueError,TypeError): raise ServiceError('ID job không hợp lệ.') from None
                viewed=job_activity.timestamp(item.get('lastViewedAt'))
                if not viewed: raise ServiceError('Hãy nhập thời điểm khách xem job trên Upwork.')
                with connect() as db:
                    db.execute('BEGIN IMMEDIATE')
                    row=db.execute("SELECT body FROM records WHERE id=? AND kind='job'",(ident,)).fetchone()
                    if not row: raise ServiceError('Không tìm thấy job.',404)
                    saved=job_activity.merge(json.loads(row['body']),{'lastViewedAt':viewed},source='manual')
                    db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(saved,ensure_ascii=False),ident))
                return self.reply(200,{'ok':True})
            if path in ('/api/jobs/interest', '/api/jobs/retry'):
                try: ident = int(item.get('id'))
                except (ValueError,TypeError): raise ServiceError('ID job không hợp lệ.') from None
                job = next((r for r in records() if r['kind']=='job' and r['id']==ident),None)
                if not job: raise ServiceError('Không tìm thấy job.',404)
                with connect() as db:
                    if path.endswith('/retry'):
                        db.execute('DELETE FROM job_reviews WHERE record_id=?',(ident,))
                    elif item.get('interested') is True:
                        db.execute('INSERT OR IGNORE INTO job_interest VALUES (?,?)',(ident,time.time()+7*86400))
                    else:
                        db.execute('DELETE FROM job_interest WHERE record_id=?',(ident,))
                return self.reply(200, {'ok':True})
            if path in ('/api/ai/proposal', '/api/ai/review'):
                job_id = str(item.get('jobId') or '')
                job = next((r for r in records() if r['kind'] == 'job' and str(r['id']) == job_id), None)
                item.pop('_library_samples', None)
                if path.endswith('/proposal') and item.get('referenceLibrary') is not None:
                    item['_library_samples'] = library_pool(records(), item['referenceLibrary'])
                action = evaluate_proposal if path.endswith('/review') else generate_proposal
                return self.reply(200, action(item, settings(), job))
            if path != '/api/records':
                return self.reply(404, {'error': 'Không tìm thấy.'})
            kind = item.pop('kind', None)
            ident = item.pop('id', None)
            item['name'] = text(item.get('name'), 1000)
            if kind not in ('client', 'job', 'proposal', 'template', 'sentproposal', 'messageTemplate') or not item['name']:
                raise ServiceError('Vui lòng điền tên.')
            if kind == 'messageTemplate':
                item['body'] = text(item.get('body'))
                item['category'] = text(item.get('category'), 100)
                if not item['body'].strip() or not item['category'].strip():
                    raise ServiceError('Điền nhóm và nội dung tin nhắn.')
            if kind == 'job':
                for derived in ('jobAssessment','interested','interestExpiresAt','clientActivity','clientActivityHistory','proposalSent','proposalSentAt'): item.pop(derived,None)
            if kind == 'sentproposal' and item.get('outcome', 'pending') not in ('pending', 'won', 'lost', 'no_reply'):
                raise ServiceError('Kết quả hợp đồng không hợp lệ.')
            if kind == 'sentproposal' and 'interaction' in item:
                if item['interaction'] not in ('unknown','not_viewed','viewed','replied'):
                    raise ServiceError('Thông tin lượt xem không hợp lệ.')
                item['interactionAt'] = datetime.now(timezone.utc).isoformat()
            if kind == 'proposal' and 'workspace' in item:
                validate_workspace(item['workspace'])
            if ident is not None and (not isinstance(ident, int) or isinstance(ident, bool)):
                raise ServiceError('ID không hợp lệ.')
            with connect() as db:
                if ident is None:
                    if kind == 'client': item = record_client_events(item)
                    ident = db.execute('INSERT INTO records(kind,body) VALUES (?,?)', (kind, json.dumps(item, ensure_ascii=False))).lastrowid
                else:
                    existing = db.execute('SELECT body FROM records WHERE id=? AND kind=?', (ident, kind)).fetchone()
                    if not existing:
                        return self.reply(404, {'error': 'Bản ghi không tồn tại.'})
                    saved = json.loads(existing['body'])
                    if kind == 'sentproposal':
                        # The sent letter is a snapshot; outcome updates never rewrite it.
                        item = {key: item[key] for key in ('outcome', 'outcomeNotes', 'contractValue', 'interaction', 'interactionAt') if key in item}
                    if kind == 'sentproposal' and 'outcome' in item:
                        for project_row in db.execute("SELECT id,body FROM records WHERE kind='project'").fetchall():
                            project=json.loads(project_row['body'])
                            if project.get('jobId')==saved.get('jobId'):
                                project['won']=item['outcome']=='won'
                                project['wonAt']=(project.get('wonAt') or datetime.now(timezone.utc).isoformat()) if project['won'] else None
                                db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(project,ensure_ascii=False),project_row['id']))
                    if kind == 'client': item = record_client_events(item, saved)
                    saved.update(item)
                    item = saved
                    db.execute('UPDATE records SET body=? WHERE id=?', (json.dumps(item, ensure_ascii=False), ident))
            return self.reply(200, dict(item, id=ident, kind=kind))
        except ServiceError as error:
            self.reply(error.status, {'error': str(error)})
        except sqlite3.Error:
            self.reply(503, {'error': 'Chưa thể ghi dữ liệu. Vui lòng thử lại.'})

    def do_DELETE(self):
        if not self.guard():
            return
        try:
            path = urlsplit(self.path).path
            if not path.startswith('/api/records/'):
                return self.reply(404, {'error': 'Không tìm thấy.'})
            ident = int(path.removeprefix('/api/records/'))
            with connect() as db:
                db.execute('DELETE FROM records WHERE id=?', (ident,))
                db.execute('DELETE FROM job_interest WHERE record_id=?', (ident,))
                db.execute('DELETE FROM job_reviews WHERE record_id=?', (ident,))
            self.reply(200, {'ok': True})
        except ValueError:
            self.reply(400, {'error': 'ID không hợp lệ.'})
        except sqlite3.Error:
            self.reply(503, {'error': 'Chưa thể ghi dữ liệu. Vui lòng thử lại.'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8000'))
    http = ThreadingHTTPServer((BIND, port), Handler)
    print(f'Freelance Desk listening on port {port}', flush=True)
    threading.Thread(target=notification_worker, daemon=True).start()
    threading.Thread(target=job_worker, daemon=True).start()
    http.serve_forever()

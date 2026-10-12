"""Read-only Gmail import; only Upwork message notices are retained, never sent."""
import base64
import hashlib
import json
import os
import re
import secrets
import threading
import time
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr, parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo
from services import ServiceError
from data_store import data_directory

SCOPE = 'https://www.googleapis.com/auth/gmail.readonly'
QUERY = 'from:(@email.upwork.com) subject:("sent you a message") newer_than:30d'
LOCK = threading.RLock()
SYNC_LOCK = threading.Lock()
PENDING = {}


def init(connect):
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS upwork_mail (id TEXT PRIMARY KEY, body TEXT NOT NULL, client_id INTEGER, seen INTEGER NOT NULL DEFAULT 0)')
        db.execute('CREATE TABLE IF NOT EXISTS upwork_mail_rooms (room TEXT PRIMARY KEY, client_id INTEGER NOT NULL)')


def private_path():
    return data_directory() / 'gmail-private.json'


def private():
    with LOCK:
        try:
            return json.loads(private_path().read_text())
        except FileNotFoundError:
            return {}
        except (ValueError, OSError):
            raise ServiceError('Không đọc được cấu hình Gmail riêng tư.', 503) from None


def save(values):
    with LOCK:
        path = private_path();path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix('.tmp')
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(values, f, ensure_ascii=False)
        temp.replace(path);path.chmod(0o600)


def status():
    p = private()
    return {'configured': bool(p.get('clientId') and p.get('clientSecret')), 'connected': bool(p.get('refreshToken')), 'lastSync': p.get('lastSync'), 'error': p.get('error', '')}


def configure(item):
    client_id, secret = item.get('clientId', ''), item.get('clientSecret', '')
    if not isinstance(client_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]+\.apps\.googleusercontent\.com', client_id):
        raise ServiceError('Nhập OAuth Client ID của Google, không phải khóa API Gemini.')
    if not isinstance(secret, str) or not secret.strip() or len(secret)>4096 or any(c.isspace() for c in secret):
        raise ServiceError('Nhập OAuth Client Secret hợp lệ.')
    with LOCK:
        current=private()
        if current.get('clientId')!=client_id or current.get('clientSecret')!=secret:
            save({'clientId':client_id,'clientSecret':secret})
            PENDING.clear()
    return status()


def google(url, data=None, token=None):
    headers = {'Authorization':'Bearer '+token} if token else {}
    raw = urlencode(data).encode() if data is not None else None
    if raw is not None:headers['Content-Type']='application/x-www-form-urlencoded'
    try:
        with urlopen(Request(url, data=raw, headers=headers), timeout=25) as r:
            return json.loads(r.read(8*1024*1024))
    except HTTPError as e:
        if e.code in (400,401):message='Phiên Gmail hết hiệu lực hoặc cấu hình OAuth chưa đúng. Kết nối Google lại.'
        elif e.code==403:message='Google chưa cấp quyền Gmail. Bật Gmail API và thêm tài khoản vào Test users trong Google Cloud.'
        elif e.code==429:message='Gmail giới hạn lượt đọc. Thử đồng bộ sau.'
        else:message='Google đang gặp lỗi. Thử lại sau.'
        raise ServiceError(message, 502) from None
    except (URLError, ValueError, OSError):
        raise ServiceError('Không kết nối được Google. Kiểm tra mạng rồi thử lại.',502) from None


def begin(redirect):
    p=private()
    if not p.get('clientId'):raise ServiceError('Lưu OAuth Client ID và Client Secret trước.')
    state=secrets.token_urlsafe(32);verifier=secrets.token_urlsafe(48)
    cookie=secrets.token_urlsafe(32)
    with LOCK:
        for k in list(PENDING):
            if PENDING[k]['expires']<time.time():del PENDING[k]
        PENDING[state]={'expires':time.time()+600,'cookie':cookie,'verifier':verifier,'redirect':redirect,'clientId':p['clientId']}
    challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    return {'url':'https://accounts.google.com/o/oauth2/v2/auth?'+urlencode({'client_id':p['clientId'],'redirect_uri':redirect,'response_type':'code','scope':SCOPE,'access_type':'offline','prompt':'consent','state':state,'code_challenge':challenge,'code_challenge_method':'S256'}),'cookie':cookie}


def callback(query,cookie):
    state=query.get('state',[''])[0]
    with LOCK:
        flow=PENDING.get(state)
        if not flow or flow['expires']<time.time() or not secrets.compare_digest(flow['cookie'],cookie):
            raise ServiceError('Phiên kết nối Gmail không hợp lệ hoặc hết hạn. Bấm Kết nối Google lại.')
        del PENDING[state]
        p=private()
        if p.get('clientId')!=flow['clientId']:raise ServiceError('Cấu hình Google đã đổi. Kết nối lại.')
        if query.get('error'):raise ServiceError('Bạn chưa cấp quyền đọc Gmail. Có thể kết nối lại sau.')
        code=query.get('code',[''])[0]
        if not code:raise ServiceError('Google chưa trả mã kết nối.')
        token=google('https://oauth2.googleapis.com/token', {'code':code,'client_id':p['clientId'],'client_secret':p['clientSecret'],'redirect_uri':flow['redirect'],'grant_type':'authorization_code','code_verifier':flow['verifier']})
        if not token.get('refresh_token') or SCOPE not in token.get('scope','').split():raise ServiceError('Google chưa cấp quyền đọc Gmail đầy đủ. Kết nối lại.')
        p.update(refreshToken=token['refresh_token'],error='');save(p)


class BodyText(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.skip=0;self.urls=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.skip+=1
        if tag in ('p','div','br','tr','h1','h2','td'):self.parts.append('\n')
        if tag=='a':
            href=dict(attrs).get('href','')
            try:
                u=urlsplit(href)
                if u.scheme=='https' and (u.hostname=='upwork.com' or (u.hostname or '').endswith('.upwork.com')):self.urls.append(href)
            except ValueError:
                pass
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip=max(0,self.skip-1)
        if tag in ('p','div','tr','td'):self.parts.append('\n')
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)


def parse(raw, ident=None, received=None):
    if len(raw)>1024*1024:raise ServiceError('Thư quá lớn, tối đa 1 MB.')
    msg=BytesParser(policy=policy.default).parsebytes(raw)
    sender=parseaddr(str(msg.get('From','')))[1].lower()
    room=re.fullmatch(r'(room_[a-z0-9]+)@email\.upwork\.com',sender)
    subject=str(msg.get('Subject',''))
    match=re.fullmatch(r'(.+?) sent you a message(?: on Upwork)?[.!]?',subject.strip(),re.I)
    if not room or not match:return None
    part=msg.get_body(preferencelist=('html','plain')) if msg.is_multipart() else msg
    if not part or part.get_content_type() not in ('text/html','text/plain'):return None
    try:content=part.get_content()
    except (LookupError, ValueError):return None
    parser=BodyText();parser.feed(content) if part.get_content_type()=='text/html' else parser.parts.append(content)
    body='\n'.join(line.strip() for line in ''.join(parser.parts).splitlines() if line.strip())
    notice=re.search(r'Unread message from\s+(.+?)\s+about\s+(.+?)(?:\n|$)',body,re.I)
    project=notice.group(2).rstrip('.') if notice else ''
    # Keep only the message section; never treat navigation/footer as message content.
    start=re.search(r'\b\d{1,2}:\d{2}\s*(?:AM|PM)\s+[A-Z]{2,5},?\s+\d{1,2}\s+[A-Za-z]+\s+\d{4}\s*\n',body)
    content=body[start.end():] if start else ''
    content=re.split(r'\n(?:View on Upwork|View your message|Or, you can respond)',content,1,flags=re.I)[0].strip()
    try:stamp=datetime.fromtimestamp(int(received)/1000,timezone.utc) if received else parsedate_to_datetime(str(msg.get('Date','')))
    except (ValueError,TypeError,OverflowError):stamp=datetime.now(timezone.utc)
    if stamp.tzinfo is None:stamp=stamp.replace(tzinfo=timezone.utc)
    google_auth=next((str(h).strip() for h in msg.get_all('Authentication-Results', []) if re.search(r'^mx\.google\.com;', str(h).strip(), re.I)), '')
    authenticated=bool(re.search(r'dkim=pass\b[^;]*header\.i=@?(?:email\.)?upwork\.com(?=[;\s]|$)', google_auth, re.I))
    return {'authenticated':bool(authenticated),'messageId':str(msg.get('Message-ID','')), 'id':ident or hashlib.sha256(raw).hexdigest(),'room':room.group(1),'sender':match.group(1),'project':project,'text':content[:20000], 'previewOnly':not bool(content),'receivedAt':stamp.isoformat(),'url':next((u for u in parser.urls if '/messages/' in u),''), 'source':'gmail' if ident else 'eml'}


def apply_reply(db, client_id, item):
    row=db.execute("SELECT body FROM records WHERE kind='client' AND id=?",(client_id,)).fetchone()
    if not row:raise ServiceError('Khách không còn tồn tại. Chọn khách khác.')
    client=json.loads(row['body'])
    day=datetime.fromisoformat(item['receivedAt']).astimezone(ZoneInfo('Asia/Bangkok')).date().isoformat()
    if day >= (client.get('lastReplyDate') or ''):
        client.update(lastReplyDate=day,lastReplySource='gmail' if item['source']=='gmail' else 'upwork-email')
    client['upworkMailUnread']=bool(db.execute('SELECT 1 FROM upwork_mail WHERE client_id=? AND seen=0',(client_id,)).fetchone())
    db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(client,ensure_ascii=False),client_id))


def store(connect, item):
    if not item:return False
    with connect() as db:
        if db.execute('SELECT 1 FROM upwork_mail WHERE id=?',(item['id'],)).fetchone():return False
        if item.get('messageId') and db.execute("SELECT 1 FROM upwork_mail WHERE json_extract(body,'$.messageId')=?",(item['messageId'],)).fetchone():return False
        room=db.execute('SELECT client_id FROM upwork_mail_rooms WHERE room=?',(item['room'],)).fetchone()
        client_id=room['client_id'] if (item['source']=='eml' or item.get('authenticated')) and room and db.execute("SELECT 1 FROM records WHERE id=? AND kind='client'",(room['client_id'],)).fetchone() else None
        db.execute('INSERT INTO upwork_mail(id,body,client_id) VALUES (?,?,?)',(item['id'],json.dumps(item,ensure_ascii=False),client_id))
        if client_id:apply_reply(db,client_id,item)
    return True


def inbox(connect):
    with connect() as db:
        return [dict(json.loads(r['body']),clientId=r['client_id'],seen=bool(r['seen'])) for r in db.execute('SELECT * FROM upwork_mail ORDER BY julianday(json_extract(body,\'$.receivedAt\')) DESC LIMIT 200')]


def link(connect, item):
    ident=item.get('id');client_id=item.get('clientId')
    if not isinstance(ident,str) or not isinstance(client_id,int) or isinstance(client_id,bool):raise ServiceError('Chọn thư và khách hợp lệ.')
    with connect() as db:
        row=db.execute('SELECT body FROM upwork_mail WHERE id=?',(ident,)).fetchone()
        if not row:raise ServiceError('Không tìm thấy thư.')
        mail=json.loads(row['body']);apply_reply(db,client_id,mail)
        db.execute('INSERT OR REPLACE INTO upwork_mail_rooms(room,client_id) VALUES (?,?)',(mail['room'],client_id))
        for r in db.execute('SELECT id,body FROM upwork_mail WHERE client_id IS NULL').fetchall():
            m=json.loads(r['body'])
            if m['room']==mail['room'] and (m['id']==ident or m['source']=='eml' or m.get('authenticated')):
                db.execute('UPDATE upwork_mail SET client_id=? WHERE id=?',(client_id,r['id']));apply_reply(db,client_id,m)
        db.execute('UPDATE upwork_mail SET client_id=? WHERE id=?',(client_id,ident))
        apply_reply(db,client_id,mail)
        if row['body']:
            for old in db.execute("SELECT id,body FROM records WHERE kind='client' AND id!=?",(client_id,)).fetchall():
                c=json.loads(old['body'])
                if c.get('upworkMailUnread') and not db.execute('SELECT 1 FROM upwork_mail WHERE client_id=? AND seen=0',(old['id'],)).fetchone():
                    c['upworkMailUnread']=False;db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(c,ensure_ascii=False),old['id']))
    return {'ok':True}


def seen(connect,ident):
    with connect() as db:
        row=db.execute('SELECT client_id FROM upwork_mail WHERE id=?',(ident,)).fetchone()
        if not row:raise ServiceError('Không tìm thấy thư.')
        db.execute('UPDATE upwork_mail SET seen=1 WHERE id=?',(ident,))
        if row['client_id'] and not db.execute('SELECT 1 FROM upwork_mail WHERE client_id=? AND seen=0',(row['client_id'],)).fetchone():
            r=db.execute("SELECT body FROM records WHERE id=? AND kind='client'",(row['client_id'],)).fetchone()
            if r:
                c=json.loads(r['body']);c['upworkMailUnread']=False;db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(c,ensure_ascii=False),row['client_id']))
    return {'ok':True}


def sync(connect):
    if not SYNC_LOCK.acquire(blocking=False):raise ServiceError('Gmail đang đồng bộ. Đợi lượt hiện tại xong.',409)
    try:
        p=private()
        if not p.get('refreshToken'):raise ServiceError('Kết nối Google trước khi đồng bộ.')
        try:
            token=google('https://oauth2.googleapis.com/token',{'grant_type':'refresh_token','refresh_token':p['refreshToken'],'client_id':p['clientId'],'client_secret':p['clientSecret']})['access_token']
            page=p.get('pageToken','');added=0;checked=0;pages=0
            with connect() as db:known={r['id'] for r in db.execute('SELECT id FROM upwork_mail')}
            # Walk past known messages so an older unimported notice is not starved.
            while pages<2:
                result=google('https://gmail.googleapis.com/gmail/v1/users/me/messages?'+urlencode({'q':QUERY,'maxResults':50,**({'pageToken':page} if page else {})}),token=token)
                pages+=1
                for m in result.get('messages',[]):
                    checked+=1
                    if m['id'] in known:continue
                    raw=google('https://gmail.googleapis.com/gmail/v1/users/me/messages/'+m['id']+'?format=raw',token=token)
                    encoded=raw.get('raw','');mail=parse(base64.urlsafe_b64decode(encoded+'='*(-len(encoded)%4)),m['id'],raw.get('internalDate'))
                    with LOCK:
                        if private().get('refreshToken')!=p['refreshToken']:raise ServiceError('Kết nối Gmail đã thay đổi. Dừng lượt đồng bộ.',409)
                        added+=int(store(connect,mail))
                page=result.get('nextPageToken','')
                if not page:break
            with LOCK:
                if private().get('refreshToken')!=p['refreshToken']:raise ServiceError('Kết nối Gmail đã thay đổi. Dừng lượt đồng bộ.',409)
                p.update(lastSync=datetime.now(timezone.utc).isoformat(),error='',pageToken=page);save(p)
            return {'ok':True,'added':added,'limited':bool(page)}
        except ServiceError as e:
            with LOCK:
                if private().get('refreshToken')==p['refreshToken']:
                    p['error']=str(e);p.pop('pageToken',None);save(p)
            raise
        except (KeyError,ValueError):raise ServiceError('Google trả dữ liệu thư không hợp lệ.',502) from None
    finally:
        SYNC_LOCK.release()


def disconnect():
    with LOCK:
        p=private();save({k:v for k,v in p.items() if k in ('clientId','clientSecret')});PENDING.clear()
    return status()


def worker(connect):
    while True:
        time.sleep(120)
        try:
            if status()['connected']:sync(connect)
        except Exception:
            pass  # Errors are exposed through /api/mail status; never log private payloads.

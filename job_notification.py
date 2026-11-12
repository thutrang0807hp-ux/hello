"""Escaped Telegram job notifications with local customer scoring. No AI or translation calls."""
import math
from html import escape
from urllib.parse import urlsplit


def number(value):
    if value is None or isinstance(value,bool) or not isinstance(value,(int,float,str)) or value=='':
        return None
    try:
        result=float(value.strip() or '0') if isinstance(value,str) else float(value)
        return result if math.isfinite(result) and result>=0 else None
    except ValueError:
        return None


def customer_stars(job):
    c=job.get('clientInfo') or {}
    rating,hires,posted=(number(c.get(k)) for k in ('rating','totalHires','totalJobsPosted'))
    rate=number(c.get('hireRate'))
    if rate is not None and rate>100:rate=None
    if rate is None and hires is not None and posted is not None and posted>0 and hires<=posted:rate=100*hires/posted
    components=[]
    if rating is not None and 0<rating<=5:components.append((rating,.45))
    if hires is not None:components.append((5 if hires>=50 else 4 if hires>=20 else 3 if hires>=5 else 2 if hires>=1 else 1,.25))
    if rate is not None:components.append((5 if rate>=80 else 4 if rate>=60 else 3 if rate>=40 else 2 if rate>=20 else 1,.2))
    if isinstance(c.get('paymentVerified'),bool):components.append((5 if c['paymentVerified'] else 1,.1))
    if len(components)<2 or (hires is None and rate is None):return None
    return max(1,min(5,math.floor(sum(v*w for v,w in components)/sum(w for _,w in components)+.5)))


def clip(value,limit):
    # Telegram counts UTF-16 units; preserve complete code points and a visible truncation mark.
    value=value if isinstance(value,str) else str(value) if isinstance(value,(int,float)) else ''
    raw=value.encode('utf-16-le')
    return value if len(raw)<=limit*2 else raw[:max(0,limit-1)*2].decode('utf-16-le',errors='ignore')+'…'


def units(value):
    return len(value.encode('utf-16-le'))//2


def render(job):
    """One self-contained Telegram message with a native expandable description."""
    stars=customer_stars(job)
    score='★'*stars+'☆'*(5-stars) if stars is not None else 'Chưa đủ dữ liệu chấm sao'
    title=clip(job.get('name') or 'Job Upwork',240)
    client=job.get('clientInfo') or {}
    value=lambda raw:clip(raw,100).strip() or 'Chưa có dữ liệu'
    heading=score+' · '+title
    facts='Điểm khách theo quy tắc, không dùng AI.\nNgân sách: '+value(job.get('budget'))+' · Khách: '+value(client.get('country'))
    rating=number(client.get('rating'))
    if rating is not None and 0<rating<=5:facts+=f'\nSao Upwork: {rating:g}/5'
    notes=job.get('notes') or 'Nguồn chưa gửi mô tả. Hãy mở job trên Upwork để xem tại nguồn.'
    url=job.get('url');valid=valid_url(url)
    footer='Mở job trên Upwork ↗' if valid else 'Chưa có đường dẫn Upwork hợp lệ.'
    warning='Mô tả vượt giới hạn một tin Telegram; mở Upwork để đọc phần còn lại.'
    # Count visible UTF-16 text, not HTML tags/entities or the hidden href value.
    room=max(0,4096-units(heading+'\n'+facts+'\n\n'+footer)-4)
    shortened=units(notes)>room
    if shortened:room=max(0,room-units(warning+'\n'))
    description=clip(notes,room)
    body='<b>'+escape(heading)+'</b>\n'+escape(facts)+'\n<blockquote expandable>'+escape(description)+'</blockquote>'
    if shortened:body+='\n'+escape(warning)
    body+='\n'+('<a href="'+escape(url,quote=True)+'">'+footer+'</a>' if valid else footer)
    return body


def valid_url(url):
    try:
        parsed=urlsplit(url) if isinstance(url,str) else None
        return bool(parsed and parsed.scheme=='https' and parsed.hostname in ('upwork.com','www.upwork.com') and not parsed.username and not parsed.password)
    except ValueError:
        return False

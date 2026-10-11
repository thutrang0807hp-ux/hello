"""Observed client activity; never equate time of import with time of viewing."""
from datetime import datetime, timezone
from services import ServiceError, text

def timestamp(value):
    raw = text(value,200)
    if not raw: return ''
    try:
        date=datetime.fromisoformat(raw.replace('Z','+00:00'))
        if not date.tzinfo or date>datetime.now(timezone.utc): raise ValueError()
        return date.astimezone(timezone.utc).isoformat()
    except ValueError:
        raise ServiceError('Thời điểm hoạt động cần có múi giờ và không được ở tương lai.') from None

def normalize(raw):
    activity=raw.get('clientActivity') or {}
    if not isinstance(activity,dict): raise ServiceError('Thông tin hoạt động khách không hợp lệ.')
    viewed=timestamp(activity.get('lastViewedAt') or raw.get('clientLastViewedAt'))
    active=timestamp(activity.get('lastBuyerActivity') or activity.get('lastActivityAt'))
    result={}
    if viewed: result['lastViewedAt']=viewed
    if active: result['lastActivityAt']=active
    return result

def merge(job, incoming, source='toolkit', now=None):
    now=now or datetime.now(timezone.utc).isoformat()
    history=list(job.get('clientActivityHistory') or [])
    current=dict(job.get('clientActivity') or {})
    accepted=False
    for key in ('lastViewedAt','lastActivityAt'):
        value=incoming.get(key)
        if not value: continue
        # ISO values normalized to UTC. Older arrivals do not move activity backwards.
        if current.get(key) and datetime.fromisoformat(value)<datetime.fromisoformat(current[key]): continue
        accepted=True
        current[key]=value
        if not any(h.get('field')==key and h.get('at')==value for h in history):
            history.append({'field':key,'at':value,'observedAt':now,'source':source})
    if current and accepted:
        current['observedAt']=now
        job['clientActivity']=current
        job['clientActivityHistory']=history[-30:]
    return job

def status(job, now=None):
    now=now or datetime.now(timezone.utc)
    activity=job.get('clientActivity') or {}
    events=[]
    for key in ('lastViewedAt','lastActivityAt'):
        try:
            date=datetime.fromisoformat(str(activity.get(key,'')).replace('Z','+00:00'))
            if date.tzinfo and date<=now: events.append(date)
        except ValueError: pass
    if not events: return {'state':'unknown','penalty':0,'reason':'Chưa có dữ liệu khách xem / hoạt động trên job.'}
    latest=max(events); hours=(now-latest).total_seconds()/3600
    try:
        observed=datetime.fromisoformat(str(activity.get('observedAt','')).replace('Z','+00:00'))
        fresh=observed.tzinfo is not None and 0 <= (now-observed).total_seconds() <= 1800
    except ValueError: fresh=False
    if not fresh: return {'state':'outdated','penalty':0,'reason':'Dữ liệu hoạt động chưa được cập nhật gần đây; chưa biết khách đã quay lại hay chưa.'}
    if hours>=5: return {'state':'quiet','penalty':10,'reason':'Dữ liệu mới ghi nhận cho thấy khách chưa xem / hoạt động lại ít nhất 5 giờ. Giảm ưu tiên, không kết luận khách bỏ job.'}
    return {'state':'recent' if hours<=1 else 'waiting','penalty':0,'reason':'Có hoạt động của khách trong 1 giờ gần đây.' if hours<=1 else 'Có hoạt động được ghi nhận; nên theo dõi lần khách quay lại.'}

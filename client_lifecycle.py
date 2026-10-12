"""Archive unanswered new leads using an explicitly recorded inquiry date."""
from datetime import date, datetime, timezone, timedelta

# Vietnam/Thailand use UTC+7 without DST; no external tzdata needed on Windows.
LOCAL_ZONE = timezone(timedelta(hours=7))


def archive_unanswered(client, today=None):
    if client.get('clientGroup') != 'talk' or client.get('clientStage') not in ('new', 'testing'):
        return None
    today = today or datetime.now(LOCAL_ZONE).date()
    testing = client.get('clientStage') == 'testing'
    try:
        asked = date.fromisoformat(client.get('clientTestSentDate' if testing else 'clientInquiryDate', ''))
    except (ValueError, TypeError):
        return None
    if (today - asked).days < 14:
        return None
    reply = client.get('lastReplyDate')
    if reply:
        try:
            if date.fromisoformat(reply) >= asked:
                return None
        except (ValueError, TypeError):
            return None  # Unknown reply date is insufficient evidence of silence.
    return dict(client, clientGroup='archive', clientStage='closed-no-contract',
                status='Đã hoàn thành', clientHadContract='no',
                clientArchivedDate=today.isoformat(), clientLostReason='silent',
                clientPreviousGroup='talk', clientPreviousStage=client.get('clientStage'),
                clientArchiveReason=('Đã gửi test nhưng khách chưa phản hồi sau 14 ngày.' if testing
                                     else 'Khách mới chưa phản hồi sau 14 ngày từ tin hỏi.'))


def record_client_events(update, previous=None, now=None):
    """Record new CRM transitions without inventing historical events."""
    previous = previous or {}
    result = dict(previous, **update)
    now = now or datetime.now(LOCAL_ZONE).isoformat()
    if not previous:
        result.setdefault('clientCreatedAt', now)
    old_group = previous.get('clientGroup')
    group = result.get('clientGroup')
    stage = result.get('clientStage')
    if group=='active' and stage=='paused' and previous.get('clientStage')!='paused':
        result['clientPausedAt']=now
    if group=='active' and stage in ('working','waiting') and previous.get('clientStage')=='paused':
        result['clientResumedAt']=now
    starts_talk = (group == 'talk' and stage == 'discussing' and
                   (old_group != 'talk' or previous.get('clientStage') != 'discussing'))
    new_contract = group == 'active' and old_group not in ('active', 'archive')
    if not result.get('clientTalkAt'):
        reply = update.get('lastReplyDate')
        if reply and group == 'talk':
            try:
                reply_date = date.fromisoformat(reply)
                result['clientTalkAt'] = reply_date.isoformat()+'T00:00:00+07:00'
            except (ValueError, TypeError):
                pass
        elif starts_talk or new_contract:
            result['clientTalkAt'] = now
    if new_contract and not result.get('clientContractAt'):
        result['clientContractAt'] = now
    if group == 'archive' and old_group in ('talk', 'active'):
        result['clientPreviousGroup'] = old_group
        result['clientPreviousStage'] = previous.get('clientStage', '')
        result.setdefault('clientArchivedDate', now[:10])
    return result

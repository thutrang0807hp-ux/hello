"""On-demand Telegram description pages, bound to the bot/chat/message that received the job."""
import hashlib
import json
import os
import re
import time
import urllib.error
from html import escape
from services import post_json
from job_notification import clip, customer_stars

last_error=''


def init(connect):
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS telegram_delivery (key TEXT PRIMARY KEY, outbox_id INTEGER NOT NULL, chat_id TEXT NOT NULL, message_id INTEGER NOT NULL, bot TEXT NOT NULL, target TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS telegram_poll (bot TEXT PRIMARY KEY, offset INTEGER NOT NULL)')


def identity():
    return hashlib.sha256(os.environ.get('FREELANCE_TELEGRAM_TOKEN','').encode()).hexdigest()


def api(method,payload):
    return post_json('https://api.telegram.org/bot'+os.environ['FREELANCE_TELEGRAM_TOKEN']+'/'+method,payload)


def keyboard(job,page=-1,total=1):
    key=job.get('_telegramDetails')
    if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_-]{16}',key):return {}
    rows=[]
    if page<0:rows.append([{'text':'Xem mô tả đầy đủ ▾','callback_data':f'fd:{key}:0'}])
    else:
        navigation=[]
        if page>0:navigation.append({'text':'← Trang trước','callback_data':f'fd:{key}:{page-1}'})
        if page+1<total:navigation.append({'text':'Trang sau →','callback_data':f'fd:{key}:{page+1}'})
        if navigation:rows.append(navigation)
        rows.append([{'text':'Thu gọn ▴','callback_data':f'fd:{key}:-1'}])
    from job_notification import valid_url
    if valid_url(job.get('url')):rows.append([{'text':'Mở job trên Upwork ↗','url':job['url']}])
    return {'inline_keyboard':rows}


def chunks(text,limit=2600):
    """Split by Telegram's UTF-16 length without losing or repeating any text."""
    result=[];part=[];size=0
    for char in text:
        units=2 if ord(char)>65535 else 1
        if size+units>limit:
            result.append(''.join(part));part=[];size=0
        part.append(char);size+=units
    if part or not result:result.append(''.join(part))
    return result


def expanded(job,page):
    notes=job.get('notes') or 'Nguồn chưa gửi mô tả. Mở link Upwork để xem thông tin tại nguồn.'
    pages=chunks(notes)
    if not 0<=page<len(pages):raise ValueError('Invalid description page')
    stars=customer_stars(job);score='★'*stars+'☆'*(5-stars) if stars is not None else 'Chưa đủ dữ liệu chấm sao'
    client=job.get('clientInfo') or {}
    value=lambda v:clip(v,100).strip() or 'Chưa có dữ liệu'
    payment='Đã xác minh' if client.get('paymentVerified') is True else 'Chưa xác minh' if client.get('paymentVerified') is False else 'Chưa có dữ liệu'
    header=f'<b>{escape(score)} · {escape(clip(job.get("name","Job Upwork"),180))}</b>\nĐiểm khách theo quy tắc, không dùng AI.\n'
    if page==0:
        header+='Ngân sách: '+escape(value(job.get('budget')))+' · '+escape(value(job.get('jobType')))+'\n'
        rating=value(client.get('rating'));rating=rating+'/5' if rating!='Chưa có dữ liệu' else rating
        header+='Khách: '+escape(value(client.get('country')))+' · Sao Upwork: '+escape(rating)+'\n'
        header+='Thanh toán: '+payment+' · Đã thuê: '+escape(value(client.get('totalHires')))+'\n'
    return header+f'\n<b>Mô tả gốc · trang {page+1}/{len(pages)}</b>\n'+escape(pages[page]),keyboard(job,page,len(pages))


def register(connect,job,outbox_id,result):
    message=result.get('result') if isinstance(result,dict) else None
    if not isinstance(message,dict) or type(message.get('message_id')) is not int:return
    chat=message.get('chat') or {}
    if not isinstance(chat.get('id'),(int,str)):return
    with connect() as db:
        db.execute('INSERT OR REPLACE INTO telegram_delivery VALUES(?,?,?,?,?,?)',(job['_telegramDetails'],outbox_id,str(chat['id']),message['message_id'],identity(),os.environ.get('FREELANCE_TELEGRAM_CHAT_ID','')))


def process_callback(connect,callback):
    if not isinstance(callback,dict):return
    match=re.fullmatch(r'fd:([A-Za-z0-9_-]{16}):(-1|\d{1,4})',str(callback.get('data','')))
    message=callback.get('message') or {};chat=message.get('chat') or {}
    notice='Thông báo này không còn được liên kết. Hãy mở link Upwork.'
    if match:
        with connect() as db:
            row=db.execute('SELECT d.*,o.body FROM telegram_delivery d JOIN outbox o ON o.id=d.outbox_id WHERE d.key=?',(match[1],)).fetchone()
        if row and row['bot']==identity() and row['target']==os.environ.get('FREELANCE_TELEGRAM_CHAT_ID','') and row['chat_id']==str(chat.get('id')) and row['message_id']==message.get('message_id') and json.loads(row['body']).get('_telegramDetails')==match[1]:
            job=json.loads(row['body']);page=int(match[2])
            try:
                if page<0:
                    from job_notification import render
                    text,buttons=render(job),keyboard(job)
                else:text,buttons=expanded(job,page)
            except ValueError:notice='Trang mô tả không hợp lệ.'
            else:
                try:
                    result=api('editMessageText',{'chat_id':row['chat_id'],'message_id':row['message_id'],'text':text,'parse_mode':'HTML','reply_markup':buttons,'link_preview_options':{'is_disabled':True}})
                    if not isinstance(result,dict) or result.get('ok') is not True:raise ValueError('Edit rejected')
                except urllib.error.HTTPError as error:
                    try:unchanged=error.code==400 and 'message is not modified' in json.loads(error.read(4096)).get('description','').lower()
                    except (ValueError,OSError,AttributeError):unchanged=False
                    if not unchanged and error.code!=400:raise
                    if not unchanged:notice='Tin nhắn không còn sửa được. Hãy dùng link Upwork.'
                if notice=='Thông báo này không còn được liên kết. Hãy mở link Upwork.':notice='Đã mở mô tả.' if page>=0 else 'Đã thu gọn.'
    if isinstance(callback.get('id'),str):
        try:api('answerCallbackQuery',{'callback_query_id':callback['id'],'text':notice})
        except urllib.error.HTTPError as error:
            if error.code!=400:raise  # Expired query acknowledgements must not stall all later clicks.


def poll_once(connect):
    global last_error
    if not os.environ.get('FREELANCE_TELEGRAM_TOKEN') or not os.environ.get('FREELANCE_TELEGRAM_CHAT_ID'):return False
    bot=identity()
    with connect() as db:row=db.execute('SELECT offset FROM telegram_poll WHERE bot=?',(bot,)).fetchone()
    offset=row[0] if row else 0
    response=api('getUpdates',{'offset':offset,'timeout':15,'limit':30,'allowed_updates':['callback_query']})
    if not isinstance(response,dict) or response.get('ok') is not True:raise ValueError('Telegram rejected updates')
    updates=response.get('result')
    if not isinstance(updates,list):raise ValueError('Invalid Telegram updates')
    for update in updates:
        if not isinstance(update,dict) or type(update.get('update_id')) is not int:continue
        if 'callback_query' in update:process_callback(connect,update['callback_query'])
        offset=max(offset,update['update_id']+1)
        with connect() as db:db.execute('INSERT INTO telegram_poll VALUES(?,?) ON CONFLICT(bot) DO UPDATE SET offset=excluded.offset',(bot,offset))
    last_error=''
    return True


def worker(connect):
    global last_error
    while True:
        try:
            if not poll_once(connect):time.sleep(5)
        except Exception:
            # Do not delete webhooks or take over another bot consumer automatically.
            last_error='Chưa đọc được nút Telegram. Giữ app mở; kiểm tra bot có đang dùng webhook hoặc một ứng dụng nhận cập nhật khác không.'
            time.sleep(30)

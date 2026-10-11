"""Provider adapter. Credentials stay in headers, never URLs or frontend data."""
import os
import json
import re
import urllib.error
import urllib.request
from urllib.parse import quote, urlencode

DEFAULT_MODELS = {'openai': 'gpt-4.1-mini', 'gemini': 'gemini-2.5-flash'}


def provider():
    from services import ServiceError
    value = os.environ.get('FREELANCE_AI_PROVIDER', 'openai').strip().lower()
    if value not in DEFAULT_MODELS:
        raise ServiceError('Nhà cung cấp AI cần là gemini hoặc openai. Mở configure-windows.bat để chọn lại.', 503)
    return value


def model():
    value = os.environ.get('FREELANCE_AI_MODEL', '').strip() or DEFAULT_MODELS[provider()]
    if provider() == 'gemini':
        value = value.removeprefix('models/')
    return value


def automatic_jobs():
    """Gemini defaults to on-demand job scoring so writing retains its free quota."""
    value = os.environ.get('FREELANCE_AI_AUTO_JOBS', '').strip().lower()
    return value in ('1', 'true', 'yes') if value else provider() == 'openai'


def request(payload, transport):
    """Keep the established completed/text contract for every existing AI feature."""
    from services import ServiceError
    key = os.environ.get('FREELANCE_AI_KEY')
    if not key:
        raise ServiceError('Chưa có khóa AI. Mở configure-windows.bat, chọn Gemini hoặc OpenAI và nhập khóa rồi khởi động lại.', 503)
    if provider() == 'openai':
        try:
            return transport('https://api.openai.com/v1/responses', payload, {'Authorization': 'Bearer ' + key})
        except urllib.error.HTTPError as error:
            try:
                detail = json.loads(error.read(65536)).get('error', {})
                code = detail.get('code') or detail.get('type')
            except (ValueError,OSError,AttributeError):
                code = None
            if code in ('insufficient_quota','billing_hard_limit_reached','billing_not_active'):
                raise ServiceError('OpenAI: tài khoản API chưa có credit, đã hết credit hoặc chạm giới hạn chi tiêu. Kiểm tra Billing và Usage trên platform.openai.com. Gói ChatGPT không bao gồm tiền API; bản nháp được giữ nguyên.', 429) from None
            if error.code == 429:
                raise ServiceError('OpenAI HTTP 429: đang giới hạn lượt gọi hoặc hạn mức. Kiểm tra Usage và Billing; chờ rồi thử lại nếu còn credit.', 429) from None
            if error.code in (401,403):
                raise ServiceError('OpenAI: khóa API không hợp lệ, bị thu hồi hoặc không có quyền dùng model. Cập nhật khóa trong Hồ sơ & kết nối.', 502) from None
            if error.code == 404:
                raise ServiceError('OpenAI HTTP 404: không tìm thấy model hoặc tài khoản chưa có quyền sử dụng. Kiểm tra model đã cấu hình.', 502) from None
            if error.code == 400:
                raise ServiceError('OpenAI HTTP 400: model từ chối tham số hoặc định dạng yêu cầu. Báo lại lỗi này để kiểm tra phần tích hợp.', 502) from None
            raise ServiceError('OpenAI HTTP '+str(error.code)+': dịch vụ chưa xử lý được yêu cầu. Bản nháp được giữ nguyên; thử lại sau.', 502) from None

    generation = {'maxOutputTokens': payload.get('max_output_tokens', 2200)}
    schema = payload.get('text', {}).get('format', {}).get('schema')
    if schema:
        generation.update(responseMimeType='application/json', responseJsonSchema=schema)
    # Flash 2.5 supports disabling thinking; reserve the output budget for the requested content.
    if model().startswith('gemini-2.5-flash'):
        generation['thinkingConfig'] = {'thinkingBudget': 0}
    body = {
        'systemInstruction': {'parts': [{'text': payload.get('instructions', '')}]},
        'contents': [{'role': 'user', 'parts': [{'text': payload.get('input', '')}]}],
        'generationConfig': generation,
    }
    try:
        result = transport('https://generativelanguage.googleapis.com/v1beta/models/' + quote(model(), safe='') + ':generateContent',
                           body, {'x-goog-api-key': key})
    except urllib.error.HTTPError as error:
        try:
            detail = json.loads(error.read(65536)).get('error', {})
            message = str(detail.get('message', '')).lower()
            reasons = {str(d.get('reason', '')) for d in detail.get('details', []) if isinstance(d, dict)}
        except (ValueError, OSError, AttributeError, TypeError):
            message, reasons = '', set()
            detail = {}
        explanation = str(detail.get('message', '')).replace('\n',' ')
        # Provider diagnostics may echo request values; remove locally configured secrets.
        for name, secret in os.environ.items():
            if name.startswith('FREELANCE_') and any(word in name for word in ('KEY','TOKEN','PASSWORD')) and secret:
                explanation = explanation.replace(secret, '[ẩn]')
        explanation = re.sub(r'(?:AIza|AQ\.)[A-Za-z0-9_-]+', '[ẩn]', explanation)[:600]
        if 'API_KEY_INVALID' in reasons or 'api key not valid' in message or 'api key expired' in message:
            raise ServiceError('Gemini: khóa API không hợp lệ hoặc đã hết hiệu lực. Mở configure-windows.bat, chọn 1 = Gemini và dán khóa mới từ Google AI Studio.', 502) from None
        if 'API_KEY_SERVICE_BLOCKED' in reasons or 'SERVICE_DISABLED' in reasons:
            raise ServiceError('Gemini: dự án hoặc khóa chưa được phép gọi Generative Language API. Kiểm tra dự án và giới hạn của khóa trong Google AI Studio.', 502) from None
        if error.code == 429:
            raise ServiceError('Gemini đã chạm hạn mức. Chờ hạn mức phục hồi hoặc kiểm tra quota/model trong Google AI Studio.', 429) from None
        if error.code in (401, 403):
            raise ServiceError('Gemini từ chối khóa API. Kiểm tra khóa, quyền truy cập và khu vực tài khoản trong Google AI Studio.', 502) from None
        if error.code == 404:
            if explanation:
                raise ServiceError('Gemini HTTP 404 — Google trả lời: '+explanation+' Chọn model khác trong Hồ sơ & kết nối và kiểm tra kết nối.', 502) from None
            raise ServiceError('Gemini HTTP 404 nhưng không có nội dung lỗi JSON từ Google. Có thể đường gọi bị proxy hoặc phần mềm mạng chặn. Thử tắt VPN/proxy hoặc dùng mạng khác rồi kiểm tra kết nối.', 502) from None
        if error.code == 400:
            if 'thinking' in message:
                reason = 'cấu hình thinking không được model chấp nhận'
            elif any(word in message for word in ('schema', 'responsejson', 'response_schema')):
                reason = 'model từ chối định dạng JSON/schema của yêu cầu'
            elif 'model' in message:
                reason = 'tên model không hợp lệ'
            else:
                reason = 'tham số yêu cầu không hợp lệ'
            raise ServiceError('Gemini: '+reason+' (HTTP 400). Kiểm tra Model AI trong Hồ sơ & kết nối; báo lại nguyên thông báo này để kiểm tra.', 502) from None
        suffix = (' Google trả lời: '+explanation) if explanation else ' Google không trả về chi tiết lỗi.'
        if error.code == 503:
            raise ServiceError('Gemini HTTP 503: model đang tạm thời không phục vụ hoặc quá tải.'+suffix+' Đợi một lúc hoặc chọn model Flash khác rồi Kiểm tra kết nối.', 502) from None
        if error.code == 500:
            raise ServiceError('Gemini đang gặp lỗi nội bộ HTTP 500.'+suffix+' Thử Kiểm tra kết nối; nếu chỉ lỗi khi viết thư, báo lại thông báo này.', 502) from None
        raise ServiceError('Gemini đang gặp lỗi HTTP '+str(error.code)+'.'+suffix, 502) from None
    except (OSError, ValueError):
        raise ServiceError('Chưa kết nối được Gemini. Kiểm tra mạng rồi thử lại.', 502) from None
    try:
        if result.get('promptFeedback', {}).get('blockReason'):
            raise ServiceError('Gemini từ chối xử lý nội dung này. Kiểm tra mô tả và yêu cầu rồi thử lại.', 502)
        candidate = result['candidates'][0]
        if candidate.get('finishReason') != 'STOP':
            raise ServiceError('Gemini chưa trả về nội dung hoàn chỉnh. Thử rút ngắn yêu cầu hoặc kho mẫu rồi thử lại.', 502)
        parts = candidate.get('content', {}).get('parts', [])
        output = '\n'.join(p['text'] for p in parts if isinstance(p, dict) and isinstance(p.get('text'), str) and not p.get('thought')).strip()
        if not output:
            raise ValueError()
        return {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': output}]}]}
    except (KeyError, IndexError, TypeError, AttributeError, ValueError):
        raise ServiceError('Gemini chưa trả về nội dung hợp lệ. Thử lại; bản nháp hiện tại được giữ nguyên.', 502) from None


def gemini_models():
    """Discover only models offering generateContent; credentials remain in headers."""
    from services import ServiceError
    key = os.environ.get('FREELANCE_AI_KEY', '')
    if provider() != 'gemini' or not key:
        raise ServiceError('Chọn Gemini và nhập khóa API trong công cụ cấu hình trước.', 503)
    models, token = {}, ''
    for _ in range(20):
        url = 'https://generativelanguage.googleapis.com/v1beta/models?' + urlencode({'pageSize':100, **({'pageToken':token} if token else {})})
        req = urllib.request.Request(url, headers={'x-goog-api-key':key})
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                data = json.load(response)
        except urllib.error.HTTPError as error:
            if error.code in (400,401,403):
                raise ServiceError('Gemini không cho lấy danh sách model. Kiểm tra khóa API và quyền của dự án trong Google AI Studio.', 502) from None
            if error.code == 429:
                raise ServiceError('Gemini đang giới hạn lượt gọi. Chờ một lúc rồi lấy lại danh sách.', 429) from None
            raise ServiceError('Không lấy được danh sách Gemini. Thử lại sau.', 502) from None
        except (OSError, ValueError):
            raise ServiceError('Không kết nối được Gemini để lấy model. Kiểm tra mạng rồi thử lại.', 502) from None
        if not isinstance(data,dict):
            raise ServiceError('Danh sách Gemini trả về không hợp lệ.', 502)
        for entry in data.get('models', []):
            if not isinstance(entry,dict) or 'generateContent' not in entry.get('supportedGenerationMethods', []): continue
            name = entry.get('name','')
            if not isinstance(name,str) or not name.startswith('models/'): continue
            ident = name.removeprefix('models/')
            models[ident] = {'id':ident, 'label':str(entry.get('displayName') or ident)}
        token = data.get('nextPageToken')
        if not token: break
    else:
        raise ServiceError('Danh sách model quá dài. Thử lại sau.', 502)
    if not models:
        raise ServiceError('Khóa này chưa có model hỗ trợ viết nội dung. Kiểm tra dự án trong Google AI Studio.', 502)
    return sorted(models.values(), key=lambda m:('flash' not in m['id'], m['id']))


def select_gemini_model(ident):
    from services import ServiceError
    from local_config import config_path, save
    if not isinstance(ident,str) or ident not in {m['id'] for m in gemini_models()}:
        raise ServiceError('Model không nằm trong danh sách Gemini hỗ trợ. Lấy lại danh sách rồi chọn.')
    path = config_path()
    try:
        values = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        if not isinstance(values,dict) or any(not isinstance(v,str) for v in values.values()): raise ValueError()
        values['FREELANCE_AI_MODEL'] = ident
        save(values)
    except (OSError,ValueError):
        raise ServiceError('Không lưu được model. Kiểm tra quyền ghi thư mục data.', 500) from None
    os.environ['FREELANCE_AI_MODEL'] = ident
    return ident

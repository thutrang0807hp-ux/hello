"""Provider adapter. Credentials stay in headers, never URLs or frontend data."""
import os
import json
import urllib.error
from urllib.parse import quote

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
        return transport('https://api.openai.com/v1/responses', payload, {'Authorization': 'Bearer ' + key})
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
        if 'API_KEY_INVALID' in reasons or 'api key not valid' in message or 'api key expired' in message:
            raise ServiceError('Gemini: khóa API không hợp lệ hoặc đã hết hiệu lực. Mở configure-windows.bat, chọn 1 = Gemini và dán khóa mới từ Google AI Studio.', 502) from None
        if 'API_KEY_SERVICE_BLOCKED' in reasons or 'SERVICE_DISABLED' in reasons:
            raise ServiceError('Gemini: dự án hoặc khóa chưa được phép gọi Generative Language API. Kiểm tra dự án và giới hạn của khóa trong Google AI Studio.', 502) from None
        if error.code == 429:
            raise ServiceError('Gemini đã chạm hạn mức. Chờ hạn mức phục hồi hoặc kiểm tra quota/model trong Google AI Studio.', 429) from None
        if error.code in (401, 403):
            raise ServiceError('Gemini từ chối khóa API. Kiểm tra khóa, quyền truy cập và khu vực tài khoản trong Google AI Studio.', 502) from None
        if error.code == 404:
            raise ServiceError('Gemini: không tìm thấy model hoặc model không hỗ trợ generateContent (HTTP 404). Đặt Model AI thành gemini-2.5-flash trong configure-windows.bat rồi khởi động lại.', 502) from None
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
        raise ServiceError('Gemini đang gặp lỗi. Thử lại sau; nội dung hiện tại được giữ nguyên.', 502) from None
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

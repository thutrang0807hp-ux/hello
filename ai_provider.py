"""Provider adapter. Credentials stay in headers, never URLs or frontend data."""
import os
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
        if error.code == 429:
            raise ServiceError('Gemini đã chạm hạn mức. Chờ hạn mức phục hồi hoặc kiểm tra quota/model trong Google AI Studio.', 429) from None
        if error.code in (401, 403):
            raise ServiceError('Gemini từ chối khóa API. Kiểm tra khóa, quyền truy cập và khu vực tài khoản trong Google AI Studio.', 502) from None
        if error.code in (400, 404):
            raise ServiceError('Gemini chưa chấp nhận model hoặc yêu cầu. Kiểm tra tên model trong configure-windows.bat.', 502) from None
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

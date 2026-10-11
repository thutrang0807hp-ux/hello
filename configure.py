"""Interactive configuration on the user's own computer. Never echoes tokens."""
import getpass
import json
from local_config import config_path, save


def configure():
    print('Freelance Desk — cấu hình trên máy của bạn')
    print('Enter: giữ giá trị hiện tại hoặc bỏ qua. Nhập dấu - để xóa một giá trị.')
    path = config_path()
    try:
        previous = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        if not isinstance(previous, dict) or any(not isinstance(value, str) for value in previous.values()):
            raise ValueError()
    except (ValueError, OSError):
        print('Không đọc được cấu hình hiện tại. Hãy sao lưu/khôi phục tệp trước khi cấu hình lại.')
        return False
    prompts = [
        ('FREELANCE_PASSWORD', 'Mật khẩu mở web (khuyên dùng)', True),
        ('FREELANCE_AI_KEY', 'Khóa API OpenAI để viết thư bằng AI', True),
        ('FREELANCE_AI_MODEL', 'Model AI (mặc định gpt-4.1-mini)', False),
        ('FREELANCE_SLACK_TOKEN', 'Slack bot token (quyền chat:write)', True),
        ('FREELANCE_SLACK_CHANNEL', 'Slack channel ID', False),
        ('FREELANCE_TELEGRAM_TOKEN', 'Telegram bot token từ BotFather', True),
        ('FREELANCE_TELEGRAM_CHAT_ID', 'Telegram chat ID', False),
    ]
    values = dict(previous)
    for name, label, secret in prompts:
        status = ' [đã có]' if previous.get(name) else ''
        value = (getpass.getpass if secret else input)(label + status + ': ')
        if value == '-':
            values.pop(name, None)
        elif value:
            values[name] = value
    if bool(values.get('FREELANCE_SLACK_TOKEN')) != bool(values.get('FREELANCE_SLACK_CHANNEL')):
        print('Slack cần cả token lẫn channel ID; kênh chưa đầy đủ sẽ chưa gửi thông báo.')
    if bool(values.get('FREELANCE_TELEGRAM_TOKEN')) != bool(values.get('FREELANCE_TELEGRAM_CHAT_ID')):
        print('Telegram cần cả token lẫn chat ID; kênh chưa đầy đủ sẽ chưa gửi thông báo.')
    save(values)
    print('Đã lưu riêng trong thư mục data. Không chia sẻ thư mục này hoặc đưa vào Git.')
    print('Khởi động lại ứng dụng để áp dụng cấu hình mới.')
    return True


if __name__ == '__main__':
    configure()

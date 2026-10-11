"""Interactive configuration on the user's own computer. Secrets stay local; Windows entry is masked unless revealed."""
import getpass
import json
import sys
from local_config import config_path, save
from ai_provider import DEFAULT_MODELS


def secret_input(label):
    if sys.platform != 'win32':
        return getpass.getpass(label + ': ')
    try:
        import tkinter as tk
        from tkinter import ttk
        root = tk.Tk()
    except Exception:
        print('Không mở được hộp nhập. Thử chạy cấu hình trong Windows Terminal.')
        return getpass.getpass(label + ': ')
    root.title('Freelance Desk — nhập thông tin riêng tư')
    root.geometry('560x230')
    root.minsize(460, 230)
    root.attributes('-topmost', True)
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text=label, wraplength=500).pack(anchor='w')
    value = tk.StringVar()
    entry = ttk.Entry(frame, textvariable=value, show='•')
    entry.pack(fill='x', pady=(12, 8))
    status = ttk.Label(frame, text='Dán bằng Ctrl+V hoặc nút Dán. Để trống để giữ/bỏ qua.')
    status.pack(anchor='w')
    buttons = ttk.Frame(frame)
    buttons.pack(fill='x', pady=16)
    result = ['']
    def paste():
        try:
            value.set(root.clipboard_get().strip())
            status.configure(text='Đã dán khóa.' if value.get() else 'Clipboard đang trống.')
            entry.focus_set()
        except tk.TclError:
            status.configure(text='Clipboard chưa có chữ. Hãy sao chép khóa rồi thử lại.')
    def reveal():
        hidden = bool(entry.cget('show'))
        entry.configure(show='' if hidden else '•')
        toggle.configure(text='Ẩn' if hidden else 'Hiện')
    def accept(event=None):
        result[0] = value.get()
        root.destroy()
    ttk.Button(buttons, text='Dán', command=paste).pack(side='left')
    toggle = ttk.Button(buttons, text='Hiện', command=reveal)
    toggle.pack(side='left', padx=8)
    ttk.Button(buttons, text='Tiếp tục', command=accept).pack(side='right')
    root.bind('<Return>', accept)
    root.protocol('WM_DELETE_WINDOW', accept)
    root.after(100, entry.focus_force)
    root.mainloop()
    return result[0]


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
    values = dict(previous)
    def prompt(name, label, secret=False):
        status = ' [đã có]' if values.get(name) else ''
        value = (secret_input(label + status) if secret else input(label + status + ': ')).strip()
        if value == '-':
            values.pop(name, None)
        elif value:
            values[name] = value
    prompt('FREELANCE_PASSWORD', 'Mật khẩu mở web (khuyên dùng)', True)
    old_provider = previous.get('FREELANCE_AI_PROVIDER', 'openai' if previous.get('FREELANCE_AI_KEY') else 'gemini')
    if old_provider not in DEFAULT_MODELS:
        old_provider = 'gemini'
    while True:
        choice = input(f'AI: 1 = Gemini, 2 = OpenAI (Enter giữ {old_provider}): ').strip().lower()
        selected = {'1': 'gemini', '2': 'openai', 'gemini': 'gemini', 'openai': 'openai', '': old_provider}.get(choice)
        if selected:
            break
        print('Chọn 1 (Gemini) hoặc 2 (OpenAI).')
    if selected != old_provider:
        values.pop('FREELANCE_AI_KEY', None)
        values.pop('FREELANCE_AI_MODEL', None)
        print('Đã đổi nhà cung cấp. Hãy nhập khóa của nhà cung cấp mới; khóa cũ sẽ không được dùng nhầm.')
    values['FREELANCE_AI_PROVIDER'] = selected
    if selected == 'gemini':
        print('Tạo khóa Gemini tại https://aistudio.google.com/apikey')
        print('Mức miễn phí tùy model/tài khoản và có quota; ứng dụng không bảo đảm mọi lượt gọi đều miễn phí.')
    prompt('FREELANCE_AI_KEY', f'Khóa API {"Gemini" if selected == "gemini" else "OpenAI"}', True)
    prompt('FREELANCE_AI_MODEL', f'Model AI (mặc định {DEFAULT_MODELS[selected]})')
    prompt('FREELANCE_SLACK_TOKEN', 'Slack bot token (quyền chat:write)', True)
    prompt('FREELANCE_SLACK_CHANNEL', 'Slack channel ID')
    prompt('FREELANCE_TELEGRAM_TOKEN', 'Telegram bot token từ BotFather', True)
    prompt('FREELANCE_TELEGRAM_CHAT_ID', 'Telegram chat ID')
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

"""Windows desktop window + tray; the existing local backend keeps the same data."""
import ctypes
import hashlib
import json
import os
import sys
import threading
import webbrowser
from pathlib import Path

TITLE = 'Freelance Desk'


class DesktopController:
    """Small, testable lifecycle: close hides, explicit exit stops our local server."""
    def __init__(self, window, stop_server, ready=True):
        self.window = window
        self.ready = ready
        self.stop_server = stop_server
        self.tray = None
        self.exiting = False
        self.lock = threading.Lock()

    def closing(self):
        if self.exiting:
            return True
        if self.tray is None:
            # Without a tray the user must never be left with an invisible app.
            self.quit()
            return True
        self.window.hide()
        return False

    def show(self, *_):
        self.window.show()
        self.window.restore()

    def quit(self, *_):
        with self.lock:
            if self.exiting:
                return
            self.exiting = True
        try:
            self.stop_server()
        except Exception:
            from desktop_background import message
            message('Chưa dừng được dịch vụ nền. Dùng stop-background-windows.bat để dừng; dữ liệu vẫn được giữ.', True)
        finally:
            if self.tray:
                self.tray.stop()
            if self.ready:
                self.window.destroy()


class DesktopAPI:
    def __init__(self, port):
        self.port = int(port)

    def open_mail_browser(self):
        # No URL argument: JS cannot use this bridge to execute commands or open files.
        webbrowser.open(f'http://127.0.0.1:{self.port}/?openMail=1')
        return {'ok': True}


def single_instance(directory):
    """Mutex belongs to this data directory, never to an arbitrary Python process."""
    identity = hashlib.sha256(str(Path(directory).resolve()).casefold().encode()).hexdigest()[:24]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    kernel.CreateMutexW.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.CreateMutexW(None, False, 'Local\\FreelanceDesk-' + identity)
    if not handle:
        raise RuntimeError('Không tạo được phiên ứng dụng. Thử mở lại.')
    duplicate = ctypes.get_last_error() == 183
    if duplicate:
        user = ctypes.windll.user32
        user.FindWindowW.restype = ctypes.c_void_p
        user.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
        window = user.FindWindowW(None, TITLE)
        if window:
            user.ShowWindow(ctypes.c_void_p(window), 9)
            user.SetForegroundWindow(ctypes.c_void_p(window))
        kernel.CloseHandle(handle)
        return None, kernel
    return handle, kernel


def main():
    if os.name != 'nt':
        raise RuntimeError('Bản desktop này dành cho Windows 10/11.')
    from data_store import data_directory
    from desktop_background import start, stop, message
    from desktop_diagnostics import require_runtime, report, safe_error
    # pythonw has no console streams; libraries must not fail while writing diagnostics.
    if sys.stdout is None:sys.stdout=open(os.devnull,'w',encoding='utf-8')
    if sys.stderr is None:sys.stderr=open(os.devnull,'w',encoding='utf-8')
    handle = kernel = controller = item = None
    stage = 'Kiểm tra thành phần Windows'
    try:
        require_runtime()
        stage = 'Mở phiên ứng dụng'
        handle, kernel = single_instance(data_directory())
        if handle is None:return 0
        stage = 'Nạp thư viện desktop'
        import webview
        import pystray
        from PIL import Image, ImageDraw
        stage = 'Khởi động dịch vụ local'
        item = start(open_browser=False)
        window = webview.create_window(TITLE, f"http://127.0.0.1:{item['port']}/?desktop=1",
                                       js_api=DesktopAPI(item['port']), width=1360, height=900,
                                       min_size=(760, 560), text_select=True)
        controller = DesktopController(window, stop, ready=False)
        def shown():controller.ready=True
        window.events.shown += shown
        window.events.closing += controller.closing
        image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((5, 5, 59, 59), radius=14, fill='#246b51')
        draw.line((22, 46, 22, 19, 43, 19), fill='white', width=6)
        draw.line((22, 31, 39, 31), fill='white', width=6)
        tray = pystray.Icon('freelance-desk', image, TITLE,
                            menu=pystray.Menu(pystray.MenuItem('Mở ứng dụng', controller.show, default=True),
                                              pystray.MenuItem('Thoát hoàn toàn', controller.quit)))
        def tray_setup(icon):
            icon.visible = True
            controller.tray = icon
        def run_tray():
            try:
                tray.run(setup=tray_setup)
            except Exception:
                controller.tray = None
                controller.show()
                message('Không mở được khay hệ thống. Đóng cửa sổ sẽ thoát ứng dụng.', True)
        threading.Thread(target=run_tray, daemon=True).start()
        # Edge Chromium/WebView2 is required; never fall back to obsolete IE.
        profile = data_directory() / 'desktop-webview'
        if profile.is_symlink():
            raise RuntimeError('Không dùng thư mục WebView là liên kết tệp.')
        profile.mkdir(exist_ok=True)
        marker = profile / '.freelance-profile.json'
        if marker.is_symlink():
            raise RuntimeError('Không ghi đè dấu dữ liệu WebView là liên kết tệp.')
        if marker.exists() and json.loads(marker.read_text(encoding='utf-8')).get('application')!='Freelance Desk WebView':
            raise RuntimeError('Giữ thư mục WebView không thuộc app.')
        if not marker.exists() and any(profile.iterdir()):
            raise RuntimeError('Thư mục WebView đã tồn tại; giữ nguyên để kiểm tra.')
        marker.write_text(json.dumps({'application':'Freelance Desk WebView'}), encoding='utf-8')
        stage = 'Khởi tạo cửa sổ WebView2'
        from webview.guilib import initialize
        if initialize('edgechromium').renderer!='edgechromium':
            raise RuntimeError('Thư viện chưa sử dụng được WebView2. Chạy repair-webview2-windows.bat; app không dùng bộ hiển thị IE cũ.')
        webview.start(gui='edgechromium', private_mode=False, storage_path=str(profile))
        return 0
    except ImportError as error:
        report(stage,error)
        message('Thiếu thư viện desktop: '+safe_error(error)+'\nChạy install-desktop-windows.bat để cài lại. Chi tiết: desktop-diagnostic.txt.', True)
        return 1
    except Exception as error:
        report(stage,error)
        message(stage+'\n'+type(error).__name__+': '+safe_error(error)+'\n\nChạy diagnose-desktop-windows.bat và gửi nội dung desktop-diagnostic.txt nếu vẫn lỗi.', True)
        return 1
    finally:
        if controller and not controller.exiting:
            controller.quit()
        elif item and not controller:
            stop()
        if handle is not None:kernel.CloseHandle(handle)


if __name__ == '__main__':
    raise SystemExit(main())

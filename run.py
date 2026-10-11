"""Desktop launcher: explicit optional setup and open the local browser."""
import json
import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path
from local_config import load


def main():
    if sys.version_info < (3, 10):
        print('Freelance Desk cần Python 3.10 trở lên.')
        return 1
    if '--configure' in sys.argv:
        from configure import configure
        if not configure():
            return 1
    load()
    port = int(os.environ.get('PORT', '8000'))
    process = subprocess.Popen([sys.executable, str(Path(__file__).with_name('server.py'))])
    address = 'http://127.0.0.1:' + str(port)
    try:
        for _ in range(100):
            if process.poll() is not None:
                print('Máy chủ chưa khởi động được. Nếu cổng đang được dùng, đóng bản đang chạy hoặc chọn PORT khác.')
                return 1
            try:
                with urllib.request.urlopen(address + '/api/auth', timeout=1) as response:
                    if isinstance(json.load(response).get('authenticated'), bool):
                        # Give a conflicting port time to fail before opening a different instance.
                        time.sleep(.2)
                        if process.poll() is not None:
                            return 1
                        webbrowser.open(address)
                        print('Web đã mở trên trình duyệt. Giữ cửa sổ này mở; nhấn Ctrl+C để dừng.')
                        process.wait()
                        return process.returncode
            except OSError:
                time.sleep(.1)
        print('Hết thời gian chờ khởi động.')
        return 1
    except KeyboardInterrupt:
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait()


if __name__ == '__main__':
    raise SystemExit(main())

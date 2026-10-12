"""One-time Windows dependency installer; no admin or system-wide pip changes."""
import os
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    if os.name != 'nt' or not ((3, 10) <= sys.version_info[:2] < (3, 14)):
        print('Cần Windows 10/11 và Python 3.10–3.13 (khuyên dùng 3.12).')
        return 1
    if (ROOT / '.desktop-venv').is_symlink():
        print('Thư mục .desktop-venv là liên kết; giữ nguyên và kiểm tra trước khi cài.')
        return 1
    subprocess.run([sys.executable, '-m', 'venv', str(ROOT / '.desktop-venv')], check=True)
    python = ROOT / '.desktop-venv' / 'Scripts' / 'python.exe'
    subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(ROOT / 'desktop-requirements.txt')], check=True)
    installed = [file.relative_to(ROOT).as_posix() for file in (ROOT / '.desktop-venv').rglob('*') if file.is_file() and not file.is_symlink()]
    (ROOT / '.desktop-installed-files.json').write_text(json.dumps({'application':'Freelance Desk desktop','files':installed}),encoding='utf-8')
    from desktop_diagnostics import windows_runtime, require_runtime, MissingNet
    if not windows_runtime().get('webview2'):
        print('Chưa có WebView2. Bộ cài sẽ tải bản chính thức và kiểm tra chữ ký Microsoft.')
        repair_env=dict(os.environ,FREELANCE_DESKTOP_ROOT=str(ROOT))
        repair_command="& ([scriptblock]::Create([IO.File]::ReadAllText((Join-Path $env:FREELANCE_DESKTOP_ROOT 'repair-webview2-windows.ps1'))))"
        subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',repair_command],env=repair_env,check=True)
    try:require_runtime()
    except RuntimeError as error:
        print(str(error))
        return 1
    # Literal paths travel through environment variables, never PowerShell source interpolation.
    env = dict(os.environ, FREELANCE_DESKTOP_ROOT=str(ROOT))
    script = r"""
$ErrorActionPreference = 'Stop'
$deskRoot = $env:FREELANCE_DESKTOP_ROOT
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Freelance Desk.lnk'))
$shortcut.TargetPath = Join-Path $deskRoot '.desktop-venv\Scripts\pythonw.exe'
$shortcut.Arguments = '"' + (Join-Path $deskRoot 'desktop_app.py') + '"'
$shortcut.WorkingDirectory = $deskRoot
$shortcut.IconLocation = (Join-Path $deskRoot 'public\desktop.ico')
$shortcut.Description = 'Freelance Desk - ung dung local'
$shortcut.Save()
"""
    subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script], env=env, check=True)
    print('Đã cài. Bấm biểu tượng Freelance Desk trên Desktop để mở, không cần CMD.')
    print('Windows cần Microsoft Edge WebView2 Runtime. Nếu thiếu: https://developer.microsoft.com/microsoft-edge/webview2/')
    subprocess.Popen([str(ROOT / '.desktop-venv' / 'Scripts' / 'pythonw.exe'), str(ROOT / 'desktop_app.py')], cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError:
        print('Cài chưa thành công. Kiểm tra Internet và lỗi phía trên rồi chạy lại bộ cài.')
        raise SystemExit(1)

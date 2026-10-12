@echo off
set "DESK_UNINSTALL_ROOT=%~dp0"
(
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%TEMP%"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%DESK_UNINSTALL_ROOT%uninstall_desk.py"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Chua tim thay Python. Cai Python 3.12 tu https://www.python.org/downloads/windows/
    echo Tich Add python.exe to PATH, sau do mo lai file nay.
    pause
    exit /b 1
  )
  python "%DESK_UNINSTALL_ROOT%uninstall_desk.py"
)
pause
)

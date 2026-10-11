@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 run.py
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Chua tim thay Python. Cai Python 3.12 tu https://www.python.org/downloads/windows/
    echo Tich Add python.exe to PATH, sau do mo lai file nay.
    pause
    exit /b 1
  )
  python run.py
)
pause

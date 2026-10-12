@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 install_desktop.py
) else (
  python install_desktop.py
)
if errorlevel 1 (
  echo Cai chua thanh cong. Xem dong loi cu the o phia tren.
  pause
  exit /b 1
)
pause

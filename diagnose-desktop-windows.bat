@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if exist ".desktop-venv\Scripts\python.exe" (
  ".desktop-venv\Scripts\python.exe" desktop_diagnostics.py
) else (
  echo Chua cai desktop. Chay install-desktop-windows.bat truoc.
  where py >nul 2>nul
  if %errorlevel% equ 0 (py -3 desktop_diagnostics.py) else (python desktop_diagnostics.py)
)
pause

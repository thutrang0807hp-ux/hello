@echo off
cd /d "%~dp0"
set "FREELANCE_DESKTOP_ROOT=%~dp0"
powershell.exe -NoProfile -Command "& ([scriptblock]::Create([IO.File]::ReadAllText((Join-Path $env:FREELANCE_DESKTOP_ROOT 'repair-webview2-windows.ps1'))))"
pause

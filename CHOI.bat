@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "THONNY=%LOCALAPPDATA%\Programs\Thonny\python.exe"
if exist "%THONNY%" (
    "%THONNY%" game.py
) else (
    python game.py
)
if errorlevel 1 pause

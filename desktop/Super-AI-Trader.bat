@echo off
REM Super-AI-Trader launcher for Windows. Double-click this file.
cd /d "%~dp0\.."
where python >nul 2>nul
if errorlevel 1 (
  echo Python 3 is not installed. Install from https://www.python.org - tick "Add Python to PATH".
  pause
  exit /b 1
)
if not exist .venv (
  echo First run: creating a private environment (one-time)...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
python -c "import ccxt" 2>nul || pip install -q ccxt
python -c "import webview" 2>nul || pip install -q pywebview
python -c "import pystray" 2>nul || pip install -q pystray pillow
python start_app.py
pause

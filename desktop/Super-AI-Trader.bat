@echo off
REM Super-AI-Trader launcher for Windows. Double-click this file.
cd /d "%~dp0\.."
where python >nul 2>nul
if errorlevel 1 (
  echo Python 3 is not installed.
  echo Install it from https://www.python.org  (tick "Add Python to PATH") then run again.
  pause
  exit /b 1
)
python -c "import ccxt" 2>nul || echo (Tip: pip install ccxt  for live Binance/Gate prices)
python start_app.py
pause

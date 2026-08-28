#!/bin/bash
# Super-AI-Trader launcher for macOS. Double-click this file (or put in Dock).
# It creates a private Python environment (venv) the first time so installs
# never clash with Homebrew's Python, then opens the app.
cd "$(dirname "$0")/.."

# Find a Python 3 (prefer 3.11-3.13; the app is stdlib-first).
PY=$(command -v python3)
if [ -z "$PY" ]; then
  osascript -e 'display dialog "Python 3 is not installed. Install it from https://www.python.org then run again." buttons {"OK"}' 2>/dev/null
  echo "Python 3 not found. Install from https://www.python.org"
  exit 1
fi

VENV=".venv"
if [ ! -d "$VENV" ]; then
  echo "First run: creating a private environment (one-time)…"
  "$PY" -m venv "$VENV" || { echo "Could not create venv"; "$PY" start_app.py; exit; }
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

# Optional extras for native window / tray / live exchange data.
python -c "import ccxt" 2>/dev/null || pip install -q ccxt || true
python -c "import webview" 2>/dev/null || pip install -q pywebview || true
python -c "import pystray" 2>/dev/null || pip install -q pystray pillow || true

exec python start_app.py

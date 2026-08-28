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
# Install into the ACTIVE venv (which is now activated). Retry with a visible error.
ensure() {
  python -c "import $1" 2>/dev/null && return 0
  echo "Installing $1 (one-time)…"
  if ! python -m pip install "$2"; then
    echo "WARNING: could not install $2 — that feature will be off."
  fi
}
ensure ccxt ccxt
ensure webview pywebview
# tray is not auto-started on Mac (NSApplication main-thread crash); skip pystray install.

export SAT_NATIVE=0
export SAT_TRAY=0  # tray NSApplication is unsafe from a double-click script on Mac
exec python start_app.py


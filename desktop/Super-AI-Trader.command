#!/bin/bash
# Super-AI-Trader launcher for macOS. Double-click this file (or put it in Dock).
cd "$(dirname "$0")/.."
if ! command -v python3 >/dev/null 2>&1; then
  osascript -e 'display dialog "Python 3 is not installed. Install it from https://www.python.org then run again." buttons {"OK"}' 2>/dev/null
  echo "Python 3 not found. Install from https://www.python.org"
  exit 1
fi
# Optional: auto-install ccxt for live exchange data (no harm if offline).
python3 -c "import ccxt" 2>/dev/null || echo "(Tip: pip3 install ccxt  for live Binance/Gate prices)"
exec python3 start_app.py

#!/bin/bash
# Super-AI-Trader launcher for Linux. Double-click or run: ./Super-AI-Trader.sh
cd "$(dirname "$0")/.."
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed. Install python3 then run again."
  read -r -p "Press Enter to exit..."
  exit 1
fi
python3 -c "import ccxt" 2>/dev/null || echo "(Tip: pip3 install ccxt  for live Binance/Gate prices)"
exec python3 start_app.py

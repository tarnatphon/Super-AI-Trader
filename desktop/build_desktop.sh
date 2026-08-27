#!/bin/bash
# Build a standalone double-click app with PyInstaller (optional, one-time).
# Produces dist/Super-AI-Trader/ with a runnable binary (no terminal needed).
#
#   macOS:   run this script  -> dist/Super-AI-Trader.app (drag to /Applications)
#   Windows: pip install pyinstaller && pyinstaller desktop/Super-AI-Trader.spec
#
set -e
cd "$(dirname "$0")/.."
python3 -m pip install --user pyinstaller || pip3 install pyinstaller
python3 -m PyInstaller --noconfirm desktop/Super-AI-Trader.spec \
  || pyinstaller --noconfirm desktop/Super-AI-Trader.spec
echo
echo "Done. Look in the dist/ folder for the app."
echo "Double-click it; the dashboard opens in your browser (127.0.0.1, local only)."

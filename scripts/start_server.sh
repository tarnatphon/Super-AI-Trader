#!/usr/bin/env bash
# Start the Super-AI-Trader local server for the Tauri native app.
# Resolves to the bundled binary when packaged, otherwise the Python module.
set -e
cd "$(dirname "$0")/.."

PORT=8787

# 1) Prefer a bundled PyInstaller binary (created by desktop/build_desktop.sh)
for candidate in "dist/superai" "dist/super-ai-trader" "./SuperAITrader"; do
  if [ -x "$candidate" ]; then
    exec "$candidate" web --port "$PORT"
  fi
done

# 2) Otherwise run from a local virtualenv if present (dev).
if [ -d ".venv" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
  exec python -m super_ai_trader web --port "$PORT"
fi

# 3) Fallback to system python3.
exec python3 -m super_ai_trader web --port "$PORT"

# Run Super-AI-Trader as a normal desktop app

You don't need to type terminal commands to use it. Pick the option that fits.

## Option A — Double-click launcher (simplest, recommended now)

The app already runs entirely in your browser while staying **100% local**.

1. Make sure Python 3 is installed (macOS/Linux: usually pre-installed;
   Windows: install from python.org and tick "Add Python to PATH").
2. **macOS:** double-click `desktop/Super-AI-Trader.command`
   **Windows:** double-click `desktop\Super-AI-Trader.bat`
   **Linux:** double-click `desktop/Super-AI-Trader.sh` (or run it in a terminal)
3. A small window opens (keep it open) and your browser automatically shows the
   dashboard at `http://127.0.0.1:8787`.
4. **Close that window** to stop the bot.

> First time on macOS, if macOS says it can't open the file: right-click → Open → Open.
> (Or in Terminal once: `chmod +x desktop/Super-AI-Trader.command`)

Everything stays on your computer; the app binds to `127.0.0.1` (not reachable
from the internet). Optional, for live exchange prices: `pip3 install ccxt`.

## Optional: own app window instead of a browser tab

If you want Super-AI-Trader to open in its **own window titled "Super-AI-Trader"**
(like a normal app, not a browser tab), install one optional package:

```
pip3 install pywebview       # Windows/macOS/Linux
```

Then the double-click launcher automatically opens the native window and stops
the app when you close it. If pywebview isn't installed, the launcher still
works — it just opens in your default browser.

## Option B — True standalone app (.app / .exe) with PyInstaller

Builds a normal double-click application with its own bundled Python, so end
users don't need Python installed.

- **macOS / Linux:** `bash desktop/build_desktop.sh`  → produces `dist/Super-AI-Trader.app`
- **Windows:** `pip install pyinstaller` then `pyinstaller desktop/Super-AI-Trader.spec`

Drag the built app to your Applications folder / Start menu and double-click it.
The dashboard still opens in your browser locally.

## What the desktop "app" really is

- A tiny **local server** on your machine + the browser **UI**. This is the same
  design used by many trading/crypto tools and means the same interface also
  works in the packaged Tauri/Rust app later (see LOCAL-FULLSTACK-PLAN.md).
- Keys/settings stay in local owner-only files (`~/.super-ai-trader`).
- No internet is used except to reach Binance/Gate.io when you connect/look at
  live prices; the AI brain is local.

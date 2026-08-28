"""`doctor` — one-page self-check before trading.

Verifies Python version, optional packages, internet/exchange reachability
(real Binance/Gate price via ccxt), and local folder permissions. Prints a
green/red report and exits non-zero on critical failures.
"""
from __future__ import annotations

import sys
import urllib.request


def _check(name: str, ok: bool, detail: str = "", critical: bool = False):
    mark = "PASS" if ok else ("FAIL" if critical else "WARN")
    line = f"[{mark}] {name}"
    if detail:
        line += f" — {detail}"
    print(line)
    return ok if ok else not critical


def run() -> int:
    fails = 0

    # Python
    v = sys.version_info
    ok = v >= (3, 9)
    print(f"      Super-AI-Trader doctor")
    if not _check(f"Python {v.major}.{v.minor}", ok,
                  "needs 3.9+" if not ok else "ok", critical=True):
        fails += 1

    # Optional packages
    for pkg, label, how in (
        ("ccxt", "ccxt (live Binance/Gate data)", "import ccxt"),
        ("webview", "pywebview (native window)", "import webview"),
        ("pystray", "pystray (menu-bar icon)", "import pystray"),
        ("PIL", "pillow (tray icon)", "import PIL"),
    ):
        try:
            __import__(pkg)
            _check(label, True, "installed")
        except Exception:
            _check(label, False, "not installed (optional; app still runs)", critical=False)

    # Network: can we reach an exchange and get a real price?
    try:
        import ccxt  # noqa: F401
        ex = __import__("ccxt").binance()
        try:
            t = ex.fetch_ticker("BTC/USDT")
            price = t.get("last")
            _check("Live Binance price", price and price > 0,
                   f"BTC/USDT = {price:,.2f}" if price else "no price", critical=False)
        except Exception as e:  # noqa: BLE001
            _check("Live Binance price", False, f"unreachable: {type(e).__name__} {e}")
    except Exception:
        _check("Live Binance price", False, "ccxt not installed")

    # Local storage / permissions
    import os, tempfile
    home = os.path.expanduser("~")
    satdir = os.path.join(home, ".super-ai-trader")
    try:
        os.makedirs(satdir, exist_ok=True)
        test = os.path.join(satdir, ".writetest")
        with open(test, "w") as f:
            f.write("ok")
        os.remove(test)
        _check("Local data folder", True, satdir)
    except Exception as e:  # noqa: BLE001
        _check("Local data folder", False, str(e), critical=True)
        fails += 1

    # App imports
    try:
        from .web.server import Handler  # noqa: F401
        _check("App modules", True, "import cleanly")
    except Exception as e:  # noqa: BLE001
        _check("App modules", False, str(e), critical=True)
        fails += 1

    print()
    if fails:
        print("Some critical checks failed — fix them before trading.")
        return 1
    print("All critical checks passed. Safe to open the app.")
    print("Start it with:  python start_app.py   (or double-click the launcher)")
    return 0


if __name__ == "__main__":
    sys.exit(run())

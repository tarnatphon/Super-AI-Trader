"""Double-click launcher: start the local app and open it in the browser.

This is what the desktop shortcuts call. It binds to 127.0.0.1 (this computer
only), picks a free port, opens the default browser, and stays open until you
close the window or press Ctrl+C.
"""
from __future__ import annotations

import socket
import threading
import time
import webbrowser


def find_free_port(preferred: int = 8787) -> int:
    for port in [preferred] + list(range(8788, 8820)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return preferred


def open_browser(url: str, delay: float = 1.2) -> None:
    def _open():
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception:
            pass
    threading.Thread(target=_open, daemon=True).start()


def launch(port: int | None = None, open_window: bool = True) -> None:
    from .web.server import run
    port = port or find_free_port()
    url = f"http://127.0.0.1:{port}"
    banner = (
        "\n==========================================================\n"
        "  Super-AI-Trader is starting...\n"
        f"  Open this address in your browser:  {url}\n"
        "  (It only runs on YOUR computer — not reachable from the internet.)\n"
        "\n"
        "  KEEP THIS WINDOW OPEN while you use the app.\n"
        "  Close this window or press Ctrl+C to STOP the bot.\n"
        "==========================================================\n"
    )
    print(banner)
    if open_window:
        open_browser(url)
    run(host="127.0.0.1", port=port)

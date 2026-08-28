"""Double-click launcher: start the local app and open it in the browser.

This is what the desktop shortcuts call. It binds to 127.0.0.1 (this computer
only), picks a free port, opens the default browser, and stays open until you
close the window or press Ctrl+C.
"""
from __future__ import annotations

import os
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


def _icon_path() -> str | None:
    import os
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name in ("desktop/app.ico", "desktop/app.png", "desktop/app.icns"):
        p = os.path.join(base, name)
        if os.path.exists(p):
            return p
    return None


def open_native_window(url: str) -> bool:
    """Open the app in its own native window (not a browser tab).

    Uses pywebview if installed. Returns True on success, False to fall back
    to the system browser. Install with: pip3 install pywebview
    """
    try:
        import webview  # type: ignore
    except Exception:
        return False
    try:
        icon = _icon_path()
        window = webview.create_window(
            "Super-AI-Trader",
            url,
            width=1024,
            height=820,
            min_size=(420, 640),
            icon=icon,
        )

        def _on_closed():
            import os
            os._exit(0)  # closing the window stops the whole app

        window.events.closed += _on_closed
        webview.start()
        return True
    except Exception:
        return False


def launch(port: int | None = None, open_window: bool = True, window: bool = True) -> None:
    from .web.server import make_server
    import threading

    port = port or find_free_port()
    url = f"http://127.0.0.1:{port}"
    server = make_server("127.0.0.1", port)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    banner = (
        "\n==========================================================\n"
        "  Super-AI-Trader is starting...\n"
        f"  Local address:  {url}\n"
        "  (Runs only on YOUR computer — not reachable from the internet.)\n"
        "\n"
        "  KEEP THIS WINDOW OPEN while you use the app.\n"
        "  Close the app window (or Ctrl+C here) to STOP.\n"
        "==========================================================\n"
    )
    print(banner)

    if open_window:
        used_native = False
        if window:
            open_browser = None  # don't open browser if we want a native window
            used_native = open_native_window(url)
        if not used_native:
            open_browser(url)
        if not used_native:
            # Staying browser-based: keep the process alive until Ctrl+C.
            try:
                while True:
                    time.sleep(3600)
            except KeyboardInterrupt:
                server.shutdown()
    else:
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            server.shutdown()

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


def launch(port: int | None = None, open_window: bool = True, window: bool = True,
           host: str | None = None, token: str | None = None) -> None:
    from .web.server import make_server
    import threading

    port = port or find_free_port()
    # Default to localhost. For phone remote control, pass host="100.x" (your
    # Tailscale address) + a token — NEVER 0.0.0.0/public.
    if host is None:
        host = "127.0.0.1"
    url = f"http://{host}:{port}"
    try:
        server = make_server(host, port)
    except OSError:
        # can't bind that address (e.g. no Tailscale) — fall back to localhost
        host = "127.0.0.1"
        url = f"http://{host}:{port}"
        server = make_server(host, port)
    if token:
        server.access_token = token  # enables token-gated remote access
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    remote = host not in ("127.0.0.1", "localhost")
    banner = (
        "\n==========================================================\n"
        "  Super-AI-Trader is starting...\n"
        f"  Address:  {url}\n"
        + ("  REMOTE mode — reachable on your private network (Tailscale).\n"
           "  Keep this on a password-protected / VPN-only address.\n"
           if remote else
           "  Local mode — only THIS computer can reach it.\n")
        + "\n  KEEP THIS WINDOW OPEN while you use the app.\n"
        "  Close the app window (or Ctrl+C here) to STOP.\n"
        "==========================================================\n"
    )
    print(banner)

    # Menu-bar/tray icon (optional; no-op if pystray isn't installed).
    try:
        from .tray import run_tray
        run_tray(url, on_quit=lambda: server.shutdown())
    except Exception:
        pass

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

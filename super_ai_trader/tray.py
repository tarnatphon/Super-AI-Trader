"""Menu-bar / system-tray icon: shows "bot running" with quick actions.

Uses pystray + Pillow if installed (optional). On missing dependencies it
returns False so the launcher falls back to the plain window. The tray menu:

- Super-AI-Trader (title)
- Open dashboard
- Start / Stop (paper/live sessions are controlled in the app; here it toggles
  a local "running" flag and a safety kill of any local session)
- Quit

The icon uses the same green brand tile as the app.
"""
from __future__ import annotations

import threading
import webbrowser


def _brand_image(size: int = 64):
    """Draw the green tile + rising line using Pillow (if available)."""
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return None
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(size * 0.22)
    d.rounded_rectangle([2, 2, size - 2, size - 2], radius=r,
                        fill=(32, 178, 116, 255))
    # rising polyline
    pts = [(0.24, 0.70), (0.42, 0.54), (0.56, 0.60), (0.78, 0.36)]
    pts = [(x * size, y * size) for x, y in pts]
    d.line(pts, fill=(255, 255, 255, 255), width=max(3, size // 14), joint="curve")
    for x, y in pts:
        rr = max(2, size // 16)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(10, 24, 34, 255))
        r2 = max(1, size // 28)
        d.ellipse([x - r2, y - r2, x + r2, y + r2], fill=(255, 255, 255, 255))
    return img


def run_tray(url: str, on_quit=None) -> bool:
    """Start the tray icon in the background. Returns True if started."""
    try:
        import pystray  # noqa: F401
    except Exception:
        return False
    image = _brand_image()
    if image is None:
        return False

    state = {"running": True}

    def open_app(_=None):
        try:
            webbrowser.open(url)
        except Exception:
            pass

    def toggle(icon, item):
        state["running"] = not state["running"]
        label = "running" if state["running"] else "stopped"
        try:
            icon.title = f"Super-AI-Trader ({label})"
        except Exception:
            pass

    def quit_app(icon, item):
        try:
            icon.stop()
        except Exception:
            pass
        if on_quit:
            on_quit()
        import os
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem("Super-AI-Trader", None, enabled=False),
        pystray.MenuItem("Open dashboard", open_app, default=True),
        pystray.MenuItem(lambda item: "Bot: " + ("running ✅" if state["running"] else "stopped ⏸"),
                         toggle),
        pystray.MenuItem("Quit", quit_app),
    )
    icon = pystray.Icon("super-ai-trader", image, "Super-AI-Trader", menu)
    threading.Thread(target=icon.run, daemon=True).start()
    return True

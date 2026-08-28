#!/usr/bin/env python3
"""Start Super-AI-Trader so your phone can reach it — via Tailscale only.

Your dashboard stays private: it does NOT open to the public internet. You put
the computer and phone on your own encrypted VPN (Tailscale, free and easy),
bind to the computer's Tailscale IP, and set an access token. Then open the
app from the phone's browser.

Setup (once):
  1. Install Tailscale on the computer AND the phone: https://tailscale.com
     (log in with the same account on both; everything is encrypted E2E.)
  2. On the computer:  python3 desktop/start_remote.py
     It prints your phone URL and an access token.
  3. On the phone's Tailscale app, tap the computer, or open the printed URL
     and enter the token when asked.

Nothing is exposed publicly, keys stay on the computer, and only a device on
your private Tailscale network with the token can view/control the app.
"""
from __future__ import annotations

import os
import secrets
import socket
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from super_ai_trader.launcher import launch


def tailscale_ip() -> str | None:
    """Return this machine's Tailscale 100.x address, or None."""
    # Prefer the Tailscale CLI if present.
    try:
        out = subprocess.check_output(["tailscale", "ip", "-4"], text=True, timeout=4)
        ip = out.strip().splitlines()[0].strip() if out.strip() else ""
        if ip.startswith("100."):
            return ip
    except Exception:
        pass
    # Fall back: scan local interfaces for a 100.x address.
    try:
        import uuid
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            ip = info[4][0]
            if ip.startswith("100."):
                return ip
    except Exception:
        pass
    return None


def main():
    port = int(os.environ.get("SAT_PORT", "8787"))
    ip = tailscale_ip()
    token = os.environ.get("SAT_TOKEN") or secrets.token_urlsafe(12)
    if not ip:
        print("\nTailscale doesn't appear to be running on this computer yet.")
        print("Install it from https://tailscale.com, log in, then run this again.")
        print("Meanwhile, the app will open on localhost only.\n")
        launch(port=port, open_window=True, window=False)
        return
    print("\n=== PHONE REMOTE CONTROL (Tailscale, private) ===")
    print(f"On your phone:  http://{ip}:{port}/?token={token}")
    print("Open that link once in the phone browser (the token is saved).")
    print("The app is NOT reachable from the public internet.")
    print("====================================================\n")
    launch(port=port, open_window=True, window=False, host=ip, token=token)


if __name__ == "__main__":
    main()

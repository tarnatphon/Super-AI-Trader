# Phone / tablet remote control — the safe way

The 24/7 bot runs on a computer (your Mac/PC/Linux box at home). Your phone is
the **remote control**: view price, start/stop the bot, watch P&L and the
smart-exit badges — from anywhere, **without opening your machine to the
public internet**.

## How it stays secure

- The dashboard is **never** published on a public port. It binds to localhost.
- You put the computer and phone on your **own encrypted VPN** using
  **Tailscale** (free, end-to-end encrypted; WireGuard underneath). The app then
  binds to the computer's private `100.x` Tailscale address.
- An **access token** is generated each run. A device must present it (the phone
  URL includes it once; it's stored locally on the phone). No token, no access.
- Exchange API keys **stay on the home computer** — the phone only sees the same
  dashboard; it never receives secrets (only a redacted fingerprint).

## One-time setup

1. Install **Tailscale** on the computer and on the phone: https://tailscale.com
   Log in with the same account on both devices.
2. On the computer (with this repo):
   ```bash
   python3 desktop/start_remote.py
   ```
   It prints a phone URL like:
   ```
   On your phone:  http://100.x.x.x:8787/?token=<long-token>
   ```
3. Open that link once in the phone's browser (on Tailscale). The token is saved
   on the phone; later visits don't need it.
4. Pin it to the phone home screen (Safari/Chrome "Add to Home Screen") so it
   behaves like an app.

> If Tailscale isn't running, the script safely falls back to localhost-only.

## What the phone can do

- View the live market chart + grid ladder and AI summaries.
- Start / stop paper (and, when armed with the confirmation wall, guarded live) sessions.
- See the regime badge (Grid ON/PAUSED) and smart-exit state (holding / locked).
- Read the plain-language AI replies.

## Notes / future

- The browser page already sends the token automatically on all API calls
  (`?token=` / `Authorization: Bearer`).
- A true native phone shell (Tauri/Rust or Flutter) that wraps this same local
  web UI is the eventual "app store" version — the web remote gives you the full
  experience today with zero store submissions.
- A menu-bar/tray icon for quick start/stop on the computer is on the roadmap.

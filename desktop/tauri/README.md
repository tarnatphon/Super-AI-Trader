# Super-AI-Trader — native Tauri shell (roadmap scaffold)

This is the scaffold for the fully-native desktop window (no browser chrome).
The actual app stays the same: a **local Python server** on `127.0.0.1:8787`.
Tauri just opens a real OS window that loads that local page.

## Why this setup
- The trading engine, AI, and security are already in Python and run locally.
- Tauri gives a lightweight native window; the HTML dashboard is reused.
- Same security model: binds to `127.0.0.1`, keys stay on the machine, phone
  access is via Tailscale + token.

## Prerequisites
1. Install Rust + Tauri CLI:
   - Rust: https://www.rust-lang.org/tools/install
   - Tauri CLI: `cargo install tauri-cli --version "^2"`
2. Have Python 3 available and the repo cloned.

## Run in dev
```bash
# from the repo root, the Tauri beforeDevCommand starts the python server
cd desktop/tauri/src-tauri
cargo tauri dev
```

## Build a native .app / .msi
```bash
cargo tauri build
```

## Notes / next steps
- In a bundled release, sidecar the Python interpreter + `start_app.py` (or a
  PyInstaller binary) so end users don't need Python. The double-click
  launchers in `../` already provide a working shipping path today.
- Icon should be placed at `desktop/tauri/icons/icon.png` (use
  `desktop/app.png`; Tauri can generate all sizes with `tauri icon`).
- This scaffold is intentionally minimal; the browser/native-window and
  PyInstaller paths remain the supported options until a Tauri build is
  produced on each platform.

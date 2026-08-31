# Building the native Tauri app (macOS / Windows / Linux)

This wraps the **existing local Python server** in a real native window
(no browser chrome). The app starts the server itself and loads
`http://127.0.0.1:8787`.

## One-time prerequisites

1. **Python 3.10+** and the project (see main README).
2. **Rust**: https://www.rust-lang.org/tools/install
   ```bash
   rustup default stable
   ```
3. **Tauri CLI** (v2):
   ```bash
   cargo install tauri-cli --version "^2" --locked
   # or use it via npx:  npm i -g @tauri-apps/cli@latest
   ```
4. macOS also needs Xcode Command Line Tools:
   ```bash
   xcode-select --install
   ```

## Option A — dev (uses your .venv / system Python)

From the repo root, make sure the server can start (the shell will run
`scripts/start_server.sh`, which prefers `.venv`):

```bash
cd desktop/tauri/src-tauri
cargo tauri dev
```

A native window opens showing the app. The Python server starts and stops
with the window.

## Option B — packaged build (recommended for distribution)

Build the Python side into a standalone binary first (so users don't need
Python), then build Tauri:

```bash
# 1. standalone Python bundle (from repo root)
bash desktop/build_desktop.sh
#    -> produces ./start_app or a dist/ binary the shell will prefer

# 2. native Tauri app
cd desktop/tauri/src-tauri
cargo tauri build
```

Outputs (in `src-tauri/target/release/bundle/`):
- macOS: `.app` / `.dmg`
- Windows: `.msi` / `.exe`
- Linux: `.AppImage` / `.deb`

The native binary shells out to `scripts/start_server.sh`, which prefers a
bundled binary in `dist/` and falls back to `.venv` / system Python.

## Notes

- Everything stays local; the window loads only `127.0.0.1`.
- Icons: Tauri can generate all sizes from one PNG:
  `cargo tauri icon ../../app.png` (writes to `src-tauri/icons/`).
- The tray/native-window extras are optional; the PyInstaller path
  (`desktop/build_desktop.sh`) remains the simplest shipping option.

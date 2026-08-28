# PyInstaller spec for a standalone Super-AI-Trader desktop app.
# Build:  pyinstaller desktop/Super-AI-Trader.spec   (see desktop/build_desktop.sh)
block_cipher = None

import os
_here = os.path.dirname(os.path.abspath(SPEC))
def _icon(name):
    p = os.path.join(_here, name)
    return p if os.path.exists(p) else None

# Bundle icon assets so the in-app/native window can find them at runtime too.
_datas = []
for f in ("app.png", "app.ico", "app.icns"):
    if _icon(f):
        _datas.append((_icon(f), "desktop"))

a = Analysis(
    ['start_app.py'],
    pathex=['.'],
    binaries=[],
    datas=_datas,
    hiddenimports=['pystray', 'PIL.Image', 'webview'],
    hookspath=[],
    runtime_hooks=[],
    # Standard library only by default; ccxt/yfinance are optional extras.
    excludes=['ccxt', 'yfinance', 'openai'],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='Super-AI-Trader',
    console=True,           # keep a small window: tells the user the app is running
    icon=_icon('app.ico'),   # native window / taskbar icon
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, name='Super-AI-Trader')

# macOS .app bundle (uses the .icns Dock/Finder icon); Windows exe uses app.ico.
app = BUNDLE(coll, name='Super-AI-Trader.app', icon=_icon('app.icns'),
             bundle_identifier='ai.supertrader.app')

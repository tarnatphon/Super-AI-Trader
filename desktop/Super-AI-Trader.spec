# PyInstaller spec for a standalone Super-AI-Trader desktop app.
# Build:  pyinstaller desktop/Super-AI-Trader.spec   (see desktop/build_desktop.sh)
block_cipher = None

a = Analysis(
    ['start_app.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    # Standard library only by default; ccxt/yfinance are optional extras.
    excludes=['ccxt', 'yfinance', 'openai'],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

import os
_icon = os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'app.ico')
_icon = _icon if os.path.exists(_icon) else None

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='Super-AI-Trader',
    console=True,           # keep a small window: tells the user the app is running
    icon=_icon,
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, name='Super-AI-Trader')

# macOS .app bundle
_icns = os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'app.icns')
_icns = _icns if os.path.exists(_icns) else _icon
app = BUNDLE(coll, name='Super-AI-Trader.app', icon=_icns, bundle_identifier='ai.supertrader.app')

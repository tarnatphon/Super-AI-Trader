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

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='Super-AI-Trader',
    console=True,           # keep a small window: tells the user the app is running
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, name='Super-AI-Trader')

# macOS .app bundle
app = BUNDLE(coll, name='Super-AI-Trader.app', icon=None, bundle_identifier='ai.supertrader.app')

# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: builds a single windowed Xynthra.exe with the art bundled.
# Build:  pyinstaller Xynthra.spec   ->   dist/Xynthra.exe

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('Graphics', 'Graphics')],   # bundle the sprite sheets
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', '_pytest'],     # don't ship the test runner
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Xynthra',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                      # windowed game (no console); set True to see logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

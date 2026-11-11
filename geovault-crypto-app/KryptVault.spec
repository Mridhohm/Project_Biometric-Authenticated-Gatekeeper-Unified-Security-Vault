# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata

datas = [('modules', 'modules'), ('storage', 'storage'), ('.streamlit', '.streamlit'), ('config.py', '.'), ('database.py', '.'), ('ui_theme.py', '.'), ('app.py', '.')]
datas += copy_metadata('streamlit')


a = Analysis(
    ['desktop_launcher.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['streamlit', 'webview', 'Crypto', 'PIL', 'psutil'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='KryptVault',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='KryptVault',
)

# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['seguridad_taller.py'],
    pathex=[],
    binaries=[],
    datas=[('panel_de_inicio_fondo.png', '.'), ('security_core.py', '.'), ('security.key', '.'), ('security_audit.log', '.')],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='seguridad_taller',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['fondo_taller.ico'],
)

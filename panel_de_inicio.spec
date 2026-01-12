# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['panel_de_inicio.py'],
    pathex=[],
    binaries=[],
    datas=[('python_ordenes_taller.py', '.'), ('ventas_taller.py', '.'), ('clientes_taller.py', '.'), ('proveedores_taller.py', '.'), ('modulo_inventario.py', '.'), ('seguridad_taller.py', '.'), ('pasarela_pagos.py', '.'), ('nomina_taller.py', '.'), ('compras_taller.py', '.'), ('cartera_taller.py', '.'), ('reportes_taller.py', '.'), ('config_taller.py', '.'), ('panel_de_inicio_fondo.png', '.'), ('licencias.json', '.'), ('security_core.py', '.')],
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
    name='panel_de_inicio',
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

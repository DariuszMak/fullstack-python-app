# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

block_cipher = None

# Workaround since __file__ is not defined in .spec context
base_path = Path(os.path.abspath(".")).resolve()

a = Analysis(
    [str(base_path / 'src' / 'main.py')],
    pathex=[str(base_path / 'src')],
    binaries=[],
    datas=[
        (
            str(base_path / 'src' / 'ui' / 'pyside_ui' / 'themes' / 'main_theme.qss'),
            'src/ui/pyside_ui/themes',
        ),
        (
            str(base_path / 'src' / 'backend' / 'openmeteo' / 'places' / 'places.json'),
            'src/backend/openmeteo/places',
        ),
        (
            str(base_path / 'src' / 'ui' / 'react_ui' / 'static'),
            'static',
        ),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt6",
        "PyQt6.sip",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GUI_client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon=str(base_path / 'src' / 'ui' / 'pyside_ui' / 'forms' / 'icons' / 'images' / 'program_icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
#    splash.binaries,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GUI_client_Linux'
)

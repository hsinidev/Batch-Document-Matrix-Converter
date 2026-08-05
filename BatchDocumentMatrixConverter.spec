# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

# Base directory path
spec_dir = os.path.dirname(os.path.abspath(SPEC))

# Collect CustomTkinter and TkinterDnD2 data files automatically
datas = [
    (os.path.join(spec_dir, 'assets'), 'assets'),
    (os.path.join(spec_dir, 'styles'), 'styles'),
    (os.path.join(spec_dir, 'bin', 'pandoc'), 'bin/pandoc')
]

hiddenimports = [
    'customtkinter',
    'tkinterdnd2',
    'pypandoc',
    'docx',
    'bs4',
    'lxml',
    'yaml',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'queue',
    'threading',
    'subprocess',
    'tempfile',
    'uuid',
    'shutil',
    'json'
]

a = Analysis(
    ['main.py'],
    pathex=[spec_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='BatchDocumentMatrixConverter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(spec_dir, 'assets', 'icon.ico'),
)

# -*- mode: python ; coding: utf-8 -*-
# Build with:  pyinstaller GrammarFixer.spec   ->  dist\GrammarFixer.exe

a = Analysis(
    ['grammarfixer/__main__.py'],
    pathex=['.'],
    hiddenimports=['pystray._win32', 'pynput.keyboard._win32', 'pynput.mouse._win32'],
    excludes=['numpy', 'pytest'],
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
    name='GrammarFixer',
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
)

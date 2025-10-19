# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['eir.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog'
    ],
    noarchive=False,
    optimize=2,
)

# Remove duplicate entries
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Eir',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='Eir.app',
    icon=None,
    bundle_identifier='com.eir.stpa-tool',
    info_plist={
        'CFBundleDisplayName': 'Eir STPA Tool',
        'CFBundleShortVersionString': '0.4.6',
        'CFBundleVersion': '0.4.6',
        'LSMinimumSystemVersion': '11.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Eir Document',
                'CFBundleTypeExtensions': ['json'],
                'CFBundleTypeRole': 'Editor',
                'LSHandlerRank': 'Owner'
            }
        ]
    }
)
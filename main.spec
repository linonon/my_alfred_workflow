# PyInstaller spec file for Alfred Workflow CLI
# Generated for bundling the CLI tool with all dependencies

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'src.base_tool',
        'src.tools.chrome_bookmarks_tool',
        'src.tools.code_with_zoxide_tool', 
        'src.tools.ssh_launcher_tool',
        'src.workflows.chrome_bookmakrs.chrome_bookmarks',
        'src.workflows.code_with_zoxide.code_with_zoxide',
        'src.workflows.ssh_launcher.ssh_launcher',
        'pypinyin',
    ],
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
    name='alfred-cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
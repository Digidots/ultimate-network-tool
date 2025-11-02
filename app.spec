# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Collect all data files
datas = [
    ('templates', 'templates'),
    ('static', 'static'),
]

# Collect hidden imports
hiddenimports = [
    'flask',
    'flask_socketio',
    'socketio',
    'engineio',
    'scapy',
    'scapy.all',
    'scapy.layers',
    'scapy.layers.l2',
    'scapy.layers.inet',
    'scapy.layers.dhcp',
    'scapy.sendrecv',
    'scapy.arch',
    'scapy.arch.windows',
    'logging',
    'logging.handlers',
    'ctypes',
    'subprocess',
    'threading',
    'asyncio',
    'ipaddress',
    'struct',
    'socket',
    'time',
    'datetime',
    're',
]

a = Analysis(
    ['app.py'],
    pathex=[],
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
    [],
    exclude_binaries=True,
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep console for logging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,  # Request admin privileges
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='app',
)

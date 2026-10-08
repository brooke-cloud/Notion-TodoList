# -*- mode: python ; coding: utf-8 -*-
datas = [("qml", "qml"), ("design/bg.jpg", "design"), ("assets/ui/app.ico", "assets/ui")]

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest", "matplotlib", "numpy", "IPython",
        "jedi", "nbformat", "zmq", "PIL", "pygame", "pandas", "scipy",
    ],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Notion TodoList",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon="assets/ui/app.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Notion TodoList V4",
)

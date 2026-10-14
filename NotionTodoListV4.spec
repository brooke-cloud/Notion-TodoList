# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files


datas = [
    ("qml", "qml"),
    ("design/bg.jpg", "design"),
    ("assets/ui/app.ico", "assets/ui"),
] + collect_data_files("certifi")

hiddenimports = [
    "certifi",
    "certifi.core",
    "requests",
    "requests.api",
    "requests.sessions",
    "urllib3",
    "idna",
    "charset_normalizer",
]

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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

# Qt 6 on Windows resolves the operating-system ICU.  A developer shell may
# put unrelated tools (for example Poppler) on PATH; PyInstaller can otherwise
# mistake those tools' versioned ICU binaries for application dependencies.
_foreign_icu_names = {"icuuc.dll", "icudt78.dll"}
a.binaries = [
    entry for entry in a.binaries
    if entry[0].lower() not in _foreign_icu_names
]
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

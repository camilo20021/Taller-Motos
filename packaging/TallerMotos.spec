# -*- mode: python ; coding: utf-8 -*-
#
# Build con: pyinstaller packaging/TallerMotos.spec --distpath dist --workpath build
# (ejecutar desde la raíz del proyecto para que las rutas relativas resuelvan bien)
#
# Genera dist/TallerMotos/TallerMotos.exe (modo onedir: arranca más rápido y
# da menos falsos positivos de antivirus que --onefile).

import os

RAIZ = os.path.abspath(os.path.join(os.path.dirname(SPEC), ".."))
ICONO = os.path.join(RAIZ, "packaging", "assets", "app.ico")
if not os.path.exists(ICONO):
    ICONO = None  # Agrega packaging/assets/app.ico con tu logo antes de vender.

a = Analysis(
    [os.path.join(RAIZ, "desktop_entry.py")],
    pathex=[RAIZ],
    binaries=[],
    datas=[
        (os.path.join(RAIZ, "python", "templates"), os.path.join("python", "templates")),
        (os.path.join(RAIZ, "python", "static"), os.path.join("python", "static")),
        (os.path.join(RAIZ, "desktop", "assets"), os.path.join("desktop", "assets")),
    ],
    hiddenimports=[
        "sqlite3",
        "flask_sqlalchemy",
        "flask_login",
        "cryptography",
        "webview.platforms.edgechromium",
        "waitress",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TallerMotos",
    debug=False,
    strip=False,
    # UPX desactivado: puede corromper sqlite3.pyd / _sqlite3 en Windows.
    upx=False,
    console=False,
    icon=ICONO,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="TallerMotos",
)

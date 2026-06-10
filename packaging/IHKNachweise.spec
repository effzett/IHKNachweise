# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller-Spec für die IHK-Ausbildungsnachweise-App.

Bündelt die Anwendung samt aller Bibliotheken (PySide6/QtPdf, llama-cpp-python).
Aufruf aus dem Projektwurzelverzeichnis:

    pyinstaller packaging/IHKNachweise.spec --noconfirm

Ergebnis (onedir) liegt unter ``dist/IHKNachweise/``. Die plattformspezifischen
Skripte (build_macos.sh / build_windows.bat) verpacken das Ergebnis als
.dmg bzw. .exe-Installer.
"""

import os
import sys

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

block_cipher = None

# Pfade robust relativ zur Spec-Datei auflösen (SPECPATH wird von PyInstaller
# in den Namensraum injiziert). So funktioniert der Build unabhängig davon, aus
# welchem Verzeichnis pyinstaller aufgerufen wird.
PROJECT_ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir))

# llama-cpp-python liefert eine native Shared Library mit, die mitgenommen
# werden muss, sonst startet die LLM-Komponente im Paket nicht.
binaries = collect_dynamic_libs("llama_cpp")
hiddenimports = collect_submodules("llama_cpp")

a = Analysis(
    [os.path.join(PROJECT_ROOT, "main.py")],
    pathex=[PROJECT_ROOT],
    binaries=binaries,
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Plattform-Icons (siehe packaging/make_icons.py). Fehlt eine Datei, baut
# PyInstaller ohne Icon weiter, statt abzubrechen.
ICON_ICNS = os.path.join(SPECPATH, "IHKNachweise.icns")
ICON_ICO = os.path.join(SPECPATH, "IHKNachweise.ico")
_exe_icon = ICON_ICO if sys.platform.startswith("win") else ICON_ICNS
EXE_ICON = _exe_icon if os.path.exists(_exe_icon) else None
BUNDLE_ICON = ICON_ICNS if os.path.exists(ICON_ICNS) else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="IHKNachweise",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # GUI-Anwendung, keine Konsole
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=EXE_ICON,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="IHKNachweise",
)

# macOS: zusätzlich ein .app-Bundle erzeugen
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="IHKNachweise.app",
        icon=BUNDLE_ICON,
        bundle_identifier="de.ihk.nachweise",
        info_plist={
            "CFBundleDisplayName": "IHK-Ausbildungsnachweise",
            "CFBundleShortVersionString": "0.1.0",
            "NSHighResolutionCapable": True,
        },
    )

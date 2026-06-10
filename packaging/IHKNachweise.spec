# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller-Spec für die IHK-Ausbildungsnachweise-App.

Bündelt die Anwendung samt aller Bibliotheken (PySide6/QtPdf, llama-cpp-python).
Aufruf aus dem Projektwurzelverzeichnis:

    pyinstaller packaging/IHKNachweise.spec --noconfirm

Ergebnis (onedir) liegt unter ``dist/IHKNachweise/``. Die plattformspezifischen
Skripte (build_macos.sh / build_windows.bat) verpacken das Ergebnis als
.dmg bzw. .exe-Installer.
"""

import sys

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

block_cipher = None

# llama-cpp-python liefert eine native Shared Library mit, die mitgenommen
# werden muss, sonst startet die LLM-Komponente im Paket nicht.
binaries = collect_dynamic_libs("llama_cpp")
hiddenimports = collect_submodules("llama_cpp")

a = Analysis(
    ["../main.py"],
    pathex=["."],
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
        icon=None,
        bundle_identifier="de.ihk.nachweise",
        info_plist={
            "CFBundleDisplayName": "IHK-Ausbildungsnachweise",
            "CFBundleShortVersionString": "0.1.0",
            "NSHighResolutionCapable": True,
        },
    )

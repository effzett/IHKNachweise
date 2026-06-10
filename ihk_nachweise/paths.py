"""Zentrale Verwaltung aller Verzeichnispfade — **portabler** Betrieb.

Die Anwendung ist bewusst portabel ausgelegt: Sie legt alle Daten (Modell,
Konfiguration, erzeugte Nachweise) in einem Ordner ``Daten`` **neben der
Anwendung** ab. Dadurch sind keine Administratorrechte nötig und es wird nichts
in geschützte System- oder Programmordner geschrieben — die App kann in einem
beliebigen, vom Nutzer beschreibbaren Ordner liegen (Home, Netzlaufwerk, USB).

Override-Möglichkeiten über Umgebungsvariablen:
- ``IHK_DATA_DIR``   – kompletter Datenordner an beliebigem Ort
- ``IHK_MODELS_DIR`` – nur das Modell-Verzeichnis
- ``IHK_CONFIG_DIR`` – nur das Konfigurations-Verzeichnis
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ENV_DATA_DIR = "IHK_DATA_DIR"
ENV_MODELS_DIR = "IHK_MODELS_DIR"
ENV_CONFIG_DIR = "IHK_CONFIG_DIR"

#: Name des Datenordners neben der Anwendung.
DATA_SUBDIR = "Daten"


def _app_base_dir() -> Path:
    """Verzeichnis, neben dem die Daten abgelegt werden.

    - Gepackt (PyInstaller): der Ordner der ausführbaren Datei. Auf macOS wird
      bewusst **nicht** ins ``.app``-Bundle geschrieben (das bräche die
      Signatur), sondern in den Ordner, der das ``.app`` enthält.
    - Aus dem Quellcode (Entwicklung): die Projektwurzel.
    """
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve()
        if sys.platform == "darwin":
            for parent in exe.parents:
                if parent.suffix == ".app":
                    return parent.parent
        return exe.parent
    return Path(__file__).resolve().parent.parent


def data_root() -> Path:
    """Wurzelordner aller Daten (enthält ``modelle/``, ``Nachweise/``, ``config.json``)."""
    override = os.environ.get(ENV_DATA_DIR)
    root = Path(override).expanduser() if override else _app_base_dir() / DATA_SUBDIR
    root.mkdir(parents=True, exist_ok=True)
    return root


def config_dir() -> Path:
    """Verzeichnis für die Konfigurationsdatei."""
    override = os.environ.get(ENV_CONFIG_DIR)
    path = Path(override).expanduser() if override else data_root()
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_file() -> Path:
    """Pfad der zentralen Konfigurationsdatei."""
    return config_dir() / "config.json"


def models_dir() -> Path:
    """Verzeichnis, in dem heruntergeladene GGUF-Modelle abgelegt werden."""
    override = os.environ.get(ENV_MODELS_DIR)
    path = Path(override).expanduser() if override else data_root() / "modelle"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_output_dir() -> Path:
    """Default-Zielverzeichnis für erzeugte PDFs/Rohdaten."""
    return data_root() / "Nachweise"

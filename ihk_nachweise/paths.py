"""Zentrale Verwaltung aller Verzeichnispfade (Config, Modelle, Default-Output).

Nutzt Qt-StandardPaths, damit die App ohne zusätzliche Abhängigkeit auf jedem
Betriebssystem die jeweils üblichen Speicherorte verwendet.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QStandardPaths

# Umgebungsvariablen zum Umleiten der Speicherorte (z. B. für eine portable
# Installation, bei der alles im Programmverzeichnis liegen soll).
ENV_MODELS_DIR = "IHK_MODELS_DIR"
ENV_CONFIG_DIR = "IHK_CONFIG_DIR"


def config_dir() -> Path:
    """Verzeichnis für die Konfigurationsdatei (z. B. ~/.config/IHKNachweise)."""
    override = os.environ.get(ENV_CONFIG_DIR)
    if override:
        path = Path(override).expanduser()
    else:
        base = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppConfigLocation
        )
        path = Path(base)
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_file() -> Path:
    """Pfad der zentralen Konfigurationsdatei."""
    return config_dir() / "config.json"


def models_dir() -> Path:
    """Verzeichnis, in dem heruntergeladene GGUF-Modelle abgelegt werden.

    Lässt sich über die Umgebungsvariable ``IHK_MODELS_DIR`` umleiten (z. B. ins
    Programmverzeichnis für eine portable Installation).
    """
    override = os.environ.get(ENV_MODELS_DIR)
    if override:
        path = Path(override).expanduser()
    else:
        base = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation
        )
        path = Path(base) / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_output_dir() -> Path:
    """Default-Zielverzeichnis für erzeugte PDFs/Rohdaten (Dokumente/Ausbildungsnachweise)."""
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    path = Path(base) / "Ausbildungsnachweise"
    return path

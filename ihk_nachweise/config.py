"""Konfigurationsverwaltung: Laden, Speichern, Löschen der Metadaten/Einstellungen.

Die Konfiguration wird als JSON in einer plattformüblichen Datei abgelegt
(siehe :mod:`ihk_nachweise.paths`). Neben zuletzt genutzten Werten enthält sie
die persistenten Listen für die editierbaren Dropdowns (Arbeitsbereiche, Betreuer).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import List

from . import paths


DEFAULT_FILENAME_PATTERN = "{name}_KW{kw}_{von}_{bis}"


@dataclass
class AppConfig:
    """Persistente Anwendungseinstellungen."""

    letzter_name: str = ""
    letztes_modell: str = ""
    output_dir: str = ""
    dateinamen_muster: str = DEFAULT_FILENAME_PATTERN
    arbeitsbereiche: List[str] = field(default_factory=list)
    betreuer: List[str] = field(default_factory=list)
    letzter_arbeitsbereich: str = ""
    letzter_betreuer: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "AppConfig":
        known = {f for f in cls().__dict__}
        return cls(**{k: v for k, v in d.items() if k in known})


class ConfigManager:
    """Lädt/speichert/löscht die :class:`AppConfig` und verwaltet die Listen."""

    def __init__(self) -> None:
        self.config = AppConfig()

    # ---- CRUD -------------------------------------------------------------
    def load(self) -> AppConfig:
        path = paths.config_file()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self.config = AppConfig.from_dict(data)
            except (json.JSONDecodeError, OSError, TypeError):
                # Defekte Datei: mit Defaults weiterarbeiten, nicht abstürzen.
                self.config = AppConfig()
        if not self.config.output_dir:
            self.config.output_dir = str(paths.default_output_dir())
        return self.config

    def save(self) -> None:
        path = paths.config_file()
        path.write_text(
            json.dumps(self.config.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def delete(self) -> AppConfig:
        """Setzt die Konfiguration zurück und entfernt die Datei."""
        path = paths.config_file()
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass
        self.config = AppConfig()
        self.config.output_dir = str(paths.default_output_dir())
        return self.config

    # ---- Listenpflege für editierbare Dropdowns ---------------------------
    def add_arbeitsbereich(self, value: str) -> None:
        self._add_unique(self.config.arbeitsbereiche, value)

    def add_betreuer(self, value: str) -> None:
        self._add_unique(self.config.betreuer, value)

    @staticmethod
    def _add_unique(target: List[str], value: str) -> None:
        value = (value or "").strip()
        if value and value not in target:
            target.append(value)
            target.sort(key=str.casefold)

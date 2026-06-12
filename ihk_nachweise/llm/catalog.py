"""Katalog der auswählbaren lokalen LLMs (GGUF-Modelle von Hugging Face).

Jeder Eintrag verweist auf ein HF-Repository und eine konkrete GGUF-Datei. Die
Modelle werden erst beim ersten Verwenden heruntergeladen (siehe
:mod:`ihk_nachweise.llm.downloader`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .. import paths


@dataclass(frozen=True)
class ModelInfo:
    """Beschreibt ein herunterladbares GGUF-Modell."""

    id: str            # eindeutige interne Kennung
    label: str         # Anzeigename im Dropdown
    repo_id: str       # Hugging-Face-Repository
    filename: str      # GGUF-Dateiname im Repo
    size_mb: int       # ungefähre Downloadgröße in MB

    @property
    def size_label(self) -> str:
        if self.size_mb >= 1024:
            return f"~{self.size_mb / 1024:.1f} GB"
        return f"~{self.size_mb} MB"

    @property
    def display(self) -> str:
        return f"{self.label}  ({self.size_label})"

    def local_path(self) -> Path:
        """Lokaler Zielpfad der GGUF-Datei im Modell-Verzeichnis."""
        return paths.models_dir() / self.filename

    def is_downloaded(self) -> bool:
        path = self.local_path()
        return path.exists() and path.stat().st_size > 0


# Reihenfolge = Reihenfolge im Dropdown. Erstes Element ist der Default.
CATALOG: List[ModelInfo] = [
    ModelInfo(
        id="qwen2.5-3b-instruct-q4",
        label="Qwen2.5 3B Instruct (gut für Deutsch)",
        repo_id="Qwen/Qwen2.5-3B-Instruct-GGUF",
        filename="qwen2.5-3b-instruct-q4_k_m.gguf",
        size_mb=1930,
    ),
    ModelInfo(
        id="llama-3.2-3b-instruct-q4",
        label="Llama 3.2 3B Instruct",
        repo_id="bartowski/Llama-3.2-3B-Instruct-GGUF",
        filename="Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        size_mb=2020,
    ),
    ModelInfo(
        id="qwen2.5-7b-instruct-q4",
        label="Qwen2.5 7B Instruct (größer, präziser)",
        # bartowski liefert eine einzelne GGUF-Datei; das offizielle
        # Qwen-Repo splittet Q4_K_M in mehrere Teile, was der Single-File-
        # Downloader nicht laden kann.
        repo_id="bartowski/Qwen2.5-7B-Instruct-GGUF",
        filename="Qwen2.5-7B-Instruct-Q4_K_M.gguf",
        size_mb=4680,
    ),
    ModelInfo(
        id="qwen2.5-1.5b-instruct-q4",
        label="Qwen2.5 1.5B Instruct (klein, schnell)",
        repo_id="Qwen/Qwen2.5-1.5B-Instruct-GGUF",
        filename="qwen2.5-1.5b-instruct-q4_k_m.gguf",
        size_mb=1070,
    ),
]


def default_model() -> ModelInfo:
    return CATALOG[0]


def by_id(model_id: str) -> Optional[ModelInfo]:
    for m in CATALOG:
        if m.id == model_id:
            return m
    return None


def get_or_default(model_id: str) -> ModelInfo:
    return by_id(model_id) or default_model()

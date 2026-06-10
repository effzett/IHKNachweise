"""Strukturierung der Azubi-Stichworte mit einer lokalen LLM (llama-cpp).

Die Generierung läuft in einem :class:`QThread`. Die geladene ``Llama``-Instanz
wird prozessweit zwischengespeichert, damit wiederholte Erzeugungen mit demselben
Modell nicht erneut von der Platte laden müssen.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal

from .catalog import ModelInfo

# Cache: (model_path) -> Llama-Instanz
_LLAMA_CACHE: dict[str, object] = {}

SYSTEM_PROMPT = (
    "Du bist ein Assistent, der wöchentliche Ausbildungsnachweise für "
    "Fachinformatiker-Azubis aufbereitet. Du erhältst lose deutsche Stichworte "
    "und Tätigkeiten und strukturierst sie zu einem sauberen, sachlichen "
    "Wochennachweis.\n"
    "Regeln:\n"
    "- Antworte ausschließlich auf Deutsch.\n"
    "- Bilde WENIGE thematische Oberkategorien (in der Regel 2 bis 4) und "
    "fasse inhaltlich verwandte Tätigkeiten unter einer gemeinsamen Überschrift "
    "zusammen. Mache NICHT aus jedem einzelnen Stichwort eine eigene Überschrift.\n"
    "- Wähle für jede Kategorie eine kurze, prägnante Themen-Überschrift "
    "(z. B. 'Softwareentwicklung', 'Wartung & Administration', "
    "'Schulung & Weiterbildung') – nicht den Wortlaut einer einzelnen Tätigkeit.\n"
    "- Schreibe jede Überschrift als eigene Zeile mit vorangestelltem '## '.\n"
    "- Liste die Tätigkeiten je Abschnitt als Stichpunkte mit vorangestelltem "
    "'- ' auf, in vollständigen, fachlich präzisen Formulierungen.\n"
    "- Wiederhole die Überschrift NICHT als ersten Stichpunkt.\n"
    "- Übernimm ALLE genannten Tätigkeiten; lasse keine weg und führe jede "
    "genau einmal im passenden Abschnitt auf.\n"
    "- Erfinde keine Tätigkeiten dazu; fasse nur das Vorgegebene sinnvoll "
    "zusammen, formuliere es aus und kategorisiere es.\n"
    "- Keine Einleitung, kein Schlusswort, keine Meta-Kommentare."
)


def _format_user(stichworte: str) -> str:
    return (
        "Hier sind die Stichworte/Tätigkeiten der Woche. Bitte strukturiere und "
        "kategorisiere sie wie beschrieben:\n\n" + stichworte.strip()
    )


class GenerateWorker(QThread):
    """Erzeugt aus den Stichworten einen strukturierten Nachweistext."""

    status = Signal(str)
    finished_ok = Signal(str)   # strukturierter Text
    failed = Signal(str)

    def __init__(
        self,
        model: ModelInfo,
        stichworte: str,
        force: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._model = model
        self._stichworte = stichworte
        self._force = force

    def run(self) -> None:  # noqa: D401 - QThread-Einstiegspunkt
        try:
            llama = self._get_llama()
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"Modell konnte nicht geladen werden: {exc}")
            return

        try:
            self.status.emit("Strukturiere Eingaben …")
            # Bei erzwungener Neugenerierung mehr Variation zulassen.
            temperature = 0.9 if self._force else 0.4
            seed = random.randint(1, 2**31 - 1) if self._force else 42
            result = llama.create_chat_completion(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _format_user(self._stichworte)},
                ],
                temperature=temperature,
                max_tokens=1536,
                seed=seed,
            )
            text = result["choices"][0]["message"]["content"].strip()
            if not text:
                self.failed.emit("Die LLM hat keinen Text erzeugt.")
                return
            self.finished_ok.emit(text)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"Generierung fehlgeschlagen: {exc}")

    def _get_llama(self):
        path = str(self._model.local_path())
        if path in _LLAMA_CACHE:
            return _LLAMA_CACHE[path]
        if not Path(path).exists():
            raise FileNotFoundError(path)
        self.status.emit("Lade Modell in den Speicher …")
        from llama_cpp import Llama

        llama = Llama(
            model_path=path,
            n_ctx=4096,
            n_threads=None,   # automatisch
            n_gpu_layers=-1,  # so viel wie möglich auf die GPU (Metal); sonst CPU
            verbose=False,
        )
        _LLAMA_CACHE[path] = llama
        return llama


def is_backend_available() -> bool:
    """True, wenn ``llama-cpp-python`` importierbar ist."""
    try:
        import llama_cpp  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False

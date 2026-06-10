"""Hintergrund-Download von GGUF-Modellen mit Fortschrittsanzeige.

Der Download läuft in einem eigenen :class:`QThread`, damit die Oberfläche
bedienbar bleibt. Es wird direkt von der Hugging-Face-``resolve``-URL gestreamt,
sodass sich der Fortschritt zuverlässig in Prozent melden lässt.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from .catalog import ModelInfo

_HF_RESOLVE = "https://huggingface.co/{repo_id}/resolve/main/{filename}"
_CHUNK = 1 << 20  # 1 MiB


class DownloadWorker(QThread):
    """Lädt die GGUF-Datei eines Modells herunter."""

    progress = Signal(int)            # Prozent 0..100
    status = Signal(str)              # Statustext
    finished_ok = Signal(str)         # lokaler Pfad bei Erfolg
    failed = Signal(str)              # Fehlermeldung

    def __init__(self, model: ModelInfo, parent=None) -> None:
        super().__init__(parent)
        self._model = model
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:  # noqa: D401 - QThread-Einstiegspunkt
        model = self._model
        target = model.local_path()
        if model.is_downloaded():
            self.progress.emit(100)
            self.finished_ok.emit(str(target))
            return

        url = _HF_RESOLVE.format(repo_id=model.repo_id, filename=model.filename)
        part = target.with_suffix(target.suffix + ".part")
        try:
            import requests

            self.status.emit(f"Lade {model.label} …")
            with requests.get(url, stream=True, timeout=60) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("Content-Length", 0))
                done = 0
                last_pct = -1
                with open(part, "wb") as fh:
                    for chunk in resp.iter_content(chunk_size=_CHUNK):
                        if self._cancel:
                            self.status.emit("Download abgebrochen.")
                            self._cleanup(part)
                            return
                        if not chunk:
                            continue
                        fh.write(chunk)
                        done += len(chunk)
                        if total > 0:
                            pct = int(done * 100 / total)
                            if pct != last_pct:
                                last_pct = pct
                                self.progress.emit(pct)
            part.replace(target)
            self.progress.emit(100)
            self.status.emit(f"{model.label} bereit.")
            self.finished_ok.emit(str(target))
        except Exception as exc:  # noqa: BLE001 - Fehler an UI weiterreichen
            self._cleanup(part)
            self.failed.emit(f"Download fehlgeschlagen: {exc}")

    @staticmethod
    def _cleanup(part: Path) -> None:
        try:
            if part.exists():
                part.unlink()
        except OSError:
            pass

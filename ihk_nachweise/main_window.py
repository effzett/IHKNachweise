"""Hauptfenster: verbindet Metadaten, Eingabe, LLM, PDF-Erzeugung und Anzeige."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from . import APP_DISPLAY_NAME
from .config import ConfigManager
from .llm import catalog, generator
from .llm.downloader import DownloadWorker
from .llm.generator import GenerateWorker
from .models import Metadata, Rohdaten
from .pdf import builder
from .storage import rawdata
from .widgets.input_panel import InputPanel
from .widgets.metadata_bar import MetadataBar
from .widgets.pdf_viewer import PdfViewer


_INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _sanitize(name: str) -> str:
    name = _INVALID.sub("_", name).strip().strip(".")
    name = re.sub(r"\s+", "_", name)
    return name or "Nachweis"


def build_basename(pattern: str, meta: Metadata) -> str:
    """Erzeugt den Dateinamen (ohne Endung) aus Muster und Metadaten."""
    values = {
        "name": meta.name or "Nachweis",
        "kw": f"{meta.kw:02d}",
        "von": meta.datum_von.isoformat(),
        "bis": meta.datum_bis.isoformat(),
        "arbeitsbereich": meta.arbeitsbereich,
        "betreuer": meta.betreuer,
    }
    try:
        raw = pattern.format(**values)
    except (KeyError, IndexError, ValueError):
        raw = "{name}_KW{kw}_{von}_{bis}".format(**values)
    return _sanitize(raw)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_DISPLAY_NAME)
        self.resize(1280, 800)

        self.config_manager = ConfigManager()
        self.config = self.config_manager.load()

        # Worker-Referenzen (verhindert vorzeitiges Garbage-Collecting)
        self._dl_worker: DownloadWorker | None = None
        self._gen_worker: GenerateWorker | None = None
        self._last_pdf_path: str | None = None

        self._build_ui()
        self._build_menu()
        self.metadata_bar.load_from_config(self.config)
        self._update_model_status()

    # ---- Aufbau ----------------------------------------------------------
    def _build_ui(self) -> None:
        self.metadata_bar = MetadataBar()
        self.input_panel = InputPanel()
        self.pdf_viewer = PdfViewer()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.input_panel)
        splitter.addWidget(self.pdf_viewer)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([560, 720])

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.metadata_bar)
        layout.addWidget(splitter, 1)
        self.setCentralWidget(central)

        self.statusBar().showMessage("Bereit.")

        self.input_panel.erzeugeClicked.connect(lambda: self._start_generation(force=False))
        self.input_panel.neuClicked.connect(lambda: self._start_generation(force=True))
        self.input_panel.ladenClicked.connect(self._load_rawdata)
        self.metadata_bar.modelChanged.connect(self._update_model_status)

    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu("&Datei")

        act_save = QAction("Einstellungen &speichern", self)
        act_save.triggered.connect(self._save_settings)
        menu.addAction(act_save)

        act_reset = QAction("Einstellungen &zurücksetzen …", self)
        act_reset.triggered.connect(self._reset_settings)
        menu.addAction(act_reset)

        menu.addSeparator()
        act_load = QAction("Rohdaten &laden …", self)
        act_load.triggered.connect(self._load_rawdata)
        menu.addAction(act_load)

        menu.addSeparator()
        act_quit = QAction("&Beenden", self)
        act_quit.triggered.connect(self.close)
        menu.addAction(act_quit)

    # ---- Einstellungen (Config CRUD) -------------------------------------
    def _save_settings(self) -> None:
        self.metadata_bar.apply_to_config(self.config)
        self.config_manager.save()
        self.statusBar().showMessage("Einstellungen gespeichert.", 4000)

    def _reset_settings(self) -> None:
        reply = QMessageBox.question(
            self, "Einstellungen zurücksetzen",
            "Wirklich alle gespeicherten Einstellungen (Name, Listen, Pfade, "
            "Muster) löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.config = self.config_manager.delete()
            self.metadata_bar.load_from_config(self.config)
            self.statusBar().showMessage("Einstellungen zurückgesetzt.", 4000)

    # ---- Modell-Status ---------------------------------------------------
    def _update_model_status(self) -> None:
        model = self.metadata_bar.current_model()
        if model.is_downloaded():
            self.metadata_bar.set_model_status("bereit (heruntergeladen)")
        else:
            self.metadata_bar.set_model_status(
                f"nicht geladen – wird bei Bedarf geladen ({model.size_label})"
            )

    # ---- Erzeugen --------------------------------------------------------
    def _start_generation(self, force: bool) -> None:
        if self._gen_worker is not None or self._dl_worker is not None:
            return  # läuft bereits

        stichworte = self.input_panel.stichworte().strip()
        if not stichworte:
            QMessageBox.information(
                self, "Keine Eingabe",
                "Bitte zuerst Stichworte/Tätigkeiten eintragen.",
            )
            return
        if not self.metadata_bar.output_dir():
            QMessageBox.information(
                self, "Kein Speicherort",
                "Bitte oben einen Speicherort für die PDFs festlegen.",
            )
            return
        if not generator.is_backend_available():
            QMessageBox.critical(
                self, "LLM nicht verfügbar",
                "Die LLM-Komponente (llama-cpp-python) ist nicht verfügbar.",
            )
            return

        # Einstellungen/Listen persistieren
        self._save_settings()

        model = self.metadata_bar.current_model()
        self.input_panel.set_busy(True)

        if not model.is_downloaded():
            self._start_download(model, force)
        else:
            self._run_generation(force)

    def _start_download(self, model, force: bool) -> None:
        self.input_panel.set_status(f"Lade Modell »{model.label}« herunter …")
        self.input_panel.set_progress(0)
        self.metadata_bar.set_model_status("lädt …")

        worker = DownloadWorker(model)
        self._dl_worker = worker
        worker.progress.connect(self.input_panel.set_progress)
        worker.status.connect(self.input_panel.set_status)
        worker.failed.connect(self._on_worker_failed)
        worker.finished_ok.connect(lambda _path: self._on_download_done(force))
        worker.finished.connect(lambda: self._clear_worker("dl"))
        worker.start()

    def _on_download_done(self, force: bool) -> None:
        self._update_model_status()
        self._run_generation(force)

    def _run_generation(self, force: bool) -> None:
        stichworte = self.input_panel.stichworte().strip()
        model = self.metadata_bar.current_model()
        self.input_panel.set_progress(-1)  # unbestimmt
        self.input_panel.set_status(
            "Neu generieren …" if force else "Strukturiere Eingaben mit der LLM …"
        )

        worker = GenerateWorker(model, stichworte, force=force)
        self._gen_worker = worker
        worker.status.connect(self.input_panel.set_status)
        worker.failed.connect(self._on_worker_failed)
        worker.finished_ok.connect(self._on_generation_done)
        worker.finished.connect(lambda: self._clear_worker("gen"))
        worker.start()

    def _on_generation_done(self, structured_text: str) -> None:
        try:
            self._write_outputs(structured_text)
        except Exception as exc:  # noqa: BLE001
            self._on_worker_failed(f"Speichern/PDF fehlgeschlagen: {exc}")
            return
        self.input_panel.set_busy(False)
        self.input_panel.hide_progress()
        self.input_panel.set_status("Fertig.")
        self.statusBar().showMessage(
            f"PDF erzeugt: {self._last_pdf_path}", 8000
        )

    def _write_outputs(self, structured_text: str) -> None:
        meta = self.metadata_bar.current_metadata()
        model = self.metadata_bar.current_model()
        out_dir = Path(self.metadata_bar.output_dir())
        out_dir.mkdir(parents=True, exist_ok=True)

        basename = build_basename(self.metadata_bar.filename_pattern(), meta)
        pdf_path = out_dir / f"{basename}.pdf"
        txt_path = out_dir / f"{basename}.txt"

        now = datetime.now().strftime("%d.%m.%Y %H:%M")

        # Rohdaten (.txt) schreiben – round-trip-fähig
        roh = Rohdaten(
            metadata=meta,
            stichworte=self.input_panel.stichworte(),
            modell_name=model.label,
            rohdaten_erzeugt=now,
            pdf_erzeugt=now,
        )
        rawdata.write(roh, txt_path)

        # PDF erzeugen
        builder.build_pdf(
            output_path=str(pdf_path),
            metadata=meta,
            structured_text=structured_text,
            model_name=model.label,
            pdf_date=now,
            raw_date=now,
        )
        self._last_pdf_path = str(pdf_path)
        self.pdf_viewer.show_pdf(str(pdf_path))

    # ---- Rohdaten laden --------------------------------------------------
    def _load_rawdata(self) -> None:
        start = self.metadata_bar.output_dir() or ""
        path, _ = QFileDialog.getOpenFileName(
            self, "Rohdaten laden", start, "Rohdaten (*.txt);;Alle Dateien (*)"
        )
        if not path:
            return
        try:
            roh = rawdata.read(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Laden fehlgeschlagen", str(exc))
            return
        self.metadata_bar.set_metadata(roh.metadata)
        self.input_panel.set_stichworte(roh.stichworte)
        self._update_model_status()
        self.statusBar().showMessage(
            "Rohdaten geladen – »Erzeuge« erstellt eine neue PDF.", 6000
        )

    # ---- Worker-Verwaltung ----------------------------------------------
    def _on_worker_failed(self, message: str) -> None:
        self.input_panel.set_busy(False)
        self.input_panel.hide_progress()
        self.input_panel.set_status("")
        self._update_model_status()
        QMessageBox.critical(self, "Fehler", message)

    def _clear_worker(self, which: str) -> None:
        if which == "dl":
            self._dl_worker = None
        else:
            self._gen_worker = None

    # ---- Schließen -------------------------------------------------------
    def closeEvent(self, event) -> None:  # noqa: N802 - Qt-Signatur
        # Laufende Downloads abbrechen
        if self._dl_worker is not None:
            self._dl_worker.cancel()
            self._dl_worker.wait(2000)
        self.metadata_bar.apply_to_config(self.config)
        self.config_manager.save()
        super().closeEvent(event)

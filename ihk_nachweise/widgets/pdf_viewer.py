"""Rechte Bildschirmhälfte: Anzeige der erzeugten PDF mittels Qt-PDF."""

from __future__ import annotations

from PySide6.QtCore import QUrl, Qt
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import QLabel, QStackedWidget, QVBoxLayout, QWidget


class PdfViewer(QWidget):
    """Zeigt die zuletzt erzeugte PDF an. Vor der ersten Erzeugung ein Hinweis."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._document = QPdfDocument(self)

        self._view = QPdfView(self)
        self._view.setDocument(self._document)
        self._view.setPageMode(QPdfView.PageMode.MultiPage)
        self._view.setZoomMode(QPdfView.ZoomMode.FitInView)

        self._placeholder = QLabel(
            "Noch keine PDF erzeugt.\n\n"
            "Trage links deine Stichworte ein und klicke auf »Erzeuge«.",
            self,
        )
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setWordWrap(True)
        self._placeholder.setStyleSheet("color: #888; font-size: 13px;")

        self._stack = QStackedWidget(self)
        self._stack.addWidget(self._placeholder)  # index 0
        self._stack.addWidget(self._view)         # index 1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)

    def show_pdf(self, path: str) -> None:
        """Lädt die PDF unter ``path`` und zeigt sie an."""
        # Vorhandenes Dokument schließen, damit eine überschriebene Datei neu lädt.
        self._document.close()
        self._document.load(path)
        self._stack.setCurrentIndex(1)

    def clear(self) -> None:
        self._document.close()
        self._stack.setCurrentIndex(0)

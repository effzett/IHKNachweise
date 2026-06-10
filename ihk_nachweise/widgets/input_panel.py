"""Linke Bildschirmhälfte: Stichwort-Eingabe und Aktionsknöpfe."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class InputPanel(QWidget):
    """Eingabefeld für Stichworte plus Buttons Erzeuge/Neu/Laden."""

    erzeugeClicked = Signal()
    neuClicked = Signal()
    ladenClicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        header = QLabel("Stichworte & Tätigkeiten der Woche")
        header.setStyleSheet("font-weight: bold; font-size: 13px;")

        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText(
            "Hier die Tätigkeiten der Woche stichpunktartig eintragen, z. B.:\n"
            "- Ticketsystem eingerichtet\n"
            "- Bugfix im Login-Modul\n"
            "- Schulung Datenbanken\n\n"
            "Die lokale LLM gliedert und kategorisiert die Eingaben beim »Erzeuge«."
        )

        self.erzeuge_btn = QPushButton("Erzeuge")
        self.erzeuge_btn.setDefault(True)
        self.neu_btn = QPushButton("Neu generieren")
        self.neu_btn.setToolTip("Erzeugt das Ergebnis neu und überschreibt das alte.")
        self.laden_btn = QPushButton("Rohdaten laden …")

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.erzeuge_btn)
        btn_row.addWidget(self.neu_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(self.laden_btn)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setVisible(False)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #555;")
        self.status_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(self.text_edit, 1)
        layout.addLayout(btn_row)
        layout.addWidget(self.progress)
        layout.addWidget(self.status_label)

        self.erzeuge_btn.clicked.connect(self.erzeugeClicked)
        self.neu_btn.clicked.connect(self.neuClicked)
        self.laden_btn.clicked.connect(self.ladenClicked)

    # ---- Zugriff ---------------------------------------------------------
    def stichworte(self) -> str:
        return self.text_edit.toPlainText()

    def set_stichworte(self, text: str) -> None:
        self.text_edit.setPlainText(text)

    # ---- Zustand ---------------------------------------------------------
    def set_busy(self, busy: bool) -> None:
        self.erzeuge_btn.setEnabled(not busy)
        self.neu_btn.setEnabled(not busy)
        self.laden_btn.setEnabled(not busy)
        self.text_edit.setReadOnly(busy)

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def set_progress(self, value: int) -> None:
        if value < 0:
            self.progress.setRange(0, 0)  # unbestimmter Fortschritt
            self.progress.setVisible(True)
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(value)
            self.progress.setVisible(0 <= value < 100)

    def hide_progress(self) -> None:
        self.progress.setVisible(False)

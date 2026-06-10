"""Oberer Bereich: Metadaten, Modellauswahl, Pfade und Dateibenennung."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from ..config import AppConfig
from ..llm import catalog
from ..models import Metadata


def iso_week_range(iso_year: int, week: int) -> tuple[date, date]:
    """Montag und Freitag der angegebenen ISO-Kalenderwoche."""
    try:
        monday = date.fromisocalendar(iso_year, week, 1)
        friday = date.fromisocalendar(iso_year, week, 5)
    except ValueError:
        today = date.today()
        monday, friday = today, today
    return monday, friday


def _to_qdate(d: date) -> QDate:
    return QDate(d.year, d.month, d.day)


def _from_qdate(q: QDate) -> date:
    return date(q.year(), q.month(), q.day())


class MetadataBar(QWidget):
    """Erfasst alle Metadaten eines Nachweises (oberer Fensterbereich)."""

    modelChanged = Signal(str)  # model_id

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        today = date.today()
        self._iso_year = today.isocalendar().year

        # --- Widgets ------------------------------------------------------
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Vor- und Nachname")

        self.kw_spin = QSpinBox()
        self.kw_spin.setRange(1, 53)
        self.kw_spin.setPrefix("KW ")

        self.von_edit = QDateEdit()
        self.von_edit.setCalendarPopup(True)
        self.von_edit.setDisplayFormat("dd.MM.yyyy")
        self.bis_edit = QDateEdit()
        self.bis_edit.setCalendarPopup(True)
        self.bis_edit.setDisplayFormat("dd.MM.yyyy")

        self.arbeitsbereich_combo = QComboBox()
        self.arbeitsbereich_combo.setEditable(True)
        self.arbeitsbereich_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.betreuer_combo = QComboBox()
        self.betreuer_combo.setEditable(True)
        self.betreuer_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.model_combo = QComboBox()
        for m in catalog.CATALOG:
            self.model_combo.addItem(m.display, m.id)
        self.model_status = QLabel("—")
        self.model_status.setStyleSheet("color: #888;")

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Zielordner für PDFs und Rohdaten")
        self.browse_btn = QPushButton("Durchsuchen …")

        self.pattern_edit = QLineEdit()
        self.pattern_edit.setPlaceholderText("{name}_KW{kw}_{von}_{bis}")
        self.pattern_edit.setToolTip(
            "Platzhalter: {name} {kw} {von} {bis} {arbeitsbereich} {betreuer}"
        )

        self._build_layout()

        # --- Signale ------------------------------------------------------
        self.kw_spin.valueChanged.connect(self._on_kw_changed)
        self.model_combo.currentIndexChanged.connect(
            lambda: self.modelChanged.emit(self.current_model_id())
        )
        self.browse_btn.clicked.connect(self._browse_output)

        # Default: aktuelle KW
        self.kw_spin.setValue(today.isocalendar().week)
        self._apply_week_to_dates()

    # ---- Layout ----------------------------------------------------------
    def _build_layout(self) -> None:
        box = QGroupBox("Metadaten")
        grid = QGridLayout(box)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(6)

        # Zeile 1: Name | KW | von | bis
        grid.addWidget(QLabel("Name:"), 0, 0)
        grid.addWidget(self.name_edit, 0, 1)
        grid.addWidget(QLabel("Woche:"), 0, 2)
        grid.addWidget(self.kw_spin, 0, 3)
        grid.addWidget(QLabel("von:"), 0, 4)
        grid.addWidget(self.von_edit, 0, 5)
        grid.addWidget(QLabel("bis:"), 0, 6)
        grid.addWidget(self.bis_edit, 0, 7)

        # Zeile 2: Arbeitsbereich | Betreuer
        grid.addWidget(QLabel("Arbeitsbereich:"), 1, 0)
        grid.addWidget(self.arbeitsbereich_combo, 1, 1)
        grid.addWidget(QLabel("Betreuer/in:"), 1, 2)
        grid.addWidget(self.betreuer_combo, 1, 3, 1, 5)

        # Zeile 3: Modell + Status
        grid.addWidget(QLabel("Lokale LLM:"), 2, 0)
        grid.addWidget(self.model_combo, 2, 1, 1, 3)
        grid.addWidget(QLabel("Status:"), 2, 4)
        grid.addWidget(self.model_status, 2, 5, 1, 3)

        # Zeile 4: Ausgabeordner + Durchsuchen
        grid.addWidget(QLabel("Speicherort:"), 3, 0)
        out_row = QHBoxLayout()
        out_row.addWidget(self.output_edit, 1)
        out_row.addWidget(self.browse_btn)
        out_w = QWidget()
        out_w.setLayout(out_row)
        grid.addWidget(out_w, 3, 1, 1, 5)
        grid.addWidget(QLabel("Dateiname:"), 3, 6)
        grid.addWidget(self.pattern_edit, 3, 7)

        grid.setColumnStretch(1, 3)
        grid.setColumnStretch(7, 2)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(box)

    # ---- KW <-> Datum ----------------------------------------------------
    def _on_kw_changed(self) -> None:
        self._apply_week_to_dates()

    def _apply_week_to_dates(self) -> None:
        monday, friday = iso_week_range(self._iso_year, self.kw_spin.value())
        self.von_edit.setDate(_to_qdate(monday))
        self.bis_edit.setDate(_to_qdate(friday))

    # ---- Pfadauswahl -----------------------------------------------------
    def _browse_output(self) -> None:
        start = self.output_edit.text() or ""
        chosen = QFileDialog.getExistingDirectory(
            self, "Speicherort wählen", start
        )
        if chosen:
            self.output_edit.setText(chosen)

    # ---- Config-Anbindung ------------------------------------------------
    def load_from_config(self, config: AppConfig) -> None:
        self.name_edit.setText(config.letzter_name)
        self.output_edit.setText(config.output_dir)
        self.pattern_edit.setText(config.dateinamen_muster)

        self._set_combo_items(self.arbeitsbereich_combo, config.arbeitsbereiche,
                              config.letzter_arbeitsbereich)
        self._set_combo_items(self.betreuer_combo, config.betreuer,
                              config.letzter_betreuer)

        if config.letztes_modell:
            idx = self.model_combo.findData(config.letztes_modell)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)

    def apply_to_config(self, config: AppConfig) -> None:
        """Schreibt aktuelle Werte (inkl. neuer Dropdown-Einträge) in die Config."""
        config.letzter_name = self.name_edit.text().strip()
        config.output_dir = self.output_edit.text().strip()
        config.dateinamen_muster = self.pattern_edit.text().strip() or "{name}_KW{kw}_{von}_{bis}"
        config.letztes_modell = self.current_model_id()

        ab = self.arbeitsbereich_combo.currentText().strip()
        bt = self.betreuer_combo.currentText().strip()
        config.letzter_arbeitsbereich = ab
        config.letzter_betreuer = bt
        if ab and ab not in config.arbeitsbereiche:
            config.arbeitsbereiche.append(ab)
            config.arbeitsbereiche.sort(key=str.casefold)
        if bt and bt not in config.betreuer:
            config.betreuer.append(bt)
            config.betreuer.sort(key=str.casefold)
        # Combos um ggf. neue Einträge ergänzen
        self._set_combo_items(self.arbeitsbereich_combo, config.arbeitsbereiche, ab)
        self._set_combo_items(self.betreuer_combo, config.betreuer, bt)

    @staticmethod
    def _set_combo_items(combo: QComboBox, items: list[str], current: str) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(items)
        combo.setCurrentText(current or "")
        combo.blockSignals(False)

    # ---- Zugriff ---------------------------------------------------------
    def current_model_id(self) -> str:
        return self.model_combo.currentData() or catalog.default_model().id

    def current_model(self):
        return catalog.get_or_default(self.current_model_id())

    def output_dir(self) -> str:
        return self.output_edit.text().strip()

    def filename_pattern(self) -> str:
        return self.pattern_edit.text().strip() or "{name}_KW{kw}_{von}_{bis}"

    def current_metadata(self) -> Metadata:
        return Metadata(
            name=self.name_edit.text().strip(),
            kw=self.kw_spin.value(),
            datum_von=_from_qdate(self.von_edit.date()),
            datum_bis=_from_qdate(self.bis_edit.date()),
            arbeitsbereich=self.arbeitsbereich_combo.currentText().strip(),
            betreuer=self.betreuer_combo.currentText().strip(),
            modell_id=self.current_model_id(),
        )

    def set_metadata(self, meta: Metadata) -> None:
        """Übernimmt geladene Rohdaten-Metadaten in die Oberfläche."""
        self.name_edit.setText(meta.name)
        self.kw_spin.blockSignals(True)
        self.kw_spin.setValue(max(1, min(53, meta.kw)))
        self.kw_spin.blockSignals(False)
        self.von_edit.setDate(_to_qdate(meta.datum_von))
        self.bis_edit.setDate(_to_qdate(meta.datum_bis))
        self.arbeitsbereich_combo.setCurrentText(meta.arbeitsbereich)
        self.betreuer_combo.setCurrentText(meta.betreuer)
        if meta.modell_id:
            idx = self.model_combo.findData(meta.modell_id)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)

    def set_model_status(self, text: str) -> None:
        self.model_status.setText(text)

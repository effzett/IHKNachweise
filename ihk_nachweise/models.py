"""Datenmodelle für Metadaten und Rohdaten eines Wochennachweises."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date


@dataclass
class Metadata:
    """Metadaten eines einzelnen Nachweises (oberer Bereich der Oberfläche)."""

    name: str = ""
    kw: int = 1
    datum_von: date = field(default_factory=date.today)
    datum_bis: date = field(default_factory=date.today)
    arbeitsbereich: str = ""
    betreuer: str = ""
    modell_id: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["datum_von"] = self.datum_von.isoformat()
        d["datum_bis"] = self.datum_bis.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Metadata":
        return cls(
            name=d.get("name", ""),
            kw=int(d.get("kw", 1)),
            datum_von=_parse_date(d.get("datum_von")),
            datum_bis=_parse_date(d.get("datum_bis")),
            arbeitsbereich=d.get("arbeitsbereich", ""),
            betreuer=d.get("betreuer", ""),
            modell_id=d.get("modell_id", ""),
        )


@dataclass
class Rohdaten:
    """Vollständiger Eingabe-Datensatz eines Nachweises inkl. Stichworten.

    Wird zusammen mit der PDF als ``.txt`` gespeichert und kann später wieder
    eingelesen werden, um eine neue PDF zu erzeugen.
    """

    metadata: Metadata = field(default_factory=Metadata)
    stichworte: str = ""
    # Anzeige-/Nachverfolgungsfelder (in PDF-Fußzeile sichtbar)
    modell_name: str = ""
    rohdaten_erzeugt: str = ""  # Zeitpunkt, zu dem die Rohdaten gespeichert wurden
    pdf_erzeugt: str = ""       # Zeitpunkt, zu dem die PDF erzeugt wurde


def _parse_date(value) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    return date.today()

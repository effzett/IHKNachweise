"""Lesen/Schreiben der Rohdaten als ``.txt`` (round-trip-fähig).

Format der Datei::

    # IHK-Ausbildungsnachweis Rohdaten v1
    # name: Max Mustermann
    # kw: 24
    # datum_von: 2026-06-08
    # datum_bis: 2026-06-12
    # arbeitsbereich: Softwareentwicklung
    # betreuer: Erika Beispiel
    # modell_id: qwen2.5-3b-instruct-q4
    # modell_name: Qwen2.5 3B Instruct (gut für Deutsch)
    # rohdaten_erzeugt: 10.06.2026 14:30
    # pdf_erzeugt: 10.06.2026 14:31
    ---
    <Roh-Stichworte des Azubis, unverändert>

Der Kopfbereich enthält die Metadaten als ``# key: value``-Zeilen, getrennt vom
Stichworttext durch eine ``---``-Zeile. Dadurch lässt sich der Datensatz später
wieder vollständig laden und eine neue PDF erzeugen.
"""

from __future__ import annotations

from pathlib import Path

from ..models import Metadata, Rohdaten, _parse_date

_HEADER = "# IHK-Ausbildungsnachweis Rohdaten v1"
_SEP = "---"


def write(rohdaten: Rohdaten, path: str | Path) -> str:
    m = rohdaten.metadata
    lines = [
        _HEADER,
        f"# name: {m.name}",
        f"# kw: {m.kw}",
        f"# datum_von: {m.datum_von.isoformat()}",
        f"# datum_bis: {m.datum_bis.isoformat()}",
        f"# arbeitsbereich: {m.arbeitsbereich}",
        f"# betreuer: {m.betreuer}",
        f"# modell_id: {m.modell_id}",
        f"# modell_name: {rohdaten.modell_name}",
        f"# rohdaten_erzeugt: {rohdaten.rohdaten_erzeugt}",
        f"# pdf_erzeugt: {rohdaten.pdf_erzeugt}",
        _SEP,
    ]
    content = "\n".join(lines) + "\n" + (rohdaten.stichworte or "")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return str(p)


def read(path: str | Path) -> Rohdaten:
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    header: dict[str, str] = {}
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip() == _SEP:
            body_start = i + 1
            break
        if line.startswith("#") and ":" in line:
            key, _, value = line[1:].partition(":")
            header[key.strip()] = value.strip()
    else:
        # Keine Trennlinie gefunden: gesamte Datei als Stichworte behandeln.
        body_start = 0

    stichworte = "\n".join(lines[body_start:])

    meta = Metadata(
        name=header.get("name", ""),
        kw=_safe_int(header.get("kw"), 1),
        datum_von=_parse_date(header.get("datum_von")),
        datum_bis=_parse_date(header.get("datum_bis")),
        arbeitsbereich=header.get("arbeitsbereich", ""),
        betreuer=header.get("betreuer", ""),
        modell_id=header.get("modell_id", ""),
    )
    return Rohdaten(
        metadata=meta,
        stichworte=stichworte,
        modell_name=header.get("modell_name", ""),
        rohdaten_erzeugt=header.get("rohdaten_erzeugt", ""),
        pdf_erzeugt=header.get("pdf_erzeugt", ""),
    )


def _safe_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

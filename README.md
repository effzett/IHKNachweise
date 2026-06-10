# IHK-Ausbildungsnachweise

Desktop-Anwendung, mit der Fachinformatiker-Azubis ihre **wöchentlichen
Ausbildungsnachweise** führen. Stichworte werden links eingetragen, eine
**lokale LLM** strukturiert sie in thematische Abschnitte, und rechts wird die
daraus erzeugte **PDF** angezeigt.

## Funktionen

- Zweigeteilte Oberfläche: links Stichwort-Eingabe, rechts PDF-Vorschau (Qt PDF).
- Oberer Metadaten-Bereich: Name, Kalenderwoche + Datumsbereich (überschreibbar
  bei Arbeitsbereichswechsel innerhalb der KW), Modellauswahl, editierbare
  Dropdowns für Arbeitsbereich und Betreuer, Speicherort und Dateinamen-Muster.
- **Lokale LLM** (llama-cpp-python, GGUF). Modelle werden beim ersten Verwenden
  automatisch von Hugging Face heruntergeladen. Auswählbar u. a. Qwen2.5 3B
  (Default), Llama 3.2 3B, Qwen2.5 7B, Qwen2.5 1.5B.
- **PDF-Ausgabe** mit Kopfbereich, kategorisierten Abschnitten und Fußzeile, die
  LLM-Name sowie Erzeugungsdaten (PDF & Rohdaten) ausweist.
- Zu jeder PDF werden die **Rohdaten als `.txt`** gespeichert und können später
  wieder geladen werden, um eine neue PDF zu erzeugen.
- **Neu generieren** überschreibt ein unbefriedigendes Ergebnis (mehr Variation).
- Metadaten/Einstellungen werden in einer **Konfigurationsdatei** persistiert
  (anlegen/lesen/ändern/zurücksetzen).

## Entwicklung

```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

Beim ersten Generieren wird das gewählte Modell heruntergeladen (~1–5 GB, je
nach Auswahl). Der Download und die Generierung laufen im Hintergrund; die
Oberfläche bleibt bedienbar.

### Speicherorte (portabel)

Die App ist **portabel**: Alle Daten liegen in einem Ordner `Daten/` **neben der
Anwendung** — keine Administratorrechte nötig, nichts wird in geschützte System-
oder Programmordner geschrieben. Die App kann in jedem beschreibbaren Ordner
liegen (Home, Netzlaufwerk, USB-Stick) und wird manuell gestartet.

```
<frei gewählter Ordner>/
  IHKNachweise(.exe / .app)      # die Anwendung
  Daten/
    config.json                 # Konfiguration
    modelle/                    # heruntergeladene GGUF-Modelle
    Nachweise/                  # erzeugte PDFs + Rohdaten (.txt), konfigurierbar
```

Im Dev-Betrieb (`python main.py`) entsteht `Daten/` in der Projektwurzel.
Override per Umgebungsvariable: `IHK_DATA_DIR` (kompletter Datenordner),
`IHK_MODELS_DIR`, `IHK_CONFIG_DIR`.

> Hinweis: Beim Aktualisieren der App den Ordner `Daten/` behalten — er enthält
> Modell, Konfiguration und alle Nachweise.

## Distribution

Eigenständige Pakete (alle Bibliotheken enthalten) werden mit PyInstaller gebaut:

```bash
.venv/bin/pip install pyinstaller

# macOS (Apple Silicon) -> dist/IHKNachweise.dmg
bash packaging/build_macos.sh

# Windows 11 -> dist/IHKNachweise/IHKNachweise.exe
packaging\build_windows.bat
```

Die GitHub-Action `.github/workflows/release.yml` baut beide Plattformen, sobald
auf `master` ein Tag `v*` gepusht wird (derzeit als Gerüst angelegt).

### App-Icon

Das Icon ist als `packaging/icon.svg` hinterlegt. Aus ihm werden die
plattformspezifischen Dateien erzeugt (gerendert mit PySide6/QtSvg, keine
Zusatzabhängigkeit):

```bash
.venv/bin/python packaging/make_icons.py
# -> packaging/IHKNachweise.icns (macOS)
# -> packaging/IHKNachweise.ico  (Windows)
```

Die erzeugten Icons sind eingecheckt; der PyInstaller-Build bindet sie automatisch
ein. Nach einer Änderung an `icon.svg` das Skript erneut ausführen.

## Projektstruktur

```
ihk_nachweise/
  app.py            QApplication-Setup, Einstieg
  main_window.py    Orchestrierung (Erzeugen, Download, Laden)
  config.py         Konfigurationsverwaltung (CRUD)
  models.py         Datenmodelle (Metadata, Rohdaten)
  paths.py          plattformübliche Pfade
  llm/              Modellkatalog, Download-Worker, Generierungs-Worker
  pdf/              PDF-Erzeugung (reportlab)
  storage/          Rohdaten-IO (.txt, round-trip)
  widgets/          Metadaten-Leiste, Eingabe-Panel, PDF-Viewer
```

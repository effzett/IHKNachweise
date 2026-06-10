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

### Speicherorte

- Konfiguration: plattformüblicher App-Konfigordner (`config.json`).
- Modelle: App-Datenordner, Unterordner `models/`.
- PDFs/Rohdaten: standardmäßig `Dokumente/Ausbildungsnachweise/` (konfigurierbar).

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

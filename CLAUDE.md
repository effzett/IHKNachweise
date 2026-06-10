## Python Environment
Dieses Projekt verwendet venv unter .venv/
Immer .venv/bin/pip und .venv/bin/python verwenden.

## Projekt
Desktop-App (PySide6) für wöchentliche IHK-Ausbildungsnachweise von Azubis.
Linke Hälfte: Stichwort-Eingabe. Rechte Hälfte: PDF-Vorschau (Qt PDF / QPdfView).
Oben: Metadaten (Name, KW+Zeitraum, Modell, Arbeitsbereich/Betreuer, Pfade).

- Start: `.venv/bin/python main.py`
- Einstiegspunkt: `ihk_nachweise/app.py` (`main()`), Orchestrierung in `main_window.py`.
- Lokale LLM: `llama-cpp-python` + GGUF; Modelle werden bei Bedarf von Hugging Face
  geladen (`ihk_nachweise/llm/`). Default-Modell: Qwen2.5 3B Instruct.
- PDF: reportlab (`ihk_nachweise/pdf/builder.py`). Rohdaten als `.txt`
  (`ihk_nachweise/storage/rawdata.py`, round-trip-fähig).
- Config als JSON über Qt-StandardPaths (`config.py`, `paths.py`).
- Headless testen: `QT_QPA_PLATFORM=offscreen` voranstellen.
- Packaging: `packaging/` (PyInstaller-Spec + Build-Skripte), CI-Gerüst in
  `.github/workflows/release.yml` (Trigger: Tag `v*`).
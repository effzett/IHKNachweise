"""Anwendungseinstieg: QApplication konfigurieren und Hauptfenster starten."""

from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import QApplication

from . import APP_DISPLAY_NAME, APP_NAME, ORG_NAME, __version__


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_DISPLAY_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(ORG_NAME)

    # Import erst nach QApplication-Setup (QStandardPaths braucht App-Namen).
    from .main_window import MainWindow

    window = MainWindow()
    window.show()
    rc = app.exec()

    # Harter Prozess-Abbruch nach der Event-Loop: Die native Metal-/GGML-Engine
    # von llama-cpp-python löst beim regulären Interpreter-Teardown
    # gelegentlich eine GGML_ASSERT aus (bekanntes Upstream-Problem beim
    # Freigeben der Metal-Ressourcen). Da alle relevanten Daten (Config, PDF,
    # Rohdaten) bereits gespeichert sind, beenden wir hart und überspringen die
    # fehlerhaften nativen Destruktoren.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(rc)


if __name__ == "__main__":
    main()

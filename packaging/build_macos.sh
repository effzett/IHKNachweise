#!/usr/bin/env bash
# Baut die macOS-App (.app) und packt sie in ein .dmg.
# Voraussetzung: Aufruf aus dem Projektwurzelverzeichnis in der aktiven venv,
#   mit installiertem pyinstaller (.venv/bin/pip install pyinstaller).
set -euo pipefail

APP_NAME="IHKNachweise"
DIST_DIR="dist"
DMG_NAME="${APP_NAME}.dmg"

PYTHON="${PYTHON:-.venv/bin/python}"
PYINSTALLER="${PYINSTALLER:-.venv/bin/pyinstaller}"

echo "==> Baue ${APP_NAME}.app mit PyInstaller …"
rm -rf build "${DIST_DIR}"
"${PYINSTALLER}" packaging/IHKNachweise.spec --noconfirm

APP_PATH="${DIST_DIR}/${APP_NAME}.app"
if [[ ! -d "${APP_PATH}" ]]; then
  echo "FEHLER: ${APP_PATH} wurde nicht erzeugt." >&2
  exit 1
fi

echo "==> Erzeuge DMG …"
rm -f "${DIST_DIR}/${DMG_NAME}"
# Staging-Ordner: App + LIESMICH.txt landen gemeinsam im DMG.
STAGE="${DIST_DIR}/dmg_stage"
rm -rf "${STAGE}"
mkdir -p "${STAGE}"
cp -R "${APP_PATH}" "${STAGE}/"
cp packaging/LIESMICH.txt "${STAGE}/" 2>/dev/null || true
hdiutil create \
  -volname "${APP_NAME}" \
  -srcfolder "${STAGE}" \
  -ov -format UDZO \
  "${DIST_DIR}/${DMG_NAME}"
rm -rf "${STAGE}"

echo "==> Fertig: ${DIST_DIR}/${DMG_NAME}"

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
# Außerhalb des Workspace (mktemp), damit Spotlight/mdworker den Ordner nicht
# indexiert und hdiutil nicht mit "Resource busy" abbricht.
STAGE="$(mktemp -d "${TMPDIR:-/tmp}/ihk_dmg_stage.XXXXXX")"
trap 'rm -rf "${STAGE}"' EXIT
cp -R "${APP_PATH}" "${STAGE}/"
cp packaging/LIESMICH.txt "${STAGE}/" 2>/dev/null || true
# Spotlight-Indizierung für das Staging unterbinden (best effort).
mdutil -i off "${STAGE}" >/dev/null 2>&1 || true
touch "${STAGE}/.metadata_never_index"
sync

# hdiutil schlägt auf CI-Runnern gelegentlich mit "Resource busy" fehl, weil
# noch ein Prozess auf den frisch signierten Bundle zugreift – daher mehrere
# Versuche mit kurzer Pause.
dmg_ok=0
for attempt in 1 2 3 4 5; do
  if hdiutil create \
      -volname "${APP_NAME}" \
      -srcfolder "${STAGE}" \
      -fs HFS+ \
      -ov -format UDZO \
      "${DIST_DIR}/${DMG_NAME}"; then
    dmg_ok=1
    break
  fi
  echo "   hdiutil-Versuch ${attempt} fehlgeschlagen, neuer Versuch in 5 s …" >&2
  sleep 5
done
if [[ "${dmg_ok}" -ne 1 ]]; then
  echo "FEHLER: DMG konnte nach mehreren Versuchen nicht erzeugt werden." >&2
  exit 1
fi

echo "==> Fertig: ${DIST_DIR}/${DMG_NAME}"

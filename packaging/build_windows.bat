@echo off
REM Baut die Windows-Anwendung (.exe, onedir) mit PyInstaller.
REM Voraussetzung: Aufruf aus dem Projektwurzelverzeichnis in der aktiven venv,
REM   mit installiertem pyinstaller (.venv\Scripts\pip install pyinstaller).
setlocal

set APP_NAME=IHKNachweise
set PYINSTALLER=.venv\Scripts\pyinstaller.exe

echo ==^> Baue %APP_NAME% mit PyInstaller ...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

"%PYINSTALLER%" packaging\IHKNachweise.spec --noconfirm
if errorlevel 1 (
  echo FEHLER: PyInstaller-Build fehlgeschlagen.
  exit /b 1
)

echo ==^> Fertig. Ergebnis unter dist\%APP_NAME%\%APP_NAME%.exe
echo     (Optional: mit Inno Setup / NSIS zu einem Installer .exe verpacken.)
endlocal

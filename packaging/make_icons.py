"""Erzeugt aus ``packaging/icon.svg`` die Plattform-Icons.

- macOS:   ``IHKNachweise.icns``  (via ``iconutil``, nur auf macOS verfügbar)
- Windows: ``IHKNachweise.ico``   (reiner Python-Writer, PNG-basierte ICO)

Gerendert wird mit dem ohnehin vorhandenen PySide6 (QtSvg) – keine zusätzliche
Abhängigkeit nötig. Aufruf:

    .venv/bin/python packaging/make_icons.py
"""

from __future__ import annotations

import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

HERE = Path(__file__).resolve().parent
SVG = HERE / "icon.svg"

# Für ICNS (inkl. @2x) und ICO benötigte Kantenlängen.
SIZES = [16, 32, 48, 64, 128, 256, 512, 1024]


def render_png(renderer: QSvgRenderer, size: int, out: Path) -> None:
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    renderer.render(painter)
    painter.end()
    if not img.save(str(out), "PNG"):
        raise RuntimeError(f"Konnte {out} nicht schreiben")


def build_icns(pngs: dict[int, Path]) -> None:
    if sys.platform != "darwin":
        print("[i] ICNS übersprungen (iconutil nur auf macOS).")
        return
    iconset = HERE / "IHKNachweise.iconset"
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir()
    # (Quellgröße, Zielname) gemäß Apple-Iconset-Konvention
    mapping = [
        (16, "icon_16x16"), (32, "icon_16x16@2x"),
        (32, "icon_32x32"), (64, "icon_32x32@2x"),
        (128, "icon_128x128"), (256, "icon_128x128@2x"),
        (256, "icon_256x256"), (512, "icon_256x256@2x"),
        (512, "icon_512x512"), (1024, "icon_512x512@2x"),
    ]
    for size, name in mapping:
        shutil.copy(pngs[size], iconset / f"{name}.png")
    out = HERE / "IHKNachweise.icns"
    subprocess.run(
        ["iconutil", "-c", "icns", "-o", str(out), str(iconset)], check=True
    )
    shutil.rmtree(iconset)
    print(f"[ok] {out.name} erzeugt")


def build_ico(pngs: dict[int, Path]) -> None:
    """Schreibt eine ICO mit eingebetteten PNGs (Windows Vista+)."""
    ico_sizes = [16, 32, 48, 64, 128, 256]
    blobs = [(s, pngs[s].read_bytes()) for s in ico_sizes]

    header = struct.pack("<HHH", 0, 1, len(blobs))  # reserved, type=icon, count
    offset = 6 + 16 * len(blobs)
    entries = b""
    data = b""
    for size, png in blobs:
        dim = 0 if size >= 256 else size  # 0 bedeutet 256 im ICO-Format
        entries += struct.pack(
            "<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset
        )
        offset += len(png)
        data += png
    out = HERE / "IHKNachweise.ico"
    out.write_bytes(header + entries + data)
    print(f"[ok] {out.name} erzeugt")


def main() -> int:
    QGuiApplication(sys.argv)
    if not SVG.exists():
        print(f"[FEHLER] {SVG} fehlt.", file=sys.stderr)
        return 1
    renderer = QSvgRenderer(str(SVG))

    tmp = HERE / "_iconbuild"
    tmp.mkdir(exist_ok=True)
    pngs: dict[int, Path] = {}
    try:
        for size in SIZES:
            out = tmp / f"icon_{size}.png"
            render_png(renderer, size, out)
            pngs[size] = out
        build_icns(pngs)
        build_ico(pngs)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

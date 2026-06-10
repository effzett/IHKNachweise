"""Erzeugt aus Metadaten und strukturiertem Text eine Nachweis-PDF (reportlab).

Layout: Kopfbereich mit Metadaten, Body mit thematischen Abschnitten
(Überschriften + Stichpunkte) und eine Fußzeile auf jeder Seite, die den
LLM-Namen sowie die Erzeugungsdaten von PDF und Rohdaten anzeigt.
"""

from __future__ import annotations

import html
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    ListFlowable,
    ListItem,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from ..models import Metadata

_ACCENT = colors.HexColor("#1f4e79")
_LIGHT = colors.HexColor("#eef3f8")
_GREY = colors.HexColor("#666666")


def _styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "NwTitle", parent=base["Title"], fontSize=18, textColor=_ACCENT,
            spaceAfter=2, alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "NwSubtitle", parent=base["Normal"], fontSize=10, textColor=_GREY,
            spaceAfter=8,
        ),
        "meta": ParagraphStyle(
            "NwMeta", parent=base["Normal"], fontSize=10, leading=14,
        ),
        "meta_label": ParagraphStyle(
            "NwMetaLabel", parent=base["Normal"], fontSize=10, leading=14,
            textColor=_GREY,
        ),
        "heading": ParagraphStyle(
            "NwHeading", parent=base["Heading2"], fontSize=13, textColor=_ACCENT,
            spaceBefore=12, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "NwBody", parent=base["Normal"], fontSize=10.5, leading=15,
        ),
        "bullet": ParagraphStyle(
            "NwBullet", parent=base["Normal"], fontSize=10.5, leading=15,
        ),
    }
    return styles


def _meta_table(meta: Metadata, styles) -> Table:
    zeitraum = f"{meta.datum_von.strftime('%d.%m.%Y')} – {meta.datum_bis.strftime('%d.%m.%Y')}"
    rows = [
        ("Name", meta.name or "—", "Kalenderwoche", f"KW {meta.kw:02d}"),
        ("Arbeitsbereich", meta.arbeitsbereich or "—", "Zeitraum", zeitraum),
        ("Betreuer/in", meta.betreuer or "—", "", ""),
    ]
    data = []
    for l1, v1, l2, v2 in rows:
        data.append([
            Paragraph(l1, styles["meta_label"]),
            Paragraph(html.escape(v1), styles["meta"]),
            Paragraph(l2, styles["meta_label"]),
            Paragraph(html.escape(v2), styles["meta"]),
        ])
    table = Table(data, colWidths=[28 * mm, 62 * mm, 30 * mm, 50 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, _ACCENT),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _parse_body(text: str, styles) -> list:
    """Wandelt den (markdown-artigen) LLM-Text in Platypus-Flowables um."""
    flow: list = []
    pending_bullets: list = []

    def flush_bullets():
        nonlocal pending_bullets
        if pending_bullets:
            items = [
                ListItem(Paragraph(html.escape(b), styles["bullet"]), leftIndent=6)
                for b in pending_bullets
            ]
            flow.append(ListFlowable(items, bulletType="bullet", start="•",
                                     leftIndent=12))
            pending_bullets = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_bullets()
            continue
        if stripped.startswith("##"):
            flush_bullets()
            heading = stripped.lstrip("#").strip()
            flow.append(Paragraph(html.escape(heading), styles["heading"]))
        elif stripped.startswith(("- ", "* ", "• ")):
            pending_bullets.append(stripped[2:].strip())
        else:
            flush_bullets()
            flow.append(Paragraph(html.escape(stripped), styles["body"]))
    flush_bullets()
    if not flow:
        flow.append(Paragraph("(Kein Inhalt erzeugt.)", styles["body"]))
    return flow


def _make_footer(model_name: str, pdf_date: str, raw_date: str):
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(_GREY)
        width, _ = A4
        left = f"Erzeugt mit lokaler LLM: {model_name or '—'}"
        right = f"PDF: {pdf_date}   |   Rohdaten: {raw_date or pdf_date}"
        canvas.drawString(18 * mm, 12 * mm, left)
        canvas.drawRightString(width - 18 * mm, 12 * mm, right)
        canvas.setStrokeColor(_GREY)
        canvas.setLineWidth(0.3)
        canvas.line(18 * mm, 15 * mm, width - 18 * mm, 15 * mm)
        canvas.drawCentredString(width / 2, 6 * mm, f"Seite {doc.page}")
        canvas.restoreState()

    return footer


def build_pdf(
    output_path: str,
    metadata: Metadata,
    structured_text: str,
    model_name: str,
    pdf_date: str | None = None,
    raw_date: str = "",
) -> str:
    """Baut die PDF und schreibt sie nach ``output_path``. Gibt den Pfad zurück."""
    styles = _styles()
    pdf_date = pdf_date or date.today().strftime("%d.%m.%Y")

    doc = BaseDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=22 * mm,
        title=f"Ausbildungsnachweis KW{metadata.kw:02d} {metadata.name}",
        author=metadata.name,
    )
    frame = Frame(
        doc.leftMargin, doc.bottomMargin,
        doc.width, doc.height, id="main",
    )
    footer = _make_footer(model_name, pdf_date, raw_date)
    doc.addPageTemplates([PageTemplate(id="nw", frames=[frame], onPage=footer)])

    story: list = [
        Paragraph("Ausbildungsnachweis", styles["title"]),
        Paragraph("Wöchentlicher Ausbildungsnachweis für Fachinformatiker/innen",
                  styles["subtitle"]),
        _meta_table(metadata, styles),
        Spacer(1, 8 * mm),
    ]
    story.extend(_parse_body(structured_text, styles))

    doc.build(story)
    return output_path

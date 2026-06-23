from __future__ import annotations

import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#15263F")
BLUE = colors.HexColor("#246BCE")
LIGHT_BLUE = colors.HexColor("#EAF2FC")
LIGHT_GREY = colors.HexColor("#F4F6F8")
MID_GREY = colors.HexColor("#697386")
GRID = colors.HexColor("#D8DEE8")


def _plain(value: object) -> str:
    text = str(value or "")
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1 (\2)", text)
    text = text.replace("**", "").replace("`", "")
    return (
        text.replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u2022", "-")
        .replace("\u00a0", " ")
        .strip()
    )


def _paragraph(value: object, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(_plain(value)).replace("\n", "<br/>"), style)


def _draw_page(canvas, doc) -> None:
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(GRID)
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.setFillColor(MID_GREY)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18 * mm, 9 * mm, "Reddit Product and API-User Insights")
    canvas.drawRightString(width - 18 * mm, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _table(
    headers: list[str],
    rows: list[list[object]],
    widths: list[float],
    styles: dict[str, ParagraphStyle],
) -> Table:
    data = [[_paragraph(header, styles["table_header"]) for header in headers]]
    for row in rows:
        data.append([_paragraph(cell, styles["table_body"]) for cell in row])
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.45, GRID),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def generate_insights_pdf(output_path: Path, report: dict) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    custom = {
        "title": ParagraphStyle(
            "Title", parent=styles["Title"], fontName="Helvetica-Bold",
            fontSize=21, leading=26, textColor=NAVY, alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "section": ParagraphStyle(
            "Section", parent=styles["Heading2"], fontName="Helvetica-Bold",
            fontSize=13, leading=16, textColor=NAVY, spaceBefore=10, spaceAfter=7,
        ),
        "body": ParagraphStyle(
            "Body", parent=styles["BodyText"], fontName="Helvetica",
            fontSize=9.5, leading=14, textColor=colors.HexColor("#263445"),
            spaceAfter=6,
        ),
        "summary": ParagraphStyle(
            "Summary", parent=styles["BodyText"], fontName="Helvetica",
            fontSize=10, leading=15, textColor=colors.HexColor("#263445"),
            leftIndent=7, borderColor=BLUE, borderWidth=0, borderPadding=6,
            backColor=LIGHT_BLUE, spaceAfter=7,
        ),
        "table_header": ParagraphStyle(
            "TableHeader", parent=styles["BodyText"], fontName="Helvetica-Bold",
            fontSize=7.6, leading=9.5, textColor=colors.white,
        ),
        "table_body": ParagraphStyle(
            "TableBody", parent=styles["BodyText"], fontName="Helvetica",
            fontSize=7.3, leading=9.4, textColor=colors.HexColor("#263445"),
        ),
    }

    doc = BaseDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=17 * mm, bottomMargin=19 * mm,
        title="Reddit Product and API-User Insights",
        author="Reddit Product Insights",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates(PageTemplate(id="insights", frames=[frame], onPage=_draw_page))

    story = [_paragraph("Reddit Product and API-User Insights", custom["title"]), Spacer(1, 3 * mm)]

    story.append(_paragraph("1. Executive Summary", custom["section"]))
    for index, item in enumerate(report.get("executive_summary", []), start=1):
        story.append(_paragraph(f"{index}. {item}", custom["summary"]))

    story.append(_paragraph("2. Most Discussed Topics and Product Response", custom["section"]))
    topic_rows = [[
        row.get("topic"), row.get("discussion"), row.get("product_thinking"), row.get("solution")
    ] for row in report.get("topics", [])]
    story.append(_table(
        ["Topic", "Discussion", "Product thinking", "Suggested solution"],
        topic_rows, [31 * mm, 40 * mm, 50 * mm, 50 * mm], custom,
    ))

    story.append(_paragraph("3. Most Requested API Capabilities", custom["section"]))
    feature_rows = [[
        row.get("capability"), row.get("demand"), row.get("nubra_status"), row.get("action")
    ] for row in report.get("api_capabilities", [])]
    story.append(_table(
        ["Capability", "User need", "Nubra status", "Recommended action"],
        feature_rows, [38 * mm, 45 * mm, 34 * mm, 54 * mm], custom,
    ))

    story.append(_paragraph("4. Retail and API/Algo Discussion Split", custom["section"]))
    split_rows = [[row.get("segment"), row.get("needs"), row.get("product_use")] for row in report.get("segment_split", [])]
    story.append(_table(
        ["Segment", "Dominant needs", "Product use"],
        split_rows, [30 * mm, 65 * mm, 76 * mm], custom,
    ))

    story.append(_paragraph("5. Webinar Opportunities", custom["section"]))
    webinar_rows = [[
        row.get("title"), row.get("audience"), row.get("why"), row.get("outcome")
    ] for row in report.get("webinars", [])]
    story.append(_table(
        ["Webinar", "Audience", "Why it matters", "Product outcome"],
        webinar_rows, [47 * mm, 32 * mm, 47 * mm, 45 * mm], custom,
    ))

    story.append(_paragraph("6. Product Roadmap", custom["section"]))
    roadmap_rows = []
    for horizon in ("Now", "Next", "Later"):
        actions = report.get("roadmap", {}).get(horizon, [])
        roadmap_rows.append([horizon, "\n".join(f"- {item}" for item in actions) or "Continue product discovery."])
    story.append(_table(["Horizon", "Recommended actions"], roadmap_rows, [30 * mm, 141 * mm], custom))

    story.append(_paragraph("7. Awareness, Documentation and Onboarding Gaps", custom["section"]))
    for item in report.get("awareness_gaps", []):
        story.append(_paragraph(f"- {item}", custom["body"]))

    doc.build(story)
    return output_path


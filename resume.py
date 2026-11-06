"""Local project storage and Word export for the first Academicgent workflow."""

import io
import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


from storage import DATA_DIR, connect, list_projects, load_project, save_project

PRESET = json.loads(
    (Path(__file__).parent / "templates/presets/resume-v0.1.json").read_text(encoding="utf-8")
)


def section_label(index):
    label = ""
    while index:
        index, digit = divmod(index - 1, 26)
        label = chr(65 + digit) + label
    return label


def parse_content(content):
    """Read headings and paragraphs from a small, predictable text format."""
    blocks = []
    paragraph = []

    def flush():
        if paragraph:
            blocks.append(("paragraph", " ".join(paragraph)))
            paragraph.clear()

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            flush()
        elif line.startswith("### "):
            flush()
            blocks.append(("subheading", line[4:].strip()))
        elif line.startswith("## "):
            flush()
            blocks.append(("heading", line[3:].strip()))
        elif line.startswith("- "):
            flush()
            blocks.append(("bullet", line[2:].strip()))
        else:
            paragraph.append(line)
    flush()
    return [(kind, value) for kind, value in blocks if value]


def _font(run, size, bold=False, family="Times New Roman"):
    run.font.name = family
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)


def build_docx(payload):
    """Return a DOCX byte stream from a saved or edited resume payload."""
    doc = Document()
    section = doc.sections[0]
    preset = payload.get("preset_snapshot") or PRESET
    page = preset["page"]
    section.page_width, section.page_height = Cm(page["width_cm"]), Cm(page["height_cm"])
    for side, value in page["margins_cm"].items():
        setattr(section, side + "_margin", Cm(value))
    section.header_distance = Cm(page["header_distance_cm"])
    section.footer_distance = Cm(page["footer_distance_cm"])

    body = preset["typography"]["body"]
    normal = doc.styles["Normal"]
    normal.font.name = body["font"]
    normal.font.size = Pt(body["size_pt"])
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.line_spacing = body["line_spacing"]
    normal.paragraph_format.space_after = Pt(body["space_after_pt"])
    normal.paragraph_format.first_line_indent = Cm(body["first_line_indent_cm"])
    for style_name, size in (("Title", 16), ("Heading 1", 12), ("Heading 2", 11.5)):
        style = doc.styles[style_name]
        style.font.name = body["font"]
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        for border in style.element.xpath("./w:pPr/w:pBdr"):
            border.getparent().remove(border)

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _font(header.add_run(f'RESUME MATERI  |  {payload["course"].upper()}'), 8, family="Arial")

    title = doc.add_paragraph(style="Title")
    title.paragraph_format.keep_with_next = True
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(22)
    title.paragraph_format.first_line_indent = Cm(0)
    _font(title.add_run(payload["title"].upper()), 16, bold=True)
    if payload["subtitle"].strip():
        subtitle = doc.add_paragraph()
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle.paragraph_format.first_line_indent = Cm(0)
        subtitle.paragraph_format.space_after = Pt(16)
        _font(subtitle.add_run(payload["subtitle"].upper()), 10, bold=True)

    table = doc.add_table(rows=0, cols=2)
    table.autofit = False
    table.columns[0].width = Cm(4.6)
    content_width = page["width_cm"] - page["margins_cm"]["left"] - page["margins_cm"]["right"]
    table.columns[1].width = Cm(content_width - 4.6)
    for label, key in [
        ("Nama", "name"), ("NIM", "student_number"),
        ("Program Studi", "study_program"), ("Dosen Pengampu", "lecturer"),
    ]:
        cells = table.add_row().cells
        cells[0].width, cells[1].width = Cm(4.6), Cm(content_width - 4.6)
        for cell in cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cell.paragraphs[0].paragraph_format.first_line_indent = Cm(0)
        _font(cells[0].paragraphs[0].add_run(label), 9, bold=True, family="Arial")
        _font(cells[1].paragraphs[0].add_run(":  " + payload[key]), 9, family="Arial")

    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    heading_number = 0
    subheading_number = 0
    for kind, value in parse_content(payload["content"]):
        if kind == "heading":
            heading_number += 1
            subheading_number = 0
            paragraph = doc.add_paragraph(style="Heading 1")
            paragraph.paragraph_format.space_before = Pt(9)
            paragraph.paragraph_format.space_after = Pt(4)
            paragraph.paragraph_format.keep_with_next = True
            paragraph.paragraph_format.first_line_indent = Cm(0)
            _font(paragraph.add_run(f"{section_label(heading_number)}. {value}"), 12, bold=True)
        elif kind == "subheading":
            subheading_number += 1
            paragraph = doc.add_paragraph(style="Heading 2")
            paragraph.paragraph_format.space_before = Pt(6)
            paragraph.paragraph_format.space_after = Pt(3)
            paragraph.paragraph_format.keep_with_next = True
            paragraph.paragraph_format.first_line_indent = Cm(0)
            _font(paragraph.add_run(f"{subheading_number}. {value}"), 11.5, bold=True)
        elif kind == "bullet":
            paragraph = doc.add_paragraph(style="List Bullet")
            paragraph.paragraph_format.first_line_indent = None
            paragraph.add_run(value)
        else:
            paragraph = doc.add_paragraph(value)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _font(footer.add_run(f'{payload["name"]}    {payload["student_number"]}    |    '), 8, family="Arial")
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    field_run = OxmlElement("w:r")
    properties = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts")
    fonts.set(qn("w:ascii"), "Arial")
    fonts.set(qn("w:hAnsi"), "Arial")
    properties.append(fonts)
    size = OxmlElement("w:sz")
    size.set(qn("w:val"), "16")
    properties.append(size)
    field_run.append(properties)
    text = OxmlElement("w:t")
    text.text = "1"
    field_run.append(text)
    field.append(field_run)
    footer._p.append(field)
    output = io.BytesIO()
    doc.save(output)
    return output.getvalue()

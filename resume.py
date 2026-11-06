"""Local project storage and Word export for the first Academicgent workflow."""

import io
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


DATA_DIR = Path.home() / "AcademicgentData"
PRESET = json.loads(
    (Path(__file__).parent / "templates/presets/resume-v0.1.json").read_text(encoding="utf-8")
)


def connect(data_dir=DATA_DIR):
    data_dir.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(data_dir / "projects.sqlite3")
    db.execute("PRAGMA busy_timeout = 5000")
    db.execute(
        """CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            payload TEXT NOT NULL,
            revision INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        )"""
    )
    db.commit()
    return db


def list_projects(db):
    return db.execute(
        "SELECT id, title, revision FROM projects ORDER BY updated_at DESC, id DESC"
    ).fetchall()


def load_project(db, project_id):
    row = db.execute(
        "SELECT payload, revision FROM projects WHERE id = ?", (project_id,)
    ).fetchone()
    return (json.loads(row[0]), row[1]) if row else None


def save_project(db, payload, project_id=None, expected_revision=None):
    """Save a revision, rejecting edits based on an older browser tab."""
    now = datetime.now(timezone.utc).isoformat()
    serialized = json.dumps(payload, ensure_ascii=False)
    if project_id is None:
        project_id = uuid4().hex
        with db:
            db.execute(
                "INSERT INTO projects VALUES (?, ?, ?, ?, ?)",
                (project_id, payload["title"], serialized, 1, now),
            )
        return project_id, 1

    with db:
        cursor = db.execute(
            """UPDATE projects SET title = ?, payload = ?, revision = revision + 1,
               updated_at = ? WHERE id = ? AND revision = ?""",
            (payload["title"], serialized, now, project_id, expected_revision),
        )
        if cursor.rowcount != 1:
            raise ValueError("Proyek telah diubah di tab lain. Muat ulang sebelum menyimpan.")
    return project_id, expected_revision + 1


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
    page = PRESET["page"]
    section.page_width, section.page_height = Cm(page["width_cm"]), Cm(page["height_cm"])
    for side, value in page["margins_cm"].items():
        setattr(section, side + "_margin", Cm(value))
    section.header_distance = Cm(page["header_distance_cm"])
    section.footer_distance = Cm(page["footer_distance_cm"])

    body = PRESET["typography"]["body"]
    normal = doc.styles["Normal"]
    normal.font.name = body["font"]
    normal.font.size = Pt(body["size_pt"])
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.line_spacing = body["line_spacing"]
    normal.paragraph_format.space_after = Pt(body["space_after_pt"])
    normal.paragraph_format.first_line_indent = Cm(body["first_line_indent_cm"])

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _font(header.add_run(f'RESUME MATERI  |  {payload["course"].upper()}'), 8, family="Arial")

    title = doc.add_paragraph()
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
    table.columns[1].width = Cm(10.5)
    for label, key in [
        ("Nama", "name"), ("NIM", "student_number"),
        ("Program Studi", "study_program"), ("Dosen Pengampu", "lecturer"),
    ]:
        cells = table.add_row().cells
        cells[0].width, cells[1].width = Cm(4.6), Cm(10.5)
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
            paragraph = doc.add_paragraph()
            paragraph.paragraph_format.space_before = Pt(9)
            paragraph.paragraph_format.space_after = Pt(4)
            paragraph.paragraph_format.keep_with_next = True
            paragraph.paragraph_format.first_line_indent = Cm(0)
            _font(paragraph.add_run(f"{section_label(heading_number)}. {value}"), 12, bold=True)
        elif kind == "subheading":
            subheading_number += 1
            paragraph = doc.add_paragraph()
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
    footer._p.append(field)
    output = io.BytesIO()
    doc.save(output)
    return output.getvalue()

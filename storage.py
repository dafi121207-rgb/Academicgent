"""SQLite project revisions and immutable PDF originals on local disk."""

import hashlib
import json
import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


DATA_DIR = Path.home() / "AcademicgentData"


def now():
    return datetime.now(timezone.utc).isoformat()


def connect(data_dir=None):
    directory = Path(data_dir or os.environ.get("ACADEMICGENT_DATA_DIR", DATA_DIR))
    directory.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(directory / "projects.sqlite3", timeout=10)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, payload TEXT NOT NULL,
            revision INTEGER NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS project_revisions (
            project_id TEXT NOT NULL REFERENCES projects(id), revision INTEGER NOT NULL,
            payload TEXT NOT NULL, created_at TEXT NOT NULL,
            PRIMARY KEY (project_id, revision)
        );
        INSERT OR IGNORE INTO project_revisions
            SELECT id, revision, payload, updated_at FROM projects;
        CREATE TABLE IF NOT EXISTS sources (
            project_id TEXT PRIMARY KEY REFERENCES projects(id), name TEXT NOT NULL,
            sha256 TEXT NOT NULL, revision INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS source_pages (
            project_id TEXT NOT NULL REFERENCES sources(project_id), position INTEGER NOT NULL,
            printed_label TEXT NOT NULL DEFAULT '', reading_order INTEGER NOT NULL,
            selected INTEGER NOT NULL DEFAULT 1, text TEXT NOT NULL,
            method TEXT NOT NULL, reviewed INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (project_id, position)
        );
        CREATE TABLE IF NOT EXISTS generation_jobs (
            id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
            status TEXT NOT NULL, input_json TEXT NOT NULL, results_json TEXT NOT NULL,
            error TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL
        );
        CREATE UNIQUE INDEX IF NOT EXISTS one_active_generation
            ON generation_jobs((1)) WHERE status IN ('running', 'cancelling');
    """)
    db.commit()
    return db


def data_directory(db):
    return Path(db.execute("PRAGMA database_list").fetchone()[2]).parent


def list_projects(db):
    return db.execute("SELECT id, title, revision FROM projects ORDER BY updated_at DESC, id").fetchall()


def load_project(db, project_id, revision=None):
    if revision is None:
        row = db.execute("SELECT payload, revision FROM projects WHERE id = ?", (project_id,)).fetchone()
    else:
        row = db.execute(
            "SELECT payload, revision FROM project_revisions WHERE project_id = ? AND revision = ?",
            (project_id, revision),
        ).fetchone()
    return (json.loads(row[0]), row[1]) if row else None


def save_project(db, payload, project_id=None, expected_revision=None):
    title = payload.get("title", "").strip()
    if not title:
        raise ValueError("Isi judul proyek sebelum menyimpan.")
    serialized = json.dumps(payload, ensure_ascii=False)
    timestamp = now()
    with db:
        if project_id is None:
            project_id, revision = uuid4().hex, 1
            db.execute("INSERT INTO projects VALUES (?, ?, ?, ?, ?)",
                       (project_id, title, serialized, revision, timestamp))
        else:
            cursor = db.execute(
                "UPDATE projects SET title=?, payload=?, revision=revision+1, updated_at=? "
                "WHERE id=? AND revision=?", (title, serialized, timestamp, project_id, expected_revision),
            )
            if cursor.rowcount != 1:
                raise ValueError("Proyek diubah di tab lain. Salin perubahanmu, lalu buka kembali proyek.")
            revision = expected_revision + 1
        db.execute("INSERT INTO project_revisions VALUES (?, ?, ?, ?)",
                   (project_id, revision, serialized, timestamp))
    return project_id, revision


def list_revisions(db, project_id):
    return db.execute(
        "SELECT revision, created_at FROM project_revisions WHERE project_id=? ORDER BY revision DESC",
        (project_id,),
    ).fetchall()


def get_source(db, project_id):
    row = db.execute("SELECT name, sha256, revision FROM sources WHERE project_id=?", (project_id,)).fetchone()
    if row is None:
        return None
    name, digest, revision = row
    return {"name": name, "sha256": digest, "revision": revision,
            "path": data_directory(db) / "sources" / f"{digest}.pdf"}


def get_pages(db, project_id):
    rows = db.execute(
        "SELECT position, printed_label, reading_order, selected, text, method, reviewed "
        "FROM source_pages WHERE project_id=? ORDER BY reading_order, position", (project_id,),
    ).fetchall()
    keys = ("position", "printed_label", "reading_order", "selected", "text", "method", "reviewed")
    return [dict(zip(keys, row)) for row in rows]


def _advance_source(db, project_id, expected_revision):
    cursor = db.execute("UPDATE sources SET revision=revision+1 WHERE project_id=? AND revision=?",
                        (project_id, expected_revision))
    if cursor.rowcount != 1:
        raise ValueError("Bahan sumber sudah berubah. Muat ulang halaman sebelum menyimpan perubahan ini.")


def install_source(db, project_id, filename, data, pages, expected_revision=None):
    """Publish a PDF only after extraction succeeds; preserve prior sources on failure."""
    if not pages or not load_project(db, project_id):
        raise ValueError("Simpan proyek dan pilih PDF yang memiliki halaman.")
    digest = hashlib.sha256(data).hexdigest()
    current = get_source(db, project_id)
    if current and current["sha256"] == digest:
        return current
    folder = data_directory(db) / "sources"
    folder.mkdir(exist_ok=True)
    target = folder / f"{digest}.pdf"
    if not target.exists():
        handle, temporary = tempfile.mkstemp(dir=folder, suffix=".tmp")
        try:
            with os.fdopen(handle, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            Path(temporary).unlink(missing_ok=True)
    with db:
        if current:
            _advance_source(db, project_id, expected_revision)
            db.execute("UPDATE sources SET name=?, sha256=? WHERE project_id=?", (filename, digest, project_id))
            db.execute("DELETE FROM source_pages WHERE project_id=?", (project_id,))
        else:
            db.execute("INSERT INTO sources VALUES (?, ?, ?, 1)", (project_id, filename, digest))
        db.executemany(
            "INSERT INTO source_pages VALUES (?, ?, ?, ?, 1, ?, 'native', 0)",
            [(project_id, p["position"], p.get("printed_label", ""), p["position"], p["text"]) for p in pages],
        )
    return get_source(db, project_id)


def save_page(db, project_id, position, text, label, reviewed, expected_revision, method="edited"):
    if len(text) > 100_000 or len(label) > 40:
        raise ValueError("Teks halaman atau label terlalu panjang.")
    if reviewed and not text.strip():
        raise ValueError("Isi teks halaman sebelum menandainya sudah diperiksa.")
    with db:
        _advance_source(db, project_id, expected_revision)
        cursor = db.execute(
            "UPDATE source_pages SET text=?, printed_label=?, reviewed=?, method=? WHERE project_id=? AND position=?",
            (text, label.strip(), int(reviewed), method, project_id, position),
        )
        if cursor.rowcount != 1:
            raise ValueError("Halaman sumber tidak ditemukan.")


def save_order(db, project_id, rows, expected_revision):
    original = get_pages(db, project_id)
    try:
        positions = [int(row["position"]) for row in rows]
        orders = [int(row["reading_order"]) for row in rows]
    except (TypeError, ValueError, KeyError) as error:
        raise ValueError("Isi semua urutan baca dengan angka sebelum menyimpan.") from error
    if sorted(positions) != sorted(p["position"] for p in original):
        raise ValueError("Daftar halaman berubah. Muat ulang tabel.")
    if sorted(orders) != list(range(1, len(rows) + 1)):
        raise ValueError("Gunakan urutan 1 sampai jumlah halaman, masing-masing satu kali.")
    if not any(row["selected"] for row in rows):
        raise ValueError("Pilih setidaknya satu halaman.")
    with db:
        _advance_source(db, project_id, expected_revision)
        db.executemany(
            "UPDATE source_pages SET reading_order=?, selected=? WHERE project_id=? AND position=?",
            [(int(row["reading_order"]), int(bool(row["selected"])), project_id, int(row["position"])) for row in rows],
        )


def source_signature(source, pages):
    if source is None:
        return ""
    value = {"sha256": source["sha256"], "pages": [p for p in pages if p["selected"]]}
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def source_locator(page):
    label = page["printed_label"].strip()
    return f"hlm. {label}" if label else f"halaman PDF {page['position']}"

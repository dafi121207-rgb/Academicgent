"""Regression checks for source order, persisted edits, and resumable Ollama jobs."""

import io
import json
import sqlite3
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from docx import Document

from generation import JobRunner, get_job, make_chunks, validate_result
from pdf_tools import inspect_pdf, preview_page
from resume import build_docx
from storage import (
    connect, get_pages, get_source, install_source, load_project, save_order, save_page,
    save_project, source_signature,
)


def sample_pdf():
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R 5 0 R] /Count 2 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 7 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length 72 >>\nstream\nBT /F1 12 Tf 50 750 Td (Learning uses practice and feedback.) Tj ET\nendstream",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 7 0 R >> >> /Contents 6 0 R >>",
        b"<< /Length 70 >>\nstream\nBT /F1 12 Tf 50 750 Td (Students reflect on their learning.) Tj ET\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Roman >>",
    ]
    # Compute stream lengths rather than relying on literal test text sizes.
    for index in (3, 5):
        stream = objects[index].split(b"stream\n", 1)[1].split(b"\nendstream")[0]
        objects[index] = b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return bytes(pdf)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.db = connect(self.directory)
        self.record = {
            "title": "Resume contoh", "subtitle": "Pembelajaran", "name": "Mahasiswa Contoh",
            "student_number": "00123", "study_program": "Sistem Informasi",
            "lecturer": "Dosen Contoh", "course": "Teknologi Pendidikan",
            "content": "## Pendahuluan\n\nIsi awal.",
        }
        self.project_id, self.revision = save_project(self.db, self.record)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def add_source(self):
        data = sample_pdf()
        pages = inspect_pdf(data)
        self.assertEqual(len(pages), 2)
        source = install_source(self.db, self.project_id, "materi.pdf", data, pages)
        for page in get_pages(self.db, self.project_id):
            source = get_source(self.db, self.project_id)
            save_page(self.db, self.project_id, page["position"], page["text"],
                      str(230 - page["position"]), True, source["revision"])
        return get_source(self.db, self.project_id)

    def test_revision_history_and_stale_tab(self):
        updated = dict(self.record, content="## Revisi\n\nIsi berikutnya.")
        _, revision = save_project(self.db, updated, self.project_id, 1)
        self.assertEqual(revision, 2)
        self.assertEqual(load_project(self.db, self.project_id, 1)[0], self.record)
        with self.assertRaises(ValueError):
            save_project(self.db, self.record, self.project_id, 1)
        self.assertEqual(load_project(self.db, self.project_id)[0], updated)

    def test_migration_from_p1(self):
        old_path = self.directory / "legacy"
        old_path.mkdir()
        old = sqlite3.connect(old_path / "projects.sqlite3")
        old.execute("CREATE TABLE projects (id TEXT PRIMARY KEY, title TEXT, payload TEXT, revision INTEGER, updated_at TEXT)")
        old.execute("INSERT INTO projects VALUES ('legacy', 'Old', ?, 5, '2026-01-01')", (json.dumps(self.record),))
        old.commit()
        old.close()
        migrated = connect(old_path)
        self.assertEqual(load_project(migrated, "legacy", 5)[0], self.record)
        migrated.close()

    def test_pdf_order_review_and_stale_page(self):
        source = self.add_source()
        original = get_pages(self.db, self.project_id)
        signature = source_signature(source, original)
        reordered = [dict(original[1], reading_order=1), dict(original[0], reading_order=2)]
        save_order(self.db, self.project_id, reordered, source["revision"])
        self.assertEqual([p["position"] for p in get_pages(self.db, self.project_id)], [2, 1])
        self.assertNotEqual(source_signature(get_source(self.db, self.project_id),
                                            get_pages(self.db, self.project_id)), signature)
        with self.assertRaises(ValueError):
            save_page(self.db, self.project_id, 1, "stale edit", "", True, source["revision"])
        before = get_source(self.db, self.project_id)["revision"]
        invalid = [dict(p, reading_order=1) for p in reordered]
        with self.assertRaises(ValueError):
            save_order(self.db, self.project_id, invalid, before)
        with self.assertRaises(ValueError):
            save_order(self.db, self.project_id, [dict(p, reading_order=None) for p in reordered], before)
        self.assertEqual(get_source(self.db, self.project_id)["revision"], before)
        png = preview_page(source["path"], 1)
        self.assertTrue(png.startswith(b"\x89PNG"))

    def test_bad_pdf_and_unreviewed_sources(self):
        with self.assertRaises(ValueError):
            inspect_pdf(b"not a PDF")
        self.add_source()
        pages = get_pages(self.db, self.project_id)
        pages[0]["reviewed"] = False
        with self.assertRaises(ValueError):
            make_chunks(pages)
        with self.assertRaises(ValueError):
            validate_result({"heading": "Judul", "paragraphs": [
                {"text": "Ringkasan.", "evidence": "This evidence was invented."}
            ]}, {"text": "Learning uses practice and feedback."})

    def test_word_from_old_project(self):
        document = Document(io.BytesIO(build_docx(self.record)))
        self.assertAlmostEqual(document.sections[0].page_width.cm, 21, places=2)
        self.assertEqual(document.tables[0].rows[1].cells[1].text, ":  00123")
        self.assertTrue(document.sections[0].footer.paragraphs[0]._p.xpath(".//w:fldSimple"))
        self.assertEqual(document.paragraphs[3].style.name, "Heading 1")
        self.assertFalse(document.styles["Title"]._element.xpath("./w:pPr/w:pBdr"))

    def test_checkpoint_and_resume_via_local_api(self):
        source = self.add_source()
        pages = get_pages(self.db, self.project_id)
        calls = []
        failures = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if self.path == "/api/show":
                    response = {}
                else:
                    text = body["messages"][1]["content"].split("SUMBER\n", 1)[1].split("\nAKHIR SUMBER")[0]
                    calls.append(text)
                    if "Students" in text and not failures:
                        failures.append(True)
                        self.send_response(503)
                        self.end_headers()
                        self.wfile.write(b"temporary test failure")
                        return
                    response = {"done_reason": "stop", "message": {"content": json.dumps({
                        "heading": "Pembelajaran", "paragraphs": [{"text": "Ringkasan uji.", "evidence": text}]
                    })}}
                encoded = json.dumps(response).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        runner = JobRunner(self.directory)
        try:
            job_id = runner.start(self.project_id, source_signature(source, pages), pages,
                                  "local-test", server.server_port, "sedang", 1)
            self.wait_status(job_id, "failed")
            self.assertEqual(len(get_job(self.db, job_id)["results"]), 1)
            runner.resume(job_id)
            self.wait_status(job_id, "succeeded")
            self.assertEqual(len(get_job(self.db, job_id)["results"]), 2)
            self.assertEqual(sum("Learning uses" in text for text in calls), 1)
        finally:
            runner.executor.shutdown(wait=True)
            server.shutdown()
            server.server_close()

    def wait_status(self, job_id, desired):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if get_job(self.db, job_id)["status"] == desired:
                return
            time.sleep(0.03)
        self.fail(str(get_job(self.db, job_id)))


if __name__ == "__main__":
    unittest.main()

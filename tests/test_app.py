"""Exercise the user workflow with Streamlit's test harness and synthetic sources."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from generation import make_chunks
from companion import buddy_state, get_task, list_tasks, pending_reminder
from storage import connect, get_pages, get_source, load_project, now, source_signature
from test_workflow import sample_pdf


APP = Path(__file__).resolve().parents[1] / "app.py"


def widget(elements, label):
    return next(element for element in elements if element.label == label)


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.environment = patch.dict("os.environ", {"ACADEMICGENT_DATA_DIR": self.temp.name})
        self.environment.start()
        self.app = AppTest.from_file(str(APP)).run(timeout=20)

    def tearDown(self):
        self.environment.stop()
        self.temp.cleanup()

    def assert_clean(self):
        self.assertFalse(self.app.exception, [error.message for error in self.app.exception])
        self.assertFalse(self.app.error, [error.value for error in self.app.error])

    def save_identity(self):
        widget(self.app.text_input, "Nama").set_value("Mahasiswa Uji")
        widget(self.app.text_input, "NIM").set_value("00123")
        widget(self.app.text_input, "Program studi").set_value("Sistem Informasi")
        widget(self.app.button, "Simpan identitas").click().run(timeout=20)
        self.assert_clean()

    def test_pdf_to_candidate_and_revision_restore(self):
        self.save_identity()
        project_id = self.app.session_state["project_id"]
        # AppTest has no upload setter; supply the same UploadedFile interface.
        with patch("streamlit.file_uploader", return_value=SimpleNamespace(name="materi.pdf", getvalue=sample_pdf)):
            self.app.run(timeout=20)
            widget(self.app.button, "Baca PDF").click().run(timeout=20)
        self.assert_clean()
        for position, label in ((1, "229"), (2, "228")):
            widget(self.app.selectbox, "Halaman yang diperiksa").select(position).run(timeout=20)
            widget(self.app.text_input, "Nomor halaman tercetak di buku").set_value(label)
            widget(self.app.checkbox, "Teks dan nomor halaman sudah saya periksa").check()
            widget(self.app.button, "Simpan teks halaman").click().run(timeout=20)
            self.assert_clean()
        widget(self.app.button, "Urutkan dari nomor buku").click().run(timeout=20)
        self.assert_clean()
        db = connect(self.temp.name)
        try:
            pages = get_pages(db, project_id)
            self.assertEqual([page["position"] for page in pages], [2, 1])
            manual = "## Awal\n\nNaskah manual uji.\n"
            widget(self.app.text_area, "Naskah resume").set_value(manual)
            widget(self.app.button, "Simpan naskah").click().run(timeout=20)
            self.assert_clean()
            self.assertEqual(len(self.app.get("download_button")), 3)
            self.assertFalse(self.app.warning)
            chunks = make_chunks(pages)
            payload = {"source_signature": source_signature(get_source(db, project_id), pages), "chunks": chunks}
            results = [dict(chunk, heading="Pembelajaran", paragraphs=[{
                "text": "Ringkasan pembelajaran untuk uji antarmuka.", "evidence": chunk["text"],
            }]) for chunk in chunks]
            with db:
                db.execute("INSERT INTO generation_jobs VALUES (?, ?, 'succeeded', ?, ?, '', ?)",
                           ("ui-fixture", project_id, json.dumps(payload), json.dumps(results), now()))
            self.app.run(timeout=20)
            self.assertTrue(widget(self.app.button, "Terapkan kandidat sebagai revisi baru").disabled)
            widget(self.app.checkbox, "Saya sudah meninjau kandidat dan kutipan pendukungnya").check().run(timeout=20)
            widget(self.app.button, "Terapkan kandidat sebagai revisi baru").click().run(timeout=20)
            self.assert_clean()
            current, revision = load_project(db, project_id)
            self.assertEqual(current["provenance"]["job_id"], "ui-fixture")
            self.assertIn("Ringkasan pembelajaran", widget(self.app.text_area, "Naskah resume").value)
            self.assertEqual(len(self.app.get("download_button")), 4)
            widget(self.app.selectbox, "Revisi").select(2).run(timeout=20)
            widget(self.app.button, "Pulihkan sebagai revisi baru").click().run(timeout=20)
            self.assert_clean()
            current, revision = load_project(db, project_id)
            self.assertEqual(current["content"], manual)
            self.assertEqual(revision, 4)
        finally:
            db.close()

    def test_unsaved_text_and_unavailable_model(self):
        text = "## Catatan\n\nTeks yang ditulis sebelum identitas disimpan.\n"
        widget(self.app.text_area, "Naskah resume").set_value(text).run(timeout=20)
        self.save_identity()
        self.assertEqual(widget(self.app.text_area, "Naskah resume").value, text)
        widget(self.app.button, "Simpan naskah").click().run(timeout=20)
        with patch("generation.installed_models", side_effect=ValueError("Ollama belum berjalan.")):
            widget(self.app.button, "Periksa model lokal").click().run(timeout=20)
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.error[0].value, "Ollama belum berjalan.")
        self.assertEqual(widget(self.app.text_area, "Naskah resume").value, text)
        self.assertEqual(len(self.app.get("download_button")), 3)

    def test_task_and_buddy_workflow(self):
        from datetime import datetime, timedelta
        from companion import ZONES

        widget(self.app.text_input, "Nama tugas").set_value("Kumpulkan resume uji")
        deadline = datetime.now(ZONES["WIB"]) + timedelta(minutes=30)
        widget(self.app.date_input, "Tanggal deadline").set_value(deadline.date())
        widget(self.app.time_input, "Jam deadline").set_value(deadline.time().replace(second=0, microsecond=0))
        widget(self.app.button, "Simpan tugas").click().run(timeout=20)
        self.assert_clean()
        db = connect(self.temp.name)
        try:
            task = list_tasks(db)[0]
            self.assertEqual(task["title"], "Kumpulkan resume uji")
            self.assertIsNotNone(pending_reminder(db))
            widget(self.app.button, "Tunda 15 m").click().run(timeout=20)
            self.assert_clean()
            self.assertIsNone(pending_reminder(db))
            widget(self.app.selectbox, "Kelola tugas").select(task["id"]).run(timeout=20)
            widget(self.app.text_input, "Nama tugas").set_value("Kumpulkan resume final")
            widget(self.app.button, "Simpan tugas").click().run(timeout=20)
            self.assert_clean()
            self.assertEqual(get_task(db, task["id"])["title"], "Kumpulkan resume final")
            widget(self.app.button, "Selesai").click().run(timeout=20)
            self.assert_clean()
            self.assertTrue(get_task(db, task["id"])["completed"])
            self.assertIsNone(pending_reminder(db))
            widget(self.app.button, "Buddy, bantu aku").click().run(timeout=20)
            self.assertEqual(buddy_state(db)["state"], "question")
            widget(self.app.button, "Jalankan pilihan").click().run(timeout=20)
            self.assert_clean()
            self.assertEqual(buddy_state(db)["state"], "focus")
            self.assertIn("Langkah kerja", [item.value for item in self.app.markdown])
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()

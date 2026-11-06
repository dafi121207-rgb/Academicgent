"""Academicgent local resume workspace. Run with streamlit run app.py."""

import copy
import hashlib
import json
import sqlite3
from pathlib import Path

import streamlit as st

from generation import JobRunner, candidate_text, installed_models, latest_job
from pdf_tools import guess_label, inspect_pdf, ocr_languages, ocr_page, preview_page
from resume import PRESET, build_docx, parse_content
from storage import (
    connect, data_directory, get_pages, get_source, install_source, list_projects,
    list_revisions, load_project, save_order, save_page, save_project, source_locator,
    source_signature,
)


@st.cache_data(max_entries=8, show_spinner=False)
def cached_preview(path, digest, position, rotation):
    return preview_page(Path(path), position, rotation)


@st.cache_resource
def runner_for(directory):
    runner = JobRunner(directory)
    runner.recover_expired()
    return runner


def blank_record(recent):
    record = {field: recent.get(field, "") for field in
              ("name", "student_number", "study_program", "lecturer", "course")}
    record.update(title="Resume materi", subtitle="", content="", preset_snapshot=copy.deepcopy(PRESET))
    return record


def editor_key():
    return f"editor-{st.session_state.get('project_id') or 'new'}"


def open_project(db, project_id):
    projects = list_projects(db)
    recent = load_project(db, projects[0][0])[0] if projects else {}
    record, revision = load_project(db, project_id) if project_id else (blank_record(recent), None)
    st.session_state["record"] = record
    st.session_state["revision"] = revision
    st.session_state["project_id"] = project_id
    st.session_state["reset_editor"] = True
    st.session_state["form_epoch"] = st.session_state.get("form_epoch", 0) + 1


def persist(db, record, reset_editor=False):
    previous_editor_key = editor_key()
    editor_buffer = st.session_state.get(editor_key(), record.get("content", ""))
    project_id, revision = save_project(
        db, record, st.session_state["project_id"], st.session_state["revision"],
    )
    st.session_state.update(project_id=project_id, revision=revision, record=record)
    if not reset_editor and editor_key() != previous_editor_key:
        st.session_state[editor_key()] = editor_buffer
    st.session_state["reset_editor"] = reset_editor
    st.session_state["notice"] = f"Proyek disimpan sebagai revisi {revision}."
    st.rerun()


def project_sidebar(db):
    with st.sidebar:
        st.subheader("Proyek")
        projects = list_projects(db)
        names = {pid: f"{title} · r{revision}" for pid, title, revision in projects}
        current = st.session_state["project_id"]
        options = [None, *names]
        selected = st.selectbox("Buka proyek tersimpan", options,
                                index=options.index(current) if current in options else 0,
                                format_func=lambda pid: "Resume baru" if pid is None else names[pid])
        unsaved = st.session_state.get(editor_key(), "") != st.session_state["record"].get("content", "")
        discard = True
        if unsaved:
            discard = st.checkbox("Abaikan perubahan naskah yang belum disimpan")
        if st.button("Buka pilihan", width="stretch", disabled=not discard):
            open_project(db, selected)
            st.rerun()
        st.caption("Simpan identitas dan naskah sebelum berpindah proyek.")
        st.divider()
        st.caption("Preset resume 0.1")
        st.write("A4 · Times New Roman · spasi 1,2")
        st.caption("Bahan, draf, dan riwayat disimpan pada laptop.")


def identity_tab(db):
    record = st.session_state["record"]
    with st.form(f"identity-{st.session_state.get('form_epoch', 0)}"):
        st.subheader("Identitas dan materi")
        left, right = st.columns(2)
        name = left.text_input("Nama", value=record.get("name", ""))
        student_number = right.text_input("NIM", value=record.get("student_number", ""))
        study_program = left.text_input("Program studi", value=record.get("study_program", ""))
        lecturer = right.text_input("Dosen pengampu", value=record.get("lecturer", ""))
        course = st.text_input("Mata kuliah", value=record.get("course", ""))
        title = st.text_input("Judul resume", value=record.get("title", ""))
        subtitle = st.text_input("Topik bab", value=record.get("subtitle", ""))
        if st.form_submit_button("Simpan identitas", type="primary"):
            updated = dict(record, name=name.strip(), student_number=student_number.strip(),
                           study_program=study_program.strip(), lecturer=lecturer.strip(),
                           course=course.strip(), title=title.strip(), subtitle=subtitle.strip())
            updated.setdefault("preset_snapshot", copy.deepcopy(PRESET))
            persist(db, updated)


def sources_tab(db):
    project_id = st.session_state["project_id"]
    st.subheader("Bahan sumber")
    if not project_id:
        st.info("Simpan identitas proyek dahulu, lalu unggah PDF untuk resume ini.")
        return
    source = get_source(db, project_id)
    uploaded = st.file_uploader("PDF materi", type=["pdf"], key=f"pdf-{project_id}",
                                help="Maksimal 50 MB dan 100 halaman. Satu PDF aktif per proyek.")
    replace = False
    if source:
        st.caption(f"Bahan aktif · {source['name']}")
        replace = st.checkbox("Ganti bahan aktif dengan PDF baru", key=f"replace-{project_id}")
    if st.button("Baca PDF", disabled=uploaded is None or (source is not None and not replace)):
        with st.spinner("Membaca halaman PDF…"):
            data = uploaded.getvalue()
            pages = inspect_pdf(data)
            install_source(db, project_id, uploaded.name, data, pages,
                           source["revision"] if source else None)
        st.session_state["notice"] = "PDF tersimpan. Periksa urutan dan teks setiap halaman."
        st.rerun()
    if source is None:
        st.caption("PDF hasil foto dapat dibaca melalui OCR setelah Tesseract dipasang.")
        return

    pages = get_pages(db, project_id)
    selected = [page for page in pages if page["selected"]]
    st.write(f"{len(pages)} halaman · {len(selected)} dipilih · "
             f"{sum(bool(p['reviewed']) for p in selected)} diperiksa")
    with st.expander("Atur urutan dan pilih halaman", expanded=False):
        st.caption("Urutan harus berisi 1 sampai jumlah halaman tanpa angka ganda. "
                   "Nomor PDF tetap mengikuti berkas asli.")
        rows = [{"position": p["position"], "printed_label": p["printed_label"],
                 "reading_order": p["reading_order"], "selected": bool(p["selected"])} for p in pages]
        with st.form(f"order-{project_id}-{source['revision']}"):
            edited = st.data_editor(
                rows, hide_index=True, width="stretch", num_rows="fixed",
                disabled=["position", "printed_label"],
                column_config={
                    "position": st.column_config.NumberColumn("Halaman PDF"),
                    "printed_label": st.column_config.TextColumn("Nomor buku"),
                    "reading_order": st.column_config.NumberColumn("Urutan baca", min_value=1, max_value=len(pages), step=1),
                    "selected": st.column_config.CheckboxColumn("Pakai"),
                },
            )
            if st.form_submit_button("Simpan urutan"):
                save_order(db, project_id, edited, source["revision"])
                st.session_state["notice"] = "Urutan halaman tersimpan."
                st.rerun()
        numeric = all(p["printed_label"].isdigit() for p in pages)
        if st.button("Urutkan dari nomor buku", disabled=not numeric):
            labels = [int(p["printed_label"]) for p in pages]
            if len(set(labels)) != len(labels):
                st.error("Ada nomor buku yang sama. Perbaiki label atau atur urutan secara manual.")
            else:
                sorted_pages = sorted(pages, key=lambda p: int(p["printed_label"]))
                for index, page in enumerate(sorted_pages, 1):
                    page["reading_order"] = index
                save_order(db, project_id, sorted_pages, source["revision"])
                st.rerun()

    page_lookup = {p["position"]: p for p in pages}
    position = st.selectbox(
        "Halaman yang diperiksa", list(page_lookup),
        format_func=lambda pos: f"PDF {pos} · {source_locator(page_lookup[pos])}",
        key=f"position-{project_id}-{source['sha256']}",
    )
    page = page_lookup[position]
    left, right = st.columns(2)
    with left:
        rotation = st.selectbox("Rotasi pratinjau dan OCR", [0, 90, 180, 270], format_func=lambda x: f"{x}°")
        with st.spinner("Menampilkan halaman…"):
            st.image(cached_preview(str(source["path"]), source["sha256"], position, rotation),
                     caption=f"Halaman PDF {position}", width="stretch")
        languages = ocr_languages()
        if languages:
            default = languages.index("ind") if "ind" in languages else 0
            language = st.selectbox("Bahasa OCR", languages, index=default)
            if "ind" not in languages:
                st.caption("Paket bahasa Indonesia belum terpasang. Hasil OCR perlu diperiksa kembali.")
            replace_text = not page["text"].strip()
            if not replace_text:
                replace_text = st.checkbox("Ganti teks halaman ini dengan hasil OCR baru")
            if st.button("OCR halaman ini", disabled=not replace_text):
                with st.spinner("Membaca teks pada foto…"):
                    text = ocr_page(source["path"], position, language, rotation)
                    label = page["printed_label"] or guess_label(text)
                    save_page(db, project_id, position, text, label, False, source["revision"], method="ocr")
                st.session_state["notice"] = "OCR selesai. Koreksi teks lalu tandai sudah diperiksa."
                st.rerun()
            with st.expander("OCR halaman kosong"):
                st.caption("Memproses halaman terpilih yang belum memiliki teks. Setiap hasil langsung disimpan.")
                if st.button("OCR semua halaman kosong"):
                    empty_pages = [p for p in selected if not p["text"].strip()]
                    progress = st.progress(0.0)
                    for index, empty in enumerate(empty_pages):
                        current = get_source(db, project_id)
                        if current["sha256"] != source["sha256"]:
                            raise ValueError("PDF sumber telah diganti. Buka kembali proyek.")
                        latest_page = next(p for p in get_pages(db, project_id) if p["position"] == empty["position"])
                        if latest_page["text"].strip():
                            continue
                        text = ocr_page(source["path"], empty["position"], language, rotation)
                        save_page(db, project_id, empty["position"], text,
                                  empty["printed_label"] or guess_label(text), False,
                                  current["revision"], method="ocr")
                        progress.progress((index + 1) / len(empty_pages))
                    st.session_state["notice"] = "OCR selesai. Periksa dan koreksi hasil setiap halaman."
                    st.rerun()
        else:
            st.info("Pasang Tesseract dan paket bahasa Indonesia untuk membaca scan. "
                    "Kamu juga bisa mengetik atau menempelkan teks halaman di editor.")
    with right:
        with st.form(f"page-{project_id}-{source['revision']}-{position}"):
            label = st.text_input("Nomor halaman tercetak di buku", value=page["printed_label"],
                                  help="Boleh angka, Romawi, atau kosong jika tidak diketahui.")
            text = st.text_area("Teks halaman", value=page["text"], height=490)
            reviewed = st.checkbox("Teks dan nomor halaman sudah saya periksa", value=bool(page["reviewed"]))
            if st.form_submit_button("Simpan teks halaman", type="primary"):
                save_page(db, project_id, position, text, label, reviewed, source["revision"])
                st.session_state["notice"] = f"Halaman PDF {position} tersimpan."
                st.rerun()


@st.fragment(run_every="3s")
def job_status(directory, project_id):
    runner_for(directory).recover_expired()
    db = connect(directory)
    try:
        job = latest_job(db, project_id)
        if not job:
            return
        labels = {"running": "Menyusun ringkasan", "cancelling": "Menunggu pembatalan",
                  "succeeded": "Kandidat selesai", "failed": "Proses perlu dilanjutkan",
                  "cancelled": "Proses dibatalkan", "interrupted": "Proses terhenti"}
        completed, total = len(job["results"]), len(job["input"]["chunks"])
        st.progress(completed / total, text=f"{labels[job['status']]} · {completed}/{total} bagian")
        if job["error"]:
            st.warning(job["error"])
        if job["status"] == "running" and st.button("Batalkan generasi", key=f"cancel-{job['id']}"):
            runner_for(directory).cancel(job["id"])
            st.rerun(scope="fragment")
        if job["status"] == "cancelling":
            st.caption("Permintaan AI aktif ditunggu selesai. Bagian berikutnya akan dihentikan.")
        if job["status"] in ("failed", "cancelled", "interrupted"):
            source = get_source(db, project_id)
            compatible = source_signature(source, get_pages(db, project_id)) == job["input"]["source_signature"]
            if st.button("Lanjutkan dari bagian terakhir", disabled=not compatible, key=f"resume-{job['id']}"):
                runner_for(directory).resume(job["id"])
                st.rerun(scope="fragment")
            if not compatible:
                st.caption("Bahan berubah. Buat proses baru dari sumber terkini.")
        if st.button("Tampilkan kandidat terbaru", key=f"refresh-{job['id']}"):
            st.rerun()
    except (ValueError, OSError, sqlite3.Error) as error:
        st.error(str(error))
    finally:
        db.close()


def drafting_tab(db):
    project_id = st.session_state["project_id"]
    record = st.session_state["record"]
    st.subheader("Susun resume")
    if project_id:
        source, pages = get_source(db, project_id), get_pages(db, project_id)
        with st.expander("Buat kandidat dengan AI lokal", expanded=not record.get("content")):
            st.caption("Ollama merangkum bahan yang telah kamu periksa. Hasilnya menjadi kandidat untuk ditinjau.")
            port = st.number_input("Port Ollama", min_value=1024, max_value=65535, value=11434, step=1)
            if st.button("Periksa model lokal"):
                try:
                    st.session_state["model_options"] = installed_models(port)
                    st.session_state["model_port"] = port
                except ValueError as error:
                    st.session_state["model_options"] = []
                    st.error(str(error))
            models = st.session_state.get("model_options", []) if st.session_state.get("model_port") == port else []
            if models:
                model = st.selectbox("Model", models)
                detail = st.select_slider("Panjang ringkasan", ["singkat", "sedang", "rinci"], value="sedang")
                ready = source is not None and any(p["selected"] for p in pages)
                ready = ready and all(p["reviewed"] and p["text"].strip() for p in pages if p["selected"])
                if not ready:
                    st.caption("Pilih halaman sumber dan tandai setiap teksnya sudah diperiksa.")
                if st.button("Buat kandidat resume", type="primary", disabled=not ready):
                    try:
                        runner_for(str(data_directory(db))).start(
                            project_id, source_signature(source, pages), pages, model, port, detail,
                            st.session_state["revision"],
                        )
                        st.rerun()
                    except (ValueError, OSError, sqlite3.Error) as error:
                        st.error(str(error))
            else:
                st.caption("Jalankan Ollama dan unduh model lokal, lalu tekan Periksa model lokal. "
                           "Editor manual dan ekspor Word sudah dapat digunakan.")
            job_status(str(data_directory(db)), project_id)

        job = latest_job(db, project_id)
        if job and job["results"]:
            with st.expander("Tinjau kandidat dan bukti sumber", expanded=False):
                st.text(candidate_text(job))
                for result in job["results"]:
                    for paragraph in result["paragraphs"]:
                        st.caption(f"PDF {result['position']} · {result['locator']}")
                        st.text(paragraph["evidence"])
                same_source = source_signature(source, pages) == job["input"]["source_signature"]
                unsaved = st.session_state.get(editor_key(), "") != record.get("content", "")
                if not same_source:
                    st.warning("Sumber berubah setelah kandidat dibuat. Buat kandidat baru.")
                if unsaved:
                    st.caption("Simpan perubahan naskah sebelum menerapkan kandidat.")
                acknowledge = st.checkbox("Saya sudah meninjau kandidat dan kutipan pendukungnya",
                                          key=f"review-{job['id']}-{len(job['results'])}")
                if st.button("Terapkan kandidat sebagai revisi baru",
                             disabled=not same_source or unsaved or not acknowledge or job["status"] in ("running", "cancelling")):
                    text = candidate_text(job)
                    provenance = {"job_id": job["id"], "source_signature": job["input"]["source_signature"],
                                  "source_name": source["name"], "results": job["results"],
                                  "content_sha256": hashlib.sha256(text.encode()).hexdigest(),
                                  "partial": job["status"] != "succeeded"}
                    persist(db, dict(record, content=text, provenance=provenance), reset_editor=True)

    st.caption("Awali bagian dengan ##, subbagian dengan ###, dan poin dengan -. "
               "Pisahkan paragraf dengan baris kosong. Penomoran dibuat otomatis.")
    content = st.text_area("Naskah resume", height=420, key=editor_key())
    st.caption(f"{len(content.split())} kata · {len(parse_content(content))} blok")
    if st.button("Simpan naskah", type="primary"):
        persist(db, dict(record, content=content))
    if project_id:
        with st.expander("Riwayat revisi"):
            history = list_revisions(db, project_id)
            choice = st.selectbox("Revisi", [r[0] for r in history], key=f"history-{project_id}")
            historical, _ = load_project(db, project_id, choice)
            st.text(historical.get("content", "")[:3000])
            if st.button("Pulihkan sebagai revisi baru", disabled=choice == st.session_state["revision"]):
                persist(db, historical, reset_editor=True)


def export_tab(db):
    record = st.session_state["record"]
    project_id = st.session_state["project_id"]
    st.subheader("Ekspor Word")
    if not project_id or not record.get("content", "").strip():
        st.info("Simpan identitas dan naskah resume untuk menyiapkan Word.")
        return
    missing = [label for key, label in [("name", "nama"), ("student_number", "NIM"),
               ("study_program", "program studi")] if not record.get(key, "").strip()]
    if missing:
        st.warning("Lengkapi " + ", ".join(missing) + " pada tab Identitas.")
        return
    unsaved = st.session_state.get(editor_key(), "") != record["content"]
    if unsaved:
        st.warning("Ada perubahan naskah yang belum disimpan. Unduhan menggunakan revisi tersimpan.")
    st.caption(f"Dokumen dari revisi {st.session_state['revision']}. Periksa kembali halaman di Microsoft Word.")
    provenance = record.get("provenance")
    if provenance:
        if provenance["partial"]:
            st.warning("Draf ini menggunakan kandidat sebagian. Lengkapi bagian sumber yang belum dirangkum.")
        signature = source_signature(get_source(db, project_id), get_pages(db, project_id))
        if signature != provenance["source_signature"]:
            st.warning("Bahan telah berubah sejak draf dibuat. Tinjau ulang rujukan halaman.")
        if hashlib.sha256(record["content"].encode()).hexdigest() != provenance["content_sha256"]:
            st.caption("Naskah telah disunting. Cocokkan kembali bukti sumber pada peta kandidat.")
        st.download_button("Unduh peta sumber kandidat", json.dumps(provenance, ensure_ascii=False, indent=2),
                           file_name="peta_sumber.json", mime="application/json")
    document = build_docx(record)
    st.download_button("Unduh resume Word", document, file_name="resume_materi.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary")
    st.download_button("Unduh naskah teks", record["content"], file_name="resume_materi.txt", mime="text/plain")
    st.download_button("Unduh data revisi", json.dumps(record, ensure_ascii=False, indent=2),
                       file_name="resume_revisi.json", mime="application/json")
    with st.expander("Lihat isi yang akan diekspor"):
        st.text(record["content"])


def main():
    st.set_page_config(page_title="Academicgent", layout="wide")
    st.title("Academicgent")
    st.caption("Baca bahan, susun resume, dan simpan Word.")
    db = connect()
    try:
        if "record" not in st.session_state:
            open_project(db, None)
        if st.session_state.pop("reset_editor", False) or editor_key() not in st.session_state:
            st.session_state[editor_key()] = st.session_state["record"].get("content", "")
        if notice := st.session_state.pop("notice", None):
            st.success(notice)
        project_sidebar(db)
        identity, sources, drafting, export = st.tabs(["Identitas", "Bahan PDF", "Draf resume", "Ekspor"])
        with identity:
            identity_tab(db)
        with sources:
            try:
                sources_tab(db)
            except (ValueError, OSError, sqlite3.Error) as error:
                st.error(str(error))
        with drafting:
            drafting_tab(db)
        with export:
            export_tab(db)
    except (ValueError, OSError, sqlite3.Error) as error:
        st.error(str(error))
        st.caption("Perubahan yang sudah tersimpan dapat dibuka kembali dari daftar proyek.")
    finally:
        db.close()


main()

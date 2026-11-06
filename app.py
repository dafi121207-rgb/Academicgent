"""Run with: streamlit run app.py"""

import streamlit as st

from resume import build_docx, connect, list_projects, load_project, save_project


st.set_page_config(page_title="Academicgent", page_icon="📄", layout="centered")
st.title("Academicgent")
st.caption("Resume materi ke Word")

db = connect()
projects = list_projects(db)
recent = load_project(db, projects[0][0])[0] if projects else {}
pending_project = st.session_state.pop("open_after_save", None)
if pending_project:
    st.session_state["project_selection"] = pending_project
selection = st.selectbox(
    "Proyek",
    [None] + [row[0] for row in projects],
    format_func=lambda project_id: "Resume baru" if project_id is None else next(
        f"{title} · revisi {revision}" for pid, title, revision in projects if pid == project_id
    ),
    key="project_selection",
)
loaded = load_project(db, selection) if selection else None
record, revision = loaded if loaded else ({}, None)

with st.form(f"resume-{selection or 'new'}"):
    st.subheader("Identitas dan materi")
    name = st.text_input("Nama", value=record.get("name", recent.get("name", "")))
    student_number = st.text_input("NIM", value=record.get("student_number", recent.get("student_number", "")))
    study_program = st.text_input("Program studi", value=record.get("study_program", recent.get("study_program", "")))
    lecturer = st.text_input("Dosen pengampu", value=record.get("lecturer", recent.get("lecturer", "")))
    course = st.text_input("Mata kuliah", value=record.get("course", recent.get("course", "")))
    title = st.text_input("Judul", value=record.get("title", "RESUME MATERI BAB 12"))
    subtitle = st.text_input("Topik bab", value=record.get("subtitle", ""))
    st.subheader("Isi resume")
    st.caption("Awali bagian dengan ## dan subbagian dengan ###. Pisahkan paragraf dengan baris kosong. Gunakan - untuk poin.")
    content = st.text_area(
        "Naskah",
        value=record.get("content", "## Pendahuluan (hlm. 227–230)\n\nTulis ringkasan di sini."),
        height=360,
    )
    submitted = st.form_submit_button("Simpan dan siapkan Word", type="primary")

if submitted:
    payload = {
        "name": name.strip(), "student_number": student_number.strip(),
        "study_program": study_program.strip(), "lecturer": lecturer.strip(),
        "course": course.strip(), "title": title.strip(), "subtitle": subtitle.strip(),
        "content": content.strip(),
    }
    missing = [key for key in ("name", "student_number", "study_program", "title", "content") if not payload[key]]
    if missing:
        st.error("Lengkapi nama, NIM, program studi, judul, dan isi resume.")
    else:
        try:
            document = build_docx(payload)
            project_id, saved_revision = save_project(db, payload, selection, revision)
            st.session_state["download"] = (project_id, saved_revision, document)
            st.session_state["open_after_save"] = project_id
            st.session_state["saved_revision"] = saved_revision
            st.rerun()
        except ValueError as error:
            st.error(str(error))

download = st.session_state.get("download")
if download and download[0] == selection:
    st.success(f"Tersimpan sebagai revisi {st.session_state['saved_revision']}.")
    st.download_button(
        "Unduh Word",
        download[2],
        file_name="resume_materi.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

"""Streamlit companion and task forms. Desktop uses the same persisted state."""

import base64
import html
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, time as clock
from functools import lru_cache

import streamlit as st

from companion import (
    ASSET_DIR, STATES, ZONES, buddy_state, deadline_label, delete_task, ensure_reminders,
    get_task, list_tasks, local_deadline, pending_reminder, publish, respond_reminder,
    save_settings, save_task, settings, time_left,
)
from storage import connect, list_projects


@lru_cache(maxsize=6)
def image_uri(state):
    return "data:image/jpeg;base64," + base64.b64encode((ASSET_DIR / STATES[state][1]).read_bytes()).decode()


@contextmanager
def activity(db, message, project_id=None, state="working"):
    publish(db, state, message, project_id, seconds=180)
    slot = st.empty()
    # Safe markup only: messages are escaped, images are bundled local assets.
    slot.html(f'''<aside style="position:fixed;right:20px;bottom:20px;z-index:1002;
        max-width:min(310px,90vw);padding:14px;background:#fff;color:#182B25;
        border:1px solid #CBD8D1;border-radius:12px;box-shadow:0 8px 28px #0002"
        role="status" aria-live="polite"><img alt="{STATES[state][0]}" src="{image_uri(state)}"
        style="width:92px;height:auto;float:right;margin:0 0 8px 12px">
        <strong>{STATES[state][0]}</strong><p>{html.escape(message)}</p></aside>''')
    try:
        yield
    except Exception as error:
        publish(db, "error", str(error), project_id, seconds=90)
        raise
    else:
        publish(db, "success", "Proses selesai. Hasilnya siap diperiksa.", project_id, seconds=25)
    finally:
        slot.empty()


BUDDY_CSS = """
<style>
div.st-key-meme_buddy {
 position:fixed;right:22px;bottom:18px;width:280px;max-height:78vh;overflow:auto;
 z-index:990;background:#FFFFFF;color:#182B25;padding:14px;
 border:1px solid #CBD8D1;border-radius:14px;box-shadow:0 8px 28px #152D2526;
}
div.st-key-meme_buddy button:focus-visible {outline:3px solid #245644;outline-offset:2px}
div.st-key-meme_buddy [data-testid="stHorizontalBlock"] {flex-wrap:nowrap}
div.st-key-meme_buddy [data-testid="stColumn"] {min-width:0 !important;flex-basis:0 !important}
div.st-key-meme_buddy ::selection {background:#CFE4D8;color:#182B25}
div.st-key-meme_buddy [data-testid="stImage"] img {object-fit:contain}
.ag-meme {display:block;width:128px;height:auto;max-height:154px;object-fit:contain;margin:0 auto 10px}
.ag-working {animation:ag-breathe 2.4s ease-in-out infinite}
@keyframes ag-breathe {50% {transform:translateY(-4px) rotate(-1deg)}}
@media (prefers-reduced-motion:reduce) {.ag-working {animation:none}}
@media (max-width:640px) {
 div.st-key-meme_buddy {right:10px;bottom:10px;width:250px;max-width:calc(100vw - 20px);max-height:65vh;padding:10px}
 .ag-meme {width:86px;max-height:100px}
}
</style>
"""


@st.fragment(run_every="3s")
def render_buddy(directory, project_id=None):
    db = connect(directory)
    try:
        prefs = settings(db)
        if not prefs["web_enabled"]:
            return
        ensure_reminders(db)
        desktop_active = time.time() - prefs["desktop_heartbeat"] < 12
        reminder = None if desktop_active else pending_reminder(db)
        view = reminder or buddy_state(db, project_id)
        if reminder and st.session_state.get("buddy_notification") != reminder["notification_id"]:
            st.session_state["buddy_notification"] = reminder["notification_id"]
            st.session_state["buddy_small"] = False
        state = view["state"]
        st.html(BUDDY_CSS)
        with st.container(key="meme_buddy"):
            small = st.session_state.get("buddy_small", False)
            col1, col2 = st.columns([3, 2])
            col1.caption("Academicgent buddy")
            if col2.button("Buka" if small else "Kecilkan", key="buddy_size", help="Ubah ukuran buddy"):
                st.session_state["buddy_small"] = not small
                st.rerun(scope="fragment")
            if small:
                st.caption(STATES[state][0])
            else:
                motion = " ag-working" if state == "working" and prefs["animations"] else ""
                st.html(f'<img class="ag-meme{motion}" src="{image_uri(state)}" alt="{STATES[state][0]}">')
                st.write(STATES[state][0])
                st.text(view["message"])
                if reminder:
                    first, second = st.columns(2)
                    action = None
                    if first.button("Tunda 15 m", key="buddy_snooze"):
                        action = "snooze"
                    if second.button("Selesai", key="buddy_done", help="Tandai tugas sudah selesai"):
                        action = "done"
                    if st.button("Tutup pengingat ini", key="buddy_dismiss", width="stretch"):
                        action = "dismiss"
                    if action:
                        respond_reminder(db, reminder["notification_id"], action)
                        st.rerun()
                elif desktop_active:
                    st.caption("Pop-up deadline aktif di buddy desktop.")
    except (ValueError, OSError, sqlite3.Error) as error:
        st.warning(f"Buddy: {error}")
    finally:
        db.close()


def draft_assistant(db, record, pages, project_id):
    with st.expander("Buddy bantu merencanakan dan mengoreksi"):
        if st.button("Buddy, bantu aku"):
            st.session_state["buddy_question_open"] = True
            publish(db, "question", "Mau menyusun langkah kerja atau memeriksa draf yang ada? Pilih di panel bantuan.", project_id, seconds=120)
        if st.session_state.get("buddy_question_open"):
            choice = st.radio("Mau dibantu apa?", ["Susun langkah kerja", "Periksa draf"], horizontal=True)
            if st.button("Jalankan pilihan"):
                publish(db, "focus", "Ijin kompe. Kita cek langkah dan bagian yang perlu dibereskan.", project_id, seconds=120)
                selected = [p for p in pages if p["selected"]]
                if choice == "Susun langkah kerja":
                    steps = []
                    if not project_id:
                        steps.append("Simpan identitas dan judul proyek.")
                    if not selected:
                        steps.append("Unggah PDF dan pilih halaman untuk materi ini.")
                    else:
                        remaining = sum(not p["reviewed"] for p in selected)
                        steps.append(f"Cek urutan {len(selected)} halaman; {remaining} halaman belum ditandai diperiksa.")
                    steps += ["Susun bagian utama dari bahan yang sudah diperiksa.",
                              "Tulis resume atau buat kandidat Ollama, lalu cocokkan isi dan bukti sumber.",
                              "Simpan naskah dan ekspor Word. Periksa hasil sebelum mengumpulkan."]
                    st.session_state["buddy_report"] = ("Langkah kerja", steps)
                else:
                    text = record.get("content", "")
                    checks = []
                    if not text.strip():
                        checks.append("Naskah masih kosong. Tulis atau terapkan kandidat terlebih dahulu.")
                    if text.strip() and not any(line.startswith("## ") for line in text.splitlines()):
                        checks.append("Belum ada judul bagian. Gunakan ## untuk membagi isi resume.")
                    if any(not record.get(key, "").strip() for key in ("name", "student_number", "study_program")):
                        checks.append("Lengkapi nama, NIM, dan program studi sebelum ekspor.")
                    if any(not p["reviewed"] for p in selected):
                        checks.append("Ada teks sumber yang belum ditandai diperiksa.")
                    if any(marker in text.lower() for marker in ("[isi", "todo", "[tambahkan")):
                        checks.append("Ada penanda isi sementara yang perlu dilengkapi.")
                    if not checks:
                        checks.append("Pemeriksaan struktur dasar tidak menemukan bagian wajib yang kosong.")
                    checks.append("Baca ulang makna, angka, dan rujukan terhadap sumber. Pemeriksaan ini tidak memverifikasi kebenaran isi.")
                    st.session_state["buddy_report"] = ("Catatan pemeriksaan", checks)
            if report := st.session_state.get("buddy_report"):
                st.write(report[0])
                for step in report[1]:
                    st.write("- " + step)
                st.caption("Bantuan langkah dan pemeriksaan struktur lokal; bukan penilaian isi oleh model AI.")


def tasks_tab(db):
    st.subheader("Tugas dan deadline")
    st.caption("Pengingat muncul saat buddy berjalan. Waktu dipilih secara eksplisit agar deadline tidak bergeser.")
    prefs = settings(db)
    with st.expander("Pengaturan buddy"):
        with st.form("buddy_preferences"):
            web = st.checkbox("Tampilkan buddy di aplikasi", value=prefs["web_enabled"])
            reminders = st.checkbox("Aktifkan pengingat deadline", value=prefs["reminders_enabled"])
            animations = st.checkbox("Animasi ringan saat bekerja", value=prefs["animations"])
            if st.form_submit_button("Simpan pengaturan buddy"):
                save_settings(db, web_enabled=web, reminders_enabled=reminders, animations=animations)
                st.rerun()
        if prefs["quiet_until"] > time.time():
            st.info("Pengingat sedang dijeda sementara.")
            if st.button("Aktifkan lagi sekarang"):
                save_settings(db, quiet_until=0)
                st.rerun()
        elif st.button("Jeda semua pengingat 1 jam"):
            save_settings(db, quiet_until=time.time() + 3600)
            st.rerun()
        st.caption("Jalankan start_buddy.bat untuk buddy di atas jendela desktop. Tutup buddy melalui menu Keluar untuk menghentikannya.")

    include_completed = st.checkbox("Tampilkan tugas selesai")
    tasks = list_tasks(db, include_completed)
    if tasks:
        st.dataframe([{"Tugas": t["title"], "Deadline": deadline_label(t),
                       "Status": "Selesai" if t["completed"] else time_left(t),
                       "Pengingat": "Aktif" if t["reminders_enabled"] else "Mati"} for t in tasks],
                     hide_index=True, width="stretch")
    else:
        st.info("Belum ada tugas pada daftar ini. Tambahkan deadline pertamamu di bawah.")
    names = {task["id"]: task["title"] for task in tasks}
    selected = st.selectbox("Kelola tugas", [None, *names], format_func=lambda key: "Tambah tugas baru" if key is None else names[key])
    snapshot = st.session_state.get("task_snapshot")
    if not snapshot or snapshot.get("id") != selected:
        snapshot = get_task(db, selected) if selected else {"id": None}
        st.session_state["task_snapshot"] = snapshot
    if selected and st.button("Muat ulang tugas"):
        st.session_state.pop("task_snapshot", None)
        st.session_state["task_form_epoch"] = st.session_state.get("task_form_epoch", 0) + 1
        st.rerun()
    zone_name = snapshot.get("timezone", "WIB")
    due = datetime.fromtimestamp(snapshot["due_at"], ZONES[zone_name]) if selected else datetime.now(ZONES[zone_name]) + timedelta(days=1)
    projects = {pid: title for pid, title, _ in list_projects(db)}
    with st.form(f"task-{selected}-{st.session_state.get('task_form_epoch', 0)}", clear_on_submit=selected is None):
        title = st.text_input("Nama tugas", value=snapshot.get("title", ""), max_chars=160)
        first, second, third = st.columns([2, 2, 1])
        day = first.date_input("Tanggal deadline", value=due.date())
        due_time = second.time_input("Jam deadline", value=due.timetz().replace(tzinfo=None) if selected else clock(23, 59), step=60)
        zone = third.selectbox("Zona waktu", list(ZONES), index=list(ZONES).index(zone_name))
        lead = st.selectbox("Mulai ingatkan", [60, 180, 360, 720, 1440, 2880, 10080],
                            index=[60, 180, 360, 720, 1440, 2880, 10080].index(snapshot.get("lead_minutes", 1440)),
                            format_func=lambda value: f"{value // 60} jam sebelumnya" if value < 1440 else f"{value // 1440} hari sebelumnya")
        options = [None, *projects]
        project = st.selectbox("Terkait proyek", options,
                               index=options.index(snapshot.get("project_id")) if snapshot.get("project_id") in options else 0,
                               format_func=lambda key: "Tugas umum" if key is None else projects[key])
        note = st.text_area("Catatan tugas", value=snapshot.get("note", ""), max_chars=2000, height=80)
        completed = st.checkbox("Tugas sudah selesai", value=bool(snapshot.get("completed", False)))
        enabled = st.checkbox("Ingatkan tugas ini", value=bool(snapshot.get("reminders_enabled", True)))
        if st.form_submit_button("Simpan tugas", type="primary"):
            try:
                save_task(db, title, local_deadline(day, due_time, zone), zone, lead, note, project,
                          completed, enabled, selected, snapshot.get("revision"))
                st.session_state.pop("task_snapshot", None)
                st.session_state["task_form_epoch"] = st.session_state.get("task_form_epoch", 0) + 1
                st.session_state["notice"] = "Tugas dan deadline tersimpan."
                publish(db, "success", "Deadline tersimpan. Aku ingatkan sesuai jadwal yang kamu pilih.")
                st.rerun()
            except (ValueError, sqlite3.Error) as error:
                publish(db, "error", str(error), seconds=60)
                st.error(str(error))
    if selected:
        with st.expander("Hapus tugas"):
            confirm = st.checkbox("Hapus tugas ini beserta pengingatnya")
            if st.button("Hapus tugas", disabled=not confirm):
                delete_task(db, selected, snapshot["revision"])
                st.session_state.pop("task_snapshot", None)
                st.rerun()

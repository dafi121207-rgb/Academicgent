"""Shared meme states and durable, offline deadline reminders for web and desktop."""

import json
import math
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from storage import now


ASSET_DIR = Path(__file__).parent / "assets" / "buddy"
STATES = {
    "working": ("Proses verifikasi", "working.jpg"),
    "success": ("Verifikasi berhasil", "success.jpg"),
    "error": ("Verifikasi gagal", "error.jpg"),
    "focus": ("Ijin kompe", "focus.jpg"),
    "question": ("Jarvis bertanya", "question.jpg"),
    "deadline": ("Deadline sudah dekat, kid", "deadline.jpg"),
}
ZONES = {"WIB": timezone(timedelta(hours=7)), "WITA": timezone(timedelta(hours=8)),
         "WIT": timezone(timedelta(hours=9))}
DEFAULTS = {"web_enabled": True, "reminders_enabled": True, "animations": True,
            "quiet_until": 0, "desktop_heartbeat": 0, "desktop_topmost": True}


def settings(db):
    return {**DEFAULTS, **{key: json.loads(value) for key, value in
                          db.execute("SELECT key, value FROM buddy_settings")}}


def save_settings(db, **values):
    if not set(values) <= set(DEFAULTS):
        raise ValueError("Pengaturan buddy tidak dikenal.")
    with db:
        db.executemany("INSERT INTO buddy_settings VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                       [(key, json.dumps(value)) for key, value in values.items()])


def publish(db, state, message, project_id=None, seconds=30, at=None):
    if state not in STATES:
        raise ValueError("Status buddy tidak dikenal.")
    at = time.time() if at is None else at
    with db:
        db.execute("DELETE FROM buddy_events WHERE expires_at < ?", (at,))
        db.execute("INSERT INTO buddy_events(state,message,project_id,expires_at) VALUES (?,?,?,?)",
                   (state, str(message)[:500], project_id, at + seconds))


def local_deadline(day, clock, zone="WIB"):
    if zone not in ZONES:
        raise ValueError("Pilih WIB, WITA, atau WIT.")
    return datetime.combine(day, clock, tzinfo=ZONES[zone]).timestamp()


def deadline_label(task):
    value = datetime.fromtimestamp(task["due_at"], ZONES[task["timezone"]])
    return value.strftime("%d/%m/%Y %H:%M") + " " + task["timezone"]


def time_left(task, at=None):
    seconds = task["due_at"] - (time.time() if at is None else at)
    minutes = math.ceil(abs(seconds) / 60)
    if minutes < 60:
        value = f"{max(1, minutes)} menit"
    elif minutes < 1440:
        value = f"{minutes // 60} jam {minutes % 60} menit"
    else:
        value = f"{minutes // 1440} hari {(minutes % 1440) // 60} jam"
    return f"Terlambat {value}" if seconds < 0 else f"Sisa {value}"


TASK_COLUMNS = "id,title,note,project_id,due_at,timezone,lead_minutes,completed,reminders_enabled,next_reminder_at,revision,updated_at"


def task_from_row(row):
    return dict(zip(TASK_COLUMNS.split(","), row)) if row else None


def get_task(db, task_id):
    return task_from_row(db.execute(f"SELECT {TASK_COLUMNS} FROM tasks WHERE id=?", (task_id,)).fetchone())


def list_tasks(db, include_completed=False):
    rows = db.execute(f"SELECT {TASK_COLUMNS} FROM tasks " +
                      ("" if include_completed else "WHERE completed=0 ") + "ORDER BY completed,due_at,id").fetchall()
    return [task_from_row(row) for row in rows]


def next_milestone(due_at, lead_minutes, at):
    moments = {due_at - lead_minutes * 60, due_at - min(60, lead_minutes) * 60, due_at}
    return next(iter(sorted(moment for moment in moments if moment > at)), None)


def save_task(db, title, due_at, zone="WIB", lead_minutes=1440, note="", project_id=None,
              completed=False, reminders_enabled=True, task_id=None, expected_revision=None):
    title, note = title.strip(), note.strip()
    if not title or len(title) > 160 or len(note) > 2000:
        raise ValueError("Isi nama tugas (maksimal 160 karakter) dan catatan maksimal 2.000 karakter.")
    if zone not in ZONES or not math.isfinite(due_at) or not 0 <= due_at <= 4_102_444_800:
        raise ValueError("Tanggal atau zona waktu tidak valid.")
    if not isinstance(lead_minutes, int) or not 1 <= lead_minutes <= 10080:
        raise ValueError("Pengingat awal harus 1 menit sampai 7 hari sebelum deadline.")
    next_at = None if completed or not reminders_enabled else due_at - lead_minutes * 60
    values = (title, note, project_id, due_at, zone, lead_minutes, int(completed),
              int(reminders_enabled), next_at)
    with db:
        if task_id is None:
            task_id = uuid4().hex
            db.execute("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,1,?)", (task_id, *values, now()))
        else:
            cursor = db.execute("UPDATE tasks SET title=?,note=?,project_id=?,due_at=?,timezone=?,lead_minutes=?,"
                                "completed=?,reminders_enabled=?,next_reminder_at=?,revision=revision+1,updated_at=? "
                                "WHERE id=? AND revision=?", (*values, now(), task_id, expected_revision))
            if cursor.rowcount != 1:
                raise ValueError("Tugas berubah di jendela lain. Buka ulang tugas sebelum menyimpan.")
            db.execute("UPDATE task_notifications SET status='cancelled' WHERE task_id=? AND status='pending'", (task_id,))
    return task_id


def delete_task(db, task_id, revision):
    with db:
        cursor = db.execute("DELETE FROM tasks WHERE id=? AND revision=?", (task_id, revision))
        if cursor.rowcount != 1:
            raise ValueError("Tugas sudah berubah. Muat ulang daftar sebelum menghapus.")


def ensure_reminders(db, at=None):
    """Catch up once after downtime; a pending message coalesces later milestones."""
    at = time.time() if at is None else at
    prefs = settings(db)
    if not prefs["reminders_enabled"] or prefs["quiet_until"] > at:
        return
    with db:
        # Acquire the writer lock before reading candidates so two surfaces cannot claim twice.
        db.execute("UPDATE tasks SET next_reminder_at=next_reminder_at WHERE 0")
        for task in list_tasks(db):
            if not task["reminders_enabled"] or task["next_reminder_at"] is None or task["next_reminder_at"] > at:
                continue
            cursor = db.execute("INSERT OR IGNORE INTO task_notifications VALUES (?,?,?,'pending',?,?)",
                                (uuid4().hex, task["id"], task["revision"], at, at))
            if cursor.rowcount:
                db.execute("UPDATE tasks SET next_reminder_at=? WHERE id=?",
                           (next_milestone(task["due_at"], task["lead_minutes"], at), task["id"]))


def pending_reminder(db, at=None):
    at = time.time() if at is None else at
    prefs = settings(db)
    if not prefs["reminders_enabled"] or prefs["quiet_until"] > at:
        return None
    row = db.execute("SELECT n.id,n.task_id FROM task_notifications n JOIN tasks t ON n.task_id=t.id "
                     "WHERE n.status='pending' AND n.not_before<=? AND t.completed=0 "
                     "AND t.reminders_enabled=1 AND n.task_revision=t.revision ORDER BY t.due_at,n.created_at LIMIT 1", (at,)).fetchone()
    if not row:
        return None
    task = get_task(db, row[1])
    return {"notification_id": row[0], "task": task, "state": "deadline",
            "message": f"{task['title']}\n{time_left(task, at)}. Deadline {deadline_label(task)}."}


def respond_reminder(db, notification_id, action, at=None):
    if action not in ("dismiss", "snooze", "done"):
        raise ValueError("Tindakan pengingat tidak dikenal.")
    at = time.time() if at is None else at
    with db:
        db.execute("UPDATE tasks SET next_reminder_at=next_reminder_at WHERE 0")
        row = db.execute("SELECT task_id,task_revision FROM task_notifications WHERE id=? AND status='pending'",
                         (notification_id,)).fetchone()
        task = get_task(db, row[0]) if row else None
        if not task or task["completed"] or task["revision"] != row[1]:
            return False
        if action == "snooze":
            db.execute("UPDATE task_notifications SET not_before=? WHERE id=?", (at + 15 * 60, notification_id))
        else:
            db.execute("UPDATE task_notifications SET status='acknowledged' WHERE id=?", (notification_id,))
            next_at = None if action == "done" else next_milestone(task["due_at"], task["lead_minutes"], at)
            db.execute("UPDATE tasks SET completed=?,next_reminder_at=?,revision=revision+?,updated_at=? WHERE id=?",
                       (int(action == "done"), next_at, int(action == "done"), now(), task["id"]))
    if action == "done":
        publish(db, "success", f"Tugas {task['title']} selesai. Mantap, satu tugas beres!", seconds=25, at=at)
    return True


def buddy_state(db, project_id=None, at=None):
    at = time.time() if at is None else at
    args = (at, project_id, project_id)
    event = db.execute("SELECT state,message,id FROM buddy_events WHERE expires_at>? "
                       "AND (? IS NULL OR project_id IS NULL OR project_id=?) ORDER BY id DESC LIMIT 1", args).fetchone()
    if event and event[0] == "error":
        return {"state": event[0], "message": event[1], "key": f"event-{event[2]}"}
    job = db.execute("SELECT j.id,j.status,j.updated_at,j.results_json,j.input_json,p.title,p.payload FROM generation_jobs j "
                     "JOIN projects p ON p.id=j.project_id WHERE (? IS NULL OR j.project_id=?) "
                     "ORDER BY (j.status IN ('running','cancelling')) DESC,j.updated_at DESC LIMIT 1",
                     (project_id, project_id)).fetchone()
    if job and job[1] in ("running", "cancelling"):
        age = at - datetime.fromisoformat(job[2]).timestamp()
        state = "working" if age < 600 else "error"
        done, total = len(json.loads(job[3])), len(json.loads(job[4])["chunks"])
        message = f"{job[5]} · {done}/{total} bagian. "
        message += "Menunggu bagian aktif sebelum berhenti." if job[1] == "cancelling" else "Sedang menyusun kandidat resume."
        if state == "error":
            message = "Proses AI terhenti. Buka proyek untuk melanjutkan bagian yang tersimpan."
        return {"state": state, "message": message, "key": f"job-{job[0]}-{job[1]}"}
    if event:
        return {"state": event[0], "message": event[1], "key": f"event-{event[2]}"}
    if job:
        age = at - datetime.fromisoformat(job[2]).timestamp()
        if job[1] == "succeeded" and json.loads(job[6]).get("provenance", {}).get("job_id") != job[0]:
            state = "success" if age < 40 else "question"
            message = "Kandidat selesai. Buka Draf resume untuk meninjau bukti sumber." if state == "success" else "Kandidatnya sudah kamu periksa? Tinjau bukti, lalu terapkan saat sudah sesuai."
            return {"state": state, "message": message, "key": f"job-{job[0]}-{state}"}
        if job[1] in ("failed", "interrupted") and age < 120:
            return {"state": "error", "message": "Proses AI mengalami kendala. Buka Draf resume untuk melihat pesan dan melanjutkan.", "key": f"job-{job[0]}-error"}
    return {"state": "focus", "message": "Ijin kompe. Aku siap menemani ngerjain tugasmu.", "key": "idle"}

import json
import tempfile
import unittest
from datetime import date, datetime, time, timezone
from pathlib import Path

from companion import (
    ASSET_DIR, STATES, buddy_state, delete_task, ensure_reminders, get_task,
    local_deadline, pending_reminder, publish, respond_reminder, save_settings, save_task,
)
from storage import connect, save_project


class CompanionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = connect(self.temp.name)
        self.at = 1_800_000_000

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_timezone_boundary(self):
        value = local_deadline(date(2026, 11, 8), time(0, 15), "WIB")
        self.assertEqual(datetime.fromtimestamp(value, timezone.utc).isoformat(), "2026-11-07T17:15:00+00:00")
        self.assertEqual(local_deadline(date(2026, 11, 8), time(1, 15), "WITA"), value)

    def test_milestones_and_no_duplicate_polling(self):
        task_id = save_task(self.db, "Resume", self.at + 90000)
        ensure_reminders(self.db, self.at)
        self.assertIsNone(pending_reminder(self.db, self.at))
        ensure_reminders(self.db, self.at + 3600)
        first = pending_reminder(self.db, self.at + 3600)
        other = connect(self.temp.name)
        try:
            ensure_reminders(other, self.at + 3600)
            self.assertEqual(pending_reminder(other, self.at + 3600)["notification_id"], first["notification_id"])
        finally:
            other.close()
        respond_reminder(self.db, first["notification_id"], "dismiss", self.at + 3600)
        ensure_reminders(self.db, self.at + 3601)
        self.assertIsNone(pending_reminder(self.db, self.at + 3601))
        ensure_reminders(self.db, self.at + 86400)
        self.assertEqual(pending_reminder(self.db, self.at + 86400)["task"]["id"], task_id)

    def test_snooze_persists_across_restart_and_completion(self):
        task_id = save_task(self.db, "Makalah", self.at + 1000)
        ensure_reminders(self.db, self.at)
        notification = pending_reminder(self.db, self.at)["notification_id"]
        respond_reminder(self.db, notification, "snooze", self.at)
        self.db.close()
        self.db = connect(self.temp.name)
        ensure_reminders(self.db, self.at + 899)
        self.assertIsNone(pending_reminder(self.db, self.at + 899))
        self.assertEqual(pending_reminder(self.db, self.at + 900)["notification_id"], notification)
        respond_reminder(self.db, notification, "done", self.at + 900)
        ensure_reminders(self.db, self.at + 2000)
        self.assertIsNone(pending_reminder(self.db, self.at + 2000))
        self.assertTrue(get_task(self.db, task_id)["completed"])

    def test_overdue_catchup_and_quiet_mode(self):
        save_task(self.db, "Tugas tertinggal", self.at - 100000)
        save_settings(self.db, quiet_until=self.at + 30)
        ensure_reminders(self.db, self.at)
        self.assertIsNone(pending_reminder(self.db, self.at))
        ensure_reminders(self.db, self.at + 31)
        item = pending_reminder(self.db, self.at + 31)
        self.assertIn("Terlambat", item["message"])
        respond_reminder(self.db, item["notification_id"], "dismiss", self.at + 31)
        ensure_reminders(self.db, self.at + 500)
        self.assertIsNone(pending_reminder(self.db, self.at + 500))

    def test_edit_invalidates_old_notification_and_stale_edits(self):
        task_id = save_task(self.db, "Draf awal", self.at + 500)
        ensure_reminders(self.db, self.at)
        notification = pending_reminder(self.db, self.at)["notification_id"]
        save_task(self.db, "Draf baru", self.at + 200000, task_id=task_id, expected_revision=1)
        self.assertFalse(respond_reminder(self.db, notification, "done", self.at))
        self.assertFalse(get_task(self.db, task_id)["completed"])
        self.assertIsNone(pending_reminder(self.db, self.at))
        with self.assertRaises(ValueError):
            save_task(self.db, "Tab lama", self.at, task_id=task_id, expected_revision=1)
        delete_task(self.db, task_id, 2)
        self.assertIsNone(get_task(self.db, task_id))

    def test_disabled_reminders_leave_tasks_intact(self):
        task_id = save_task(self.db, "Tugas", self.at)
        save_settings(self.db, reminders_enabled=False)
        ensure_reminders(self.db, self.at)
        self.assertIsNone(pending_reminder(self.db, self.at))
        save_settings(self.db, reminders_enabled=True)
        ensure_reminders(self.db, self.at)
        self.assertEqual(pending_reminder(self.db, self.at)["task"]["id"], task_id)

    def test_all_states_and_ai_transition(self):
        self.assertEqual(set(STATES), {"working", "success", "error", "focus", "question", "deadline"})
        for state, (_, filename) in STATES.items():
            self.assertTrue((ASSET_DIR / filename).is_file())
            publish(self.db, state, "Uji status", seconds=5, at=self.at)
            self.assertEqual(buddy_state(self.db, at=self.at)["state"], state)
        project, _ = save_project(self.db, {"title": "Proyek", "content": ""})
        timestamp = datetime.fromtimestamp(self.at + 10, timezone.utc).isoformat()
        with self.db:
            self.db.execute("INSERT INTO generation_jobs VALUES ('job',?,'running',?,'[]','',?)",
                            (project, json.dumps({"chunks": [1, 2]}), timestamp))
        self.assertEqual(buddy_state(self.db, project, at=self.at + 10)["state"], "working")
        with self.db:
            self.db.execute("UPDATE generation_jobs SET status='succeeded' WHERE id='job'")
        self.assertEqual(buddy_state(self.db, project, at=self.at + 11)["state"], "success")
        self.assertEqual(buddy_state(self.db, project, at=self.at + 60)["state"], "question")
        publish(self.db, "focus", "Koreksi", project, at=self.at + 60)
        self.assertEqual(buddy_state(self.db, project, at=self.at + 60)["state"], "focus")


if __name__ == "__main__":
    unittest.main()

"""Small draggable desktop companion. Run with python desktop_buddy.py."""

import os
import sqlite3
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

from companion import (
    ASSET_DIR, STATES, buddy_state, ensure_reminders, pending_reminder, publish,
    respond_reminder, save_settings, settings,
)
from storage import connect, data_directory


class InstanceLock:
    """OS releases the lock on crash; double launches do not create duplicate pets."""
    def __init__(self, path):
        self.stream = path.open("a+b")
        self.stream.seek(0, 2)
        if self.stream.tell() == 0:
            self.stream.write(b"0")
            self.stream.flush()
        self.stream.seek(0)
        try:
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.stream.close()
            raise

    def close(self):
        self.stream.close()


def open_app(directory):
    """Reuse the local server; start it if the standalone buddy is running alone."""
    opener = build_opener(ProxyHandler({}))

    def ready():
        try:
            with opener.open("http://127.0.0.1:8501/_stcore/health", timeout=1) as response:
                return response.read(20).strip() == b"ok"
        except OSError:
            return False

    if not ready():
        executable = Path(sys.executable)
        if executable.name.lower() == "pythonw.exe":
            executable = executable.with_name("python.exe")
        kwargs = {"cwd": str(Path(__file__).parent), "env": {**os.environ, "ACADEMICGENT_DATA_DIR": str(directory)}}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
        subprocess.Popen([str(executable), "-m", "streamlit", "run", "app.py",
                          "--server.address", "127.0.0.1", "--server.port", "8501",
                          "--server.headless", "true"], **kwargs)
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline and not ready():
            time.sleep(0.5)
    if not ready():
        db = connect(directory)
        try:
            publish(db, "error", "Aplikasi belum terbuka. Jalankan start.bat dan periksa pesan di terminal.", seconds=90)
        finally:
            db.close()
        return
    webbrowser.open("http://127.0.0.1:8501")


class DesktopBuddy:
    """Small desktop pet with a temporary message bubble and draggable image."""
    def __init__(self, root, directory=None):
        import tkinter as tk
        from PIL import Image, ImageTk
        self.root, self.tk = root, tk
        self.db = connect(directory)
        self.directory = data_directory(self.db)
        self.notification = None
        self.last_notification = None
        self.last_key = None
        self.bubble_until = 0
        self.drag_origin = None
        self.closed = False
        self.direction = -1
        self.walk = True
        self.photos = {}
        for state, (_, filename) in STATES.items():
            with Image.open(ASSET_DIR / filename) as source:
                photo = source.copy()
                photo.thumbnail((110, 110), Image.Resampling.LANCZOS)
                self.photos[state] = ImageTk.PhotoImage(photo, master=root)
        root.title("Academicgent buddy")
        root.overrideredirect(True)
        root.attributes("-topmost", bool(settings(self.db)["desktop_topmost"]))
        root.configure(bg="#ff00ff")
        if sys.platform == "win32":
            root.attributes("-transparentcolor", "#ff00ff")
        self.bubble = tk.Frame(root, bg="white", highlightbackground="#b6c9bd", highlightthickness=1, padx=8, pady=8)
        self.title = tk.Label(self.bubble, bg="white", fg="#245644", font=("Segoe UI", 9, "bold"), anchor="w")
        self.title.pack(fill="x")
        self.message = tk.Label(self.bubble, bg="white", fg="#182b25", font=("Segoe UI", 9), wraplength=220, justify="left", anchor="w")
        self.message.pack(fill="x", pady=4)
        self.actions = tk.Frame(self.bubble, bg="white")
        self.snooze = tk.Button(self.actions, text="Tunda 15 m", command=lambda: self.respond("snooze"))
        self.snooze.pack(side="left")
        self.done = tk.Button(self.actions, text="Selesai", command=lambda: self.respond("done"))
        self.done.pack(side="left")
        self.dismiss = tk.Button(self.actions, text="Tutup", command=lambda: self.respond("dismiss"))
        self.dismiss.pack(side="left")
        self.photo = tk.Label(root, bg="#ff00ff", cursor="hand2", borderwidth=0)
        self.photo.pack(pady=2)
        self.photo.bind("<ButtonPress-1>", self.begin_drag)
        self.photo.bind("<B1-Motion>", self.drag)
        self.photo.bind("<ButtonRelease-1>", self.end_drag)
        self.photo.bind("<Double-Button-1>", lambda event: self.open_application())
        root.bind("<Button-3>", self.show_menu)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.menu = tk.Menu(root, tearoff=False)
        self.menu.add_command(label="Buka Academicgent", command=self.open_application)
        self.menu.add_command(label="Tampilkan pesan", command=self.show_message)
        self.menu.add_command(label="Jeda / lanjut gerakan", command=self.toggle_walk)
        self.menu.add_command(label="Jeda pengingat 1 jam", command=self.quiet)
        self.menu.add_command(label="Aktifkan pengingat lagi", command=self.unquiet)
        self.topmost = tk.BooleanVar(value=bool(settings(self.db)["desktop_topmost"]))
        self.menu.add_checkbutton(label="Selalu di atas", variable=self.topmost, command=self.set_topmost)
        self.menu.add_separator()
        self.menu.add_command(label="Keluar dari buddy", command=self.close)
        root.geometry(f"+{max(0, root.winfo_screenwidth() - 250)}+{max(0, root.winfo_screenheight() - 180)}")
        self.poll()
        self.move()

    def begin_drag(self, event):
        self.drag_origin = (event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y())
        self.dragged = False

    def drag(self, event):
        if self.drag_origin:
            self.dragged = True
            x = max(0, min(event.x_root - self.drag_origin[0], self.root.winfo_screenwidth() - self.root.winfo_width()))
            y = max(0, min(event.y_root - self.drag_origin[1], self.root.winfo_screenheight() - self.root.winfo_height()))
            self.root.geometry(f"+{x}+{y}")

    def end_drag(self, event):
        self.drag_origin = None
        if not self.dragged:
            self.show_message()

    def show_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def set_topmost(self):
        save_settings(self.db, desktop_topmost=self.topmost.get())
        self.root.attributes("-topmost", self.topmost.get())

    def toggle_walk(self):
        self.walk = not self.walk

    def quiet(self):
        save_settings(self.db, quiet_until=time.time() + 3600)
        self.refresh()

    def unquiet(self):
        save_settings(self.db, quiet_until=0, reminders_enabled=True)
        self.refresh()

    def open_application(self):
        threading.Thread(target=open_app, args=(self.directory,), daemon=True).start()

    def show_message(self):
        self.bubble_until = time.time() + 10
        self.last_key = None
        self.refresh()

    def respond(self, action):
        if self.notification:
            respond_reminder(self.db, self.notification["notification_id"], action)
        self.bubble_until = 0
        self.last_key = None
        self.refresh()

    def refresh(self):
        ensure_reminders(self.db)
        self.notification = pending_reminder(self.db)
        view = self.notification or buddy_state(self.db)
        key = (view.get("key"), view["state"], view["message"])
        if self.notification and self.notification["notification_id"] != self.last_notification:
            self.last_notification = self.notification["notification_id"]
        if key != self.last_key and view["state"] != "focus":
            self.bubble_until = time.time() + 10
        self.last_key = key
        self.photo.configure(image=self.photos[view["state"]])
        self.title.configure(text=STATES[view["state"]][0])
        self.message.configure(text=view["message"])
        if self.notification or time.time() < self.bubble_until:
            self.bubble.pack(before=self.photo, padx=2, pady=2)
        else:
            self.bubble.pack_forget()
        if self.notification:
            self.actions.pack(fill="x")
        else:
            self.actions.pack_forget()
        self.root.update_idletasks()
        w, h = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        x = max(0, min(self.root.winfo_x(), self.root.winfo_screenwidth() - w))
        y = max(0, min(self.root.winfo_y(), self.root.winfo_screenheight() - h))
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def move(self):
        if self.closed:
            return
        if self.walk and not self.drag_origin and not self.notification and settings(self.db)["animations"]:
            x = self.root.winfo_x() + 2 * self.direction
            limit = max(0, self.root.winfo_screenwidth() - self.root.winfo_width())
            if x <= 0 or x >= limit:
                self.direction *= -1
                x = max(0, min(x, limit))
            self.root.geometry(f"+{x}+{self.root.winfo_y()}")
        self.root.after(250, self.move)

    def poll(self):
        if self.closed:
            return
        try:
            save_settings(self.db, desktop_heartbeat=time.time())
            self.refresh()
        except (sqlite3.Error, ValueError, OSError):
            pass
        self.root.after(3000, self.poll)

    def close(self):
        self.closed = True
        try:
            save_settings(self.db, desktop_heartbeat=0)
        finally:
            self.db.close()
            self.root.destroy()


def main():
    import tkinter as tk
    from tkinter import messagebox

    db = connect()
    directory = data_directory(db)
    db.close()
    try:
        lock = InstanceLock(directory / "buddy.lock")
    except OSError:
        return
    try:
        root = tk.Tk()
        try:
            DesktopBuddy(root, directory)
        except Exception as error:
            root.withdraw()
            messagebox.showerror("Academicgent buddy", f"Buddy belum dapat dibuka. Jalankan setup.bat, lalu coba lagi.\n\n{error}")
            root.destroy()
            return
        root.mainloop()
    finally:
        lock.close()


if __name__ == "__main__":
    main()

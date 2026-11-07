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
    def __init__(self, root, directory=None):
        import tkinter as tk
        from PIL import Image, ImageTk

        self.root, self.tk = root, tk
        self.db = connect(directory)
        self.directory = data_directory(self.db)
        self.small = False
        self.notification = None
        self.last_view = None
        self.last_notification = None
        self.opening = False
        self.drag_origin = None
        self.closed = False
        self.tick_number = 0
        self.photos = {}
        for state, (_, filename) in STATES.items():
            with Image.open(ASSET_DIR / filename) as source:
                for size in (80, 164):
                    photo = source.copy()
                    photo.thumbnail((size, size), Image.Resampling.LANCZOS)
                    self.photos[state, size] = ImageTk.PhotoImage(photo, master=root)

        root.title("Academicgent buddy")
        root.overrideredirect(True)
        root.attributes("-topmost", bool(settings(self.db)["desktop_topmost"]))
        root.configure(background="#CBD8D1")
        self.shell = tk.Frame(root, background="#FFFFFF", padx=12, pady=10)
        self.shell.pack(fill="both", expand=True, padx=1, pady=1)
        self.header = tk.Frame(self.shell, background="#FFFFFF")
        self.header.pack(fill="x")
        self.grip = tk.Label(self.header, text="Academicgent buddy", background="#FFFFFF", foreground="#245644",
                             font=("Segoe UI", 9, "bold"), cursor="fleur")
        self.grip.pack(side="left")
        self.size_button = self.button(self.header, "Kecilkan", self.toggle_size)
        self.size_button.pack(side="right")
        self.photo = tk.Label(self.shell, background="#FFFFFF", cursor="fleur")
        self.photo.pack(pady=(10, 8))
        self.title = tk.Label(self.shell, background="#FFFFFF", foreground="#182B25", font=("Segoe UI", 11, "bold"),
                              wraplength=252, justify="left", anchor="w")
        self.title.pack(fill="x")
        self.message = tk.Label(self.shell, background="#FFFFFF", foreground="#243C32", font=("Segoe UI", 10),
                                wraplength=252, justify="left", anchor="w")
        self.message.pack(fill="x", pady=(6, 12))
        self.actions = tk.Frame(self.shell, background="#FFFFFF")
        self.actions.pack(fill="x")
        self.snooze = self.button(self.actions, "Tunda 15 m", lambda: self.respond("snooze"))
        self.done = self.button(self.actions, "Sudah selesai", lambda: self.respond("done"))
        self.dismiss = self.button(self.shell, "Tutup pengingat ini", lambda: self.respond("dismiss"))
        self.footer = tk.Frame(self.shell, background="#FFFFFF")
        self.footer.pack(fill="x", pady=(8, 0))
        self.button(self.footer, "Buka aplikasi", self.open_application).pack(side="left")
        self.button(self.footer, "Menu", self.show_menu).pack(side="right")
        self.menu = tk.Menu(root, tearoff=False)
        self.menu.add_command(label="Buka Academicgent", command=self.open_application)
        self.menu.add_command(label="Jeda pengingat 1 jam", command=self.quiet)
        self.menu.add_command(label="Aktifkan pengingat lagi", command=self.unquiet)
        self.topmost = tk.BooleanVar(value=bool(settings(self.db)["desktop_topmost"]))
        self.menu.add_checkbutton(label="Selalu di atas jendela lain", variable=self.topmost, command=self.set_topmost)
        self.menu.add_separator()
        self.menu.add_command(label="Keluar dari buddy", command=self.close)
        for widget in (self.grip, self.photo):
            widget.bind("<ButtonPress-1>", self.begin_drag)
            widget.bind("<B1-Motion>", self.drag)
            widget.bind("<ButtonRelease-1>", self.end_drag)
        root.bind("<Button-3>", self.show_menu)
        root.bind("<Escape>", lambda event: self.toggle_size())
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.update_idletasks()
        root.geometry(f"280x420+{max(0, root.winfo_screenwidth() - 300)}+{max(0, root.winfo_screenheight() - 470)}")
        self.poll()

    def button(self, parent, text, command):
        return self.tk.Button(parent, text=text, command=command, font=("Segoe UI", 9),
                              foreground="#183E2C", background="#EDF4EF", activebackground="#D5E7DC",
                              relief="flat", borderwidth=0, padx=7, pady=6, cursor="hand2", takefocus=True)

    def begin_drag(self, event):
        self.drag_origin = (event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y())

    def drag(self, event):
        if self.drag_origin:
            x = max(0, min(event.x_root - self.drag_origin[0], self.root.winfo_screenwidth() - self.root.winfo_width()))
            y = max(0, min(event.y_root - self.drag_origin[1], self.root.winfo_screenheight() - self.root.winfo_height()))
            self.root.geometry(f"+{x}+{y}")

    def end_drag(self, event):
        self.drag_origin = None

    def show_menu(self, event=None):
        try:
            self.menu.tk_popup(event.x_root if event else self.root.winfo_pointerx(),
                               event.y_root if event else self.root.winfo_pointery())
        finally:
            self.menu.grab_release()

    def set_topmost(self):
        save_settings(self.db, desktop_topmost=self.topmost.get())
        self.root.attributes("-topmost", self.topmost.get())

    def quiet(self):
        save_settings(self.db, quiet_until=time.time() + 3600)
        self.refresh()

    def unquiet(self):
        save_settings(self.db, quiet_until=0, reminders_enabled=True)
        self.refresh()

    def toggle_size(self):
        self.small = not self.small
        self.last_view = None
        self.refresh()

    def open_application(self):
        if self.opening:
            return
        self.opening = True

        def work():
            try:
                open_app(self.directory)
            finally:
                self.opening = False
        threading.Thread(target=work, daemon=True).start()

    def respond(self, action):
        if self.notification:
            respond_reminder(self.db, self.notification["notification_id"], action)
        self.last_view = None
        self.refresh()

    def display(self, view):
        state = view["state"]
        title = STATES[state][0]
        if state == "working" and settings(self.db)["animations"]:
            title += "." * (1 + self.tick_number % 3)
        self.title.configure(text=title)
        key = (state, view["message"], self.small, bool(self.notification))
        if key == self.last_view:
            return
        self.last_view = key
        self.photo.configure(image=self.photos[state, 80 if self.small else 164])
        self.size_button.configure(text="Buka" if self.small else "Kecilkan")
        self.message.configure(text=view["message"])
        if self.small:
            self.message.pack_forget()
            self.actions.pack_forget()
            self.dismiss.pack_forget()
        else:
            self.message.pack(fill="x", pady=(6, 12), after=self.title)
            if self.notification:
                self.actions.pack(fill="x", after=self.message)
                self.snooze.pack(side="left", padx=(0, 8))
                self.done.pack(side="left")
                self.dismiss.pack(fill="x", pady=(6, 0), after=self.actions)
            else:
                self.actions.pack_forget()
                self.dismiss.pack_forget()
        self.root.update_idletasks()
        height = self.root.winfo_reqheight()
        x = max(0, min(self.root.winfo_x(), self.root.winfo_screenwidth() - 280))
        y = max(0, min(self.root.winfo_y(), self.root.winfo_screenheight() - height - 45))
        self.root.geometry(f"280x{height}+{x}+{y}")

    def refresh(self):
        ensure_reminders(self.db)
        self.notification = pending_reminder(self.db)
        if self.notification and self.notification["notification_id"] != self.last_notification:
            self.last_notification = self.notification["notification_id"]
            self.small = False
        self.display(self.notification or buddy_state(self.db))

    def poll(self):
        if self.closed:
            return
        try:
            save_settings(self.db, desktop_heartbeat=time.time())
            self.tick_number += 1
            self.refresh()
        except (sqlite3.Error, ValueError, OSError) as error:
            self.notification = None
            self.display({"state": "error", "message": f"Buddy belum bisa membaca data. Akan dicoba kembali. {str(error)[:120]}"})
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

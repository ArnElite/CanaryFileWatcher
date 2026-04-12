from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import psutil
import tkinter as tk
from tkinter import messagebox
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

CANARY_DIR = Path(r"C:\Users\Arnav\Documents\demo_target")
TARGET_DIR = CANARY_DIR  # Aligning both to demo_target

SAFE_PROCESS_NAMES = {
    "system",
    "registry",
    "smss.exe",
    "csrss.exe",
    "wininit.exe",
    "services.exe",
    "lsass.exe",
    "svchost.exe",
    "dwm.exe",
    "explorer.exe",
    "searchindexer.exe",
    "msmpeng.exe",
    "sihost.exe",
    "taskhostw.exe",
    "notepad.exe",
    "winword.exe",
}

ALLOWED_DEMO_PROCESS_NAMES = {"python.exe", "pythonw.exe", "py.exe"}
DEMO_MARKER = "--demo-ransomware"


@dataclass
class SuspectProcess:
    pid: int
    name: str
    cmdline: str
    disk_write_mb: float


class AlertState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.triggered = False


class CanaryEventHandler(FileSystemEventHandler):
    def __init__(self, alert_queue: queue.Queue[str], alert_state: AlertState) -> None:
        super().__init__()
        self.alert_queue = alert_queue
        self.alert_state = alert_state

    def on_modified(self, event: FileSystemEvent) -> None:
        self._check_event(event)

    def on_moved(self, event: FileSystemEvent) -> None:
        self._check_event(event)

    def on_created(self, event: FileSystemEvent) -> None:
        self._check_event(event)

    def _check_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if not path.exists() and hasattr(event, "dest_path") and event.dest_path:
            path = Path(event.dest_path)

        if CANARY_DIR in path.parents or path == CANARY_DIR:
            with self.alert_state.lock:
                if not self.alert_state.triggered:
                    self.alert_state.triggered = True
                    self.alert_queue.put(f"Canary touched: {path.name}")


def ensure_canary_files(count: int = 10) -> None:
    CANARY_DIR.mkdir(parents=True, exist_ok=True)
    for index in range(1, count + 1):
        file_path = CANARY_DIR / f"canary_{index:02d}.txt"
        if not file_path.exists():
            file_path.write_text(
                f"Canary file {index}. If changed, detector must alert.\n",
                encoding="utf-8",
            )


def safe_process_iter() -> Iterable[psutil.Process]:
    for proc in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
        try:
            _ = proc.info["pid"]
            yield proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


def measure_disk_write_mb(proc: psutil.Process, sample_seconds: float = 0.25) -> float:
    try:
        io1 = proc.io_counters()
        time.sleep(sample_seconds)
        io2 = proc.io_counters()
        if io1 is None or io2 is None:
            return 0.0
        delta = max(io2.write_bytes - io1.write_bytes, 0)
        return delta / (1024 * 1024)
    except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
        return 0.0


def find_demo_suspect() -> SuspectProcess | None:
    for proc in safe_process_iter():
        try:
            name = (proc.info.get("name") or "").lower()
            cmdline_parts = proc.info.get("cmdline") or []
            cmdline = " ".join(cmdline_parts).lower()

            if name in SAFE_PROCESS_NAMES:
                continue

            if DEMO_MARKER in cmdline and "mock_attack.py" in cmdline:
                if name not in ALLOWED_DEMO_PROCESS_NAMES:
                    continue
                write_mb = measure_disk_write_mb(proc)
                return SuspectProcess(
                    pid=proc.pid,
                    name=name,
                    cmdline=" ".join(cmdline_parts),
                    disk_write_mb=write_mb,
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return None


def suspend_then_kill(pid: int) -> bool:
    try:
        process = psutil.Process(pid)
        process.suspend()
        process.kill()
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.Error):
        return False


class SecurityDashboard:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Ransomware Detection Dashboard (Prototype)")
        self.root.geometry("780x430")

        self.alert_queue: queue.Queue[str] = queue.Queue()
        self.alert_state = AlertState()
        self.observer = Observer()

        self.mode = tk.StringVar(value="kill_demo_only")
        self.status_text = tk.StringVar(value="Status: Monitoring")
        self.event_text = tk.StringVar(value="Event: Waiting for canary event")
        self.process_text = tk.StringVar(value="Process: No suspect")
        self.mitigation_text = tk.StringVar(value="Mitigation: Idle")

        self._build_ui()
        self._start_monitor()
        self._poll_alert_queue()

        self.root.protocol("WM_DELETE_WINDOW", self._shutdown)

    def _build_ui(self) -> None:
        container = tk.Frame(self.root, padx=16, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(container, text="Prototype Scope: only demo process termination", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(container, text=f"Canary Folder: {CANARY_DIR}").pack(anchor="w", pady=(6, 0))
        tk.Label(container, text=f"Demo Target: {TARGET_DIR}").pack(anchor="w")

        mode_frame = tk.Frame(container)
        mode_frame.pack(anchor="w", pady=(10, 8))
        tk.Label(mode_frame, text="Mitigation Mode:").pack(side=tk.LEFT)
        tk.Radiobutton(mode_frame, text="Observe only", variable=self.mode, value="observe").pack(side=tk.LEFT, padx=(10, 4))
        tk.Radiobutton(mode_frame, text="Kill demo process only", variable=self.mode, value="kill_demo_only").pack(side=tk.LEFT, padx=4)

        self.status_label = tk.Label(container, textvariable=self.status_text, bg="#1a7f37", fg="white", padx=8, pady=8)
        self.status_label.pack(fill=tk.X, pady=(6, 8))

        tk.Label(container, textvariable=self.event_text, anchor="w").pack(fill=tk.X)
        tk.Label(container, textvariable=self.process_text, anchor="w").pack(fill=tk.X, pady=(4, 0))
        tk.Label(container, textvariable=self.mitigation_text, anchor="w").pack(fill=tk.X, pady=(4, 0))

        self.log = tk.Text(container, height=11)
        self.log.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self._log("Dashboard started.")

    def _log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log.see(tk.END)

    def _start_monitor(self) -> None:
        ensure_canary_files()
        event_handler = CanaryEventHandler(self.alert_queue, self.alert_state)
        self.observer.schedule(event_handler, str(CANARY_DIR), recursive=True)
        self.observer.start()
        self._log(f"Watching canary folder: {CANARY_DIR}")

    def _poll_alert_queue(self) -> None:
        try:
            while True:
                event_msg = self.alert_queue.get_nowait()
                self._handle_canary_alert(event_msg)
        except queue.Empty:
            pass
        self.root.after(250, self._poll_alert_queue)

    def _handle_canary_alert(self, event_msg: str) -> None:
        self.status_text.set("Status: ALERT - Canary Triggered")
        self.event_text.set(f"Event: {event_msg}")
        self.status_label.configure(bg="#b62324")
        self._log(event_msg)

        suspect = find_demo_suspect()
        if suspect is None:
            self.process_text.set("Process: No demo suspect matched safety rules")
            self.mitigation_text.set("Mitigation: No action taken")
            self._log("No suspect found. Project remained in safe state.")
            return

        self.process_text.set(
            f"Process: PID={suspect.pid} NAME={suspect.name} WRITE={suspect.disk_write_mb:.2f} MB"
        )

        if self.mode.get() == "observe":
            self.mitigation_text.set("Mitigation: Observe-only mode enabled")
            self._log(f"Observe mode: would terminate PID {suspect.pid} ({suspect.name})")
            return

        killed = suspend_then_kill(suspect.pid)
        if killed:
            self.mitigation_text.set("Mitigation: Suspended + killed demo process")
            self._log(f"Terminated suspect PID {suspect.pid} ({suspect.name})")
            messagebox.showwarning(
                "Ransomware Behavior Detected",
                f"Demo ransomware behavior detected from process PID {suspect.pid}. Process terminated.",
            )
        else:
            self.mitigation_text.set("Mitigation: Termination attempt failed")
            self._log(f"Failed to terminate PID {suspect.pid}. Check permissions.")

    def _shutdown(self) -> None:
        try:
            self.observer.stop()
            self.observer.join(timeout=2)
        except RuntimeError:
            pass
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    dashboard = SecurityDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()

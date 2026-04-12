# Project Structure Guide

## 1) Languages and Technologies

- Python 3: Main implementation language for simulation, monitoring, and UI.
- Markdown: Documentation (`README.md`, `theory.md`, this file).
- Requirements file format: Dependency pinning in `requirements.txt`.

Core Python libraries used:
- `watchdog`: File-system event monitoring (canary watcher).
- `psutil`: Process inspection and safe process termination.
- `tkinter`: Desktop dashboard UI.
- `cryptography` (`Fernet`): Reversible encryption used in mock attack simulation.

## 2) File-by-File Structure

### `detector.py`
Purpose:
- Runs a dashboard.
- Watches canary files for changes.
- Finds only the demo attacker process.
- Optionally suspends/kills only that demo process.

Imports and what they do:
- `from __future__ import annotations`: Enables modern type hint behavior.
- `queue`: Thread-safe queue for passing watcher alerts to UI loop.
- `threading`: Locking for one-time alert trigger state.
- `time`: Sleep and timestamp utilities.
- `dataclasses.dataclass`: Compact data container (`SuspectProcess`).
- `pathlib.Path`: Cross-platform path handling.
- `typing.Iterable`: Type hint for iterator-returning functions.
- `psutil`: Process listing, I/O counters, suspend/kill APIs.
- `tkinter as tk`: UI widgets/window.
- `from tkinter import messagebox`: Popup warning dialog.
- `watchdog.events.FileSystemEvent, FileSystemEventHandler`: Event model and handler base class.
- `watchdog.observers.Observer`: Starts/stops file watcher thread.

Top-level constants:
- `CANARY_DIR`: Canary folder path.
- `TARGET_DIR`: Target path (currently set equal to `CANARY_DIR`).
- `SAFE_PROCESS_NAMES`: Process names never treated as suspect.
- `ALLOWED_DEMO_PROCESS_NAMES`: Allowed executable names for demo attacker.
- `DEMO_MARKER`: Required command-line marker for safe demo detection.

Classes:
- `SuspectProcess`: Holds process metadata (`pid`, `name`, `cmdline`, `disk_write_mb`).
- `AlertState`: Holds `triggered` flag with lock to avoid repeated first-alert race.
- `CanaryEventHandler(FileSystemEventHandler)`:
  - `on_modified`, `on_moved`, `on_created`: Forward events to `_check_event`.
  - `_check_event(event)`: If canary path touched and alert not yet triggered, enqueue alert.
- `SecurityDashboard`:
  - `__init__`: Builds Tk app state, watcher state, and polling loop.
  - `_build_ui`: Creates labels, mode radio buttons, and log box.
  - `_log(message)`: Timestamped log writer.
  - `_start_monitor`: Ensures canary files exist and starts watchdog observer.
  - `_poll_alert_queue`: Polls queue periodically and handles new alerts.
  - `_handle_canary_alert(event_msg)`: Updates UI, resolves suspect process, performs observe/kill action.
  - `_shutdown`: Stops observer and closes app.
  - `run`: Starts Tk main loop.

Functions:
- `ensure_canary_files(count=10)`: Creates canary folder/files if missing.
- `safe_process_iter()`: Iterates processes while handling access/vanish errors.
- `measure_disk_write_mb(proc, sample_seconds=0.25)`: Samples write bytes delta and returns MB written.
- `find_demo_suspect()`: Returns first process matching strict demo rules.
- `suspend_then_kill(pid)`: Suspends then kills process, returns success boolean.
- `main()`: Entry point that launches dashboard.

---

### `mock_attack.py`
Purpose:
- Simulates ransomware-like behavior on `.txt` files in a restricted demo path.

Imports and what they do:
- `from __future__ import annotations`: Modern type hint behavior.
- `argparse`: CLI arguments (`--target`, `--delay`, etc.).
- `base64`: Key encoding for `Fernet` key format.
- `os`: Directory walking.
- `time`: Delay between file operations.
- `pathlib.Path`: File path handling.
- `cryptography.fernet.Fernet`: Encrypt/decrypt primitive used for simulation.

Top-level constants:
- `ALLOWED_TARGET`: Security boundary; target must be within this folder.

Functions:
- `build_deterministic_key(seed)`: Builds fixed demo key bytes from seed string.
- `encrypt_and_lock_file(path, cipher, dry_run=False)`: Encrypts file, writes `.locked`, removes original.
- `iter_txt_files(target_folder)`: Recursively yields `.txt` files.
- `main()`: Parses CLI args, validates target, runs file loop, logs progress.

CLI options:
- `--target`: Folder to process.
- `--delay`: Delay between files.
- `--max-files`: Stop after N files (0 means all).
- `--demo-ransomware`: Marker used by detector safety filter.
- `--dry-run`: Simulate without modifying files.

---

### `setup_demo_data.py`
Purpose:
- Creates reproducible demo files used by detector and mock attack.

Imports and what they do:
- `from __future__ import annotations`: Modern type hint behavior.
- `pathlib.Path`: Directory/file path creation and writes.

Top-level constants:
- `CANARY_DIR`: Directory where canary files are created.
- `TARGET_DIR`: Directory where demo target documents are created.

Functions:
- `ensure_folder(path)`: Ensures directory exists.
- `write_file(path, content)`: Writes UTF-8 text file.
- `setup_canary_files(count=10)`: Creates numbered canary files.
- `setup_target_files(count=20)`: Creates numbered demo documents.
- `main()`: Runs setup functions and prints locations.

---

### `requirements.txt`
Purpose:
- Declares runtime dependencies for installation.

Entries:
- `watchdog>=4.0.0`: File event monitoring.
- `psutil>=5.9.0`: Process/IO inspection and control.
- `pywin32>=306`: Windows integration support used by ecosystem/tools.
- `cryptography>=42.0.0`: Encryption library for mock attack simulation.

---

### `README.md`
Purpose:
- Setup and demo execution instructions.
- High-level safety model and limitations summary.

---

### `theory.md`
Purpose:
- Conceptual explanation of project, ransomware, canary monitoring, and setup guidance.

## 3) Execution Flow (Simple)

1. Run `setup_demo_data.py` to create demo files.
2. Run `detector.py` to start canary monitoring UI.
3. Run `mock_attack.py --demo-ransomware ...` to trigger simulated attack.
4. `detector.py` receives canary event, identifies demo process, and either observes or kills (based on mode).

## 4) Important Practical Note

Current path constants are not fully aligned across files:
- `detector.py` uses `C:\Users\Arnav\Documents\demo_target`.
- `setup_demo_data.py` and `mock_attack.py` use `C:\Users\Public\Documents\demo_target` as default/allowed target.

For predictable demos, all three files should point to the same base folder.
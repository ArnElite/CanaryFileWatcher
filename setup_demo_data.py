from __future__ import annotations

from pathlib import Path

CANARY_DIR = Path(r"C:\Users\Public\Documents\demo_target")
TARGET_DIR = Path(r"C:\Users\Public\Documents\demo_target")


def ensure_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def setup_canary_files(count: int = 10) -> None:
    ensure_folder(CANARY_DIR)
    for index in range(1, count + 1):
        file_path = CANARY_DIR / f"canary_{index:02d}.txt"
        write_file(file_path, f"Canary file {index}. If modified, alert should trigger.\n")


def setup_target_files(count: int = 20) -> None:
    ensure_folder(TARGET_DIR)
    for index in range(1, count + 1):
        file_path = TARGET_DIR / f"document_{index:02d}.txt"
        write_file(file_path, f"Demo target file {index}.\nThis is safe test content.\n")


def main() -> None:
    setup_canary_files()
    setup_target_files()
    print(f"Canary folder ready: {CANARY_DIR}")
    print(f"Target folder ready: {TARGET_DIR}")


if __name__ == "__main__":
    main()

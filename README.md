# Ransomware Detection Prototype (Safe Demo)

This project is a **classroom-safe prototype** that demonstrates ransomware-style behavior detection using canary files.

## What this prototype does

- Creates/uses canary files in:
  - `C:\Users\Public\Documents\.canary_protected`
- Monitors canary file events using `watchdog`
- Searches for a suspect process using `psutil`
- Displays alerts in a `tkinter` dashboard
- Optionally suspends and kills **only an explicitly marked demo attacker process**

## Safety model (important)

This project is intentionally designed to avoid killing legitimate system processes.

Termination is allowed only if all of the following are true:
1. Process command line contains `mock_attack.py`
2. Process command line contains `--demo-ransomware`
3. Process name is one of: `python.exe`, `pythonw.exe`, `py.exe`

If these conditions are not met, the dashboard logs an alert but takes no kill action.

## Files

- `setup_demo_data.py` - prepares canary and target test files
- `mock_attack.py` - simulated ransomware behavior (`.txt` -> encrypted `.txt.locked`)
- `detector.py` - dashboard + canary monitor + safe mitigation logic
- `requirements.txt` - dependencies

## Setup (Windows 10/11 VM recommended)

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python setup_demo_data.py
```

## Demo flow

### Terminal A: run detector dashboard

```powershell
python detector.py
```

### Terminal B: run mock attack simulation

```powershell
python mock_attack.py --demo-ransomware --target "C:\Users\Public\Documents\demo_target" --delay 0.2
```

## Suggested presentation script

1. Show canary files exist and detector status is green.
2. Explain mitigation mode (`Observe only` vs `Kill demo process only`).
3. Start mock attacker with `--demo-ransomware`.
4. Show detector alert turns red and captures PID.
5. In kill mode, show process terminated after touching early files.

## Known limitations (good to discuss)

- Slow-and-low attacks may not show high disk bursts in a short sample.
- False positives are reduced by strict demo-only kill rules, but this is not enterprise-grade EDR.
- Production tools need kernel telemetry, stronger allowlists, and tamper protection.

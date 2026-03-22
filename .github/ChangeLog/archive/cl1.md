# Changelog Entry — CL1: Complete Database Schema
**Date/Time:** 2026-03-15 (Session 3)  
**Phase:** Phase 1 — Foundation (F2: Database Schema)

---

## What Changed

Created 10 new SQLAlchemy model files and activated all imports so the database now has **15 tables total** (up from 2: `users` and `audit_log`).

### New Files Created
| File | Tables | Purpose |
|------|--------|---------|
| `models/timelog.py` | `time_logs` | Chart time + face-to-face timer records |
| `models/inbox.py` | `inbox_snapshots`, `inbox_items` | Inbox OCR monitoring + diff tracking |
| `models/oncall.py` | `oncall_notes` | After-hours call notes |
| `models/orderset.py` | `order_sets`, `order_items` | Saved order sets for Amazing Charts automation |
| `models/medication.py` | `medication_entries` | Medication reference (personal + shared) |
| `models/labtrack.py` | `lab_tracks`, `lab_results` | Per-patient lab monitoring + trend data |
| `models/caregap.py` | `care_gaps` | Preventive care gap tracking |
| `models/tickler.py` | `ticklers` | Follow-up reminders with MA delegation |
| `models/message.py` | `delayed_messages` | Queued messages for scheduled sending |
| `models/reformatter.py` | `reformat_logs` | Note reformatter session tracking |

### Modified Files
- **`models/__init__.py`** — Uncommented all 10 import lines so `db.create_all()` picks up every table on app startup.

---

## Verification Checkpoints

### Checkpoint 1 — Confirm the tables exist in the database

1. Open a terminal in VS Code (press `` Ctrl+` `` to open it)
2. Make sure you're in the project folder:
   ```powershell
   cd C:\Users\coryd\Documents\CareCompanion
   ```
3. Run this command:
   ```powershell
   venv\Scripts\python.exe -c "from app import create_app; app = create_app(); from models import db; print(sorted(db.metadata.tables.keys()))"
   ```
4. **Expected output** — a list of 15 table names:
   ```
   ['audit_log', 'care_gaps', 'delayed_messages', 'inbox_items', 'inbox_snapshots', 'lab_results', 'lab_tracks', 'medication_entries', 'oncall_notes', 'order_items', 'order_sets', 'reformat_logs', 'ticklers', 'time_logs', 'users']
   ```

### Checkpoint 2 — Confirm the app still starts without errors

1. Double-click **Start_CareCompanion.bat** (or run in terminal):
   ```powershell
   venv\Scripts\python.exe app.py
   ```
2. Open Chrome and go to: **http://localhost:5000**
3. You should see the login page — no 500 errors.
4. Press `Ctrl+C` in the terminal to stop the server when done.

### Checkpoint 3 — Check the SQLite file directly

1. Run this command to list tables straight from the database file:
   ```powershell
   venv\Scripts\python.exe -c "import sqlite3; c=sqlite3.connect('data/carecompanion.db'); [print(r[0]) for r in c.execute(chr(34)+'SELECT name FROM sqlite_master WHERE type='+chr(39)+'table'+chr(39)+' ORDER BY name'+chr(34)).fetchall()]; c.close()"
   ```
   *(This is a long one-liner — copy the whole thing!)*

2. **Expected output** — 15 table names, one per line:
   ```
   audit_log
   care_gaps
   delayed_messages
   inbox_items
   inbox_snapshots
   lab_results
   lab_tracks
   medication_entries
   oncall_notes
   order_items
   order_sets
   reformat_logs
   ticklers
   time_logs
   users
   ```

---

## Architecture Notes

- Every model uses `datetime.now(timezone.utc)` for timestamps (not the deprecated `datetime.utcnow()`)
- All models with a `user_id` column have a foreign key to `users.id`
- `MedicationEntry.user_id` is nullable — `NULL` means it's a practice-wide shared entry
- `Tickler` has TWO foreign keys to `users`: `user_id` (creator) and `assigned_to_user_id` (MA assignee)
- `ReformatLog` stores `flagged_items` as JSON text with a Python property for safe read/write
- `OrderItem` uses `cascade='all, delete-orphan'` — deleting an OrderSet removes its items automatically
- `LabResult` uses `cascade='all, delete-orphan'` on LabTrack — deleting a tracker removes its results

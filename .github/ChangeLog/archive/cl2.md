# Changelog Entry — CL2: Agent Health, Active User Tracking, Crash Recovery
**Date/Time:** 2026-03-15 (Session 3)  
**Phase:** Phase 1 — Foundation (F3: Background Agent, F3a: Agent Health Monitor, F3b: Per-Provider Agent Profiles, F3c: Crash Recovery)

---

## What Changed

### 1. Agent Health Indicator (F3a)
Added a coloured status dot in the header (left side, next to hamburger) that shows agent health:
- **Green (pulsing):** Agent heartbeat within last 60 seconds
- **Yellow:** Heartbeat 60–300 seconds ago (may be stale)
- **Red (glowing):** Heartbeat > 5 minutes ago or no heartbeat
- **Grey:** Unable to check (agent API unreachable)

The dot polls `GET /api/agent-status` every 15 seconds via JavaScript.

### 2. Agent Status API
- **`GET /api/agent-status`** — Returns JSON: `{status, last_heartbeat, age_seconds, active_user, jobs_running}`
- **`GET /admin/agent`** — Full admin dashboard showing uptime, heartbeat card, active user, recent events table, recent errors table
- **`POST /admin/agent/restart`** — Starts `agent.py` as a detached subprocess (admin only, requires confirmation)

### 3. Active User Tracking (F3b)
The `data/active_user.json` file was already being written on login/logout (from auth.py `_write_active_user()`). Now the agent reads it every loop iteration to know who is logged in. When `user_id` is null or the file is missing, the agent pauses MRN tracking but continues scheduled jobs.

### 4. Background Agent (F3 — agent.py)
Created `agent.py` at project root with:
- Flask app context for SQLAlchemy access
- Heartbeat logging every 30 seconds to `agent_logs` table
- Startup/shutdown event logging with PID
- `safe_job()` wrapper that catches all exceptions and logs them to `agent_errors`
- Main loop with 1-second sleep, 30s heartbeat, 3s MRN check cycle
- Placeholder slots for MRN reader and inbox monitor (Phase 2)

### 5. Crash Recovery (F3c)
On startup, agent.py:
1. Queries `time_logs` for entries with `session_start` but no `session_end` from the last 24 hours
2. Closes them using the last heartbeat timestamp as an estimated end time
3. Marks billing_notes with "ESTIMATED: session closed by crash recovery"
4. Logs a `crash_recovery` event to `agent_logs`
5. Writes a startup log with PID and whether recovery was performed

### New Files
| File | Purpose |
|------|---------|
| `models/agent.py` | `AgentLog` + `AgentError` database models |
| `routes/agent_api.py` | `/api/agent-status`, `/admin/agent`, `/admin/agent/restart` |
| `templates/admin_agent.html` | Admin-only agent dashboard page |
| `agent.py` | Background agent with heartbeat, crash recovery, safe job wrappers |

### Modified Files
| File | Change |
|------|--------|
| `models/__init__.py` | Added `AgentLog, AgentError` imports |
| `app.py` | Registered `agent_api_bp` blueprint; added `/api/agent-status` to audit skip list |
| `templates/base.html` | Added "Agent" link in admin sidebar section |
| `static/js/main.js` | Added `initAgentStatus()` — polls `/api/agent-status` every 15s |
| `static/css/main.css` | Enhanced status dot styles: pulse animation (green), glow (red), cursor: help |

---

## Database Changes
Two new tables added (17 total now):
- `agent_logs` — event, pid, details, timestamp
- `agent_errors` — job_name, error_message, traceback, user_id, timestamp

---

## Verification Checkpoints

### Checkpoint 1 — Confirm new tables exist
```powershell
cd C:\Users\coryd\Documents\CareCompanion
venv\Scripts\python.exe -c "from app import create_app; app = create_app(); from models import db; tables = sorted(db.metadata.tables.keys()); print(f'{len(tables)} tables'); [print(f'  {t}') for t in tables]"
```
**Expected:** 17 tables listed, including `agent_logs` and `agent_errors`.

### Checkpoint 2 — Start the app and check the header
1. Run: `venv\Scripts\python.exe app.py`
2. Open Chrome → `http://localhost:5000` → log in
3. Look at the **left side of the header** — you should see a small **grey or red dot**
4. Hover over it — tooltip should say "Agent: offline" or "Agent: not responding"
5. This is correct! The agent isn't running, so it should show offline.

### Checkpoint 3 — Start the agent and watch the dot turn green
1. Open a **second terminal** (keep the Flask server running in the first)
2. Navigate to the project: `cd C:\Users\coryd\Documents\CareCompanion`
3. Run: `venv\Scripts\python.exe agent.py`
4. You should see log output: `Agent starting...` → `Startup logged` → `Agent running (PID ...)`
5. Go back to Chrome — within 15 seconds, the **dot should turn green** with a gentle pulse
6. Hover over it — tooltip should say "Agent: running (heartbeat Xs ago)"
7. Press `Ctrl+C` in the agent terminal to stop it
8. Wait ~60 seconds — the dot should turn **yellow**, then after 5 minutes → **red**

### Checkpoint 4 — Check the admin agent dashboard
1. Make sure you're logged in as the admin user (CORY)
2. Look in the sidebar under the "Admin" section — you should see three links:
   - Users
   - Audit Log
   - **Agent** (new!)
3. Click "Agent"
4. You should see:
   - **Uptime** card with hours/minutes
   - **Last Heartbeat** card (green/yellow/red depending on when you last ran agent.py)
   - **Active User** card (shows who's logged in)
   - **Recent Errors** card (should say 0 if no errors)
   - **Recent Events** table showing startup, heartbeat, and shutdown entries
   - **Restart Agent** button (yellow, top-right)

### Checkpoint 5 — Test the restart button
1. On the Admin → Agent page, click "Restart Agent"
2. A confirmation dialog should appear — click OK
3. The button should change to "Restarted!" (green)
4. A new agent.py process should start in the background
5. The page should auto-reload after 3 seconds

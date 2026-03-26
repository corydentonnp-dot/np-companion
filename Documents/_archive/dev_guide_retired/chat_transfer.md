# Archived on 03-26-26 05:37:32 UTC

Consolidated into Documents/dev_guide/SETUP_GUIDE.md under 'Second Machine / Computer 2 Setup'.

---


Let me check the current MCP config and VS Code setup to write accurate instructions: 

Read [](file:///c%3A/Users/coryd/Documents/NP_Companion/.vscode)

Ran terminal command: node --version; python --version 2>&1; git --version 2>&1

Read [](file:///c%3A/Users/coryd/Documents/NP_Companion/.vscode/mcp.json)

Good. Now make sure mcp.json is tracked in git (it's in .vscode which has a wildcard exclusion — need to add an exception): 

Read [](file:///c%3A/Users/coryd/Documents/NP_Companion/.gitignore#10-10), lines 10 to 25

Searched for text `.vscode` (`**/.gitignore`), 3 results

mcp.json isn't whitelisted. Fix that and push it to GitHub so Computer 2 gets it automatically: 

Replacing 3 lines with 4 lines in [](file:///c%3A/Users/coryd/Documents/NP_Companion/.gitignore)


```

```


Ran terminal command: git add .gitignore .vscode/mcp.json; git commit -m "Track mcp.json for Playwright MCP sync to Computer 2"; git push

Good — mcp.json is now on GitHub. Here's the complete copy-paste guide for Computer 2:

---

## CareCompanion — Computer 2 Setup Guide

*Copy this whole thing into Gmail, then paste into VS Code chat on the other computer.*

---

### PART 1 — Install these 4 programs (in order)

**1. Python 3.11** — https://www.python.org/downloads/release/python-3110/
- Scroll down to "Files", download **Windows installer (64-bit)**
- ⚠️ On the FIRST screen of the installer, check **"Add Python to PATH"** before clicking Install

**2. Git** — https://git-scm.com/download/win
- Click the first download link, run it, click Next through everything

**3. Node.js** — https://nodejs.org/en/download
- Download **LTS version**, run installer, click Next through everything
- (This is needed for the Playwright browser tools)

**4. VS Code** — https://code.visualstudio.com/
- Download, install, defaults are fine

---

### PART 2 — Get the project (PowerShell commands)

Open **PowerShell** (search it in the Start menu). Paste these one at a time:

```powershell
cd C:\Users\coryd\Documents
git clone https://github.com/corydentonnp-dot/np-companion.git NP_Companion
cd NP_Companion
```

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

```powershell
Get-ChildItem migrations\*.py | Sort-Object Name | ForEach-Object { Write-Host "Running $($_.Name)..."; venv\Scripts\python.exe $_.FullName }
```

```powershell
code .
```

---

### PART 3 — VS Code setup (one-time)

**Install extensions** — when VS Code opens it will show a popup: *"Do you want to install recommended extensions?"* → click **Install All**. This installs:
- GitDoc (auto-sync on save)
- GitHub Copilot + Copilot Chat
- Python + Pylance

If the popup doesn't appear: press `Ctrl+Shift+X`, search each one manually and install.

**Sign into GitHub Copilot** — VS Code will prompt you to sign in. Use the same GitHub account (`corydentonnp-dot`).

---

### PART 4 — Enable Playwright MCP (browser tools for Copilot)

Press `Ctrl+Shift+P`, type `Developer: Reload Window`, press Enter.

After reload, open Copilot Chat (`Ctrl+Alt+I`), switch the dropdown from **Ask** to **Agent** mode. Click the tools icon — you should see Playwright browser tools listed (navigate, screenshot, click, etc.).

The first time you use a browser tool, it will download Playwright automatically (~30 seconds). After that it's instant.

---

### PART 5 — Run the app

In the VS Code terminal (`Ctrl+`` ` ``):

```powershell
.\run.ps1
```

Chrome should open to `localhost:5000`. Log in: `CORY` / `ASDqwe123`

---

### PART 6 — Verify sync is working

1. On **this computer**, save any file
2. Wait 30 seconds
3. On **Computer 2**, wait up to 60 seconds — the file should update automatically without doing anything

GitDoc handles this automatically. You'll see it in the VS Code status bar at the bottom.

---

### What's the same on both computers
- All code, templates, routes ✅
- config.py (credentials/settings) ✅
- tesseract (OCR engine) ✅
- Playwright MCP config ✅
- VS Code settings ✅

### What each computer keeps separately
- carecompanion.db — each machine has its own database (patients, sessions, etc.)
- venv — Python packages are reinstalled locally from requirements.txt

---

*Paste this into Copilot Chat on Computer 2 after VS Code is open and say: "I just cloned CareCompanion. Verify everything is set up correctly and start where we left off."* 



Made changes.








You are taking over development of CareCompanion — a locally-hosted Flask clinical workflow app for a family NP. You need to review the project and get ready to continue work. Do NOT start any work yet. Just audit, orient yourself, and give me a status summary.

---

## Step 1 — Read These Files First (in order)

1. `.github/copilot-instructions.md` — your full operational rules (roles, HIPAA, tech constraints, workflow rules). This governs EVERYTHING.
2. `Documents/dev_guide/PROJECT_STATUS.md` — build state, Feature Registry, Risk Register, all blueprints, models.
3. `Documents/dev_guide/ACTIVE_PLAN.md` — current sprint plan with every phase and checkbox.
4. `Documents/CHANGE_LOG.md` — top 10 entries (newest-first). Recent: CL-119 through CL-123.
5. `init.prompt.md` — if it exists, read it for any additional session notes.

---

## Step 2 — Read These Instruction Files

These apply to all code work:
- `.github/instructions/routes.instructions.md`
- `.github/instructions/models.instructions.md`
- `.github/instructions/agent-boundary.instructions.md`
- `.github/instructions/adapters.instructions.md`

---

## Step 3 — Orient Yourself on Current State

After reading the above, understand the following:

**App Version:** 1.1.3  
**Stack:** Python 3.11, Flask 3.1.3, SQLAlchemy 2.0.48, SQLite, Vanilla HTML/CSS/JS, Jinja2  
**Platform:** Windows 11 Pro, dual-monitor, 1920×1080  

**What was recently completed (last session — 03-25-26):**
- CL-122: Process Watchdog & Orphan Prevention System — full rewrite of `tools/process_guard.py`, `run.ps1`, `run.bat`, agent spawn guard in `routes/agent_api.py`, PID lifecycle in `agent_service.py`
- CL-118: Test infrastructure fix — `tests/conftest.py` rewritten for SQLAlchemy 2.0 nested savepoint pattern. All 83/83 billing tests now pass.
- CL-119: UI Testing Checklist Remediation (8 batch items) — unified `.cc-tabs` system, dashboard patient tabs, chart load optimization, billing sidebar nav
- CL-120: Loading states + button feedback (UX-L.1, L.2, L.3) — global `_withSpinner` utility, patient chart deferred endpoints
- UI Overhaul phases M1–M4 all complete
- AC Chart-Open Detection Flag (CF-1 through CF-4) all complete — `parse_chart_title()`, `get_all_chart_windows()`, `data/active_chart.json`, `/api/active-chart` endpoint, polling widget in `base.html`
- AC Automation UIA Phase UIA-1 complete — `uia_probe.py`, `uia_helpers.py`, `win32_actions.py`, `ac_interact.py` all created
- Medication Monitoring Master Catalog (MM-1 through MM-8) complete
- Benchmark Suite (Phase BM) complete

**What is NOT yet done (open in ACTIVE_PLAN.md):**
- UIA-2: Feasibility probe (BLOCKING GATE) — must run `uia_probe.py` against live AC to assess tree richness before migrating automation
- UIA-3: Migrate existing automation to UIA-first — blocked by UIA-2
- UX-L.4: Skeleton/shimmer placeholder for patient chart panels
- UX-S.1–S.7: Inline style → CSS class migration (billing_log, billing_em_calculator, labtrack, medref, oncall, caregap)
- UX-F.1–F.4: Form input preservation on POST errors
- UX-E.1–E.5: Empty state & error polish
- CF Verification Checklist: Hardware-dependent items (need live AC running with test patient MRN 62815)
- One stale cleanup item: delete `tests/_debug_auth.py` (leftover debug file)

---

## Step 4 — Key Architecture Facts

- `app.py` → `create_app()` factory. 20 registered blueprints in `routes/`
- `agent_service.py` is a SEPARATE process from Flask (port 5001). They communicate via SQLite + `data/active_user.json`.
- Desktop automation ONLY in `agent/` — never import pyautogui/win32gui outside that folder.
- All external API calls through `utils/api_client.py` → `get_cached_or_fetch()`. NEVER raw `requests.get()`.
- All timestamps: `datetime.now(timezone.utc)`. Never `datetime.utcnow()`.
- All routes need `@login_required` except: `/login`, `/timer/room-widget`, `/timer/face/room-toggle`, `/oncall/handoff/<token>`.
- HIPAA: No PHI in logs. Use `hashlib.sha256(mrn.encode()).hexdigest()[:12]` for log identifiers. Soft-delete only (`is_archived` flag). Never `db.session.delete()` on clinical records.

---

## Step 5 — Critical Process Management Rules

**This machine has crashed from 160+ orphaned Python processes before. These are absolute rules:**
- Never `isBackground: true` for tests, migrations, or one-shot scripts.
- Every terminal command MUST have a timeout. Never `timeout: 0` for commands that should finish.
- Before starting Flask: check `Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue` first.
- At session start: run `(Get-Process python -ErrorAction SilentlyContinue).Count` — if >5, clean up first.
- Max 8 Python processes at any time during dev.

---

## Step 6 — Your Deliverable (Before Starting Any Work)

After reading everything above, give me:

1. **Confirmation** that you've read and understood `copilot-instructions.md` and all instruction files.
2. **Top 3 risks** from the Risk Register in `PROJECT_STATUS.md`.
3. **Accurate summary** of next open tasks in priority order from `ACTIVE_PLAN.md`.
4. **Any stale/inconsistent items** you noticed — ACTIVE_PLAN steps marked done that don't match code reality, Feature Registry rows that look wrong, etc.
5. **Your recommended next task** — what should we work on first when we're ready to resume?

Do NOT write any code yet. Do NOT create any files. Just review and report.

# NP Companion — Master Project Instructions
# File: init.prompt.md
# Location: project root (alongside app.py)
#
# This is the single source of truth for coding conventions, architecture,
# HIPAA rules, and feature reference. Read this before writing any code.

---

## Project Overview

NP Companion is a locally-hosted clinical workflow automation platform for a
family nurse practitioner at a primary care office. It automates repetitive
tasks inside two legacy Windows desktop applications that have no public API:

- **Amazing Charts** — the clinic's EHR / charting software (desktop app)
- **NetPractice / WebPractice** — scheduling and patient communications (web app)

The platform runs as a Flask web server on the provider's work PC. It is
accessible from any Chrome browser on the clinic network and remotely via
Tailscale from the provider's phone. A background agent (agent_service.py)
runs in the Windows system tray handling all desktop automation, OCR
screen-reading, and scheduled jobs.

**The developer is a non-programmer.** All code must be:
- Clearly commented in plain English
- Simple and explicit — never clever or overly terse
- Broken into small, testable functions
- Consistent with patterns already established in the project

When two approaches are equally valid, always choose the more readable one.

---

## Key Documents

| Document | Location | Purpose |
|----------|----------|---------|
| This file | `init.prompt.md` | Coding rules, conventions, HIPAA, architecture |
| Development Guide | `Documents/NP_Companion_Development_Guide.md` | Phase-by-phase feature specs, 94 features, master build checklist |
| API Integration Plan | `Documents/np_companion_api_intelligence_plan.md` | All 17+ external APIs, caching, offline, billing intelligence |
| AC Interface Reference | `Documents/ac_interface_reference_v2.md` | Amazing Charts UI ground truth, automation reference, clinical summary pipeline |
| Deployment Guide | `Documents/Deployment_Guide.md` | Build, transfer, install, update workflow |
| Verification Checklist | `Documents/VERIFICATION_CHECKLIST.md` | Step-by-step testing for non-programmers |
| Project Status | `PROJECT_STATUS.md` | Current build state, what's done, what's next |

---

## Tech Stack

| Layer              | Technology                                      |
|--------------------|-------------------------------------------------|
| Language           | Python 3.11 (strictly — not 3.12+)             |
| Web framework      | Flask with app factory pattern                  |
| Database ORM       | SQLAlchemy + SQLite                             |
| Authentication     | Flask-Login + Flask-Bcrypt                      |
| Browser automation | Playwright (Chromium only)                      |
| Desktop automation | PyAutoGUI                                       |
| OCR                | Tesseract via pytesseract + Pillow              |
| Scheduled jobs     | APScheduler (BackgroundScheduler)               |
| Push notifications | Pushover API via requests library               |
| System tray        | pystray                                         |
| Windows API        | pywin32 + psutil                                |
| Frontend           | Pure HTML + CSS + vanilla JavaScript            |
| CSS                | CSS custom properties, no frameworks            |
| JS                 | Vanilla ES6+, no build tools, no npm            |
| Hotkeys / macros   | AutoHotkey v2 (.ahk scripts)                    |
| Remote access      | Tailscale (peer-to-peer VPN)                    |
| OS target          | Windows 11 Pro (work PC deployment)             |
| Packaging          | PyInstaller (single-folder .exe bundle)         |
| Version control    | Git + private GitHub repository                 |

**Never suggest:**
- React, Vue, Angular, or any JS framework
- npm packages or build steps for the frontend
- External CSS frameworks (Bootstrap, Tailwind, etc.)
- Cloud databases or cloud storage of any kind
- Python 3.12+ specific syntax or libraries

---

## Project Folder Structure

```
NP_Companion/
├── app.py                    ← Flask app factory + blueprint registration
├── agent_service.py          ← Windows system tray background agent
├── config.py                 ← Machine-specific settings (NEVER commit)
├── build.py                  ← PyInstaller build script
├── npcompanion.spec          ← PyInstaller spec file
├── requirements.txt          ← All Python dependencies pinned to versions
├── init.prompt.md            ← This file
├── PROJECT_STATUS.md         ← Current build state
├── launcher.py               ← Starts Flask + agent together
├── .gitignore
│
├── models/
│   ├── __init__.py           ← db = SQLAlchemy(), import all models here
│   ├── user.py               ← User accounts, roles, preferences, PIN
│   ├── patient.py            ← Patient data, clinical summaries, cache tables
│   ├── timelog.py            ← Chart time + face-to-face timer records
│   ├── inbox.py              ← InboxSnapshot + InboxItem diff tracking
│   ├── oncall.py             ← After-hours call notes
│   ├── orderset.py           ← OrderSet + OrderItem + OrderSetVersion
│   ├── medication.py         ← Medication reference entries
│   ├── labtrack.py           ← LabTrack criteria + LabResult values
│   ├── caregap.py            ← Preventive care gap records
│   ├── tickler.py            ← Follow-up reminder items
│   ├── message.py            ← Delayed message queue
│   ├── notification.py       ← Notification log entries
│   ├── audit.py              ← AuditLog model
│   ├── schedule.py           ← Schedule data from NetPractice
│   ├── agent.py              ← Agent status/error log models
│   └── reformatter.py        ← Note reformat session logs
│
├── routes/
│   ├── __init__.py
│   ├── auth.py               ← /login /logout /register /settings
│   ├── dashboard.py          ← / and /dashboard (Today View)
│   ├── patient.py            ← /patient/<mrn> (Patient Chart View)
│   ├── timer.py              ← /timer /billing
│   ├── inbox.py              ← /inbox
│   ├── oncall.py             ← /oncall
│   ├── orders.py             ← /orders /prep
│   ├── medref.py             ← /medref
│   ├── labtrack.py           ← /labtrack
│   ├── caregap.py            ← /caregap
│   ├── metrics.py            ← /metrics /briefing
│   ├── tools.py              ← /tickler /cs-tracker /pa /referral
│   │                           /macros /coding /notifications /eod
│   ├── admin.py              ← /admin/* routes
│   ├── agent_api.py          ← /agent/* API endpoints
│   ├── ai_api.py             ← /ai/* AI panel endpoints
│   └── netpractice_admin.py  ← /netpractice/* admin routes
│
├── templates/
│   ├── base.html             ← Shared layout: nav, header, auto-lock, AI panel
│   ├── login.html
│   ├── dashboard.html        ← Today View
│   └── [one .html per route]
│
├── static/
│   ├── css/main.css          ← All styles, CSS custom properties
│   └── js/
│       ├── main.js           ← Shared JS: dark mode, auto-lock, clock, AI panel
│       └── service-worker.js ← Offline caching
│
├── agent/
│   ├── mrn_reader.py         ← OCR loop: reads MRN every 3 seconds
│   ├── inbox_monitor.py      ← Inbox OCR + diff snapshot comparison
│   ├── inbox_reader.py       ← Filter dropdown cycling + OCR row extraction
│   ├── inbox_digest.py       ← Daily inbox digest notification
│   ├── ac_window.py          ← win32gui window management + MRN from title bar
│   ├── ocr_helpers.py        ← OCR-first element detection engine for AC automation
│   ├── clinical_summary_parser.py ← XML CDA parser, all structured sections
│   ├── scheduler.py          ← APScheduler job definitions
│   ├── notifier.py           ← Pushover sender with quiet hours logic
│   ├── pyautogui_runner.py   ← Amazing Charts mouse/keyboard executor
│   └── caregap_engine.py     ← USPSTF rules evaluation
│
├── utils/
│   └── [utility modules]
│
├── scrapers/
│   └── netpractice.py        ← Playwright schedule + messaging scraper
│
├── scripts/
│   ├── seed_master_orders.py ← Seed order catalog from AC orders spreadsheet
│   └── seed_test_data.py     ← Seed test data for development
│
├── Documents/                ← Project documentation (see Key Documents table)
│   ├── ac_interface_reference/  ← AC screenshots + sample files
│   │   ├── Amazing charts interface/
│   │   │   ├── ..md files/
│   │   │   │   └── ac_interface_reference_v4.md  ← GROUND TRUTH (3459 lines)
│   │   │   ├── screenshots/       ← 50+ AC screenshots
│   │   │   └── Order Sets/
│   │   │       └── AC orders.xlsx  ← Full order catalog (~870 items)
│   │   ├── *.png                  ← Legacy AC screenshots
│   │   └── ClinicalSummary_*.xml  ← Sample CDA XML export
│   └── [documentation .md files]
│
├── tests/
│   ├── ac_mock.py             ← Mock provider: simulates AC using screenshots
│   └── test_agent_mock.py     ← Standalone mock test runner
│
├── data/                     ← Runtime only — excluded from Git
│   ├── npcompanion.db        ← SQLite database
│   ├── np_session.pkl        ← NetPractice Playwright session cookies
│   ├── active_user.json      ← Currently active provider ID for agent
│   ├── clinical_summaries/   ← XML exports, auto-deleted after 183 days
│   └── backups/              ← Nightly database backups
│
└── migrate_*.py              ← Database migration scripts (idempotent)
```

---

## Flask Conventions

### App Factory Pattern
```python
# app.py — always use create_app()
def create_app():
    app = Flask(__name__)
    app.config.from_object('config')
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    # ... register all blueprints

    with app.app_context():
        db.create_all()

    return app
```

### Blueprint Pattern
Every route file follows this structure exactly:
```python
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models import db
from models.relevant_model import RelevantModel

module_bp = Blueprint('module', __name__)

@module_bp.route('/path')
@login_required
def index():
    # scope all queries to current_user.id
    items = RelevantModel.query.filter_by(user_id=current_user.id).all()
    return render_template('module.html', items=items)
```

### Route Protection Rules
- Every route requires `@login_required` EXCEPT:
  - `/login`
  - `/timer/room-widget` (exam room computers, no login)
  - `/oncall/handoff/<token>` (temporary read-only handoff link)
- Use `@require_role('admin')` for all `/admin/*` routes
- Use `@require_role('provider')` for billing, metrics, and on-call routes

---

## Database Conventions

### Always Scope Queries to Current User
```python
# CORRECT
records = TimeLog.query.filter_by(user_id=current_user.id).all()

# WRONG — never return all users' data
records = TimeLog.query.all()
```

### Shared vs Personal Data
Some tables have both personal and shared entries:
```python
# Personal entries: user_id = current_user.id, is_shared = False
# Shared entries: is_shared = True (readable by all, editable by author only)
shared = MedicationEntry.query.filter_by(is_shared=True).all()
personal = MedicationEntry.query.filter_by(
    user_id=current_user.id, is_shared=False
).all()
```

### Timestamp Convention
All models use UTC for timestamps:
```python
from datetime import datetime, timezone
created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
```

### Never Delete Clinical Records
Use soft deletion — set an `is_archived` or `is_resolved` flag. Hard deletes
are only allowed on non-clinical data (e.g., draft messages not yet sent).
Exception: discarded Note Reformatter items must be logged before any removal.

---

## HIPAA and De-Identification Rules

**These rules override any other consideration. Follow them in every
code change without exception.**

### Rule 1 — No PHI in Push Notifications
Pushover notifications must contain ONLY counts and flags. Never names,
MRNs, dates of birth, diagnoses, or any other identifying information.

```python
# CORRECT
message = f"New labs: {new_labs}, Radiology: {new_rad}, Messages: {new_msg}"

# WRONG
message = f"New lab result for {patient_name}: {result_value}"
```

### Rule 2 — No PHI in Log Files
Application logs must never contain patient names or full MRNs. Use
hashed identifiers or last-4 of MRN only.

```python
import hashlib

def safe_patient_id(mrn: str) -> str:
    """Returns a non-reversible hash for logging purposes."""
    return hashlib.sha256(mrn.encode()).hexdigest()[:12]
```

### Rule 3 — No PHI Leaves the Local Network
- SQLite database never leaves the work PC
- No patient data is sent to any cloud service
- Tailscale provides encrypted peer-to-peer access — no relay server sees data
- The only outbound HTTP calls allowed are:
  - Pushover API (de-identified notification counts only)
  - Weather API (ZIP code only, no patient data)
  - Playwright navigating NetPractice (credentials stay local in session file)
  - NIH/NLM APIs (RxNorm, RxClass, LOINC, UMLS, ICD-10, NLM Conditions, PubMed, MedlinePlus) — clinical vocabulary only, never patient identifiers
  - FDA APIs (OpenFDA Labels, FAERS, Recalls) — drug names/RXCUI only, never patient data
  - AHRQ HealthFinder API — age and sex only (no names, DOBs, or MRNs)
  - CMS APIs (PFS, data.cms.gov) — CPT/HCPCS codes only, never patient data
  - Open-Meteo API — ZIP code/coordinates only

### Rule 4 — MRN Display in UI
Show only the last 4 digits of MRN in any web UI element that might be
visible on a shared screen. Full MRN is only used internally in the database
and in the billing audit log (which requires login to access).

```python
# In templates:
{{ mrn[-4:] }}  {# Shows only last 4 digits #}
```

### Rule 5 — Audit Log Every Patient-Adjacent Action
```python
from utils import log_access

@module_bp.route('/labtrack/<mrn>')
@login_required
def patient_labs(mrn):
    log_access(current_user.id, action='view_lab_tracker', module='labtrack')
    # ... rest of route
```

### Rule 6 — Note Reformatter Discard Rule
Any clinical content the user chooses to discard during reformatting must be
written to the ReformatLog.discarded_items JSON field BEFORE removal from
the working state. The discard is permanent in the log even if the user
later reformats the same note.

---

## External API Conventions

NP Companion integrates 17+ free government APIs (NIH, FDA, CMS, CDC, AHRQ).
The full API specification is in `Documents/np_companion_api_intelligence_plan.md`.

### API Client Pattern
All API calls go through `utils/api_client.py` using the `get_cached_or_fetch()`
helper. Never make raw `requests.get()` calls to external APIs from routes
or agent modules.

```python
from utils.api_client import get_cached_or_fetch
from models.patient import RxNormCache

# CORRECT — cache-first with graceful fallback
data = get_cached_or_fetch(RxNormCache, rxcui, fetch_rxnorm_properties)

# WRONG — direct API call bypasses cache and offline handling
data = requests.get(f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json").json()
```

### Cache Table Pattern
All cache tables follow the `Icd10Cache` structure:
- `lookup_key` (indexed, unique) — the search key
- `response` (Text) — JSON string of the full API response
- `fetched_at` (DateTime) — when fetched
- `expires_at` (DateTime, nullable) — null means permanent cache

### Offline Behavior
Every feature that uses an API must work without internet:
1. Return stale cached data if available (with staleness indicator)
2. Fall back to hardcoded data if no cache (e.g., 19 USPSTF rules for care gaps)
3. Show "not available" with explanation if no fallback exists
4. Never block page loads waiting for API responses

### Rate Limiting
- RxNorm/RxClass: 20 requests/second shared
- OpenFDA: 40/min anonymous, 240/min with API key
- PubMed: 3/sec anonymous, 10/sec with API key
- All others: no published limits, be conservative

---

## Multi-User Architecture

### User Roles
```python
class UserRole:
    PROVIDER = 'provider'  # Full access to all modules
    MA = 'ma'              # dashboard, orders, caregap, medref only
    ADMIN = 'admin'        # Everything + /admin/* routes
```

### Role Permissions Map
```python
ROLE_PERMISSIONS = {
    'ma':       ['dashboard', 'orders', 'caregap', 'medref'],
    'provider': ['dashboard', 'orders', 'caregap', 'medref', 'timer',
                 'billing', 'inbox', 'oncall', 'labtrack', 'metrics',
                 'tools', 'reformatter', 'briefing'],
    'admin':    ['*']  # all of the above plus /admin/*
}
```

### Active Provider Tracking (for Background Agent)
The agent writes and reads `data/active_user.json` to know who is currently
logged in and whose data to attribute time logs and MRN reads to:

```python
# Written by app.py on login:
{"user_id": 3, "username": "cory", "logged_in_at": "2025-01-01T08:00:00"}

# Written on logout:
{"user_id": null}

# Agent reads this every 10 seconds
```

---

## Background Agent Architecture

The agent (agent_service.py) and Flask app (app.py) are two **separate processes**
that communicate only through the shared SQLite database and the
`data/active_user.json` file. They never call each other directly.

```
Flask app (port 5000)    ←——— browser requests ———→   User's browser
        ↕ reads/writes
   SQLite database
        ↕ reads/writes
Background agent         ←——— status JSON (port 5001) ←— Flask app polls
```

The agent exposes a minimal status endpoint on port 5001.
Every agent job is wrapped in try/except. Exceptions are logged to the
database — they never crash the agent process.

---

## Frontend Conventions

### CSS Custom Properties (use these everywhere)
```css
:root {
    --color-navy:      #1B3A6B;
    --color-teal:      #0D7377;
    --color-gold:      #E8A020;
    --color-red:       #C0392B;
    --color-green:     #1E7E34;
    --color-lt-blue:   #D6E8F7;
    --color-lt-green:  #D4EDDA;
    --color-lt-yellow: #FFF8DC;
    --color-lt-red:    #FDECEA;
    --color-lt-gray:   #F5F5F5;
    --color-mid-gray:  #DDDDDD;
}
```

### Dark Mode Pattern
```css
[data-theme="dark"] {
    --bg-primary:   #1a1a2e;
    --bg-card:      #16213e;
    --text-primary: #e0e0e0;
}
```

### Template Inheritance
Every page template extends base.html:
```html
{% extends "base.html" %}
{% block title %}Module Name{% endblock %}
{% block content %}
  <!-- page content here -->
{% endblock %}
```

### API Endpoints for JavaScript
Endpoints called by JavaScript return JSON:
```python
@module_bp.route('/api/some-data')
@login_required
def api_some_data():
    return jsonify({"success": True, "data": [...], "error": None})

# On error:
return jsonify({"success": False, "data": None, "error": "Description"}), 400
```

### No Page Reloads for Status Updates
Use `fetch()` polling for live data (timer, agent status, prep progress).
Never use WebSockets — too complex for this project's maintenance level.

---

## Amazing Charts Interface Reference

**ALWAYS READ THIS FILE FIRST** before writing any AC automation code:
`Documents/ac_interface_reference_v2.md`

This consolidated reference covers the entire AC desktop application UI.
The detailed ground truth (3459 lines) is at:
`Documents/ac_interface_reference/Amazing charts interface/..md files/ac_interface_reference_v4.md`

### AC System Information
| Property | Value |
|---|---|
| AC Version | 12.3.1 (build 297) |
| AC Process Title | `Amazing Charts EHR (32 bit)` |
| AC Executable | `C:\Program Files (x86)\Amazing Charts\AmazingCharts.exe` |
| Practice ID | 2799 |
| Practice Name | Family Practice Associates of Chesterfield |
| AC Database | `\\192.168.2.51\Amazing Charts\AmazingCharts.mdf` (SQL Server) |
| Imported Items | `\\192.168.2.51\amazing charts\ImportItems\[MRN]\` |

### Work PC Specs
| Property | Value |
|---|---|
| OS | Windows 11 Pro |
| PC | HP EliteDesk 705 G5 |
| CPU | AMD Ryzen 5 PRO 3400G |
| RAM | 16 GB |
| Username | `FPA-D-NP-DENTON\FPA` |

---

## AC State Detection

The agent detects which of 4 states AC is in before performing any automation:

```python
AC_STATES = {
    'not_running':   'No AC process found — cannot automate',
    'login_screen':  'AC is open but at the login prompt',
    'home_screen':   'AC is logged in, showing the home screen (no chart open)',
    'chart_open':    'A patient chart window is in the foreground',
}
```

State detection logic:
1. Check if `Amazing Charts EHR (32 bit)` appears in `win32gui.EnumWindows()`
2. If found, read the window title — if it matches the chart regex
   (`LASTNAME, FIRSTNAME  (DOB: M/D/YYYY; ID: XXXXX)`), state = `chart_open`
3. If no chart match but AC window exists, check for "Amazing Charts Login"
   → `login_screen`, otherwise → `home_screen`
4. If no AC window → `not_running`

---

## AC Mock Mode (Testing Without Amazing Charts)

Set `AC_MOCK_MODE = True` in config.py to test the agent pipeline on any
machine that doesn't have Amazing Charts installed.

How it works:
- `agent/ac_window.py` returns simulated window data
- `agent/ocr_helpers.py` loads reference screenshots instead of screen captures
- All modules run their real logic against the screenshot images
- The mock provider lives in `tests/ac_mock.py`

Test patient data: MRN 62815, Name TEST TEST, DOB 10/1/1980, Age 45, Female

---

## PyAutoGUI / Amazing Charts Automation Rules

**OCR-FIRST APPROACH** — All UI element detection must use Tesseract OCR
to find elements by their visible text labels before falling back to
coordinates. This makes automation portable across any machine.

The OCR detection engine lives in `agent/ocr_helpers.py`:
- `find_and_click(text)` — find text via OCR and click it
- `find_text_on_screen(text)` — find screen coordinates of a label
- `find_element_near_text(anchor, direction, offset)` — find adjacent elements

Key rules:
1. **OCR first, coordinates as fallback only** — pass `fallback_xy=` parameter
2. **Verify AC is foreground** before any click via `win32gui`
3. **Screenshot before every order set execution** (audit trail)
4. **Add delays between actions** (minimum 0.5s)
5. **Stop immediately on any failure** — log what was/wasn't completed
6. **Use keyboard shortcuts** when available (Alt+P, Ctrl+S, etc.)

```python
# CORRECT — OCR-first with fallback
find_and_click('Export Clinical Summary',
               fallback_xy=config.EXPORT_CLIN_SUM_MENU_XY)

# WRONG — hardcoded coordinates as primary
pyautogui.click(*config.EXPORT_CLIN_SUM_MENU_XY)
```

---

## Playwright / NetPractice Scraper Rules

1. Always load saved session before navigating
2. Check for Google login redirect before scraping
3. Never automate Google login — set `needs_reauth = True` and notify
4. Include placeholder comments for CSS selectors pending screenshot review

---

## OCR / MRN Reader Rules

1. Always preprocess images (grayscale, upscale 2x, contrast 2.0) before OCR
2. Always validate MRN format after OCR (6-10 numeric digits)
3. MRN capture uses AC window position via `win32gui.GetWindowRect()` — title bar only
4. Use `agent/ocr_helpers.py` for all new OCR work

---

## Notification Rules

All notifications go through `agent/notifier.py`. Never call Pushover
directly from routes or other modules.

Pushover priority levels:
- `-1` — Quiet (no sound)
- ` 0` — Normal (default)
- ` 1` — High priority (bypasses quiet hours)
- ` 2` — Emergency (requires acknowledgment — critical values only)

---

## Error Handling Conventions

```python
# In routes — user-facing errors:
try:
    result = some_operation()
except Exception as e:
    db.session.rollback()
    app.logger.error(f"Error in module.action: {str(e)}")
    return jsonify({"success": False, "error": "Operation failed"}), 500

# In agent jobs — never crash the agent:
try:
    run_inbox_check(user_id)
except Exception as e:
    log_agent_error(user_id=user_id, job='inbox_check',
                    error=str(e), traceback=traceback.format_exc())
    # Continue — do not re-raise
```

---

## Amazing Charts Keyboard Shortcuts

```python
AC_SHORTCUTS = {
    'demographics':          'F5',
    'summary_sheet':         'F6',
    'most_recent_encounter': 'F7',
    'past_encounters':       'F8',
    'imported_items':        'F9',
    'account_information':   'F11',
    'patient_menu':          'Alt+P',
    'medications':           'Ctrl+M',
    'health_risk_factors':   'Ctrl+H',
    'immunizations':         'Ctrl+I',
    'print_summary_sheet':   'Ctrl+P',
    'print_messages':        'Ctrl+G',
    'tracked_data':          'Ctrl+T',
    'set_flags':             'Alt+P → Set Flags',
    'set_reminder':          'Alt+P → Set Reminder',
    'confidential':          'Alt+P → Confidential',
    'allergies':             'Alt+P → Allergies',
    'diagnoses':             'Alt+P → Diagnoses',
    'physical_exam':         'Alt+P → Physical Exam',
    'clinical_decision_support': 'Alt+P → Clinical Decision Support',
    'export_clinical_summary': 'Alt+P → Export Clinical Summary',
    'save_and_close':        'Ctrl+S',
}
```

---

## Clinical Summary XML Export

### Format and Naming
- Format: HL7 CDA (C-CDA R2.1)
- Namespace: `{'cda': 'urn:hl7-org:v3'}`
- File naming: `ClinicalSummary_PatientId_[MRN]_[YYYYMMDD]_[HHMMSS].xml`
- Export folder: `config.CLINICAL_SUMMARY_EXPORT_FOLDER`
- Retention: auto-delete after 183 days, audit log every parse

### CRITICAL — Two-Phase Export Workflow

Charts must be opened for ALL patients first (Phase 1), then XML exports
happen for ALL patients (Phase 2). Exporting CANNOT be triggered while a
patient chart window is open.

**Phase 1 — Chart Opening** (repeat for each patient):
1. Search patient in Patient List panel by ID
2. Verify name matches expected patient
3. Double-click to open chart
4. Select Visit Template → Procedure Visit → Companion
5. Clear popups, Ctrl+S to save and close
6. Repeat for all patients

**Phase 2 — XML Export** (only after ALL charts are saved):
1. Ensure AC is on home screen (no chart windows open)
2. In inbox, find patient's most recent chart
3. Single-click to select (do NOT double-click)
4. Alt+P → Export Clinical Summary
5. Select "Full Patient Record" (never single encounter)
6. Verify checkboxes and destination, click Export
7. Repeat for all patients

### XML Sections Available

| Section | LOINC Code | Data Type |
|---------|-----------|-----------|
| Medications | 10160-0 | Structured |
| Allergies | 48765-2 | Structured |
| Problems / Diagnoses | 11450-4 | Structured |
| Vital Signs | 8716-3 | Structured |
| Results / Labs | 30954-2 | Structured |
| Immunizations | 11369-6 | Structured |
| Social History | 29762-2 | Structured |
| Encounters | 46240-8 | Structured |
| Plan of Care | 18776-5 | Narrative |
| Assessments | 51848-0 | Narrative |
| Goals | 61146-7 | Narrative |
| Health Concerns | 75310-3 | Narrative |
| Instructions | 69730-0 | Narrative |
| Mental Status | 10190-7 | Narrative |
| Reason for Visit | 29299-5 | Narrative |
| Progress Notes | 11506-3 | Narrative |

---

## Canonical Note Section List

```python
AC_NOTE_SECTIONS = [
    "Chief Complaint",
    "History of Present Illness",
    "Review of Systems",
    "Past Medical History",
    "Social History",
    "Family History",
    "Allergies",
    "Medications",
    "Physical Exam",
    "Functional Status/Mental Status",
    "Confidential Information",
    "Assessment",
    "Plan",
    "Instructions",
    "Goals",
    "Health Concerns",
]

AC_SPECIAL_SECTIONS = ["Allergies", "Medications"]
```

---

## Build Phases — Current Status Reference

| Phase | Focus | Features |
|-------|-------|---------|
| 1 | Foundation | App shell, auth, database schema, background agent |
| 2 | Data Layer | NetPractice scraper, inbox monitor, MRN reader |
| 3 | Daily Tools | On-call notes, order sets, note prep, med reference |
| 4 | Monitoring | Lab tracker, visit timer, productivity dashboard, billing log |
| 5 | Clinical Support | Care gaps, billing capture, coding suggester |
| 6 | Communication | Delayed messages, result templates, end-of-day checker |
| 7 | Notifications + Utilities | Push system, morning briefing, macros, tickler, CS tracker, PA generator, referral generator |
| 8 | Multi-User Platform | Onboarding wizard, admin view, offline mode |
| 9 | Note Reformatter | Note capture, parsing, classification, template engine, review UI |

---

## Complete Feature Reference

### Phase 1 — Foundation
- **F1** Project skeleton: Flask app, base.html, CSS, JS
- **F1a** Multi-user accounts: User model, login, register, roles
- **F1b** Role-based access: @require_role decorator, sidebar filtering
- **F1c** Dark mode: data-theme toggle, localStorage + server persistence
- **F1d** Notification preferences: per-user Pushover settings
- **F1e** Session timeout + auto-lock: PIN overlay, 5-min inactivity
- **F1f** Audit trail: AuditLog model, log_access() helper, /admin/audit-log
- **F2** Database schema: all tables created upfront
- **F3** Background agent: system tray, heartbeat, status endpoint (5001)
- **F3a** Agent health monitor: green/yellow/red dot in header
- **F3b** Per-provider agent profiles: active_user.json tracking
- **F3c** Crash recovery: incomplete session detection on agent startup

### Phase 2 — Data Layer
- **F4** NetPractice schedule scraper: Playwright, session persistence
- **F4a** New patient flag: gold NEW badge in Today View
- **F4b** Visit duration estimator: historical avg vs booked time
- **F4c** Double-booking + gap detector: anomaly flags in briefing
- **F4e** Re-auth watchdog: immediate Pushover on session expiry
- **F5** Inbox monitor: OCR per filter tab, diff tracking, snapshots
- **F5b** Critical value flag: immediate siren notification
- **F5c** Held item registry: /inbox/held, intentional holds excluded from count
- **F5d** Inbox age tracker: yellow/red clock icons, 48/72hr thresholds
- **F5f** Inbox review timestamp log: /inbox/audit-log, PDF export
- **F6** MRN screen reader: 3-second OCR loop, auto time log entries
- **F6a** Chart open duration warning: 20-min idle popup
- **F6b** Idle detection: pause timer on inactivity, net vs gross time
- **F6c** Manual MRN override: manual entry form, pencil icon in log

### Phase 3 — High-Value Daily Tools
- **F7** On-call note keeper: mobile-first, Tailscale accessible
- **F7a** Voice-to-text: Web Speech API dictation on note form
- **F7b** Callback tracker: overdue callbacks section, 30-min reminder
- **F7d** Colleague handoff: temporary de-identified read-only link
- **F7e** Note status tracking: kanban flow, Monday pending filter
- **F8** Order set manager: saved sets, per-patient toggles, PyAutoGUI executor
- **F8a** Shared order sets: community tab, import/fork
- **F8b** Version history: OrderSetVersion table, restore button
- **F8d** Pre-execution confirmation: modal, typed confirmation, 3s countdown
- **F8e** Partial execution recovery: interrupted banner, resume option
- **F9** Pre-visit note prep: overnight automation, template mapping
- **F9a** Template source sync: discover_ac_templates(), weekly resync
- **F9c** Prep status dashboard: auto-refresh progress bar
- **F9d** Failed prep alert: screenshot, yellow flag in Today View
- **F9e** MA prep handoff: MA-triggered prep, chief complaint paste
- **F10** Medication reference: condition-based, first/second line, popup
- **F10a** Shared formulary notes: practice annotations, author + date
- **F10c** Pregnancy + renal filter: context bar, contraindication hiding
- **F10d** Guideline update flag: /medref/review-needed, yellow banner

### Phase 4 — Monitoring & Tracking
- **F11** Lab value tracker: per-patient criteria, inbox auto-population
- **F11a** Trend visualization: Chart.js line graph, threshold lines
- **F11b** Custom thresholds: alert_low/high/critical per patient, sliders
- **F11c** Overdue lab notification: 6 AM daily job, red clock in Today View
- **F11d** Lab panel grouping: BMP, CMP, CBC, Lipids, Thyroid, Diabetes
- **F12** Visit timer + face-to-face timer: auto MRN-driven + manual toggle
- **F12a** Visit type auto-tag: schedule lookup on session open
- **F12b** Complexity flag: one-tap toggle, excludes from avg calculations
- **F12c** Room widget: /timer/room-widget, no login, QR code
- **F13** Productivity dashboard: Chart.js charts, date range filter
- **F13a** Benchmark comparison: opt-in, anonymized practice average
- **F13b** Burnout indicators: 3-week trend on 3 metrics, weekly report note
- **F13c** Weekly summary email: Friday 5 PM, Gmail SMTP
- **F14** Billing audit log: permanent record, PDF export
- **F14a** E&M calculator: time-based vs MDM, 2023 AMA guidelines
- **F14b** Anomaly detector: under/over-billing flags, review filter
- **F14c** Monthly billing report: RVU totals, prior month comparison

### Phase 5 — Clinical Decision Support
- **F15** Care gap tracker: USPSTF rules engine, per-patient checklist
- **F15a** Age/sex auto-population: evaluate on schedule pull
- **F15b** Closure documentation: pre-generated snippet, copy button
- **F15c** Panel gap report: coverage %, outreach list for MA
- **F16** Billing capture: AWV add-ons, CCM, prolonged service, TCM
- **F16a** AWV checklist: component tracking, eligible codes at end
- **F16b** CCM eligibility: monthly minute accumulation, 99490 alert
- **F16c** Prolonged service calculator: auto-detect 99417 eligibility
- **F17** Coding suggester: ICD-10 search, favorites, pairing
- **F17b** Specificity reminder: unspecified code detection, child codes
- **F17c** Code pairing: historical + seeded common pairings

### Phase 6 — Communication Tools
- **F18** Delayed message sender: queue, Playwright execution, recurring
- **F18a** Recurring templates: interval-based auto-scheduling
- **F19** Abnormal result templates: 5 urgency tiers, bracketed fields
- **F19a** Shared template library: practice-wide, legal review flag
- **F20** End-of-day checker: unsigned notes, inbox, ticklers, on-call
- **F20a** Unsigned note counter: priority=1 push, 30-min closing reminder
- **F20c** Configurable checklist: per-user toggles, custom items

### Phase 7 — Notifications & Utilities
- **F21** Push notification system: Notifier class, quiet hours, logging
- **F21b** Escalating alerts: unacknowledged critical resend
- **F22** Morning briefing: schedule + gaps + inbox + weather, 6:30 AM
- **F22a** Commute mode: /briefing/commute, SpeechSynthesis auto-read
- **F23** AutoHotkey macros: macros.json-driven, NP Companion management UI
- **F23a** Macro sync: macros.json stored in DB, synced to .ahk
- **F24** Follow-up tickler: three-column dashboard, MA assignment
- **F24a** Priority levels: routine/important/urgent, push on urgent
- **F24b** MA assignment: delegate + completion tracking
- **F25** Controlled substance tracker: fill dates, PDMP, UDS intervals
- **F25a** PDMP reminder: morning briefing flag, configurable interval
- **F25b** CS patient registry: private, local only
- **F26** Prior auth generator: narrative builder, payer history, appeal
- **F26a** Shared PA library: community-contributed winning language
- **F26b** PA status tracker: pending/approved/denied/appealed
- **F27** Referral letter generator: specialty templates, log
- **F27a** Specialty-specific templates: per-specialty field prompts
- **F27b** Referral tracking log: overdue return report flag

### Phase 8 — Multi-User Platform
- **F28** Onboarding wizard: 5-step, account + calibration + NetPractice + starter pack
- **F28a** MRN calibration tool: click-to-set capture region
- **F28b** Starter pack: import colleagues' order sets + macros + medref
- **F29** Practice admin view: aggregate only, no individual breakdown
- **F30** Offline mode: service worker, IndexedDB queue, sync on reconnect

### Phase 9 — Note Reformatter
- **F31** Prior note reformatter: 6-step wizard with mandatory flagged review
  - note_reader.py: AC note capture via OCR/print
  - note_parser.py: section header detection, unclassified_text bucket
  - note_classifier.py: medication + diagnosis + allergy + ROS classification
  - note_reformatter.py: template filling engine
  - Review UI: flagged items queue, discard requires "DISCARD" typed
  - User template builder: drag-drop section ordering, /reformatter/template
  - Medication flagging reference: 500 common meds, fuzzy match
  - Diagnosis flagging reference: 200 common Dx, ICD-10 mapping

---

## Sensitive Files — Never Suggest Committing These

```
config.py           ← API tokens, IP addresses, screen coordinates
data/               ← Database, session cookies, screenshots
.env                ← If used
*.pkl               ← Playwright session files
*.log               ← Application logs
venv/               ← Virtual environment
dist/               ← PyInstaller build output
build/              ← PyInstaller intermediate files
```

---

## Common Mistakes to Avoid

1. **Don't use `Query.all()` without `filter_by(user_id=...)`** in any
   table that has a user_id column.
2. **Don't suggest JavaScript frameworks** — vanilla JS only.
3. **Don't suggest environment variables** — config comes from `config.py`.
4. **Don't use `datetime.utcnow()`** — use `datetime.now(timezone.utc)`.
5. **Don't use `db.session.delete()`** on clinical records — use soft deletion.
6. **Don't put patient names or MRNs in notification bodies** — ever.
7. **Don't hardcode pixel coordinates** — use OCR-first via `agent/ocr_helpers.py`.
8. **Don't suggest `python-dotenv`** — not used in this project.
9. **Don't use `redirect(request.referrer)`** — always use `url_for()`.
10. **Don't skip the pre-execution screenshot** in PyAutoGUI runner.

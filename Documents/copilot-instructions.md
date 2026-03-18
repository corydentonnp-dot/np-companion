# NP Companion — GitHub Copilot Instructions
# File: init.prompt.md
# Location: np-companion/ (project root)
#
# Copilot reads this file automatically for all files in this project.
# Update it as the project evolves.

---
password for the original admin account is ASDqwe123 and the username is CORY. This will be changed before going live and is a development admin account. you may use this password until we go live. 

---
After every prompt, update the change log, the tables in the NP_Companion_Development_Guide, and the verification checklist. this is not negotiable. 
---

 I have never coded before and dont know how to work with VScode, terminals, servers, ect ect. This will help keep track of progress and maintain a clear history of modifications for future reference. 

Additionally, after the end of every prompt, summarize the completed features and any important architectural decisions in `.github/ChangeLog/CHANGELOG.md` — add a new `## CL#` section at the top (reverse chronological). Each entry should include a date/time stamp. These entries can be brief and to the point. This ensures all changes are well-documented and accessible.

After every prompt that adds or modifies code:
1. Run your own internal tests (syntax, logic, imports).
2. Add a new `## CL#` section at the top of `.github/ChangeLog/CHANGELOG.md` with: date, phase, summary, files changed, and step-by-step verification checkpoints a non-programmer can follow.
3. Include PowerShell commands for verification where possible.
4. After major milestones, include a PowerShell test script and update test.py.
---

## Project Overview

NP Companion is a locally-hosted clinical workflow automation platform for a
family nurse practitioner at a primary care office. It automates repetitive
tasks inside two legacy Windows desktop applications that have no public API:

- **Amazing Charts** — the clinic's EHR / charting software (desktop app)
- **NetPractice / WebPractice** — scheduling and patient communications (web app)

The platform runs as a Flask web server on the provider's work PC. It is
accessible from any Chrome browser on the clinic network and remotely via
Tailscale from the provider's phone. A background agent (agent.py) runs in
the Windows system tray handling all desktop automation, OCR screen-reading,
and scheduled jobs.

**The developer is a non-programmer.** All code must be:
- Clearly commented in plain English
- Simple and explicit — never clever or overly terse
- Broken into small, testable functions
- Consistent with patterns already established in the project

When two approaches are equally valid, always choose the more readable one.

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
| OS target          | Windows 11 Pro (work PC deployment)              |
| Dev OS             | Any (personal computer)                         |
| Version control    | Git + private GitHub repository                 |
| Notifications      | Pushover (de-identified counts only)            |

**Never suggest:**
- React, Vue, Angular, or any JS framework
- npm packages or build steps for the frontend
- External CSS frameworks (Bootstrap, Tailwind, etc.)
- Cloud databases or cloud storage of any kind
- Python 3.12+ specific syntax or libraries

---

## Project Folder Structure

```
np-companion/
├── app.py                    ← Flask app factory + blueprint registration
├── agent.py                  ← Windows system tray background agent
├── config.py                 ← Machine-specific settings (NEVER commit)
├── requirements.txt          ← All Python dependencies pinned to versions
├── .gitignore
├── init.prompt.md            ← This file
│
├── models/
│   ├── __init__.py           ← db = SQLAlchemy(), import all models here
│   ├── user.py               ← User accounts, roles, preferences, PIN
│   ├── timelog.py            ← Chart time + face-to-face timer records
│   ├── inbox.py              ← InboxSnapshot + InboxItem diff tracking
│   ├── oncall.py             ← After-hours call notes
│   ├── orderset.py           ← OrderSet + OrderItem + OrderSetVersion
│   ├── medication.py         ← Medication reference entries
│   ├── labtrack.py           ← LabTrack criteria + LabResult values
│   ├── caregap.py            ← Preventive care gap records
│   ├── tickler.py            ← Follow-up reminder items
│   ├── message.py            ← Delayed message queue
│   ├── billing.py            ← BillingOpportunity + BillingRuleCache (Phase 10B)
│   └── reformatter.py        ← Note reformat session logs
│
├── routes/
│   ├── __init__.py
│   ├── auth.py               ← /login /logout /register /settings
│   ├── dashboard.py          ← / and /dashboard (Today View)\n│   ├── patient.py            ← /patient/<mrn> (Patient Chart View)
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
│   └── reformatter.py        ← /reformatter
│
├── templates/
│   ├── base.html             ← Shared layout: nav, header, auto-lock
│   ├── login.html
│   ├── dashboard.html        ← Today View
│   └── [one .html per route]
│
├── static/
│   ├── css/main.css          ← All styles, CSS custom properties
│   └── js/
│       ├── main.js           ← Shared JS: dark mode, auto-lock, clock
│       └── service-worker.js ← Offline caching
│
├── agent/
│   ├── mrn_reader.py         ← OCR loop: reads MRN every 3 seconds
│   ├── inbox_monitor.py      ← Inbox OCR + diff snapshot comparison
│   ├── inbox_reader.py       ← Filter dropdown cycling + OCR row extraction
│   ├── ac_window.py          ← win32gui window management + MRN from title bar
│   ├── ocr_helpers.py        ← OCR-first element detection engine for AC automation
│   ├── clinical_summary_parser.py ← XML CDA parser, all structured sections
│   ├── scheduler.py          ← APScheduler job definitions
│   ├── notifier.py           ← Pushover sender with quiet hours logic
│   ├── pyautogui_runner.py   ← Amazing Charts mouse/keyboard executor
│   ├── note_prep.py          ← Nightly pre-visit note automation
│   ├── note_reader.py        ← Note capture for reformatter
│   ├── note_parser.py        ← Section header detection (uses AC_NOTE_SECTIONS)
│   ├── note_classifier.py    ← Medication + diagnosis classification
│   ├── note_reformatter.py   ← Template filling engine
│   ├── caregap_engine.py     ← USPSTF rules evaluation
│   ├── eod_checker.py        ← End-of-day pending items check
│   └── morning_briefing.py   ← Daily summary generator
│
├── utils/
│   └── api_client.py         ← get_cached_or_fetch() + rate limiter for all APIs
│
├── scrapers/
│   └── netpractice.py        ← Playwright schedule + messaging scraper
│
├── macros/
│   ├── np_companion.ahk      ← AutoHotkey v2 macro script
│   └── macros.json           ← Macro definitions (loaded by .ahk)
│
├── Documents/
│   ├── copilot-instructions.md     ← This file
│   ├── NP_Companion_Development_Guide.md
│   ├── API_Integration_Plan.md     ← Full API spec, caching, offline, Phase 10
│   ├── ac_interface_reference.md   ← AC UI reference for all automation
│   ├── AC_Patient_Info_Guide.md    ← Patient data pipeline chapter
│   ├── VERIFICATION_CHECKLIST.md   ← Step-by-step deploy verification
│   └── ac_interface_reference/     ← AC SCREENSHOTS + sample files
│       ├── Amazing charts interface/
│       │   ├── ..md files/
│       │   │   └── ac_interface_reference_v4.md  ← GROUND TRUTH (latest)
│       │   ├── screenshots/           ← 50+ AC screenshots
│       │   └── Order Sets/
│       │       └── AC orders.xlsx      ← Full order catalog (~870 items)
│       ├── *.png                      ← Legacy AC screenshots (10 images)
│       └── ClinicalSummary_*.xml      ← Sample CDA XML export
│
├── tests/
│   ├── __init__.py
│   ├── ac_mock.py             ← Mock provider: simulates AC using screenshots
│   └── test_agent_mock.py     ← Standalone mock test runner (26 tests)
│
└── data/                     ← Runtime only — excluded from Git
    ├── npcompanion.db        ← SQLite database
    ├── np_session.pkl        ← NetPractice Playwright session cookies
    ├── active_user.json      ← Currently active provider ID for agent
    ├── config_backup.py      ← Previous config.py state (before last save)
    ├── clinical_summaries/   ← XML exports, auto-deleted after 183 days
    └── backups/              ← Nightly database backups
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
code suggestion without exception.**

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
Application logs written to files or printed to console must never contain
patient names or full MRNs. Use hashed identifiers or last-4 of MRN only.

```python
import hashlib

def safe_patient_id(mrn: str) -> str:
    """Returns a non-reversible hash for logging purposes."""
    return hashlib.sha256(mrn.encode()).hexdigest()[:12]

# In logs:
logger.info(f"Session opened for patient {safe_patient_id(mrn)}")
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
# In templates, always use:
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

```python
# Before allowing discard:
reformat_session.discarded_items = json.dumps(
    existing_discards + [{"text": item_text, "reason": reason,
                          "discarded_at": datetime.utcnow().isoformat(),
                          "discarded_by": current_user.id}]
)
db.session.commit()
# THEN remove from working state
```

---

## External API Conventions

NP Companion integrates 17+ free government APIs (NIH, FDA, CMS, CDC, AHRQ).
The full API specification is in **`Documents/API_Integration_Plan.md`** —
the authoritative reference for all API details, endpoints, and caching.

### API Client Pattern
All API calls go through `utils/api_client.py` using the `get_cached_or_fetch()`
helper. This ensures cache-first behavior, graceful degradation, and no PHI
leakage. Never make raw `requests.get()` calls to external APIs from routes
or agent modules — always use the api_client helper.

```python
from utils.api_client import get_cached_or_fetch
from models.patient import RxNormCache

# CORRECT — cache-first with graceful fallback
data = get_cached_or_fetch(RxNormCache, rxcui, fetch_rxnorm_properties)

# WRONG — direct API call bypasses cache and offline handling
data = requests.get(f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json").json()
```

### Cache Table Pattern
All cache tables inherit the same structure as `Icd10Cache`:
- `lookup_key` (indexed, unique) — the search key
- `response` (Text) — JSON string of the full API response
- `fetched_at` (DateTime) — when fetched
- `expires_at` (DateTime, nullable) — null means permanent cache

### No PHI in Outbound Requests
API calls contain ONLY clinical vocabulary:
- Drug names, RXCUI codes (RxNorm, OpenFDA)
- ICD-10 diagnosis codes (ICD-10, UMLS)
- LOINC lab codes (LOINC)
- Age and sex (HealthFinder — never names/DOBs/MRNs)
- CPT/HCPCS codes (CMS PFS)

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

### New Files for API Integration
- `utils/api_client.py` — shared `get_cached_or_fetch()` helper, rate limiter
- `models/billing.py` — `BillingOpportunity`, `BillingRuleCache` models
- Cache table models added to `models/patient.py` (following `Icd10Cache` pattern)

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

The agent (agent.py) and Flask app (app.py) are two **separate processes**
that communicate only through the shared SQLite database and the
`data/active_user.json` file. They never call each other directly.

```
Flask app (port 5000)    ←——— browser requests ———→   User's browser
        ↕ reads/writes
   SQLite database
        ↕ reads/writes
Background agent         ←——— status JSON (port 5001) ←— Flask app polls
```

The agent exposes a minimal status endpoint on port 5001:
```python
# GET http://localhost:5001/status returns:
{
    "is_running": true,
    "last_heartbeat": "2025-01-01T10:00:00",
    "active_mrn_hash": "abc123...",
    "active_user_id": 3,
    "jobs": {"inbox_check": "2025-01-01T09:58:00", ...}
}
```

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

    /* Dark mode variants are set on [data-theme="dark"] */
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

```javascript
// In main.js — on page load:
const theme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', theme);
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
Endpoints called by JavaScript return JSON and follow this pattern:
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

```javascript
// Standard polling pattern used throughout the project:
async function pollStatus() {
    try {
        const response = await fetch('/api/some-status');
        const data = await response.json();
        updateUI(data);
    } catch (err) {
        showOfflineBanner();
    }
}
setInterval(pollStatus, 10000); // every 10 seconds
```

---

## Amazing Charts Interface Reference

**ALWAYS READ THIS FILE FIRST** before writing any AC automation code:
`Documents/ac_interface_reference/Amazing charts interface/..md files/ac_interface_reference_v4.md`

This is the definitive ground truth (2788 lines, v4) for the entire AC
desktop application UI. It supersedes all prior versions.

### What the reference covers:
- Window identification: title bar regex, process name, 4 AC states
- Home screen: 6-zone layout (toolbar, patient list, inbox, schedule, buttons, status bar)
- Inbox panel: 7 filter options (Labs, Radiology, Messages, Calls, Chart Notes, Show All, **Show Everything**)
- Patient chart: 6 tabs (Demographics F5, Summary Sheet F6, Most Recent F7, Past Encounters F8, Imported Items F9, Account Info F11)
- Patient menu: full item list with keyboard shortcuts
- Print/Export dialogs: Notes & Letters, clinical summary XML export
- Login flow: login screen fields, automation approach
- AC state detection: not_running → login_screen → home_screen → chart_open
- Resurrect note dialog handling
- Summary sheet: chronicity editing, problem resolution workflow
- Past encounters tab: alternative to OCR for reading old notes
- Imported items: accessible via network share `\\192.168.2.51\amazing charts\ImportItems\[MRN]\`
- Dialogs: Set Flags, Confidential tab, Physical Exam (vitals grid), Allergies (search-as-you-type), Medications (read-only textbox), Set Reminder (reveals provider roster), Diagnoses (assessment vs problem list), CDS window (USPSTF), Risk Factors (checkbox list)
- Template system: personal + practice-wide templates
- Toolbar button layout confirmed
- Database discovery: SQL Server at `\\192.168.2.51\Amazing Charts\AmazingCharts.mdf`

### AC System Information (confirmed from v4)
| Property | Value |
|---|---|
| AC Version | 12.3.1 (build 297) |
| AC Process Title | `Amazing Charts EHR (32 bit)` |
| AC Executable | `C:\Program Files (x86)\Amazing Charts\AmazingCharts.exe` |
| Practice ID | 2799 |
| Practice Name | Family Practice Associates of Chesterfield |
| AC Log Path | `C:\Program Files (x86)\Amazing Charts\Logs` |
| AC Database | `\\192.168.2.51\Amazing Charts\AmazingCharts.mdf` (SQL Server) |
| Imported Items Path | `\\192.168.2.51\amazing charts\ImportItems\[MRN]\` |

### Work PC Specs (confirmed from v4)
| Property | Value |
|---|---|
| OS | Windows 11 Pro |
| PC | HP EliteDesk 705 G5 |
| CPU | AMD Ryzen 5 PRO 3400G |
| RAM | 16 GB |
| GPU | AMD Radeon Vega 11 |
| Username | `FPA-D-NP-DENTON\FPA` |

### Screenshot Library
The original 10 screenshots + 1 XML are in `Documents/ac_interface_reference/`.
50+ new screenshots are in `Documents/ac_interface_reference/Amazing charts interface/screenshots/`.
The full order catalog (~870 items with CPT codes) is at `Documents/ac_interface_reference/Amazing charts interface/Order Sets/AC orders.xlsx`.

| Legacy Screenshots (original 10) | Shows |
|---|---|
| `home screen pateitn chart highlighted.png` | AC main window with all zones |
| `Inbox lab home page.png` | Inbox panel with lab items |
| `AC inbox drop down filter options .png` | Inbox filter dropdown open |
| `fresh open patient chart.png` | Patient chart (Most Recent Encounter) |
| `navigate to clinical summary.png` | Patient menu → Export Clinical Summary |
| `patient, print last note menu tab.png` | Patient menu → Print submenu |
| `print notes_letters last note opening page .png` | Notes & Letters dialog |
| `print notes_letters last note opening page variable 2 .png` | Notes & Letters variant |
| `export to HIE & PHR.png` | Export to HIE dialog |
| `reports tab.png` | Reports/Search view |
| `ClinicalSummary_PatientId_62815_*.xml` | Real CDA XML export (test patient) |

### Order Catalog Summary (from AC orders.xlsx)
| Tab Name | Item Count | Notes |
|---|---|---|
| Nursing | ~163 | Includes CPT codes, injections, procedures, quality measures (CO/MA/MC prefixed) |
| Labs | ~416 | Includes LabCorp test numbers |
| Imaging | ~70 | X-ray items |
| Diagnostics | ~220 | CT, MRI, ultrasound, stress tests, etc. |
| Referrals | 0 | Empty column — not populated in AC |
| Follow Up | 0 | Empty column |
| Patient Education | 0 | Empty column |
| Other | 0 | Empty column |

When writing new automation for AC, always check the v4 reference doc to
confirm the exact text label that OCR should search for.

---

## AC Database — Direct Access Potential

**Discovery (v4):** The AC database is a SQL Server `.mdf` file accessible
at `\\192.168.2.51\Amazing Charts\AmazingCharts.mdf`. This means direct
database reads may be possible, which could eliminate many OCR-based
workarounds for reading patient data.

**Status:** Not yet tested. Before using:
1. Confirm read-only SQL Server access from the work PC
2. Map the database schema (tables, columns, relationships)
3. Determine whether AC uses SQL Server Express LocalDB or a full instance
4. Test that reading from the DB does not interfere with AC's live operation

**If DB access works**, it could replace OCR for:
- Patient demographics lookup (instead of OCR on title bar)
- Medication list retrieval (instead of navigating the Medications dialog)
- Lab results / vital signs (instead of clinical summary XML export)
- Allergen list (instead of OCR on Allergies dialog)
- Diagnosis / problem list extraction

**Rule:** Until DB access is tested and confirmed safe, all existing OCR-based
automation remains the primary approach. DB access is an enhancement, not
a replacement — OCR code stays as fallback.

---

## AC State Detection (from v4)

The agent should detect which of 4 states AC is in before performing any
automation. This prevents automation from running against the wrong screen.

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
3. If no chart regex match but AC window exists, check for "Amazing Charts Login"
   in title → `login_screen`, otherwise → `home_screen`
4. If no AC window → `not_running`

**Resurrect Note Dialog:** When opening a previously saved-but-not-finished
note, AC may show a "Resurrect [date] note?" dialog. Automation must handle
this by clicking "Yes" or "No" as appropriate before proceeding.

---

## AC Mock Mode (Testing Without Amazing Charts)

Set `AC_MOCK_MODE = True` in config.py to test the agent pipeline on any
machine that doesn't have Amazing Charts installed.

**How it works:**
- `agent/ac_window.py` returns simulated window data (title bar, MRN, DOB)
- `agent/ocr_helpers.py` loads reference screenshots instead of screen captures
- All modules above (mrn_reader, inbox_reader, clinical_summary_parser) run
  their real logic against the screenshot images — validating OCR detection,
  text matching, and data flow
- The mock provider lives in `tests/ac_mock.py`

**At deployment:** Set `AC_MOCK_MODE = False` (the default). All mock code
paths are skipped. No recoding needed — mock code sits silent forever.

**To run mock tests:**
```powershell
venv\Scripts\python.exe tests/test_agent_mock.py
```

**Test patient data (from screenshots + XML):**
- MRN: 62815
- Name: TEST, TEST
- DOB: 10/1/1980
- Age: 45, Female

---

## PyAutoGUI / Amazing Charts Automation Rules

**OCR-FIRST APPROACH** — All UI element detection must use Tesseract OCR
to find elements by their visible text labels before falling back to
coordinates. This makes automation portable across any machine, screen
resolution, window size, or window position.

The OCR detection engine lives in `agent/ocr_helpers.py`. Key functions:
- `find_and_click(text)` — find text via OCR and click it
- `find_text_on_screen(text)` — find screen coordinates of a label
- `find_element_near_text(anchor, direction, offset)` — find adjacent elements
- `screenshot_region_near_text(anchor)` — screenshot a region near a label

1. **Always use OCR to find UI elements first:**
```python
from agent.ocr_helpers import find_and_click, find_element_near_text

# CORRECT — OCR-first with optional coordinate fallback
find_and_click('Export Clinical Summary',
               fallback_xy=config.EXPORT_CLIN_SUM_MENU_XY)

# WRONG — hardcoded coordinates as primary method
pyautogui.click(*config.EXPORT_CLIN_SUM_MENU_XY)
```

2. **Coordinates are FALLBACK ONLY:**
   Config.py coordinate values (e.g. `EXPORT_BUTTON_XY`) exist solely as
   last-resort fallbacks when OCR cannot find the expected text. When
   writing new automation, always pass coordinates as `fallback_xy=`
   parameter, never as the primary click target.

3. **Always verify Amazing Charts is the foreground window before any click:**
```python
import win32gui

def is_amazing_charts_active():
    hwnd = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(hwnd)
    return 'Amazing Charts' in title
```

4. **Always take a screenshot before executing any order set:**
```python
screenshot = pyautogui.screenshot()
screenshot.save(f'data/screenshots/pre_exec_{timestamp}.png')
```

5. **Always add delays between actions** to give Amazing Charts time to respond:
```python
import time
pyautogui.click(x, y)
time.sleep(0.5)  # minimum — increase if AC is slow
```

6. **Stop immediately on any failure** — never continue a partially completed
   automation. Log what was completed and what wasn't.

7. **Use keyboard shortcuts whenever possible** — `Alt+P` for Patient menu,
   `Ctrl+S` to save, etc. These never change position and don't need OCR.
   See AC_SHORTCUTS reference table below.

---

## Playwright / NetPractice Scraper Rules

1. **Always load the saved session before navigating:**
```python
import pickle

async def load_session(context):
    if os.path.exists(config.SESSION_COOKIE_FILE):
        with open(config.SESSION_COOKIE_FILE, 'rb') as f:
            cookies = pickle.load(f)
        await context.add_cookies(cookies)
```

2. **Always check for Google login redirect before scraping:**
```python
async def is_session_valid(page):
    await page.goto(config.NETPRACTICE_URL)
    return 'accounts.google.com' not in page.url
```

3. **Never automate the Google login itself.** If re-auth is needed:
   - Set `needs_reauth = True` in the database
   - Send a Pushover notification to the provider
   - Skip the scrape attempt and wait

4. **Include placeholder comments for CSS selectors** that will need
   updating once the developer provides NetPractice screenshots:
```python
# TODO: Update selector once NetPractice schedule page is inspected
# Expected: a row element per appointment in the day view
appointments = await page.query_selector_all('.appointment-row')
```

---

## OCR / MRN Reader Rules

1. **Always preprocess images before OCR:**
```python
from PIL import Image, ImageFilter, ImageEnhance

def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    image = image.convert('L')                    # grayscale
    image = image.resize(                          # upscale 2x
        (image.width * 2, image.height * 2),
        Image.LANCZOS
    )
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)                  # increase contrast
    return image
```

2. **Always validate MRN format after OCR** — never trust raw OCR output:
```python
import re

def is_valid_mrn(text: str) -> bool:
    """MRN is expected to be 6-10 numeric digits. Update regex if format differs."""
    return bool(re.match(r'^\d{6,10}$', text.strip()))
```

3. **MRN capture uses the AC window position** — the OCR fallback in
   `mrn_reader.py` finds the AC window via `win32gui.GetWindowRect()` and
   screenshots just its title bar (top 60 pixels). No static region config
   is needed. `config.MRN_CAPTURE_REGION` exists only as a last-resort
   fallback if the window rect lookup fails:
```python
from agent.ocr_helpers import get_ac_window_rect

rect = get_ac_window_rect()
if rect:
    left, top, right, _ = rect
    region = (left, top, right, top + 60)  # Title bar only
else:
    region = config.MRN_CAPTURE_REGION  # Fallback
```

4. **Use `agent/ocr_helpers.py` for all new OCR work** — the standard
   preprocessing, word-level bounding boxes, and multi-word phrase matching
   are already built there. Don't reinvent OCR patterns.

---

## Notification Rules

All notifications go through `agent/notifier.py`. Never call Pushover
directly from routes or other modules.

```python
from agent.notifier import Notifier

notifier = Notifier()

# Normal notification (respects quiet hours):
notifier.send(user_id=current_user.id, title="Inbox Update",
              message="New labs: 2, Messages: 1")

# Critical (bypasses quiet hours — use only for clinical urgency):
notifier.send_critical(user_id=current_user.id, title="CRITICAL VALUE",
                       message="Critical flag in inbox. Log in immediately.")
```

Pushover priority levels used in this project:
- `-1` — Quiet (no sound, no interruption)
- ` 0` — Normal (default)
- ` 1` — High priority (bypasses quiet hours)
- ` 2` — Emergency (requires acknowledgment, reserved for critical values only)

---

## Error Handling Conventions

```python
# In routes — user-facing errors return JSON or redirect with flash message:
try:
    result = some_operation()
except Exception as e:
    db.session.rollback()
    app.logger.error(f"Error in module.action: {str(e)}")
    return jsonify({"success": False, "error": "Operation failed"}), 500

# In agent jobs — never let exceptions propagate and crash the agent:
try:
    run_inbox_check(user_id)
except Exception as e:
    log_agent_error(user_id=user_id, job='inbox_check',
                    error=str(e), traceback=traceback.format_exc())
    # Continue — do not re-raise
```

---

## Build Phases — Current Status Reference

The project is built in 9 phases. When Copilot suggests code, it should
be consistent with what has already been built in completed phases and
should not reference modules or tables from future phases unless explicitly
asked.

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

## Feature Reference

> **Single source of truth for feature specs:** `Documents/NP_Companion_Development_Guide.md`
> The dev guide has the complete feature list (94 features across 9 phases),
> detailed prompts, and the Master Build Checklist with status tracking.
> This file contains only coding rules and technical conventions.

For a quick phase overview, see the Build Phases table above.

---

## Sensitive Files — Never Suggest Committing These

```
config.py           ← API tokens, IP addresses, screen coordinates
data/               ← Database, session cookies, screenshots
.env                ← If used
*.pkl               ← Playwright session files
*.log               ← Application logs
venv/               ← Virtual environment
```

---

## Common Mistakes to Avoid

1. **Don't use `Query.all()` without a `filter_by(user_id=...)`** in any
   table that has a user_id column.

2. **Don't suggest JavaScript frameworks** — this project uses vanilla JS only.

3. **Don't suggest environment variables** — config comes from `config.py`.

4. **Don't use `datetime.utcnow()`** — it's deprecated. Use
   `datetime.now(timezone.utc)` instead.

5. **Don't use `db.session.delete()`** on clinical records — use soft
   deletion flags (`is_archived`, `is_resolved`).

6. **Don't put patient names or MRNs in notification bodies** — ever.

7. **Don't hardcode pixel coordinates** — use `agent/ocr_helpers.py` to find
   elements by text via OCR. Config coordinates are fallback-only, passed via
   `fallback_xy=` parameter. Never use coordinates as the primary detection
   method.

8. **Don't suggest `python-dotenv`** — not used in this project.

9. **Don't use `redirect(request.referrer)`** — it's fragile. Always
   redirect to a named route: `redirect(url_for('module.index'))`.

10. **Don't skip the pre-execution screenshot** in PyAutoGUI runner — it
    is required for the order execution audit trail.

---

## Amazing Charts Keyboard Shortcuts

Reference table for all confirmed AC keyboard shortcuts. Use these in
PyAutoGUI automation scripts. All require a patient chart window to be
open and focused unless noted otherwise.

```python
AC_SHORTCUTS = {
    # Patient chart tab navigation
    'demographics':          'F5',
    'summary_sheet':         'F6',
    'most_recent_encounter': 'F7',
    'past_encounters':       'F8',
    'imported_items':        'F9',
    'account_information':   'F11',
    # Patient menu items (Alt+P opens menu)
    'patient_menu':          'Alt+P',
    'medications':           'Ctrl+M',     # Opens medication window
    'health_risk_factors':   'Ctrl+H',     # Opens risk factors checkbox list
    'immunizations':         'Ctrl+I',     # Opens immunization window
    'print_summary_sheet':   'Ctrl+P',     # Print → Summary Sheet
    'print_messages':        'Ctrl+G',     # Print → Messages
    'tracked_data':          'Ctrl+T',     # Opens tracked data window
    # Additional confirmed shortcuts from v4
    'set_flags':             'Alt+P → Set Flags',  # Via Patient menu
    'set_reminder':          'Alt+P → Set Reminder',  # Reveals provider roster
    'confidential':          'Alt+P → Confidential',  # Role-restricted tab
    'allergies':             'Alt+P → Allergies',  # Search-as-you-type dialog
    'diagnoses':             'Alt+P → Diagnoses',  # Assessment vs Problem list
    'physical_exam':         'Alt+P → Physical Exam',  # Vitals grid
    'clinical_decision_support': 'Alt+P → Clinical Decision Support',  # CDS/USPSTF
    'export_clinical_summary': 'Alt+P → Export Clinical Summary',
    # Note editing
    'save_and_close':        'Ctrl+S',     # Saves note and closes chart
}
```

---

## Clinical Summary XML Export

### Format and Naming
- Format: HL7 CDA (Consolidated CDA / C-CDA R2.1)
- Namespace: `{'cda': 'urn:hl7-org:v3'}`
- File naming: `ClinicalSummary_PatientId_[MRN]_[YYYYMMDD]_[HHMMSS].xml`
- MRN confirmed in filename AND in `//cda:recordTarget/cda:patientRole/cda:id/@extension`
- Export folder configured once in AC, path saved in `config.py` as
  `CLINICAL_SUMMARY_EXPORT_FOLDER`
- Retention: auto-delete after 183 days (configurable via
  `CLINICAL_SUMMARY_RETENTION_DAYS` in config.py), audit log every parse

### CRITICAL — Two-Phase Export Workflow

The Clinical Summary export is a **two-phase process**. Charts must be opened
for ALL patients first (Phase 1), then XML exports happen for ALL patients
(Phase 2). Exporting **CANNOT** be triggered while a patient chart window is
open.

#### Phase 1 — Chart Opening (repeat for ALL patients before exporting)

1. In the **Patient List** panel — the blue search field underneath the
   "Schedule", "Messages", "Reports", "Secure" buttons — search by patient
   ID (from the NetPractice schedule)
2. Verify the first and last name match the expected patient
3. **Double-click** the verified name to open a new chart
4. In the chart window (title bar format:
   `LASTNAME, FIRSTNAME  (DOB: M/D/YYYY; ID: XXXXX)`)
   select the **Visit Template** radio button (not "Encounter")
5. Click the **Select Template** dropdown → **Procedure Visit** → **Companion**
6. Clear any popup boxes (click OK or X)
7. Press **Ctrl+S** to save and close the chart (this sends the note to the inbox)
8. Repeat steps 1–7 for every patient on today's schedule

#### Phase 2 — XML Export (only after ALL charts are in the inbox)

1. Ensure AC is on the **home screen** (no chart windows open)
2. Verify no window titles match the chart pattern:
   `[LASTNAME], [FIRSTNAME]  (DOB:...`
3. In the inbox, find the patient's **most recent chart** — verify by
   checking the time column, patient name, and MRN
4. Single-click the chart row to select it (do NOT double-click)
5. Navigate to `Patient menu (Alt+P) > Export Clinical Summary`
6. In the Export dialog: select **"Full Patient Record"** from the
   "Select Encounter Date" dropdown (do NOT use the default single
   encounter — we always want the complete patient record)
7. Verify all section checkboxes are checked, verify destination folder
8. Click **Export**, dismiss the success dialog (press Enter)
8. Repeat steps 3–7 for every patient on today's schedule

This is a **hard constraint** on all automation code in
`clinical_summary_parser.py`. The export function must:
- Complete Phase 1 for ALL patients before starting Phase 2
- Verify NO chart window is open before any Phase 2 export
- Close any open chart windows before triggering an export
- Confirm the AC home screen is in the foreground during Phase 2
- Always select **"Full Patient Record"** from the encounter dropdown
  (never export a single encounter — we need all patient history)

### XML Sections Available

| Section | LOINC Code | templateId (section) | Data Type |
|---------|-----------|---------------------|-----------|
| Medications | 10160-0 | 2.16.840.1.113883.10.20.22.2.1.1 | Structured |
| Allergies | 48765-2 | 2.16.840.1.113883.10.20.22.2.6.1 | Structured |
| Problems / Diagnoses | 11450-4 | 2.16.840.1.113883.10.20.22.2.5.1 | Structured |
| Vital Signs | 8716-3 | 2.16.840.1.113883.10.20.22.2.4.1 | Structured |
| Results / Labs | 30954-2 | 2.16.840.1.113883.10.20.22.2.3.1 | Structured |
| Immunizations | 11369-6 | 2.16.840.1.113883.10.20.22.2.2 | Structured |
| Social History | 29762-2 | 2.16.840.1.113883.10.20.22.2.17 | Structured |
| Encounters | 46240-8 | 2.16.840.1.113883.10.20.22.2.22.1 | Structured |
| Plan of Care | 18776-5 | 2.16.840.1.113883.10.20.22.2.10 | Narrative |
| Assessments | 51848-0 | 2.16.840.1.113883.10.20.22.2.8 | Narrative |
| Goals | 61146-7 | 2.16.840.1.113883.10.20.22.2.60 | Narrative |
| Health Concerns | 75310-3 | 2.16.840.1.113883.10.20.22.2.58 | Narrative |
| Instructions | 69730-0 | 2.16.840.1.113883.10.20.22.2.45 | Narrative |
| Mental Status | 10190-7 | 2.16.840.1.113883.10.20.22.2.56 | Narrative |
| Reason for Visit | 29299-5 | 2.16.840.1.113883.10.20.22.2.12 | Narrative |
| Progress Notes | 11506-3 | 2.16.840.1.113883.10.20.22.2.65 | Narrative |

Sections with `nullFlavor="NI"` when empty → return empty list, not an error.

---

## Canonical Note Section List

The following list matches the Enlarge Textbox window in Amazing Charts
exactly. Use this constant in `note_parser.py`, the Prepped Note tab,
the Note Reformatter, and any module that references note sections.

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

# Sections that open separate windows in the Enlarge Textbox UI
AC_SPECIAL_SECTIONS = ["Allergies", "Medications"]
```

---

## Config Editor — Implementation Rules

> Feature spec is in `Documents/NP_Companion_Development_Guide.md` (Feature 10e).
> Below are only the coding constraints:

- Before writing changes, copy current config.py → `data/config_backup.py`
- Restart Flask via `os.execv(sys.executable, [sys.executable] + sys.argv)`
- Agent monitors config.py mtime and auto-reloads without full restart
- Admin-role-only access via `@require_role('admin')`

---

## MANDATORY: Update Tracking Tables After Every Prompt

**After completing ANY prompt that adds, modifies, or fixes code, you MUST update BOTH tables in `Documents/NP_Companion_Development_Guide.md` before finishing:**

1. **ACTION ITEMS table** (top of file, within first 40 lines) — Add/remove/update rows for:
   - New calibration values that need setting
   - New config variables with placeholder defaults
   - New TODOs or FIXMEs introduced in code
   - Missing API keys or credentials
   - Migrations that need to be run
   - Any item that requires manual human action before a feature works
   - Remove items that have been completed/resolved

2. **Master Build Checklist table** (Section 9, bottom of file) — Update the status columns:
   - Change "Not Started" → "In Progress" or "Done — Needs Testing" as features are built
   - Update "AI Tested" column when you run verification (imports, routes, logic checks)
   - NEVER mark "User Verified" — only the human marks that column
   - If a feature has known issues, mark it "Done — Issues Found" and note the issue in the ACTION ITEMS table

**Also add a new `## CL#` section** at the top of `.github/ChangeLog/CHANGELOG.md` with the standard format: date, phase, summary, files changed, verification steps.

---

*Last updated: 03/17/2026. Updated with AC interface reference v4 findings:
Windows 11 Pro confirmed, AC process name confirmed, 50+ screenshots documented,
~870 orders cataloged, direct DB access discovered, AC state detection documented,
login flow/resurrect dialog documented, full keyboard shortcuts expanded, new
screenshots folder structure updated, work PC specs confirmed.*

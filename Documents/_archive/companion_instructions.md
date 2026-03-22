# CareCompanion — GitHub Copilot Instructions
# File: init.prompt.md
# Location: carecompanion/ (project root)
#
# Copilot reads this file automatically for all files in this project.
# Update it as the project evolves.

---

## Project Overview

CareCompanion is a locally-hosted clinical workflow automation platform for a
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
| OS target          | Windows 10 (work PC deployment)                 |
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
carecompanion/
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
│   └── reformatter.py        ← Note reformat session logs
│
├── routes/
│   ├── __init__.py
│   ├── auth.py               ← /login /logout /register /settings
│   ├── dashboard.py          ← / and /dashboard (Today View)
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
│   ├── scheduler.py          ← APScheduler job definitions
│   ├── notifier.py           ← Pushover sender with quiet hours logic
│   ├── pyautogui_runner.py   ← Amazing Charts mouse/keyboard executor
│   ├── note_prep.py          ← Nightly pre-visit note automation
│   ├── note_reader.py        ← Note capture for reformatter
│   ├── note_parser.py        ← Section header detection
│   ├── note_classifier.py    ← Medication + diagnosis classification
│   ├── note_reformatter.py   ← Template filling engine
│   ├── caregap_engine.py     ← USPSTF rules evaluation
│   ├── eod_checker.py        ← End-of-day pending items check
│   └── morning_briefing.py   ← Daily summary generator
│
├── scrapers/
│   └── netpractice.py        ← Playwright schedule + messaging scraper
│
├── macros/
│   ├── carecompanion.ahk      ← AutoHotkey v2 macro script
│   └── macros.json           ← Macro definitions (loaded by .ahk)
│
└── data/                     ← Runtime only — excluded from Git
    ├── carecompanion.db        ← SQLite database
    ├── np_session.pkl        ← NetPractice Playwright session cookies
    ├── active_user.json      ← Currently active provider ID for agent
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

## PyAutoGUI / Amazing Charts Automation Rules

1. **Always verify Amazing Charts is the foreground window before any click:**
```python
import win32gui

def is_amazing_charts_active():
    hwnd = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(hwnd)
    return 'Amazing Charts' in title
```

2. **Always take a screenshot before executing any order set:**
```python
screenshot = pyautogui.screenshot()
screenshot.save(f'data/screenshots/pre_exec_{timestamp}.png')
```

3. **Always add delays between actions** to give Amazing Charts time to respond:
```python
import time
pyautogui.click(x, y)
time.sleep(0.5)  # minimum — increase if AC is slow
```

4. **Stop immediately on any failure** — never continue a partially completed
   automation. Log what was completed and what wasn't.

5. **All pixel coordinates come from config.py** — never hardcode them in
   automation scripts. This allows per-machine calibration.

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

3. **MRN capture region comes from config.py:**
```python
region = config.MRN_CAPTURE_REGION  # (x, y, width, height)
screenshot = pyautogui.screenshot(region=region)
```

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

## Complete Feature Reference

The following features exist in this project. When writing code for any
feature, check this list to understand what models, routes, and templates
are expected to exist.

### Phase 1 — Foundation
- **F1** Project skeleton: Flask app, base.html, CSS, JS
- **F1a** Multi-user accounts: User model, login, register, roles
- **F1b** Role-based access: @require_role decorator, sidebar filtering
- **F1c** Dark mode: data-theme toggle, localStorage + server persistence
- **F1d** Notification preferences: per-user Pushover settings
- **F1e** Session timeout + auto-lock: PIN overlay, 5-min inactivity
- **F1f** Audit trail: AuditLog model, log_access() helper, /admin/audit-log
- **F2** Database schema: all 15 tables created upfront
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
- **F23** AutoHotkey macros: macros.json-driven, CareCompanion management UI
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

7. **Don't hardcode pixel coordinates** — they always come from `config.py`
   so each machine can be calibrated independently.

8. **Don't suggest `python-dotenv`** — not used in this project.

9. **Don't use `redirect(request.referrer)`** — it's fragile. Always
   redirect to a named route: `redirect(url_for('module.index'))`.

10. **Don't skip the pre-execution screenshot** in PyAutoGUI runner — it
    is required for the order execution audit trail.

---

*Last updated: initial setup. Update this file whenever a new phase is
completed or a significant architectural decision is made.*

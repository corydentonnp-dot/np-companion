# Changelog — CL6
**Date:** 2026-03-16
**Phase:** Phase 2 — Major Feature Build-Out + Tracking System
**Summary:** Implemented all remaining Phase 2 features: MRN Reader with idle detection and chart duration warnings (F6/6a/6b), Timer page with manual entry (F6c), Inbox Monitor with critical value detection, held items, and audit log (F5/5b/5c/5d/5f), Clinical Summary XML Exporter & Parser (F6d), Patient Search (F4f), Admin Config UI, and supporting migration + model updates. Also added comprehensive project tracking tables and mandatory update instructions.

---

## New Files Created

| File | Purpose |
|------|---------|
| `agent/ac_window.py` | pywin32 window management — find/focus AC window, extract MRN and DOB from title bar |
| `agent/mrn_reader.py` | Core MRN detection loop (3-tier: title bar → OCR region → Tesseract fallback), idle tracking, chart duration warnings |
| `agent/inbox_reader.py` | OCR-based inbox reading with 6-filter cycling, hash-based diff tracking, critical value detection |
| `agent/inbox_monitor.py` | Thin wrapper combining inbox_reader + notifier |
| `agent/notifier.py` | Pushover push notifications (counts only, never PHI), quiet hours + critical bypass |
| `agent/clinical_summary_parser.py` | Two-phase XML export/parse pipeline, CDA HL7 parsing, watchdog file observer, poll fallback |
| `models/patient.py` | PatientVitals + PatientRecord models for clinical summary data |
| `templates/patient_detail.html` | Patient detail page with vitals/meds/labs counts and refresh button |
| `templates/admin_config.html` | Browser-based config editor for Section 2/4/6/7 settings |
| `migrate_phase2_columns.py` | Migration: adds total_idle_seconds + manual_entry to time_logs, creates patient_vitals + patient_records tables |

## Files Modified

| File | Changes |
|------|---------|
| `agent.py` | Wired F6 (mrn_reader), F5 (inbox_monitor), F6d (watchdog observer); added tray calibration menu item |
| `config.py` | Added Section 7 — Amazing Charts Automation (12 config values: idle threshold, coordinate tuples, export paths) |
| `models/__init__.py` | Added PatientVitals + PatientRecord imports |
| `models/timelog.py` | Added `total_idle_seconds` and `manual_entry` columns |
| `routes/admin.py` | Added GET/POST /admin/config route with whitelist-based config editor |
| `routes/timer.py` | Complete rewrite — 6 routes: timer view, status API, manual entry, edit, delete, add note |
| `routes/inbox.py` | Complete rewrite — 6 routes: inbox view, held items, audit log (CSV), hold, resolve, status API |
| `routes/dashboard.py` | Added patient search API, patient detail page, patient refresh endpoint |
| `templates/timer.html` | Complete rewrite — active session card, manual entry form, sessions table with 3s polling |
| `templates/inbox.html` | Complete rewrite — tabbed UI (inbox/held/audit), age indicators, hold/resolve actions |
| `templates/base.html` | Added patient search input in header with debounced dropdown |
| `templates/admin_dashboard.html` | Added Config Settings card linking to /admin/config |
| `requirements.txt` | Added plyer==2.1.0, watchdog==6.0.0 |

---

## Feature Details

### F6 — MRN Reader Agent (`agent/ac_window.py` + `agent/mrn_reader.py`)
- 3-tier MRN detection: `win32gui.GetWindowText()` title bar → OCR pink bar region → Tesseract fallback
- Automatic TimeLog creation on chart open, session close on chart change/close
- Blank-timeout (60s) before closing a session
- Calibration mode via system tray menu item

### F6a — Chart Duration Warning
- Configurable `MAX_CHART_OPEN_MINUTES` (default 20)
- Toast notification via plyer when threshold exceeded
- One warning per MRN per hour to avoid alert fatigue

### F6b — Idle Detection
- `ctypes` + `GetLastInputInfo` to detect user inactivity
- Configurable `IDLE_THRESHOLD_SECONDS` (default 300)
- Accumulates `total_idle_seconds` on TimeLog entries
- Active session timer pauses display when idle

### F6c — Timer Page
- Live timer display with 3-second polling (`/api/timer-status`)
- Manual entry form for off-computer time (`manual_entry=True`)
- Edit/delete restricted to manual entries only
- Billing notes on any entry

### F5 — Inbox Monitor (`agent/inbox_reader.py` + `agent/inbox_monitor.py`)
- Cycles 6 inbox filters via PyAutoGUI click automation
- OCR reads inbox table contents per filter
- Hash-based diff tracking — new items detected, resolved items marked
- InboxSnapshot captures category counts per check

### F5b — Critical Value Detection
- Scans OCR text for CRITICAL, PANIC VALUE, STAT, H*, L*
- Critical items flagged in InboxItem records
- Pushover push with priority=1, siren sound, bypasses quiet hours

### F5c — Held Items
- POST /inbox/<id>/hold with reason text
- Separate /inbox/held view for held items
- POST /inbox/<id>/resolve clears items

### F5d — Age Indicators
- Clock icons turn yellow at INBOX_WARNING_HOURS (48h)
- Clock icons turn red at INBOX_CRITICAL_HOURS (72h)

### F5f — Audit Log
- /inbox/audit-log with date range filter
- CSV export via ?format=csv
- Shows snapshot history with category counts

### F6d — Clinical Summary Exporter & Parser
- Two-phase pipeline: export XML from AC → parse CDA HL7
- Extracts 12 sections by LOINC code (vitals, meds, allergies, problems, etc.)
- Stores to PatientVitals + PatientRecord tables
- Watchdog file observer for real-time detection + polling fallback
- 183-day retention with scheduled deletion

### F4f — Patient Search
- Debounced search input in header (300ms)
- Searches PatientRecord + Schedule models
- MRN displayed as last-4 only (HIPAA)
- Patient detail page at /patient/<mrn>

### Admin Config Editor
- Browser UI at /admin/config (admin-only)
- Whitelist of editable config keys across Sections 2, 4, 6, 7
- Reads/writes config.py directly with regex replacement
- Live config module update on save (no restart needed for runtime values)

---

## Migration Required
After deploying, run:
```powershell
venv\Scripts\python.exe migrate_phase2_columns.py
```
This adds `total_idle_seconds` and `manual_entry` columns to `time_logs`, and creates `patient_vitals` and `patient_records` tables.

## New Dependencies
```
pip install plyer==2.1.0 watchdog==6.0.0
```

---

## Verification Steps

### Step 1: Install new dependencies
```powershell
venv\Scripts\pip.exe install -r requirements.txt
```

### Step 2: Run migration
```powershell
venv\Scripts\python.exe migrate_phase2_columns.py
```

### Step 3: Start the server
```powershell
venv\Scripts\python.exe app.py
```

### Step 4: Verify pages load
- `/timer` — Timer page with active session card and manual entry form
- `/inbox` — Inbox page with tabbed UI (Inbox / Held Items / Audit Log)
- `/admin/config` — Config editor with grouped settings
- `/admin` — Dashboard should show Config Settings card
- Header search bar should appear on all authenticated pages

### Step 5: Verify agent imports
```powershell
venv\Scripts\python.exe -c "from agent.ac_window import find_ac_window; from agent.mrn_reader import read_mrn; from agent.inbox_reader import read_inbox; from agent.clinical_summary_parser import ClinicalSummaryHandler; print('OK')"
```

### Step 6: Verify model columns
```powershell
venv\Scripts\python.exe -c "from models.timelog import TimeLog; print(hasattr(TimeLog, 'total_idle_seconds'), hasattr(TimeLog, 'manual_entry'))"
```
Expected: `True True`

---

## Next Development Steps

Phase 2 feature code is now built. The following work remains before moving to Phase 3:

### Immediate — Calibration & Testing
1. **Install dependencies** — `pip install plyer watchdog` (if not already done)
2. **Run migration** — `python migrate_phase2_columns.py`
3. **Calibrate MRN Reader** — Use the tray menu "Calibrate MRN Reader" to verify title bar MRN extraction works with your AC installation
4. **Configure coordinates** — Visit `/admin/config` and set all `_XY` coordinate tuples and `INBOX_TABLE_REGION` for your screen resolution
5. **Configure Pushover** — Set `PUSHOVER_USER_KEY` and `PUSHOVER_API_TOKEN` in config or via admin UI
6. **Set export folder** — Confirm `CLINICAL_SUMMARY_EXPORT_FOLDER` points to where AC exports XML files
7. **Test each page** — Timer, Inbox, Patient Search, Config Editor

### Phase 2 Remaining Items (Not Yet Built)
- **Feature 5e** — Inbox digest email/report (scheduled summary)
- **Feature 11e** — Clinical Summary Auto-Archive cleanup job (183-day retention cron)

### Ready for Phase 3
Once calibration is verified and coordinate tuples are set, Phase 3 features can begin:
- **Feature 7** — Lab Tracking integration with agent automation
- **Feature 8** — Care Gap workflow with automated flagging
- **Feature 9** — Order management / order set builder
- **Feature 10** — Medication reconciliation with per-patient storage
- **Feature 10e** — Patient Chart View (sidebar tabs, overview widgets)
- **Feature 31** — Note Reformatter (XML-first approach with OCR fallback)

---

## Full Calibration & TODO Inventory (Project-Wide as of CL6)

All items from project inception through this changelog that require human action:

### Uncalibrated Screen Coordinates (config.py Section 7)
All set to `(0, 0)` — must be calibrated on the work PC via `/admin/config`:
| Variable | Default | Used By |
|----------|---------|---------|
| `INBOX_FILTER_DROPDOWN_XY` | `(0, 0)` | F5 inbox filter cycling |
| `INBOX_TABLE_REGION` | `(0, 0, 0, 0)` | F5 inbox OCR |
| `PATIENT_LIST_ID_SEARCH_XY` | `(0, 0)` | F6d patient chart open |
| `VISIT_TEMPLATE_RADIO_XY` | `(0, 0)` | F9 note prep |
| `SELECT_TEMPLATE_DROPDOWN_XY` | `(0, 0)` | F9 note prep |
| `EXPORT_CLIN_SUM_MENU_XY` | `(0, 0)` | F6d clinical summary export |
| `EXPORT_BUTTON_XY` | `(0, 0)` | F6d clinical summary export |
| `MRN_CAPTURE_REGION` | `(0, 0, 300, 50)` | F6 OCR fallback — verify on work PC |

### Missing API Keys & Credentials
| Variable | File | Impact |
|----------|------|--------|
| `PUSHOVER_USER_KEY` | config.py | Notifications disabled (logged as warning) |
| `PUSHOVER_API_TOKEN` | config.py | Notifications disabled (logged as warning) |

### Config Values to Verify
| Variable | Current Value | Action |
|----------|---------------|--------|
| `NETPRACTICE_URL` | hard-coded URL | Confirm production URL |
| `NETPRACTICE_CLIENT_NUMBER` | `"2034"` | Confirm client number |
| `AMAZING_CHARTS_PROCESS_NAME` | `"AmazingCharts.exe"` | Verify via Task Manager |
| `CLINICAL_SUMMARY_EXPORT_FOLDER` | `"data/clinical_summaries/"` | Confirm AC export path |

### Migrations Not Yet Run
| File | Action |
|------|--------|
| `migrate_phase2_columns.py` | Adds `total_idle_seconds` + `manual_entry` to time_logs, creates patient tables |

### Code TODOs
| Location | Description |
|----------|-------------|
| `copilot-instructions.md` L563 | Update selector for NetPractice schedule page |
| `routes/auth.py` `api_notifications()` | Stub returning `{}` — needs real endpoint when F21 is built |
| `ac_interface_reference.md` L432, L587, L598 | Three coordinate calibration TODOs for Print/Export menus |
| `ac_interface_reference.md` L693 | XPath extraction for medication entries |

### Features Not Yet Built (Planned Phase 2)
| Feature | Description |
|---------|-------------|
| F5e | Inbox Digest Report — scheduled email/push summary |
| F11e | Clinical Summary Auto-Archive — 183-day retention cron job |

### Placeholder Routes (Coming Soon pages)
| Route | Phase | Feature Area |
|-------|-------|-------------|
| `/caregap` | 5 | Care Gap Tracker |
| `/labtrack` | 4 | Lab Value Tracker |
| `/medref` | 3 | Medication Reference |
| `/metrics` | 4 | Productivity Dashboard |
| `/oncall` | 3 | On-Call Notes |
| `/orders` | 3 | Order Sets |
| `/tools` | 7 | Tools Hub |

### Tracking System Added (This CL)
- **ACTION ITEMS table** added to top of `NP_Companion_Development_Guide.md` (within first 40 lines)
- **Master Build Checklist** in Section 9 converted from bullet list to full status table with AI Tested / User Verified columns
- **Mandatory update instruction** added to `copilot-instructions.md` — both tables must be updated after every prompt

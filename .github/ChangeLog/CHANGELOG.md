# NP Companion — Consolidated Changelog

All project changes documented in reverse chronological order.
Use Ctrl+F to search. Each entry includes date, phase, summary, files changed, and verification steps.

> **New entries go at the top.** After every prompt, add a new `## CL#` section here.

---

## CL20 — 2025-07-22 — AI Assistant + Custom Right-Click Context Menu
**Phase:** Feature — AI Integration + UX Improvement
**Summary:** Added an AI assistant accessible via right-click context menu on highlighted text. Users configure their own API key + provider (OpenAI, Anthropic, xAI Grok) in Settings. HIPAA acknowledgment hard-stop before first use. Admin can toggle AI access per user. Also built a custom right-click context menu app-wide with Cut, Copy, Paste, Select All, Google Search, and UpToDate Search.

| Change | Details |
|--------|---------|
| **User model: AI columns** | Added `ai_api_key_enc` (Fernet-encrypted), `ai_provider`, `ai_enabled`, `ai_hipaa_acknowledged` columns to User model |
| **Migration script** | Created `migrate_add_ai_columns.py` — adds AI columns, enables AI for admin/provider by default |
| **Custom right-click menu** | Custom menu with Cut, Copy, Paste, Select All, Google Search, UpToDate Search. Selection-dependent items appear only when text selected |
| **AI Assistant** | Right-click menu option opens floating chat panel with selected text as context. Supports conversation history |
| **HIPAA modal** | Hard-stop acknowledgment on first use. Checkbox + explicit consent required. Persisted to database |
| **AI proxy API** | New `routes/ai_api.py` — proxies to OpenAI, Anthropic, or xAI using user's encrypted API key. Uses urllib |
| **Settings UI** | AI configuration card in Account Settings: provider dropdown, API key input, Test Connection button |
| **Admin controls** | AI column in user management table with toggle badge. `POST /admin/users/<id>/toggle-ai` route |

### Files Changed
- `models/user.py`, `routes/ai_api.py` (NEW), `routes/auth.py`, `app.py`
- `templates/base.html`, `templates/settings_account.html`, `templates/admin_users.html`
- `static/js/main.js`, `static/css/main.css`, `migrate_add_ai_columns.py` (NEW)

---

## CL19 — 2025-07-22 — Global UI Refresh + Patient Chart Interactivity + Care Gaps Fix
**Phase:** Sprint — Groups 1, 3, 6
**Summary:** Comprehensive UI refresh across the entire app. Fixed dark mode for all widgets, added browser-style controls (zoom, back/forward nav, text selection), notification bell dropdown, version in sidebar, user info popover. Made patient chart interactive: clickable toggle badges for medication status/diagnosis category, UpToDate drug links, claim button, inactive row styling. Fixed the care gaps bug by adding `patient_sex` column and normalizing DOB format.

### Group 1 — Global UI / Browser Controls

| Change | Details |
|--------|---------|
| **Dark mode widget fix** | Added `--bg-surface`, `--bg-muted`, `--bg-input`, `--border`, `--bg-success`, `--text-success`, `--bg-warning`, `--bg-danger` CSS variables to `[data-theme="dark"]`. Added dark mode overrides for `.widget`, `.widget-header`, `.widget-filter`, `.widget-input`, `.widget-table`, `.badge-*`, `.pt-header`, `.pt-no-data-banner`, `.note-textarea`, `.lab-modal-*` |
| **Ctrl+/- zoom** | New `initZoom()` in `main.js`: Ctrl+= zooms in (max 2x), Ctrl+- zooms out (min 0.5x), Ctrl+0 resets. Persists to localStorage. Uses CSS `zoom` property. |
| **Alt+Left/Right nav** | New `initNavKeys()` in `main.js`: Alt+Left calls `history.back()`, Alt+Right calls `history.forward()` |
| **Text highlight/copy** | Added `user-select: text` to `.widget-body` in patient chart inline styles |
| **Notification bell dropdown** | Wrapped bell button in positioned container, added `#notification-dropdown` div. On click: fetches `/api/notifications`, renders list or "No new notifications". Closes on outside click. CSS styles: `.notification-dropdown`, `.notif-dd-header`, `.notif-dd-body`, `.notif-dd-item`, `.notif-dd-empty` |
| **Version in sidebar** | Added `<span class="sidebar-version">v{{ app_version }}</span>` to sidebar header in `base.html`. Styled with `font-size:10px; opacity:0.55` |
| **User info popover** | Wrapped username in `#user-wrapper` container with hidden `#user-popover` div showing Name/Username/Role. Shows on mouseenter, hides on mouseleave with 200ms delay. CSS styles: `.user-popover`, `.user-popover-row`, `.user-popover-label`, `.user-popover-value` |

### Group 3 — Patient Chart Improvements

| Change | Details |
|--------|---------|
| **Claim patient button** | Added "Claim" / "✓ Claimed" button to patient chart header. Calls existing `POST /patient/<mrn>/claim` endpoint. Updates button text/style on success without page reload |
| **Diagnoses column clip** | Added `.cell-clip` CSS class (`white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:200px`). Applied to diagnosis name `<td>` with `title` attribute for hover tooltip |
| **Medications → UpToDate link** | Each medication drug name is now a hyperlink to UpToDate: `https://www.uptodate.com/contents/{first-word-lowercased}-drug-information`. Opens in new tab |
| **Toggle dx category** | Diagnosis type badge (acute/chronic) is now clickable. Calls `POST /patient/<mrn>/diagnosis/<id>/toggle-category`. Badge color and text update in-place without reload |
| **Toggle med/dx status** | Status badge (active/inactive) for both medications and diagnoses is now clickable. Calls `POST /patient/<mrn>/<type>/<id>/toggle-status`. Row toggles `.row-inactive` class |
| **Inactive row greyout** | New `.row-inactive { opacity: 0.45 }` CSS class. Applied to medication and diagnosis rows with `status != 'active'` |

### Group 6 — Care Gaps Bug Fix

| Change | Details |
|--------|---------|
| **patient_sex column** | Added `patient_sex = db.Column(db.String(10), default='')` to `PatientRecord` model. Migration script: `migrate_add_patient_sex.py` |
| **Gender extraction from XML** | Updated `clinical_summary_parser.py` to parse `<administrativeGenderCode>` from CDA XML: `code="M"` → `'M'`, `code="F"` → `'F'` |
| **DOB normalization** | `store_parsed_summary()` now converts `YYYYMMDD` → `YYYY-MM-DD` before storing. Migration also fixes existing records |
| **caregap_engine age calc** | `_calculate_age()` now accepts `%Y%m%d` format in addition to `%m/%d/%Y` and `%Y-%m-%d` |

### Backend API Routes Added

| Route | Method | Purpose |
|-------|--------|---------|
| `/patient/<mrn>/diagnosis/<id>/toggle-category` | POST | Toggle diagnosis acute ↔ chronic |
| `/patient/<mrn>/<type>/<id>/toggle-status` | POST | Toggle medication or diagnosis active ↔ inactive |

### Files Modified
| File | Changes |
|------|---------|
| `static/css/main.css` | Added 13 dark theme CSS variables, 14 dark mode widget/badge overrides, notification dropdown styles, user popover styles, `.row-inactive` class, `.sidebar-version` class |
| `static/js/main.js` | Added `initZoom()`, `initNavKeys()`, `initUserPopover()`. Updated `initNotifications()` with dropdown toggle/fetch. All three new inits registered in `DOMContentLoaded` |
| `templates/base.html` | Added sidebar version span, notification dropdown HTML, user popover HTML wrapping username |
| `templates/patient_chart.html` | Added claim button, `cell-clip` class to diagnosis names, UpToDate links on meds, clickable toggle badges (category + status), `row-inactive` class on inactive rows, `user-select:text` on widget-body. Added JS functions: `toggleDxCategory()`, `toggleItemStatus()`, `claimPatient()` |
| `routes/patient.py` | Added `toggle_dx_category()` and `toggle_item_status()` route handlers |
| `models/patient.py` | Added `patient_sex` column to `PatientRecord` |
| `agent/clinical_summary_parser.py` | Added `administrativeGenderCode` extraction, DOB normalization in `store_parsed_summary()` |
| `agent/caregap_engine.py` | Added `%Y%m%d` format to `_calculate_age()` |

### New Files Created
| File | Purpose |
|------|---------|
| `migrate_add_patient_sex.py` | Migration to add `patient_sex` column and normalize YYYYMMDD DOBs |

### Verification
```powershell
# 1. Run migration (only needed if DB already exists)
venv\Scripts\python.exe migrate_add_patient_sex.py

# 2. Start app
venv\Scripts\python.exe launcher.py

# 3. Visual checks:
#    - Toggle dark mode → widgets should have dark backgrounds, not white
#    - Ctrl+= / Ctrl+- → page zooms in/out, persists on reload
#    - Alt+Left → navigates back
#    - Click notification bell → dropdown appears
#    - Sidebar shows version number next to "NP Companion"
#    - Hover username → popover shows Name/Username/Role
#    - Patient chart: "Claim" button in header
#    - Click status badge on a medication → toggles active/inactive
#    - Click type badge on a diagnosis → toggles acute/chronic
#    - Inactive rows are greyed out (opacity 0.45)
#    - Medication names are hyperlinks to UpToDate
#    - Long diagnosis names are clipped with ellipsis, hover shows full text
#    - Text in widget tables is selectable/copyable

# 4. Re-upload XML for test patient → sex should be parsed, DOB normalized
#    → Care gaps should now appear for the patient
```

---

## CL18 — 2026-03-17 — AC Interface v4 Code Retrofit
**Phase:** Cross-cutting — AC Interface v4 Code Alignment
**Summary:** Retrofitted all existing code with confirmed AC Interface Reference v4 findings. This is the code counterpart to CL17 (documentation-only). Added 4-state AC detection, resurrect dialog handling, 7th inbox filter, CPT code support for orders, tab validation, v4-aware patient route stubs, and 3 new mock tests.

### Key Changes
- **config.py:** Added `AC_WINDOW_TITLE_PREFIX`, `AC_VERSION`, `AC_BUILD`, `AC_PRACTICE_ID`, `AC_PRACTICE_NAME`, `AC_EXE_PATH`, `AC_LOG_PATH`, `AC_DB_PATH`, `AC_IMPORTED_ITEMS_PATH`, `AC_LOGIN_USERNAME/PASSWORD`, `WORK_PC_OS`, `WORK_PC_NAME`, `AC_STATES` dict, `ORDER_TABS` list
- **ac_window.py:** Added `psutil` import, `get_ac_state()` (4-state machine), `detect_resurrect_dialog()`, `handle_resurrect_dialog()`
- **inbox_reader.py:** Added "Show Everything" as 7th filter, replaced foreground/chart check with `get_ac_state()`
- **orderset.py:** Added `ORDER_TABS` constant, `cpt_code` field on `MasterOrder`
- **pyautogui_runner.py:** Added tab name validation against `ORDER_TABS`
- **patient.py:** Updated `send_to_ac()` with AC state checks and v4 workflow notes; updated `refresh_patient()` to check ImportItems path
- **ac_mock.py:** Added `mock_get_ac_state()`, `mock_detect_resurrect_dialog()`, `mock_handle_resurrect_dialog()`, expanded `set_mock_state` to support `'login'` state
- **test_agent_mock.py:** Added 3 new tests (AC state home, AC state chart, resurrect dialog detection)

### Files Modified
| File | Changes |
|------|---------|
| `config.py` | Added `AC_WINDOW_TITLE_PREFIX` + 15 new AC system values, state constants, order tabs |
| `agent/ac_window.py` | Added psutil import, `get_ac_state()`, `detect_resurrect_dialog()`, `handle_resurrect_dialog()` |
| `agent/inbox_reader.py` | Added 7th filter "Show Everything", replaced state check with `get_ac_state()` |
| `models/orderset.py` | Added `ORDER_TABS` constant, `cpt_code` column on `MasterOrder` |
| `agent/pyautogui_runner.py` | Added tab name validation in `_execute_single_order()` |
| `routes/patient.py` | Updated `send_to_ac()` and `refresh_patient()` with v4-aware logic |
| `tests/ac_mock.py` | Added 3 mock functions for new ac_window features, expanded `set_mock_state` |
| `tests/test_agent_mock.py` | Added 3 new tests (tests 11-13), total mock tests now 39+ |
| `Documents/NP_Companion_Development_Guide.md` | Resolved ACTION ITEMS #42, #43, #45, #46, #48; updated #44, #47 to IN PROGRESS |
| `Documents/VERIFICATION_CHECKLIST.md` | Updated header to CL18, added STEP 16 for v4 retrofit verification |

### New Files Created
| File | Purpose |
|------|---------|
| `migrate_add_master_order_cpt.py` | Migration to add `cpt_code` column to `master_orders` table |
| `scripts/seed_master_orders.py` | Seed script to populate master_orders from AC orders.xlsx (~870 orders) |

### Verification
```powershell
venv\Scripts\python.exe migrate_add_master_order_cpt.py   # Add cpt_code column
venv\Scripts\python.exe test.py                            # Expected: 36 passed, 0 failed
venv\Scripts\python.exe tests\test_agent_mock.py           # Expected: 39+ passed, 0 failed
venv\Scripts\python.exe -c "import config; print(config.AC_VERSION)"                    # 12.3.1
venv\Scripts\python.exe -c "from agent.ac_window import get_ac_state; print('OK')"      # OK
venv\Scripts\python.exe -c "from models.orderset import ORDER_TABS; print(len(ORDER_TABS))"  # 8
venv\Scripts\python.exe -c "from agent.inbox_reader import INBOX_FILTERS; print(len(INBOX_FILTERS))"  # 7
```

---

## CL17 — 2026-03-17 — AC Interface Reference v4 Integration (Documentation Update)
**Phase:** Cross-cutting — Documentation & AC Reference
**Summary:** Integrated the complete AC Interface Reference v4 (2788 lines, 50+ screenshots, ~870 order catalog) into all project documentation. This is a documentation-only update — no code changes were made. The v4 reference represents the most comprehensive documentation of the Amazing Charts desktop application ever created for this project, based on hands-on exploration of the live AC application.

### Key Discoveries from v4
- **Work PC confirmed:** Windows 11 Pro (not Windows 10), HP EliteDesk 705 G5, AMD Ryzen 5 PRO 3400G, 16GB RAM
- **AC Version confirmed:** 12.3.1 (build 297), Practice ID 2799
- **AC process name confirmed:** Window title is `"Amazing Charts EHR (32 bit)"`, exe is `AmazingCharts.exe`
- **Direct database access discovered:** SQL Server at `\\192.168.2.51\Amazing Charts\AmazingCharts.mdf` — could replace OCR for many data lookups
- **Imported Items accessible via file share:** `\\192.168.2.51\amazing charts\ImportItems\[MRN]\` — patient documents without AC UI navigation
- **7th inbox filter found:** "Show Everything" was missing from the 6-filter list in `inbox_reader.py`
- **Order catalog documented:** ~870 orders across 4 tabs (Nursing ~163, Labs ~416, Imaging ~70, Diagnostics ~220) with CPT codes
- **4 AC states defined:** not_running → login_screen → home_screen → chart_open
- **Login automation documented:** Login screen fields and workflow now known
- **Resurrect Note dialog documented:** Previously unknown blocking dialog when reopening saved notes
- **Provider roster discovered:** Available from Set Reminder dialog
- **AC Log path confirmed:** `C:\Program Files (x86)\Amazing Charts\Logs`
- **50+ new screenshots** covering every major dialog, window, and workflow in AC

### Impact on Existing Code
A full analysis is in `Documents/AC_Retroactive_Update_Guide.md`. Key findings:
- `config.py` needs process name update + ~6 new config values
- `ac_window.py` needs 4-state detection, login detection, resurrect dialog handling
- `inbox_reader.py` needs 7th filter "Show Everything"
- `orderset.py` needs `cpt_code` column + ~870 order seed data
- `patient.py` stubs (`send_to_ac`, `refresh_patient`) can now be implemented with v4 knowledge
- **No changes needed:** mrn_reader, clinical_summary_parser, ocr_helpers, caregap_engine (all confirmed correctly aligned)

### Files Modified
| File | Changes |
|------|---------|
| `Documents/copilot-instructions.md` | Updated OS to Windows 11 Pro; rewrote AC Interface Reference section with v4 content, system info table, work PC specs, 50+ screenshot documentation, order catalog summary; added AC Database Direct Access section; added AC State Detection section; expanded AC_SHORTCUTS table with v4 confirmations; updated folder structure to show new subfolders; updated timestamp |
| `Documents/NP_Companion_Development_Guide.md` | Updated to Windows 11 Pro; resolved ACTION ITEMS #20 (process name), #23 (master order list), #24 (orders tab layout), #25 (order tab names); partially resolved #26 (work PC specs); added 10 new ACTION ITEMS (#41–#50) for DB access testing, state detection, login automation, resurrect dialog, inbox filter, order seeding, new config values, DB schema mapping, provider roster |
| `Documents/VERIFICATION_CHECKLIST.md` | Updated header to CL17; added confirmed Work PC Environment table with all v4 system values; added STEP 15 for verifying v4 integration (7 checks); updated mock test description for 50+ screenshots |

### New Files Created
| File | Purpose |
|------|---------|
| `Documents/AC_Retroactive_Update_Guide.md` | File-by-file analysis of how v4 findings impact every already-built module. Covers 10 files, identifies 14 prioritized action items, documents what doesn't need changing, and lists 5 new capabilities unlocked by v4 |

### Verification
```powershell
# No code changes — verify documentation files exist and are updated:
Test-Path "Documents\AC_Retroactive_Update_Guide.md"          # Should be True
Test-Path "Documents\copilot-instructions.md"                  # Should be True
Test-Path "Documents\VERIFICATION_CHECKLIST.md"                # Should be True
Test-Path "Documents\NP_Companion_Development_Guide.md"        # Should be True
# Verify v4 reference materials are in place:
Test-Path "Documents\ac_interface_reference\Amazing charts interface\..md files\ac_interface_reference_v4.md"  # Should be True
(Get-ChildItem "Documents\ac_interface_reference\Amazing charts interface\screenshots\*.png").Count  # Should be 50+
# No test suite changes — existing tests should still pass:
venv\Scripts\python.exe test.py              # Expected: 36 passed, 0 failed
venv\Scripts\python.exe tests\test_agent_mock.py  # Expected: 36 passed, 0 failed
```

---

## CL16 — 2026-03-17 — Feature 15: Care Gap Tracker (F15, F15a, F15b, F15c)
**Phase:** Phase 5 — Clinical Decision Support
**Summary:** Built the complete Care Gap Tracker with USPSTF rules engine (19 hardcoded screening rules), per-patient care gap UI with inline expansion on Today View, documentation snippet system with clipboard copy, panel-wide coverage report with outreach CSV export, and admin-editable screening rules. Care gaps auto-populate from schedule scraper. Dashboard shows gap count badges per patient. Panel report shows coverage % sorted by worst coverage with age/sex filters.

### Files Modified
| File | Changes |
|------|---------|
| `models/caregap.py` | Complete rewrite: CareGap model expanded with `patient_name`, `gap_name`, `description`, `status` (open/in_progress/addressed/declined/not_applicable), `addressed_by` FK, `updated_at`. New CareGapRule model with `gap_type` (unique), `criteria_json`, `interval_days`, `billing_code_pair`, `documentation_template`, `source` (hardcoded/api), `is_active`. |
| `models/__init__.py` | Added `CareGapRule` import |
| `routes/caregap.py` | Complete rewrite: 7 endpoints — overview with date nav, patient gaps, mark addressed (returns doc snippet), update status (decline/reopen/N/A), panel report with filters, outreach list with CSV export, JSON API for inline dashboard use |
| `routes/dashboard.py` | Added care gap count lookup — queries open gaps, builds `care_gap_counts` dict, passes to template |
| `routes/admin.py` | Added 3 routes: GET /admin/caregap-rules (list), POST /admin/caregap-rules/<id>/edit (update), POST /admin/caregap-rules/reset (reset to defaults) |
| `scrapers/netpractice.py` | Added `_evaluate_care_gaps_for_appointments()` method — triggers gap evaluation after schedule save |
| `app.py` | Added `seed_default_rules(app)` call after `db.create_all()` to populate rules on first run |
| `templates/caregap.html` | Complete rewrite: date nav, patient table with gap badges, inline expandable gap detail rows (F15a), address/decline buttons, documentation snippet modal with clipboard copy (F15b) |
| `templates/dashboard.html` | Added "Gaps" column to schedule table with count badges linking to `/caregap/<mrn>` |
| `templates/admin_dashboard.html` | Added Care Gap Rules card to admin hub |
| `test.py` | Added `care_gap_rules` to expected tables (27 total), added Admin – Gap Rules page test (36 checks total) |

### New Files Created
| File | Purpose |
|------|---------|
| `agent/caregap_engine.py` | USPSTF rules engine: 19 DEFAULT_RULES, `seed_default_rules()`, `evaluate_care_gaps()`, `evaluate_and_persist_gaps()` with age/sex/risk factor matching |
| `templates/caregap_patient.html` | Per-patient gap view: open gaps with Address/Decline/N/A, editable doc snippet textarea, addressed gaps with Copy Doc + Reopen |
| `templates/caregap_panel.html` | Panel-wide report (F15c): summary cards, coverage table sorted by worst coverage, visual coverage bars (green/yellow/red), outreach button per gap type |
| `templates/caregap_outreach.html` | Outreach list: MRN last 4 only in UI (HIPAA), CSV export with full names for MA use |
| `templates/admin_caregap_rules.html` | Admin rule editor: collapsible cards per rule, edit form (name, interval, billing code, active toggle, criteria JSON, doc template), Reset to Defaults |
| `migrate_add_caregap_columns.py` | Migration: adds 6 columns to care_gaps, creates care_gap_rules table |

### Verification
```powershell
venv\Scripts\python.exe migrate_add_caregap_columns.py  # Run migration first
venv\Scripts\python.exe test.py              # Expected: 36 passed, 0 failed
venv\Scripts\python.exe tests/test_agent_mock.py  # Expected: 36 passed, 0 failed
# Visit: /caregap (overview), /caregap/panel (panel report), /admin/caregap-rules (rule editor)
```

---

## CL15 — 2026-03-17 — Feature 14 Gap-Fill: F14a, F14b, F14c spec completion
**Phase:** Phase 4 — Clinical Tools
**Summary:** Filled spec gaps in Billing Audit Log sub-features. F14a: E&M calculator now computes BOTH MDM and time-based methods and returns whichever supports the higher level; added inline calculator widget to Timer page with "Use This Level" button; added JSON API endpoint. F14b: anomaly detector now flags upcode opportunities ("Consider higher level based on time"); clicking an anomaly flag in the billing log opens a slide-out side panel with concern explanation and resolution guidance. F14c: monthly report now shows new patient vs established patient split, comparison to prior month with delta indicators, and monthly billing email job (1st of month at 7AM via scheduler).

### Files Modified
| File | Changes |
|------|---------|
| `routes/timer.py` | Rewrote `em_calculate()` to compute both MDM + time and return higher; extracted `_em_from_mdm()` and `_em_from_time()` helpers; added `POST /billing/em-calculate-json` JSON API for inline widget; rewrote `_detect_anomalies()` to return dicts with `msg`+`type` (was plain strings); added upcode detection logic and `ANOMALY_GUIDANCE` resolution text dict; extracted `_monthly_stats()` helper; added new/estab patient split, prior month query + comparison to `monthly_report()`; passes `anomaly_guidance` to billing_log template. |
| `templates/billing_em_calculator.html` | Rewritten: single form with both MDM + time inputs, "Calculate (Higher of Two)" button, result shows recommended level + comparison of both methods side-by-side. |
| `templates/billing_log.html` | Anomaly flags now clickable buttons that open a slide-out side panel; detail rows use `a.msg` for dict-based anomalies; added panel overlay + JS for `openAnomalyPanel()`/`closeAnomalyPanel()` with per-type resolution guidance. |
| `templates/billing_log_export.html` | Updated anomaly display to use `a.msg` (dict format). |
| `templates/billing_monthly.html` | Added new/established patient split card with visual bar; added prior month comparison table with delta coloring; summary cards now show "vs prior" indicators. |
| `templates/timer.html` | Added collapsible E&M Calculator Widget card (F14a inline) with MDM + time inputs, "Use This Level" button that pre-fills active session's billing level selector; added `calcEM()` and `useThisLevel()` JS functions. |
| `agent/scheduler.py` | Added `monthly_billing_fn` parameter + 1st-of-month 7AM cron job (9th job total). |
| `agent.py` | Added `job_monthly_billing()` and `_send_monthly_billing_email()` methods for F14c. Wired `monthly_billing_fn` into `start_scheduler()`. |

### Verification
```powershell
venv\Scripts\python.exe test.py              # Expected: 35 passed, 0 failed
venv\Scripts\python.exe tests/test_agent_mock.py  # Expected: 36 passed, 0 failed
# Visit: /timer (check E&M calculator widget), /billing/log (click anomaly flags), /billing/em-calculator, /billing/monthly-report
```

---

## CL14 — 2026-03-17 — Feature 13: Productivity Dashboard + Feature 14: Billing Audit Log (F13, F13a, F13b, F13c, F14, F14a, F14b, F14c)
**Phase:** Phase 4 — Clinical Tools
**Summary:** Built the full Productivity Dashboard (7 Chart.js charts, date range picker, today-at-a-glance card, burnout early-warning indicators, anonymized benchmark comparison, weekly summary page + email job) and the Billing Audit Log (filtered audit table with expandable detail rows, anomaly detection, rationale capture, E&M calculator widget, monthly billing report with RVU totals and Chart.js distribution chart, print/PDF export).

### Files Modified
| File | Changes |
|------|---------|
| `routes/metrics.py` | Complete rewrite: 5 endpoints — dashboard index with today stats + burnout indicators, chart-data JSON API (7 chart datasets + benchmarks), weekly summary page, preview-weekly, on-call stats API. Added `_compute_burnout_indicators()`, `_compute_benchmarks()`, `_generate_weekly_summary()` helpers. |
| `templates/metrics.html` | Complete rewrite: Today at a Glance card, burnout warnings card, 7 Chart.js charts (daily count, daily time, visit type donut, avg by type bar, F2F ratio donut, inbox activity line, on-call volume bar), date range picker, export PDF button, benchmark toggle. |
| `routes/timer.py` | Added 6 F14 endpoints — billing log (filtered), billing log export, add-rationale, E&M calculator (GET+POST), monthly report. Added `_detect_anomalies()`, RVU_TABLE, EM_TIME_RANGES, MDM_LEVELS, TIME_BASED_EM constants. |
| `routes/auth.py` | Added `POST /settings/account/preference` — JSON API for saving a single preference key/value (used by benchmark toggle). |
| `agent/scheduler.py` | Added `weekly_summary_fn` parameter + Friday 5PM cron job for F13c weekly summary. |
| `agent.py` | Added `job_weekly_summary()` and `_send_weekly_email()` methods for F13c. Wired `weekly_summary_fn` into `start_scheduler()`. |

### New Files Created
| File | Purpose |
|------|---------|
| `templates/metrics_weekly.html` | F13c — Weekly summary page with stats, top visit types, inbox items, notable metric comparison |
| `templates/billing_log.html` | F14 — Billing audit log with filters, expandable detail rows, anomaly flags, rationale forms |
| `templates/billing_log_export.html` | F14 — Print-friendly billing log for PDF export |
| `templates/billing_em_calculator.html` | F14a — E&M calculator with MDM and time-based methods, quick reference table |
| `templates/billing_monthly.html` | F14c — Monthly billing report with summary cards, E&M distribution table + chart, weekly breakdown |

### Verification
```powershell
# Run tests
venv\Scripts\python.exe test.py
# Expected: 35 passed, 0 failed

venv\Scripts\python.exe tests/test_agent_mock.py
# Expected: 36 passed, 0 failed

# Start server and check
venv\Scripts\python.exe app.py
# Visit: http://localhost:5000/metrics — full productivity dashboard with 7 charts
# Visit: http://localhost:5000/metrics/weekly — weekly summary
# Visit: http://localhost:5000/billing/log — billing audit log
# Visit: http://localhost:5000/billing/em-calculator — E&M calculator
# Visit: http://localhost:5000/billing/monthly-report — monthly billing report
```

---

## CL13 — 2026-03-17 — Feature 12: Visit Timer & Face-to-Face Timer (F12, F12a, F12b, F12c)
**Phase:** Phase 4 — Clinical Tools
**Summary:** Expanded the Visit Timer from a basic session tracker into a full billing-ready timer dashboard with face-to-face tracking, billing level annotation, complex visit flags, visit type auto-tagging from schedule, CSV export, day-summary JSON, E&M distribution bar chart, and an unauthenticated room-computer widget for F2F toggling.

### Files Modified
| File | Changes |
|------|---------|
| `models/timelog.py` | Added `visit_type_source` (auto/manual, F12a) and `complexity_notes` (F12b) columns |
| `routes/timer.py` | Complete rewrite: 13 endpoints — dashboard with daily summary, billing annotation, complex flag toggle, F2F start/stop, room widget (no auth), room toggle (no auth), CSV export, day report JSON. Added `auto_tag_visit_type()` helper for F12a Schedule matching. |
| `templates/timer.html` | Complete rewrite: active session with F2F button + live elapsed, daily summary cards, E&M distribution bar chart, sessions table with inline billing level dropdown, complex star toggle, visit type with Auto/Manual badge, CSV export button |

### New Files Created
| File | Purpose |
|------|---------|
| `templates/timer_room_widget.html` | F12c — Standalone no-auth page with large "Provider Entered/Left Room" button, auto-refresh, QR placeholder |
| `migrate_add_timer_columns.py` | Migration: adds `visit_type_source`, `complexity_notes` to time_logs |

### Verification
```powershell
# Run tests
venv\Scripts\python.exe test.py
# Expected: 35 passed, 0 failed

venv\Scripts\python.exe tests/test_agent_mock.py
# Expected: 36 passed, 0 failed

# Start server and check
venv\Scripts\python.exe app.py
# Visit: http://localhost:5000/timer — full dashboard
# Visit: http://localhost:5000/timer/room-widget — room widget (no login needed)
```

---

## CL12 — 2026-03-17 — Feature 11: Lab Value Tracker (F11, F11a, F11b, F11c, F11d, F11e)
**Phase:** Phase 4 — Clinical Tools
**Summary:** Built the Lab Value Tracker from scratch — full CRUD for per-patient lab tracking with custom alert thresholds, critical value detection, Chart.js trend visualization, overdue lab notifications via scheduler, standard panel grouping (BMP, CMP, CBC, Lipids, Thyroid, Diabetes), and clinical summary auto-archive cron job.

### Files Modified
| File | Changes |
|------|---------|
| `models/labtrack.py` | Complete rewrite: `LabTrack` (critical thresholds, panel_name, is_overdue, source + computed properties: next_due, status, trend), `LabResult` (result_value, is_critical, trend_direction), `LabPanel` (components_json), `STANDARD_PANELS` dict |
| `models/__init__.py` | Added `LabPanel` import |
| `routes/labtrack.py` | Complete rewrite from placeholder: 11 routes (index, patient_detail, add_tracking, add_panel, edit_tracking, delete_tracking, add_result, trend_data JSON, overdue_count JSON, seed_panels). Helper functions: `check_overdue_labs()`, `get_overdue_lab_count()`, `_send_critical_lab_alert()` |
| `templates/labtrack.html` | Full dashboard: stats cards, add-tracking form, add-panel form, patient/lab table with status badges and trend arrows |
| `agent/scheduler.py` | Added `overdue_lab_fn` and `xml_archive_fn` job slots (daily 6AM + daily 2AM) |
| `agent.py` | Added `check_overdue_labs` import, `job_overdue_lab_check()` and `job_xml_archive_cleanup()` methods |

### New Files Created
| File | Purpose |
|------|---------|
| `templates/labtrack_patient.html` | Per-patient detail: Chart.js trend graphs (F11a), threshold range bars (F11b), panel group headers (F11d), result tables, edit/add-result forms |
| `migrate_add_labtrack_columns.py` | Migration: adds 5 columns to lab_tracks, creates lab_panels table, seeds 6 standard panels |

### Verification
```powershell
venv\Scripts\python.exe test.py
# Expected: 35 passed, 0 failed

venv\Scripts\python.exe app.py
# Visit: http://localhost:5000/labtrack — lab dashboard
# Visit: http://localhost:5000/labtrack/99999 — patient detail (empty)
```

---

## CL11 — 2026-03-17 — Feature 7 Gap Fixes + Feature 8 Migration + Test Expansion
**Phase:** Phase 3 — Feature Completion
**Summary:** Fixed 5 gaps in Feature 7 (On-Call Note Keeper): first_or_404 replaced with query+404, pending badge in nav, weekly stats on index, callback reminders in scheduler, overdue callback count endpoint. Completed Feature 8 (Order Set Manager) migration adding 3 columns + 4 tables. Created master order list template. Fixed Unicode encoding error in test_agent_mock.py. Tests expanded to 35/35 + 36/36.

### Files Modified
| File | Changes |
|------|---------|
| `routes/oncall.py` | Replaced `first_or_404()` with `.first()` + manual `abort(404)`. Added weekly stats query. Added overdue callback count endpoint. |
| `templates/oncall.html` | Added weekly stats section, callback reminder indicators |
| `templates/base.html` | Added pending on-call badge in sidebar nav |
| `tests/test_agent_mock.py` | Fixed Unicode arrow → to ASCII `->` for Windows console encoding |

### New Files Created
| File | Purpose |
|------|---------|
| `templates/orders_master.html` | F8 master order list management UI |
| `migrate_add_orderset_columns.py` | F8 migration: is_retracted, shared_by_user_id, forked_from_id + 4 new tables |

### Verification
```powershell
venv\Scripts\python.exe test.py
# Expected: 35 passed, 0 failed

venv\Scripts\python.exe tests/test_agent_mock.py
# Expected: 36 passed, 0 failed
```

---

## CL10 — 2026-03-16 — AC Mock Test Framework + Database Migration + Full Verification
**Phase:** Testing & Stability
**Summary:** Built a mock testing framework that lets the entire agent pipeline (MRN reader, inbox reader, clinical summary parser) run against reference screenshots instead of a live Amazing Charts installation. Added `AC_MOCK_MODE` config flag. Fixed a missing database migration (time_logs columns). Updated test.py to cover new patient/oncall features. Added permanent AC screenshot reference to copilot instructions. Created verification checklist for non-programmer deployment.

### New Files Created
| File | Purpose |
|------|---------|
| `tests/__init__.py` | Test package init |
| `tests/ac_mock.py` | Mock provider: simulates AC window functions and OCR using reference screenshots from `Documents/ac_interface_reference/`. Maps 10 screenshot images + 1 sample XML to different AC screen states (home, chart, inbox). |
| `tests/test_agent_mock.py` | Standalone test runner: 8 test groups (26 total checks) validating mock provider, screenshot files, ac_window mocking, OCR on screenshots, element detection, XML parsing, MRN reader pipeline, and window rect. |

### Files Modified
| File | Changes |
|------|---------|
| `config.py` | Added `AC_MOCK_MODE = True` flag (Section 2). Set to True for dev/test, False for deployment. |
| `agent/ac_window.py` | Added mock-mode interception: all 7 public functions check `_mock` before calling win32gui. When mock is active, delegates to `tests.ac_mock` functions. |
| `agent/ocr_helpers.py` | Added mock-mode interception: 7 public functions (`get_ac_window_rect`, `screenshot_ac_window`, `find_and_click`, `find_text_on_screen`, `find_element_near_text`, `screenshot_region_near_text`) check `_mock` first. When mock is active, uses screenshot images instead of live screen captures. |
| `test.py` | Added 8 new table checks (patient_vitals, patient_records, patient_medications, patient_diagnoses, patient_allergies, patient_immunizations, patient_note_drafts, handoff_links). Added Patient Chart and On-Call New page tests. Total: 26 tables, 32 checks. |
| `Documents/copilot-instructions.md` | Added "Amazing Charts Interface Reference" section with screenshot inventory table. Added "AC Mock Mode" section with usage instructions. Updated folder structure with `tests/` directory and `Documents/ac_interface_reference/` contents. |

### Database Migration
Ran `migrate_phase2_columns.py` to add missing columns:
- `time_logs.total_idle_seconds` (INTEGER DEFAULT 0)
- `time_logs.manual_entry` (BOOLEAN DEFAULT 0)

### How Mock Mode Works
```
config.AC_MOCK_MODE = True
        ↓
ac_window.py → returns fake window data (title, MRN, DOB)
ocr_helpers.py → loads screenshot images instead of live captures
        ↓
mrn_reader, inbox_reader, clinical_summary_parser
all run their REAL logic against the screenshot data
        ↓
At deployment: set AC_MOCK_MODE = False → mock code never runs
```

### Verification
```powershell
# Step 1: Run mock agent tests (26 checks)
venv\Scripts\python.exe tests/test_agent_mock.py
# Expected: "All mock tests passed! The agent pipeline works with screenshots."

# Step 2: Run main web app tests (32 checks)
venv\Scripts\python.exe test.py
# Expected: "*** ALL CHECKS PASSED ***"

# Step 3: Verify mock mode flag is set
venv\Scripts\python.exe -c "import config; print('AC_MOCK_MODE:', config.AC_MOCK_MODE)"
# Expected: AC_MOCK_MODE: True
```

---

## CL9 — 2026-03-16 — OCR-First Automation + Patient Route Cleanup
**Phase:** Architecture — Automation Portability
**Summary:** Replaced all coordinate-based Amazing Charts automation with an OCR-first detection engine. The agent now finds UI elements by their visible text labels using Tesseract, making automation portable across any machine, screen resolution, window size, or position. Hardcoded coordinates in config.py are now fallback-only. Also removed duplicate patient routes from dashboard.py (now handled by patient.py).

### New Files Created
| File | Purpose |
|------|---------|
| `agent/ocr_helpers.py` | OCR-first element detection engine: screenshots AC window, finds text via Tesseract word-level bounding boxes, computes click targets relative to text positions. Key functions: `find_and_click()`, `find_text_on_screen()`, `find_element_near_text()`, `screenshot_region_near_text()`, multi-word phrase matching. |

### Files Modified
| File | Changes |
|------|---------|
| `routes/dashboard.py` | Removed `patient_detail()` and `refresh_patient()` routes (now in `routes/patient.py`). Removed unused `PatientVitals` import. |
| `agent/inbox_reader.py` | `_click_filter()`: OCR finds "Show" dropdown text first, falls back to `INBOX_FILTER_DROPDOWN_XY`. `_ocr_inbox_table()`: OCR finds "Subject" column header to locate table, falls back to `INBOX_TABLE_REGION`. |
| `agent/clinical_summary_parser.py` | `open_patient_chart()`: OCR finds "Patient List"/"ID" label, "Visit Template", "Select Template" by text. `export_clinical_summary()`: OCR finds "Export Clinical Summary" menu item and "Export" button by text. All use `find_and_click()` with fallback. |
| `agent/mrn_reader.py` | `_try_ocr_mrn()`: Now uses `get_ac_window_rect()` to find AC window position and screenshot its title bar. Falls back to `MRN_CAPTURE_REGION` only if window rect fails. |
| `config.py` | Section 7 rewritten: header changed from "calibrate per machine" to "AMAZING CHARTS AUTOMATION". Added OCR-first explanation comments. All coordinate variables marked as "Fallback" with explanations. |
| `Documents/copilot-instructions.md` | PyAutoGUI rules section rewritten for OCR-first. MRN Reader rules updated. Common Mistakes #7 updated. Folder structure updated with `ocr_helpers.py` and `patient.py`. |
| `Documents/NP_Companion_Development_Guide.md` | ACTION ITEMS rows 1–8 and 19 marked RESOLVED (OCR-first eliminates calibration). Added row 21 for Tesseract path verification. |

### Architecture: OCR-First Detection Strategy
The old approach required each machine to have 7 screen coordinate values manually calibrated in config.py. This was fragile because:
- Different screen resolutions change pixel positions
- Different window sizes/positions change where elements appear
- Each new user machine needed fresh calibration

The new approach:
1. **Find the AC window** via `win32gui.GetWindowRect()` — gets its exact screen position
2. **Screenshot only the AC window** — no full-screen capture, works at any position
3. **OCR the screenshot** with Tesseract at word-level — gets bounding boxes for every visible text label
4. **Match target text** (e.g. "Show Charts", "Export Clinical Summary") against OCR results
5. **Compute click target** from the matching bounding box center, converted to screen coordinates
6. **Fallback to config coordinates** only if OCR fails AND a fallback is set

### Verification
```powershell
# Step 1: Verify new module imports
venv\Scripts\python.exe -c "from agent.ocr_helpers import find_and_click, find_text_on_screen, find_element_near_text, screenshot_region_near_text; print('ocr_helpers OK')"

# Step 2: Verify refactored modules import cleanly
venv\Scripts\python.exe -c "from agent.inbox_reader import read_inbox; print('inbox_reader OK')"
venv\Scripts\python.exe -c "from agent.clinical_summary_parser import open_patient_chart, export_clinical_summary; print('clinical_summary_parser OK')"
venv\Scripts\python.exe -c "from agent.mrn_reader import read_mrn; print('mrn_reader OK')"

# Step 3: Verify dashboard routes
venv\Scripts\python.exe -c "from app import create_app; app = create_app(); [print(r) for r in app.url_map.iter_rules() if 'patient' in r.rule or 'dashboard' in r.rule]"

# Step 4: Verify no 'TODO: calibrate' remains in config.py
Select-String -Path config.py -Pattern 'TODO: calibrate'
# Expected: no matches
```

---

## CL8 — 2026-03-16 — F5e Inbox Digest Report (Phase 2 Complete)
**Phase:** Phase 2 — Data Layer (Final Feature)
**Summary:** Built the Inbox Digest Report (F5e) — a scheduled daily summary of inbox activity with Pushover push notification and web UI. This completes all Phase 2 coding; only calibration of screen coordinates and API keys remains.

### New Files Created
| File | Purpose |
|------|---------|
| `agent/inbox_digest.py` | Digest generator: queries InboxSnapshot + InboxItem for configurable time window, computes trends, category breakdown, builds de-identified summary message, sends via Pushover |

### Files Modified
| File | Changes |
|------|---------|
| `routes/inbox.py` | Added `GET /inbox/digest` route with period selector (8h–7d) and CSV export |
| `templates/inbox.html` | Added Digest tab with summary stats, trend indicator, category breakdown, current totals |
| `config.py` | Added 4 config vars: `INBOX_DIGEST_ENABLED`, `INBOX_DIGEST_HOURS`, `INBOX_DIGEST_SEND_HOUR`, `INBOX_DIGEST_SEND_MINUTE` |
| `agent/scheduler.py` | Added optional `digest_fn` cron job parameter to `build_scheduler()` |
| `agent.py` | Added `job_inbox_digest()` method, wired digest cron job into `start_scheduler()` |
| `Documents/NP_Companion_Development_Guide.md` | Updated ACTION ITEMS (row 17) and Master Build Checklist (F5e → Done) |

### Feature Details
- **Web UI** — New "Digest" tab on `/inbox` page. Configurable lookback period (8h, 12h, 24h, 48h, 72h, 7d). Shows: new/resolved/unresolved/critical/held/overdue counts, trend indicator (improving/stable/growing based on first-half vs second-half snapshot averages), category breakdown table, current inbox totals. CSV export available.
- **Scheduled Push** — Daily cron job at configurable hour (default 5 PM). Sends de-identified Pushover notification with quiet priority (-1). Skips if no activity in the period.
- **On-demand** — Visit `/inbox/digest` anytime for current report.
- **HIPAA compliant** — Message contains only category counts and trend, never patient names or MRNs.

### Verification
```powershell
# Step 1: Verify imports
venv\Scripts\python.exe -c "from agent.inbox_digest import generate_digest, run_digest_job; print('OK')"

# Step 2: Verify route registered
venv\Scripts\python.exe -c "from app import create_app; app = create_app(); print([r.rule for r in app.url_map.iter_rules() if 'digest' in r.rule])"
# Expected: ['/inbox/digest']

# Step 3: Verify digest runs without error
venv\Scripts\python.exe -c "from app import create_app; app = create_app(); exec('with app.app_context():\\n from agent.inbox_digest import generate_digest\\n print(generate_digest(1))')"

# Step 4: Start server and visit /inbox → click Digest tab
venv\Scripts\python.exe app.py
# Visit: http://localhost:5000/inbox → Digest tab
```

---

## CL7 — 2026-03-16 — Documentation Consolidation
**Phase:** Project Management
**Summary:** Consolidated 6 individual changelog files + day1 log + original changelog.md into this single file. Removed duplicate feature specs from copilot-instructions.md (dev guide is now the single source of truth for feature specs). Old files preserved in `.github/ChangeLog/archive/`.

### Changes
- Created `.github/ChangeLog/CHANGELOG.md` (this file) — single rolling changelog
- Moved old `cl1.md`–`cl6.md`, `changelog.md`, `day1_dev_log.md` into `.github/ChangeLog/archive/`
- Trimmed `Documents/copilot-instructions.md` — removed duplicated feature descriptions, kept only coding rules/conventions/tech specs
- Updated changelog references in copilot-instructions.md to point to this file

### Verification
- Open `.github/ChangeLog/CHANGELOG.md` — all CL entries plus foundation entries present
- Old files preserved in `.github/ChangeLog/archive/` for reference
- `copilot-instructions.md` no longer duplicates feature specs from the dev guide

---

## CL6 — 2026-03-16 — Phase 2 Feature Build-Out + Tracking System
**Phase:** Phase 2 — Data Layer (Major Build)
**Summary:** Implemented all remaining Phase 2 features: MRN Reader with idle detection + chart duration warnings (F6/6a/6b), Timer page with manual entry (F6c), Inbox Monitor with critical value detection, held items, and audit log (F5/5b/5c/5d/5f), Clinical Summary XML Exporter & Parser (F6d), Patient Search (F4f), Admin Config UI, migration helper, and project tracking tables.

### New Files Created
| File | Purpose |
|------|---------|
| `agent/ac_window.py` | pywin32 window management — find/focus AC window, extract MRN and DOB from title bar |
| `agent/mrn_reader.py` | Core MRN detection loop (3-tier: title bar → OCR → Tesseract fallback), idle tracking, chart warnings |
| `agent/inbox_reader.py` | OCR-based inbox reading with 6-filter cycling, hash-based diff tracking, critical value detection |
| `agent/inbox_monitor.py` | Thin wrapper combining inbox_reader + notifier |
| `agent/notifier.py` | Pushover push notifications (counts only, never PHI), quiet hours + critical bypass |
| `agent/clinical_summary_parser.py` | Two-phase XML export/parse pipeline, CDA HL7 parsing, watchdog observer + poll fallback |
| `models/patient.py` | PatientVitals + PatientRecord models |
| `templates/patient_detail.html` | Patient detail page with vitals/meds/labs counts |
| `templates/admin_config.html` | Browser-based config editor grouped by section |
| `migrate_phase2_columns.py` | Migration: total_idle_seconds + manual_entry on time_logs, patient_vitals + patient_records tables |

### Files Modified
| File | Changes |
|------|---------|
| `agent.py` | Wired F6 (mrn_reader), F5 (inbox_monitor), F6d (watchdog observer); tray calibration item |
| `config.py` | Added Section 7 — AC Automation (12 config values) |
| `models/__init__.py` | Added PatientVitals + PatientRecord imports |
| `models/timelog.py` | Added `total_idle_seconds` and `manual_entry` columns |
| `routes/admin.py` | Added GET/POST /admin/config with whitelist-based config editor |
| `routes/timer.py` | Complete rewrite — 6 routes (view, status API, manual entry, edit, delete, note) |
| `routes/inbox.py` | Complete rewrite — 6 routes (view, held, audit-log, hold, resolve, status API) |
| `routes/dashboard.py` | Added patient search API, patient detail page, refresh endpoint |
| `templates/timer.html` | Complete rewrite — active session card, manual entry, sessions table, 3s polling |
| `templates/inbox.html` | Complete rewrite — tabbed UI (inbox/held/audit), age indicators, hold/resolve |
| `templates/base.html` | Added patient search input in header with debounced dropdown |
| `templates/admin_dashboard.html` | Added Config Settings card |
| `requirements.txt` | Added plyer==2.1.0, watchdog==6.0.0 |
| `Documents/copilot-instructions.md` | Added mandatory table-update instructions |
| `Documents/NP_Companion_Development_Guide.md` | Added ACTION ITEMS table (top) + Master Build Checklist status table (Section 9) |

### Feature Details
- **F6 MRN Reader** — 3-tier: `win32gui.GetWindowText()` → OCR pink bar → Tesseract. Auto TimeLog create/close. 60s blank timeout. Tray calibration menu.
- **F6a Chart Duration Warning** — Toast via plyer at MAX_CHART_OPEN_MINUTES (default 20). One per MRN per hour.
- **F6b Idle Detection** — ctypes GetLastInputInfo, IDLE_THRESHOLD_SECONDS (300). Accumulates total_idle_seconds.
- **F6c Timer Page** — Live display with 3s polling. Manual entry form. Edit/delete for manual only. Billing notes.
- **F5 Inbox Monitor** — 6-filter cycling via PyAutoGUI. OCR + hash diff. InboxSnapshot category counts.
- **F5b Critical Values** — Scans for CRITICAL/PANIC/STAT/H*/L*. Pushover priority=1, siren, bypasses quiet hours.
- **F5c Held Items** — hold with reason, resolve, separate /inbox/held view.
- **F5d Age Indicators** — Yellow at 48h, red at 72h (configurable).
- **F5f Audit Log** — /inbox/audit-log with date range + CSV export.
- **F6d Clinical Summary** — Export XML from AC → parse CDA HL7 (12 sections by LOINC). Store to PatientVitals/PatientRecord. Watchdog + poll. 183-day retention.
- **F4f Patient Search** — Debounced header search (300ms). PatientRecord + Schedule. MRN last-4 only (HIPAA). Detail page at /patient/<mrn>.
- **Admin Config Editor** — /admin/config, whitelist of editable keys, regex config.py rewrite, live module update.

### Migration Required
```powershell
venv\Scripts\python.exe migrate_phase2_columns.py
```

### New Dependencies
```
pip install plyer==2.1.0 watchdog==6.0.0
```

### Verification
```powershell
# Step 1: Install deps
venv\Scripts\pip.exe install -r requirements.txt

# Step 2: Run migration
venv\Scripts\python.exe migrate_phase2_columns.py

# Step 3: Verify imports
venv\Scripts\python.exe -c "from agent.ac_window import find_ac_window; from agent.mrn_reader import read_mrn; from agent.inbox_reader import read_inbox; from agent.clinical_summary_parser import ClinicalSummaryHandler; print('OK')"

# Step 4: Verify model columns
venv\Scripts\python.exe -c "from models.timelog import TimeLog; print(hasattr(TimeLog, 'total_idle_seconds'), hasattr(TimeLog, 'manual_entry'))"
# Expected: True True

# Step 5: Start server and check pages
venv\Scripts\python.exe app.py
# Visit: /timer, /inbox, /admin/config, /admin (Config Settings card), header search bar
```

### Calibration & TODO Inventory (as of CL6)
| Category | Items |
|----------|-------|
| Uncalibrated coordinates | 7 `_XY` tuples + `INBOX_TABLE_REGION` in config.py Section 7 — all `(0,0)` |
| Missing API keys | `PUSHOVER_USER_KEY`, `PUSHOVER_API_TOKEN` — empty strings |
| Config to verify | `NETPRACTICE_URL`, `NETPRACTICE_CLIENT_NUMBER`, `AMAZING_CHARTS_PROCESS_NAME`, `CLINICAL_SUMMARY_EXPORT_FOLDER` |
| Migration needed | `migrate_phase2_columns.py` |
| Code TODOs | copilot-instructions L563 selector, auth.py notification stub, ac_interface_reference 3 calibrate TODOs |
| Unbuilt features | F5e (inbox digest), F11e (auto-archive cron) |
| Placeholder routes | /caregap, /labtrack, /medref, /metrics, /oncall, /orders, /tools |

---

## CL5 — 2026-03-16 — Documentation: AC Integration Update
**Phase:** Documentation Only (no code changes)
**Summary:** Major documentation update integrating Amazing Charts Clinical Summary XML pipeline, Enlarge Textbox window reference, answered outstanding questions, and 4 new features (4f, 6d, 10e, 11e).

### Changes
1. **AC Interface Reference** — Added Enlarge Textbox Window section, canonical AC_NOTE_SECTIONS (16), AC_SPECIAL_SECTIONS
2. **Copilot Instructions** — Updated F5 (filter-cycling), F6 (title-bar), F31 (XML-first), added AC_SHORTCUTS (13), Clinical Summary XML section, AC_NOTE_SECTIONS, folder structure updates, F6d/F10e/Config Editor specs
3. **Dev Guide** — Answered 6 outstanding questions (MRN location, inbox nav, note creation, templates, print/export, patient search). Added F4f, F6d, F10e, F11e. Updated F5 and F6 prompts. Updated master checklist.
4. **AC Patient Info Guide** (NEW) — 8 sections: purpose, data collection, XML structure, DB schema, browser display, AC automation, HIPAA, AI prompts

### Files Created/Modified
| File | Change |
|------|--------|
| `Documents/AC_Patient_Info_Guide.md` | NEW — complete patient data pipeline documentation |
| `Documents/copilot-instructions.md` | AC integration updates (F5, F6, F31, shortcuts, XML, note sections, folder structure) |
| `Documents/NP_Companion_Development_Guide.md` | Answered questions, 4 new features, 2 updated features, build checklist |
| `Documents/ac_interface_reference.md` | Enlarge Textbox Window section |

### Verification
```powershell
Test-Path "Documents\AC_Patient_Info_Guide.md"   # True
Test-Path "Documents\ac_interface_reference.md"   # True
```
Search dev guide for: "Feature 4f", "Feature 6d", "Feature 10e", "Feature 11e" — all present.

---

## CL4 — 2026-03-16 01:20 AM — Admin Hub, Dashboard Nav, Setup Wizard, AC Credentials
**Phase:** Phase 1 (Foundation) + Phase 2 (Data Layer kick-off)
**Summary:** Admin hub consolidation (5 sidebar links → 1 hub), dashboard date navigation, role-based setup wizard, AC + PC credential storage, site map page, Windows strftime fix.

### Changes
1. Fixed Dashboard 500 error (invalid Jinja syntax)
2. Admin Dashboard Hub — 6 cards replacing 5 sidebar links
3. Site Map — `/admin/sitemap` listing all routes by blueprint
4. Dashboard Date Navigation — Yesterday/Today/Tomorrow buttons, `?date=` param
5. Role-Based Setup Wizard — `/setup` with inline forms per incomplete task
6. Setup Button in Header — gold gear icon with count badge, polls /api/setup-status
7. AC Credential Storage — Fernet-encrypted `ac_username_enc`, `ac_password_enc`
8. PC Password Storage — Optional `pc_password_enc`
9. Migration — `migrate_add_ac_columns.py` (4 new user columns)
10. Windows strftime fix — `%-d` → `%d` with Jinja replace pattern

### Files Created
`routes/admin.py`, `templates/admin_dashboard.html`, `templates/admin_sitemap.html`, `templates/setup.html`, `migrate_add_ac_columns.py`

### Files Modified
`models/user.py`, `app.py`, `routes/auth.py`, `routes/dashboard.py`, `templates/dashboard.html`, `templates/base.html`, `templates/settings_account.html`, `static/js/main.js`, `static/css/main.css`

### Verification
```powershell
venv\Scripts\python.exe app.py
# Visit: /dashboard (date nav), /admin (hub), /admin/sitemap, /setup, /settings/account (AC creds)
```

---

## CL3 — 2025-07-14 — NetPractice Admin, Setup Wizard & CGM webPRACTICE Scraper
**Phase:** Phase 2 — Data Layer (F4)
**Summary:** Per-user encrypted NetPractice credentials, schedule model detail columns, admin NP settings page, setup wizard, account settings NP card, complete CGM webPRACTICE scraper rewrite.

### Changes
1. Per-user encrypted NP credentials (Fernet) — `np_username_enc`, `np_password_enc`, `np_provider_name`, `nav_steps`
2. Schedule model — 7 new columns (patient_mrn, phone, reason, units, location, comment, entered_by)
3. Admin NP Settings — `/admin/netpractice` (6 routes), `data/np_settings.json`
4. Setup Wizard — `/admin/netpractice/wizard` with add/remove/reorder steps
5. Account Settings — NP credentials card
6. CGM webPRACTICE Scraper Rewrite — login, nav step replay, regex parsing, detail collection, cookie persistence

### Files Created
`routes/netpractice_admin.py`, `templates/admin_netpractice.html`, `templates/np_setup_wizard.html`, `migrate_add_np_columns.py`, `requirements.txt`

### Files Modified
`models/user.py`, `models/schedule.py`, `scrapers/netpractice.py`, `routes/auth.py`, `templates/settings_account.html`, `templates/base.html`, `app.py`, `config.py`

### Verification
```powershell
venv\Scripts\python.exe migrate_add_np_columns.py
venv\Scripts\python.exe app.py
# Visit: /admin/netpractice, /admin/netpractice/wizard, /settings/account (NP creds)
```

---

## CL2 — 2026-03-15 — Agent Health, Active User Tracking, Crash Recovery
**Phase:** Phase 1 — Foundation (F3, F3a, F3b, F3c)
**Summary:** Agent health indicator (green/yellow/red dot), agent status API, active user tracking via active_user.json, background agent with heartbeat + crash recovery, admin agent dashboard.

### Changes
1. Agent Health Dot — polls /api/agent-status every 15s, green (pulse) / yellow / red (glow) / grey
2. Agent Status API — `/api/agent-status` JSON, `/admin/agent` dashboard, `/admin/agent/restart`
3. Active User Tracking — agent reads `data/active_user.json` each loop
4. Background Agent — Flask context, 30s heartbeat to agent_logs, safe_job() wrapper, MRN/inbox placeholders
5. Crash Recovery — detects orphaned time_logs (24h), closes with estimated end time

### New Tables
`agent_logs`, `agent_errors` (17 total)

### Files Created
`models/agent.py`, `routes/agent_api.py`, `templates/admin_agent.html`, `agent.py`

### Files Modified
`models/__init__.py`, `app.py`, `templates/base.html`, `static/js/main.js`, `static/css/main.css`

### Verification
```powershell
venv\Scripts\python.exe app.py          # Start server
venv\Scripts\python.exe agent.py        # Start agent in 2nd terminal
# Header dot should turn green within 15 seconds
# Visit /admin/agent for full dashboard
```

---

## CL1 — 2026-03-15 — Complete Database Schema
**Phase:** Phase 1 — Foundation (F2)
**Summary:** Created 10 new SQLAlchemy model files. Database now has 15 tables total (up from users + audit_log).

### New Models
| File | Tables |
|------|--------|
| `models/timelog.py` | time_logs |
| `models/inbox.py` | inbox_snapshots, inbox_items |
| `models/oncall.py` | oncall_notes |
| `models/orderset.py` | order_sets, order_items |
| `models/medication.py` | medication_entries |
| `models/labtrack.py` | lab_tracks, lab_results |
| `models/caregap.py` | care_gaps |
| `models/tickler.py` | ticklers |
| `models/message.py` | delayed_messages |
| `models/reformatter.py` | reformat_logs |

### Verification
```powershell
venv\Scripts\python.exe -c "from app import create_app; app = create_app(); from models import db; print(sorted(db.metadata.tables.keys()))"
# Expected: 15 table names
```

---

## Foundation — 2026-03-15 — Phase 1 Complete Build
**Phase:** Phase 1 — Foundation (F1, F1a–F1f)
**Summary:** Built the entire Phase 1 foundation in one day: project skeleton, multi-user auth, role-based access, dark mode, notification preferences, auto-lock with PIN, audit trail, all 15 database tables, background agent with health monitoring and crash recovery, placeholder modules for all sidebar pages.

### Phase 1 Features Built
| Feature | Description | Status |
|---------|-------------|--------|
| F1 | Project Skeleton (app.py, base.html, main.css, main.js) | Built |
| F1a | Multi-User Accounts (User model, login, register, roles) | Built |
| F1b | Role-Based Access (@require_role, sidebar filtering, /admin/users) | Built |
| F1c | Dark Mode / Light Mode (toggle, localStorage + server persist) | Built |
| F1d | Notification Preferences (/settings/notifications) | Built |
| F1e | Session Timeout & Auto-Lock (PIN overlay, /api/verify-pin) | Built |
| F1f | Audit Trail (/admin/audit-log, after_request hook) | Built |
| F2 | Database Schema (15+ tables) | Built |
| F3 | Background Agent (heartbeat, crash recovery) | Built |
| F3a | Agent Health Monitor (status dot + /admin/agent) | Built |
| F3b | Per-Provider Agent Profiles (active_user.json) | Built |
| F3c | Crash Recovery & Resume (orphaned session detection) | Built |

### Phase 2 Partial (also Day 1)
| Feature | Description | Status |
|---------|-------------|--------|
| F4 | NetPractice Schedule Scraper (Playwright/CGM webPRACTICE) | Built |
| F4a | New Patient Flag (gold badge) | Built |
| F4b | Visit Duration Estimator (pace/end time) | Built |
| F4c | Double-Booking & Gap Detector | Built |
| F4e | Re-Auth Watchdog (banner + Pushover) | Built |

### Architectural Decisions
| Decision | Rationale |
|---|---|
| Flask app factory | Allows testing and multiple instances |
| SQLite + SQLAlchemy ORM | Local-only, zero server setup |
| Flask-Bcrypt for passwords AND PINs | Consistent, brute-force resistant |
| JSON column for user preferences | Avoids separate table for small data |
| `data/active_user.json` for agent IPC | Simple file-based, no socket setup needed |
| `after_request` hook for audit log | Zero per-route boilerplate |
| All timestamps UTC | Avoids DST ambiguity |

### Known Gaps (from Day 1)
- agent.py uses while-loop, not APScheduler (added later in CL6 wiring)
- No pystray tray icon yet (added in CL6)
- No agent/scheduler.py yet (created later)
- NP Setup Wizard needs redesign (text-based → visual recorder)
- No manual scrape button on dashboard

---

## Reference: patient_getter_plan.md
**Status:** Plan documented, partial implementation in scraper rewrite (CL3)

The original scraper clicked into each patient's detail page (25 clicks = 1-2 min, fragile). Chrome DevTools revealed most data is already in the schedule page DOM via `td.schSlot` attributes and `jsModApt()` onclick parameters. Plan documents: DOM structure, CSS selectors, jsModApt parameter mapping, visit type color codes, blocked appointment detection. Used to inform the scraper rewrite in CL3.

See `.github/ChangeLog/archive/patient_getter_plan.md` for full details.

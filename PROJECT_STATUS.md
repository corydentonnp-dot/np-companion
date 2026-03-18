# NP Companion — Project Status
# File: PROJECT_STATUS.md
# Updated: 2026-03-18
# Version: 1.1.2

---

## Current Build State

| Property | Value |
|---|---|
| App Version | 1.1.2 |
| Python | 3.11 |
| Framework | Flask 3.1.3 + SQLAlchemy 2.0.48 + SQLite |
| Packager | PyInstaller (single-folder .exe via `build.py`) |
| Platform | Windows 11 Pro (1920×1080, dual monitor) |
| Deployment | USB zip → work PC, auto-start via `.bat` |
| Dev Machine | Local dev with venv, VS Code + GitHub Copilot |
| Work PC Name | FPA-D-NP-DENTON |

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────┐
│  Flask Web Server (port 5000)                           │
│  ├── 16 route blueprints (auth, dashboard, patient, …)  │
│  ├── 39+ SQLAlchemy models (SQLite)                     │
│  ├── Jinja2 templates + vanilla JS frontend             │
│  └── Role-based access: admin / provider / ma           │
├─────────────────────────────────────────────────────────┤
│  Background Agent (agent_service.py, port 5001)         │
│  ├── System tray (pystray)                              │
│  ├── APScheduler (interval + cron jobs)                 │
│  ├── Amazing Charts automation (PyAutoGUI + OCR)        │
│  ├── NetPractice scraping (Playwright + CDP)            │
│  ├── Inbox monitoring + clinical summary parsing        │
│  └── Watchdog file watcher                              │
├─────────────────────────────────────────────────────────┤
│  External Integrations                                  │
│  ├── NIH RxNorm API (drug data, cached in RxNormCache)  │
│  ├── NIH ICD-10 API (diagnosis codes, Icd10Cache)       │
│  ├── Pushover API (mobile push notifications)           │
│  └── Tailscale (remote phone access)                    │
└─────────────────────────────────────────────────────────┘
```

---

## Registered Blueprints (16)

| Blueprint | Module | Purpose |
|---|---|---|
| auth_bp | routes/auth.py | Login, logout, session, user CRUD |
| admin_bp | routes/admin.py | Admin panel, user management |
| agent_api_bp | routes/agent_api.py | Agent ↔ server communication |
| dashboard_bp | routes/dashboard.py | Home dashboard, My Patients, schedule |
| timer_bp | routes/timer.py | Time tracking per encounter |
| inbox_bp | routes/inbox.py | Inbox snapshots, message viewer |
| oncall_bp | routes/oncall.py | On-call notes, handoff links |
| orders_bp | routes/orders.py | Order sets, master orders |
| medref_bp | routes/medref.py | Medical reference links |
| labtrack_bp | routes/labtrack.py | Lab result tracking |
| caregap_bp | routes/caregap.py | Care gap rules, USPSTF screening |
| metrics_bp | routes/metrics.py | Analytics, usage metrics |
| tools_bp | routes/tools.py | Utility tools (reformatter, etc.) |
| np_admin_bp | routes/netpractice_admin.py | NetPractice administration |
| patient_bp | routes/patient.py | Patient chart, demographics, meds |
| ai_api_bp | routes/ai_api.py | AI assistant integration |

---

## Database Models (39+)

### Core
- `User` — login credentials, role (`admin`/`provider`/`ma`), preferences

### Patient Data
- `PatientRecord` — demographics (MRN, name, DOB, sex)
- `PatientMedication` — medications with `rxnorm_cui` column
- `PatientDiagnosis` — diagnoses with ICD-10 codes
- `PatientAllergy`, `PatientImmunization`, `PatientVitals`
- `PatientSpecialist`, `PatientNoteDraft`

### Caching
- `Icd10Cache` — cached ICD-10 lookups (keyed by code, permanent)
- `RxNormCache` — cached RxNorm drug data (keyed by rxcui, permanent)

### Clinical Workflow
- `Schedule` — daily appointment schedule
- `CareGap`, `CareGapRule` — USPSTF screening rules + patient gaps
- `LabTrack`, `LabResult`, `LabPanel` — lab result tracking
- `OrderSet`, `OrderItem`, `MasterOrder` — clinical order sets
- `OrderSetVersion`, `OrderExecution`, `OrderExecutionItem`
- `MedicationEntry` — medication reference
- `Tickler` — follow-up reminders

### Communication
- `InboxSnapshot`, `InboxItem` — inbox message snapshots
- `OnCallNote`, `HandoffLink` — on-call handoff data
- `Notification` — push notifications (Pushover)
- `DelayedMessage` — scheduled messages

### Operations
- `AuditLog` — request audit trail (auto-logged)
- `TimeLog` — encounter time tracking
- `AgentLog`, `AgentError` — background agent logs
- `ReformatLog` — text reformatting history

---

## Migration Files (17)

All migrations are idempotent (`ALTER TABLE … ADD COLUMN` with `try/except` or column-existence checks). Safe to re-run.

| Migration | Purpose |
|---|---|
| migrate_phase2_columns.py | Phase 2 widget schema |
| migrate_phase4_columns.py | Phase 4 feature columns |
| migrate_cl21.py | CareLink 2.1 schema |
| migrate_add_ac_columns.py | Amazing Charts integration |
| migrate_add_ai_columns.py | AI feature columns |
| migrate_add_caregap_columns.py | Care gap tracking |
| migrate_add_chart_columns.py | Chart feature columns |
| migrate_add_claim_columns.py | Patient claim data |
| migrate_add_forward_columns.py | Message forwarding |
| migrate_add_icd10_cache.py | ICD-10 cache table |
| migrate_add_labtrack_columns.py | Lab tracking columns |
| migrate_add_master_order_cpt.py | CPT codes on orders |
| migrate_add_np_columns.py | NetPractice columns |
| migrate_add_orderset_columns.py | Order set columns |
| migrate_add_patient_sex.py | Patient sex demographic |
| migrate_add_rxnorm_cache.py | RxNorm cache table |
| migrate_add_timer_columns.py | Timer feature columns |

---

## What's Done (CL23 Beta Readiness)

### Phase 0 — Critical Bugs ✅
- [x] 0.1 Admin send-notification endpoint fixed (JSON body, field alignment)
- [x] 0.2 Patient "unknown" name on claim fixed
- [x] 0.3 RxNorm API integration — `RxNormCache` model, `rxnorm_cui` on `PatientMedication`, `utils/api_client.py`, enrichment pipeline

### Phase 1 — Data Correctness ✅
- [x] 1.1 Full MRN displayed everywhere
- [x] 1.2 DOB format MM/DD/YYYY
- [x] 1.3 Sex/gender in chart header
- [x] 1.4 Demographics edit UI
- [x] 1.5 ICD-10 auto-lookup on chart load
- [x] 1.6 Care gap sex filter

### Phase 2 — Widget System ✅
- [x] 2.1 True freeform default (no snap)
- [x] 2.2 Per-widget settings button
- [x] 2.3 Scrollable widget content
- [x] 2.4 Layout persists per-user

### Phase 3 — Context Menu & Clipboard ✅
- [x] 3.1 Enhanced right-click on links
- [x] 3.2 Right-click on selected text
- [x] 3.3 Text selection on admin pages

### Phase 4 — Feature Completions ✅
- [x] 4.1 USPSTF enhancements (billing codes, due/overdue filter)
- [x] 4.2 Order set redesign (popup flow, master order browser)
- [x] 4.3 Notification admin rebuild
- [x] 4.4 Care gaps spreadsheet for claimed patients
- [x] 4.5 Diagnoses copy with column picker
- [x] 4.6 Admin deactivation scheduling
- [x] 4.7 Collect user email

### Phase 5 — UI Polish ✅
- [x] 5.1 Version → user popover only
- [x] 5.2 Center dashboard appointment banner
- [x] 5.3 Remove redundant "Open" button
- [x] 5.4 Refresh button next to notification bell
- [x] 5.5 AI panel minimize/snap-back
- [x] 5.6 My Patients live search filter
- [x] 5.7 Provider name format verified

### Code Cleanup ✅
- [x] models/__init__.py — all models exported (Notification, Icd10Cache, RxNormCache added)
- [x] npcompanion.spec — routes.ai_api added to hiddenimports
- [x] requirements.txt — psutil added
- [x] .gitignore — dist/, build/, *.ico, *.code-workspace added
- [x] 9 unused imports cleaned across 6 route files
- [x] 0 compile errors across all Python files

---

## What's Next — Immediate Priorities

### 1. First Patient Deployment
- Build with `python build.py --bump patch --notes "CL23 beta" --usb E:`
- Transfer zip to work PC via USB or Google Drive
- Unzip, run `Start_NP_Companion.bat`
- Verify: login, dashboard, schedule pull, patient chart, MRN reader, timer
- Set `AC_MOCK_MODE = False` and `DEBUG = False` in config.py on work PC
- Update `TESSERACT_PATH` to match work PC Tesseract install location

### 2. Post-Deployment Validation
- Test MRN reading with live Amazing Charts
- Test clinical summary parsing from AC inbox
- Verify Pushover notifications reach phone
- Verify Tailscale remote access from phone
- Run through `Documents/VERIFICATION_CHECKLIST.md`

### 3. Known Issues / Warnings
- `AC_MOCK_MODE = True` in dev config — must flip to `False` for production
- `DEBUG = True` in dev config — must flip to `False` for production
- `SECRET_KEY` is hardcoded in config.py — acceptable for single-user local deploy
- Clinical summary parser depends on AC XML export format — if AC updates, parser may need adjustment
- Tesseract path is machine-specific — must be updated per machine
- Chrome CDP port 9222 required for NetPractice Playwright scraping

### 4. Prepare Modules, Phases, and Features integrating API as outlined in API_Integration_Plan.md
- we want to demonstarte the functinoaly and usefulness of this program to office admin and IT staff. integrating API is the biggest "wow" factor that turn this project from a data displayer to a pseudo clinical decision support engine.
-all features that interact with API are prioritized ove those which do not involve API
-read the API development plan and begin development of those features integrating API. 
- once you have finished to the best of your ability, prompt the user to provide further required information, API keys, log-in information (virginia vaccine information system)(prescription drug monitoring program)
-the goal is to have these ready to present by EOD 03/19/2026 or 03/20/26 at the latest. 
-You may partially build these fetures to prove function and design for the moment, understanding you will be asked to "finish any uncompleted tasks" at some point in the near future. 
-document what was and was not completed, store it for your own use later on and in the change log for human review. 
-reference  "Ongoing Development — Phase Roadmap" and any other files for further information about upcoming development involving API. 
---

## Ongoing Development — Phase Roadmap

### Next: Phase 6+ Features (from Development Guide)
- **API Intelligence (Phase 10A/10B)** — 17+ external APIs: OpenFDA, LOINC, UMLS, NLM DailyMed, Medicare fee schedules, drug interactions, lab reference ranges. Foundation exists in `utils/api_client.py`.
- **Billing Intelligence** — CPT/ICD-10 auto-suggestion, modifier logic, claim scrubbing
- **AI Assistant Expansion** — clinical decision support, documentation assistance
- **Enhanced Scheduling** — WebPractice bidirectional sync, patient reminders
- **Reporting** — provider productivity, care gap compliance, panel management

### Multi-Year Horizon
- Migration from Amazing Charts if EHR changes
- Multi-provider support (currently single-provider optimized)
- FHIR/HL7 integration if AC or replacement EHR supports it
- Potential cloud component for cross-device sync (currently local-only by design for HIPAA)

---

## Dependencies (41 packages)

### Core Framework
| Package | Version |
|---|---|
| Flask | 3.1.3 |
| Flask-SQLAlchemy | 3.1.1 |
| Flask-Login | 0.6.3 |
| Flask-Bcrypt | 1.0.1 |
| SQLAlchemy | 2.0.48 |
| Werkzeug | 3.1.6 |
| Jinja2 | 3.1.6 |

### Desktop Automation
| Package | Version |
|---|---|
| PyAutoGUI | 0.9.54 |
| pytesseract | 0.3.13 |
| Pillow | 12.1.1 |
| pywin32 | 311 |
| psutil | 7.0.0 |
| pyperclip | 1.11.0 |

### Browser Automation
| Package | Version |
|---|---|
| Playwright | 1.58.0 |

### Background Services
| Package | Version |
|---|---|
| APScheduler | 3.11.0 |
| pystray | 0.19.5 |
| watchdog | 6.0.0 |

### Notifications & UI
| Package | Version |
|---|---|
| plyer | 2.1.0 |
| pywebview | 5.3.2 |

### Security
| Package | Version |
|---|---|
| bcrypt | 5.0.0 |
| cryptography | 46.0.5 |

---

## File Reference

| Document | Path | Purpose |
|---|---|---|
| Master Instructions | `init.prompt.md` | Coding rules, conventions, HIPAA, architecture |
| Development Guide | `Documents/NP_Companion_Development_Guide.md` | Phase-by-phase feature specs (94 features) |
| API Plan | `Documents/np_companion_api_intelligence_plan.md` | All 17+ APIs, caching, billing rules |
| AC Reference (condensed) | `Documents/ac_interface_reference_v2.md` | AC UI ground truth — read first |
| AC Reference (full) | `Documents/ac_interface_reference/…/ac_interface_reference_v4.md` | Detailed AC ground truth (2788 lines) |
| Deployment Guide | `Documents/Deployment_Guide.md` | Build, transfer, install workflow |
| Verification Checklist | `Documents/VERIFICATION_CHECKLIST.md` | End-to-end testing steps |
| This File | `PROJECT_STATUS.md` | Current build state, what's done, what's next |
| README | `README.md` | Project overview for IT review / GitHub landing page |
| Security Overview | `SECURITY.md` | HIPAA compliance, data handling, access controls |
| Env Template | `.env.example` | Environment variable structure (no real values) |

---

## VS Code Pre-Flight Findings (2026-03-18)

- **Problems panel**: 0 errors in actual project files (108 stale Copilot chat code-block artifacts — not real code)
- **Dependency conflicts (pip check)**: None known
- **Python compile errors**: 0 across all .py files
- **.git repository**: Not yet initialized — `git init` required before first push
- **config.py**: Contains hardcoded credentials — correctly excluded from Git via `.gitignore`

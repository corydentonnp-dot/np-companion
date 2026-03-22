# CareCompanion Ã¢â‚¬â€ Pre-Beta Deployment Checklist

> **File-by-file verification checklist for the _active_final_plan.md implementation.**
> Generated after completing all 7 phases. Every file touched, created, or modified is listed below with its verification status.

---

## Files Created

| # | File | Phase | Purpose | Verified |
|---|------|-------|---------|----------|
| 1 | `app/services/api/uptodate.py` | 0 | UpToDate clinical decision support service | [ ] |
| 2 | `templates/caregap_print_handout.html` | 1 | Clean printable care gap patient handout | [ ] |
| 3 | `tests/test_caregap_ui.py` | 1 | 10 tests for care gap UI enhancements | [ ] |
| 4 | `tests/test_misc_audit_fixes.py` | 2 | 5 tests for provider name + F10 audit | [ ] |
| 5 | `tests/test_e2e_billing_pipeline.py` | 3 | 25 E2E billing engine tests | [ ] |
| 6 | `tests/test_e2e_calculator_pipeline.py` | 3 | 15 E2E calculator pipeline tests | [ ] |
| 7 | `tests/test_morning_briefing_integration.py` | 3 | 15 morning briefing integration tests | [ ] |
| 8 | `tests/test_billing_multi_patient.py` | 3 | 15 multi-patient billing tests | [ ] |
| 9 | `tools/deploy_check.py` | 4 | 11-section automated pre-flight checker | [ ] |
| 10 | `tests/test_deploy_check.py` | 4 | 10 tests for deploy_check.py | [ ] |
| 11 | `tools/usb_smoke_test.py` | 5 | USB deployment smoke test (8 checks) | [ ] |
| 12 | `tools/backup_restore_test.py` | 5 | DB backup/restore validator | [ ] |
| 13 | `tools/connectivity_test.py` | 5 | Network & Tailscale connectivity tester | [ ] |
| 14 | `tests/test_infrastructure.py` | 5 | 10 infrastructure smoke tests | [ ] |
| 15 | `tools/verify_all.py` | 6 | Interactive 5-stage verification orchestrator | [ ] |
| 16 | `tests/test_verify_all.py` | 6 | 10 verify_all tests | [ ] |

## Files Modified

| # | File | Phase | Change | Verified |
|---|------|-------|--------|----------|
| 17 | `app/api_config.py` | 0 | Added UpToDate config constants | [ ] |
| 18 | `config.example.py` | 0 | Added UPTODATE_API_KEY entry | [ ] |
| 19 | `app/services/monitoring_rule_engine.py` | 0 | Wired UpToDate into waterfall step 5 | [ ] |
| 20 | `routes/caregap.py` | 1 | Added `/caregap/<mrn>/print` route + trigger_type | [ ] |
| 21 | `templates/caregap_patient.html` | 1 | Print button, Personalized/All toggle, data-trigger-type | [ ] |
| 22 | `templates/netpractice_setup.html` | 2 | Improved provider name placeholder text | [ ] |
| 23 | `templates/np_wizard.html` | 2 | Improved provider name placeholder text | [ ] |
| 24 | `templates/settings_account.html` | 2 | Improved provider name placeholder text | [ ] |
| 25 | `templates/layout.html` | 2 | Version label in user popover | [ ] |
| 26 | `tests/test_phase15_data_pipeline.py` | 3 | +5 E2E chain tests (20Ã¢â€ â€™25) | [ ] |
| 27 | `agent/scheduler.py` | 7 | Added `**kwargs` to `build_scheduler` (bug fix) | [ ] |
| 28 | `routes/dashboard.py` | 7 | Removed redundant `from datetime import timedelta` (bug fix) | [ ] |
| 29 | `Documents/dev_guide/DEPLOYMENT_GUIDE.md` | 5 | Added "Pre-Beta USB Deployment Smoke Test" section | [ ] |
| 30 | `Documents/dev_guide/CARECOMPANION_DEVELOPMENT_GUIDE.md` | 7 | Updated test count, added final_plan note | [ ] |
| 31 | `Documents/dev_guide/PROJECT_STATUS.md` | 7 | Added final_plan.md summary, updated What's Next | [ ] |
| 32 | `Documents/dev_guide/RUNNING_PLAN.md` | 7 | Added final_plan.md completion summary | [ ] |
| 33 | `Documents/dev_guide/_ACTIVE_FINAL_PLAN.md` | 0Ã¢â‚¬â€œ7 | All phase checkboxes marked complete | [ ] |
| 34 | `routes/daily_summary.py` | P7 | New blueprint Ã¢â‚¬â€ daily provider summary, MA rooming sheet, REMS/disease references | [ ] |
| 35 | `templates/daily_summary_print.html` | P7 | Provider daily summary print template | [ ] |
| 36 | `templates/rooming_sheet_print.html` | P7 | MA/rooming staff sheet print template | [ ] |
| 37 | `templates/rems_reference.html` | P7 | Searchable REMS medication reference viewer | [ ] |
| 38 | `templates/reportable_diseases_reference.html` | P7 | Searchable reportable disease reference viewer | [ ] |
| 39 | `data/rems_database.json` | P7 | 22 REMS programs Ã¢â‚¬â€ FDA REMS medication database | [ ] |
| 40 | `data/reportable_diseases.json` | P7 | 31 reportable conditions Ã¢â‚¬â€ infectious disease guide | [ ] |
| 41 | `tests/test_daily_summary.py` | P7 | 26 tests for all Part 7 features | [ ] |
| 42 | `app/__init__.py` | P7 | Added daily_summary_bp to blueprint_map | [ ] |
| 43 | `Documents/dev_guide/RUNNING_PLAN.md` | P7 | Added Part 7 Ã¢â‚¬â€ Phases 39Ã¢â‚¬â€œ42 documentation | [ ] |
| 44 | `routes/help.py` | P7 | Help/Feature Guide blueprint Ã¢â‚¬â€ 3 routes | [ ] |
| 45 | `templates/help_guide.html` | P7 | Feature guide template (extends base.html) | [ ] |
| 46 | `data/help_guide.json` | P7 | 40+ features documented across 7 categories | [ ] |
| 47 | `tests/test_help.py` | P7 | 25 tests for help system | [ ] |
| 48 | `app/__init__.py` | P7 | Added help_bp to blueprint_map | [ ] |
| 49 | `templates/base.html` | P7 | Added Feature Guide to Help menu + command palette | [ ] |

---

## Test Suite Summary

| Suite | Count | Runner | Status |
|-------|-------|--------|--------|
| `python test.py` | 127 | Custom | Ã¢Å“â€¦ 127/127 pass, 0 errors |
| `pytest tests/` | 93 | pytest | Ã¢Å“â€¦ 93/93 pass (51 added in Part 7) |
| `test_caregap_ui.py` | 10 | Custom | Ã¢Å“â€¦ 10/10 pass |
| `test_misc_audit_fixes.py` | 5 | Custom | Ã¢Å“â€¦ 5/5 pass |
| `test_e2e_billing_pipeline.py` | 25 | Custom | Ã¢Å“â€¦ 25/25 pass |
| `test_e2e_calculator_pipeline.py` | 15 | Custom | Ã¢Å“â€¦ 15/15 pass |
| `test_morning_briefing_integration.py` | 15 | Custom | Ã¢Å“â€¦ 15/15 pass |
| `test_billing_multi_patient.py` | 15 | Custom | Ã¢Å“â€¦ 15/15 pass |
| `test_phase15_data_pipeline.py` | 25 | Custom | Ã¢Å“â€¦ 25/25 pass |
| `test_deploy_check.py` | 10 | Custom | Ã¢Å“â€¦ 10/10 pass |
| `test_infrastructure.py` | 10 | Custom | Ã¢Å“â€¦ 10/10 pass |
| `test_verify_all.py` | 10 | Custom | Ã¢Å“â€¦ 10/10 pass |
| **Total** | **360** | | **Ã¢Å“â€¦ All pass** |

---

## Bug Fixes (Pre-Existing)

| # | File | Bug | Fix |
|---|------|-----|-----|
| 1 | `routes/dashboard.py` | `from datetime import timedelta` inside TCM try-block caused Python to treat `timedelta` as local for entire function, making lines 289-290 fail with "cannot access local variable" | Removed redundant local import (already imported at module level, line 17) |
| 2 | `agent/scheduler.py` | `kwargs.get('tcm_deadline_fn')` at line 279 referenced undefined `kwargs` Ã¢â‚¬â€ function signature used explicit keyword args but no `**kwargs` | Added `**kwargs` to `build_scheduler()` signature |

---

## Deployment Tools Created

| Tool | Purpose | Run Command |
|------|---------|-------------|
| `tools/deploy_check.py` | 11-section automated pre-flight checker | `python tools/deploy_check.py` |
| `tools/usb_smoke_test.py` | USB deployment health check (8 checks) | `python tools/usb_smoke_test.py` |
| `tools/backup_restore_test.py` | DB backup verify + restore dry-run | `python tools/backup_restore_test.py` |
| `tools/connectivity_test.py` | LAN, Tailscale, AC share connectivity | `python tools/connectivity_test.py` |
| `tools/verify_all.py` | Interactive 5-stage verification session | `python tools/verify_all.py` |

---

## Pre-Production Checklist

Before first real-patient session:

- [ ] Run `python tools/deploy_check.py` Ã¢â‚¬â€ all checks pass
- [ ] Run `python test.py` Ã¢â‚¬â€ 127/127 pass
- [ ] Run `python tools/usb_smoke_test.py` Ã¢â‚¬â€ 8/8 pass
- [ ] Run `python tools/backup_restore_test.py` Ã¢â‚¬â€ backup healthy, restore viable
- [ ] Run `python tools/connectivity_test.py` Ã¢â‚¬â€ LAN reachable
- [ ] Run `python tools/verify_all.py` Ã¢â‚¬â€ complete all 5 stages
- [ ] Verify `config.py`: `DEBUG = False`
- [ ] Verify `config.py`: `AC_MOCK_MODE = False`
- [ ] Verify `config.py`: `SECRET_KEY` is not a dev default
- [ ] VERIFICATION_REPORT decision = **GO FOR BETA**
- [ ] Provider signature on report

---

## Production Environment Setup

> Merged from PRODUCTION_CHECKLIST.md Ã¢â‚¬â€ complete every item before the app handles real patient data.

### Environment & Security

- [ ] **DEBUG = False** in `config.py`
- [ ] **AC_MOCK_MODE = False** in `config.py`
- [ ] **SECRET_KEY** replaced with a cryptographically random key (Ã¢â€°Â¥32 chars); never reuse the dev default
- [ ] Sensitive values moved to **environment variables** (SECRET_KEY, SMTP_PASS, API keys, Pushover keys, AC credentials)
- [ ] `config.py` is listed in `.gitignore` and excluded from any shared/backup folder
- [ ] BitLocker (or equivalent full-disk encryption) enabled on the deployment machine
- [ ] Windows Firewall Ã¢â‚¬â€ allow inbound TCP 5000 only from trusted IPs, block all else
- [ ] Automatic Windows Update enabled

### Machine & Display

- [ ] **Screen resolution** matches `SCREEN_RESOLUTION` in config (default 1920Ãƒâ€”1080)
- [ ] Tesseract OCR installed and `TESSERACT_PATH` resolves correctly (`tesseract --version` succeeds)
- [ ] Display scaling set to 100 % (125 %+ breaks OCR coordinates)
- [ ] Amazing Charts EHR installed and opens normally
- [ ] `AC_EXE_PATH`, `AC_DB_PATH`, `AC_IMPORTED_ITEMS_PATH` are reachable from the deployment PC
- [ ] Chrome installed with `--remote-debugging-port=9222` launch shortcut (for NetPractice scraper)

### Database & Migrations

- [ ] SQLite database created at `data/carecompanion.db` (first run auto-creates)
- [ ] All `migrate_*.py` scripts have been applied (auto-run on startup via `_applied_migrations` table)
- [ ] Run `python -c "import sqlite3; c=sqlite3.connect('data/carecompanion.db'); print(c.execute('PRAGMA integrity_check').fetchone())"` Ã¢â€ â€™ should print `('ok',)`
- [ ] `data/backups/` directory exists and nightly backup job is registered

### User Accounts

- [ ] Admin account created via `/setup/onboarding` wizard
- [ ] Provider account(s) created and can log in
- [ ] Role assignments verified: admin can see all modules, provider sees permitted modules, MA sees restricted set
- [ ] Password strength acceptable (bcrypt hashed)

### Notifications

- [ ] **Pushover** Ã¢â‚¬â€ `PUSHOVER_USER_KEY` and `PUSHOVER_API_TOKEN` set and tested (send a test push from Admin > Agent)
- [ ] **SMTP** Ã¢â‚¬â€ `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` configured; send a test email
- [ ] Quiet hours configured (`NOTIFY_QUIET_HOURS_START` / `END`)
- [ ] End-of-day notification time suitable for the practice schedule

### API Keys

- [ ] **OpenFDA** Ã¢â‚¬â€ `OPENFDA_API_KEY` set (increases rate limit from 40/min Ã¢â€ â€™ 240/min)
- [ ] **UMLS** Ã¢â‚¬â€ `UMLS_API_KEY` set and approved (provides SNOMED CT, VSAC, RxNorm)
- [ ] **LOINC** Ã¢â‚¬â€ `LOINC_USERNAME` / `LOINC_PASSWORD` set (lab reference ranges)
- [ ] **PubMed** Ã¢â‚¬â€ `PUBMED_API_KEY` set (optional; increases rate limit)
- [ ] Drug Safety, Lab Interpretation, Guidelines, Formulary Gaps, Patient Education endpoints return 200 (run `python test.py` Section 7)

### NetPractice / Amazing Charts

- [ ] `NETPRACTICE_URL` and `NETPRACTICE_CLIENT_NUMBER` configured
- [ ] Chrome CDP session alive Ã¢â‚¬â€ `/api/auth-status` shows green
- [ ] Schedule scraper pulls tomorrow's appointments successfully
- [ ] AC login credentials (`AC_LOGIN_USERNAME` / `AC_LOGIN_PASSWORD`) correct
- [ ] AC_MOCK_MODE confirmed **False** Ã¢â‚¬â€ agent reads live screen, not mock images

### Agent Service

- [ ] Agent starts via `Start_CareCompanion.bat` or `python agent_service.py`
- [ ] `/api/agent-status` returns `{"status": "green"}` within 60 seconds
- [ ] All 16 scheduled jobs registered (heartbeat, mrn_reader, inbox_check, inbox_digest, callback_check, overdue_lab_check, xml_archive_cleanup, xml_poll, weekly_summary, monthly_billing, deactivation_check, delayed_message_sender, eod_check, drug_recall_scan, previsit_billing, daily_backup)
- [ ] Agent tray icon appears in system tray
- [ ] Admin > Agent dashboard shows uptime and recent heartbeats

### Health & Logging

- [ ] `/api/health` returns `{"status": "ok", "db": "connected"}` (200)
- [ ] `data/logs/carecompanion.log` exists and contains JSON entries
- [ ] Log rotation set to daily with 7-day retention
- [ ] Error log captures 500 errors with traceback

### Test Gate

- [ ] **`python test.py`** Ã¢â‚¬â€ all checks PASS (0 failures, 0 errors)
- [ ] Manual verification: Dashboard loads, Timer works, Inbox shows, On-Call creates notes, Orders loads, Med Ref search works, Lab Track shows, Care Gaps loads, Metrics charts render, EOD checker runs, Settings save, Admin pages accessible, Patient chart loads, Messages send, Notifications load, Commute briefing renders, Macros load, Billing opportunities appear, Health check responds

---

## Manual Verification Walkthrough

> Merged from VERIFICATION_CHECKLIST.md Ã¢â‚¬â€ step-by-step guide for non-programmer verification.

### Confirmed Work PC Environment

| Property | Confirmed Value |
|---|---|
| Operating System | Windows 11 Pro |
| PC Hardware | HP EliteDesk 705 G5, AMD Ryzen 5 PRO 3400G, 16GB RAM |
| AC Version | 12.3.1 (build 297) |
| AC Window Title | `Amazing Charts EHR (32 bit)` |
| AC Installation | `C:\Program Files (x86)\Amazing Charts\AmazingCharts.exe` |
| AC Practice ID | 2799 (Family Practice Associates of Chesterfield) |
| AC Database | `\\192.168.2.51\Amazing Charts\AmazingCharts.mdf` |
| Imported Items | `\\192.168.2.51\amazing charts\ImportItems\[MRN]\` |

### Step 1 Ã¢â‚¬â€ Run Main Test Suite

```
venv\Scripts\activate
venv\Scripts\python.exe test.py
```
Expected: `Results: 36 passed, 0 failed, 0 errors out of 36 checks`

### Step 2 Ã¢â‚¬â€ Run Agent Mock Tests

```
venv\Scripts\python.exe tests/test_agent_mock.py
```
Expected: `Passed: 36, Failed: 0`

### Step 3 Ã¢â‚¬â€ Start Server & Check All Pages

Start: `venv\Scripts\python.exe app.py`
Login at `http://localhost:5000` Ã¢â€ â€™ Dashboard

| # | Page | URL | Expected |
|---|------|-----|----------|
| 1 | Dashboard | `/` | Today's schedule |
| 2 | Timer | `/timer` | Timer dashboard with E&M bar |
| 3 | Inbox | `/inbox` | Inbox with filter tabs + Digest |
| 4 | On-Call | `/oncall` | Notes list + New Note button |
| 5 | Orders | `/orders` | Order sets page |
| 6 | Med Ref | `/medref` | Medication reference |
| 7 | Lab Track | `/labtrack` | Lab tracking with stats cards |
| 8 | Care Gaps | `/caregap` | Preventive care gaps overview |
| 9 | Metrics | `/metrics` | 7 Chart.js charts |
| 10 | Patient Chart | `/patient/99999` | Loads without errors (empty OK) |

### Step 4 Ã¢â‚¬â€ Check Admin Pages

| # | Page | URL |
|---|------|-----|
| 1 | Admin Hub | `/admin` |
| 2 | Users | `/admin/users` |
| 3 | Audit Log | `/admin/audit-log` |
| 4 | Agent | `/admin/agent` |
| 5 | NetPractice | `/admin/netpractice` |
| 6 | Sitemap | `/admin/sitemap` |
| 7 | Care Gap Rules | `/admin/caregap-rules` |

### Step 5 Ã¢â‚¬â€ Check Settings & Restart

- `/settings/account` Ã¢â‚¬â€ account settings load
- `/settings/notifications` Ã¢â‚¬â€ notification preferences load
- Double-click `restart.bat` Ã¢â‚¬â€ kills old server, runs tests, starts fresh, opens Chrome

### Step 6 Ã¢â‚¬â€ Feature-Specific Checks (F11Ã¢â‚¬â€œF15, CL16Ã¢â‚¬â€œCL23)

| # | Feature | URL | Key Check |
|---|---------|-----|-----------|
| 1 | Lab Tracker | `/labtrack` | Stats cards, add-tracking form |
| 2 | Timer | `/timer` | Daily summary, E&M bar, Quick Calc widget |
| 3 | Metrics | `/metrics` | 7 charts, date range picker, Export PDF |
| 4 | Billing Log | `/billing/log` | Filter controls, expandable detail rows |
| 5 | E&M Calculator | `/billing/em-calculator` | MDM + Time-based, higher-of-two result |
| 6 | Monthly Report | `/billing/monthly-report` | Summary cards, E&M chart, prior month comparison |
| 7 | Care Gap Panel | `/caregap/panel` | Coverage table, outreach list, CSV export |
| 8 | Admin Rules Editor | `/admin/caregap-rules` | 19 USPSTF rules, edit forms |
| 9 | Clinical Summary Import | Dashboard drop zone | Drag XML from `Documents/xml_test_patients/` Ã¢â€ â€™ imports Ã¢â€ â€™ panel appears |
| 10 | Patient Chart Widgets | `/patient/62815` | Medications, diagnoses, allergies, immunizations, vitals |

### Step 7 Ã¢â‚¬â€ Verify AC Interface v4 Integration

| # | Check | Command |
|---|-------|---------|
| 1 | AC Version | `python -c "import config; print(config.AC_VERSION)"` Ã¢â€ â€™ `12.3.1` |
| 2 | AC State Detection | `python -c "from agent.ac_window import get_ac_state; print('OK')"` |
| 3 | ORDER_TABS | `python -c "from models.orderset import ORDER_TABS; print(len(ORDER_TABS))"` Ã¢â€ â€™ `8` |
| 4 | Inbox Filters | `python -c "from agent.inbox_reader import INBOX_FILTERS; print(len(INBOX_FILTERS))"` Ã¢â€ â€™ `7` |

### Step 8 Ã¢â‚¬â€ Verify API Integration Foundation

Prerequisites: `python migrate_add_api_cache_tables.py`

| # | Check | Command |
|---|-------|---------|
| 1 | API Client | `python -c "from utils.api_client import get_cached_or_fetch; print('OK')"` |
| 2 | RxNormCache | `python -c "from models.patient import RxNormCache; print('OK')"` |
| 3 | RxNorm API | `python -c "import requests; r = requests.get('https://rxnav.nlm.nih.gov/REST/rxcui/203644/properties.json'); print(r.json()['properties']['name'])"` Ã¢â€ â€™ `lisinopril` |

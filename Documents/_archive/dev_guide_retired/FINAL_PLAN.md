# final_plan.md — CareCompanion Pre-Beta Deployment Plan

> **Generated:** 2026-03-22 | **Version:** 1.1.2 → 1.2.0 (Deploy Target)
> **Purpose:** Step-by-step guide with phases, sub-phases, checkpoints, and testing gates. Specifies exactly what Copilot will code and what information the user (Cory) must provide for deployment.

---

## PLAN OVERVIEW

| Phase | Name | Items | Who | Estimated Scope |
|-------|------|-------|-----|-----------------|
| **0** | Critical Bug Fixes | 8 | Copilot | Runtime-breaking bugs |
| **1** | Security Hardening | 6 | Copilot | Vulnerability remediation |
| **2** | Billing Accuracy | 5 | Copilot | CMS compliance corrections |
| **3** | Code Quality & Cleanup | 12 | Copilot | Polish and dedup |
| **4** | User Configuration | 13 | **Cory** | API keys, credentials, paths |
| **5** | Work-PC Integration | 6 | Cory + Copilot | Physical environment calibration |
| **6** | Build, Test & Deploy | 5 | Copilot + Cory | Final build and transfer |

**Gate Rule:** Each phase must pass its checkpoint before advancing.

---

## PHASE 0: CRITICAL BUG FIXES

> **Goal:** Fix all bugs that will cause crashes or incorrect behavior at runtime.
> **Actor:** Copilot (100% automated)

### 0.1 — Fix PracticeBookmark import

| Key | Value |
|-----|-------|
| **File** | `models/__init__.py` |
| **Bug** | `PracticeBookmark` class from `models/bookmark.py` is not imported → `db.create_all()` silently skips `practice_bookmark` table |
| **Fix** | Add `from models.bookmark import PracticeBookmark` to the import block |
| **Test** | `from models import PracticeBookmark; assert PracticeBookmark.__tablename__ == 'practice_bookmark'` |

### 0.2 — Fix verify_all.py Stage 1 crash

| Key | Value |
|-----|-------|
| **File** | `tools/verify_all.py`, around line 125 |
| **Bug** | `run_stage1()` calls `checker.run()` — method doesn't exist (should be `run_all_checks()`). Also unpacks `checker.results` as 3-tuples — but `results` is a `dict`, not a list |
| **Fix** | (a) Change `checker.run()` → `checker.run_all_checks()`. (b) Change `for name, ok, detail in checker.results:` → `for name, info in checker.results.items():` with appropriate unpacking based on `info` structure. Confirm by reading `deploy_check.py`'s `DeployChecker` class to verify method and data shape. |
| **Test** | Run `python -c "from tools.verify_all import run_stage1; print('import OK')"` — should not crash |

### 0.3 — Consolidate duplicate `months_since()`

| Key | Value |
|-----|-------|
| **Files** | `billing_engine/shared.py` (L121) and `billing_engine/utils.py` (L60) |
| **Bug** | Both define `months_since()`. For `None` input: `shared.py` returns `0` (= "just happened"), `utils.py` returns `9999` (= "never happened"). If a detector imports the wrong one, eligibility logic inverts. |
| **Fix** | Keep ONE canonical `months_since()` in `utils.py` (returns `9999` for None, because None = "never done" = overdue). Delete the copy in `shared.py`. Update all `from billing_engine.shared import months_since` → `from billing_engine.utils import months_since`. |
| **Coding Logic** | (1) Search all files for `from billing_engine.shared import` and `from billing_engine.utils import` containing `months_since`. (2) Verify all call sites pass date/None and expect "big number for None". (3) Remove from shared.py, update imports. |
| **Test** | `from billing_engine.utils import months_since; assert months_since(None) == 9999` |

### 0.4 — Remove duplicate server restart route

| Key | Value |
|-----|-------|
| **Files** | `routes/admin.py` (L225) and `routes/agent_api.py` (L344) |
| **Bug** | Both register `@bp.route('/admin/server/restart')`. Flask uses whichever was registered last — unpredictable. |
| **Fix** | Keep the route in `admin.py` (where admin routes belong). Remove the duplicate from `agent_api.py`. If agent_api needs restart capability, have it call a shared function rather than registering the same route. |
| **Test** | `flask routes | grep restart` shows exactly one `/admin/server/restart` entry |

### 0.5 — Deduplicate triple 96127

| Key | Value |
|-----|-------|
| **Bug** | `calculator_detector.py`, `screening.py`, and `pediatric.py` all emit CPT 96127 (brief emotional/behavioral assessment). CMS allows max 1 per encounter. Patient gets 3 identical recs. |
| **Fix** | (a) In `engine.py`, after collecting all detector results, add a dedup step that keeps only the highest-scoring 96127 opportunity when multiple exist. OR (b) Add a `_96127_emitted` flag to detection context so downstream detectors skip if already emitted. Approach (a) is safer — dedup at the engine level. |
| **Test** | Create a test patient with GAD-7 score + depression screening + age in pediatric range → verify only 1 96127 opportunity |

### 0.6 — Add threading lock to VSAC code cache

| Key | Value |
|-----|-------|
| **File** | `billing_engine/shared.py` (L22) |
| **Bug** | `_vsac_code_cache = {}` is mutated by concurrent APScheduler threads without synchronization |
| **Fix** | Add `_vsac_code_cache_lock = threading.Lock()` at module level. Wrap all reads/writes to `_vsac_code_cache` in `with _vsac_code_cache_lock:` blocks. |
| **Test** | Import shared.py → verify `_vsac_code_cache_lock` exists and is a `threading.Lock` |

### 0.7 — Fix TCM `add_business_days()` off-by-one

| Key | Value |
|-----|-------|
| **File** | `billing_engine/shared.py` (L128–137) |
| **Bug** | Starts counting business days from `date + 1`, making the deadline 1 business day late vs CMS requirement. Example: discharge Monday → should count Tue as day 1, but current code makes Tue = day 0 and adds an extra day. |
| **Fix** | Change starting point to `date` instead of `date + timedelta(days=1)`, or adjust the loop to match CMS's "within N business days of discharge" definition. Create unit test with known dates. |
| **Test** | `add_business_days(datetime(2025, 3, 17), 2)` (Monday) should return Wednesday 3/19 (2 biz days later). Verify with Thursday → skip weekend case too. |

### 0.8 — Replace pickle with JSON for cookie serialization

| Key | Value |
|-----|-------|
| **Files** | `scrapers/pdmp.py` (L309) and `scrapers/viis.py` (L309) |
| **Bug** | `pickle.load()` / `pickle.dump()` for cookie storage — arbitrary code execution vulnerability if cookie file is tampered with |
| **Fix** | Replace with `json.load()` / `json.dump()`. Cookies are simple dicts of strings — JSON handles them natively. Add try/except for malformed JSON → delete and re-authenticate. |
| **Test** | Verify cookie files are valid JSON after save. Verify load handles corrupted file gracefully (deletes and returns None). |

### PHASE 0 CHECKPOINT
- [ ] All 8 fixes applied
- [ ] `python test.py` — all 127+ tests pass
- [ ] `python test_phase7.py` — all 70+ tests pass
- [ ] Manual smoke: launch app, navigate dashboard, open patient chart, check billing review
- [ ] Commit: `v1.2.0-alpha.1 — Critical bug fixes`

---

## PHASE 1: SECURITY HARDENING

> **Goal:** Close all security vulnerabilities before exposing the app on a clinic network.
> **Actor:** Copilot (100% automated)

### 1.1 — Fix zip-slip in updater.py

| Key | Value |
|-----|-------|
| **File** | `utils/updater.py` (L85) |
| **Bug** | `zipfile.extractall()` without validating that extracted paths don't escape the target directory |
| **Fix** | Before extraction, iterate `zipfile.namelist()` and reject any entry where `os.path.commonpath([target_dir, os.path.join(target_dir, name)]) != target_dir` or that contains `..`. |
| **Test** | Create a test ZIP with a `../malicious.txt` entry → verify extraction is blocked |

### 1.2 — Fix file handle leak in app/__init__.py

| Key | Value |
|-----|-------|
| **File** | `app/__init__.py` (L262) |
| **Bug** | `f = open(...)` without `with` statement — file handle leaked on exceptions |
| **Fix** | Replace with `with open(...) as f:` block |
| **Test** | No resource warnings in test output |

### 1.3 — Fix cui_result variable in tools.py

| Key | Value |
|-----|-------|
| **File** | `routes/tools.py` |
| **Bug** | `pa_generate()` uses `'cui_result' in dir()` — anti-pattern that checks local namespace incorrectly |
| **Fix** | Initialize `cui_result = None` before the conditional block, then check `if cui_result is not None:` |
| **Test** | Navigate to PA generation page → no errors |

### 1.4 — Move RVU_TABLE definition in timer.py

| Key | Value |
|-----|-------|
| **File** | `routes/timer.py` |
| **Bug** | `RVU_TABLE` referenced at L113 but defined at L664 — works at module level but fragile |
| **Fix** | Move `RVU_TABLE = {...}` to the top of the file (after imports) |
| **Test** | Import timer blueprint, verify `RVU_TABLE` is accessible |

### 1.5 — Fix mrn_reader race condition

| Key | Value |
|-----|-------|
| **File** | `agent/mrn_reader.py` |
| **Bug** | `_chart_open_since` and `_last_warning_at` accessed outside lock scope |
| **Fix** | Move variable reads/writes inside the existing `with _lock:` blocks |
| **Test** | Code review — all shared state access within lock |

### 1.6 — Delete stale config bytecode

| Key | Value |
|-----|-------|
| **File** | `__pycache__/config.cpython-311.pyc` |
| **Bug** | Compiled bytecode of config.py may contain plaintext secrets, and __pycache__ is not always gitignored |
| **Fix** | Delete the file. Add `__pycache__/` to `.gitignore` if not already present. |

### PHASE 1 CHECKPOINT
- [ ] All 6 fixes applied
- [ ] `python test.py` — all tests pass
- [ ] `python test_phase7.py` — all tests pass
- [ ] No `ResourceWarning` in test output
- [ ] Commit: `v1.2.0-alpha.2 — Security hardening`

---

## PHASE 2: BILLING ACCURACY

> **Goal:** Ensure all billing detectors match CMS rules and produce correct recommendations.
> **Actor:** Copilot (100% automated)

### 2.1 — Add STI frequency guard

| Key | Value |
|-----|-------|
| **File** | `billing_engine/detectors/sti.py` |
| **Bug** | Fires Hep C screening for every visit for 18-79yo without checking if screening was already done within the lookback period |
| **Fix** | Check `patient_data.get('last_hep_c_screen')` or equivalent. If screened within lookback period (configurable, default 12 months), suppress. Mirror pattern used by other screening detectors. |
| **Test** | Patient with recent Hep C screen → no opportunity. Patient without → opportunity generated. |

### 2.2 — Review prolonged service unit calculation

| Key | Value |
|-----|-------|
| **File** | `billing_engine/detectors/prolonged.py` (L35) |
| **Bug** | `threshold - 15` formula may overcount by 1 unit — need to verify against CMS 2024 prolonged service rules |
| **Fix** | CMS rule: 99354 starts at >30min beyond typical time. Each additional 30min = 99355 unit. Verify the formula matches. If off by one, fix. |
| **Test** | 45 min over → 1 unit 99354. 75 min over → 1×99354 + 1×99355. 105 min over → 1×99354 + 2×99355. |

### 2.3 — Add MDM check to TCM code selection

| Key | Value |
|-----|-------|
| **File** | `billing_engine/detectors/tcm.py` (L39) |
| **Bug** | Selects 99496 vs 99495 based only on time window; CMS requires MDM complexity (moderate vs high) |
| **Fix** | Add MDM complexity check from patient_data. If MDM is moderate + 14-day contact → 99495. If MDM is high + 7-day contact → 99496. Current logic only checks time — need to add MDM as a factor. Log a note if MDM data is unavailable (default to lower code). |
| **Test** | High MDM + 7-day window → 99496. Moderate MDM + 14-day → 99495. No MDM data → 99495 with note. |

### 2.4 — Fix NADAC dataset ID

| Key | Value |
|-----|-------|
| **File** | `app/api_config.py` (L155) |
| **Bug** | `NADAC_DATASET_ID = "a]4y-5ky]b"` — bracket characters indicate garbled copy/paste |
| **Fix** | Look up the correct NADAC dataset identifier from data.cms.gov. The Socrata dataset ID format is `xxxx-xxxx` (alphanumeric). If cannot verify, add a TODO and disable the NADAC pricing endpoint with a meaningful error. |
| **Cory Action** | Verify the correct NADAC dataset ID from https://data.cms.gov/provider-data/dataset/nadac |

### 2.5 — Verify TCM deadline alignment with CMS

| Key | Value |
|-----|-------|
| **Note** | This is the validation step for 0.7 — after fixing off-by-one, run comprehensive date tests |
| **Test Matrix** | Discharge on Mon/Tue/Wed/Thu/Fri → verify 2-day and 7-day deadlines skip weekends correctly |

### PHASE 2 CHECKPOINT
- [ ] All 5 items addressed
- [ ] Billing engine unit tests pass
- [ ] Manual: Run billing review for test patients → verify no duplicate 96127, correct TCM codes, STI frequency respected
- [ ] Commit: `v1.2.0-alpha.3 — Billing accuracy`

---

## PHASE 3: CODE QUALITY & CLEANUP

> **Goal:** Resolve all medium/low-priority issues for a clean codebase.
> **Actor:** Copilot (100% automated)

### 3.1 — Fix generators.py syntax error
- **File:** `tools/emulated_patient_generator/generators.py` L13
- **Fix:** Correct the invalid ternary inside import statement

### 3.2 — Fix MENU_ACTIONS reference in main.js
- **File:** `static/js/main.js` L1517
- **Fix:** Change `MENU_ACTIONS.openWhatsNew` → `_menuActions.openWhatsNew` (matching the actual variable name)

### 3.3 — Add __repr__ to 4 models
- **Files:** PracticeBookmark, CodeFavorite, CodePairing, CalculatorResult
- **Fix:** Add standard `__repr__` returning `<ClassName id=X>` format

### 3.4 — Add FK indexes
- **Fix:** Add `index=True` to the 17+ FK columns identified in audit (highest priority: `AuditLog.user_id`)
- **Migration:** Create `migrations/migrate_add_fk_indexes.py`

### 3.5 — Add missing cascades
- **Fix:** BillingOpportunity → ClosedLoopStatus, MonitoringRule → MonitoringSchedule — add `cascade="all, delete-orphan"` to relationships

### 3.6 — Consolidate `_require_admin` decorator
- **Fix:** Move to `utils/` or `app/` as a shared decorator. Update 3 route files to import from shared location.

### 3.7 — Consolidate `_fetch_rxnorm()` duplicate
- **Fix:** Move shared RxNorm fetch logic to a service utility. Update `routes/patient.py` and `routes/medref.py`.

### 3.8 — Remove dead code in dashboard.py
- **Fix:** Remove `_collect_jobs` function if unused

### 3.9 — Remove empty CSS ruleset
- **File:** `static/css/main.css` L787
- **Fix:** Remove `.nav-item {}` empty block

### 3.10 — Move stray migration files
- **Fix:** Move 4 migration files from root to `migrations/` directory

### 3.11 — Delete stale __pycache__ bytecode
- **Fix:** Delete `__pycache__/config.cpython-311.pyc`

### 3.12 — Clean up tesseract language packs (optional)
- **Fix:** Remove all `tessdata/*.traineddata` except `eng.traineddata` (saves ~3GB in distribution)
- **Note:** Only do this on the build/deploy side — keep dev tesseract intact

### PHASE 3 CHECKPOINT
- [ ] All 12 items addressed
- [ ] `python test.py` — all tests pass
- [ ] `python test_phase7.py` — all tests pass
- [ ] No lint warnings in modified files
- [ ] Commit: `v1.2.0-beta.1 — Code quality cleanup`

---

## PHASE 4: USER CONFIGURATION

> **Goal:** Cory provides all environment-specific values that cannot be automated.
> **Actor:** Cory (with Copilot guidance)

### ⚠️ IMPORTANT: Copilot cannot infer these values — they are environment-specific.

### 4.1 — Amazing Charts Credentials
| Setting | Where | Format | Notes |
|---------|-------|--------|-------|
| `AC_LOGIN_USERNAME` | config.py | String | AC application username |
| `AC_LOGIN_PASSWORD` | config.py | String | AC application password |
| `AC_PRACTICE_ID` | config.py | String | From AC About dialog |
| `AC_PRACTICE_NAME` | config.py | String | Practice display name |
| `AC_VERSION` | config.py | String (e.g. "12.3.4") | From AC About dialog |
| `AC_BUILD` | config.py | String | From AC About dialog |

**How to get:** Open Amazing Charts → Help → About → copy Practice ID, Version, Build.

### 4.2 — Amazing Charts File Paths
| Setting | Where | Format | Notes |
|---------|-------|--------|-------|
| `AC_EXE_PATH` | config.py | Absolute path | e.g. `C:\Program Files\Amazing Charts\ac.exe` |
| `AC_LOG_PATH` | config.py | Absolute path | e.g. `C:\AC\Logs\` |
| `AC_DB_PATH` | config.py | Absolute path | AC local database location |
| `AC_IMPORTED_ITEMS_PATH` | config.py | Absolute path | Where AC reads CDA XML imports |
| `CLINICAL_SUMMARY_EXPORT_FOLDER` | config.py | Absolute path | Where AC writes CDA XML exports |

**How to get:** Open File Explorer → navigate to AC installation → note each path. Check AC Settings for import/export paths.

### 4.3 — NetPractice / CGM webPRACTICE
| Setting | Where | Format | Notes |
|---------|-------|--------|-------|
| `NETPRACTICE_URL` | config.py | URL | e.g. `https://yourpractice.cgmwebpractice.com` |
| `NETPRACTICE_CLIENT_NUMBER` | config.py | String | Practice client number |
| `NETPRACTICE_BOOKMARKED_URL` | config.py | URL | Bookmarked schedule page URL |

**How to get:** Open Chrome → navigate to NetPractice → copy URL from address bar. Client number is in the login page or account settings.

### 4.4 — Pushover Notifications
| Setting | Where | Format | Notes |
|---------|-------|--------|-------|
| `PUSHOVER_USER_KEY` | config.py | 30-char alphanumeric | Your Pushover user key |
| `PUSHOVER_API_TOKEN` | config.py | 30-char alphanumeric | CareCompanion app token |
| `PUSHOVER_EMAIL` | config.py | Email | Pushover account email |

**How to get:** Log in to https://pushover.net → Dashboard shows User Key. Create an Application → copy API Token.

### 4.5 — External API Keys
| Setting | Where | Source | Free? |
|---------|-------|--------|-------|
| `OPENFDA_API_KEY` | config.py | https://open.fda.gov/apis/authentication/ | ✅ Free |
| `PUBMED_API_KEY` | config.py | https://www.ncbi.nlm.nih.gov/account/ | ✅ Free |
| `UMLS_API_KEY` | config.py | https://uts.nlm.nih.gov/uts/profile | ✅ Free (UMLS license required, expires 2026-03-19) |
| `LOINC_USERNAME` | config.py | https://loinc.org/get-started/ | ✅ Free registration |
| `LOINC_PASSWORD` | config.py | Same account | ✅ Free |

**Status:** All are free. UMLS key is already known (needs renewal by 2026-03-19).

### 4.6 — Scraper Credentials
| Setting | Where | Source | Notes |
|---------|-------|--------|-------|
| `VIIS_USERNAME` | config.py | Virginia Dept of Health VIIS account | Requires clinic provider enrollment |
| `VIIS_PASSWORD` | config.py | Same | — |
| `PDMP_EMAIL` | config.py | PMP AWARxE (Virginia) account | Requires DEA registration |
| `PDMP_PASSWORD` | config.py | Same | — |

**How to get:** These are existing clinic system credentials. Cory should have them.

### 4.7 — SMTP (Email Reports)
| Setting | Where | Format | Notes |
|---------|-------|--------|-------|
| `SMTP_SERVER` | config.py | Hostname | e.g. `smtp.gmail.com` or clinic mail server |
| `SMTP_PORT` | config.py | Integer | 587 (TLS) or 465 (SSL) |
| `SMTP_USER` | config.py | Email | Sending account |
| `SMTP_PASS` | config.py | String | App password (NOT regular password for Gmail) |
| `SMTP_FROM` | config.py | Email | From address |
| `SMTP_TO` | config.py | Email | Report recipient |

**How to get:** If using Gmail: Google Account → Security → 2-Step Verification → App Passwords → generate for "CareCompanion".

### 4.8 — Screen/OCR Configuration
| Setting | Where | Notes |
|---------|-------|-------|
| `SCREEN_RESOLUTION` | config.py | Work PC monitor resolution (e.g. `(1920, 1080)`) |
| `MRN_CAPTURE_REGION` | config.py | Pixel region of AC title bar showing MRN |
| `TESSERACT_PATH` | config.py | Path to bundled tesseract.exe |

**How to get:** These are calibrated on the work PC using the MRN calibration tool (F28a).

### 4.9 — Chrome Configuration
| Setting | Where | Notes |
|---------|-------|-------|
| `CHROME_EXE_PATH` | config.py | Path to Chrome executable on work PC |
| `CHROME_CDP_PORT` | config.py | Default `9222` — only change if conflicting |
| `CHROME_DEBUG_PROFILE_DIR` | config.py | e.g. `C:\Users\coryd\AppData\Local\Google\Chrome\Automation` |

### 4.10 — Database Path
| Setting | Where | Notes |
|---------|-------|-------|
| `DATABASE_PATH` | config.py | Default works for most cases |
| `BACKUP_PATH` | config.py | Where daily backups are stored |

### 4.11 — Agent Timing Configuration
| Setting | Where | Default | Notes |
|---------|-------|---------|-------|
| `IDLE_THRESHOLD_SECONDS` | config.py | 300 | Agent idle detection |
| `MAX_CHART_OPEN_MINUTES` | config.py | 30 | Chart duration alert |
| `INBOX_CHECK_INTERVAL_MINUTES` | config.py | 15 | Inbox poll frequency |
| `NOTIFY_QUIET_HOURS_START` | config.py | 22 | No push after 10pm |
| `NOTIFY_QUIET_HOURS_END` | config.py | 7 | No push before 7am |

**Note:** These have sensible defaults. Adjust after first week of use.

### 4.12 — Windows Task Scheduler
| Item | Notes |
|------|-------|
| Import `agent_startup.xml` | Task Scheduler → Import Task → select file → set "Run whether user is logged on or not" |
| Verify trigger | Trigger: At system startup, Delay: 30 seconds |
| Set user account | Use the clinic PC's Windows login account |

### 4.13 — SECRET_KEY
| Setting | Notes |
|---------|-------|
| `SECRET_KEY` | Auto-generates on first run. For production: set a fixed 32+ char random string so sessions survive restarts. Generate with: `python -c "import secrets; print(secrets.token_hex(32))"` |

### PHASE 4 CHECKPOINT
- [ ] All 13 configuration sections reviewed
- [ ] config.py populated with real values (at minimum: AC paths, NP URL, Pushover keys, API keys)
- [ ] `python -c "import config; print(config.AC_EXE_PATH)"` returns valid path
- [ ] SMTP test email sent successfully
- [ ] Secret key is fixed (not auto-generated)
- [ ] No placeholder values remain in config.py

---

## PHASE 5: WORK-PC INTEGRATION

> **Goal:** Connect CareCompanion to the physical clinic workstation.
> **Actor:** Cory (on work PC) + Copilot (remote debugging if needed)

### 5.1 — Transfer Application
1. Build: `python build.py` → creates `dist/NP_Companion_v1.2.0.zip`
2. Copy ZIP to work PC via USB or network share
3. Extract to `C:\CareCompanion\` (or preferred location)
4. Verify: `dir C:\CareCompanion\NP_Companion\` shows all expected files

### 5.2 — First Launch
1. Run `Start_CareCompanion.bat` (or `NP_Companion.exe`)
2. App creates fresh database from `carecompanion_empty.db`
3. Register admin user at first-run screen
4. Verify: Dashboard loads at `http://localhost:5000`

### 5.3 — Amazing Charts Connection
1. Open Amazing Charts on the same PC
2. Navigate to patient chart
3. Open CareCompanion → Admin → Agent → "Calibrate MRN Reader"
4. Follow calibration wizard to set MRN capture region
5. Verify: MRN appears in CareCompanion status bar when chart is open

### 5.4 — NetPractice Connection
1. Open CareCompanion → Admin → NetPractice Setup Wizard
2. Follow 4-step wizard (URL, client number, Chrome debug, login)
3. Verify: Today's schedule appears on Dashboard

### 5.5 — Scraper Verification
1. PDMP: Admin → Tools → PDMP → test search
2. VIIS: Admin → Immunizations → VIIS → test lookup
3. Verify: both return data without errors

### 5.6 — Push Notification Test
1. Admin → Settings → Notifications → "Send Test Push"
2. Verify: Pushover notification arrives on phone

### PHASE 5 CHECKPOINT
- [ ] App launches and runs without errors
- [ ] MRN reader detects open chart
- [ ] Schedule loads from NetPractice
- [ ] At least one scraper returns data
- [ ] Push notification received
- [ ] Agent tray icon visible and green

---

## PHASE 6: BUILD, TEST & DEPLOY

> **Goal:** Final validation, build, and go-live.
> **Actor:** Copilot (test writing) + Cory (execution on work PC)

### 6.1 — Run Full Test Suite
```
python test.py          # 127+ main tests
python test_phase7.py   # 70+ UI tests
```
All must pass. Any failure → back to relevant phase.

### 6.2 — Run Deployment Checker
```
python tools/deploy_check.py
```
Should report all green. After fixing verify_all.py (Phase 0.2), also run:
```
python tools/verify_all.py
```

### 6.3 — Smoke Test Matrix

| Test | Steps | Expected |
|------|-------|----------|
| Dashboard | Open app → Dashboard | Schedule loads, widgets rendered |
| Patient Chart | Click patient → Chart view | All 21 widgets render, vitals chart works |
| Timer | Start timer → stop → submit | Time logged, billing suggestions appear |
| Billing Review | Timer page → Billing Review tab | Opportunities listed, scoring visible, Why-Not links work |
| Inbox | Navigation → Inbox | Inbox items load from last scan |
| Orders | Navigation → Orders | Order sets listed, can execute (or mock execute) |
| Medref | Search "metformin" | Drug info, interactions, pricing shown |
| Calculators | Open BMI calculator → enter values | Score computed, history saved |
| Dark Mode | Settings → Theme → Dark | All pages render correctly |
| Morning Briefing | Navigation → Intelligence → Briefing | Today's prep summary loads |
| Admin | Admin → Dashboard | All admin panels accessible |
| Agent Status | Admin → Agent | Agent health green, jobs listed |
| Push Notif | Trigger test alert | Phone receives push |
| EOD Check | Tools → End of Day | Checklist renders correctly |

### 6.4 — Backup Verification
1. Admin → Settings → Backup → "Create Backup Now"
2. Verify backup file exists in backup path
3. Run `python tools/backup_restore_test.py`

### 6.5 — Go-Live
1. Set `DEBUG = False` in config.py
2. Set fixed `SECRET_KEY`
3. Import `agent_startup.xml` into Task Scheduler
4. Reboot PC → verify auto-start
5. Monitor logs for first full business day
6. Version bump: 1.2.0 release

### PHASE 6 CHECKPOINT (FINAL)
- [ ] All tests pass (127+ main, 70+ UI)
- [ ] Deploy checker all green
- [ ] All 14 smoke tests pass
- [ ] Backup verified
- [ ] Agent auto-starts on reboot
- [ ] First full day monitored — no crashes, no error spike
- [ ] **🎉 v1.2.0 RELEASED**

---

## APPENDIX A: CREDENTIAL QUICK-REFERENCE

Summary of everything Cory needs to gather before deployment:

### Must Have (App Won't Fully Work Without)
| Credential | Source | Difficulty |
|------------|--------|------------|
| AC Username/Password | Already known | ✅ Easy |
| AC Practice ID/Version/Build | AC About dialog | ✅ Easy |
| AC file paths (exe, log, DB, import, export) | File Explorer | ✅ Easy |
| NetPractice URL + Client Number | Browser bookmark | ✅ Easy |
| Work PC Chrome path | File Explorer | ✅ Easy |
| Work PC screen resolution | Display Settings | ✅ Easy |
| SECRET_KEY (generate) | Python one-liner | ✅ Easy |

### Should Have (Features degraded without)
| Credential | Source | Difficulty |
|------------|--------|------------|
| Pushover User Key + API Token | pushover.net account | ✅ Easy (5 min) |
| OpenFDA API Key | open.fda.gov | ✅ Easy (2 min) |
| PubMed API Key | ncbi.nlm.nih.gov | ✅ Easy (5 min) |
| UMLS API Key | Already have (renew by 2026-03) | ✅ Already done |
| LOINC Username/Password | loinc.org | ✅ Easy (5 min) |

### Nice to Have (Optional features)
| Credential | Source | Difficulty |
|------------|--------|------------|
| VIIS Username/Password | VA Dept of Health | ⚠️ May need enrollment |
| PDMP Email/Password | PMP AWARxE | ⚠️ Requires DEA |
| SMTP credentials | Gmail app password or clinic SMTP | ⚠️ Moderate |

---

## APPENDIX B: TESTING THEORY

### Test Taxonomy
| Type | Location | Runner | Coverage |
|------|----------|--------|----------|
| Unit tests (models, billing) | `test.py` | pytest-style asserts | Models, billing logic, API caching |
| UI tests (templates, JS) | `test_phase7.py` | pytest-style HTTP | Menu bar, bookmarks, command palette, themes |
| Integration tests | `tools/` | Standalone scripts | Deploy check, connectivity, backup, clinical summary |
| Smoke tests | Manual (Phase 6.3) | Human | End-to-end feature walkthrough |

### Test-First Approach for Bug Fixes
Each Phase 0-2 fix should:
1. Write a failing test that exercises the bug
2. Apply the fix
3. Verify the test now passes
4. Run full suite to ensure no regressions

### Regression Gates
- **No PR without green suite** — all 127+ main tests must pass
- **Billing changes require billing test update** — any detector change needs a test case
- **Template changes tested via test_phase7.py** — any UI change verified by HTTP test

---

## PHASE 7: REMAINING WORK — FINAL AUDIT (2026-03-22)

> **Generated from:** Comprehensive codebase audit across 4 parallel subagent passes
> **Context:** Phases 0–3 are 100% complete (127/127 main tests passing). Recent file reorganization moved test files to `tests/` and migrations to `migrations/`. This phase covers ALL remaining Copilot-actionable work before deployment.

### STATUS SUMMARY

| Area | Items | Priority | Actor |
|------|-------|----------|-------|
| **7A** Phase 7 Test Failures | 10 (7 fail + 3 error) | HIGH | Copilot |
| **7B** Documentation Stale References | ~50 refs across 8 files | HIGH | Copilot |
| **7C** Smart Bookmarks UI Completion | 6 sub-items | MEDIUM | Copilot |
| **7D** Split View Completion | 3 sub-items | MEDIUM | Copilot |
| **7E** AI Enhancements Completion | 5 sub-items | LOW | Copilot |
| **7F** LLM_ABOUT.md Refresh | 1 item | MEDIUM | Copilot |
| **7G** Misc Cleanup | 3 items | LOW | Copilot/Cory |

---

### 7A — Fix Phase 7 Test Failures (10 tests: 7 FAIL + 3 ERROR)

> **Current state:** `tests/test_phase7.py` — 41 passed, 7 failed, 3 errors
> **Root cause:** All failures are 500 errors from route handlers — NOT file-path issues.
> **Test command:** `$env:PYTHONIOENCODING = "utf-8"; venv\Scripts\python.exe tests\test_phase7.py`

**Failure inventory (exact output):**
```
[FAIL] Pin item: status=500 body=None
[ERROR] 7.4 pin/unpin: 'NoneType' object has no attribute 'get'
[FAIL] Add personal bookmark: status=500 body=None
[FAIL] Personal bookmark not found in GET: personal=[]
[FAIL] Reorder bookmarks: status=500 body=None
[ERROR] 7.5 bookmarks: list index out of range
[FAIL] Generate 1 Simple: status=500 body=None
[ERROR] 7.7 patient generator: 'NoneType' object has no attribute 'get'
[FAIL] Dismiss What's New: status=500 body=None
[FAIL] last_seen_version not set after dismiss
```

#### Root Cause Analysis

All 10 failures share one underlying problem: **the test client's session-based login (`sess['_user_id'] = str(TEST_USER_ID)`) does not fully initialize Flask-Login's `current_user` proxy**, so `current_user.get_pref(...)` returns `None` inside route handlers, which then crashes on `.get()` calls or `db.session.commit()` without rollback protection.

The fix has two parts:
1. **Add defensive error handling** in the 4 affected route handlers so they return proper JSON errors instead of 500s
2. **Fix the test client auth** so `current_user` is properly loaded

---

- [ ] **7A.1** Fix pin/unpin route error handling (`routes/auth.py` L1135–1162)
  - **File:** `routes/auth.py`, function `api_pin_menu()` (line ~1135)
  - **Problem:** `db.session.commit()` at line 1160 is unguarded. If `current_user` is not fully loaded, `current_user.set_pref()` fails and `commit()` throws an unhandled exception → 500
  - **Fix:** Wrap the commit in try/except:
    ```python
    try:
        current_user.set_pref('pinned_menu_items', pinned)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    ```
  - **Also check:** The `api_unpin_menu()` function (line ~1163) — apply same pattern
  - **Test:** Re-run `tests/test_phase7.py` — section 7.4 should go from ERROR → PASS

- [ ] **7A.2** Fix bookmarks route error handling (`routes/auth.py` L1220–1278)
  - **File:** `routes/auth.py`, functions `api_add_personal_bookmark()` (line ~1220), `api_reorder_bookmarks()`, `api_delete_bookmark()`
  - **Problem:** Multiple `db.session.commit()` calls (lines 1267, 1277) are unguarded. `_migrate_bookmarks()` is called on user pref data that may be `None` if `current_user` isn't loaded
  - **Fix:** Add try/except around each commit block. Also add a `None` guard:
    ```python
    personal = current_user.get_pref('bookmarks', [])
    if personal is None:
        personal = []
    if not isinstance(personal, list):
        personal = []
    personal = _migrate_bookmarks(personal)
    # ... rest of logic ...
    try:
        current_user.set_pref('bookmarks', personal)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    ```
  - **Apply to:** `api_add_personal_bookmark`, `api_reorder_bookmarks`, `api_delete_bookmark`, `api_get_bookmarks`
  - **Test:** Re-run — section 7.5 should improve

- [ ] **7A.3** Fix patient generator 500 (`routes/patient_gen.py` L35–104)
  - **File:** `routes/patient_gen.py`, function `generate()` (line ~35)
  - **Problem:** The `generate_patient()` call at line 86 and `build_cda()` at line 87 are not wrapped in try/except. If the generator crashes (e.g., missing data file, random.choice on empty list), the entire route returns 500 with no JSON body
  - **Fix:** Wrap the generation loop in try/except:
    ```python
    results = []
    for _ in range(count):
        try:
            patient = generate_patient(overrides, complexity)
            xml_str = build_cda(patient)
        except Exception as e:
            return jsonify({'error': f'Generation failed: {str(e)}'}), 500
        # ... rest of result building ...
    ```
  - **Also investigate:** Run `python -c "from tools.patient_gen.generators import generate_patient; p = generate_patient({}, 'Simple'); print(p['demo']['last'])"` to see if generator works standalone
  - **Test:** Re-run — section 7.7 should go from ERROR → PASS

- [ ] **7A.4** Fix dismiss-whats-new 500 (`routes/auth.py` L1415–1421)
  - **File:** `routes/auth.py`, function `api_dismiss_whats_new()` (line ~1415)
  - **Problem:** `db.session.commit()` at line 1420 is unguarded. 7 lines total, no error handling.
  - **Fix:**
    ```python
    @auth_bp.route('/api/settings/dismiss-whats-new', methods=['POST'])
    @login_required
    def api_dismiss_whats_new():
        version = current_app.config.get('APP_VERSION', '')
        try:
            current_user.set_pref('last_seen_version', version)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        return jsonify({'success': True})
    ```
  - **Test:** Re-run — section 7.8 "Dismiss What's New" should pass

- [ ] **7A.5** Fix test client authentication method (`tests/test_phase7.py` L90–96)
  - **File:** `tests/test_phase7.py`, function `authed_client()` (line 90)
  - **Current code:**
    ```python
    def authed_client():
        c = app.test_client()
        with app.app_context():
            with c.session_transaction() as sess:
                sess['_user_id'] = str(TEST_USER_ID)
        return c
    ```
  - **Problem:** Setting `_user_id` in the session is the correct Flask-Login approach, but the user object may not be in the DB session's identity map when the route handler runs. The test setup creates the app context, sets the session, but the route handler's `current_user` proxy may get a detached User object.
  - **Fix:** Verify that the `User` model's `get_id()` returns a string and that `login_manager.user_loader` correctly handles the ID. If the user_loader returns `None`, add a fallback. Also verify the `User` query works:
    ```python
    # Add to test setup (after line 96):
    # Verify auth works before running tests
    c = authed_client()
    with app.app_context():
        r = c.get('/api/bookmarks')
        if r.status_code == 500:
            print(f"WARNING: Auth may not work. Check user_loader in app/__init__.py")
            print(f"Response: {r.data.decode()[:200]}")
    ```
  - **Root analysis:** Find the `user_loader` callback in `app/__init__.py` — verify it handles string IDs
  - **Test:** After fix, all 10 failing tests should be resolved

- [ ] **7A.6** Run full test suite and verify
  - **Command:** `$env:PYTHONIOENCODING = "utf-8"; venv\Scripts\python.exe tests\test_phase7.py`
  - **Expected result:** 51 passed, 0 failed, 0 errors
  - **If still failing:** Add debug prints to the affected route handlers to log `current_user`, `current_user.is_authenticated`, and `type(current_user)` — this will reveal if the proxy is `AnonymousUserMixin`

### 7A CHECKPOINT
- [ ] All 10 test failures resolved
- [ ] `tests/test_phase7.py` → 51 passed, 0 failed, 0 errors
- [ ] `tests/test_verification.py` → 127 passed, 0 failed, 0 errors (no regressions)

---

### 7B — Fix Documentation Stale References (~50 references across 8 files)

> **Context:** Files were recently reorganized: `test.py` → `tests/test_verification.py`, `test_phase7.py` → `tests/test_phase7.py`, migrations moved to `migrations/`, `config.example.py` deleted. All active Python code references were already updated. These are documentation-only fixes.

- [ ] **7B.1** Update `Documents/dev_guide/final_plan.md` test commands
  - **Lines to fix:** Every occurrence of `python test.py` → `python tests/test_verification.py`, and `python test_phase7.py` → `python tests/test_phase7.py`
  - **Locations:** Phase 0 checkpoint (L103-104), Phase 1 checkpoint (L170-171), Phase 2 checkpoint (L219-220), Phase 3 checkpoint (L282-283), Phase 6.1 (L480-481)
  - **Fix:** Global find-replace within this file:
    - `python test.py` → `python tests/test_verification.py`
    - `python test_phase7.py` → `python tests/test_phase7.py`
  - **Also update:** Appendix B "Test Taxonomy" table — update Location column from `test.py` to `tests/test_verification.py` and `test_phase7.py` to `tests/test_phase7.py`

- [ ] **7B.2** Update `Documents/dev_guide/LLM_ABOUT.md`
  - **Lines to fix:** ~6 references to root-level test files and deleted files
  - **Specific changes:**
    - Line 20: Change `test.py` and `test_phase7.py` references to `tests/test_verification.py` and `tests/test_phase7.py`
    - Line 266: Remove or update `config.example.py` reference (file was deleted)
    - Lines 285-286: Update test file paths in testing section
    - Line 295: Remove `deploy_check_output.txt` reference (deleted artifact)
  - **Also update:** Version from `1.1.2` to `1.1.3` to match `PROJECT_STATUS.md`, or decide on canonical version
  - **Also update:** Test counts — main tests: 127, Phase 7 tests: **51** (once 7A is fixed; currently 41)

- [ ] **7B.3** Update `Documents/dev_guide/SETUP_GUIDE.md`
  - **Lines to fix:** Lines 239 and 368
  - **Change:** `python test.py` → `python tests/test_verification.py`

- [ ] **7B.4** Update `Documents/dev_guide/_ACTIVE_FINAL_PLAN.md`
  - **Lines to fix:** Lines 54, 128, 463, 623, 641, 645, 780, 877 (~10 references)
  - **Change:** All `python test.py` → `python tests/test_verification.py`
  - **Also fix:** Line 463 subprocess ref: `["python", "test.py"]` → `["python", "tests/test_verification.py"]`
  - **Also fix:** Line 641 subprocess ref: same pattern

- [ ] **7B.5** Update `Documents/dev_guide/PRE_BETA_DEPLOYMENT_CHECKLIST.md`
  - **Lines to fix:** Lines 73, 115, 232
  - **Change:** `python test.py` → `python tests/test_verification.py`
  - **Also change:** `venv\Scripts\python.exe test.py` → `venv\Scripts\python.exe tests\test_verification.py`

- [ ] **7B.6** Update `Documents/dev_guide/RUNNING_PLAN.md`
  - **Lines to fix:** Lines 405, 2659
  - **Change:** `python test.py` → `python tests/test_verification.py`
  - **Note:** This file is FROZEN (historical) — add a header note: `> NOTE: test.py was renamed to tests/test_verification.py in March 2026 file reorganization.`

- [ ] **7B.7** Update `Documents/dev_guide/UI_OVERHAUL.md`
  - **Line to fix:** Line 546
  - **Change:** `python test.py` → `python tests/test_verification.py`

- [ ] **7B.8** Mark Phase 0–3 checkpoint boxes as complete in `final_plan.md`
  - **Phase 0 checkpoint** (around line 100): Change all `[ ]` → `[x]`
  - **Phase 1 checkpoint** (around line 168): Change all `[ ]` → `[x]`
  - **Phase 2 checkpoint** (around line 217): Change all `[ ]` → `[x]`
  - **Phase 3 checkpoint** (around line 280): Change all `[ ]` → `[x]`
  - **Note:** Only check boxes for work that was actually completed. The "manual smoke" and "commit" checkboxes should remain unchecked if not done.

### 7B CHECKPOINT
- [ ] All documentation references updated
- [ ] No stale `test.py` or `test_phase7.py` references in active docs
- [ ] Phase 0–3 checkboxes reflect completed state

---

### 7C — Complete Smart Bookmarks UI (System 5)

> **Current state:** Backend is 100% complete. Frontend drag-to-bookmark is 60%. The bookmark bar renders but is **non-functional** — drop events, folder rendering, API calls, and context menus are all missing.
>
> **What exists:**
> - `PracticeBookmark` model (admin bookmarks in DB)
> - Full folder API: `POST /api/bookmarks/personal`, `POST /api/bookmarks/personal/folder/rename`, `POST /api/bookmarks/personal/folder/delete`
> - Data model supports `{ type: 'link', label, url }` and `{ type: 'folder', label, children: [...] }`
> - Migration auto-upgrades old flat bookmarks to typed schema (`_migrate_bookmarks()` in `routes/auth.py`)
> - HTML structure: `#bookmarks-bar` with `.bm-practice-section` + `.bm-personal-section`
> - Full CSS: `.bookmark-bar`, `.bookmark-chip`, `.bookmark-folder`, `.bookmark-folder-dropdown`, `.bm-add-btn`, `.bm-add-popover`
> - Drag detection: All `<a href>` marked as draggable, `dragstart` extracts href + text, `MutationObserver` re-marks new links, bookmarks bar has `dragover` listener with `.drag-over` highlight

- [ ] **7C.1** Implement drop handler for bookmarks bar (`static/js/main.js`)
  - **What to do:** In the bookmarks bar JS section, find the `dragover` listener and add a corresponding `drop` event handler
  - **Logic:**
    1. On `drop`, extract `label` and `url` from `event.dataTransfer`
    2. Call `fetch('/api/bookmarks/personal', { method: 'POST', body: JSON.stringify({label, url}), headers: {'Content-Type': 'application/json'} })`
    3. On success, re-render the bookmark chip in the bar (call existing `_renderBookmarks()` or equivalent)
    4. Prevent default and remove `.drag-over` class
  - **Find existing code:** Search `static/js/main.js` for `dragover` near `bookmarks-bar` — the drop handler goes right next to it
  - **Test:** Drag any page link to bookmarks bar → chip appears, persists on refresh

- [ ] **7C.2** Implement folder rendering in bookmarks bar
  - **What to do:** When `GET /api/bookmarks` returns items with `type: 'folder'`, render them as folder chips with a dropdown
  - **Logic:**
    1. In the bookmarks render function, check `item.type`
    2. If `type === 'folder'`: render chip with folder icon (📁), on click toggle a dropdown showing `item.children` as sub-chips
    3. If `type === 'link'`: render as normal bookmark chip (already exists)
    4. Use existing CSS classes: `.bookmark-folder`, `.bookmark-folder-dropdown`
  - **Test:** Create a folder via API → verify dropdown renders

- [ ] **7C.3** Add right-click context menu for bookmarks
  - **What to do:** Add a custom context menu on bookmark chips and the bookmarks bar
  - **Menu items:**
    - On empty bar area: "New Folder", "Add Bookmark"
    - On bookmark chip: "Delete", "Move to Folder..."
    - On folder chip: "Rename", "Delete Folder"
  - **Implementation:** Create a `<div class="bm-context-menu">` element, position it at cursor on `contextmenu` event, hide on click-away
  - **API calls:** Delete → `DELETE /api/bookmarks/personal/{index}`, Rename → `POST /api/bookmarks/personal/folder/rename`

- [ ] **7C.4** Implement chip reordering via drag
  - **What to do:** Allow dragging bookmark chips to reorder them within the bar
  - **Logic:**
    1. Make each `.bookmark-chip` draggable (already are)
    2. On `dragstart` of a chip, set a `data-reorder` flag so the drop handler distinguishes reorder from new-bookmark
    3. On `drop` on another chip or between chips, compute new order array
    4. Call `POST /api/bookmarks/personal/reorder` with `{order: [newIndexArray]}`
  - **Test:** Drag chip A after chip B → order persists on refresh

- [ ] **7C.5** Add delete button on bookmark chips
  - **What to do:** Add an `×` close button on each chip (visible on hover)
  - **CSS:** Use `.bookmark-chip:hover .bm-delete { display: inline; }` pattern
  - **JS:** On click, call `DELETE /api/bookmarks/personal/{index}`, then remove chip from DOM
  - **Test:** Hover chip → × appears → click → chip removed → refresh confirms

- [ ] **7C.6** Wire up "Add Bookmark" popover
  - **What to do:** The `.bm-add-btn` and `.bm-add-popover` CSS exists but the JS to show/populate it does not
  - **Logic:**
    1. Click `+` button → show popover with label/URL inputs
    2. On "Add" click → `POST /api/bookmarks/personal` → re-render bar
    3. "Cancel" → hide popover
  - **Test:** Click + → fill form → Add → chip appears

### 7C CHECKPOINT
- [ ] Personal bookmarks: add, delete, reorder all work end-to-end
- [ ] Folder creation, folder dropdown rendering work
- [ ] Drag-to-bookmark from any page link works
- [ ] Context menu available on right-click
- [ ] `tests/test_phase7.py` section 7.5 → all bookmarks tests pass

---

### 7D — Complete Split View (System 3)

> **Current state:** ~60% done. Core JS `SplitViewManager` class, draggable divider, Ctrl+click interceptor, and 2-pane CSS grid are all working. Missing: settings UI, multi-pane CSS, persistence.
>
> **What exists:**
> - `SplitViewManager` class with `open()`, `close()`, `toggle()` in `static/js/main.js`
> - Draggable divider with live resize
> - Split button in header with tooltip
> - Ctrl+click interceptor → opens URLs in secondary iframe pane
> - User preference endpoint: `GET/POST /api/settings/split-max-panes` (saves 2–4 pane preference)
> - CSS: `.split-view`, `.split-panes`, `.split-pane`, `.split-divider` — all styled and responsive

- [ ] **7D.1** Add multi-pane CSS grid (3-pane and 4-pane layouts)
  - **File:** `static/css/main.css`
  - **What to do:** Currently only 2-pane grid exists (`.split-panes { grid-template-columns: 1fr 1fr }`). Add:
    ```css
    .split-panes[data-panes="3"] { grid-template-columns: 1fr 1fr 1fr; }
    .split-panes[data-panes="4"] { grid-template-columns: 1fr 1fr 1fr 1fr; }
    ```
  - **Also add:** Responsive breakpoints — on tablet, collapse to 2 panes max. On mobile, disable split view entirely.
  - **Test:** Set `data-panes="3"` on element → verify 3 equal columns render

- [ ] **7D.2** Add pane settings picker UI
  - **File:** `templates/base.html` (settings area) + `static/js/main.js`
  - **What to do:** Add a small control (dropdown or radio buttons) in View menu or settings panel:
    - "Split Panes: [2] [3] [4]"
    - On selection, call `POST /api/settings/split-max-panes` with value

---
---

## FILE REORGANIZATION — COMPLETED MARCH 22, 2026

> **Context:** Root directory cleanup to reduce clutter, move test/migration files to proper directories, consolidate config templates, and delete generated output.

### What Was Done (Completed)

#### Files Deleted
| File | Reason |
|------|--------|
| `deploy_check_output.txt` | Generated test output (ANSI codes). Regenerable via `python tools/deploy_check.py`. |
| `config.example.py` | Settings merged into `.env.example`. Redundant config template eliminated. |

#### Files Moved
| From (root) | To | Reason |
|---|---|---|
| `test.py` | `tests/test_verification.py` | Belongs with other test files. Renamed for clarity. |
| `test_phase7.py` | `tests/test_phase7.py` | Matches `tests/test_phase15_*.py` convention. |
| `migrate_add_dismissal_reason.py` | `migrations/migrate_add_dismissal_reason.py` | Belongs with the other 57 migration files. |
| `migrate_add_dotphrase_sharing.py` | `migrations/migrate_add_dotphrase_sharing.py` | Same. |
| `migrate_add_notification_priority.py` | `migrations/migrate_add_notification_priority.py` | Same. |
| `migrate_add_template_sharing.py` | `migrations/migrate_add_template_sharing.py` | Same. |

#### Code References Updated (Verified Working)
| File | Change | Verified |
|---|---|---|
| `.gitignore` | Added `deploy_check_output.txt` | ✅ |
| `.env.example` | Merged all settings from deleted `config.example.py` | ✅ |
| `restart.bat` | `test.py` → `tests\test_verification.py` (4 refs) | ✅ |
| `tools/verify_all.py` | `test.py` → `tests/test_verification.py` (7 refs) | ✅ |
| `tools/deploy_check.py` | `test.py` → `tests/test_verification.py` (1 ref) | ✅ |
| `app/__init__.py` | Migration glob now searches BOTH root AND `migrations/` subfolder | ✅ |
| `tests/test_starter_pack.py` | Migration path updated to `migrations/` | ✅ |
| `tests/test_notification_tiers.py` | Migration path updated to `migrations/` | ✅ |
| `tests/test_template_library.py` | Migration path updated to `migrations/` | ✅ |
| `tests/test_phase7.py` | Fixed `dirname(__file__)` paths for CSS/JS (2 refs) | ✅ |
| `tests/test_verification.py` | Added `sys.path.insert` for parent dir | ✅ |
| `tests/test_phase7.py` | Added `sys.path.insert` for parent dir | ✅ |

#### Test Results After Reorganization
- **`tests/test_verification.py`**: **127 passed, 0 failed, 0 errors** ✅
- **`tests/test_phase7.py`**: **41 passed** (up from 36 — path fix recovered 5 tests). Remaining 7 failures / 3 errors are pre-existing API-level issues (500 errors on pin/bookmark/patient-generator/dismiss endpoints) — not file-path related.

---

### Remaining Tasks from File Reorganization

> **IMPORTANT:** These are leftover items from the March 22 reorganization that must be completed to avoid future breakage. None are runtime-blocking right now (all affected migrations have already been applied), but they WILL break if a fresh database setup is ever performed.

---

#### TASK R1 — Delete `Documents/CareCompanion.code-workspace` (Manual)

> **Status:** Blocked — terminal deletion commands were policy-denied.
> **Risk:** None (duplicate file, no code references).
> **Who:** Cory (manual action).

- [ ] **R1.1** Open File Explorer → navigate to `Documents/` inside the project
- [ ] **R1.2** Delete `CareCompanion.code-workspace`
  - This file is an exact duplicate of the root `CareCompanion.code-workspace`
  - Both contain: `{"folders": [{"path": ".."}]}`
  - The root copy is the one VS Code uses

---

#### TASK R2 — Fix 17 Broken Migration DB Paths (Critical for Fresh DB Setup)

> **Status:** Not started.
> **Risk:** MEDIUM — All 17 have already been applied to the live database (tracked in `_applied_migrations` table), so they won't re-run. But they WILL fail if:
>   - Setting up a fresh database on a new machine
>   - Running a migration manually for debugging
>   - Resetting the `_applied_migrations` table
>
> **Root cause:** These files use `os.path.dirname(__file__)` to find the database, which resolved correctly when they lived in the project root. Now that they're in `migrations/`, it resolves to `migrations/data/carecompanion.db` (wrong) instead of `data/carecompanion.db` (correct).
>
> **How `_run_pending_migrations()` works:**
> - Searches `migrate_*.py` in BOTH project root AND `migrations/` subfolder
> - For files with `def run_migration(app, db)`: calls them directly with Flask app context (DB path comes from app config — **safe**)
> - For files WITHOUT `run_migration`: runs them as **subprocess** with `cwd=project_root` (CWD is correct, but `__file__` still points to `migrations/filename.py` — **broken** if using `dirname(__file__)`)
>
> **The fix:** Change one line in each file — replace single `dirname(__file__)` with double `dirname(dirname(__file__))` to go up from `migrations/` to project root.
>
> **Actor:** Copilot (automated).

**Bucket A — 17 files with broken `dirname(__file__)` paths:**

- [ ] **R2.1** `migrations/migrate_add_dismissal_reason.py` (line 7)
  - **Current:** `DB = os.path.join(os.path.dirname(__file__), 'data', 'carecompanion.db')`
  - **Fix to:** `DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'carecompanion.db')`

- [ ] **R2.2** `migrations/migrate_add_notification_priority.py` (line 13)
  - **Current:** `DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'carecompanion.db')`
  - **Fix to:** `DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'carecompanion.db')`

- [ ] **R2.3** `migrations/migrate_add_template_sharing.py` (line 16)
  - **Current:** `DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'carecompanion.db')`
  - **Fix to:** `DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'carecompanion.db')`

- [ ] **R2.4** `migrations/migrate_add_ac_columns.py` (line 16)
  - **Current:** `DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'carecompanion.db')`
  - **Fix to:** `DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'carecompanion.db')`

- [ ] **R2.5** `migrations/migrate_add_bookmarks.py` (line 11)
  - **Current:** `DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'carecompanion.db')`
  - **Fix to:** `DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'carecompanion.db')`

- [ ] **R2.6** `migrations/migrate_add_escalation_columns.py` (line 9)
  - **Current:** `DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'carecompanion.db')`
  - **Fix to:** `DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'carecompanion.db')`

- [ ] **R2.7** `migrations/migrate_add_icd10_cache.py` (line 11)
  - **Current:** `DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'carecompanion.db')`
  - **Fix to:** `DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'carecompanion.db')`

- [ ] **R2.8** `migrations/migrate_add_insurer_type.py` (line 9)
  - **Current:** `DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'carecompanion.db')`
  - **Fix to:** `DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'carecompanion.db')`

- [ ] **R2.9** `migrations/migrate_add_macros.py` (line 9)
  - **Current:** `DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'carecompanion.db')`
  - **Fix to:** `DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'carecompanion.db')`

- [ ] **R2.10** `migrations/migrate_add_nlm_conditions_cache.py` (line 12)
  - **Current:** `DB_PATH = os.path.join(os.path.dirname(__file__), "data", "carecompanion.db")`
  - **Fix to:** `DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "carecompanion.db")`

- [ ] **R2.11** `migrations/migrate_add_patient_sex.py` (line 9)
  - **Current:** `DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'carecompanion.db')`
  - **Fix to:** `DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'carecompanion.db')`

- [ ] **R2.12** `migrations/migrate_add_recurring_messages.py` (line 13)
  - **Current:** `DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'carecompanion.db')`
  - **Fix to:** `DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'carecompanion.db')`

- [ ] **R2.13** `migrations/migrate_add_result_templates.py` (line 11)
  - **Current:** `DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'carecompanion.db')`
  - **Fix to:** `DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'carecompanion.db')`

- [ ] **R2.14** `migrations/migrate_add_rxnorm_cache.py` (line 12)
  - **Current:** `DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'carecompanion.db')`
  - **Fix to:** `DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'carecompanion.db')`

- [ ] **R2.15** `migrations/migrate_add_shared_pa.py` (line 9)
  - **Current:** `DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'carecompanion.db')`
  - **Fix to:** `DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'carecompanion.db')`

- [ ] **R2.16** `migrations/migrate_add_vsac_cache.py` (line 12)
  - **Current:** `DB_PATH = os.path.join(os.path.dirname(__file__), "data", "carecompanion.db")`
  - **Fix to:** `DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "carecompanion.db")`

- [ ] **R2.17** `migrations/migrate_add_api_cache_tables.py` (line 16)
  - **Current:** `DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'carecompanion.db')`
  - **Fix to:** `DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'carecompanion.db')`

- [ ] **R2.18** `migrations/migrate_cl21.py` (lines 12-13)
  - **Current:** `here = os.path.dirname(os.path.abspath(__file__))` / `return os.path.join(here, 'data', 'carecompanion.db')`
  - **Fix to:** `here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` / `return os.path.join(here, 'data', 'carecompanion.db')`

- [ ] **R2.19** `migrations/migrate_add_claim_columns.py` (lines 13-16) — Borderline: uses `config.DATABASE_PATH` with a fallback to `dirname(__file__)` when path is relative
  - **Current fallback:** `db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_path)`
  - **Fix fallback to:** `db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), db_path)`

- [ ] **R2.20** `migrations/migrate_add_forward_columns.py` (lines 13-16) — Same borderline pattern as R2.19
  - **Current fallback:** `db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_path)`
  - **Fix fallback to:** `db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), db_path)`

- [ ] **R2.21** After fixing all 20 files above, run a quick import check by executing each standalone (old-style) migration with `--help` or a dry-run to verify the DB path resolves correctly. At minimum, verify:
  ```
  python -c "import os; __file__ = 'migrations/migrate_add_dismissal_reason.py'; print(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'carecompanion.db'))"
  ```
  Should output the project root + `data/carecompanion.db`.

---

#### TASK R3 — Update Active Documentation References

> **Status:** Not started.
> **Risk:** LOW — Documentation only. No runtime impact. But will confuse future Copilot sessions that read these files for context.
> **Who:** Copilot (automated).
> **Rule:** Do NOT update `Documents/_archive/` files — those are historical records and should reflect what was true at the time they were written. Only update ACTIVE documentation that is still used as reference.

**Active documentation files that need updating:**

- [ ] **R3.1** `Documents/dev_guide/LLM_ABOUT.md` — 10 stale references
  - Update `test.py` → `tests/test_verification.py` (lines 20, 285)
  - Update `test_phase7.py` → `tests/test_phase7.py` (lines 20, 286)
  - Remove or update `config.example.py` reference (line 266) — file was deleted; reference `.env.example` instead
  - Update 4 root-level migration file references (lines 291-294) — now in `migrations/`
  - Update `deploy_check_output.txt` reference (line 295) — file was deleted
  - Update env vars section referencing config.example.py (line 642) — reference `.env.example` instead

- [ ] **R3.2** `Documents/dev_guide/final_plan.md` — Update inline test/tool references
  - All occurrences of `python test.py` → `python tests/test_verification.py`
  - All occurrences of `python test_phase7.py` → `python tests/test_phase7.py`
  - Example lines: 103, 104, 170, 171, 282, 283, 480, 481
  - Update file reference tables (lines 575-576)

- [ ] **R3.3** `Documents/dev_guide/_ACTIVE_FINAL_PLAN.md` — 15+ stale references
  - Update `test.py` → `tests/test_verification.py`
  - Update `config.example.py` references → `.env.example`
  - Update migration file paths to `migrations/` subfolder

- [ ] **R3.4** `Documents/dev_guide/SETUP_GUIDE.md` — 6 stale references
  - Line 126: `copy config.example.py config.py` → update instruction to reference `.env.example` and `.env` workflow
  - Line 239: `test.py` → `tests/test_verification.py`

- [ ] **R3.5** `Documents/dev_guide/PROJECT_STATUS.md` — 7 stale references
  - Lines 134-137: Update 4 migration file paths to `migrations/` prefix
  - Line 330: Update `config.example.py` reference

- [ ] **R3.6** `Documents/dev_guide/RUNNING_PLAN.md` — 10 stale references
  - Update migration file path references (lines 204, 289, 520)
  - Update `config.example.py` reference (line 1429)
  - Update `test.py` reference (line 405)

- [ ] **R3.7** `Documents/overview/SECURITY.md` — 1 stale reference
  - Line 223: Update `config.example.py` → `.env.example`

- [ ] **R3.8** `Documents/overview/UI_OVERHAUL.md` — 1 stale reference
  - Line 546: `python test.py` → `python tests/test_verification.py`

- [ ] **R3.9** `Documents/dev_guide/PRE_BETA_DEPLOYMENT_CHECKLIST.md` — 18 stale references
  - Update `config.example.py` reference (line 34)
  - Update `test.py` references throughout
  - Update tool path references

- [ ] **R3.10** `Documents/dev_guide/DEPLOYMENT_GUIDE.md` — 2 stale references
  - Update tool path references (lines 395, 416)

- [ ] **R3.11** Do NOT touch any files in `Documents/_archive/` — these are historical records

- [ ] **R3.12** After updating all active docs, search for any remaining stale references:
  ```
  grep -r "config\.example\.py\|\"test\.py\"\|'test\.py'" Documents/dev_guide/ Documents/overview/ --include="*.md"
  ```
  Confirm zero matches in active documentation (archive exclusions expected).

---

#### TASK R4 — Pre-Existing test_phase7.py Failures (Optional / Separate Track)

> **Status:** Known pre-existing issues — not caused by file reorganization.
> **Risk:** LOW — These are API endpoint failures, not path issues.
> **Who:** Copilot (separate task — do not bundle with reorganization cleanup).

The following 7 failures and 3 errors existed BEFORE the file reorganization and persist after:

- [ ] **R4.1** Pin item: `POST /api/bookmarks/pin` → status 500
- [ ] **R4.2** Personal bookmark add: status 500
- [ ] **R4.3** Bookmark reorder: status 500
- [ ] **R4.4** Patient generator (Simple): status 500
- [ ] **R4.5** What's New dismiss: status 500
- [ ] **R4.6** `last_seen_version` not set after dismiss
- [ ] **R4.7** Investigate root cause — likely missing test database fixtures or session state

---

#### TASK R5 — Pre-Existing Unicode Encoding Issue in test_verification.py (Optional)

> **Status:** Known pre-existing issue — not caused by file reorganization.
> **Risk:** LOW — Tests pass correctly; only the terminal output encoding fails on Windows.
> **Who:** Copilot (optional quality improvement).

`tests/test_verification.py` uses `→` (U+2192) in ~20 print statements. On Windows terminals with non-UTF-8 codepage, this causes `UnicodeEncodeError: 'charmap' codec can't encode character '\u2192'`. The tests themselves pass — only the console output crashes.

- [ ] **R5.1** Replace all `→` characters in print statements with `->` (ASCII-safe)
  - **Why:** Windows cmd.exe / PowerShell default codepage (cp1252) can't render U+2192
  - **Workaround that works now:** `$env:PYTHONIOENCODING = "utf-8"` before running
  - **Permanent fix:** Replace `→` with `->` in all print/format strings in `tests/test_verification.py` (~20 occurrences)
- [ ] **R5.2** Search all other test files for non-ASCII characters in print statements and replace similarly

---

### Migration System — Complete Audit Reference (61 files)

> **Purpose:** This table documents the DB path pattern used by every migration file in the `migrations/` folder. Use this to understand which files are safe and which need attention.

| Status | Count | Description |
|--------|-------|-------------|
| 🔴 Broken (Bucket A) | 17 | Uses single `dirname(__file__)` — looks for DB in `migrations/data/` (wrong) |
| ⚠️ Borderline (Bucket B₂) | 2 | Config fallback uses single `dirname(__file__)` — broken if config path is relative |
| 🟢 Safe — double dirname (Bucket B) | 16 | Uses nested `dirname(dirname(__file__))` — correctly reaches project root |
| 🟢 Safe — new style (Bucket C) | 12 | Has `def run_migration(app, db)` — uses Flask app context, no DB path needed |
| 🟢 Safe — delegated (Bucket C₂) | 1 | Uses `utils.paths.get_db_path()` — centralized path resolution |
| 🟡 Hardcoded (Bucket D) | 9 | Uses `'data/carecompanion.db'` relative path — works because subprocess sets `cwd=project_root` |
| ⚫ Other (Bucket E) | 4 | Various patterns — individually safe |

**Total: 61 migration files audited.**
    - Update `SplitViewManager` to use the preference
  - **JS logic:** On load, fetch `/api/settings/split-max-panes`, store in `SplitViewManager._maxPanes`
  - **Test:** Change setting to 3 → Ctrl+click 3 links → 3 panes render side-by-side

- [ ] **7D.3** Add state persistence to localStorage
  - **File:** `static/js/main.js` (SplitViewManager)
  - **What to do:** On split view open/close/resize, save state to `localStorage`:
    ```javascript
    localStorage.setItem('splitViewState', JSON.stringify({
        isOpen: true,
        paneUrls: ['/dashboard', '/patients'],
        dividerPosition: 50  // percent
    }));
    ```
  - On page load, if `splitViewState` exists and `isOpen`, restore the split view
  - **Test:** Open split view → navigate away → come back → split view still open with same URLs

### 7D CHECKPOINT
- [ ] 3-pane and 4-pane layouts render correctly
- [ ] User can choose pane count from UI
- [ ] Split view state persists across page loads
- [ ] Responsive: 2 panes max on tablet, hidden on mobile

---

### 7E — Complete AI Enhancements (System 9)

> **Current state:** ~50% done. Chat panel UI, `/api/ai/chat` endpoint, HIPAA acknowledgment modal, and user AI config all exist. Missing: workflow coach, NLP navigation, writing assistant, help popovers, rate limiting.
>
> **What exists:**
> - Chat panel UI: `.ai-panel` with messages, input, minimize button
> - Chat functions: `initAIPanel()`, `openAIPanel()`, `sendAIMessage()`
> - Main AI API: `/api/ai/chat` endpoint with message building + provider call
> - HIPAA acknowledgment: modal + checkbox + `/api/ai/acknowledge-hipaa` endpoint
> - User AI config: `can_use_ai()`, `get_ai_api_key()`, `ai_provider` methods

- [ ] **7E.1** Implement Workflow Coach (System 9A)
  - **Files:** `static/js/main.js` (AI panel section), `routes/ai_api.py`
  - **What to do:**
    1. Load `data/help_guide.json` into AI context as system prompt supplement
    2. Inject `window.__npRoutes` (already exists for command palette) into AI message context
    3. When AI responds with a page reference, format it as a clickable `[link text](/path)` that JS converts to `<a href="/path">link text</a>`
  - **Backend change:** In `/api/ai/chat` route, prepend help_guide context to the system message:
    ```python
    import json
    with open('data/help_guide.json') as f:
        help_data = json.load(f)
    system_msg = f"You are a clinical workflow assistant. Available features:\n{json.dumps(help_data, indent=2)}\n\nWhen referencing a feature, include its URL path."
    ```
  - **Frontend change:** In `sendAIMessage()`, parse AI response for `[text](path)` patterns and convert to clickable links
  - **Test:** Ask "how do I track labs?" → response includes link to `/labtrack`

- [ ] **7E.2** Implement Natural Language Navigation (System 9B)
  - **Files:** `static/js/main.js`
  - **What to do:**
    1. In the command palette input, detect natural language queries (e.g., "show me care gaps")
    2. Build a simple intent → route matcher using `window.__npRoutes` data
    3. If match confidence > threshold, show a "Navigate to [page]" action button
  - **Intent matching algorithm:**
    ```javascript
    function matchIntent(query) {
        const q = query.toLowerCase();
        return window.__npRoutes.find(r =>
            r.keywords && r.keywords.some(k => q.includes(k))
        );
    }
    ```
  - **Add keywords to routes:** In the context processor that builds `__npRoutes`, add a `keywords` array to each entry (e.g., `{path: '/caregap', label: 'Care Gaps', keywords: ['care gap', 'gaps', 'preventive', 'screening']}`)
  - **Test:** Type "where are the care gaps" in command palette → shows "Navigate to Care Gaps" option

- [ ] **7E.3** Implement Writing Assistant (System 9C)
  - **Files:** `static/js/main.js`, `static/css/main.css`
  - **What to do:**
    1. Add sparkle icon (✦) next to all `<textarea>` and `[contenteditable]` elements
    2. On click, open a small popover with "Suggest phrasing..." option
    3. Send current textarea content + context (which page, field name) to `/api/ai/chat` with a writing-assistant system prompt
    4. Display suggestion in popover — click to insert at cursor position
  - **CSS:** `.ai-sparkle { position: absolute; top: 4px; right: 4px; cursor: pointer; opacity: 0.6; }` + `:hover { opacity: 1; }`
  - **JS:** Use `MutationObserver` to attach sparkle to dynamically created textareas
  - **Test:** Click ✦ next to a note textarea → suggestion appears → click inserts text

- [ ] **7E.4** Implement Help Popovers (System 9D)
  - **Files:** `templates/base.html`, `static/js/main.js`, `data/help_guide.json`
  - **What to do:**
    1. Add `<span class="help-icon" data-help-id="feature_name">?</span>` next to page headers
    2. On hover: show brief tooltip from `help_guide.json[feature_name].summary`
    3. On click: show full popover with `.help-popover` class, containing description + "Learn More" link
  - **CSS exists:** `.help-icon` is already styled. Add `.help-popover` with backdrop.
  - **JS:** Create `initHelpPopovers()` that reads `data-help-id`, fetches from help_guide.json (cached in-memory), and renders tooltip/popover
  - **Pages to annotate:** Dashboard, Timer, Billing Review, Lab Track, Care Gaps, Inbox, Orders, Medref (8 pages minimum — add `data-help-id` to each page's `<h1>`)
  - **Test:** Hover `?` icon on Dashboard → tooltip shows. Click → popover with full help text.

- [ ] **7E.5** Implement rate limiting for AI features
  - **Files:** `static/js/main.js`, `models/user.py`
  - **What to do:**
    1. User preferences `ai_rate_limit_hourly` (default 20) and `ai_rate_limit_daily` (default 100) already exist as pref keys
    2. In `sendAIMessage()`, before making API call:
       - Read `sessionStorage` counters: `ai_calls_hour`, `ai_calls_day`, `ai_hour_reset`, `ai_day_reset`
       - If over limit, show warning message in chat panel instead of calling API
       - On successful call, increment counters and save to sessionStorage
    3. Show "Approaching limit" warning at 80% of hourly/daily cap
  - **Test:** Set hourly limit to 2 → make 2 AI calls → 3rd shows "Rate limit reached" message

### 7E CHECKPOINT
- [ ] Workflow coach injects help_guide context and returns clickable links
- [ ] NLP navigation matches natural language to routes in command palette
- [ ] Writing assistant sparkle icon appears next to textareas
- [ ] Help popovers render on 8+ pages
- [ ] Rate limiting prevents API abuse

---

### 7F — Refresh LLM_ABOUT.md

> **Context:** This file is the primary reference for future Copilot sessions. It must accurately reflect the current codebase state after all Phases 0–3 fixes, file reorganization, and any Phase 7 work.

- [ ] **7F.1** Update `Documents/dev_guide/LLM_ABOUT.md` to reflect current state
  - **Updates needed:**
    1. **File structure:** Remove root-level `test.py`, `test_phase7.py`, `config.example.py`, `deploy_check_output.txt` references. Add `tests/test_verification.py`, `tests/test_phase7.py` in correct locations.
    2. **Version:** Align with `PROJECT_STATUS.md` (currently says 1.1.2, PROJECT_STATUS says 1.1.3)
    3. **Test counts:** Update to current numbers (127 main, 51 Phase 7 target)
    4. **Blueprint count:** Verify and update (docs say 29, PROJECT_STATUS says 19 — actual is ~28 route files)
    5. **Model count:** Verify and update (docs say 82 classes, PROJECT_STATUS says 59+ — actual is 30 model files with multiple classes per file)
    6. **Bug status:** Add section noting Phases 0–3 completion with brief summary of what was fixed (8 critical bugs, 6 security items, 4 billing accuracy, 12 code quality)
    7. **Migration file locations:** Note that all migrations are now in `migrations/` directory
  - **Approach:** Read the full file, make a single comprehensive edit pass, verify accuracy against actual codebase

### 7F CHECKPOINT
- [ ] LLM_ABOUT.md version, paths, counts all match actual codebase
- [ ] Future Copilot sessions will get accurate context

---

### 7G — Miscellaneous Cleanup

- [ ] **7G.1** Delete `Documents/CareCompanion.code-workspace` (duplicate)
  - **Context:** This is an exact duplicate of the root-level `.code-workspace` file. Deletion was blocked by terminal policy in the prior session.
  - **Action:** Cory must manually delete: `Documents\CareCompanion.code-workspace`
  - **Verify:** `Test-Path "Documents\CareCompanion.code-workspace"` returns `False`

- [ ] **7G.2** Archive `Documents/dev_guide/REVIEW_2025_03_21.md`
  - **Context:** This review is from March 2025 — over 1 year old. Many items listed as CRITICAL/HIGH were fixed in Phases 0–3 or during prior UI overhaul work. Keeping it in active docs causes confusion.
  - **Action:** Move to `Documents/_archive/REVIEW_2025_03_21_LEGACY.md` with a header note:
    ```markdown
    > ✅ ARCHIVED — Items from this review were addressed in final_plan.md Phases 0–3 (March 2026).
    > See final_plan.md for current status.
    ```
  - **Alternative:** If keeping in place, add checked checkboxes `[x]` to every item confirmed fixed

- [ ] **7G.3** Fix Unicode test output on Windows (`tests/test_verification.py`)
  - **Context:** The test file uses `→` (U+2192) in print output labels. Windows terminal codepage cp1252 doesn't support this character, causing a `UnicodeEncodeError` crash unless `$env:PYTHONIOENCODING = "utf-8"` is set.
  - **Fix:** Replace all `→` characters in print statements with `->`:
    ```python
    # Before:
    print(f"  {label} → {result}")
    # After:
    print(f"  {label} -> {result}")
    ```
  - **Find:** `grep -n "→" tests/test_verification.py` — approximately 20 occurrences
  - **Alternative:** Add `# -*- coding: utf-8 -*-` header and wrap print with `try/except UnicodeEncodeError`
  - **Simpler alternative:** Add at the top of the file:
    ```python
    import sys, io
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    ```
  - **Test:** Run `venv\Scripts\python.exe tests\test_verification.py` WITHOUT `$env:PYTHONIOENCODING` set — should not crash

### 7G CHECKPOINT
- [ ] Duplicate workspace file deleted
- [ ] REVIEW doc archived or updated
- [ ] Tests run without Unicode encoding errors on Windows

---

### PHASE 7 MASTER CHECKPOINT
- [ ] `tests/test_verification.py` → 127 passed, 0 failed, 0 errors
- [ ] `tests/test_phase7.py` → 51 passed, 0 failed, 0 errors
- [ ] All documentation references point to correct file locations
- [ ] Smart Bookmarks bar is fully functional
- [ ] Split View supports 2–4 panes with persistence
- [ ] AI enhancements: workflow coach, NLP nav, writing assist, help popovers all work
- [ ] LLM_ABOUT.md accurately reflects codebase
- [ ] No stale files in repo
- [ ] Commit: `v1.2.0-rc.1 — Phase 7 complete, all systems functional`

---

### PRIORITY TRIAGE (Recommended Implementation Order)

| Order | Section | Why First | Est. Effort |
|-------|---------|-----------|-------------|
| 1 | **7A** Test Failures | Blocks all other testing/validation | 2–3 hours |
| 2 | **7B** Doc References | Quick wins, prevents confusion | 1 hour |
| 3 | **7G** Misc Cleanup | Quick wins, unblocks clean state | 30 min |
| 4 | **7F** LLM_ABOUT Refresh | Ensures future sessions get good context | 30 min |
| 5 | **7C** Smart Bookmarks | Visible user-facing feature | 5–7 days |
| 6 | **7D** Split View | Visible user-facing feature | 3–4 days |
| 7 | **7E** AI Enhancements | Largest scope, optional for beta | 4–6 days |

> **Minimum for deployment:** 7A + 7B + 7G + 7F (total ~4 hours)
> **Full completion:** All sections (~2–3 weeks)

---

*End of final_plan.md — Follow phases sequentially. Do not skip checkpoints.*

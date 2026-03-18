# NP Companion — Verification Checklist

**Last updated:** March 17, 2026 (CL22 — Clinical Summary Import & Patient Chart Widgets)

This is a **step-by-step guide** for someone who is not a programmer to verify that everything in NP Companion is working. Follow every step in order. If something fails, stop and note which step failed.

---

## Before You Start

You need:
- The NP Companion folder at `C:\Users\coryd\Documents\NP_Companion`
- The Python virtual environment already set up (`venv\` folder exists)
- Tesseract OCR installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`
- An internet connection (for Tailscale check only)

### Confirmed Work PC Environment (from AC Interface Reference v4)
| Property | Confirmed Value |
|---|---|
| Operating System | Windows 11 Pro |
| PC Hardware | HP EliteDesk 705 G5, AMD Ryzen 5 PRO 3400G, 16GB RAM |
| AC Version | 12.3.1 (build 297) |
| AC Window Title | `Amazing Charts EHR (32 bit)` |
| AC Installation | `C:\Program Files (x86)\Amazing Charts\AmazingCharts.exe` |
| AC Practice ID | 2799 (Family Practice Associates of Chesterfield) |
| AC Database | `\\192.168.2.51\Amazing Charts\AmazingCharts.mdf` |
| AC Log Path | `C:\Program Files (x86)\Amazing Charts\Logs` |
| Imported Items | `\\192.168.2.51\amazing charts\ImportItems\[MRN]\` |

---

## STEP 1 — Open PowerShell in the Project Folder

1. Open File Explorer
2. Navigate to `C:\Users\coryd\Documents\NP_Companion`
3. Click in the address bar at the top and type: `powershell` then press Enter
4. A blue PowerShell window should open
5. Type this command and press Enter:
   ```
   venv\Scripts\activate
  
   ```
6. You should see `(venv)` appear at the start of the command line. If you see an error about execution policies, type this first and press Enter, then try again:
   ```
   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
   ```

---

## STEP 2 — Run the Main Test Suite (Web App)

This checks that all 36 web pages and database tables work.

1. In the same PowerShell window, type:
   ```
   venv\Scripts\python.exe test.py
   ```
2. Wait for it to finish (takes about 5 seconds)
3. **What you should see:**
   ```
   Results: 36 passed, 0 failed, 0 errors out of 36 checks
   *** ALL CHECKS PASSED ***
   ```
4. **If something fails:** Write down which line says `FAIL` or `ERROR` and what the message is.

---

## STEP 3 — Run the Agent Mock Tests

This checks that the Amazing Charts automation pipeline works using the reference screenshots (no AC needed).

1. In the same PowerShell window, type:
   ```
   venv\Scripts\python.exe tests/test_agent_mock.py
   ```
2. Wait for it to finish (takes about 10-15 seconds — the OCR part is slow)
3. **What you should see:**
   ```
   Passed: 36
   Failed: 0
   All mock tests passed! The agent pipeline works with screenshots.
   ```
4. **If OCR tests fail:** Make sure Tesseract is installed. Open File Explorer and check that this file exists:
   ```
   C:\Program Files\Tesseract-OCR\tesseract.exe
   ```
   If it doesn't exist, download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
   Install it to the default location. Then try Step 3 again.

---

## STEP 4 — Start the Server

1. In the same PowerShell window, type:
   ```
   venv\Scripts\python.exe app.py
   ```
2. **What you should see:**
   ```
   * Running on all addresses (0.0.0.0)
   * Running on http://127.0.0.1:5000
   ```
3. **Leave this window open!** The server is now running. Don't close it.

---

## STEP 5 — Check the Website in Chrome

1. Open Google Chrome
2. Go to: `http://localhost:5000`
3. **You should see:** The login page
4. Log in with:
   - Username: `CORY`
   - Password: `ASDqwe123`
5. **You should see:** The Dashboard (Today View)

---

## STEP 6 — Check Each Page

Click each item in the sidebar and confirm the page loads without errors. You should see content, not a white screen or error message.

| # | Sidebar Link | What You Should See |
|---|---|---|
| 1 | **Dashboard** | Today's schedule (may be empty if no appointments loaded) |
| 2 | **Timer** | Timer dashboard with active session banner, daily summary stats, E&M distribution bar, today's sessions table with billing level dropdown and complex flag |
| 3 | **Inbox** | Inbox monitor with filter tabs and a Digest tab |
| 4 | **On-Call** | On-Call notes list with a "New Note" button |
| 5 | **Orders** | Order sets page |
| 6 | **Med Ref** | Medication reference page |
| 7 | **Lab Track** | Lab tracking dashboard with stats cards, tracked labs table, add tracking/panel forms |
| 8 | **Care Gaps** | Preventive care gaps overview with date navigation, scheduled patients with gap counts |
| 9 | **Metrics** | Productivity dashboard with 7 Chart.js charts, burnout indicators, benchmark toggle, weekly summary |
| 10 | **Tools** | Tools page |

**To check the Patient Chart page** (doesn't appear in sidebar — you get there from the dashboard):
- Go to the address bar and type: `http://localhost:5000/patient/99999`
- You should see the patient chart page (it will be empty since there's no data for MRN 99999, but it should load without errors)

**To check On-Call New Note:**
- Click **On-Call** in the sidebar, then click **New Note**
- You should see a form for creating a new on-call note

---

## STEP 7 — Check Admin Pages

1. Click your username in the top-right corner or go to the admin hub
2. Navigate to: `http://localhost:5000/admin`
3. Check each admin page:

| # | Admin Page | URL | What You Should See |
|---|---|---|---|
| 1 | Admin Hub | `/admin` | Links to all admin pages |
| 2 | Users | `/admin/users` | List of user accounts |
| 3 | Audit Log | `/admin/audit-log` | Table of recent actions |
| 4 | Agent | `/admin/agent` | Agent status dashboard |
| 5 | NetPractice | `/admin/netpractice` | NetPractice connection status |
| 6 | Sitemap | `/admin/sitemap` | List of all routes in the app |
| 7 | Care Gap Rules | `/admin/caregap-rules` | List of screening rules with edit forms |

---

## STEP 8 — Check Settings Pages

1. Go to: `http://localhost:5000/settings/account`
   - You should see your account settings (username, role, etc.)
2. Go to: `http://localhost:5000/settings/notifications`
   - You should see notification preferences

---

## STEP 9 — Stop the Server

1. Go back to the PowerShell window where the server is running
2. Press `Ctrl + C` to stop it
3. The server will shut down

---

## STEP 10 — Test the Restart Script

The restart script kills old servers, runs tests, and starts fresh.

1. In File Explorer, navigate to `C:\Users\coryd\Documents\NP_Companion`
2. Double-click `restart.bat`
3. A black command window will appear showing progress
4. **What you should see:**
   - Step 1: Killing Python processes — Done
   - Step 2: Port 5000 is free
   - Step 3: Python OK
   - Step 4: Running tests — ALL CHECKS PASSED
   - Step 5: Starting server
   - Chrome opens to the dashboard

If it opens Notepad with an error file instead, read the error message and note it.

---

## STEP 11 — Check New Features (F11 Lab Tracker + F12 Timer)

With the server running, check these specific features:

| # | Page | URL | What to Check |
|---|------|-----|---------------|
| 1 | Lab Tracker | `/labtrack` | Stats cards (0s are fine), add-tracking form, seed-panels button |
| 2 | Lab Patient Detail | `/labtrack/99999` | Patient detail page loads (empty is fine) |
| 3 | Timer Dashboard | `/timer` | Daily summary cards, E&M bar, sessions table with billing level dropdown |
| 4 | Timer CSV Export | `/timer/export` | Downloads a CSV file (may have 0 rows) |
| 5 | Room Widget | `/timer/room-widget` | **Opens without logging in** — large green button, provider name shown |

---

## STEP 12 — Check New Features (F13 Productivity Dashboard + F14 Billing Audit Log)

**Added:** CL14

| # | Page | URL | What to Check |
|---|------|-----|---------------|
| 1 | Metrics Dashboard | `/metrics` | Today at a Glance card, 7 Chart.js charts load (may be empty), date range picker works, Export PDF button |
| 2 | Chart Data API | `/metrics/api/chart-data?days=30` | Returns JSON with all chart datasets (labels, daily_counts, visit_type_breakdown, etc.) |
| 3 | Weekly Summary | `/metrics/weekly` | Weekly summary page loads with stats, top visit types, notable metric |
| 4 | Preview Weekly | `/metrics/preview-weekly` | Same as weekly but shows "(Preview)" label |
| 5 | Benchmark Toggle | `/metrics` | Check/uncheck "Participate in anonymized practice benchmarks" — saves preference |
| 6 | Burnout Warnings | `/metrics` | Red warning card only appears if 3-week worsening detected (may not show with test data) |
| 7 | Billing Log | `/billing/log` | Filter controls (date, level, anomaly status), sessions table, expandable detail rows |
| 8 | Billing Export | `/billing/log/export` | Print-friendly page with Print/Save PDF button |
| 9 | Add Rationale | `/billing/log` | Click Detail on any row, submit a rationale — appears in billing_notes |
| 10 | E&M Calculator | `/billing/em-calculator` | MDM method + Time-based method, result card with CPT code and wRVU |
| 11 | Monthly Report | `/billing/monthly-report` | Summary cards (patients, chart hrs, RVU, anomaly count), E&M distribution chart, weekly breakdown |

---

## STEP 13 — Check F14a/F14b/F14c Gap-Fill Features (CL15)

**Added:** CL15

| # | Page | URL | What to Check |
|---|------|-----|---------------|
| 1 | E&M Calculator (Both Methods) | `/billing/em-calculator` | Single form with BOTH MDM + time inputs. Click "Calculate (Higher of Two)." Result shows recommended level + comparison showing MDM result AND time-based result side-by-side. Winner is highlighted. |
| 2 | Inline E&M Widget | `/timer` | Click "Quick Calc" on the E&M Level Calculator card. Enter MDM complexity + total time. Click "Calculate." Result card shows recommended code + wRVU + method details. |
| 3 | Use This Level | `/timer` | After calculating in the inline widget, click "Use This Level" — the billing level dropdown on the most recent session should update and submit. (Requires at least one session in today's table.) |
| 4 | Upcode Suggestion | `/billing/log` | Find a session where chart time exceeds the minimum for the next-higher E&M level. It should show a yellow flag: "Consider higher level based on time." |
| 5 | Anomaly Side Panel | `/billing/log` | Click any yellow anomaly flag button. A slide-out panel should appear on the right with: the concern text AND "How to resolve" guidance specific to the anomaly type. Click outside or X to close. |
| 6 | New vs Established Split | `/billing/monthly-report` | "Patient Type Split" card shows New Patients (992xx) count and Established (992xx) count with a visual bar. |
| 7 | Prior Month Comparison | `/billing/monthly-report` | "Comparison to Prior Month" table shows Current vs Prior columns for patients, wRVU, chart hours, new patients, anomaly flags. Green/red delta coloring. |
| 8 | Monthly Email Config | N/A | **Requires SMTP setup** — Set `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` in `config.py`. Monthly billing report will auto-email on 1st of each month at 7AM. Same config needed for F13c weekly email. |

### Items Requiring Your Input Before Full Deployment
- **SMTP Configuration:** Both weekly summary email (F13c) and monthly billing email (F14c) need SMTP credentials in config.py
- **RVU Values:** The RVU lookup table in `routes/timer.py` uses approximate 2024 Medicare RBRVS values — verify against your payer schedule
- **E&M Time Thresholds:** The time ranges in `EM_TIME_RANGES` should be verified against your clinical documentation standards
- **Monthly Billing Email Opt-in:** Users are opted in by default (`monthly_billing_email` preference). Can be changed in user preferences.

---

## STEP 14 — Check F15 Care Gap Tracker Features (CL16)

**Added:** CL16

**Migration required:** Run `venv\Scripts\python.exe migrate_add_caregap_columns.py` before testing if upgrading from a prior version.

| # | Page | URL | What to Check |
|---|------|-----|---------------|
| 1 | Care Gap Overview | `/caregap` | Date navigation (yesterday/today/tomorrow), scheduled patients table with gap count badges, expandable inline gap detail rows |
| 2 | Care Gap Overview (expand) | `/caregap` | Click a patient row — should expand to show individual gaps with Address/Decline buttons. Addressing shows documentation snippet modal with Copy button |
| 3 | Patient Gaps | `/caregap/<mrn>` | Open gaps with Address Now / Decline / N/A buttons. Expandable address form with editable documentation snippet. Addressed gaps show Copy Doc + Reopen |
| 4 | Panel Report | `/caregap/panel` | Summary cards (total open gaps, unique patients, gap types). Coverage table sorted by worst coverage. Visual bars (green >80%, yellow 50-80%, red <50%). Age/sex filter form |
| 5 | Outreach List | `/caregap/panel` → click Outreach | Shows patients due for a specific screening. MRN shows last 4 only. CSV Export button downloads full list with names for MA use |
| 6 | Dashboard Gaps Column | `/dashboard` | "Gaps" column in schedule table. Patients with open gaps show count badge linking to `/caregap/<mrn>`. Others show "—" |
| 7 | Admin Rule Editor | `/admin/caregap-rules` | All 19 USPSTF rules listed as collapsible cards. Click to expand edit form: name, interval, billing code, active toggle, criteria JSON, doc template. Save button per rule |
| 8 | Reset Rules | `/admin/caregap-rules` | "Reset to Defaults" button with confirmation — deletes all rules and re-seeds from hardcoded defaults |

### Items Requiring Your Input Before Full Deployment
- **USPSTF Screening Criteria:** The 19 rules in `agent/caregap_engine.py` use standard USPSTF guidelines. Review age ranges, intervals, and risk factors against your clinical practice standards
- **Billing Code Pairs:** Verify billing codes (G0104, G0105, 77067, etc.) match your payer schedule
- **Documentation Templates:** Review and customize the auto-generated documentation snippets in each rule's `documentation_template` field to match your charting style
- **Rule Customization:** Use Admin → Care Gap Rules to deactivate rules you don't use, adjust intervals, or edit criteria

---

## STEP 15 — Verify AC Interface Reference v4 Integration (CL17)

**Added:** CL17

These steps verify that the AC interface reference v4 materials are properly integrated.

| # | Check | How to Verify |
|---|-------|---------------|
| 1 | Reference file exists | Open `Documents\ac_interface_reference\Amazing charts interface\..md files\ac_interface_reference_v4.md` — should be ~2788 lines |
| 2 | Screenshots folder | Open `Documents\ac_interface_reference\Amazing charts interface\screenshots\` — should contain 50+ .png files |
| 3 | Orders spreadsheet | Open `Documents\ac_interface_reference\Amazing charts interface\Order Sets\AC orders.xlsx` — should show Nursing, Labs, Imaging, Diagnostics tabs with ~870 total items |
| 4 | config.py process name | Open `config.py` — `AMAZING_CHARTS_PROCESS_NAME` should be updated to match v4 findings (window title: "Amazing Charts EHR (32 bit)") |
| 5 | AC version confirmed | AC version is 12.3.1 (build 297), Practice ID 2799. Verify these match when you open AC at work |
| 6 | DB access test (work PC only) | From work PC, try: `Test-Path "\\\\192.168.2.51\\Amazing Charts\\AmazingCharts.mdf"` in PowerShell. If True, direct DB access is possible |
| 7 | Imported items path test (work PC only) | From work PC, try: `Test-Path "\\\\192.168.2.51\\amazing charts\\ImportItems"` in PowerShell. If True, patient documents accessible via file share |

### Items Requiring Your Action After v4 Integration
- ~~**Update config.py:** Add new values~~ **DONE (CL18)** — `AC_VERSION`, `AC_WINDOW_TITLE_PREFIX`, `AC_STATES`, `ORDER_TABS`, and all system values added
- **Seed master orders:** Run `venv\Scripts\python.exe scripts/seed_master_orders.py` to populate master_orders from AC orders.xlsx (requires openpyxl)
- **Test DB access:** ACTION ITEM #41 — test SQL Server read access from work PC to determine if OCR can be supplemented with direct queries
- ~~**Verify inbox filters:** Confirm "Show Everything" is a 7th filter option~~ **DONE (CL18)** — added to `INBOX_FILTERS` in `inbox_reader.py`

---

## STEP 16 — Verify AC Interface v4 Code Retrofit (CL18)

**Added:** CL18

These steps verify that the v4 retrofit code changes are working correctly.

| # | Check | How to Verify |
|---|-------|---------------|
| 1 | config.py imports | Run: `venv\Scripts\python.exe -c "import config; print(config.AC_VERSION)"` — should print `12.3.1` |
| 2 | AC state detection | Run: `venv\Scripts\python.exe -c "from agent.ac_window import get_ac_state; print('OK')"` — should print `OK` |
| 3 | ORDER_TABS constant | Run: `venv\Scripts\python.exe -c "from models.orderset import ORDER_TABS; print(len(ORDER_TABS))"` — should print `8` |
| 4 | Inbox filters count | Run: `venv\Scripts\python.exe -c "from agent.inbox_reader import INBOX_FILTERS; print(len(INBOX_FILTERS))"` — should print `7` |
| 5 | Migration | Run: `venv\Scripts\python.exe migrate_add_master_order_cpt.py` — should add cpt_code column or say it already exists |
| 6 | Web tests pass | Run: `venv\Scripts\python.exe test.py` — should show 36 passed, 0 failed |
| 7 | Mock tests pass | Run: `venv\Scripts\python.exe tests/test_agent_mock.py` — should show 39+ passed, 0 failed (3 new v4 tests added) |

---

## STEP 17 — Verify Clinical Summary Import & Patient Chart (CL21–CL22)

**Added:** CL22

These steps verify the XML parser, folder watcher, dashboard drop zone, patient panel, and widget-based patient chart.

### Migration

Run the migration first (skip if already done):
```
venv\Scripts\python.exe migrate_add_chart_columns.py
```

### XML Parser Checks

| # | Check | How to Verify |
|---|-------|---------------|
| 1 | Parser import | `venv\Scripts\python.exe -c "from agent.clinical_summary_parser import parse_clinical_summary; print('OK')"` → `OK` |
| 2 | Parse a test file | `venv\Scripts\python.exe -c "from agent.clinical_summary_parser import parse_clinical_summary; p = parse_clinical_summary(r'Documents\xlm test patients\ClinicalSummary_PatientId_62815_20260317_142457.xml'); print(p['patient_name'], len(p['medications']), 'meds', len(p['diagnoses']), 'dx')"` → `TEST TEST 11 meds 15 dx` |
| 3 | Medication data correct | In the output above, medications should have real drug names (Ventolin, Wegovy, lisinopril…), NOT provider/practice addresses |
| 4 | Diagnoses have codes | Diagnoses should include ICD-10 or SNOMED codes like `[ICD10: U07.1]`, `[SNOMED-CT: 56018004]` |

### Dashboard Checks

| # | Check | How to Verify |
|---|-------|---------------|
| 5 | XML drop zone visible | Open `http://localhost:5000/dashboard` — after the schedule table, there should be a dashed-border "Drag & drop Clinical Summary XML files here" area |
| 6 | Drag-and-drop upload | Drag an XML file from `Documents\xlm test patients\` onto the drop zone. Status should show "Imported 1 of 1 file(s)" and refresh the page |
| 7 | Patient panel appears | After importing, a "My Patients" table should appear below the drop zone with the imported patient |
| 8 | Patient panel search | Type part of a patient name in the search box — table should filter in real time |
| 9 | Patient panel sort | Change the dropdown to Name/MRN/Recent — table rows should reorder |
| 10 | Click to open chart | Click a patient name or "Open" button in the panel — should navigate to `/patient/<mrn>` |

### Patient Chart Checks

| # | Check | How to Verify |
|---|-------|---------------|
| 11 | Chart loads | Go to `http://localhost:5000/patient/62815` after import — should show widget-based layout |
| 12 | Medications widget | Shows drug names, dosages, frequencies from XML. Active vs inactive count displayed |
| 13 | Diagnoses widget | Shows problems with ICD-10/SNOMED codes. Active vs resolved. Acute/chronic classification |
| 14 | Allergies widget | Shows substance names, reactions, severities |
| 15 | Immunizations widget | Shows vaccine names with dates |
| 16 | Vitals widget | Shows vital signs data per encounter date |

### Settings Check

| # | Check | How to Verify |
|---|-------|---------------|
| 17 | Export folder setting | Go to Settings → scroll to "Clinical Summary Import" → enter a folder path → Save. Confirm it persists on refresh |

---

## STEP 18 — Verify API Integration Foundation (CL23+)

**Added:** CL23

These steps verify the External API integration layer is working correctly. Run these after the API foundation code (Phase 0.3) is built.

### Prerequisites

Run migrations for API cache tables first:
```
venv\Scripts\python.exe migrate_add_api_cache_tables.py
```

### API Client & Cache Verification

| # | Check | How to Verify |
|---|-------|---------------|
| 1 | api_client import | `venv\Scripts\python.exe -c "from utils.api_client import get_cached_or_fetch; print('OK')"` → `OK` |
| 2 | RxNormCache exists | `venv\Scripts\python.exe -c "from models.patient import RxNormCache; print('OK')"` → `OK` |
| 3 | Icd10Cache exists | `venv\Scripts\python.exe -c "from models.patient import Icd10Cache; print('OK')"` → `OK` (already working) |
| 4 | RxNorm API call | `venv\Scripts\python.exe -c "import requests; r = requests.get('https://rxnav.nlm.nih.gov/REST/rxcui/203644/properties.json'); print(r.json()['properties']['name'])"` → should print `lisinopril` (or similar) |
| 5 | PatientMedication has rxnorm_cui | `venv\Scripts\python.exe -c "from models.patient import PatientMedication; print(hasattr(PatientMedication, 'rxnorm_cui'))"` → `True` |
| 6 | Parser saves RXCUI | Import a Clinical Summary XML with medications, then check database: medications should have `rxnorm_cui` populated from the XML's RxNorm CUI codes |
| 7 | Cache-first works | Call the same RxNorm lookup twice — second call should be instant (from SQLite cache) |

### Feature-Specific API Checks (Build as Features Complete)

| # | Check | When to Test | How to Verify |
|---|-------|-------------|---------------|
| 8 | OpenFDA Label fetch | When F10 med reference is built | Search for "lisinopril" in Medication Reference → should show FDA label data (indications, dosing, warnings) |
| 9 | ICD-10 autocomplete | When F17 coding suggester is built | Type "HTN" in coding suggester → should show I10, I11.9, etc. |
| 10 | LOINC reference ranges | When F11 gets LOINC column | Lab Tracker should show LOINC reference range next to custom thresholds |
| 11 | HealthFinder care gaps | When F15 HealthFinder integration is built | Care Gap Tracker should show age/sex-appropriate USPSTF recommendations matching HealthFinder API |
| 12 | Drug recall check | When NEW-A recall system is built | No active recalls should appear for most common medications ✅ |
| 13 | PubMed guidelines | When NEW-C guideline panel is built | Opening a patient chart with active diagnoses should show recent guideline articles in sidebar |
| 14 | Offline behavior | Disconnect internet, reload patient chart | Features should show cached data with staleness timestamps, or "not available" messages — no errors |

### API Admin Checks

| # | Check | How to Verify |
|---|-------|---------------|
| 15 | API settings page | Go to `/admin/api` (admin login required) — should show API key fields and cache management |
| 16 | Cache statistics | Admin API page should show entry count per cache table |
| 17 | Flush cache | Click "Flush Cache" for RxNorm → entry count should go to 0 → next lookup should hit live API |

---

## STEP 19 — Verify Billing Intelligence (Phase 10B)

**Added:** CL23

Test these after the Billing Intelligence Layer (Phase 10B) is built.

### Prerequisites

```
venv\Scripts\python.exe migrate_add_billing_tables.py
```

### Billing Engine Checks

| # | Check | How to Verify |
|---|-------|---------------|
| 1 | BillingOpportunity model | `venv\Scripts\python.exe -c "from models.billing import BillingOpportunity; print('OK')"` → `OK` |
| 2 | BillingRuleCache model | `venv\Scripts\python.exe -c "from models.billing import BillingRuleCache; print('OK')"` → `OK` |
| 3 | PFS data loaded | Admin billing page shows current-year PFS data for at least common E&M codes (99213, 99214, 99215) |
| 4 | CCM detection | Import a test patient with ≥2 chronic conditions → billing card shows "CCM: 99490 eligible" |
| 5 | AWV detection | Import a test patient with no AWV in last 12 months → billing card suggests appropriate AWV code |
| 6 | G2211 reminder | Established patient with chronic condition → "Consider G2211" reminder appears |
| 7 | Revenue estimates | Dollar amounts labeled "approximate" with payer caveats |
| 8 | Settings pages | `/settings/billing` and `/admin/billing` load without errors |
| 9 | Opportunity gap | Post-visit review shows captured vs. missed opportunities |

---

## Setup Items That Still Need Doing

These are things you'll need to set up before going live at the office. They are **not needed** for testing on this computer.

### Pushover Notifications (Optional — For Phone Alerts)
Pushover sends push notifications to your phone for critical inbox items and digest reports.

1. Go to https://pushover.net and create an account
2. Download the Pushover app on your phone
3. On the Pushover website, find your **User Key** (a long string of letters/numbers)
4. Create an **Application** in Pushover, name it "NP Companion"
5. Copy the **API Token** it gives you
6. Open `config.py` in the NP_Companion folder and fill in:
   ```python
   PUSHOVER_USER_KEY = "your-user-key-here"
   PUSHOVER_API_TOKEN = "your-api-token-here"
   ```

### Tailscale (For Remote Access From Phone)
Tailscale lets you access NP Companion from your phone when you're not at the office.

1. Install Tailscale on your work PC: https://tailscale.com/download
2. Install Tailscale on your phone
3. Sign in with the same account on both
4. Once connected, you can access NP Companion from your phone at:
   `http://[your-pc-tailscale-ip]:5000`
5. To find your PC's Tailscale IP, open Tailscale on the PC and look for the IP address (starts with `100.`)

### NetPractice Session Setup
NetPractice scraping requires a Chrome browser session.

1. This only works on the **work PC** where you use NetPractice
2. Start Chrome with this special command (create a shortcut):
   ```
   "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
   ```
3. Log into NetPractice in that Chrome window
4. The NP Companion agent will use that browser session to scrape schedules

### Before Going Live — Config Changes
When you move to the work PC and go live:

1. Open `config.py` and change:
   ```python
   DEBUG = False               # Was True
   AC_MOCK_MODE = False        # Was True — turns off screenshot testing
   SECRET_KEY = "new-random-string"  # Generate a new one
   ```
2. Run the restart script (`restart.bat`) to apply changes

### API Keys (Optional — For Higher Rate Limits)
These are all free but give you higher API rate limits and access to more data.

1. **OpenFDA API Key** — Register at https://open.fda.gov/apis/authentication/ for 240 requests/min (vs. 40 anonymous). Enter the key in Admin → API Settings.
2. **NCBI (PubMed) API Key** — Register at https://www.ncbi.nlm.nih.gov/account/ for 10 requests/sec (vs. 3). Enter in Admin → API Settings.
3. **UMLS API Key** — Register at https://uts.nlm.nih.gov/uts/ (requires a free UMLS Terminology Services account). Enter in Admin → API Settings.
4. **LOINC Account** — Register at https://loinc.org/get-started/ for FHIR API access. Enter credentials in Admin → API Settings.

None of these keys are required — all APIs work without them at lower rate limits. Register when you start hitting rate limits or when Phase 10 features are being used actively.

---

## Quick Reference — Useful Commands

All commands should be run from `C:\Users\coryd\Documents\NP_Companion` in PowerShell with `(venv)` active.

| What | Command |
|---|---|
| Activate virtual environment | `venv\Scripts\activate` |
| Run web app tests | `venv\Scripts\python.exe test.py` |
| Run agent mock tests | `venv\Scripts\python.exe tests/test_agent_mock.py` |
| Start the server | `venv\Scripts\python.exe app.py` |
| Restart everything | Double-click `restart.bat` |
| Check database tables | `venv\Scripts\python.exe -c "from app import create_app; app = create_app()"` |
| See all URL routes | `venv\Scripts\python.exe -c "from app import create_app; app = create_app(); [print(r) for r in app.url_map.iter_rules()]"` |

---

## What the Tests Check

### test.py (Web App — 36 checks)
- All 27 database tables exist
- User account "CORY" is active
- All 32 pages load without errors (dashboard, timer, inbox, oncall, orders, medref, labtrack, caregap, metrics, tools, patient chart, oncall new, settings, admin pages incl. gap rules, APIs)
- 404 page works
- Login redirect works for unauthenticated users

### tests/test_agent_mock.py (Agent — 26 checks)
- Mock provider loads and screenshot files exist (10 legacy images + 1 XML; 50+ new screenshots available in `ac_interface_reference/Amazing charts interface/screenshots/`)
- ac_window mock: fake window detection, MRN extraction, DOB extraction
- OCR on screenshots: Tesseract finds key words (inbox, patient, schedule, subject, from, received)
- Mock element detection: find_text_on_screen and find_and_click work against screenshots
- Clinical Summary XML parsing: extracts MRN 62815, 6 clinical sections
- MRN reader pipeline: full mock flow from window → MRN
- Window rect: mock returns valid rectangle

---

## If Something Goes Wrong

1. **Server won't start:** Make sure no other Python process is using port 5000. Run `restart.bat` which kills old processes first.
2. **Tests fail with "no such column":** Run the database migrations:
   - `venv\Scripts\python.exe migrate_phase2_columns.py`
   - `venv\Scripts\python.exe migrate_add_caregap_columns.py` (for care_gaps.patient_name etc.)
3. **OCR tests fail:** Install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki and make sure it's at `C:\Program Files\Tesseract-OCR\tesseract.exe`
4. **"ModuleNotFoundError":** The virtual environment might not be activated. Make sure you see `(venv)` in your PowerShell prompt. If not, run `venv\Scripts\activate`.
5. **Page shows error 500:** Stop the server, run `venv\Scripts\python.exe test.py` to identify which page fails, and note the error message.

---

## Part 2 — CL11 Feature Verification

**Added:** CL11

These steps verify the new features added in CL11. Complete Part 1 (Steps 1–10) first.

### STEP 11 — Run Database Migrations

CL11 adds new columns. Run these before testing new features.

1. In PowerShell with `(venv)` active:
   ```
   venv\Scripts\python.exe migrate_add_claim_columns.py
   venv\Scripts\python.exe migrate_add_forward_columns.py
   ```
2. Each should print "Migration complete" or "Columns already exist."

### STEP 12 — Verify Updated Test Counts

1. Run:
   ```
   venv\Scripts\python.exe test.py
   ```
2. **Expected:** 35 passed (was 32 — added Admin Config, Admin Tools, Patient Roster)

3. Run:
   ```
   venv\Scripts\python.exe tests/test_agent_mock.py
   ```
4. **Expected:** 30+ passed (was 26 — added seed data, store_parsed_summary tests)

### STEP 13 — Clickable Patient Names on Dashboard

1. Start the server and log in
2. Go to the Dashboard
3. **What you should see:** A test patient row at 07:00 (TEST, TEST)
4. Click the patient name — it should link to the patient chart page
5. **To disable the test row:** Go to Admin > Config Settings > Test Data section and set `TEST_PATIENT_APPOINTMENT_ENABLED` to False

### STEP 14 — My Patients (Patient Roster)

1. Click **My Patients** in the sidebar (between Dashboard and Timer)
2. **What you should see:** An empty roster with instructions
3. Go to a patient chart (click the test patient from Dashboard)
4. Click the **Claim Patient** button on the chart page
5. Go back to **My Patients** — the patient should now appear in your roster

### STEP 15 — On-Call Note Forwarding

1. Click **On-Call** in the sidebar
2. Create a new note (click **New Note**)
3. After creating the note, you should see a **Forward** dropdown next to the note
4. Select another user from the dropdown and click **Forward**
5. The note should show a forwarded badge ( → Provider Name)

### STEP 16 — Unified Settings Page

1. Go to Settings (gear icon in the sidebar)
2. **What you should see:** A single page with three sections:
   - **Profile & Security** — Display name, password, PIN
   - **Credentials** — NetPractice, Amazing Charts, Work PC password
   - **Notifications** — Pushover, quiet hours, inbox interval, notification types
3. Go to `http://localhost:5000/settings/notifications` — it should redirect to the unified page

### STEP 17 — Admin Config Pre-Live Warnings

1. Go to Admin > Config Settings
2. **What you should see:** A red warning banner at the top titled "⚠ Pre-Live Checklist"
3. The banner should list items like:
   - AC_MOCK_MODE is True
   - DEBUG is True
   - PUSHOVER keys are empty
   - TEST_PATIENT_APPOINTMENT_ENABLED is True

### STEP 18 — Admin Tools Page

1. Go to Admin Dashboard (`/admin`)
2. **What you should see:** A new card "Admin Tools" next to Config Settings
3. Click **Admin Tools**
4. **What you should see:** Buttons for "Seed Test Data" and "Clear Test Data"
5. Click **Seed Test Data** — should show a success flash message
6. Check that test patients appear:
   - Go to `http://localhost:5000/patient/10001` — should show SARAH JOHNSON
   - Go to `http://localhost:5000/patient/10002` — should show CARLOS MARTINEZ
   - Go to `http://localhost:5000/patient/10003` — should show PRIYA PATEL
7. Click **Clear Test Data** — should clear all test patients

### STEP 19 — Clinical Summary Integration Test

This tests the full clinical summary pipeline (parsing XML → storing in DB → viewing on chart).

1. In PowerShell with `(venv)` active:
   ```
   venv\Scripts\python.exe tools/clinical_summary_test.py
   ```
2. **What you should see:** All checks passed
3. **On the work PC with real XML files**, you can test with:
   ```
   venv\Scripts\python.exe tools/clinical_summary_test.py --xml path/to/exported.xml
   ```

---

## Updated Quick Reference

| What | Command |
|---|---|
| Run CL11 migrations | `venv\Scripts\python.exe migrate_add_claim_columns.py` then `venv\Scripts\python.exe migrate_add_forward_columns.py` |
| Seed test patients | `venv\Scripts\python.exe scripts/seed_test_data.py` |
| Run clinical summary test | `venv\Scripts\python.exe tools/clinical_summary_test.py` |

---

## Updated Test Counts

### test.py (Web App — 35 checks, was 32)
- All 26 database tables exist
- User account active
- All 31 pages load (added: Admin Config, Admin Tools, Patient Roster)
- 404 page works
- Login redirect works

### tests/test_agent_mock.py (Agent — 30+ checks, was 26)
- Original 8 test sections (mock provider, screenshots, ac_window, OCR, element detection, XML parsing, MRN pipeline, window rect)
- **NEW:** Test 9 — Seed test data, verify DB rows, test patient chart route, clear data
- **NEW:** Test 10 — store_parsed_summary completeness (all 5 patient tables)

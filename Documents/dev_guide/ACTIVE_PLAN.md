# CareCompanion — Final Pre-Beta Plan

> **Created:** 2026-03-22
> **Version:** v1.1.3
> **Predecessor:** `running_plan.md` (Phases 1–38, all complete — see Part 6 for tier inventory)
> **Scope:** Complete remaining audit items, build the deferred E2E test suite, harden infrastructure with deployment utility scripts, automate the production checklist, and close with a mandatory human-guided verification session before Tier-1 beta deployment.
> **Target:** Zero regressions · all `PRODUCTION_CHECKLIST.md` items verified · `deploy_check.py` PASS · `verify_all.py` GO
> **Style:** Same as `running_plan.md` — phase-numbered, checkbox sub-steps, completion blocks.

---

# UI System Review — Implementation Progress

> Ref: Full audit in session 03-23-26, approved plan in `UI_OVERHAUL.md`

## Phase M1 — CSS Foundation ✅ COMPLETE (03-23-26)

- [x] M1.1 — Add missing utility classes (`.sticky-top`)
- [x] M1.2 — Rename `.schedule-table` → `.data-table` in CSS (16 rules, deprecated alias kept)
- [x] M1.3 — Add table modifiers (`.data-table--striped`, `.data-table--compact`, sortable headers)
- [x] M1.4 — Add unified status system (`.status--critical/warning/success/info/muted`, row tints, dots)
- [x] M1.5 — Add `.page-header` + `.action-bar` primitives
- [x] M1.6 — Add `.cc-modal` unified modal system (sm/md/lg/xl sizes, header/body/footer, dark mode)
- [x] M1.7 — Migrate all 15 templates (29 occurrences) from `schedule-table` to `data-table`
- [x] M1.8 — Mark single-dash badge aliases as deprecated
- [x] Verification — 93/93 tests passing, 0 CSS errors

## Phase M2 — High-Frequency Template Cleanup ✅ COMPLETE (03-24-26)

- [x] M2.1 — Dashboard: `.data-table--striped`, modals→`.cc-modal`, inline cleanup (~100 styles removed)
- [x] M2.2 — Patient chart: spinners→`.loading-spinner`, badges→`.widget-count-badge`, modal→`.cc-modal` (~40 styles removed)
- [x] M2.3 — Inbox: stats→`.stat-grid/.stat-block/.stat-value/.stat-label`, tables→`.data-table`, header→`.page-header` (~30 styles removed)
- [x] M2.4 — Timer: stats→`.stat-grid--auto`, kv pairs→`.kv-label/.kv-value`, table→`.data-table--striped` (~25 styles removed)
- [x] M2.5 — Billing review: header→`.page-header`, table→striped, spinner→`.loading-spinner/.widget-loading` (~8 styles removed)
- [x] M2.6 — Patient roster: header→`.page-header`, MRN→`.mono`, table→`.data-table--striped` (~5 styles removed)
- [x] M2.7 — Care gaps: modal→`.cc-modal` system, header→`.page-header` (~12 styles removed)
- [x] M2.8 — On-call: 5 inline badge patterns→`.badge--error/success/muted/warning/info`, header→`.page-header` (~15 styles removed)
- [x] Verification — 93/93 tests passing after all changes

## Phase M3 — Secondary Template Cleanup ✅ COMPLETE (06-10-25)

- [x] Admin pages (15 templates) — page-header, data-table, tool card classes, modal migrations, expand rows, section headings
- [x] Billing pages (5 templates + 1 table fix) — page-header, form-inline, data-table
- [x] Clinical tools (7 templates + 3 modal migrations) — page-header, cc-modal
- [x] Settings, auth, reference pages (4 templates) — page-header, section-heading

## Phase M4 — JS Enhancements

- [ ] `initSortableHeaders()` — client-side table column sorting
- [ ] `initStatePersistence()` — filter/scroll/tab session memory
- [ ] `initCollapsible()` — unified collapse/expand with localStorage
- [ ] `initQuickActions()` — inline status toggle buttons
- [ ] `_pagination.html` — reusable Jinja pagination macro

---

# AC Automation Upgrade — UIA + Win32 Messages

> Ref: Plan created 03-24-26. Replaces fragile OCR/pyautogui with UIA element discovery + Win32 message injection.

## Phase UIA-1 — Infrastructure ✅ COMPLETE (03-24-26)

- [x] Install pywinauto==0.6.8 + add to requirements.txt
- [x] Create `agent/uia_probe.py` — diagnostic tree dump script
- [x] Create `agent/uia_helpers.py` — UIA element finding layer
- [x] Create `agent/win32_actions.py` — Win32 message action layer
- [x] Create `agent/ac_interact.py` — smart 3-tier interaction (UIA → OCR → coordinates)
- [x] Add config flags: `AC_USE_UIA`, `AC_INTERACTION_TIER`, `AC_UIA_TIMEOUT`
- [x] Update agent-boundary.instructions.md with UIA rules + new allowed imports

## Phase UIA-2 — Feasibility Probe (BLOCKING GATE)

- [ ] Run `uia_probe.py` with AC at home screen — assess tree richness
- [ ] Run `uia_probe.py` with AC at chart open — check patient data controls
- [ ] Run `uia_probe.py` with AC at inbox — check inbox table controls
- [ ] Document findings: which AC states have rich UIA trees vs. sparse
- [ ] Decision gate: proceed with migration or stay OCR-first

## Phase UIA-3 — Migrate Existing Automation

- [ ] Replace `find_and_click()` calls in `pyautogui_runner.py` → `smart_find_and_click()`
- [ ] Replace inbox OCR table parsing in `inbox_reader.py` with UIA tree read (if controls available)
- [ ] Replace chart navigation in `clinical_summary_parser.py` → `smart_navigate_menu()`
- [ ] Update MRN reader to try UIA title bar read before OCR crop
- [ ] Verify all agent scheduler jobs still work with UIA-first path

---

# Step 0 — Project Rename: CareCompanion → CareCompanion (Manual Steps)

> **Status:** REQUIRED BEFORE BETA
> **Why:** "NP" implies Nurse Practitioner only. PAs, MDs, DOs, MAs, RNs, and unlicensed clinical staff will use this product. "CareCompanion" is credential-neutral.

### Manual steps you must complete yourself:

#### 0.1 — Rename GitHub Repository
1. Go to **github.com → your repo → Settings → General**
2. Under **Repository name**, change `CareCompanion` → `CareCompanion`
3. Click **Rename**
4. GitHub auto-redirects the old URL, but update any bookmarks/links

#### 0.2 — Rename Local Workspace Folder
1. Close VS Code completely
2. Rename `C:\Users\coryd\Documents\CareCompanion` → `C:\Users\coryd\Documents\CareCompanion`
3. Reopen VS Code from the new folder

#### 0.3 — Update Git Remote (if redirect stops working)
```bash
cd C:\Users\coryd\Documents\CareCompanion
git remote set-url origin https://github.com/<your-username>/CareCompanion.git
```

#### 0.4 — Update Windows Task Scheduler
1. Open **Task Scheduler** → find the CareCompanion agent task
2. Update the **Command** and **Working Directory** paths to use `CareCompanion`
3. Or re-import the updated `agent_startup.xml` (already updated in codebase)

#### 0.5 — Rename Database File
1. Navigate to `data/` folder
2. Rename `carecompanion.db` → `carecompanion.db`
3. Rename any backups `carecompanion_*.db` → `carecompanion_*.db` (optional)

#### 0.6 — Rename Icon File (if present)
1. Rename `CareCompanion.ico` → `CareCompanion.ico` in project root

#### 0.7 — Update VS Code Workspace File
1. Open `CareCompanion.code-workspace` (moved to project root)
2. Update any internal folder paths

#### 0.8 — Verify
1. Run `python test.py` — expect 127/127
2. Run `python -m pytest tests/ -q` — expect 93/93
3. Run `python tests/test_infrastructure.py` — expect 10/10
4. Launch the app: `python app.py` — confirm UI says "CareCompanion"

> **Step 0 complete when:** GitHub repo renamed, local folder renamed, git remote updated, database renamed, all tests pass.

---

# Part 0 — running_plan.md Carryover (Items Still Missing from Project)

> **Source:** Full project audit against `running_plan.md` Phases 1Ã¢â‚¬â€œ38 (2026-03-21).
> **Scope:** 99+ deliverables checked (40 test files, 8 models, 6 route files, 15 services, 5 billing engine modules, 19 templates, 18 migrations, 2 static assets). Only the items below are missing.

---

## Phase 0 Ã¢â‚¬â€ running_plan.md Remnants

**Goal:** Complete the 2 items explicitly listed as Phase 23 deliverables in `running_plan.md` that were never built. Both are optional/gated Ã¢â‚¬â€ the monitoring waterfall already skips step 5 gracefully Ã¢â‚¬â€ but they were promised as deliverables and should exist for completeness.

**What exists:**
- `MonitoringRuleEngine` (waterfall step 5) has a placeholder comment: `# Step 5: UpToDate/DynaMed Ã¢â‚¬â€ skip silently if no key / (placeholder for future premium API integration)`
- No `app/services/api/uptodate.py` file exists
- `config.example.py` and `config.py` have no `UPTODATE_API_KEY` or `DYNAMED_API_KEY` entries
- Test 22 in `tests/test_preventive_monitoring.py` ("UpToDate/DynaMed query skipped silently when no API key configured") passes because the engine's skip-path works, but the service class it would invoke does not exist

**Implementation:**

- [x] **0.1** Create `app/services/api/uptodate.py` Ã¢â‚¬â€ optional UpToDate/DynaMed API client:
  - Extends `BaseAPIClient` (pattern from `nadac_service.py`, `dailymed.py`)
  - `api_name="uptodate"`, gated on `config.UPTODATE_API_KEY` or `config.DYNAMED_API_KEY`
  - Method: `get_monitoring_recommendations(drug_name)` Ã¢â€ â€™ returns list of `{lab_loinc_code, lab_name, interval_days, priority, clinical_context}` dicts
  - If no API key configured: `__init__` sets `self.enabled = False`; all public methods return `[]` immediately
  - If key is present: query UpToDate or DynaMed content API for drug monitoring recommendations
  - Results cached in `MonitoringRule` with `source=UPTODATE`
  - Never raises Ã¢â‚¬â€ returns empty list on any error

- [x] **0.2** Add config entries to `config.example.py`:
  - Add to the API Keys section (commented out by default):
    ```python
    # UPTODATE_API_KEY = ''      # Optional: UpToDate Content API key (premium, license required)
    # DYNAMED_API_KEY = ''       # Optional: DynaMed API key (premium, license required)
    ```

- [x] **0.3** Wire `UpToDateService` into `MonitoringRuleEngine` waterfall step 5:
  - Replace the placeholder comment with actual import + conditional call:
    ```python
    # Step 5: UpToDate/DynaMed enrichment (optional)
    if not rules:
        try:
            from app.services.api.uptodate import UpToDateService
            utd = UpToDateService(self.db)
            if utd.enabled:
                utd_rules = utd.get_monitoring_recommendations(drug_name or rxcui)
                if utd_rules:
                    rules = self._store_rules(utd_rules, source='UPTODATE')
        except Exception:
            pass  # Optional enrichment Ã¢â‚¬â€ never blocks waterfall
    ```

- [x] **0.4** Verify test 22 in `test_preventive_monitoring.py` still passes (already tests the skip-path; with the new service file, the import will succeed but `enabled=False` without a key Ã¢â€ â€™ same behavior)

> **Phase 0 complete when:** `app/services/api/uptodate.py` exists, config entries added, waterfall step 5 wired, test 22 still passes. No new tests needed Ã¢â‚¬â€ existing test 22 covers both paths.

---

## Prerequisites

Before beginning this plan, confirm all of the following:

- [ ] All 38 phases of `running_plan.md` are complete (Part 6 completion summary: Ã¢Å“â€¦)
- [ ] Phase 0 above resolved (running_plan.md remnants)
- [ ] Current test count: ~747 tests, 0 failures
- [ ] Running on v1.1.3 with all migrations applied
- [ ] `python test.py` passes 36 checks, 0 failures
- [ ] **Phases 1Ã¢â‚¬â€œ6 do NOT require work-PC access** Ã¢â‚¬â€ all buildable remotely
- [ ] **Phase 7 (verification session) REQUIRES work-PC access** Ã¢â‚¬â€ executed on FPA-D-NP-DENTON

---

# Part 1 Ã¢â‚¬â€ Remaining Audit Items (Phases 1Ã¢â‚¬â€œ2)

---

## Phase 1 Ã¢â‚¬â€ USPSTF Care Gap UI Enhancements (K2)

**Goal:** Add a patient-ready print handout and a "Personalized / All" display toggle to the care gap pages. Both items identified in `AUDIT_REPAIR_REPORT.md` v1.1.2 as Medium priority. These are the last unresolved items from the audit before production.

**Current state:**
- `/caregap/<mrn>` Ã¢â‚¬â€ per-patient gap list with Address/Decline buttons; no clean print format
- All USPSTF rules display regardless of whether the patient has a specific triggering condition Ã¢â‚¬â€ no filter toggle
- Print button exists but outputs the full page HTML with navigation, not a patient handout

**What exists:**
- `routes/caregap.py` Ã¢â‚¬â€ all caregap routes including patient detail and panel
- `templates/caregap_patient.html` (or named equivalent) Ã¢â‚¬â€ per-patient gap display
- `agent/caregap_engine.py` Ã¢â‚¬â€ 19 USPSTF rules with `criteria` dicts (age, sex, diagnoses, risk factors)
- `CareGap` model Ã¢â‚¬â€ stores gap records including `gap_type`, `rule_name`, `status`, `criteria_met`

**Implementation:**

- [x] **1.1** Add `print_handout()` route to `routes/caregap.py`:
  - `GET /caregap/<mrn>/print` Ã¢â‚¬â€ renders a clean printer-optimized HTML page
  - Context: patient first name only (no MRN on printed page), visit date, list of due/overdue gaps in plain English
  - No navigation bar, no action buttons, no clinical status badges Ã¢â‚¬â€ pure patient handout
  - Template: `templates/caregap_print_handout.html`

- [x] **1.2** Create `templates/caregap_print_handout.html`:
  - Clean white layout, 12pt minimum font throughout
  - CSS: `@media print { @page { margin: 0.75in; } nav, .no-print, .widget-header { display: none; } }`
  - **Header block:** "Health Screening Summary" title Ã‚Â· Provider name from `current_user.full_name` Ã‚Â· Today's date
  - **Body:** One row per due/overdue gap:
    - Plain-English name (e.g., "Colorectal cancer screening" Ã¢â‚¬â€ not ICD-10 or clinical shorthand)
    - Status badge: **Due** (yellow) Ã‚Â· **Overdue** (red) Ã‚Â· **Up to Date** (green)
    - Frequency note (e.g., "Every 10 years Ã‚Â· Ages 45Ã¢â‚¬â€œ75")
    - Brief why: "Recommended by the U.S. Preventive Services Task Force (Grade A)"
  - **Footer:** "Questions about these recommendations? Talk with your provider." Ã‚Â· Date printed
  - Auto-trigger `window.print()` on page load with `onload="window.print()"` on body tag (can be disabled)
  - "Ã°Å¸â€“Â¨Ã¯Â¸Â Print Now" button for manual trigger

- [x] **1.3** Add "Print Patient Handout" button to per-patient care gap template:
  - Placed in the page header controls area next to the existing action buttons
  - Opens `/caregap/<mrn>/print` in a new tab: `target="_blank"`
  - Style: secondary outline button with printer icon

- [x] **1.4** Add "Personalized / All Applicable" toggle to per-patient care gap template:
  - Toggle control: two pill-shaped buttons Ã¢â‚¬â€ **"Personalized"** (default) Ã‚Â· **"All Applicable"**
  - **Personalized mode:** Shows only gaps where the `criteria_met` field confirms the patient has the specific triggering condition (e.g., tobacco use Ã¢â€ â€™ lung CA screening; diabetes Ã¢â€ â€™ HbA1c monitoring gap)
  - **All Applicable mode:** Shows all USPSTF-recommended screenings for this patient's age and sex, even if no specific trigger diagnosis is recorded
  - JS filter Ã¢â‚¬â€ no server round-trip needed; toggle hides/shows rows using `data-trigger-type` attribute
  - Preference saved to `localStorage['caregap_view_mode_mrn']` so it persists per patient across page loads
  - Default is "Personalized" Ã¢â‚¬â€ only show what the chart actually supports

- [x] **1.5** Add `data-trigger-type` attributes to gap rows rendered by `routes/caregap.py`:
  - In the gap list context, for each `CareGap` entry add: `trigger_type`
  - Value `"risk_factor"` Ã¢â‚¬â€ gap triggered by a specific diagnosis, medication, or result in the patient's chart
  - Value `"demographic"` Ã¢â‚¬â€ gap triggered by age and/or sex alone (no specific condition needed)
  - In the template: `<tr data-trigger-type="{{ gap.trigger_type or 'demographic' }}">`
  - Derive from `CareGapRule.criteria`: rules with specific ICD-10 patterns in criteria Ã¢â€ â€™ `"risk_factor"`, age/sex-only rules Ã¢â€ â€™ `"demographic"`

- [x] **1.6** Add 10 tests to `tests/test_caregap_ui.py`:
  1. `GET /caregap/<mrn>/print` returns 200
  2. Print template contains `@media print` CSS block
  3. Print template does NOT contain the main navigation (`<nav` or `sidebar`)
  4. Print template contains plain-English gap names (not ICD-10 codes as primary labels)
  5. Print template contains footer text
  6. Print button link present on per-patient page: `href` includes `/print`
  7. Toggle HTML elements (Personalized/All buttons) present in per-patient template
  8. `data-trigger-type` attribute set on gap rows in rendered template
  9. "Demographic" type gaps present for age-eligible Medicare patient
  10. "Risk factor" type gap present for patient with tobacco diagnosis

> **Phase 1 complete when:** `python -m pytest tests/test_caregap_ui.py -v` Ã¢â‚¬â€ 10/10 pass. Manual check: navigate to `/caregap/DEMO001/print` Ã¢â‚¬â€ clean handout renders with no nav chrome.

---

## Phase 2 Ã¢â‚¬â€ Audit Fix: WebPractice Placeholder & Minor UX (A4 + B1)

**Goal:** Fix the two remaining low-priority audit items from `AUDIT_REPAIR_REPORT.md` v1.1.2. Small targeted changes Ã¢â‚¬â€ both fit in a single phase.

**Current state:**
- A4 (WebPractice provider name): Provider name field in the WebPractice setup wizard has weak/no placeholder text Ã¢â‚¬â€ easy to enter wrong format
- B1 (right-click native feel): `Shift+F10` may be suppressed by existing keyboard shortcut handlers

**What exists:**
- WebPractice setup wizard at `/admin/netpractice` Ã¢â‚¬â€ template and route in `routes/admin.py` and nearby templates
- Keyboard shortcut handler in `static/js/main.js` (or wherever global keyboard listeners live)

**Implementation:**

- [x] **2.1** Improve provider name placeholder in WebPractice setup:
  - Open the admin NetPractice setup template (likely `templates/netpractice_setup.html` or the admin NetPractice config section)
  - Find the provider name input field
  - Change placeholder to: `"e.g., DENTON CORY (12)"`
  - Add `<small class="form-help">Enter your name exactly as it appears in the NetPractice provider list. Include the provider number in parentheses.</small>` below the input
  - No route changes needed Ã¢â‚¬â€ purely a template update

- [x] **2.2** Audit keyboard shortcut handlers for `F10` suppression:
  - Open `static/js/main.js` (and any other JS files with `addEventListener('keydown', ...)`)
  - Search for `e.preventDefault()` calls inside keyboard handlers
  - Confirm that `F10` and `Shift+F10` are NOT in the prevented set
  - If they are accidentally suppressed, add a guard: `if (e.key === 'F10') return;` before the prevent block
  - `Shift+F10` is the standard keyboard shortcut to open the context menu in Windows Ã¢â‚¬â€ CareCompanion's custom right-click menu should respond to it naturally via the browser

- [x] **2.3** Add 5 tests to `tests/test_misc_audit_fixes.py`:
  1. NetPractice admin page loads: `GET /admin/netpractice` returns 200
  2. Provider name input has `placeholder` attribute with expected hint text
  3. Provider name `<small>` help text is present in the template
  4. Version label visible in user popover in `templates/base.html` Ã¢â‚¬â€ `{{ config.VERSION }}` or equivalent rendered
  5. Keyboard shortcut JS file is importable/parseable (no syntax errors in main.js) Ã¢â‚¬â€ checked via file read + basic regex

> **Phase 2 complete when:** `python -m pytest tests/test_misc_audit_fixes.py -v` Ã¢â‚¬â€ 5/5 pass. Manual check: open NetPractice admin page Ã¢â‚¬â€ placeholder text visible.

---

# Part 2 Ã¢â‚¬â€ E2E Integration Test Suite (Phase 3)

---

## Phase 3 Ã¢â‚¬â€ Comprehensive End-to-End Test Suite

**Goal:** Build the 5 end-to-end integration test files explicitly listed in `running_plan.md` Part 6 Tier 5 as deferred. These tests exercise full data pipelines Ã¢â‚¬â€ XML parse Ã¢â€ â€™ store Ã¢â€ â€™ pre-visit job Ã¢â€ â€™ billing engine Ã¢â€ â€™ UI routes Ã¢â‚¬â€ using real SQLite in-memory or temp-file databases with fixture data. No external mocking of business logic.

**Current state:**
- ~747 tests, all unit/integration, no full pipeline E2E tests
- `tests/test_phase15_data_pipeline.py` covers XML Ã¢â€ â€™ store Ã¢â€ â€™ billing cycle (20 tests) but is not a full E2E
- No test exercises the full morning briefing assembly
- No test exercises the billing engine across multiple payer types simultaneously
- No test exercises the full calculator Ã¢â€ â€™ care gap Ã¢â€ â€™ billing opportunity chain

**What exists:**
- `app.create_app(testing=True)` test client pattern established across all prior test files
- Demo patient fixtures in `migrations/migrate_seed_demo_data.py` (DEMO001Ã¢â‚¬â€œDEMO005 with full clinical data)
- All 26 billing detectors, scoring engine, bonus tracker, TCM/CCM workflows, monitoring engine, immunization engine, calculator engine, and communication logger Ã¢â‚¬â€ all complete

**Implementation:**

- [x] **3.1** `tests/test_e2e_billing_pipeline.py` Ã¢â‚¬â€ 25 tests:
  1. Demo patient DEMO001 (Medicare 68F, HTN+DM+CKD): engine evaluate Ã¢â€ â€™ at least CCM + G2211 + AWV in opportunities
  2. Demo patient DEMO002 (Medicare 72M, post-discharge): TCM watch entry exists with deadline status
  3. Medicare patient profile Ã¢â€ â€™ all G-codes used (G0438, G0444 not CPT equivalents)
  4. Commercial patient profile Ã¢â€ â€™ CPT codes used + modifier 33 on preventive
  5. Opportunity capture call Ã¢â€ â€™ `ClosedLoopStatus` record created at stage "accepted"
  6. Opportunity dismiss call Ã¢â€ â€™ `OpportunitySuppression` record created
  7. `job_previsit_billing()` mock run Ã¢â€ â€™ creates Ã¢â€°Â¥3 `BillingOpportunity` records for DEMO001
  8. BonusTracker fixture present Ã¢â€ â€™ captured opportunity populates `bonus_impact_dollars` > 0
  9. Stack builder: AWV stack built for 68F Medicare Ã¢â€ â€™ stack contains Ã¢â€°Â¥4 codes including G0438
  10. Staff routing: accepted G0447 opportunity Ã¢â€ â€™ routed to MA role
  11. Cost-share note: Medicare AWV opportunity Ã¢â€ â€™ `cost_share_note` contains "no copay"
  12. Why-not page: `GET /billing/why-not/DEMO001` returns 200 with suppression records
  13. Closed-loop transition: accepted Ã¢â€ â€™ documented state via transition API
  14. Campaign launch: POST `/api/campaigns` with AWV Push type Ã¢â€ â€™ `BillingCampaign` record created
  15. Revenue report: `GET /reports/revenue/2026/3` returns 200 with `detected_revenue` key Ã¢â€°Â¥ 0
  16. Documentation phrase: at least one `DocumentationPhrase` exists for G2211
  17. REMS entry: clozapine REMS entry for DEMO001 has `escalation_level` in {0,1,2,3}
  18. Monitoring calendar: `GET /monitoring/calendar` returns 200 with entries in context
  19. Immunization gap: DEMO001 incomplete Shingrix series Ã¢â€ â€™ appears in `imm_gaps` list
  20. Admin billing ROI: `GET /admin/billing-roi` returns 200 (admin user)
  21. E/M calculator: POST to e/m endpoint with 45min time-based Ã¢â€ â€™ returns 99214
  22. Monthly report: `GET /billing/monthly-report` returns 200 with summary section keys
  23. Health check: `GET /api/health` returns JSON with `status: "ok"`
  24. Expected net value sort: `GET /patient/DEMO001` context Ã¢â€ â€™ auto_scores and billing both populated
  25. End-to-end capture rate: fire evaluate on all 5 demo patients Ã¢â€ â€™ total detected opportunities Ã¢â€°Â¥ 20

- [x] **3.2** `tests/test_e2e_calculator_pipeline.py` Ã¢â‚¬â€ 15 tests:
  1. BMI computed from DEMO001 vitals fixture Ã¢â€ â€™ returns numeric value and label
  2. LDL Friedewald computed from DEMO001 lab fixture Ã¢â€ â€™ correct formula selected (TG < 400)
  3. PREVENT computed for male fixture (age 55, SBP 138, TC 212, HDL 42, DM, nonsmoker) Ã¢â€ â€™ 10yr risk > 8%
  4. PREVENT computed for female fixture Ã¢â€ â€™ result differs from male (sex-specific coefficients)
  5. GAD-7 full questionnaire: POST all 7 responses Ã¢â€ â€™ score computed correctly
  6. Wells DVT: all 10 criteria positive Ã¢â€ â€™ score Ã¢â€°Â¥ 2 (high probability)
  7. Score persisted to `CalculatorResult` after compute
  8. `is_current` flag: recompute BMI Ã¢â€ â€™ prior result marked `is_current=False`, new result `True`
  9. Threshold alert: BMI Ã¢â€°Â¥ 40 Ã¢â€ â€™ `check_threshold_alerts()` returns obesity class III alert
  10. Threshold alert: LDL Ã¢â€°Â¥ 190 Ã¢â€ â€™ Dutch FH suggestion in alerts
  11. Threshold alert: PREVENT Ã¢â€°Â¥ 20% Ã¢â€ â€™ high-risk alert in response
  12. Pack years Ã¢â€°Â¥ 20 + age 52 Ã¢â€ â€™ LDCT lung CA screening eligibility alert
  13. Calculator billing detector: DEMO patient with BMI Ã¢â€°Â¥ 30 Ã¢â€ â€™ `G0447` billing opportunity surfaced
  14. Pre-fill: `get_prefilled_inputs("stop_bang", "DEMO001")` returns age, sex, BMI from chart
  15. Score history: 3 successive BMI computations Ã¢â€ â€™ `GET /patient/DEMO001/score-history/bmi` returns 3 items

- [x] **3.3** `tests/test_morning_briefing_integration.py` Ã¢â‚¬â€ 15 tests:
  1. `GET /briefing` returns 200 with all section keys in context
  2. TCM watch entry with deadline today Ã¢â€ â€™ context contains TCM alert with red priority
  3. CCM patient with 18/20 minutes this month Ã¢â€ â€™ appears in briefing CCM section
  4. Overdue A1C in `MonitoringSchedule` Ã¢â€ â€™ appears in `monitoring_due` section
  5. Critical REMS entry (escalation_level=3) Ã¢â€ â€™ surfaces in briefing as critical red alert
  6. Risk score alerts: PREVENT Ã¢â€°Â¥ 20% demo patient Ã¢â€ â€™ `prevent_high` count > 0 in context
  7. BMI Ã¢â€°Â¥ 40 demo patient Ã¢â€ â€™ `bmi_obese3` count > 0 in context
  8. BonusTracker with deficit Ã¢â€ â€™ bonus projection card in context
  9. Incomplete Shingrix Ã¢â€ â€™ `imm_gaps` section present in context
  10. PDMP overdue patient Ã¢â€ â€™ `pdmp_overdue` list in context (if ControlledSubstance entries exist)
  11. Education draft from new-med trigger Ã¢â€ â€™ `education_draft_count` > 0 in context
  12. No PHI in any briefing count field Ã¢â‚¬â€ count-only fields confirmed via template review
  13. `detect_new_medications()` returns new meds correctly when prior snapshot differs
  14. `job_previsit_billing()` runs without exception when all fixtures present
  15. Briefing template renders risk score alerts card only when at least one alert exists

- [x] **3.4** `tests/test_billing_multi_patient.py` Ã¢â‚¬â€ 15 tests:
  1. DEMO001 (Medicare): opportunities include G0438 or G0439
  2. DEMO003 (Commercial 44F, BMI 34): G0447 obesity counseling opportunity present
  3. DEMO004 (Medicaid 28F, pregnant): GDM or bacteriuria opportunity surfaced
  4. DEMO005 (Self-pay 55M, HTN): standard E/M opportunity present; CCM opportunity suppressed for self-pay
  5. Multi-patient expected-net-value: all 5 patients have `expected_net_dollars` > 0 after evaluate
  6. Campaign "AWV Push" filter: applies to Medicare patients (DEMO001, DEMO002) Ã¢â‚¬â€ not commercial
  7. Staff routing: MA gets PHQ-9 / GAD-7 screening prep task for BH-diagnosed patient (DEMO003)
  8. Cumulative bonus impact: sum of `bonus_impact_dollars` across all 5 demo patients > 0
  9. Why-not across all 5 demo patients: at least 10 suppression records created
  10. Diagnosis family rollup: `GET /reports/dx-families` returns 200 with at least 4 family groups
  11. Monitoring schedules: 5 demo patients produce Ã¢â€°Â¥ 20 active `MonitoringSchedule` entries after populate
  12. ICD-10 specificity: DEMO patient with E11.9 Ã¢â€ â€™ specificity recommendation returned by engine
  13. Revenue report with demo data: `GET /reports/revenue/2026/3` Ã¢â€ â€™ `detected_revenue` context populated
  14. Sort order: billing opportunities in `GET /patient/DEMO001` sorted by `expected_net_dollars` descending
  15. DX family report: HTN family shows I10 encounter count from demo data

- [x] **3.5** Extend `tests/test_phase15_data_pipeline.py` Ã¢â‚¬â€ 5 additional tests:
  1. XML parse Ã¢â€ â€™ `PatientLabResult` records created with LOINC codes populated
  2. XML parse Ã¢â€ â€™ `PatientSocialHistory` record created with `tobacco_status` field set
  3. `store_parsed_summary()` Ã¢â€ â€™ `detect_new_medications()` returns the newly added medication
  4. `store_parsed_summary()` Ã¢â€ â€™ `MonitoringRuleEngine.populate_patient_schedule()` called (at least 1 schedule entry created for patient with diabetes diagnosis)
  5. Full pipeline: XML file Ã¢â€ â€™ parse Ã¢â€ â€™ store Ã¢â€ â€™ `job_previsit_billing()` mock Ã¢â€ â€™ engine evaluate Ã¢â€ â€™ Ã¢â€°Â¥ 3 billing opportunities returned

**Test file summary:**

| File | New Tests | Goal |
|------|-----------|------|
| `test_e2e_billing_pipeline.py` | 25 | Full billing lifecycle end-to-end |
| `test_e2e_calculator_pipeline.py` | 15 | Calculator compute Ã¢â€ â€™ threshold Ã¢â€ â€™ billing |
| `test_morning_briefing_integration.py` | 15 | Full briefing assembly with all sections |
| `test_billing_multi_patient.py` | 15 | Multi-payer billing engine correctness |
| `test_phase15_data_pipeline.py` (extended) | +5 | XMLÃ¢â€ â€™storeÃ¢â€ â€™jobÃ¢â€ â€™engine chain |
| **Total** | **75** | Ã¢â‚¬â€ |

**Cumulative test count target:** ~822+ tests (747 + 75), 0 failures.

> **Phase 3 complete when:** `python -m pytest tests/test_e2e_billing_pipeline.py tests/test_e2e_calculator_pipeline.py tests/test_morning_briefing_integration.py tests/test_billing_multi_patient.py -v` Ã¢â‚¬â€ 70/70 pass. Extended data pipeline tests pass: `python -m pytest tests/test_phase15_data_pipeline.py -v` Ã¢â‚¬â€ all pass.

---

# Part 3 Ã¢â‚¬â€ Infrastructure Hardening (Phases 4Ã¢â‚¬â€œ5)

---

## Phase 4 Ã¢â‚¬â€ `deploy_check.py` Automated Pre-Flight Checker

**Goal:** Build a standalone Python script that verifies every automatable item from `Documents/PRODUCTION_CHECKLIST.md` Ã¢â‚¬â€ config flags, database health, migration completeness, API key presence, agent job registry, log directories, and the test suite. Produces a structured PASS/FAIL JSON report and color-coded console output. This script is the automated backbone of the Phase 6 verification session.

**Why this phase:** `PRODUCTION_CHECKLIST.md` has 11 sections and ~55 individual items. Manual checking is error-prone and time-consuming. This script runs in < 10 seconds on any machine and catches config mistakes before real patient data is ever touched. It also serves as the Stage 1 automated check in `verify_all.py` (Phase 6).

**What will be built:**
- `tools/deploy_check.py` Ã¢â‚¬â€ standalone script (no Flask server required for most checks; uses test client for health endpoint)
- `tools/deploy_report.json` Ã¢â‚¬â€ structured JSON output, updated on each run

**Implementation:**

- [x] **4.1** Section 1 Ã¢â‚¬â€ Environment & Security checks:
  ```python
  check("debug_false"):        config.DEBUG == False
  check("mock_mode_false"):    config.AC_MOCK_MODE == False
  check("secret_key_random"):  len(config.SECRET_KEY) >= 32 and config.SECRET_KEY not in KNOWN_DEV_DEFAULTS
  check("config_in_gitignore"): "config.py" in open(".gitignore").read()
  ```
  Where `KNOWN_DEV_DEFAULTS` is a list of known development placeholder keys (e.g., `"dev-secret-key"`, `"change-me"`, `"your-secret"`, etc.)

- [x] **4.2** Section 2 Ã¢â‚¬â€ Machine & Display checks:
  ```python
  check("tesseract_installed"):   os.path.exists(config.TESSERACT_PATH)
  check("ac_exe_reachable"):      os.path.exists(config.AC_EXE_PATH) if not config.AC_MOCK_MODE else "skipped"
  check("data_dir_exists"):       os.path.isdir("data/")
  check("logs_dir_exists"):       os.path.isdir("data/logs/")
  check("backups_dir_exists"):    os.path.isdir("data/backups/")
  ```

- [x] **4.3** Section 3 Ã¢â‚¬â€ Database & Migrations checks:
  ```python
  check("db_file_exists"):        os.path.exists("data/carecompanion.db")
  check("db_integrity"):          sqlite3_pragma_integrity_check() == "ok"
  check("migrations_table"):      "_applied_migrations" table exists in DB
  check("migration_count"):       count of applied migrations >= 35
  check("critical_tables"):       all critical tables exist (see list below)
  ```
  Critical tables verified: `user`, `billing_opportunity`, `billing_rule`, `patient_record`, `monitoring_rule`, `monitoring_schedule`, `rems_tracker_entry`, `calculator_result`, `ccm_enrollment`, `tcm_watch_entry`, `bonus_tracker`, `documentation_phrase`, `closed_loop_status`, `opportunity_suppression`, `immunization_series`, `communication_log`, `billing_campaign`, `payer_coverage_matrix`, `diagnosis_revenue_profile`, `patient_lab_result`, `patient_social_history`

- [x] **4.4** Section 4 Ã¢â‚¬â€ User Accounts check:
  ```python
  check("admin_exists"):   User table has at least one row with role='admin'
  check("user_count"):     User table has at least 1 row total
  ```

- [x] **4.5** Section 5 Ã¢â‚¬â€ Notifications checks:
  ```python
  check("pushover_user_key"):   bool(getattr(config, "PUSHOVER_USER_KEY", ""))
  check("pushover_api_token"):  bool(getattr(config, "PUSHOVER_API_TOKEN", ""))
  check("smtp_server"):         bool(getattr(config, "SMTP_SERVER", ""))  # warning, not critical
  ```

- [x] **4.6** Section 6 Ã¢â‚¬â€ API Keys checks:
  ```python
  check("openfda_key"):   bool(os.getenv("OPENFDA_API_KEY") or getattr(config, "OPENFDA_API_KEY", ""))
  check("umls_key"):      bool(os.getenv("UMLS_API_KEY"))
  check("loinc_creds"):   bool(os.getenv("LOINC_USERNAME"))
  check("pubmed_key"):    bool(os.getenv("PUBMED_API_KEY"))  # optional warning
  ```

- [x] **4.7** Section 7 Ã¢â‚¬â€ NetPractice / AC checks:
  ```python
  check("netpractice_url"):  bool(getattr(config, "NETPRACTICE_URL", ""))
  check("ac_mock_false"):    getattr(config, "AC_MOCK_MODE", True) == False
  check("ac_credentials"):   bool(getattr(config, "AC_LOGIN_USERNAME", "")) and bool(getattr(config, "AC_LOGIN_PASSWORD", ""))
  ```

- [x] **4.8** Section 8 Ã¢â‚¬â€ Agent Job Registry check:
  - Parse `agent_service.py` source and verify all 16 expected scheduled job names appear:
    `heartbeat`, `mrn_reader`, `inbox_check`, `inbox_digest`, `callback_check`, `overdue_lab_check`, `xml_archive_cleanup`, `xml_poll`, `weekly_summary`, `monthly_billing`, `deactivation_check`, `delayed_message_sender`, `eod_check`, `drug_recall_scan`, `previsit_billing`, `daily_backup`
  - ```python
    check("agent_job_count"):  count_of_scheduled_jobs_in_source == 16
    ```
  - Use string-search parsing of `agent_service.py` Ã¢â‚¬â€ look for `scheduler.add_job(` or equivalent pattern; count distinct job IDs

- [x] **4.9** Section 9 Ã¢â‚¬â€ Health & Logging checks:
  - Use Flask test client (no real server needed): `from app import create_app; client = create_app('testing').test_client()`
  - ```python
    check("health_endpoint"):    client.get("/api/health").status_code == 200
    check("log_dir_writable"):   os.access("data/logs/", os.W_OK)
    check("backup_job_in_src"):  "daily_backup" present in agent_service.py
    ```

- [x] **4.10** Section 10 Ã¢â‚¬â€ Full Test Suite run:
  - ```python
    result = subprocess.run(["python", "test.py"], capture_output=True, text=True, timeout=120)
    check("test_suite_pass"):    result.returncode == 0 and "0 failed" in result.stdout
    ```
  - Include abbreviated output snippet in report (last 10 lines of stdout)

- [x] **4.11** Report generation:
  - **JSON output:** `tools/deploy_report.json`
    ```json
    {
      "timestamp": "2026-03-25T14:30:00",
      "version": "v1.1.3",
      "host": "HOSTNAME",
      "checks": {
        "debug_false": {"pass": true},
        "db_integrity": {"pass": true, "detail": "ok"}
      },
      "summary": {"passed": 47, "failed": 0, "warnings": 2, "skipped": 1}
    }
    ```
  - **Console output:** Color-coded table per section
    - Green `Ã¢Å“â€œ` for pass, Red `Ã¢Å“â€”` for fail, Yellow `Ã¢Å¡Â ` for warning, Gray `-` for skip
    - Section headers with pass rate per section
    - Final summary line: `READY FOR DEPLOY Ã¢Å“â€œ  (47 passed, 0 failed, 2 warnings)` or `NOT READY Ã¢â‚¬â€ 3 failures Ã¢Å“â€”`
  - **Warning vs. failure distinction:** SMTP, PubMed key = warnings (non-blocking). DEBUG=True, bad secret key, DB integrity failure = hard failures (blocking).
  - Exit code: 0 if no hard failures, 1 if any hard failure (enables CI integration)

- [x] **4.12** Add 10 tests to `tests/test_deploy_check.py`:
  1. `tools/deploy_check.py` is importable without error
  2. Each check function returns a dict with a `"pass"` boolean key
  3. `check("debug_false")` returns `pass: False` when `config.DEBUG = True`
  4. `check("secret_key_random")` returns `pass: False` for a known dev default key
  5. `check("db_file_exists")` returns `pass: False` when DB path does not exist
  6. `check("critical_tables")` returns the expected list of table names to verify
  7. `check("admin_exists")` returns `pass: False` when User table has no admin
  8. Report JSON written to correct path and is valid JSON
  9. Console output contains the summary line with pass/fail counts
  10. `check("db_integrity")` returns `pass: True` on a healthy in-memory test DB

> **Phase 4 complete when:** `python -m pytest tests/test_deploy_check.py -v` Ã¢â‚¬â€ 10/10 pass. Manual run: `python tools/deploy_check.py` Ã¢â‚¬â€ console output shows section-by-section results, summary line visible.

---

## Phase 5 Ã¢â‚¬â€ Infrastructure Smoke Test Tools

**Goal:** Build three standalone infrastructure utility scripts for the USB deployment smoke test, database backup/restore procedure validation, and Tailscale/LAN connectivity test. These scripts are designed to be run on the work PC. The code is built in this phase; execution is confirmed in Phase 6 (the verification session).

**What will be built:**
- `tools/usb_smoke_test.py` Ã¢â‚¬â€ deployment smoke test for a fresh USB/exe installation
- `tools/backup_restore_test.py` Ã¢â‚¬â€ validates backup viability and restore procedure
- `tools/connectivity_test.py` Ã¢â‚¬â€ network connectivity verifier (LAN + Tailscale)
- Updated `Documents/dev_guide/DEPLOYMENT_GUIDE.md` Ã¢â‚¬â€ add USB deployment procedure section

**Implementation:**

- [x] **5.1** `tools/usb_smoke_test.py` Ã¢â‚¬â€ USB deployment smoke test:
  - Designed to run after `Start_CareCompanion.bat` boots the app from `build/carecompanion/`
  - Uses HTTP to test the running local server at `http://localhost:5000` (no Flask import needed)
  - **Checks performed:**
    1. `GET http://localhost:5000/api/health` Ã¢â€ â€™ status 200, body `{"status": "ok"}`
    2. `GET http://localhost:5000/login` Ã¢â€ â€™ status 200 (login page loads)
    3. `data/carecompanion.db` exists in working directory
    4. `data/logs/` directory exists
    5. `data/backups/` directory exists
    6. DB integrity: `PRAGMA integrity_check` Ã¢â€ â€™ `ok`
    7. Migration count: `_applied_migrations` table has Ã¢â€°Â¥ 35 rows
    8. Default user exists: `User` table has at least 1 row
  - **Output:** `usb_smoke_report_YYYYMMDD_HHMMSS.txt` written to the same directory as the script
  - **Format:**
    ```
    CareCompanion USB Deployment Smoke Test
    ======================================
    Timestamp: 2026-03-25 14:30:00
    Host: FPA-D-NP-DENTON
    
    Ã¢Å“â€œ Health endpoint: ok
    Ã¢Å“â€œ Login page: 200
    Ã¢Å“â€œ Database file: exists
    Ã¢Å“â€œ Migrations: 42 applied
    Ã¢Å“â€” Default user: User table empty Ã¢â‚¬â€ run /setup/onboarding
    
    RESULT: 7/8 passed Ã¢â‚¬â€ 1 action needed
    ```
  - No pytest Ã¢â‚¬â€ this is a standalone deployment tool

- [x] **5.2** `tools/backup_restore_test.py` Ã¢â‚¬â€ DB backup/restore validator:
  - **Backup verification phase:**
    1. Scan `data/backups/` for the most recent `*.db` backup file (most recent by mtime)
    2. Open backup file with `sqlite3` and run `PRAGMA integrity_check` Ã¢â€ â€™ must return `("ok",)`
    3. Compare row counts in both main DB and backup for tables: `user`, `billing_opportunity`, `patient_record` Ã¢â‚¬â€ backup counts must be within 10% of main DB
    4. Report backup age in hours: warn if backup is > 26 hours old
  - **Restore dry-run phase:**
    1. Copy most recent backup to `data/carecompanion_restore_test.db` (temp file)
    2. Open copy and verify all 21 critical tables exist (same list as Phase 4.3)
    3. Check user count > 0
    4. Run `PRAGMA integrity_check` on restore copy
    5. Print `RESTORE VIABLE Ã¢â‚¬â€ backup is sound` or `RESTORE FAILED Ã¢â‚¬â€ [reason]`
    6. Delete temp file immediately after check (no permanent side effect)
  - **Output:** Console summary + `tools/backup_check_report.txt`

- [x] **5.3** `tools/connectivity_test.py` Ã¢â‚¬â€ network and Tailscale connectivity tester:
  - **LAN checks:**
    1. `ping 192.168.2.51` via `subprocess.run(['ping', '-n', '2', '192.168.2.51'])` (Windows) Ã¢â‚¬â€ check return code 0
    2. UNC path access: `os.path.exists(config.AC_DB_PATH)` Ã¢â‚¬â€ AC database share reachable
    3. HTTP check: `requests.get(config.NETPRACTICE_URL, timeout=5)` Ã¢â‚¬â€ NetPractice responds
  - **Tailscale checks:**
    1. `tailscale status` via subprocess Ã¢â‚¬â€ check if command is in PATH
    2. If Tailscale is running: parse output for connected devices
    3. If `config.TAILSCALE_WORK_PC_IP` is set: ping that IP via Tailscale
  - **AC file share checks:**
    1. `os.path.exists(config.AC_IMPORTED_ITEMS_PATH)` Ã¢â‚¬â€ patient documents accessible via share
  - Each check: try/except so one failure does not abort the rest
  - **Output:** Console table + `tools/connectivity_report.txt`

- [x] **5.4** Add USB deployment procedure to `Documents/dev_guide/DEPLOYMENT_GUIDE.md`:
  - Open the existing `Deployment_Guide.md` and add a section: `## Pre-Beta USB Deployment Smoke Test`
  - Document steps:
    1. Build: `python build.py` Ã¢â‚¬â€ produces `build/carecompanion/`
    2. Copy `build/carecompanion/` to USB drive
    3. On work PC: run `Start_CareCompanion.bat` from USB
    4. Wait ~30 seconds for server to start
    5. Run `python tools/usb_smoke_test.py` from the USB directory
    6. Verify all checks pass in `usb_smoke_report_*.txt`
    7. Open browser to `http://localhost:5000` and confirm login page loads
    8. Log in and verify dashboard visible
  - Include link to `tools/usb_smoke_test.py` for reference

- [x] **5.5** Add 10 tests to `tests/test_infrastructure.py`:
  1. `tools/usb_smoke_test.py` is importable (syntax OK)
  2. `tools/backup_restore_test.py` is importable (syntax OK)
  3. `tools/connectivity_test.py` is importable (syntax OK)
  4. Backup verify function: returns dict with `"pass"` key and `"backup_age_hours"` key
  5. Restore dry-run: creates then deletes temp file Ã¢â‚¬â€ leaves no permanent artifact
  6. Restore dry-run: returns `"RESTORE VIABLE"` message on a valid DB
  7. Connectivity test: each check returns structured dict with `"pass"` and `"detail"` keys
  8. `GET /api/health` via test client returns JSON with `"status"` key
  9. `tools/` directory exists (no tool is accidentally placed at project root)
  10. `Deployment_Guide.md` contains "USB" section after Phase 5.4 edit

> **Phase 5 complete when:** `python -m pytest tests/test_infrastructure.py -v` Ã¢â‚¬â€ 10/10 pass. Visual confirm: `tools/` directory contains all 3 new scripts, `Deployment_Guide.md` updated.

---

# Part 4 Ã¢â‚¬â€ Guided Human Verification Session (Phase 6)

---

## Phase 6 Ã¢â‚¬â€ `verify_all.py` Ã¢â‚¬â€ Interactive Pre-Beta Verification

**Goal:** Build an interactive Python script that orchestrates the complete pre-beta verification session Ã¢â‚¬â€ the final gate before Tier-1 beta deployment with real patient data. The script automates everything automatable (deploy check, test suite, URL smoke test), then interactively guides the provider through 32 manual UI checks with Y/N prompts. At the end, it generates a signed `VERIFICATION_REPORT_<timestamp>.txt` Ã¢â‚¬â€ the go/no-go artifact for Tier-1 deployment.

**This is the mandatory final pre-Tier-1 step.** No automated tests replace the provider looking at the actual UI and confirming the right information is displayed for a real (demo) patient.

**What will be built:**
- `tools/verify_all.py` Ã¢â‚¬â€ interactive verification orchestrator
- `VERIFICATION_REPORT_<timestamp>.txt` Ã¢â‚¬â€ go/no-go artifact, written to `Documents/`

### Session Flow (5 Stages)

```
Stage 1 Ã¢â‚¬â€ Automated:  deploy_check.py (all 11 PRODUCTION_CHECKLIST sections)
Stage 2 Ã¢â‚¬â€ Automated:  full test suite (python test.py + pytest tests/)
Stage 3 Ã¢â‚¬â€ Automated:  Flask test client URL smoke test (38 URLs)
Stage 4 Ã¢â‚¬â€ Manual:     guided UI walkthrough (32 interactive checks)
Stage 5 Ã¢â‚¬â€ Output:     VERIFICATION_REPORT with go/no-go decision
```

### Implementation

- [x] **6.1** Stage 1 Ã¢â‚¬â€ Deploy check integration:
  - Import `run_all_checks()` from `tools.deploy_check` and execute
  - Print section-by-section PASS/FAIL with color codes
  - On any hard failure (not warning): prompt user:
    - `"Ã¢Å¡Â Ã¯Â¸Â  Critical failure in [{section}]: {detail}. Resolve and re-run? (Y/N): "`
    - If N: write partial report and exit with `"Ã°Å¸â€ºâ€˜ HOLD Ã¢â‚¬â€ pre-flight checks failed"`
  - Record all check results in `report_data["stage1"]`

- [x] **6.2** Stage 2 Ã¢â‚¬â€ Test suite execution:
  - ```python
    result1 = subprocess.run(["python", "test.py"], ...)
    result2 = subprocess.run(["python", "-m", "pytest", "tests/", "--tb=short", "-q"], ...)
    ```
  - Parse output to extract pass/fail counts
  - Display: `Ã¢Å“â€œ python test.py: 36 passed, 0 failed` and `Ã¢Å“â€œ pytest: 822 passed, 0 failed`
  - On any failure: list the failing test names; prompt user to note them
  - Record in `report_data["stage2"]`

- [x] **6.3** Stage 3 Ã¢â‚¬â€ URL smoke test using Flask test client:
  - Create app with testing config and log in as admin fixture user
  - Hit every route in the table below and verify expected status code
  - Display hit-by-hit results: `Ã¢Å“â€œ GET /dashboard Ã¢â€ â€™ 200` or `Ã¢Å“â€” GET /dashboard Ã¢â€ â€™ 500`
  - Record 38 URL results in `report_data["stage3"]`

  **URL smoke test list (38 URLs):**

  | URL | Expected | Category |
  |-----|----------|----------|
  | `GET /login` | 200 | Auth |
  | `GET /dashboard` | 200 | Core |
  | `GET /timer` | 200 | Core |
  | `GET /inbox` | 200 | Core |
  | `GET /oncall` | 200 | Core |
  | `GET /orders` | 200 | Core |
  | `GET /medref` | 200 | Core |
  | `GET /labtrack` | 200 | Core |
  | `GET /caregap` | 200 | Core |
  | `GET /metrics` | 200 | Core |
  | `GET /tools` | 200 | Core |
  | `GET /patient/DEMO001` | 200 | Patient |
  | `GET /caregap/DEMO001` | 200 | Patient |
  | `GET /caregap/DEMO001/print` | 200 | Patient |
  | `GET /briefing` | 200 | Intelligence |
  | `GET /billing/log` | 200 | Billing |
  | `GET /billing/em-calculator` | 200 | Billing |
  | `GET /billing/monthly-report` | 200 | Billing |
  | `GET /billing/why-not/DEMO001` | 200 | Billing |
  | `GET /bonus` | 200 | Billing |
  | `GET /ccm/registry` | 200 | Billing |
  | `GET /tcm/watch-list` | 200 | Billing |
  | `GET /monitoring/calendar` | 200 | Monitoring |
  | `GET /care-gaps/preventive` | 200 | Monitoring |
  | `GET /settings/phrases` | 200 | Settings |
  | `GET /campaigns` | 200 | Campaigns |
  | `GET /reports/revenue/2026/3` | 200 | Reports |
  | `GET /reports/dx-families` | 200 | Reports |
  | `GET /calculators` | 200 | Calculators |
  | `GET /staff/billing-tasks` | 200 | Staff |
  | `GET /admin` | 200 | Admin |
  | `GET /admin/users` | 200 | Admin |
  | `GET /admin/audit-log` | 200 | Admin |
  | `GET /admin/agent` | 200 | Admin |
  | `GET /admin/caregap-rules` | 200 | Admin |
  | `GET /admin/billing-roi` | 200 | Admin |
  | `GET /settings/account` | 200 | Settings |
  | `GET /api/health` | 200 | API |

- [x] **6.4** Stage 4 Ã¢â‚¬â€ Interactive manual UI walkthrough:
  - Before starting: prompt `"About to begin manual UI checks. Start Flask server fresh and open Chrome to http://localhost:5000. Press Enter when ready."`
  - For each manual check: print the check number, instructions, and what to confirm; then `input("PASS (y) / FAIL (n) / SKIP (s)? ")`
  - On `n`: prompt `"Describe the issue briefly: "` Ã¢â‚¬â€ record the note
  - Progress indicator: `[Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“â€˜Ã¢â€“â€˜Ã¢â€“â€˜Ã¢â€“â€˜Ã¢â€“â€˜Ã¢â€“â€˜Ã¢â€“â€˜Ã¢â€“â€˜Ã¢â€“â€˜Ã¢â€“â€˜Ã¢â€“â€˜Ã¢â€“â€˜] 40% Ã¢â‚¬â€ Check 13/32`

  **32 manual checks:**

  | # | Feature | Instruction | Confirm |
  |---|---------|-------------|---------|
  | 1 | Login page | Open Chrome Ã¢â€ â€™ `localhost:5000` | Login form visible Ã‚Â· No errors |
  | 2 | Dashboard load | Log in as CORY Ã‚Â· ASDqwe123 | Dashboard shows Ã‚Â· Today's date visible |
  | 3 | Timer | Click Timer in sidebar | Timer loads Ã‚Â· Start session works |
  | 4 | Inbox | Click Inbox | Filter tabs visible Ã‚Â· Digest tab present |
  | 5 | On-Call | Click On-Call Ã¢â€ â€™ New Note | Form opens Ã‚Â· Text can be entered |
  | 6 | Orders | Click Orders | Order sets list visible |
  | 7 | Med Ref | Click Med Ref Ã‚Â· search "metformin" | Search box works Ã‚Â· Results appear |
  | 8 | Lab Track | Click Lab Track | Stats cards + table visible |
  | 9 | Care Gaps | Click Care Gaps | Panel visible Ã‚Â· Date navigation works |
  | 10 | Metrics | Click Metrics | 7 Chart.js charts loaded (may be all zero) |
  | 11 | Patient chart | Go to `/patient/DEMO001` | Chart loads with widget layout |
  | 12 | Vitals widget | On DEMO001 chart | Height, weight, BMI, BP visible |
  | 13 | Billing alert bar | On DEMO001 chart | At least 1 billing code suggested |
  | 14 | Risk Scores widget | On DEMO001 chart | BMI, LDL, Pack Years, PREVENT cards visible |
  | 15 | Risk Tool Picker | Click Calculators tab on DEMO001 | Calculator form loads Ã‚Â· EHR-pre-filled fields shown |
  | 16 | CCM sidebar widget | On DEMO001 chart | CCM enrollment status shown |
  | 17 | Care Gap print | Go to `/caregap/DEMO001/print` | Clean handout Ã‚Â· No navigation chrome Ã‚Â· Gap list in plain English |
  | 18 | Billing log | Go to `/billing/log` | Table with filter controls visible |
  | 19 | Bonus dashboard | Go to `/bonus` | Quarterly bar Ã‚Â· Q1 2026 receipts Ã‚Â· Deficit visible |
  | 20 | CCM registry | Go to `/ccm/registry` | Ã¢â€°Â¥2 enrolled patients shown |
  | 21 | TCM watch list | Go to `/tcm/watch-list` | Ã¢â€°Â¥1 watch entry with deadline indicator |
  | 22 | Monitoring calendar | Go to `/monitoring/calendar` | Labs grouped by overdue/due/upcoming |
  | 23 | Preventive gaps | Go to `/care-gaps/preventive` | Per-service compliance bars visible |
  | 24 | Campaigns | Go to `/campaigns` | Campaign templates with launch buttons |
  | 25 | Morning briefing | Go to `/briefing` | All sections: schedule, TCM, labs, bonus, risk alerts |
  | 26 | Admin hub | Go to `/admin` | All 7 admin links visible |
  | 27 | Agent status | Go to `/admin/agent` | Agent status dashboard shows |
  | 28 | Care gap rules | Go to `/admin/caregap-rules` | 19 USPSTF rules listed |
  | 29 | Settings account | Go to `/settings/account` | Account form with username and role |
  | 30 | Restart script | Run `restart.bat` from File Explorer | Server restarts Ã‚Â· Chrome reopens to dashboard |
  | 31 | AC Mock Mode | Open `config.py` in Notepad | `AC_MOCK_MODE = False` confirmed (critical) |
  | 32 | Provider sign-off | Review this report's summary | All sections reviewed Ã‚Â· Provider acknowledges |

- [x] **6.5** Stage 5 Ã¢â‚¬â€ Report generation:
  - **File path:** `Documents/VERIFICATION_REPORT_YYYYMMDD_HHMMSS.txt`
  - Prompt for verifier name before writing: `"Enter your name for the report (e.g., Cory Denton, FNP): "`
  - **Report format:**
    ```
    Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
    CARECOMPANION Ã¢â‚¬â€ PRE-BETA VERIFICATION REPORT
    Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
    Generated: 2026-03-25 14:30:00
    Version:   v1.1.3
    Host:      FPA-D-NP-DENTON
    Python:    3.11.x
    Verified by: Cory Denton, FNP

    Ã¢â€â‚¬Ã¢â€â‚¬ SECTION 1: AUTOMATED PRE-FLIGHT (deploy_check.py) Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
    Ã¢Å“â€œ debug_false
    Ã¢Å“â€œ mock_mode_false
    Ã¢Å“â€œ secret_key_random
    Ã¢Å“â€œ tesseract_installed
    Ã¢Å“â€œ db_file_exists
    Ã¢Å“â€œ db_integrity: ok
    Ã¢Å“â€œ migration_count: 42 applied
    Ã¢Å“â€œ critical_tables: 21/21 present
    Ã¢Å“â€œ admin_exists
    Ã¢Å“â€œ pushover_user_key
    Ã¢Å“â€œ pushover_api_token
    Ã¢Å¡Â  smtp_server: not configured (non-critical Ã¢â‚¬â€ weekly email disabled)
    Ã¢Å“â€œ openfda_key
    Ã¢Å“â€œ umls_key
    Ã¢Å“â€œ loinc_creds
    Ã¢Å“â€œ netpractice_url
    Ã¢Å“â€œ ac_mock_false: confirmed
    Ã¢Å“â€œ agent_job_count: 16 jobs
    Ã¢Å“â€œ health_endpoint: 200
    Ã¢Å“â€œ log_dir_writable
    Ã¢Å“â€œ test_suite_pass: 36/36 passed
    Section result: 20/20 passed, 1 warning

    Ã¢â€â‚¬Ã¢â€â‚¬ SECTION 2: TEST SUITE Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
    Ã¢Å“â€œ python test.py: 36 passed, 0 failed
    Ã¢Å“â€œ pytest tests/: 822 passed, 0 failed

    Ã¢â€â‚¬Ã¢â€â‚¬ SECTION 3: URL SMOKE TEST Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
    Ã¢Å“â€œ 38/38 URLs returned expected status

    Ã¢â€â‚¬Ã¢â€â‚¬ SECTION 4: MANUAL VERIFICATION Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
    Ã¢Å“â€œ  1. Login page
    Ã¢Å“â€œ  2. Dashboard
    Ã¢Å“â€œ  3. Timer
    Ã¢Å“â€œ  4. Inbox
    Ã¢Å“â€œ  5. On-Call
    Ã¢Å“â€œ  6. Orders
    Ã¢Å“â€œ  7. Med Ref
    Ã¢Å“â€œ  8. Lab Track
    Ã¢Å“â€œ  9. Care Gaps
    Ã¢Å“â€œ 10. Metrics
    Ã¢Å“â€œ 11. Patient chart (DEMO001)
    Ã¢Å“â€œ 12. Vitals widget
    Ã¢Å“â€œ 13. Billing alert bar
    Ã¢Å“â€œ 14. Risk Scores widget
    Ã¢Å“â€œ 15. Risk Tool Picker
    Ã¢Å“â€œ 16. CCM sidebar
    Ã¢Å“â€œ 17. Care Gap print handout
    Ã¢Å“â€œ 18. Billing log
    Ã¢Å“â€œ 19. Bonus dashboard
    Ã¢Å“â€œ 20. CCM registry
    Ã¢Å“â€œ 21. TCM watch list
    Ã¢Å“â€œ 22. Monitoring calendar
    Ã¢Å“â€œ 23. Preventive gaps
    Ã¢Å“â€œ 24. Campaigns
    Ã¢Å“â€œ 25. Morning briefing
    Ã¢Å“â€œ 26. Admin hub
    Ã¢Å“â€œ 27. Agent status
    Ã¢Å“â€œ 28. Care gap rules
    Ã¢Å“â€œ 29. Settings account
    Ã¢Å“â€œ 30. Restart script
    Ã¢Å“â€œ 31. AC_MOCK_MODE = False  Ã¢â€ Â confirmed
    Ã¢Å“â€œ 32. Provider sign-off

    Ã¢â€â‚¬Ã¢â€â‚¬ SECTION 5: SUMMARY Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
    Automated pre-flight:  20/20 PASS Ã‚Â· 1 warning
    Test suite:            822 passed Ã‚Â· 0 failed
    URL smoke test:        38/38 PASS
    Manual checks:         32/32 PASS

    FAILS: none
    WARNINGS: smtp_server not configured (weekly summary email disabled)

    Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
    DECISION: Ã¢Å“â€¦ GO FOR BETA Ã¢â‚¬â€ all checks passed

    This report confirms that CareCompanion v1.1.3 has passed all
    automated and manual pre-deployment checks. The application
    is cleared for Tier-1 beta use with real patient data.

    Provider signature: ________________________
    Date: ____________________
    Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
    ```

- [x] **6.6** Go/no-go decision logic:
  - **GO:** All automated hard checks pass + 0 manual fails (warnings OK) Ã¢â€ â€™ `"Ã¢Å“â€¦ GO FOR BETA Ã¢â‚¬â€ all checks passed"`
  - **CONDITIONAL GO:** 0 hard failures + 1Ã¢â‚¬â€œ3 non-critical manual fails (items other than #1, #11, #31) Ã¢â€ â€™ `"Ã¢Å¡Â Ã¯Â¸Â CONDITIONAL GO Ã¢â‚¬â€ resolve noted items within 24 hours before first patient session"`
  - **HOLD:** Any hard automated failure OR any failure of items #1 (login), #11 (patient chart), or #31 (AC_MOCK_MODE) Ã¢â€ â€™ `"Ã°Å¸â€ºâ€˜ HOLD Ã¢â‚¬â€ must resolve critical issues before handling real patient data. See FAILS list above."`
  - The decision is printed prominently in the report and on the console

- [x] **6.7** Console progress display:
  - Color-coded output using ANSI escape codes (`\033[92m` green, `\033[91m` red, `\033[93m` yellow)
  - Progress bar for manual checks: `[Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“â€˜Ã¢â€“â€˜Ã¢â€“â€˜Ã¢â€“â€˜Ã¢â€“â€˜Ã¢â€“â€˜Ã¢â€“â€˜Ã¢â€“â€˜] 60% Ã¢â‚¬â€ Check 19/32`
  - Final result banner with box drawing characters (as shown in report format above)

- [x] **6.8** Add 10 tests to `tests/test_verify_all.py`:
  1. `tools/verify_all.py` is importable without error
  2. `run_automated_checks()` function returns dict with keys for all 3 automated stages
  3. URL smoke test function covers all 38 URLs in its list
  4. Report generator creates a `.txt` file at the correct path
  5. Report contains timestamp, version, and host fields
  6. Report contains PASS/FAIL counts for each section
  7. Decision logic: all stages pass + 0 manual fails Ã¢â€ â€™ returns `"GO"`
  8. Decision logic: hard automated failure Ã¢â€ â€™ returns `"HOLD"` (not `"GO"`)
  9. Decision logic: non-critical manual fail + all automated pass Ã¢â€ â€™ returns `"CONDITIONAL GO"`
  10. Report is written to the `Documents/` directory (not `tools/` or project root)

> **Phase 6 complete when:** `python -m pytest tests/test_verify_all.py -v` Ã¢â‚¬â€ 10/10 pass. \
> **Execution:** Run `python tools/verify_all.py` on the work PC (FPA-D-NP-DENTON), complete all 32 manual checks, review the generated `VERIFICATION_REPORT_*.txt`. If decision = GO, beta launch proceeds.

---

# Part 5 Ã¢â‚¬â€ Final Regression & Documentation (Phase 7)

---

## Phase 7 Ã¢â‚¬â€ Full Regression Pass & Plan Documentation

**Goal:** Run the complete test suite one final time after all phases are complete, update all documentation to reflect the final state, and write the "What Still Remains" section at the bottom of this document.

- [x] **7.1** Run full main test suite: `python test.py` Ã¢â‚¬â€ all 36 checks PASS, 0 errors
- [x] **7.2** Run all phase suites: `python -m pytest tests/ -v --tb=short` Ã¢â‚¬â€ 0 failures. Document final test count.
- [x] **7.3** Update `Documents/dev_guide/CARECOMPANION_DEVELOPMENT_GUIDE.md`:
  - Bump test count to final count after this plan (~822+)
  - Feature table: verify all feature statuses are current
  - Add note: `final_plan.md` created; pre-beta verification complete
- [x] **7.4** Update `Documents/dev_guide/PROJECT_STATUS.md`:
  - Add `final_plan.md` summary to the What's Done list (7 phases, ~120 tests, 5 new tools)
  - Update "What's Next" to: "Phase 7 verification session on FPA-D-NP-DENTON, then Tier-1 beta"
- [x] **7.5** Write "What Still Remains After final_plan.md" section below

> **Phase 7 complete when:** Full regression passes. Documentation current. `verify_all.py` is ready for the work-PC verification session.

---

## Phase Summary

| Phase | Title | Tests | Files Created |
|-------|-------|-------|---------------|
| 1 | USPSTF Care Gap UI Enhancements | 10 | `caregap_print_handout.html`, `test_caregap_ui.py` |
| 2 | Audit Fixes: WebPractice + keyboard | 5 | `test_misc_audit_fixes.py` |
| 3 | E2E Integration Test Suite | 75 | 4 new test files + 5 extended tests |
| 4 | `deploy_check.py` Pre-Flight Checker | 10 | `tools/deploy_check.py`, `test_deploy_check.py` |
| 5 | Infrastructure Smoke Test Tools | 10 | `tools/usb_smoke_test.py`, `tools/backup_restore_test.py`, `tools/connectivity_test.py`, `test_infrastructure.py` |
| 6 | `verify_all.py` Guided Verification | 10 | `tools/verify_all.py`, `test_verify_all.py` |
| 7 | Final Regression & Docs | Ã¢â‚¬â€ | Updated DevGuide, PROJECT_STATUS |
| **Total** | | **~120 tests** | **7 Python tools, 6 test files, 2 templates** |

## File Impact Map

| File | Phase(s) | Type |
|------|----------|------|
| `routes/caregap.py` | 1 | MODIFY Ã¢â‚¬â€ add print_handout route + trigger_type derivation |
| `templates/caregap_print_handout.html` | 1 | CREATE |
| `templates/caregap_patient.html` | 1 | MODIFY Ã¢â‚¬â€ Print button, toggle, data-trigger-type |
| `templates/netpractice_setup.html` | 2 | MODIFY Ã¢â‚¬â€ improved placeholder + help text |
| `static/js/main.js` | 2 | MODIFY Ã¢â‚¬â€ F10 suppression check |
| `tests/test_caregap_ui.py` | 1 | CREATE Ã¢â‚¬â€ 10 tests |
| `tests/test_misc_audit_fixes.py` | 2 | CREATE Ã¢â‚¬â€ 5 tests |
| `tests/test_e2e_billing_pipeline.py` | 3 | CREATE Ã¢â‚¬â€ 25 tests |
| `tests/test_e2e_calculator_pipeline.py` | 3 | CREATE Ã¢â‚¬â€ 15 tests |
| `tests/test_morning_briefing_integration.py` | 3 | CREATE Ã¢â‚¬â€ 15 tests |
| `tests/test_billing_multi_patient.py` | 3 | CREATE Ã¢â‚¬â€ 15 tests |
| `tests/test_phase15_data_pipeline.py` | 3 | MODIFY Ã¢â‚¬â€ +5 tests |
| `tools/deploy_check.py` | 4 | CREATE |
| `tests/test_deploy_check.py` | 4 | CREATE Ã¢â‚¬â€ 10 tests |
| `tools/usb_smoke_test.py` | 5 | CREATE |
| `tools/backup_restore_test.py` | 5 | CREATE |
| `tools/connectivity_test.py` | 5 | CREATE |
| `tests/test_infrastructure.py` | 5 | CREATE Ã¢â‚¬â€ 10 tests |
| `tools/verify_all.py` | 6 | CREATE |
| `tests/test_verify_all.py` | 6 | CREATE Ã¢â‚¬â€ 10 tests |
| `Documents/dev_guide/DEPLOYMENT_GUIDE.md` | 5 | MODIFY Ã¢â‚¬â€ USB procedure section |
| `Documents/dev_guide/CARECOMPANION_DEVELOPMENT_GUIDE.md` | 7 | MODIFY |
| `Documents/dev_guide/PROJECT_STATUS.md` | 7 | MODIFY |

---

# What Still Remains After This Plan

> **Status:** After completing all 7 phases of this plan, the following items remain outside the scope of any completed development plan. These are documented here for the next planning cycle.

---

## Tier 1 Ã¢â‚¬â€ Blocked by Work-PC Access (Unchanged from running_plan.md Part 6)

| Item | Feature | Blocker | Notes |
|------|---------|---------|-------|
| **F9** Ã¢â‚¬â€ Chart Prefill | Auto-fill patient fields in Amazing Charts | AC screen coordinate calibration on FPA-D-NP-DENTON | All structural code ready; run `python agent/ac_window.py --calibrate` on live AC |
| **F28a** Ã¢â‚¬â€ MRN Calibration | `agent/mrn_reader.py` region calibration | Live AC window required for capture | Diagnostic exists; visual tool needs live session |
| **AC Window OCR tuning** | All AC automation features | Requires live AC for snapshot | `ocr_helpers.py` + `pyautogui_runner.py` ready |

---

## Tier 2 Ã¢â‚¬â€ Awaiting External Resources (Unchanged from running_plan.md Part 6)

| Item | Dependency | Code State |
|------|------------|------------|
| **GoodRx API Key** | GoodRx developer account approval | `goodrx_service.py` fully built; activates on key addition |
| **ASCVD PCE coefficients** | Goff 2014 Appendix 7 | `compute_ascvd()` stub in engine; tagged `auto_ehr_blocked` |
| **Gail Model coefficients** | NCI BCRAT tables | Registry entry exists; tagged `blocked` |
| **Hankinson 1999 equations** | NHANES III regression tables | Partial implementation for sub-groups exists |
| **Rosner 2008 BP percentile tables** | NHBPEP tables for ages 1Ã¢â‚¬â€œ12 | Ages 13+ work; <13 tagged `partial` |
| **Part B enrollment date** | Not in AC CDA XML | Age heuristic in place; manual entry field deferred |

---

## Tier 3 Ã¢â‚¬â€ Infrastructure Deferred

| Item | Status After This Plan | Priority |
|------|------------------------|----------|
| **F30 Ã¢â‚¬â€ Offline Mode** | Still unbuilt; scope is large (Service Worker + IndexedDB + sync) | Post-beta Medium |
| **CI/CD Pipeline** | Still unbuilt; git push Ã¢â€ â€™ auto-test Ã¢â€ â€™ build | Post-beta Low |
| **USB Deployment Smoke Test** | **Tools built (Phase 5); executed in Phase 6 verification** | Ã¢â‚¬â€ done |
| **DB Backup/Restore** | **Procedure tested (Phase 5); verified in Phase 6** | Ã¢â‚¬â€ done |
| **Tailscale Remote Access** | **Connectivity test built (Phase 5); verified in Phase 6** | Ã¢â‚¬â€ done |

---

## Tier 4 Ã¢â‚¬â€ Calculator Completions (Unchanged from running_plan.md Part 6)

Calculator slots (ASCVD, Gail, Peak Flow main-group, AAP Peds HTN <13) Ã¢â‚¬â€ slots exist in the registry; implementations are added once the blocked external data arrives. No new code needed until then.

---

## Tier 6 Ã¢â‚¬â€ Future Feature Ideas (Post-Beta)

| Idea | Complexity |
|------|------------|
| FHIR R4 export | High |
| Patient portal Ã¢â‚¬â€ secure patient-facing view | High |
| Bulk claims reconciliation (EOB PDF import) | High |
| Specialty-specific billing template sets | Medium |
| Voice dictation via WebSpeech API | Medium |
| NPI registry specialist lookup | Low |
| HL7 v2 message parsing | High |

---

## Final Deployment Sequence (When All 7 Phases Complete)

1. `python tools/deploy_check.py` Ã¢â€ â€™ all checks PASS
2. `python -m pytest tests/ -v` Ã¢â€ â€™ 0 failures
3. On work PC: `python tools/verify_all.py` Ã¢â€ â€™ complete 32 manual checks Ã¢â€ â€™ generate `VERIFICATION_REPORT_*.txt`
4. Report decision = **GO**
5. Take manual DB backup: copy `data/carecompanion.db` to safe location
6. Set `DEBUG = False`, `AC_MOCK_MODE = False` in `config.py`
7. Run `Start_CareCompanion.bat` Ã¢â‚¬â€ first clinical session begins
8. Monitor `data/logs/carecompanion.log` for first 2 hours

---

*This plan addresses all three remaining Medium-priority audit items (K2 USPSTF print, K2 USPSTF toggle, A4 WebPractice placeholder), builds the five deferred E2E test suites from Tier 5, hardens infrastructure with three deployment utility scripts, automates `PRODUCTION_CHECKLIST.md` via `deploy_check.py`, and closes with a mandatory human-guided verification session orchestrated by `verify_all.py` that generates a signed go/no-go artifact. All 7 phases are buildable without work-PC access. The Phase 6 verification execution requires physical access to FPA-D-NP-DENTON.*

---

## HIPAA Compliance — Soft-Delete + MRN Masking (ad-hoc)

> **Completed:** 03-23-26 23:45:00 UTC
> **Triggered by:** Session-start HIPAA audit found 2 hard-deletes on clinical records + 4 full-MRN template displays.

- [x] Add `is_archived` column to `LabTrack` and `PatientSpecialist` models
- [x] Convert `LabTrack` delete route to soft-delete (`is_archived=True`)
- [x] Convert `PatientSpecialist` delete route to soft-delete (`is_archived=True`)
- [x] Add `is_archived=False` filter to all LabTrack list/count queries (14 sites)
- [x] Add `is_archived=False` filter to PatientSpecialist list query
- [x] Fix MRN display in `dashboard.html` → `••{{ pt.mrn[-4:] }}`
- [x] Fix MRN display in `_tickler_card.html` → `••{{ t.mrn[-4:] }}`
- [x] Fix MRN display in `daily_summary_print.html` → `MRN ••{{ pt.mrn[-4:] }}`
- [x] Fix MRN fallback in `cs_tracker.html` → `••{{ e.mrn[-4:] }}`
- [x] Create + run migration `migrate_add_is_archived.py`
- [x] Update CHANGE_LOG (CL-HIPAA-SOFTDEL) + Risk Register (R2)

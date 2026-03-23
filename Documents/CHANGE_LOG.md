# CareCompanion — Change Log

> **Single source of truth** for all development changes. Organized newest-first.
> Completed plan phases are "graduated" here from `Documents/dev_guide/ACTIVE_PLAN.md`.
> See `data/changelog.json` for the in-app user-facing changelog (separate concern).

---

## CL-MIG-RECURSION — Fix Migration Infinite Recursion Bug
**Completed:** 07-14-25 18:30:00 UTC
- **Root cause:** `migrate_add_calculator_results.py` used `def run()` which called `create_app()` → triggered `_run_pending_migrations()` → subprocess → `create_app()` → infinite loop. Same pattern in `migrate_add_scraper_overhaul.py` (alias `run = migrate` not detected).
- **Fix 1:** Refactored both migrations to use `def run_migration(app, db)` signature, matching what `_run_pending_migrations()` expects for in-process execution.
- **Fix 2:** Added recursion guard to `_run_pending_migrations()` — uses `_running` sentinel attribute to prevent re-entry, with `try/finally` cleanup.
- **Result:** Both migrations now execute in-process. 64/64 migrations applied. All 93 tests pass.

### Files Modified
- `app/__init__.py` — Added recursion guard (`_running` flag + try/finally) to `_run_pending_migrations()`
- `migrations/migrate_add_calculator_results.py` — `def run()` → `def run_migration(app, db)`, moved `create_app()` to `__main__` guard
- `migrations/migrate_add_scraper_overhaul.py` — `def migrate()` + `run = migrate` → `def run_migration(app, db)` + `_do_migrate()` helper

---

## CL-HIPAA-SOFTDEL — HIPAA Soft-Delete + MRN Masking Compliance Fix
**Completed:** 03-23-26 23:45:00 UTC
- **LabTrack hard-delete → soft-delete:** `routes/labtrack.py` delete_tracking() now sets `is_archived=True` instead of `db.session.delete()`
- **PatientSpecialist hard-delete → soft-delete:** `routes/patient.py` delete_specialist() now sets `is_archived=True` instead of `db.session.delete()`
- **Added `is_archived` column** to both `LabTrack` and `PatientSpecialist` models (Boolean, default False)
- **All LabTrack list/count queries** now filter `is_archived=False` (14 query sites across labtrack.py, patient.py, admin.py, intelligence.py)
- **All PatientSpecialist list queries** now filter `is_archived=False`
- **Fixed 4 template MRN display violations** (HIPAA: UI must show only last 4 digits):
  - `dashboard.html` — patient list table: `{{ pt.mrn }}` → `••{{ pt.mrn[-4:] }}`
  - `_tickler_card.html` — tickler MRN display: `{{ t.mrn }}` → `••{{ t.mrn[-4:] }}`
  - `daily_summary_print.html` — daily summary: `MRN {{ pt.mrn }}` → `MRN ••{{ pt.mrn[-4:] }}`
  - `cs_tracker.html` — controlled substance tracker: `{{ e.mrn }}` fallback → `••{{ e.mrn[-4:] }}`

### Files Modified
- `models/labtrack.py` — Added `is_archived` column
- `models/patient.py` — Added `is_archived` column to PatientSpecialist
- `routes/labtrack.py` — Soft-delete + is_archived=False filters on all queries
- `routes/patient.py` — Soft-delete + is_archived=False filters
- `routes/admin.py` — is_archived=False filters on admin stats
- `routes/intelligence.py` — is_archived=False filter on AI lab interpretation
- `templates/dashboard.html` — MRN masking
- `templates/_tickler_card.html` — MRN masking
- `templates/daily_summary_print.html` — MRN masking
- `templates/cs_tracker.html` — MRN masking

### Migration
- `migrations/migrate_add_is_archived.py` — Adds `is_archived BOOLEAN NOT NULL DEFAULT 0` to `lab_tracks` and `patient_specialists` tables

---

## CL-LABREF — Lab Reference & Abbreviation Editor
**Completed:** 03-23-26 04:00:00 UTC
- Added 📖 Lab Reference modal: searchable list of all 101 labs with abbreviation, panels, and range display
- Added Lab Detail card: editable abbreviation field + 4-section clinical reference (What It Measures, Clinical Significance, ⬆ Causes of High, ⬇ Causes of Low)
- Added `POST /api/lab-cache/update` endpoint: saves abbreviation and reference edits to `data/lab_cache.json`
- Added `refs` section to `lab_cache.json` with 101 pre-populated clinical reference entries (biochemistry, significance, high/low causes)
- Added ℹ info icon in autocomplete dropdown items — opens Lab Detail card directly from search
- Added "📖 Lab Reference" button in labtrack subpanel + link in orders subpanel (navigates to `/labtrack?ref=1`)
- Cache invalidation: saves clear both JS caches (`_labRefData` + `LabAutocomplete._clearCache`)

### Files Modified
- `routes/labtrack.py` — `/api/lab-cache/update` POST endpoint
- `templates/labtrack.html` — Lab Reference modal, Lab Detail card, JS functions, subpanel button
- `templates/orders.html` — Lab Reference link in subpanel
- `static/js/labtrack.js` — ℹ icon in dropdown, `clearCache()` function
- `data/lab_cache.json` — `refs` section with 101 clinical reference entries

---

## CL-CPUOPT — VS Code CPU Optimization for Autopilot Workflow
**Completed:** 03-23-26 22:30:00 UTC

Created `.vscode/settings.json` with ~60 settings to minimize CPU/memory/GPU usage. User operates purely through Copilot Chat (AI autopilot) and does not code directly, so all active-coding features are disabled.

### Key Optimizations
- **Editor:** Disabled minimap, code lens, inlay hints, bracket colorization, occurrence highlighting, folding, glyph margin, hover tooltips, parameter hints, quick suggestions, semantic highlighting, smooth scrolling/animations
- **Workbench:** Reduced motion, disabled experiments, tips, indent guides
- **Terminal:** GPU acceleration off, smooth scrolling off
- **File watcher:** Excluded venv, __pycache__, build, dist, data/logs, data/backups, tesseract, .pytest_cache — stops continuous disk scanning
- **Git:** Disabled autorefresh, autofetch, decorations — eliminates periodic `git status` polling
- **Pylance:** Open-files-only diagnostics, indexing off, auto-import off — major CPU saver (no background whole-project analysis)
- **Search:** Excluded large/irrelevant directories from search scope
- **Telemetry:** Off entirely
- **JS/TS:** Validation and suggestions disabled (Python-only project)
- **Breadcrumbs, outline, emmet:** All disabled

### Files
- `.vscode/settings.json` (new, gitignored — local to this machine)

---

## CL-PROCGUARD — Process Management Hardening
**Completed:** 03-23-26 22:15:00 UTC

### Problem
VS Code crashed repeatedly from 160+ orphaned Python processes accumulating during autopilot sessions. Terminal commands (tests, migrations, scripts) were spawned as background processes or without timeouts, never exiting.

### Changes
- **`.github/copilot-instructions.md`** — Added "Process & Resource Management — Hard Rules" section with terminal discipline, cleanup procedures, crash causes, and process limits
- **`.github/agents/CareCompanion.agent.md`** — Added mandatory process audit at Phase 1 start and Phase 4 end; added "Process & Resource Management" to Hard Rules section
- **`.github/prompts/keep-working.prompt.md`** — Added Phase 0 (Process Guard) that runs before any work; updated Phase 5 to include cleanup; loop now returns to Phase 0
- **`.github/prompts/test-plan.prompt.md`** — Added Step 0 (Process Guard) before running any tests
- **`.github/instructions/agent-boundary.instructions.md`** — Added "Process & Resource Management" section requiring timeouts on all subprocess calls, tracked Popen objects, APScheduler guards, and PID logging
- **`build.py`** — Added `timeout=600` to PyInstaller `subprocess.run()` call (was missing)
- **`tools/process_guard.py`** — New utility script for detecting/killing orphaned Python processes; supports `--kill` (high CPU/mem) and `--kill-all` modes; uses psutil with tasklist fallback

### Rules Enforced
- Every terminal command must have a timeout (never `timeout: 0`)
- Tests/migrations/builds/linters are NEVER `isBackground: true`
- Max 4 Python processes during development; hard stop at 8
- Process audit runs at session start AND end
- ONE dev server at a time; check port before starting

---

## CL-UXAUDIT2 — UX Enhancements Items 9-20
**Completed:** 07-21-25 04:00:00 UTC

### Schedule Grid (UX-9)
- Added `PUT /api/schedule/<id>/move` endpoint for drag-and-drop time changes
- Added `id` and `patient_mrn` fields to GET `/api/schedule` JSON response
- Added `schedule_grid.js` script include and init block to dashboard template
- Grid supports 44 time slots (7AM-6PM), drag-drop, table/grid toggle

### Widget Drag Improvements (UX-10)
- Replaced 6px invisible drag handle with 18px visible gripper using SVG 6-dot pattern
- Added auto-scroll when dragging near container edges (40px threshold)
- Hover state: opacity 0.5→1.0 with cursor:grab

### Settings Sub-Sidebar (UX-11)
- Added `.settings-layout` flex container with `.settings-nav` sticky sidebar (8 section links)
- Added `id` attributes to all settings section headers for anchor navigation
- Added scroll-spy JS for active link highlighting
- Responsive: collapses to horizontal tabs at 700px

### Sidebar Drag Reorder (UX-12)
- Added `data-nav-id` attributes to all 13 sidebar nav items
- HTML5 drag-and-drop reorder within sidebar, saves to localStorage and server
- Persists per-user via `POST /settings/account/preference`

### Lab Cache Data (UX-13)
- Created `data/lab_cache.json`: 98 lab entries with name, abbr, LOINC, units, ranges, critical ranges, panel membership
- 15 standard panels mapped (BMP, CMP, CBC, Lipid, Thyroid, Hepatic, Coag, etc.)

### Lab Autocomplete (UX-14)
- Created `static/js/labtrack.js`: fuzzy-match autocomplete with scoring (exact/startsWith/contains/character)
- Dropdown shows range hints and panel badges, keyboard navigation (up/down/enter/escape)
- Auto-fills alert threshold fields from lab cache reference data
- Added `GET /api/lab-cache` endpoint to labtrack routes
- Added CSS for `.lab-autocomplete-dropdown` and item classes with dark mode support

### Lab Panel Component Badges (UX-15)
- Added `data-lab-name` and `data-panel-name` attributes to lab table cells
- JS decorates panel rows with component abbreviation badges from lab cache
- Current lab highlighted with teal badge, other components shown in muted style
- CSS: `.panel-comp-badges`, `.panel-comp-dot`, `.panel-comp-dot--current`

### Care Gap Copy-to-Template (UX-16)
- Added "📋 Copy Doc" button next to "Address Now" on open care gaps
- `copyGapTemplate()` copies documentation snippet from address form textarea or gap description
- Updated textarea to prefer `documentation_snippet` over `description` for richer templates

### Order Set UI + AC Calibration Wizard (UX-17)
- Order set builder already exists (comprehensive 2-panel UI with master order browser)
- Added AC Calibration Wizard: `GET /orders/calibrate` route + `templates/ac_calibrate.html`
- 6 calibration points (inbox filter, patient search, template radio, dropdown, export menu, export button)
- 3-second countdown capture via pyautogui cursor position, saves to `data/ac_calibration.json`
- Added "🔧 AC Calibration" link in orders subpanel

### Widget Management Panel (UX-18)
- Added "⚙ Manage Widgets" button injected at top-right of `.fw-container`
- Modal panel lists all widgets with visibility toggles, drag-reorder, and size display
- "Show All" and "Reset Order" buttons in panel footer
- Widget order persists to localStorage via `widget_order` key
- Applied on init: `_applyWidgetOrder()` reorders DOM elements per saved order

### Prior Auth Intelligence (UX-19)
- Added MRN field with patient lookup button (auto-fills name and insurance via `/api/patient/<mrn>/summary`)
- Added PA Reference # field and collapsible Payer Contact Info section (phone/fax)
- Added visual status timeline in PA history table: draft→submitted→decision progression with colored dots
- Added `GET /api/patient/<mrn>/summary` endpoint to patient routes
- Timeline CSS: `.pa-timeline`, `.pa-tl-dot` (done/active/approved/denied states)

### Add/Delete Diagnosis (UX-20)
- Added `POST /patient/<mrn>/diagnosis/add` endpoint — creates new PatientDiagnosis with user_id scoping
- Added `POST /patient/<mrn>/diagnosis/<id>/remove` endpoint — soft-deletes by setting status='resolved'
- Added "+ Add" button in ICD-10 lookup modal results — adds to patient table in real-time
- Added "✕" remove button on each diagnosis row — confirms then soft-deletes
- Added "+ Add Dx" button in diagnosis widget controls
- New diagnosis rows appended to table dynamically without page reload

### Files Created
- `templates/ac_calibrate.html` — AC calibration wizard template
- `static/js/labtrack.js` — Lab autocomplete + panel badge JS module
- `data/lab_cache.json` — Lab reference data (98 labs, 15 panels)

### Files Modified
- `routes/dashboard.py` — Schedule move endpoint, API response fields
- `routes/labtrack.py` — `/api/lab-cache` endpoint
- `routes/orders.py` — Calibration wizard routes (capture, save)
- `routes/patient.py` — Patient summary API, add/remove diagnosis endpoints
- `routes/tools.py` — (no changes, PA routes already existed)
- `templates/dashboard.html` — Schedule grid script include + init
- `templates/labtrack.html` — Autocomplete input + dropdown + CSS + panel badge slots
- `templates/settings.html` — Sub-sidebar layout + scroll-spy
- `templates/orders.html` — Calibration link in subpanel
- `templates/caregap_patient.html` — Copy Doc button + template improvement
- `templates/pa.html` — MRN lookup, payer fields, timeline, patient summary
- `templates/patient_chart.html` — Add diagnosis button, remove button, ICD-10 Add button
- `templates/base.html` — Sidebar drag-reorder data attributes + JS
- `static/css/main.css` — Settings sidebar CSS
- `static/js/free_widgets.js` — Widget management panel, gripper handles, auto-scroll, widget order

---

## CL-UXAUDIT — UX Quick Fixes (Items 1-8) + Dev Guide UX Roadmap (9-20)
**Completed:** 07-20-25 18:45:00 UTC

### Quick Fixes Implemented (1-8)
- **Fix 1 & 2: Screen lock** — Lock screen now skips if user has no PIN set (`data-has-pin` body attribute). Lock state persists across page refreshes via `sessionStorage`. Lock logo changed from "NP" to "CC".
- **Fix 3: USPSTF clean names** — Added `|gap_display` Jinja template filter with 21-entry mapping dict. All caregap templates now show human-readable screening names instead of database keys.
- **Fix 4: Dismiss schedule gap alert** — Added × close button to anomaly items in both Tier 1 (warning) and Tier 2 (info) dashboard sections.
- **Fix 5: Menu bar → header consolidation** — Moved menu bar nav inside the header as inline flex child. Removed standalone menu bar grid row. Grid changed from 3-row to 2-row across all variants (default, has-subpanel, sidebar-collapsed, mobile). Removed clock element. Updated CSS class from `.app-menu-bar` to `.header-menu`. Menu font bumped to 13px matching header.
- **Fix 6: Horizontal scroll fix** — Added `table-layout: fixed`, `text-overflow: ellipsis`, tighter padding to `.schedule-table`. Added `min-width: 0` to `.dash-widget` and `.dash-widget-body` to prevent grid overflow.
- **Fix 7: PDMP/VIIS credentials** — Added 4 encrypted credential columns to User model (`pdmp_username_enc`, `pdmp_password_enc`, `viis_username_enc`, `viis_password_enc`). Added encrypt/decrypt/has helpers. Added settings forms and route handlers. Migration applied.
- **Fix 8: Re-eval care gaps on gender change** — `update_demographics()` route now detects sex changes and triggers `evaluate_and_persist_gaps()` to re-run the care gap engine with the updated sex value.

### Dev Guide Updates
- Added Section 10 "UX/UI Enhancement Roadmap" with items UX-9 through UX-20 to `CARECOMPANION_DEVELOPMENT_GUIDE.md`

### Files Modified
- `templates/base.html` — Menu bar nav moved inside header, clock removed, old standalone nav deleted
- `static/css/main.css` — Grid to 2-row, `.header-menu` class, schedule table fixes, widget min-width
- `static/js/main.js` — Screen lock PIN check + sessionStorage persist (from prior session)
- `app/__init__.py` — `gap_display` Jinja filter (from prior session)
- `templates/caregap.html`, `templates/caregap_patient.html` — `|gap_display` filter usage (from prior session)
- `templates/dashboard.html` — Anomaly dismiss buttons (from prior session)
- `models/user.py` — PDMP/VIIS credential columns + helpers
- `templates/settings.html` — PDMP and VIIS credential forms
- `routes/auth.py` — PDMP/VIIS credential save handlers
- `routes/patient.py` — Care gap re-eval on sex change
- `migrations/migrate_add_pdmp_viis_creds.py` — New migration
- `Documents/dev_guide/CARECOMPANION_DEVELOPMENT_GUIDE.md` — Section 10 added

---

## CL-UIBATCH1 — UI/UX Batch: Menu Bar, Patient Chart, Briefing Print, Pushover
**Completed:** 07-20-25 03:30:00 UTC

### Changes
- **Menu bar grid position** — Moved menu bar out of header into its own grid row. Layout is now 3-row: `header | sidebar+menubar | sidebar+main`. Sidebar spans rows 2-3. Updated all grid variants (default, has-subpanel, sidebar-collapsed, will-collapse, responsive).
- **Patient chart allergies in banner** — Added contrasting amber allergy badge in patient header (right side) showing comma-separated allergen names with hover tooltip for reactions. NKDA shown when empty.
- **Patient header sticky on scroll** — `position: sticky; top: 0; z-index: 50` so it stays visible while scrolling chart content.
- **Dismissable "no clinical summary" banner** — Added × close button to hide the banner via inline onclick.
- **Vitals widget ordered & scrollable** — Vitals now displayed in clinical priority order (pulse, BP, SpO2, RR, temp, weight, height, BMI) with scrollable overflow for long lists.
- **Morning briefing print buttons** — Added "Provider Summary", "MA Sheet", and "Print Briefing" buttons to morning briefing header, linking to existing daily-summary print routes plus native print.
- **Pushover briefing notification** — Added `send_briefing_notification()` to notifier.py (counts only, no PHI). New `/briefing/push` POST route. "Push to Phone" button on briefing page.
- **Patient print paperwork stub** — New `/patient/<mrn>/print` route + `patient_print_stub.html` template with "Coming Soon" placeholder. Print button added to patient chart header.

### Files Modified
- `templates/base.html` — Menu bar moved from header-left to own grid area child of `.app-layout`
- `static/css/main.css` — 3-row grid layout, `.app-menu-bar` with `grid-area: menubar`, updated all responsive variants
- `templates/patient_chart.html` — Allergy badge in header, sticky header, dismiss banner, ordered vitals, print button
- `templates/morning_briefing.html` — Print buttons, Pushover push button, print media styles
- `routes/intelligence.py` — `/briefing/push` POST route
- `routes/patient.py` — `/patient/<mrn>/print` GET route
- `agent/notifier.py` — `send_briefing_notification()` function
- `templates/patient_print_stub.html` — New stub template (print paperwork placeholder)

### Notes
- Widget layout already uses user-level preferences (not per-patient) — confirmed no change needed.
- No visible "CareCompanion" text on dashboard content — only in browser tab title and About dialog (appropriate).

---

## CL-P7FIX — test_phase7.py Fix: CSRF + Unicode + pytest Collection
**Completed:** 07-20-25 02:30:00 UTC

### Root Cause
`tests/test_phase7.py` was a standalone test script (68 checks) that had 3 compounding bugs:
1. **Missing `WTF_CSRF_ENABLED = False`** — all POST routes returned 500 because Flask-WTF CSRF protection rejected requests without tokens. This caused 7 test failures (pin, bookmark, patient-gen, what's-new APIs).
2. **Unicode arrow character `→` (U+2192)** — not representable in Windows cp1252 encoding when piped to file. Crashed the `ok()` print function, turning 4 PASSes into ERRORs.
3. **No `if __name__ == '__main__':` guard** — `sys.exit(1)` at module level killed pytest's collection phase, blocking **all** pytest tests from running.

### Fixes Applied
- Added `app.config['WTF_CSRF_ENABLED'] = False` to test setup
- Replaced `→` with `->` (17 occurrences) and `⏱️` with `[timer]`
- Created `tests/conftest.py` with `collect_ignore = ['test_phase7.py']` to exclude standalone script from pytest collection

### Result
- `test_phase7.py`: 68/68 passed, 0 failed, 0 errors (was: 41 passed, 7 failed, 3 errors)
- pytest collection: no longer crashes on import

### Files Modified
- `tests/test_phase7.py` — CSRF config + Unicode fixes
- `tests/conftest.py` — NEW, pytest collection exclusion

---

## CL-TEAM — Full Product Team Governance System
**Completed:** 03-22-26 15:30:00 UTC

### Copilot-Instructions Expanded (`.github/copilot-instructions.md`)
- **Identity & Role rewritten** — Copilot is now the entire product team (CTO, PM, Product Owner, QA Lead, Security Officer, DevOps, Risk Manager) with responsibility table.
- **6 new governance sections added:**
  - SaaS-Ready Development Rules — dual-mode mandate, desktop isolation, adapter-first, query scoping, SQLite→PostgreSQL path
  - Product Thinking — feature-to-tier mapping, UX quality gate (5 checks), MVP discipline, "who pays?" test
  - QA Discipline — test-with-every-feature rule, regression check protocol, test naming convention
  - Security & Compliance — HIPAA scanning every session, auth pattern enforcement, dependency hygiene
  - Risk Register Protocol — maintained in PROJECT_STATUS.md, top 3 surfaced at session start, 4 risk categories
  - Strategic Decision Log — SD-xxx entries in CHANGE_LOG.md with context/decision/rationale/consequences format
- **Session Workflow upgraded** — now includes Risk Register check, HIPAA scan, and risk surfacing at session start.

### CareCompanion Agent (`.github/agents/CareCompanion.agent.md`)
- **Full rewrite from boilerplate** — autonomous agent with audit→plan→execute autopilot protocol.
- 4-phase mandatory workflow: Audit (7 steps) → Plan (6 steps) → Execute (5 steps) → Finalize (6 steps).
- "Plan only" override for when user wants review before execution.
- Tool access: vscode, execute, read, agent, edit, search, web, todo.

### Slash Commands Created (`.github/prompts/`)
- `/sprint-review` — PM: audit progress, verify Feature Registry, plan next steps
- `/security-audit` — Security: HIPAA + OWASP scan, auth gaps, dependency CVEs
- `/saas-check` — CTO: desktop boundary, tenant isolation, DB portability audit
- `/tech-debt` — CTO: dead code, duplication, pattern violations, coverage gaps
- `/test-plan` — QA: generate test plan for any feature/module
- `/risk-report` — Risk Manager: review/update Risk Register, assess blockers

### File-Scoped Instructions Created (`.github/instructions/`)
- `models.instructions.md` — soft-delete, user_id scoping, timestamps, exports
- `routes.instructions.md` — @login_required, JSON format, error handling, HIPAA
- `agent-boundary.instructions.md` — desktop-only imports, OCR-first, error handling
- `adapters.instructions.md` — BaseAdapter pattern, EHR-agnostic data, no desktop imports

### Other Files
- `.github/COMMANDS.md` — quick reference for all commands, agents, and auto-instructions
- `Documents/dev_guide/PROJECT_STATUS.md` — Risk Register added (R1–R7, 7 initial risks)

### File Count
- 14 files created/modified
- 0 files deleted

---

## CL-PM — Copilot Project Manager Upgrade
**Completed:** 03-22-26 UTC

### Changes to `.github/copilot-instructions.md`
- **Identity rewritten** — Copilot is now explicitly the project manager AND coder. Owns organization, discipline, and long-term codebase health.
- **Added "Project Manager Discipline" section** — Anti-sprawl enforcement (search before create, propose append, challenge multi-file creation), proactive cleanup duties, code quality gate checklist.
- **Workflow Rules strengthened** — Changelog/registry updates are mandatory after every code-changing prompt, not optional housekeeping. Timestamped format required (`MM-DD-YY HH:MM:SS UTC`).
- **Session Workflow hardened** — Start-of-session now scans for stale/orphaned issues. End-of-session updates are non-skippable. Added mid-session discipline (immediate changelog, pivot tracking, pattern detection).
- **Graduation Workflow** — Now explicitly automatic and timestamped when features complete.
- **Feature Registry** — Added "Completed Feature → Changelog Migration" template with exact format for entries.
- **Pushback behavior codified** — Copilot must resist unnecessary file creation and offer alternatives. Will comply if overruled but flags for future consolidation.

---

## CL-DOC — Dev Guide Consolidation & Governance System

**Date:** 2026-03-22

### Archived to `Documents/_archive/dev_guide_retired/`
- `FINAL_PLAN.md` — superseded by ACTIVE_PLAN.md
- `LLM_ABOUT.md` — content folded into init.prompt.md
- `PROMPTS.md` — one-time prompts, no longer needed
- `PRE_BETA_DEPLOYMENT_CHECKLIST.md` — completed, items in DEPLOYMENT_GUIDE
- `RESTART_INSTRUCTIONS.md` — folded into SETUP_GUIDE.md Troubleshooting section
- `REVIEW_2025_03_21.md` — snapshot review, historical only
- `RUNNING_PLAN.md` — completed, superseded by ACTIVE_PLAN.md
- `COPILOT_INSTRUCTIONS.md` — moved to `.github/copilot-instructions.md`
- `CHANGE_LOG.md` (dev_guide copy) — merged into main `Documents/CHANGE_LOG.md`

### Created / Moved
- `.github/copilot-instructions.md` — VS Code auto-reads this location. Contains all existing rules + 3 new sections: Document Management Rules (anti-sprawl whitelist, graduation workflow), Session Workflow (start/end protocol), Feature Registry Maintenance rules.
- `Documents/dev_guide/ACTIVE_PLAN.md` — renamed from `_ACTIVE_FINAL_PLAN.md`

### Modified
- `Documents/dev_guide/PROJECT_STATUS.md` — Added **Feature Registry** table (F1–F32, 30/32 complete, 1 blocked, 1 not started). Updated File Reference table to match new file locations.
- `Documents/dev_guide/CARECOMPANION_DEVELOPMENT_GUIDE.md` — Replaced stale Section 9 Master Build Checklist (~150 lines) with pointer to Feature Registry in PROJECT_STATUS.md.
- `Documents/dev_guide/SETUP_GUIDE.md` — Folded restart instructions into Troubleshooting section.
- `Documents/CHANGE_LOG.md` — Merged UI overhaul changelog content; added governance header.
- `init.prompt.md` — Updated Key Documents table (removed archived refs, added ACTIVE_PLAN, Copilot Instructions, Changelog).

### Result
- `Documents/dev_guide/`: **20 files → 11 files** (approved whitelist)
- Anti-sprawl system: Copilot enforces file whitelist, graduation workflow, session protocol
- Feature Registry: single source of truth for build/test/verification status

---

## Phase 44 — UI Overhaul (Sessions 1–3)

### Session 1 — CSS Foundation + Base Template Systems

**What was done:**

- **Phase 1A — CSS Foundation** (`static/css/main.css`)
  - Added `.has-subpanel` grid variant: `var(--sidebar-collapsed) 220px 1fr`, grid-areas `sidebar subpanel main`
  - Added `.context-panel` component: width 220px, bg-card, right border, padding 12px, overflow-y auto, 200ms transition
  - Added `.context-panel-header`, `.context-panel-section`, `.cp-section-label`, `.cp-stat`, `.cp-stat-value`
  - Added `.cp-link`, `.cp-link.active`, `.cp-filter`, `.cp-action`, `.cp-quick-nav`, `.cp-toggle`
  - Added `.subpanel-collapsed` (width 0, overflow hidden) and responsive hide below 768px

- **Phase 1B — Base Template** (`templates/base.html`)
  - Added `<aside class="context-panel" id="context-panel">{% block subpanel %}{% endblock %}</aside>` between sidebar and content header
  - Added sub-panel activation JS: detects `panel.innerHTML.trim().length > 0`, adds `.has-subpanel` to `.app-layout` (excludes dashboard)
  - Added collapse/expand toggle JS wired to `.cp-toggle` button; persists per-page via `localStorage['subpanel:{page_id}']`

- **Phase 1B2 — Popup Taskbar** (`templates/base.html`)
  - Added `#popup-taskbar` container (CSS: fixed bottom, flex row, aligned left of AI panel)
  - Added `ModalTaskbar` JS class: `minimize(modalEl)`, `restore(tabId)`, `close(tabId)`, `getLabel(modalEl)`
  - Rewired modal backdrop `click` handlers to call `ModalTaskbar.minimize()` instead of hiding directly
  - Added `data-blocking="true"` to `#hipaa-modal`, `#lock-overlay`, `#p1-modal-overlay`

- **Phase 2B — Breadcrumb Trail** (`static/css/main.css`, `templates/base.html`)
  - Added `.breadcrumb-trail`, `.breadcrumb-chip`, `.breadcrumb-chip.active`, `.bc-badge` CSS
  - Added `<nav class="breadcrumb-trail" id="breadcrumb-trail">` in base.html after bookmarks bar
  - Added breadcrumb JS: reads `sessionStorage['breadcrumbs']`, inserts current page, caps at 5, deduplicates
  - Templates set `{% block breadcrumb_badge %}` to provide contextual badge text

- **Phase 2C — Type-Ahead Filtering** (`static/css/main.css`, `templates/base.html`)
  - Added `.type-ahead-indicator` CSS (floating pill, shows current filter string)
  - Added keydown listener: captures printable keys when no input is focused, builds filter string
  - Hides `[data-filterable]` elements whose text doesn't match; Escape clears
  - `data-filterable` attribute already present on table rows/cards across all list pages

- **Phase 4A — Page Transitions** (`static/css/main.css`, `templates/base.html`, `templates/settings.html`)
  - Added `@keyframes` for fade, slide, zoom, subtle presets
  - Added transition loader JS: reads `localStorage['pageTransition']`, applies `.page-transition-{preset}` on `<html>`
  - Settings page has "Page Transitions" section with 5 preset buttons + live preview + `current_user.set_pref` save

---

### Session 2 — Sub-Panel Implementation (Batch 1: 5 pages)

**What was done:**

- **`templates/patient_roster.html`** — Added full `{% block subpanel %}`:
  - Search input (`id="cp-roster-search"`) wired to table type-ahead filter; syncs bidirectionally with `#roster-search`
  - Stats: Total Patients count
  - Quick Nav: Care Gaps, Lab Track, Timer
  - Content declutter: none needed (main search was inline already)

- **`templates/timer.html`** — Added full `{% block subpanel %}`:
  - 5-stat daily summary: Sessions, Total Time, Avg Duration, Total F2F, Complex
  - E&M Distribution mini-bar with color map
  - Export CSV as `cp-action` (`/timer/export`)
  - Quick Nav: Billing Tasks, Bonus Tracker, My Patients
  - Content declutter: Removed Export CSV button from content header

- **`templates/inbox.html`** — Added full `{% block subpanel %}`:
  - Views nav: Inbox / Held Items / Audit Log / Digest (with conditional `active` class based on `view` var)
  - Conditional snapshot stats section (Labs/Radiology/Messages/Refills/Other; only shown on main inbox view)
  - Quick Nav: Notifications, On-Call, Orders
  - Content declutter: Removed tab nav div; removed Snapshot Summary Card entirely

- **`templates/oncall.html`** — Upgraded existing partial sub-panel:
  - Actions: New Call (`cp-action`) + Handoff (`cp-action`)
  - Filter by Status: All / Pending / Entered / No Doc Needed + conditional Weekend Pending (active class on `status_filter`)
  - Stats: Pending count, Callbacks Due count
  - Quick Nav: Inbox, Notifications, My Patients (cleaned emoji from prior version)
  - Content declutter: Removed header with New Call/Handoff buttons; removed inline filter bar

- **`templates/orders.html`** — Upgraded existing partial sub-panel:
  - Views: My Sets / Community / Master List (active class based on `tab` var)
  - Actions: `<button onclick="openBuilder(null)">+ New Order Set</button>` (not a broken href)
  - Quick Nav: Lab Tracker, My Patients, Monitoring
  - Content declutter: Removed header with Master List + New Order Set buttons; removed My Sets/Community tab bar; fixed stray `</div>` artifact

---

### Session 3 — Sub-Panel Implementation (Batch 2: 5 pages + Batch 3: 6 pages, bug fixes)

**What was done:**

- **`templates/labtrack.html`** — Upgraded existing partial sub-panel:
  - Stats: Total Tracked, Patients, Overdue (red if >0), Critical (red if >0), Due Soon (warning if >0)
  - Quick Nav: Care Gaps, Monitoring, My Patients (cleaned emoji)
  - Content declutter: Removed 4-card stats grid; removed header with badges

- **`templates/caregap.html`** — Upgraded existing partial sub-panel:
  - Date navigation section: ← arrow / Today (active if is_today) / → arrow + view_date display
  - Stats: Open Gaps (red if >0), Patients Today count
  - Panel Report as `cp-action`
  - Quick Nav: Preventive Gaps, Lab Tracker, My Patients (cleaned emoji)
  - Content declutter: Removed date navigation div; removed header with gap badge and Panel Report button

- **`templates/bonus_dashboard.html`** — Upgraded existing partial sub-panel:
  - Stats: Receipts YTD, Threshold, Progress %, Gap, Days Remaining — all formatted with `"{:,.0f}".format()`
  - Quick Nav: Timer, Billing Tasks (`/billing/staff-tasks`), CCM Registry (`/ccm`) — fixed incorrect URLs
  - Content declutter: Removed quarter label span from content header

- **`templates/tcm_watch.html`** — Upgraded existing partial sub-panel:
  - Variables renamed to `active_sp`/`done_sp` to avoid Jinja block scope conflicts
  - Stats: Active Watch count, Completed count
  - Compact Quick-Add form (`id="tcm-sp-form"`, `id="tcm-sp-msg"`) wired to `/tcm/add-discharge` via fetch
  - Quick Nav: CCM Registry (`/ccm`), My Patients, Billing Tasks (`/billing/staff-tasks`) — fixed URLs
  - JS: Added `tcm-sp-form` submit handler after existing `tcm-add-form` handler

- **`templates/ccm_registry.html`** — Cleaned existing sub-panel:
  - Fixed Quick Nav: `/tcm` (was `/tcm/watch-list`), removed emoji
  - Content declutter: Removed 3-card stats grid (Active, Ready to Bill, Monthly Revenue) from content

- **`templates/monitoring_calendar.html`** — Upgraded existing sub-panel:
  - Added trigger filter select (All / Medication / Condition / REMS) to sub-panel
  - Added source filter select (All Sources / Manual / DailyMed / VSAC / REMS / RxClass / Drug@FDA / UpToDate / LLM Extracted) to sub-panel
  - Added Clear Filters link (conditional on active filters)
  - Cleaned emoji from Quick Nav links
  - Content declutter: Removed entire 4-card Summary Bar grid; removed entire Filter Bar form

- **`templates/care_gaps_preventive.html`** — Cleaned existing sub-panel:
  - Removed emoji from Actions and Quick Nav links
  - Content declutter: Removed Export CSV button from header; removed 4-card Summary Cards grid (stats are now only in sub-panel)

- **`templates/staff_billing_tasks.html`** — Upgraded existing sub-panel:
  - Replaced static role count list with clickable role filter buttons (`cp-filter` class, call `filterRole()` JS)
  - Cleaned emoji from Quick Nav links

- **`templates/notifications.html`** — Cleaned existing sub-panel:
  - Cleaned emoji from Quick Nav links
  - Removed dead `applyFilter()` JS function (type-filter select was moved to sub-panel)
  - Content declutter: Removed Mark All Read button from header; removed inline type-filter select + label

- **`templates/patient_chart.html`** — Cleaned existing sub-panel:
  - Removed emoji from all Chart Sections `cp-link` elements
  - Removed emoji from Actions `cp-action` button text
  - Cleaned Quick Nav emoji

- **`templates/admin_users.html`** — Verified `data-blocking="true"` already present on `#deact-modal` (line 333) ✓

- **`data-filterable` audit** — Verified attribute present across all required list pages:
  - `patient_roster.html`, `timer.html`, `inbox.html`, `oncall.html`, `orders.html`, `labtrack.html`, `caregap.html`, `care_gaps_preventive.html`, `ccm_registry.html`, `monitoring_calendar.html`, `notifications.html`, `staff_billing_tasks.html`, `tcm_watch.html`

**Bug fixed:**
- `templates/base.html` line 1091: `{% block subpanel %}` text inside a JS `/* comment */` was being parsed by Jinja2, causing "Unexpected end of template" errors on all pages. Replaced with plain text description of the block.

**Test results:** `127 passed, 0 failed, 0 errors`

---

## What Was NOT Done (Deferred / Requires Human Action)

### Systems 3–4 (Phase 3): Split View + Picture-in-Picture Widgets

**Why not implemented:**
- **Split View** (Steps 27-30) requires either: (a) iframes for full page isolation, creating session token issues with Flask-Login; or (b) server-side AJAX-rendered page fragments, requiring all 28+ routes to support a `?fragment=1` render mode. Neither is safe to implement without architectural decisions from the developer.
- **PiP Widgets** (Steps 31-34) requires cloning live DOM widgets and keeping them synchronized with page navigation. The existing `free_widgets.js` system uses a different persistence model. The pop-out/clone pattern needs the developer to audit which widgets are safe to clone (some fetch live data, others are Jinja-rendered once).

**What you need to do:**
1. Decide on Split View approach: iframe-based (simpler but same-origin required) or fragment-based (cleaner but requires route changes)
2. Add `data-pip="true"` and `data-pip-title="..."` to eligible patient chart widgets after reviewing which ones are safe to detach
3. Implement `PipManager` JS class — can follow the drag/resize pattern from `free_widgets.js`

### System 5 (Phase 2A): Smart Bookmarks Folders

**Why not implemented:**
- Existing bookmarks system (`/api/bookmarks/personal`) stores flat JSON arrays. Adding folder support requires a migration that changes the data schema. The developer should back up bookmark data before running.
- Drag-to-bookmark requires `draggable="true"` on all `<a>` elements, which may interfere with existing drag behaviors in order sets and free widgets.

**What you need to do:**
1. Run a migration for the bookmarks schema: wrap existing flat entries in `{ type: 'link', ... }` objects
2. Update `/api/bookmarks/personal` POST handler to accept folder-type entries
3. Implement drag-to-bookmark JS in `base.html` (Steps 36-37)

### System 9 (Phase 4B/4C): AI Enhancements

**Why not implemented:**
- AI writing assistant (Step 53-55) requires user API key management. The current AI panel uses a shared key from `config.py`. Per-user API keys need a new model field, an encrypted storage strategy (not plaintext in DB), and rate-limit tracking per user.
- Help popovers (Steps 56-58) require `help_guide.json` to have entries for all 9 new Phase 44 systems. The current file covers Phases 1-43.

**What you need to do:**
1. Add `ai_api_key` field to `User` model (store encrypted, decrypt at request time)
2. Add per-user `ai_rate_limit_hourly` and `ai_rate_limit_daily` preference keys to settings page
3. Add Phase 44 system entries to `data/help_guide.json`
4. Implement `.ai-assist-icon` placement on textareas/contenteditable fields

---

## Archived: UI Overhaul Detailed Log (formerly dev_guide/CHANGE_LOG.md)

> Merged from `Documents/dev_guide/CHANGE_LOG.md` on 2026-03-22 during doc consolidation.
> Tracks incremental bites taken from UI_OVERHAUL.md (Phase 44).

### Bite 1 — Phase 44 Foundation (Systems 1, 2, 6, 7, 8)

**Files Changed:** 20+ templates, main.css, base.html, auth.py, settings.html, admin_users.html

**Previously Implemented (Discovered on Audit):** Systems 1 (Context Sub-Panel CSS + JS), 2 (Popup Taskbar), 6 (Breadcrumb Trail), 7 (Type-Ahead Filter), 8 (Page Transitions) — all CSS foundations and base.html containers were already in place.

**Implemented This Bite:**
- Step 26: `data-blocking="true"` on 4 security modals (hipaa, lock, p1, deactivation)
- Phase 1C: Sub-panels on all 15 non-dashboard page templates
- Step 46: `data-filterable` attribute on 13 list templates
- Step 43: `data-breadcrumb-badge` on 4 pages (patient_chart, caregap, inbox, timer)
- Step 49: Page transitions settings UI (5 presets, API persist, server→localStorage sync)
- Bonus: `page_id` block on staff_billing_tasks.html

**Tests Created:** test_subpanel (18), test_popup_taskbar (10), test_breadcrumbs (10), test_type_ahead (16), test_transitions (12) — all passing.

**Deferred:** System 3 (Split View), System 4 (PiP), System 5 (Smart Bookmarks), System 9 (AI Enhancements)

### Bite 2 — Phase 44 Continuation (Systems 3, 4, 5, 9D)

**Files Changed:** base.html, main.css, auth.py, help.py, settings.html, patient_chart.html, labtrack.html, caregap.html, timer.html, notifications.html, help_guide.json

**Implemented:**
- System 3 (Split View): CSS, SplitViewManager JS, Ctrl+click interceptor, settings pane-count UI, API endpoint
- System 4 (PiP Widgets): CSS, PipManager JS, data-pip on patient_chart (21 widgets) + 4 additional templates
- System 5 (Smart Bookmarks with Folders): CSS, drag-to-bookmark JS, folder API endpoints, schema migration
- System 9D (Help Popovers): CSS, help-icon/popover elements, __npHelp preload, /api/help/items, 8 Phase 44 entries in help_guide.json

**Tests Created:** test_split_view (19), test_pip_widgets (20), test_bookmarks_folders (19), test_ai_enhancements (20) — all passing.

**Deferred:** System 9A (AI Workflow Coach), 9B (AI Natural Language Nav), 9C (AI Writing Assistant) — require encrypted API key storage.

---

## Dev Guide Consolidation — 2026-03-22

**What was done:**
- Archived 7 completed/obsolete files from `Documents/dev_guide/` to `Documents/_archive/dev_guide_retired/`: RUNNING_PLAN.md, REVIEW_2025_03_21.md, FINAL_PLAN.md, PRE_BETA_DEPLOYMENT_CHECKLIST.md, PROMPTS.md, RESTART_INSTRUCTIONS.md, LLM_ABOUT.md
- Merged two changelogs into single `Documents/CHANGE_LOG.md`
- Folded RESTART_INSTRUCTIONS content into SETUP_GUIDE.md Troubleshooting section
- Renamed `_ACTIVE_FINAL_PLAN.md` → `ACTIVE_PLAN.md`
- Created Feature Registry table in PROJECT_STATUS.md (F1–F32 + NEW features)
- Moved COPILOT_INSTRUCTIONS.md to `.github/copilot-instructions.md` with anti-sprawl rules, graduation workflow, session protocol, and Feature Registry maintenance instructions
- Removed stale Master Build Checklist (Section 9) from CARECOMPANION_DEVELOPMENT_GUIDE.md — replaced with pointer to Feature Registry
- Updated cross-references in init.prompt.md, PROJECT_STATUS.md
- dev_guide reduced from 20 files → 11 files

---

*Log maintained by GitHub Copilot. Last updated: 2026-03-22.*

# CareCompanion — Change Log

> **Single source of truth** for all development changes. Organized newest-first.
> Completed plan phases are "graduated" here from `Documents/dev_guide/ACTIVE_PLAN.md`.
> See `data/changelog.json` for the in-app user-facing changelog (separate concern).

---

## CL-M4 — JS Enhancement System (Phase M4)
**Completed:** 03-23-26 04:00:00 UTC

### 4 Init Functions Added to `static/js/main.js`
- **`initSortableHeaders()`** (L1962) — Click-to-sort on any `<th data-sort>`. Supports `data-sort-type="number"` and `data-sort-type="date"`. Shows `▲`/`▼` indicator. Replaces per-page inline `sortTable()` functions.
- **`initStatePersistence()`** (L2032) — `data-persist="key"` on `<select>` / `<input>` saves to sessionStorage scoped by page path. Restores on load + auto-submits forms.
- **`initCollapsible()`** (L2100) — `data-collapsible="id"` on heading toggles next sibling `.cc-collapsible-body` visibility. State stored in localStorage. Shows `▸`/`▾` prefix. Adds ARIA `aria-expanded`.
- **`initQuickActions()`** (L2139) — `data-quick-action="/url"` on buttons. POSTs to URL, accepts both `{success:true}` and `{ok:true}` response patterns. Supports `data-reload` (page refresh), `data-remove` (nearest `<tr>` removal), `data-confirm="msg"` (confirmation dialog).

### Pagination Macro
- Created `templates/_pagination.html` — `{% from '_pagination.html' import pagination %}` → `{{ pagination(page, total_pages) }}`. Outputs `.pagination` nav with first/prev/numbered/next/last links.

### CSS Additions (`static/css/main.css`)
- `.cc-collapsed + .cc-collapsible-body` / `.cc-collapsible-body.cc-collapsed` — hide collapsed sections.
- `.th[data-sort]` cursor + hover styles already existed from M2.

### Templates Wired
- **data-sort** on 6 tables: admin_audit_log, admin_practice, billing_log (8 cols), cs_tracker (8 cols), labtrack (5 cols), patient_roster (already had from prior work).
- **data-persist** on billing_log: 2 filter selects (level, anomaly).
- **data-collapsible**: admin_dashboard "Admin Tools" heading + all 8 settings.html sections (Profile, Credentials, Notifications, CS Import, Appearance, Billing Intelligence, Clinical Intelligence, Feature Level) — each wrapped in `<div class="cc-collapsible-body">`.
- **data-quick-action**: notifications.html "Mark All Read" button (replaced inline `markAllRead()` function).

### Files Modified
- `static/js/main.js` — 4 new init functions + DOMContentLoaded calls
- `static/css/main.css` — collapsible CSS
- `templates/_pagination.html` — NEW (Jinja macro)
- `templates/admin_audit_log.html` — data-sort on 5 columns
- `templates/admin_practice.html` — data-sort on 7 columns
- `templates/admin_dashboard.html` — data-collapsible on section heading
- `templates/billing_log.html` — data-sort on 8 columns + data-persist on 2 selects
- `templates/cs_tracker.html` — data-sort on 8 columns
- `templates/labtrack.html` — data-sort on 5 columns
- `templates/settings.html` — data-collapsible on 8 sections + 16 cc-collapsible-body wrappers
- `templates/notifications.html` — data-quick-action on Mark All Read button

---

## CL-M3 — Secondary Template CSS Cleanup (Phase M3)
**Completed:** 06-10-25 02:30:00 UTC

### Page Header Migration (25 templates)
- Converted all admin templates (15), billing templates (5), clinical tools (7), and settings (4) from inline `style="display:flex;..."` header patterns to `.page-header` / `.page-header__title` / `.page-header__actions` classes.
- Skipped standalone print pages (billing_log_export, reportable_diseases_reference, rems_reference), auth pages (login, register — use `.auth-card` pattern), and wizard pages (onboarding).

### Table Class Migration
- Fixed `class="table"` → `class="data-table"` in billing_opportunity_report.html (2 tables).
- All admin table migrations completed in prior session.

### Modal Migration to `.cc-modal` (6 modals across 4 files)
- **admin_users.html**: Deactivation modal → `.cc-modal--sm`, Send Notification modal → `.cc-modal--md`. Updated all JS to use `classList.add/remove('cc-modal--open')`.
- **cs_tracker.html**: Add Entry modal → `.cc-modal--md`.
- **dot_phrases.html**: Add/Edit Phrase modal → `.cc-modal--md`, Import modal → `.cc-modal--sm`.
- **phrase_settings.html**: Edit Documentation Phrase modal → `.cc-modal--md`.

### Admin Dashboard Deep Cleanup
- Replaced 11 tool card inline styles (`text-decoration:none;color:inherit;` + `display:flex;...` + `font-weight:600;font-size:15px;`) with `.admin-tool-link` / `.admin-tool-link__title` / `.admin-tool-link__desc` classes.
- Stat card: inline `font-size:24px;font-weight:700;` → `.stat-value.stat-value--md`, inline desc → `.stat-label`.
- Section heading: inline uppercase styled `<h2>` → `.section-heading` class.
- admin_users.html: expand rows (reset PW, username, PIN) migrated from inline `background:var(--color-lt-*)` to `.expand-row--yellow/blue/green` classes. Role change form → `.form-inline`. Password input → `.form-input--auto`.

### Settings Page Cleanup
- All 8 section headings in settings.html migrated from inline `font-size:16px;color:var(--text-secondary);text-transform:uppercase;...` to `.section-heading` class.

### New CSS Classes Added to main.css
- `.page-header__back` — back link styling for page headers
- `.section-heading` — uppercase secondary heading for card grid sections
- (Prior session added: `.mono`, `.badge--muted`, `.admin-tool-link`, `.form-inline`, `.form-input--auto`, `.expand-row` variants)

### Files Modified
- `static/css/main.css` — added `.page-header__back`, `.section-heading`
- 15 admin templates, 5 billing templates, 7 clinical tools templates, 4 settings templates (31 total)

---

## CL-PURGE — Admin Purge & Reimport XML Test Patients
**Completed:** 06-08-25 05:15:00 UTC

- Added `POST /admin/tools/purge-reimport-xml` endpoint that: (1) deletes all patient clinical data for the current user (medications, diagnoses, allergies, immunizations, vitals, labs, encounter notes, social history, patient records), (2) re-imports every XML file from `Documents/xml_test_patients/`.
- Added "Purge & Reimport XML Patients" card to Admin Tools page with confirmation dialog.
- XML files on disk are never deleted — only DB rows are purged and re-created.
- Files modified: `routes/admin.py`, `templates/admin_tools.html`

---

## CL-XML7 — Rich Test Patient XMLs, Prior Notes Widget, Full MRN Display
**Completed:** 06-08-25 04:30:00 UTC

### 7 Rich Test Patient XML Files Generated
- **31306 — Margaret Thompson, 72F**: Medicare AWV/CCM candidate. HTN, DM2, CKD3, osteoporosis, depression, obesity. 10 medications, 18 lab results, 4 encounter notes (including AWV and acute UTI visit).
- **43461 — Marcus Williams, 32M**: Psych/behavioral health. Bipolar II, ADHD, GAD, tobacco abuse, insomnia. 9 medications, 9 labs. Nicotine cessation in progress. CCM candidate.
- **45534 — Robert Chen, 55M**: Metabolic syndrome, ASCVD risk. HTN, hyperlipidemia, prediabetes, morbid obesity, OSA, BPH. Former 30-pack-year smoker — LDCT eligible. 15 labs, 3 encounter notes.
- **62602 — Kristy Anderson, 42F**: Post-hospital discharge TCM candidate. CAP, asthma, iron deficiency anemia, B12 deficiency. 14 labs, 3 notes including TCM 99496 follow-up.
- **62815 — Demo Testpatient, 45F**: Core test patient. DM2, HTN, hyperlipidemia, neuropathy, COVID resolved. 14 labs, 3 notes including AWV and Paxlovid acute visit.
- **62816 — Tyler Johnson, 8M**: Pediatric well-child. ADHD, asthma, eczema, peanut allergy, obesity. 6 labs, 2 notes (well-child + ADHD eval).
- **63039 — Sarah Mitchell, 46F**: Chronic pain + mental health. Fibromyalgia, depression, anxiety, migraine, prediabetes. 17 labs, multiple care gaps (flu/COVID/Tdap overdue, mammogram due).
- Generator script: `scripts/generate_test_xmls.py`
- Files stored in: `Documents/xml_test_patients/`

### Prior Notes Widget Added to Patient Chart
- New model: `PatientEncounterNote` (date, provider, note type, text, location)
- Migration: `migrations/migrate_add_encounter_notes.py`
- Parser updated: LOINC 11506-3 section extracted and stored
- Patient chart: collapsible cards with date/provider/type/text, type filter dropdown
- Sidebar navigation link added

### Full MRN Display — Reversed All Masking
- **15 template files** updated: removed `mrn[-4:]` masking, now show full MRN
- **7 route files** updated: caregap, dashboard, intelligence, labtrack, monitoring, patient, timer
- **4 model files** updated: patient.py, labtrack.py, tools.py, timelog.py
- **1 service file** updated: api_scheduler.py
- **1 agent file** updated: mrn_reader.py
- **5 instruction/guide files** updated: copilot-instructions.md, CareCompanion.agent.md, routes.instructions.md, security-audit.prompt.md, init.prompt.md
- Logger calls intentionally kept masked (HIPAA log safety)

---

## CL-UIA1 — AC Automation Upgrade: UIA + Win32 Message Infrastructure
**Completed:** 03-24-26 20:00:00 UTC
- **New module: `agent/uia_probe.py`** — Diagnostic script that connects to Amazing Charts via pywinauto UIA/Win32 backends and dumps the full control tree (AutomationId, ClassName, Name, ControlType, rect) to `data/uia_dumps/` as JSON + human-readable text. Supports `--depth`, `--output`, `--backend` args. Run with AC at different states to discover UIA-accessible controls.
- **New module: `agent/uia_helpers.py`** — UIA element finding layer. `get_uia_app()` (cached connection), `uia_find_control()` (by name/automation_id/control_type/class_name with timeout), `uia_find_all()`, `uia_find_menu_item()` (walk menu tree), `uia_get_text()` (ValuePattern → window_text → Name), `uia_wait_for_control()`, `uia_get_children_text()`, `uia_get_control_rect()`. Mock mode support throughout.
- **New module: `agent/win32_actions.py`** — Win32 message action layer. `send_click()` (WM_LBUTTONDOWN/UP to hwnd, no foreground required), `send_click_to_control()` (UIA rect → client coords → Win32 message), `send_key()` (WM_KEYDOWN/UP), `send_text()` (WM_CHAR loop), `send_text_to_control()` (tries ValuePattern → WM_SETTEXT → WM_CHAR → type_keys), `get_window_text()` (WM_GETTEXT), `send_menu_command()` (WM_COMMAND). All VK constants included. Mock mode support throughout. HIPAA: typed text never logged.
- **New module: `agent/ac_interact.py`** — Smart 3-tier interaction layer. `smart_find_and_click()` (UIA → OCR → coordinates), `smart_read_text()` (UIA → OCR), `smart_type_text()` (UIA → OCR → coordinates), `smart_navigate_menu()` (UIA → OCR → coordinates). Returns `{"success": bool, "tier": str, "method": str}` for observability.
- **Config additions:** `AC_USE_UIA = True`, `AC_INTERACTION_TIER = 'uia_first'`, `AC_UIA_TIMEOUT = 1.5` in config.py.
- **Agent boundary update:** Added `pywinauto`, `comtypes`, `win32api` to allowed imports. Updated AC automation section with 3-tier guidance and UIA interaction rules.
- **Dependency:** `pywinauto==0.6.8` added to requirements.txt (installs `comtypes` automatically).
- Files added: `agent/uia_probe.py`, `agent/uia_helpers.py`, `agent/win32_actions.py`, `agent/ac_interact.py`
- Files modified: `config.py`, `requirements.txt`, `.github/instructions/agent-boundary.instructions.md`
- **Next:** Run `uia_probe.py` with AC open to assess UIA tree richness (blocking gate for migration).

---

## CL-M2 — UI System Review: Phase M2 High-Frequency Template Cleanup
**Completed:** 03-24-26 06:30:00 UTC
- **New CSS primitives** — `.stat-grid`, `.stat-grid--auto`, `.stat-block`, `.stat-value` (28px/24px/20px variants), `.stat-label`, `.kv-label`, `.kv-value` for summary metrics and key-value pairs.
- **Inbox** (M2.3) — Page header→`.page-header`, 6 digest stats→`.stat-grid/.stat-block/.stat-value`, current totals→`.stat-value--sm`, 4 tables `class="table"`→`data-table data-table--striped`, audit header→`.action-bar`, filter form→`.form-row`. ~30 inline styles removed.
- **Timer** (M2.4) — Page header→`.page-header`, active session kv pairs→`.kv-label/.kv-value`, 5 daily stats→`.stat-grid--auto/.stat-block/.stat-value--md`, E&M result→`.stat-value/.stat-label`, session table→`.data-table--striped.data-table--compact`. ~25 inline styles removed.
- **Billing Review** (M2.5) — Page header→`.page-header` with `.page-header__subtitle/.page-header__actions`, table→`.data-table--striped`, benchmark spinner→`.loading-spinner/.widget-loading`. ~8 inline styles removed.
- **Patient Roster** (M2.6) — Page header→`.page-header`, table→`.data-table--striped`, MRN cells→`.mono`. ~5 inline styles removed.
- **Care Gaps** (M2.7) — Documentation snippet modal (F15b) converted from inline `position:fixed` divs→`.cc-modal/.cc-modal__dialog--sm` with proper header/body/footer. JS updated for single-overlay pattern. Page header→`.page-header`. ~12 inline styles removed.
- **On-Call** (M2.8) — 5 inline status badges (pending/entered/no-doc/callback/forwarded) with repeated `padding:2px 8px;border-radius:12px;font-size:11px;background:...;color:...`→semantic `.badge--error/.badge--success/.badge--muted/.badge--warning/.badge--info`. Page header→`.page-header`. ~15 inline styles removed.
- **Note:** M2.1 (Dashboard) and M2.2 (Patient Chart) were completed in the prior session.
- Files modified: `static/css/main.css`, `templates/inbox.html`, `templates/timer.html`, `templates/billing_review.html`, `templates/patient_roster.html`, `templates/caregap.html`, `templates/oncall.html`
- Tests: 93/93 passing

---

## CL-M1 — UI System Review: Phase M1 CSS Foundation
**Completed:** 03-23-26 22:00:00 UTC
- **`.schedule-table` → `.data-table` rename** — Primary table component renamed across CSS (16 rules) and all 15 templates (29 class occurrences). `.schedule-table` kept as deprecated alias for back-compat.
- **Table modifiers added** — `.data-table--striped` (alternating row backgrounds), `.data-table--compact` (6px/8px padding, 12px font), sortable column header styles (`th[data-sort]` with directional arrows).
- **Unified status system** — `.status--critical`, `.status--warning`, `.status--success`, `.status--info`, `.status--muted` classes with `--status-color` / `--status-bg` CSS custom properties. Status-aware row tints for data tables. `.status-dot` indicator primitive.
- **`.page-header` + `.action-bar`** — Standardized page title bar (flex, title + actions) and grouped button row (flex, end-aligned). Size/alignment variants included.
- **`.cc-modal` system** — Unified modal overlay with `.cc-modal__dialog` (sm/md/lg/xl sizes), header, body, footer sections, close button, dark mode support, zoom-in animation. Replaces ad-hoc `position:fixed` modal divs.
- **Badge deprecation** — `.badge-success` etc. (single-dash) marked as deprecated with comment; canonical form is `.badge--success` (double-dash).
- **Utility class: `.sticky-top`** — `position:sticky; top:0; z-index:10`.
- Files modified: `static/css/main.css`, 15 templates (admin_api, admin_dismissal_audit, admin_netpractice, admin_practice, api_setup_guide, billing_review, caregap, caregap_outreach, caregap_panel, cs_tracker, dashboard, medref_review, pa, patient_roster, referral, result_template_library)
- Tests: 93/93 passing, 0 CSS errors

---

## CL-UX-OVERHAUL — UX/Usability Improvements: Full Audit Implementation
**Completed:** 03-24-26 04:30:00 UTC
- **Global double-submit protection** — added `initDoubleSubmitGuard()` in main.js: every POST form submit disables the button and dims it; re-enables after 5s safety net. Covers all 102 POST forms app-wide.
- **Global 401 session interceptor** — added `initFetchInterceptor()` in main.js: monkey-patches `window.fetch` to detect 401 responses, shows error toast, and redirects to login after 2s. Prevents silent session death.
- **Modal focus trapping + Escape** — added `initModalAccessibility()` in main.js: traps Tab focus inside visible modals/overlays, Escape key closes topmost modal. WCAG 2.4.3 compliance.
- **8 silent fetch errors fixed** — patient_chart.html: `toggleDxCategory`, `toggleItemStatus`, `removeDiagnosis`, `claimPatient`, `saveDemographics`, `saveWidgetLayout`, `saveSpecialist`, `deleteSpecialist` all now have `.catch()` with `showError()` toast.
- **Autofocus on 9 form pages** — patient_roster, message_new, oncall_new, labtrack, orders_master, dot_phrases, macros, register, settings all now autofocus the primary input.
- **Empty state improvements** — dashboard schedule shows `empty_state()` macro when 0 appointments; patient_chart care gaps shows "All care gaps addressed" when all resolved.
- **.btn-close CSS class** — reusable close/dismiss button class replacing 8+ repeated inline styles.
- **cmd-palette focus fix** — `.cmd-palette-input:focus` now has `box-shadow` inset ring, fixing WCAG focus suppression violation.
- **Input type fixes** — `pa.html` payer phone → `type="tel"`, `patient_chart.html` specialist phone/fax → `type="tel"`.
- **Status dot accessibility** — agent + NetPractice status dots now have `role="status"` + `aria-label` synced with title on every poll update.
- **12 clickable elements fixed** — added `role="button" tabindex="0"` to 3 dashboard tier headers, 3 patient_chart badge-toggles, 4 risk cards, 1 timer AWV header, 1 labtrack row.
- **Back navigation** — oncall_new.html and billing_log.html now have back links.
- **Table CSS standardization** — bare `<table>` elements inside card-body/main-area now get default styling (border, padding, hover, sticky headers).
- **Loading indicator system** — new `.loading-spinner`, `.btn--loading` CSS classes + `fetchWithLoading()` JS helper in error-handler.js for reusable async button states.
- Files modified: `static/js/main.js`, `static/js/error-handler.js`, `static/css/main.css`, `templates/patient_chart.html`, `templates/dashboard.html`, `templates/base.html`, `templates/patient_roster.html`, `templates/message_new.html`, `templates/oncall_new.html`, `templates/labtrack.html`, `templates/orders_master.html`, `templates/dot_phrases.html`, `templates/macros.html`, `templates/register.html`, `templates/settings.html`, `templates/timer.html`, `templates/billing_log.html`, `templates/pa.html`
- 93/93 tests pass

---

## CL-HIPAA-AUDIT2 — Proactive HIPAA/Security Audit: MRN Masking + PHI Logging Fixes
**Completed:** 03-24-26 02:00:00 UTC
- **Full 5-category audit** — scanned all routes, templates, models, and scrapers for: missing `@login_required`, full MRN exposure, hard-deletes on clinical records, missing `user_id` scoping, and PHI in logging.
- **CRITICAL: 3 MRN exposures fixed** — `billing_why_not.html` displayed full MRN as bold text; `patient_risk_tools.html` displayed full MRN in page badge AND browser tab title. All converted to `••{{ mrn[-4:] }}`.
- **HIGH: PHI logging fixed** — `scrapers/netpractice.py` logged patient full name + full MRN to production log file; now logs masked MRN (`••last4`) with SHA-256 hash prefix. Error handler also anonymized.
- **MEDIUM: Model repr fixed** — `models/tools.py` `CSEntry.__repr__` exposed full MRN; now uses `••last4`.
- **MEDIUM: JSON error fixed** — `routes/dashboard.py` duplicate-appointment error response included full MRN; now masked.
- **Assessed as acceptable**: `OrderSet`/`OrderItem`/`MasterOrder` hard-deletes (user templates, not clinical records); `Schedule` hard-delete (scheduling data, not clinical); `TimeLog` manual-entry delete (gated to manually-created entries only); `DocumentationPhrase` user_id scoping (shared reference data, not per-user); `/timer/face/room-toggle` without `@login_required` (POST counterpart to exempted room-widget, used from unauthenticated exam-room tablet).
- Files modified: `templates/billing_why_not.html`, `templates/patient_risk_tools.html`, `scrapers/netpractice.py`, `models/tools.py`, `routes/dashboard.py`
- 93/93 tests pass

---

## CL-FREE-MODE — Free Mode Widget Layout: Complete Overhaul
**Completed:** 03-23-26 01:30:00 UTC
- **Grid snapshot on Free click** — `setLayout('free')` now captures every widget's pixel position via `getBoundingClientRect()` while still in grid mode, then applies those exact positions as absolute coordinates. Clicking "Free" produces zero visual change; widgets only move when the user drags or resizes them.
- **Explicit height always set** — free mode widgets always get an explicit `height` (from saved positions, grid snapshot, or 300px fallback). Fixes the "thin strip" rendering bug where `position: absolute` widgets collapsed with no height.
- **Full overlap resolution** — replaced `_reflowBelow()` (same-column only, 50px threshold) with `_resolveOverlaps()` which checks all widget pairs for bounding-box overlap across up to 3 passes. Triggered on drag end, resize end, and size preset changes. Widgets push downward with smooth 200ms animation.
- **Reset clears server positions** — `resetLayout()` now POSTs empty positions to server (was localStorage-only). Switches to grid first, then re-snapshots fresh layout to free mode.
- **Size presets now resolve overlaps** — Small/Medium/Large preset buttons trigger overlap resolution after resizing, preventing widgets from stacking.
- Files modified: `static/js/free_widgets.js`
- 93/93 tests pass

---

## CL-DX-REVENUE — ICD-10 Revenue Optimization Suggestions in Billing Widget
**Completed:** 03-24-26 00:15:00 UTC
- **New feature**: Billing widget now shows "Dx Code Optimization" section suggesting same-family ICD-10 codes with higher per-encounter revenue based on practice historical data
- **Revenue CSV loader** — `billing_engine/utils.py` gains `get_icd10_revenue()` and `find_revenue_alternatives()` functions that parse `Documents/billing_resources/calendar_year_dx_revenue_priority_icd10.csv` (52 codes, lazy-loaded)
- **Safety guardrails**: Only suggests codes within the same 3-character ICD-10 family (e.g. E78.xx stays in E78). Z-codes excluded entirely. Shows "Verify clinical appropriateness" disclaimer. Never suggests cross-family codes.
- **New API endpoint**: `GET /api/patient/<mrn>/dx-revenue-suggestions` returns up to 3 same-family alternatives per active diagnosis, sorted by revenue delta
- **UI**: Gold-bordered cards in billing widget showing current code → alternatives with +$X/visit delta. Loads async after billing opportunities.
- Files modified: `billing_engine/utils.py`, `routes/intelligence.py`, `templates/patient_chart.html` (JS loader + CSS)
- 93/93 tests pass

---

## CL-MED-TABLE — Medication Widget: Generic-First Display, Frequency Standardization, No-Scroll Layout
**Completed:** 03-23-26 23:45:00 UTC
- **Generic name is now the primary display** — shown as linked text (UpToDate search), brand name appears as parenthetical hint + full tooltip on hover. Merged old "Drug Name" + "Generic" columns into single "Medication" column.
- **Frequency standardized** — new `_standardize_frequency()` function normalizes free-text instructions (e.g. "take 1 tablet by mouth once daily" → "Daily", "every 8 hours" → "Q8H", "twice daily" → "BID"). Raw text preserved as hover tooltip. Covers QID/TID/BID/Daily/QOD/Weekly/BIW/Monthly/QnH/QnD/QnW/QnM/QHS/PRN/QAM/QPM patterns.
- **No horizontal scroll** — medication table uses `table-layout: fixed` with percentage column widths (42/22/14/14/8%). Widget-body changed from `overflow:auto` to `overflow-x:hidden;overflow-y:auto` globally.
- **Dose never wraps** — `.med-dose-cell` has `white-space:nowrap` with overflow ellipsis.
- Files modified: `routes/patient.py` (added `_standardize_frequency()`, updated `_enrich_medications()`), `templates/patient_chart.html` (table restructure + CSS)
- 93/93 tests pass

## CL-SCHED-DRAGDROP — Fix: Drag Patient from My Patients Panel to Schedule Slot
**Completed:** 03-23-26 23:30:00 UTC
- **My Patients panel rows are now draggable** — `draggable="true"` + `ondragstart` stores patient JSON (name, MRN, DOB) via `application/patient` MIME type
- **`dropOnSlot()` now handles two drop types**: existing appointment move (reads `text/plain` appt ID → PUT `/api/schedule/{id}/move`) and new patient drop (reads `application/patient` JSON → POST `/api/schedule/add`)
- File modified: `templates/dashboard.html`
- 93/93 tests pass

---

## CL-SESSION-FIX — Critical: SECRET_KEY Regeneration Causing Session Loss
**Completed:** 03-23-26 23:15:00 UTC
- **Root cause:** `SECRET_KEY = secrets.token_hex(32)` generated a new random key every app start, invalidating all Flask session cookies and forcing re-login on every restart/reload
- **Fix:** SECRET_KEY now persisted to `data/.secret_key` file. Generated once, reused on all subsequent starts. Env var `SECRET_KEY` still takes priority if set.
- **Impact:** All sidebar navigation and page clicks were redirecting to login screen despite valid credentials
- File modified: `config.py`
- File created: `data/.secret_key` (auto-generated, gitignored via `data/`)
- 93/93 tests pass — no regressions

---

## CL-SCHED-SLOTS — Schedule 15-Min Slots, Drag-Drop, Configurable Hours + Orders & Care Gaps
**Completed:** 03-23-26 19:45:00 UTC
- **Schedule now shows every 15-min slot** from 07:00–19:00 (default), even if empty — full day grid
- **User-configurable schedule hours** — ⚙ gear button opens modal to set start/end hour, saved to user preferences via `User.set_pref()`
- **Drag-and-drop in table view** — appointment rows are draggable, can be dropped on any empty slot to move them
- **Grid view** reads start/end hours from user preferences (data attributes on container)
- **Sticky table header** + scrollable body (max 600px) for long schedule
- **Empty slots** styled with lighter text, compact height; filled slots show full appointment details
- **Orders page** — added prominent "+ New Order Set" button in main content header (was sidebar-only)
- **Care Gap Monitoring** redesigned:
  - Reduced Scheduled Patients table from 6 columns to 4: Time, Patient (with MRN + visit type inline), Care Gaps, Actions
  - Reduced Unscheduled table from 4 columns to 3: Patient (with MRN inline), Open Gaps, Actions
  - Gap count badges now show **hover tooltip** listing all gap names + descriptions (supports USPSTF recommendations, not just labs)
  - Standardized row spacing with dedicated `.caregap-table` CSS class (10px/12px padding, consistent vertical alignment)
- Files modified: `routes/dashboard.py`, `templates/dashboard.html`, `static/js/schedule_grid.js`, `templates/orders.html`, `templates/caregap.html`
- 93/93 tests pass — no regressions

---

## CL-DASH-POLISH — Dashboard Visual Polish (UI_REFACTOR_PHASE_DASHBOARD)
**Completed:** 03-23-26 22:30:00 UTC
- **TCM alert bar** tightened: reduced padding ~30%, smaller icon, compact text, renamed "View TCM Watch" → "Review TCM →" CTA button. Moved inline styles → `.tcm-alert-bar`, `.tcm-alert-icon`, `.tcm-alert-cta` classes.
- **Schedule table typography hierarchy**: patient names bold (`.sched-patient-name`), DOB dimmed 11px (`.sched-patient-dob`), reason column muted (`.sched-reason`). Added `.schedule-table--dashboard` modifier. Patient link hover transitions to teal.
- **My Patients panel** visual weight reduced: smaller header (13px), `.schedule-table--secondary` modifier with 12px body text, muted data columns, primary color only on patient name column. Badge changed from `badge--info` → `badge--muted`.
- **Delete button** converted to `.btn-icon` (icon-only, no text padding). Column header changed to 🗑 icon with tooltip.
- All new styles use CSS custom properties — **dark mode compatible with zero overrides needed**.
- Files modified: `templates/dashboard.html`, `static/css/main.css`
- 93/93 tests pass — no regressions

---

## CL-SCHED-REDESIGN — Dashboard Schedule Table Redesign & Delete Workflow
**Completed:** 03-23-26 19:00:00 UTC
- **Schedule table simplified** from 10 columns to 6: Time, Patient (First Last (DOB)), Reason, Care Gaps ✅, Billing ✅, Delete 🗑
- Patient name column converts "LAST, FIRST" → "First Last (MM/DD/YYYY)" format
- Gaps & Billing columns show ✅ checkmarks (linked to detail pages) instead of count badges
- **Delete now works for all appointments** — removed `entered_by == 'manual'` restriction
- **Delete confirmation modal** with two options:
  - 🗑 "Delete everything" — removes appointment + prepped billing work
  - 💾 "Save prepped work" — removes from schedule but keeps billing data for revisit
- Files modified: `templates/dashboard.html`, `routes/dashboard.py`
- 93/93 tests pass — no regressions

---

## CL-HIPAA-AUDIT2 — HIPAA Compliance Audit: 12 PHI Leak Fixes
**Completed:** 03-23-26 18:15:00 UTC
- **3 template MRN display violations fixed:**
  - `patient_roster.html` — `{{ p.mrn }}` → `••{{ p.mrn[-4:] }}`
  - `billing_review.html` — `(MRN: {{ mrn }})` → `(MRN: ••{{ mrn[-4:] }})`
  - `patient_gen.html` — JS `escHtml(p.mrn)` → `'••' + escHtml(p.mrn.slice(-4))`
- **5 route logging violations fixed** (full MRN in logger.debug/error):
  - `routes/patient.py` — 2 sites: care gap eval + bulk pricing
  - `routes/monitoring.py` — 1 site: clinical scoring
  - `routes/intelligence.py` — 2 sites: VIIS lookup + PDMP lookup
- **3 agent print violations fixed** (full MRN/DOB in calibration prints):
  - `agent/mrn_reader.py` — MRN, DOB, and OCR fallback MRN all masked
- **1 Pushover PHI violation fixed:**
  - `agent/notifier.py` — Callback reminder stripped patient_identifier from external message

### Files Modified
- `templates/patient_roster.html` — MRN masked
- `templates/billing_review.html` — MRN masked
- `templates/patient_gen.html` — MRN masked (JS)
- `routes/patient.py` — 2 logger calls masked to last-4
- `routes/monitoring.py` — 1 logger call masked to last-4
- `routes/intelligence.py` — 2 logger calls masked to last-4
- `agent/mrn_reader.py` — 3 print statements masked
- `agent/notifier.py` — Callback notification uses count-only message

---

## CL-MIG-RECURSION — Fix Migration Infinite Recursion Bug
**Completed:** 03-23-26 17:30:00 UTC
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

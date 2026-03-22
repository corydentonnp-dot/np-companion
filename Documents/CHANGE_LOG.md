# CareCompanion — Change Log

> **Single source of truth** for all development changes. Organized newest-first.
> Completed plan phases are "graduated" here from `Documents/dev_guide/ACTIVE_PLAN.md`.
> See `data/changelog.json` for the in-app user-facing changelog (separate concern).

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

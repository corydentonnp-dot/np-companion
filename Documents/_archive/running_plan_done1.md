# Running Plan: Phase 2 — Full Feature Build-Out

> **Status**: COMPLETE ✅
> **Last updated**: 2026-03-19
> **Scope**: All undeveloped, bugged, or missing features — AC-blocked features excluded
> **Final test results**: 46/46 checks passing | 59 database tables | 0 errors

---

## Phase 1 — Bug Fixes & Technical Debt

- [x] **1.1** Fix dead code in `routes/metrics.py` line 476 — delete unreachable duplicate `return jsonify(_oncall_weekly_stats(current_user.id))` after the real return on line 475 ✅ *Done — deleted unreachable line 476*
- [x] **1.2** Verify `agent/notifier.py` imports — confirm whether `timedelta` is used anywhere in the file; if so, add it to the `from datetime import datetime, timezone` on line 15 ✅ *Done — `timedelta` is NOT used anywhere in notifier.py; no change needed*
- [x] **1.3** Fix `CacheManager` deprecated `db.engine.execute()` calls in `app/services/api/cache_manager.py` — replace with `db.session.execute(text(...))` pattern (6 call sites: `_ensure_table`, `get`, `set`, `delete`, `flush_api`, `get_stats`, `get_all_api_stats`) ✅ *Done — all 8 calls converted to `db.session.execute(text(...))` with named params + commit(); added `from sqlalchemy import text` import*
- [x] **1.4** Fix `BaseAPIClient._get()` — same `db.engine.execute` deprecation flows through CacheManager ✅ *Done — BaseAPIClient delegates to CacheManager which is now fixed; no direct engine.execute calls in base_client.py*
- [x] **1.5** Investigate `/metrics` template render error ("unexpected '>'") — no Jinja2 syntax issue found in template; likely a runtime data/context issue. Check `routes/metrics.py` return dict for missing keys that templates reference. ✅ *Done — ROOT CAUSE FOUND: `templates/metrics.html` line 19 had `{% include '_free_widgets.html' %>` (angle bracket) instead of `{% include '_free_widgets.html' %}` (curly brace). Fixed; /metrics now passes test suite (was the 1 error in prior test run).*
- [x] **1.6** Search codebase for any remaining `Query.get()` deprecation sites and fix to `db.session.get()` ✅ *Done — found and fixed 10 sites: pyautogui_runner.py (1), netpractice.py (1, added db import), auth.py (1), oncall.py (1), patient.py (3), test_phase7.py (3). All converted to `db.session.get(Model, id)`.*

**Phase 1 test results**: `python test.py` → **37 passed, 0 failed, 0 errors** (previously 36 passed + 1 error on /metrics)

---

## Phase 2 — Delayed Message System (F18)

**Context**: `models/message.py` has complete `DelayedMessage` model (user_id, recipient_identifier, message_content, scheduled_send_at, status, sent_at, delivery_confirmed). No routes or templates exist.

- [x] **2.1** Create `routes/message.py` — new blueprint `message_bp` with prefix `/messages`
  - `GET /messages` — list view (pending tab + sent/history tab)
  - `GET /messages/new` — compose form
  - `POST /messages` — create new delayed message (validate scheduled_send_at is future)
  - `POST /messages/<id>/cancel` — cancel pending message (set status='cancelled')
  - `GET /api/messages/pending` — JSON endpoint for agent to poll
  - `POST /api/messages/<id>/mark-sent` — agent marks as sent
  ✅ *Done — routes/message.py created with all 6 endpoints*
- [x] **2.2** Create `templates/messages.html` — two-tab layout (Pending Queue | Sent History), table rows with status badges, cancel button for pending items ✅ *Done — tabbed layout with pending queue and sent/cancelled history tables*
- [x] **2.3** Create `templates/message_new.html` — compose form: recipient field, message content textarea, datetime picker for scheduled_send_at, submit button ✅ *Done — compose form with all fields and validation*
- [x] **2.4** Register `message_bp` in `app/__init__.py` `_register_blueprints()` — add `('routes.message', 'message_bp')` to `blueprint_map` ✅ *Done — added as 19th blueprint*
- [x] **2.5** Add "Delayed Messages" to Tools menu in `templates/base.html` — gated by `user_can_access('tools')` ✅ *Done — added 💬 Delayed Messages item between Coding Helper and Notifications*
- [x] **2.6** Add message sender job to `agent/scheduler.py` — poll pending messages where `scheduled_send_at <= now` and `status='pending'`, call send logic, update status to 'sent' or 'failed' ✅ *Done — added delayed_message_fn param + 60-second interval job; job_delayed_message_sender method added to agent_service.py*

**Phase 2 test results**: `python test.py` → **37 passed, 0 failed, 0 errors**

---

## Phase 3 — Result Response Templates (F19)

**Context**: No code exists. Need model, seed data, and integration with message compose.

- [x] **3.1** Create `models/result_template.py` — `ResultTemplate` model: id, name (String 100), category (String 50, e.g. 'normal', 'abnormal', 'critical', 'follow_up', 'referral'), body_template (Text, with `{patient_name}`, `{result_value}`, `{test_name}` placeholders), is_active (Boolean), display_order (Integer), created_at ✅ *Done — model created with all columns*
- [x] **3.2** Create `migrate_add_result_templates.py` — migration to create table + seed 10-15 default templates across 5 categories (Normal results, Abnormal results, Critical results, Follow-up needed, Referral required) ✅ *Done — migration created; 13 templates seeded across 5 categories*
- [x] **3.3** Add `/api/result-templates` endpoint to `routes/message.py` — `GET` returns active templates grouped by category; `POST` to create custom template (admin only) ✅ *Done — GET returns grouped JSON, POST requires admin role*
- [x] **3.4** Add template picker dropdown to `templates/message_new.html` — "Use Template" button loads templates by category, selecting one fills in message_content with placeholder substitution ✅ *Done — category dropdown + template select, fetches via API, fills textarea*
- [x] **3.5** Import `ResultTemplate` in `models/__init__.py` so `db.create_all()` picks it up ✅ *Done — added import*

**Phase 3 test results**: `python test.py` → **37 passed, 0 failed, 0 errors**

---

## Phase 4 — End-of-Day Checker (F20)

**Context**: `notify_eod_reminder` preference exists in user model (routes/auth.py L227, L443) but nothing consumes it. No agent module, route, or template exists.

- [x] **4.1** Create `agent/eod_checker.py` — EOD check logic (no AC/OCR):
  - `run_eod_check(user_id)` — queries DB for: unsigned notes count (ChartEntry where signed=False), open orders count, pending delayed messages, unread inbox count, uncompleted ticklers due today
  - Returns dict of counts + boolean `all_clear`
  - Sends Pushover notification via `agent/notifier.py` if issues found and user has `notify_eod_reminder` enabled
  ✅ *Done — run_eod_check() queries open orders, pending messages, inbox items, overdue + due-today ticklers; send_eod_notification() sends Pushover if issues found. No ChartEntry model exists so unsigned notes count is deferred.*
- [x] **4.2** Add `/tools/eod` route to `routes/tools.py` — renders EOD dashboard template, calls `run_eod_check()` for current user ✅ *Done — route appended at end of tools.py*
- [x] **4.3** Create `templates/eod.html` — extends base, shows checklist with green checkmarks or red X for each category (unsigned notes, open orders, pending messages, unread inbox, overdue ticklers), summary badge ("All Clear" or "N items need attention") ✅ *Done — 5-card grid with color-coded borders and status icons*
- [x] **4.4** Add EOD check to `agent/scheduler.py` — run at configurable time (default 5:00 PM), only for users with `notify_eod_reminder=True` ✅ *Done — eod_check_fn param + cron job at 17:00; job_eod_check iterates active users and calls send_eod_notification*
- [x] **4.5** Add "EOD Checker" link to Tools menu in `templates/base.html` ✅ *Done — 🌙 EOD Checker added between Delayed Messages and Notifications*

**Phase 4 test results**: `python test.py` → **37 passed, 0 failed, 0 errors**

---

## Phase 5 — Notification History UI

**Context**: `models/notification.py` has complete `Notification` model (user_id, sender_id, message, is_read, created_at, scheduled_for, template_name). `NOTIFICATION_TEMPLATES` dict has 6 types. "Notifications" is already in the Tools menu. No template exists.

- [x] **5.1** Add `/notifications` route to `routes/tools.py` — renders notification history page with pagination (30/page) and type filter ✅
- [x] **5.2** Create `templates/notifications.html` — full history table with date, type badge, message, sender, read/unread status, Mark Read / Mark All Read buttons, type filter dropdown, pagination ✅
- [x] **5.3** Already existed in `routes/auth.py` line 754 — `POST /api/notifications/<id>/read` ✅ (no new code needed)
- [x] **5.4** Already existed in `routes/auth.py` line 768 — `POST /api/notifications/read-all` ✅ (no new code needed)
- [x] **5.5** Added "View all →" link in notification bell dropdown header linking to `/notifications` ✅

> **Phase 5 complete** — 37/37 tests pass. Notification history page with filtering, pagination, and mark-read functionality is live.

---

## Phase 6 — Cache Model Completion & Migration

**Context**: Only 3 cache models exist: `RxNormCache` (models/patient.py), `Icd10Cache` (models/patient.py), `BillingRuleCache` (models/billing.py). The unified `api_response_cache` table in CacheManager handles runtime API caching via raw SQL. The per-model caches are for structured lookups (e.g., drug name → RxCUI). 10 more structured cache models are specified in the API Integration Plan.

- [x] **6.1** Created `models/api_cache.py` with all 10 structured cache models: RxClassCache, FdaLabelCache, FaersCache, RecallCache, LoincCache, UmlsCache, HealthFinderCache, PubmedCache, MedlinePlusCache, CdcImmunizationCache ✅
- [x] **6.2** Created `migrate_add_api_cache_tables.py` — all 10 tables created with indexes ✅
- [x] **6.3** Imported all 10 models in `models/__init__.py` ✅
- [x] **6.4** Wired `_save_to_structured_cache()` methods into all 10 API clients (rxclass, openfda_labels, openfda_adverse_events, openfda_recalls, loinc, umls, healthfinder, pubmed, medlineplus, cdc_immunizations) ✅

> **Phase 6 complete** — 37/37 tests pass. 10 structured cache tables created and wired into API clients for automatic population on fetch.

---

## Phase 7 — Commute Mode (F22a)

**Context**: `/briefing` route exists in `routes/intelligence.py` (line 904) serving the Morning Briefing page. `app/services/api/open_meteo.py` already fetches commute weather (precipitation_probability_commute, rain_likely_commute). No commute-specific route or TTS template exists.

- [x] **7.1** Added `/briefing/commute` route to `routes/intelligence.py` — gathers weather, schedule, care gaps, and inbox unread count ✅
- [x] **7.2** Created `templates/commute_briefing.html` — large-text cards (weather, schedule, quick stats), Web Speech API TTS with Start/Pause/Resume/Stop controls, builds spoken script from Jinja2 data ✅
- [x] **7.3** Added "Commute Mode" (🚗) to View menu in `templates/base.html` below Morning Briefing, gated by `user_can_access('briefing')` ✅

> **Phase 7 complete** — 37/37 tests pass. Commute Mode page with auto-read TTS, commute weather, schedule summary, and quick stats is live.

---

## Phase 8 — AutoHotkey Macro Manager & Dot Phrase Engine (F23)

**Context**: Full-featured AHK creation engine with three pillars: (1) dot phrase text-expansion, (2) macro step recorder/builder, (3) AHK script generator. CareCompanion generates .ahk files — never executes them.

- [x] **8A.1** Created `models/macro.py` — 4 models: AhkMacro, DotPhrase, MacroStep, MacroVariable with relationships, cascade deletes, and UniqueConstraint on user+abbreviation ✅
- [x] **8A.2** Created `migrate_add_macros.py` — 4 tables with indexes, seeded 10 starter macros (navigation, template, data_entry categories) + 15 starter dot phrases across 5 categories (hpi, exam, plan, instructions, letters) ✅
- [x] **8A.3** Imported all 4 models in `models/__init__.py` ✅
- [x] **8B.1** Added dot phrase routes to `routes/tools.py`: GET/POST/PUT/DELETE `/tools/dot-phrases`, GET `/api/dot-phrases`, POST `/api/dot-phrases/<id>/increment`, GET `/tools/dot-phrases/export` ✅
- [x] **8B.2** Created `templates/dot_phrases.html` — category tabs, phrase cards with abbreviation badge + use count, Add/Edit modal with placeholder inserter + live preview, Export AHK button, import modal ✅
- [x] **8C.1** Added macro recording routes: GET `/tools/macros/recorder`, POST `/api/macros/record/save`, GET/PUT `/api/macros/<id>/steps` ✅
- [x] **8C.2** Created `templates/macro_recorder.html` — recording panel with Start/Stop, step palette (9 action types), editable step table with reorder/delete, properties panel with AHK key helpers, variable manager, live AHK preview pane, save macro form ✅
- [x] **8D.1** Created `utils/ahk_generator.py` — 6 functions: `generate_macro_script()`, `generate_dot_phrase_script()`, `generate_full_library()`, `escape_ahk_text()`, `parse_ahk_hotstring()`, `validate_hotkey()`. Handles all 10 action types, placeholder→InputBox substitution, multi-line hotstrings ✅
- [x] **8E.1** Added macro library routes: GET/POST `/tools/macros`, PUT/DELETE `/tools/macros/<id>`, POST restore/duplicate, PUT reorder, GET preview ✅
- [x] **8E.2** Created `templates/macros.html` — stats bar, category tabs, search, card grid with hotkey badge + conflict warnings, Add modal (Write Script / Use Recorder paths), preview modal, undo banner for soft-delete ✅
- [x] **8F.1** Added import/export routes: GET export (all .ahk, single .ahk, JSON backup), GET dot-phrases/export, POST import (.ahk parse, JSON restore) with duplicate-skip logic ✅
- [x] **8F.2** Import UI integrated into `macros.html` — file upload for .ahk and .json, paste area for raw AHK, conflict skip (duplicates ignored) ✅
- [x] **8G.1** Added "Macro Library" (⌨️) to Tools menu in `base.html` between Coding Helper and Delayed Messages ✅
- [x] **8G.2** Added "Dot Phrases" (💬) to Tools menu in `base.html` immediately after Macro Library ✅

> **Phase 8 complete** — 37/37 tests pass. All 4 tables created with 10 seed macros + 15 seed dot phrases. Full macro management (CRUD, duplicate, soft-delete/undo, reorder), dot phrase engine (CRUD, use tracking, placeholder system), step-based macro recorder with live AHK preview, AHK v1 generator (single/batch/full library export), import/export (.ahk parse + JSON backup/restore), hotkey conflict detection.


---

## Phase 9 — Provider Onboarding Wizard (F28)

**Context**: Basic `/setup` route exists in `routes/auth.py` (line 1106) handling NP/AC credential entry. The full onboarding wizard (5-step guided setup) is not built.

- [x] **9.1** Expanded `/setup` route in `routes/auth.py` to redirect new users to `/setup/onboarding` wizard — detects onboarding completion via `onboarding_complete` pref and `setup_completed_at` field; existing users who already completed setup bypass the wizard ✅
- [x] **9.2** Created `templates/onboarding.html` — 5-step wizard:
  - Step 1: Welcome + Profile (full name, specialty dropdown with 11 options, NPI with validation)
  - Step 2: Credentials (NP username/password/provider name, AC username/password — reuses existing encryption)
  - Step 3: Preferences (light/dark theme radio cards, 5 notification toggles in 2-column grid, quiet hours time inputs)
  - Step 4: Module Tour (8 module cards with icon/name/description/checkbox toggle in 2-column grid)
  - Step 5: Confirmation (summary with check/skip indicators, "Get Started" button)
  - Progress bar with green/blue/gray step indicators at top of every step
  ✅
- [x] **9.3** Added step completion tracking — `onboarding_step` and `onboarding_complete` stored in user preferences JSON; `dashboard_redirect()` helper auto-redirects new users to wizard on first login; completing or skipping step 5 sets `setup_completed_at` timestamp ✅
- [x] **9.4** Added `POST /setup/step/<n>` endpoints (n=1-5) to save each step's data incrementally — Step 1 saves display_name + specialty/npi prefs, Step 2 saves encrypted NP/AC creds, Step 3 saves theme + notification + quiet hours prefs, Step 4 saves 8 module toggle prefs, Step 5 marks onboarding complete ✅
- [x] **9.5** Added `POST /setup/skip/<n>` skip endpoints — every step has a "Skip for now" button; skipping advances the step tracker without saving data; skipping step 5 completes onboarding; Back button on steps 2-5 navigates to previous step ✅

> **Phase 9 complete** — 37/37 tests pass. Updated test.py to point `/setup` smoke test at `/setup/onboarding`. Full 5-step onboarding wizard with profile, credentials, preferences, module tour, and confirmation. Auto-redirect for new users, skip support on all steps, Back navigation, step progress bar.

---

## Phase 10 — Integration Testing & DevGuide Update

- [x] **10.1** Updated `test.py` — expanded expected tables from 28 → 59 (all tables); added 9 new page smoke tests: /messages, /messages/new, /tools/eod, /notifications, /briefing/commute, /tools/macros, /tools/dot-phrases, /tools/macros/recorder, /setup/onboarding ✅
- [x] **10.2** Ran full test suite — found and fixed 1 bug: `routes/intelligence.py` commute briefing queried `InboxItem.is_read` which doesn't exist (correct column: `is_resolved`). Fixed. **46/46 checks passing.** ✅
- [x] **10.3** Updated `Documents/DevGuide/running_plan.md` — all 10 phases checked off, added "What Remains" section ✅
- [x] **10.4** Updated `Documents/DevGuide/CareCompanion_Development_Guide.md` — added Feature Implementation Status table at top of document with status for all 31 features plus cache model inventory ✅
- [x] **10.5** Updated `Documents/DevGuide/API_Integration_Plan.md` — added Status column to Cache Tables Required table (12/13 ✅, 1 future); added Status column to Phase 0/2/4/5/7 implementation tables (all ✅ Complete) ✅

> **Phase 10 complete** — 46/46 tests pass (was 37, now 46 with 9 new route smoke tests). Bug fix in commute briefing. All 3 DevGuide documents updated with current implementation status.

---

## ✅ Running Plan Complete

> All 10 phases implemented successfully. **46/46 tests passing.** 59 database tables. 20+ blueprints.

---

## What Still Remains to Be Developed

> **Note (2026-03-20):** All items below (NEW-A through NEW-G) have been completed in Running Plans 2 and 3. AC-blocked features remain blocked. Billing Intelligence (CMS PFS) is now complete with 26 detectors.

### AC-Blocked Features (Require Amazing Charts Calibration)
- **F9 — Chart Prefill Automation**: OCR-driven data entry into Amazing Charts fields. Blocked on AC window calibration and coordinate mapping.
- **F5 Refinements — Inbox Monitor OCR**: Real-time inbox item detection from AC screenshots. Current implementation works but OCR accuracy depends on AC window positioning.
- **F6 Enhancements — Data Scraper**: Additional CDA XML parsing for newer AC export formats.
- **F20a — Unsigned Note Counter**: Requires AC OCR to count unsigned notes. EOD checker currently skips this category.

### Intelligence Layer (Phase 10A in API Integration Plan)
- **NEW-A — Drug Recall Alert System**: Cross-reference patient medications against OpenFDA recall database.
- **NEW-B — Abnormal Lab Interpretation**: AI-assisted lab result analysis using LOINC reference ranges.
- **NEW-C — PubMed Guideline Lookup**: Evidence-based guideline search via PubMed E-utilities.
- **NEW-D — Formulary Gap Detection**: Identify non-formulary medications using RxClass therapeutic alternatives.
- **NEW-E — Patient Education Auto-Draft**: Generate patient-facing education materials via MedlinePlus.
- **NEW-F — Drug Safety Panel**: Consolidated view of FDA labels, adverse events, and recall status.
- **NEW-G — Differential Diagnosis Widget**: ICD-10 + UMLS crosswalk for diagnostic support.
- **NLM Conditions Cache**: `nlm_conditions_cache` table not yet created (needed for NEW-G).

### Billing Intelligence (Phase 10B in API Integration Plan)
- **CMS PFS API Integration**: Real-time RVU lookups from CMS Physician Fee Schedule.
- **Billing Rule Engine**: Automated detection of CCM, AWV, TCM, G2211, 99417, BHI, RPM opportunities.
- **`BillingOpportunity` Enhancement**: Pre-visit billing opportunity calculation.
- **Insurer Detection**: Extract insurance info from CDA XML demographics.
- **Post-Visit Billing Review**: Automated coding completeness check after note signing.

### Platform Features
- **F30 — Offline Mode**: Service Worker + IndexedDB architecture for full offline functionality. Requires architectural rework across all routes.
- **Mobile PWA Enhancements**: Add-to-home-screen, push subscription registration, background sync.
- **Multi-Provider Scheduling**: Support for practices with multiple providers sharing a schedule view.

### Quality & Operations
- **Unit Test Expansion**: Current test suite is smoke tests only (HTTP 200 checks). Need model-level unit tests, form validation tests, and API endpoint tests with mock data.
- **CI/CD Pipeline**: Automated test runs on commit, build verification, deployment automation.
- **Performance Profiling**: Query optimization for large datasets (patients with 5+ years of lab history).
- **Logging & Monitoring**: Structured logging, error aggregation, uptime monitoring dashboard.

---

## Relevant Files

### Bug Fixes (Phase 1)
- `routes/metrics.py` L476 — delete dead duplicate return
- `agent/notifier.py` L15 — verify timedelta import need
- `app/services/api/cache_manager.py` — 7 `db.engine.execute()` sites to modernize
- `app/services/api/base_client.py` — depends on cache_manager fix

### Delayed Messages (Phase 2)
- `models/message.py` — existing `DelayedMessage` model (REUSE, no changes)
- `routes/message.py` — CREATE new file, blueprint `message_bp`
- `templates/messages.html` — CREATE
- `templates/message_new.html` — CREATE
- `app/__init__.py` L611-637 — `_register_blueprints()`, add `message_bp`
- `templates/base.html` L67-85 — Tools menu, add "Delayed Messages" link
- `agent/scheduler.py` — add message sender job

### Result Templates (Phase 3)
- `models/result_template.py` — CREATE new file
- `migrate_add_result_templates.py` — CREATE migration + seed
- `routes/message.py` — ADD template API endpoints
- `templates/message_new.html` — ADD template picker dropdown
- `models/__init__.py` — ADD import

### EOD Checker (Phase 4)
- `agent/eod_checker.py` — CREATE new file
- `routes/tools.py` — ADD /tools/eod route (~L950+)
- `templates/eod.html` — CREATE
- `agent/scheduler.py` — ADD eod check job
- `templates/base.html` — ADD "EOD Checker" to Tools menu
- `routes/auth.py` L227,L443 — existing `notify_eod_reminder` pref (REUSE)

### Notification History (Phase 5)
- `models/notification.py` — existing `Notification` model (REUSE)
- `routes/tools.py` — ADD /notifications route
- `templates/notifications.html` — CREATE
- `templates/base.html` — WIRE notification bell to /notifications

### Cache Models (Phase 6)
- `models/api_cache.py` — CREATE new file with 10 models
- `migrate_add_api_cache_tables.py` — CREATE migration
- `models/__init__.py` — ADD import
- `app/services/api/*.py` — WIRE structured cache saves into 10 client modules

### Commute Mode (Phase 7)
- `routes/intelligence.py` L904 — ADD `/briefing/commute` below existing `/briefing`
- `templates/commute_briefing.html` — CREATE with Web Speech API TTS
- `templates/base.html` — ADD "Commute Mode" to View menu
- `app/services/api/open_meteo.py` — existing commute weather data (REUSE)

### Macros (Phase 8)
- `models/macro.py` — CREATE new file
- `migrate_add_macros.py` — CREATE migration + seed
- `routes/tools.py` — ADD macro CRUD routes
- `templates/macros.html` — CREATE
- `templates/base.html` — ADD "Macro Library" to Tools menu

### Onboarding (Phase 9)
- `routes/auth.py` L1106 — EXPAND existing /setup route
- `templates/onboarding.html` — CREATE 5-step wizard
- `models/user.py` — REUSE preferences JSON for onboarding_step tracking

### Testing (Phase 10)
- `test.py` — ADD new route tests
- `Documents/DevGuide/*.md` — UPDATE all 3 DevGuide documents

---

## Verification

1. After Phase 1: Run `python test.py` — all existing tests pass, no deprecation warnings from fixed sites
2. After Phase 2: Navigate to /messages — see empty pending queue; compose and schedule a message; verify it appears in pending tab; cancel it; verify status changes
3. After Phase 3: On message compose page, click "Use Template" — see templates grouped by category; select one — message body fills with template text
4. After Phase 4: Navigate to /tools/eod — see checklist with current counts; verify all-clear shows when no open items; verify Pushover notification fires when scheduler runs EOD check
5. After Phase 5: Navigate to /notifications — see notification history; click bell icon — goes to /notifications; mark one as read; mark all as read
6. After Phase 6: Run migration — all 10 new tables created; verify `db.create_all()` still works; check one API client populates its cache model
7. After Phase 7: Navigate to /briefing/commute — see large cards with schedule + weather; TTS auto-starts (or shows "Click to start" on browsers requiring gesture)
8. After Phase 8: Navigate to /tools/macros — see seeded macro cards by category; click "Export All" — downloads .ahk file; add a custom macro; edit it; delete it
9. After Phase 9: Create new user — login redirects to onboarding wizard; complete all 5 steps; verify each step saves; verify "skip" works; verify returning user goes to dashboard
10. After Phase 10: Run `python test.py` — all new routes return 200; verify DevGuide documents updated with accurate statuses

---

## Decisions

- **AC features excluded**: F9 (Chart Prefill), F6 (Data Scraper enhancements), F5 (Inbox Monitor OCR refinements) — all blocked on AC calibration
- **Offline Mode (F30) excluded**: Requires Service Worker + IndexedDB architecture that cuts across the entire app — better as its own dedicated plan
- **Cache strategy**: Keep both the unified `api_response_cache` raw SQL table (for runtime API caching) AND the structured per-model cache tables (for typed lookups). They serve different purposes.
- **Message delivery**: Phase 2 message sender is a scheduler job that polls DB — no external message bus needed. Actual delivery mechanism TBD (AC inbox paste vs email vs in-app only). Start with in-app status tracking.
- **Macro execution**: CareCompanion manages macros but does NOT execute AHK scripts directly — it exports .ahk files for the user to run via AutoHotkey.

---

## Dependency Order

Phases 1-5 can be implemented **sequentially** (each builds on prior but no hard blocks between them).
Phase 6 (Cache Models) is **independent** — can run parallel with Phases 2-5.
Phase 7 (Commute) depends on existing `/briefing` route — **independent** of 2-6.
Phase 8 (Macros) is **fully independent**.
Phase 9 (Onboarding) is **fully independent**.
Phase 10 (Testing) must run **last** — depends on all other phases being complete.

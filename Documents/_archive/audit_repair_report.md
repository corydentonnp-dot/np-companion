# CareCompanion — Audit, Repair & Hardening Report

**Date:** 2026-03-18
**Commit:** `8c369a4` (fixes applied)
**Version audited:** v1.1.2

---

## 1. Audit Summary

### Already Implemented Correctly

| Area | Status | Notes |
|------|--------|-------|
| **A1. Dark mode persistence** | Working | Per-user via `user.preferences['theme']` + localStorage. Survives restart. |
| **A2. Preferred browser** | Working | Stored in `preferences['preferred_browser']`, options: chrome/edge/firefox. Used by `/api/open-url`. |
| **A3. AI settings separation** | Working | Admin enables `ai_enabled` per user. User configures provider + key in account settings. Toggles independent. |
| **A5. Refresh button** | Working | Already placed next to notification bell in base.html (lines 257-263). |
| **B4. Copy link / copy link text** | Working | Both in right-click menu: `copy-link-text` and `copy-link-url` actions. |
| **D4. Demographics editing** | Working | Inline edit form in patient header with Name/DOB/Sex fields. Saves via `/patient/<mrn>/update-demographics`. |
| **D5. Upload XML placement** | Working | Compact label-button in patient header. |
| **E2. Medication headers / inactive styling** | Working | Inactive meds get `row-inactive` class (greyed out). |
| **G2. Widget-level settings** | Working | Gear button via `free_widgets.js`: rename, pin, hide, background color, size presets, reset. |
| **G3. Banner centering** | Working | Duration bar has `justify-content: center` (main.css line 1083). |
| **H2. Admin notification sending** | Working | Full UI modal + `/admin/send-notification` route + templates + scheduling + history API. |
| **I1. Version label** | Working | Only in user popover (base.html line 307). Not elsewhere. |
| **J2. Diagnosis copy button** | Working | Copy button + column picker (Diagnosis, ICD-10, Type, Status) in diagnoses widget. |
| **L1-L2. Order sets** | Working | Landing page with tabs, "+ New" button, full-screen 2-panel builder popup, search + tab filtering. |
| **L3. Pre-execution checklist** | Working | Confirmation checkbox + 3-second countdown + type-to-confirm safety modal. |
| **M1. Deactivate user flow** | Working | Immediate + scheduled deactivation. Background job checks every 5 minutes. |
| **M2. Email & account recovery** | Working | Email field on User model. Admin can reset password or PIN. User can change either if they know the other. |
| **N. WebPractice scraper** | Working | Full Playwright scraper with CDP support, setup wizard, nav step recording/replay, session persistence. |

### Partially Implemented (Fixed This Session)

| Area | Issue | Fix Applied |
|------|-------|-------------|
| **C1. UpToDate URLs** | Used `/contents/{drug}-drug-information` pattern → 404 | Changed to `/contents/search?search={term}` across all links |
| **C3. Secret leakage in clipboard** | No sanitization on clipboard writes | Added `_safeClipboardWrite()` blocking known API key patterns |
| **D2. DOB formatting** | Broke on YYYY-MM-DD stored dates | Strip dashes before slicing; display as MM-DD-YYYY everywhere |
| **D3. Unknown patient claim bug** | Circular: "Unknown Patient" stored literally | Client skips placeholder names; server rejects them |
| **E1. Medication dose vs quantity** | Fell back to XML quantity field | Added `_parse_dose_fallback()` regex from drug name/frequency |
| **F1. My Patients search** | No search existed | Added live-filter input with instant JS filtering |
| **G1. Widget scrollable content** | Content overflowed small widgets | Added `overflow:auto` + `min-height:0` to `.widget-body` |
| **J1. ICD-10 auto-enrichment** | Already runs on chart load via `_backfill_icd10_codes()` | Working correctly — uses cache-first, NIH API fallback |
| **K3. Care gaps not displaying** | Engine existed but never called for claimed patients | Wired `evaluate_and_persist_gaps()` into XML upload + chart load |

### Missing (Not Yet Implemented)

| Area | What's Needed | Priority |
|------|---------------|----------|
| **A4. WebPractice provider name default** | Pre-fill "FIRSTNAME LASTNAME (##)" format hint | Low — field exists, just needs better placeholder text |
| **B1. Right-click native feel** | Minor: users expect Shift+F10 / longer press behaviors | Low |
| **D1. MRN always fully visible** | Fixed in roster; chart already shows full MRN | Done |
| **K1. Missing gender impacts** | Gender field exists + editable; some patients just lack data | Data quality issue, not code bug |
| **K2. USPSTF print summary** | Print button exists; needs room-ready handout format | Medium |
| **K2. USPSTF patient-specific toggle** | "Unique to patient / All" toggle needed | Medium |

### Security Concerns Found & Addressed

| Risk | Severity | Status |
|------|----------|--------|
| **Clipboard can leak API keys** | HIGH | Fixed — `_safeClipboardWrite()` blocks sk-ant-*, sk-*, xai-*, key-* patterns |
| **AI API key in password field** | OK | Field is `type="password"`, key encrypted at rest via Fernet |
| **MRN in URLs** | Acceptable | URLs use raw MRN for routing; internal-only app, not internet-facing |
| **API keys logged** | OK | Checked — no route logs decrypted keys; only used in HTTP headers server-side |

---

## 2. Action Plan (Completed)

### Phase 1: Security & Data Integrity (DONE)
1. Clipboard secret sanitization
2. UpToDate URL fix
3. Unknown patient circular bug
4. DOB formatting

### Phase 2: Core Functionality (DONE)
5. Medication dose display fallback
6. My Patients live search
7. Widget scrollable content
8. Care gap auto-evaluation wiring

### Phase 3: Remaining (Lower Priority)
9. USPSTF print handout format enhancement
10. USPSTF "Unique to patient / All" toggle
11. WebPractice provider name placeholder improvement
12. Order set pre-execution lab checklist base set

---

## 3. Fixes Applied

### Fix 1: Clipboard Secret Sanitization (C3)
- **Issue:** No validation before writing to clipboard — API keys could leak via Copy URL
- **Root cause:** `navigator.clipboard.writeText()` called directly with no filtering
- **Files changed:** `static/js/main.js`
- **Implementation:** Added `_safeClipboardWrite(text)` that checks for known API key regex patterns (Anthropic, OpenAI, xAI) before writing. Wrapped all 3 clipboard write points.
- **Why robust:** Pattern-based detection catches keys regardless of context. Fails safe (blocks write, logs warning).

### Fix 2: UpToDate URL Pattern (C1, C2)
- **Issue:** `/contents/{drug}-drug-information` URLs return 404
- **Root cause:** UpToDate drug-information URLs use specific slug format that doesn't match drug names with spaces/special chars
- **Files changed:** `static/js/main.js`, `templates/patient_chart.html`
- **Implementation:** Changed to `/contents/search?search={term}` pattern for all UpToDate links — right-click selection, right-click link, and medication widget drug name links.
- **Why robust:** Search URL always works; UpToDate handles disambiguation at their end.

### Fix 3: Unknown Patient Claim Bug (D3)
- **Issue:** Claiming "Unknown Patient" stores that literal string as the patient name
- **Root cause:** JS reads `.pt-name` text content (which is "Unknown Patient" placeholder), sends it to server, server stores it
- **Files changed:** `templates/patient_chart.html`, `routes/patient.py`
- **Implementation:** Client: filters out "Unknown Patient" and "Unknown" before sending. Server: rejects these strings and falls back to Schedule lookup.
- **Why robust:** Double protection — client and server both filter. Existing "Unknown Patient" records will be overwritten next time real name is available.

### Fix 4: DOB Formatting (D2)
- **Issue:** DOB displayed raw when stored as YYYY-MM-DD (10 chars) instead of YYYYMMDD (8 chars)
- **Root cause:** Template sliced assuming 8-char format; fell through to raw display for 10-char dates
- **Files changed:** `templates/patient_chart.html`, `templates/patient_roster.html`
- **Implementation:** Strip dashes and slashes before slicing. Display as MM-DD-YYYY. Applied to chart header and roster.
- **Why robust:** Handles all common date storage formats (YYYYMMDD, YYYY-MM-DD, YYYY/MM/DD).

### Fix 5: Medication Dose Display (E1)
- **Issue:** Dose column showed quantity (e.g., "108") instead of dose strength when RxNorm lookup fails
- **Root cause:** XML "Dosage" column from Amazing Charts contains quantity dispensed, not dose strength
- **Files changed:** `routes/patient.py`
- **Implementation:** Added `_parse_dose_fallback()` regex parser that extracts dose from drug_name string (e.g., "Lisinopril 10 MG Tablet" → "10 MG") or from frequency/Instructions field. Falls back to this when RxNorm data unavailable.
- **Why robust:** Regex handles all common dose formats (mg, mcg, ml, units, %, meq). Creates lightweight fallback object so template displays correctly.

### Fix 6: My Patients Live Search (F1)
- **Issue:** No search functionality; static table only
- **Root cause:** Template rendered a simple `<table>` with no JS filtering
- **Files changed:** `templates/patient_roster.html`
- **Implementation:** Added search input with `oninput` handler that filters table rows by matching all text content. No Enter key needed.
- **Why robust:** Client-side filtering is instant, works on any column (name, MRN, DOB), and handles any number of patients.

### Fix 7: Widget Scrollable Content (G1)
- **Issue:** Small widgets clip content instead of scrolling
- **Root cause:** `.widget-body` had `overflow-y: auto` but was missing `min-height: 0` (required for flex children to shrink below content size)
- **Files changed:** `templates/patient_chart.html`
- **Implementation:** Changed to `overflow: auto` (both axes) + `min-height: 0`. Lowered widget min-height from 180px to 120px.
- **Why robust:** Standard CSS flex shrinking fix. Works with both grid and free-form layout modes.

### Fix 8: Care Gap Auto-Evaluation (K3)
- **Issue:** Care gaps engine existed but never triggered for manually claimed patients
- **Root cause:** `evaluate_and_persist_gaps()` was only called from NetPractice scraper, not from chart load or XML upload
- **Files changed:** `routes/patient.py`
- **Implementation:** Added `_auto_evaluate_care_gaps()` helper. Called after XML upload and on chart load when no care gaps exist yet.
- **Why robust:** Fails silently (care gaps are not critical path). Only runs when needed (empty gaps). Uses same engine as scraper.

### Fix 9: MRN Full Display in Roster (D1)
- **Issue:** My Patients showed only last 4 digits of MRN with •• prefix
- **Root cause:** Template used `p.mrn[-4:]` slice
- **Files changed:** `templates/patient_roster.html`
- **Implementation:** Changed to display full `{{ p.mrn }}`.

### Fix 10: USPSTF Care Gap Status Indicators
- **Issue:** No visual indication of gap status in USPSTF widget
- **Files changed:** `templates/patient_chart.html`
- **Implementation:** Added colored dot indicators: green (addressed), orange (open/overdue), gray (not evaluated).

---

## 4. Remaining Blockers

**No true blockers requiring user input at this time.**

Lower-priority enhancements that can be implemented independently:

1. **USPSTF print handout** — needs design decision on layout format (room-ready vs letter-size)
2. **Order set base lab panel** — needs the AC reference folder spreadsheet contents to seed
3. **WebPractice provider name** — needs confirmed exact format including ID number

---

## 5. Updated 6 Suggestions

Based on the full codebase audit, these replace and refine the earlier recommendations:

### 1. Wire API Service Classes Into Routes (High Priority)
The API service modules in `app/services/api/` are built but the routes still use raw `urllib` for ICD-10 and RxNorm lookups (`routes/patient.py` lines 151, 224). Migrating these to use the service classes would centralize caching, retry logic, and rate limiting. The service layer is ready — it just needs to be imported and instantiated in the route helpers.

### 2. Background Care Gap Refresh (Medium Priority)
Care gaps now evaluate on chart load and XML upload, but a nightly job should re-evaluate all claimed patients' gaps against updated rules. Wire `evaluate_and_persist_gaps()` into the existing `api_scheduler.py` overnight prep job so gaps are always fresh by morning.

### 3. Notification Event Triggers (Medium Priority)
The notification system works end-to-end but nothing generates notifications automatically. Key events that should create notifications: overdue lab results, new care gaps detected, drug recall alerts, scheduled deactivation warnings, care gap addressed confirmations. Each is a one-line `db.session.add(Notification(...))` call in the right spot.

### 4. Patient Identity Resolution Hardening (Medium Priority)
The "Unknown Patient" fix addresses the symptom, but the root issue is that patient identity comes from three sources (XML, Schedule scraper, manual entry) with no reconciliation. A lightweight identity service that merges name/DOB/sex from all sources and picks the most complete record would prevent future data quality issues.

### 5. HealthFinder API Integration for USPSTF (Lower Priority)
The USPSTF widget currently uses hardcoded rules from `caregap_engine.py`. The `HealthFinderService` in `app/services/api/healthfinder.py` is built and ready to provide authoritative USPSTF recommendations by age/sex. Wiring it in would add patient-specific explanations and keep rules current without code changes.

### 6. RxNorm Service Migration for Medication Enrichment (Lower Priority)
`routes/patient.py` has inline RxNorm API calls (`_fetch_rxnorm_api`, `_enrich_rxnorm_single`). The `app/services/api/rxnorm.py` service provides the same functionality with proper caching, retry, and rate limiting via `BaseAPIClient`. Migrating would reduce code duplication and improve reliability.

---

## 6. WebPractice Recommendation

### Chosen Route: Setup Wizard (Already Implemented)

**Rationale:** The setup wizard approach is already fully built and operational:

- **Admin config page** (`/admin/netpractice`): Global settings (URL, client number, scrape time)
- **Setup wizard** (`/admin/netpractice/wizard`): Walks user through recording navigation steps
- **Step recording**: Captures click targets, text inputs, waits — saved per-user as JSON
- **Scraper replay**: `NetPracticeScraper` replays recorded steps to navigate to schedule page
- **Session persistence**: Cookies saved to `data/np_session.pkl`, reused across runs
- **Health check**: `async health_check()` verifies connectivity and session validity
- **CDP support**: Prefers Chrome DevTools Protocol on port 9222 for connecting to existing browser

**What's already working:**
- Full Playwright-based scraper with login, navigation, appointment extraction
- DOM scraping of `td.schSlot` / `td.schtime` elements
- Care gap evaluation triggered after schedule save
- Reauth banner on dashboard when session expires
- Admin-level user setup status table showing credential/step completeness

**What's needed from user (not blocking now):**
- When ready to activate: the webPRACTICE URL, client number, and NP credentials entered into the admin settings page
- One run of the setup wizard to record the exact navigation clicks to reach the provider schedule

**No architectural changes needed.** The non-UI/Chrome DevTools approach would be an optimization (avoiding full browser automation) but is lower priority since the Playwright approach is already built and tested. The CDP connection already provides a hybrid path — it attaches to an existing Chrome instance rather than launching a new one.

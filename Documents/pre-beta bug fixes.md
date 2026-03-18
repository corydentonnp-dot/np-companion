The RxNorm CUI is actually **already being extracted** from the XML data — `_parse_code_from_text()` in the parser pulls codes from strings like "Lipitor 20 mg tablet [RxNorm: 617310]". So we have the CUI, we just need to use it. Let me update the plan:  

Read [](file:///c%3A/Users/coryd/Documents/NP_Companion/agent/clinical_summary_parser.py#1-1), lines 1 to 80

Searched for regex `_parse_code_from_text|rxnorm|RxNorm|icd10_cache|Icd10Cache` (`**/agent/clinical_summary_parser.py`), 6 results

Read [](file:///c%3A/Users/coryd/Documents/NP_Companion/agent/clinical_summary_parser.py#415-415), lines 415 to 440

Searched for regex `class PatientMedication|drug_name|dosage|rxnorm` (`**/models/patient.py`), 4 results

Read [](file:///c%3A/Users/coryd/Documents/NP_Companion/models/patient.py#82-82), lines 82 to 115

Searched for regex `class Icd10Cache|icd10_cache|icd_code` (`**/models/patient.py`), 2 results

Read [](file:///c%3A/Users/coryd/Documents/NP_Companion/models/patient.py#210-210), lines 210 to 229

Good — I have the full picture. The `_parse_code_from_text` function already extracts the RxNorm CUI from strings like "Lipitor 20 mg tablet [RxNorm: 617310]", but the code is thrown away (`_code` ignored). The `PatientMedication` model has no `rxnorm_cui` column. The `Icd10Cache` pattern is the exact model to mirror. Now let me update the plan: 

Updated memory file [](file:///c%3A/Users/coryd/AppData/Roaming/Code/User/workspaceStorage/a18bafe7fff1b639d7fcb20c2179b0d7/GitHub.copilot-chat/memory-tool/memories/Yzk1N2RhNjEtZmIwMi00MjI0LThlYjktOGQwZmU0OTkxNWI0/plan.md)

Read memory [](file:///c%3A/Users/coryd/AppData/Roaming/Code/User/workspaceStorage/a18bafe7fff1b639d7fcb20c2179b0d7/GitHub.copilot-chat/memory-tool/memories/Yzk1N2RhNjEtZmIwMi00MjI0LThlYjktOGQwZmU0OTkxNWI0/plan.md)

Updated memory file [](file:///c%3A/Users/coryd/AppData/Roaming/Code/User/workspaceStorage/a18bafe7fff1b639d7fcb20c2179b0d7/GitHub.copilot-chat/memory-tool/memories/Yzk1N2RhNjEtZmIwMi00MjI0LThlYjktOGQwZmU0OTkxNWI0/plan.md)

Good. Now also update the "Decisions" section to remove the regex mention and add RxNorm: 

Updated memory file [](file:///c%3A/Users/coryd/AppData/Roaming/Code/User/workspaceStorage/a18bafe7fff1b639d7fcb20c2179b0d7/GitHub.copilot-chat/memory-tool/memories/Yzk1N2RhNjEtZmIwMi00MjI0LThlYjktOGQwZmU0OTkxNWI0/plan.md)

The plan is updated in memory. Here's the full updated plan — everything unchanged except Phase 0.3 and the relevant Decisions entry, which now replace regex parsing with RxNorm API integration:

---

## Plan: CL23 Beta Deployment Readiness

Fix ~40 bugs, missing features, and UI issues across the NP Companion beta. Organized into 6 phases by priority. Each phase is independently verifiable.

**User Decisions**
- ICD-10 auto-lookup: Once per diagnosis, cached permanently
- Widget layout: Keep both grid + freeform, default to freeform
- Order sets: Full redesign — popup-based flow
- Notifications admin: Rebuild with richer UI (templates, broadcast, scheduled)

---

### Phase 0 — Critical Bugs (blocking core usage)

**0.1 Fix admin send-notification endpoint**
auth.py reads `request.form` but JS sends JSON; field mismatch (`target_user_id` vs `user_id`). Change to `request.get_json()`, align field names, return JSON instead of redirect.

**0.2 Fix patient "unknown" name on claim**
patient.py creates `PatientRecord` with only MRN. Fix: look up name from Schedule table or accept `patient_name` from the claim POST body (chart header already has it). Update patient_chart.html and dashboard.html claim JS to send name.

**0.3 RxNorm API integration — authoritative drug data from NIH *(replaces regex parsing)***

The existing parser already extracts the RxNorm CUI from the XML string "Lipitor 20 mg tablet [RxNorm: 617310]" via `_parse_code_from_text()` — but the `_code` result is immediately **discarded**. The fix is to save it and use it. This task also lays the API foundation for all Phase 10 intelligence features. See **`Documents/API_Integration_Plan.md`** for the complete API ecosystem specification.

- **New model** `RxNormCache` in patient.py — mirrors the existing `Icd10Cache` pattern:
  - Fields: `rxcui` (unique, indexed), `brand_name`, `generic_name`, `dose_strength`, `dose_form`, `route`, `source='rxnorm_api'`, `created_at`
- **New utility** `utils/api_client.py` — shared `get_cached_or_fetch()` helper for all APIs (RxNorm, OpenFDA, LOINC, UMLS, etc.). Handles cache-first lookup, rate limiting, offline graceful degradation. This is the foundation used by all Phase 10A/10B features.
- **Migration** — add `rxnorm_cui` column to `patient_medications` table (new `migrate_add_rxnorm_cache.py`)
- **Parser change** in clinical_summary_parser.py: save `_code` into `PatientMedication.rxnorm_cui` instead of discarding it
- **Enrichment function** `_enrich_rxnorm(rxcui)` in patient.py — check `RxNormCache` first; on miss, call NIH API and cache:
  - `GET https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json` → canonical name + TTY (SCD/BN/IN)
  - `GET .../rxcui/{rxcui}/related.json?tty=IN` → generic ingredient name
  - `GET .../rxcui/{rxcui}/related.json?tty=BN` → brand name
  - **Fallback** (no CUI in XML): `GET .../rxcui.json?name={drug_name}&search=1` approximate string match
- **Display**: patient_chart.html medications widget shows Brand Name, Generic Name, Dose + Form, Frequency, Status. UpToDate link uses generic name.
- **Files**: patient.py, clinical_summary_parser.py, utils/api_client.py (new), patient_chart.html, new migration file

---

### Phase 1 — Data Correctness

**1.1 Show full MRN everywhere** — Change patient.py to return raw MRN (remove masking).

**1.2 Fix DOB format** — patient_chart.html shows YYYY-MM-DD. Reformat string slicing to output MM/DD/YYYY.

**1.3 Add sex/gender to chart header** — `patient_sex` exists on `PatientRecord` but isn't shown. Add to patient_chart.html.

**1.4 Add demographics edit UI** — patient.py exists but no frontend form. Add pencil-icon button in chart header → inline form (Name, DOB, Sex) → POST to endpoint.

**1.5 ICD-10 auto-lookup on chart load** — Ensure patient.py runs for all diagnoses missing codes on chart load. Rate-limit NIH API calls (max 5/sec).

**1.6 Fix care gap sex filter** — caregap.py accepts `sex_filter` but never applies it. Add sex lookup from `PatientRecord.patient_sex` and filter logic to match age filter pattern.

---

### Phase 2 — Widget System Overhaul

**2.1 True freeform default** — free_widgets.js: freeform is default, remove 20px snap (or make optional), allow pixel-level dragging and overlapping.

**2.2 Per-widget settings button** — Gear icon in each widget header in patient_chart.html: dropdown with rename, min/max size, background color, pin, hide.

**2.3 Scrollable widget content** — Verify and set `overflow-y: auto` on `.widget-body` in main.css.

**2.4 Layout persists per-user** — Change localStorage key from MRN-based to user-based in free_widgets.js so all patient charts share one arrangement.

---

### Phase 3 — Context Menu & Clipboard

**3.1 Enhanced right-click on links** — Show: Copy Link Text, Copy Link URL, Go to Link, Google it, UpToDate lookup, Ask AI. In main.js.

**3.2 Right-click on selected text** — Show: Copy, Google, UpToDate, Ask AI. On empty area: Paste, Select All, Refresh.

**3.3 Fix text selection on admin pages** — Check for `user-select: none` overrides on admin_users.html table elements.

---

### Phase 4 — Feature Completions

**4.1 USPSTF enhancements** — Ensure `billing_code` and `medicare_code` populated from `CareGapRule`. Add "Due/Overdue Only" dropdown. Verify `printUSPSTF()` in patient_chart.html.

**4.2 Order set full redesign** *(heaviest item)* — Full rewrite of orders.html:
- **Landing page**: Active order sets list (name, category, count, last modified)
- **Create/Edit popup**: Full-screen overlay — left panel (master order browser, category tabs, search, checkboxes) + right panel (selected orders, drag-to-reorder)
- **Commonly Ordered**: Add `is_common` boolean to `MasterOrder` in orderset.py. Show starred items at top of browser.

**4.3 Notification admin rebuild** — Fix broken endpoint (0.1), then add:
- Message templates dropdown, "Send to All" checkbox, scheduled send with datetime picker, notification history
- Add `scheduled_for` and `template_name` columns to Notification model + migration

**4.4 Care gaps spreadsheet for claimed patients** — Dedicated tab in panel report for claimed patients. Add CSV export, color coding (green/red/yellow).

**4.5 Diagnoses copy with column picker** — Config popup on copy: checkboxes for Diagnosis, ICD-10, Type, Status. Tab-separated output for spreadsheet paste.

**4.6 Admin deactivation scheduling** — Verify `scheduler.py` processes deferred deactivations end-to-end.

**4.7 Collect user email** — Add email field to admin user form and settings page for future password reset.

---

### Phase 5 — UI Polish

**5.1** Version → user popover only (remove from header) in base.html
**5.2** Center dashboard appointment banner in dashboard.html
**5.3** Remove redundant "Open" button from My Patients
**5.4** Add refresh button next to notification bell in base.html
**5.5** AI panel minimize/snap-back button
**5.6** My Patients search: use `input` event for live filtering (not just Enter)
**5.7** Verify WebPractice provider name format "FIRSTNAME LASTNAME (##)"

---

### Relevant Files
- patient.py — claim, MRN, DOB, demographics, USPSTF, ICD-10, **new RxNorm enrichment function**
- auth.py — admin notification (broken), user management
- caregap.py — sex filter bug, panel report
- orders.py — order set CRUD
- patient.py — **new RxNormCache model**, PatientMedication.rxnorm_cui column
- notification.py — scheduled_for, template_name columns
- orderset.py — is_common on MasterOrder
- clinical_summary_parser.py — save RxNorm CUI instead of discarding
- patient_chart.html — header, medications widget, USPSTF, demographics edit
- base.html — header, context menu, AI panel
- dashboard.html — appointment banner, My Patients
- admin_users.html — notification modal, email field
- orders.html — full rewrite
- free_widgets.js — freeform, per-user layout key
- main.js — context menu
- main.css — widget scrolling, text selection

---

### Verification

1. **P0**: Admin notification sends. Claim patient → name shows in My Patients. Medications show clean Brand/Generic/Dose from RxNorm — not raw XML string.
2. **P1**: Full MRN, MM/DD/YYYY DOB, sex displayed. Demographics editable inline. ICD-10 auto-populates. Care gap sex filter works.
3. **P2**: Freeform default, no snap, overlapping widgets, same layout across patients, gear icon opens widget settings.
4. **P3**: Right-click link → 6 options. Select text → Copy/Google/AI. Text selectable on admin page.
5. **P4**: Orders landing + popup flow. USPSTF billing codes. Notification templates/broadcast. Diagnoses column picker.
6. **P5**: Version in user menu only. Banner centered. Refresh button. AI panel minimizes.

---

### Decisions

- **API key "leak"**: Not a code bug — stale clipboard from pasting. No fix needed.
- **Medication data**: NIH RxNorm API (free, no license). CUI already in XML but discarded — save it, build `RxNormCache` model mirroring `Icd10Cache`. Regex fallback only if no CUI and API misses.
- **Widget layout**: Per-user localStorage key — all charts share one layout.
- **Care gap sex source**: `PatientRecord.patient_sex`, fallback to Schedule data.
- **Order set redesign**: Full rewrite of orders.html.

### Further Considerations

1. **Migration strategy**: Steps 0.3 (RxNorm cache + PatientMedication.rxnorm_cui), 4.3 (Notification columns), and 4.2 (MasterOrder.is_common) each need a migration. Use the existing `migrate_*.py` pattern or consolidate into one script?
2. **Deployment phasing**: P0+P1 can ship as an immediate hotfix. P2-P5 follow as v1.2.0. Or ship everything together?
3. **Order set redesign scope**: Substantial rewrite — split into sub-phases (landing page first, then popup builder) or deliver in one pass?
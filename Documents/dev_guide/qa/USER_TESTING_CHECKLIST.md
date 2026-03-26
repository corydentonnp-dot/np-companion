# CareCompanion -- Regression Checklist

> **Generated:** 03-24-26
> **Purpose:** Quick pass/fail checklist to run after any code change. Catches regressions before they ship.
> **Usage:** Run through this checklist after every sprint, migration, or significant code change.

---

## Pre-Flight (Run First)
cd C:\Users\coryd\Documents\NP_Companion

$log = "Documents\dev_guide\qa\logs\qa_$(Get-Date -Format 'yyyy-MM-dd_HHmmss').log"; New-Item -Force -ItemType Directory (Split-Path $log) | Out-Null; "CareCompanion QA Run — $(Get-Date)" | Tee-Object -FilePath $log; function Run-Step($label, $block) { "`n=== $label ===" | Tee-Object -FilePath $log -Append; & $block 2>&1 | Tee-Object -FilePath $log -Append }; Run-Step "Smoke Test"      { venv\Scripts\python.exe scripts/smoke_test.py }; Run-Step "DB Integrity"   { venv\Scripts\python.exe scripts/db_integrity_check.py }; Run-Step "Log Scan"       { venv\Scripts\python.exe scripts/check_logs.py }; Run-Step "PHI Scan"       { venv\Scripts\python.exe scripts/check_logs.py --phi-only }; Run-Step "DB Snapshot"    { venv\Scripts\python.exe scripts/db_snapshot.py snapshot }; Run-Step "List Snapshots" { venv\Scripts\python.exe scripts/db_snapshot.py list }; Run-Step "Run All Tests"  { venv\Scripts\python.exe scripts/run_all_tests.py }; Run-Step "Detect Changes" { venv\Scripts\python.exe scripts/detect_changes.py }; Run-Step "Process Count"  { (Get-Process python -ErrorAction SilentlyContinue).Count }; "`nLog saved: $log" | Tee-Object -FilePath $log -Append

Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

## Tier 1 -- Critical Path

### Authentication
- [ ] Login with valid creds -> redirects to / = able to navigate to localhost:5000/dashboard without logging in on regular chrome. must have a cookie saved. should prompt for relog in every 12 hours. — **CONFIG VERIFIED (CL-120):** `PERMANENT_SESSION_LIFETIME = timedelta(hours=12)` in config.py, `session.permanent = True` in before_request hook. Needs manual browser test.
- [ ] Invalid password -> stays on /login with error = works
- [ ] Protected route without auth -> redirects to /login = works on incognito
- [ ] Admin route as non-admin -> 403 (need more guidance on this test)

### Dashboard
- [ ] /dashboard loads with schedule data (or empty state) 
- [ ] Active chart widget responds to polling
- [ ] Schedule add validates required fields

- ~~drag and drop patient to schedule does not work.~~ — Should work now that schedule is no longer hidden inside collapsed Reference tier. Needs re-test.
- ~~should be able to clear TCM banner~~ — **FIXED (CL-T1):** Added dismiss X button to TCM alert bar.
- ~~whats new in CareCompanion banner should be more isolated. right now it is nearly right on top of the "today view"~~ — **FIXED (CL-T1):** Added `.whats-new-banner` CSS with proper flex layout, border, gap.
- ~~daily schedule and patient list should be visible immediately, not nested under the "reference" drop down. delete "references drop down"~~ — **FIXED (CL-T1):** Removed Tier 3 Reference wrapper entirely. Schedule and My Patients are now always visible.
- ~~free resize works okay, but it should bump up items below whatever widget is being resized so there is no blank space.~~ — **FIXED (CL-T1):** Added `_compactGaps()` to `free_widgets.js`; widgets below are pulled up after resize/drag.
- ~~cant see manage widgets setting button when we are in grid mode. Free mode puts it in a weird place overlaying the patients list (not the schedule~~ — **FIXED (CL-T1b):** Moved Manage Widgets button to page header (always visible in both grid and free mode). JS-injected button disabled on dashboard to prevent overlay.
- ~~add patient to schedule button~~ — **FIXED (CL-T1):**
--- ~~when entering a patient's name into the manual add, it should start searching for patients~~ — Added typeahead search with keyboard navigation (ArrowUp/Down/Enter/Escape). Auto-fills name, MRN, DOB from search results.
--- ~~we should be able to search by MRN as well~~ — Typeahead searches both name and MRN via `/api/patient-search`.

- ~~patient schedule grid view overflows the window with no option to scroll~~ — **FIXED (CL-T1):** Changed to dynamic `minmax(18px, 1fr)` grid rows filling the container height.
- ~~when going to a different day on the schedule, when on grid mode, it changes back to table mode~~ — **FIXED (CL-T1):** Verified `localStorage` persistence in `ScheduleGrid.init()` restores saved view on page reload.
- ~~the paste option looks great~~ ... ~~We should not be able to duplicate an existing MRN.~~ — **FIXED (CL-T1):** Backend duplicate detection changed from (MRN+time+date) to (MRN+date only).
--- ~~when clicking add to schedule, the text is black on dark blue in night mode~~ — **FIXED (CL-T1):** Added comprehensive dark mode CSS for `.cc-modal__dialog` and all form elements.
--- after patients are added to schedule, we should have an option to begin amazing charts' auto chart opener/template automation — **NOT YET IMPLEMENTED:** Requires AC automation work (UIA-2/UIA-3 phases).
- ~~scrape tomorrow button stays in a clicked state and just shows "scraping.."~~ — **FIXED (CL-119):** Added 60-second client-side timeout to `pollScrapeProgress()`. Button resets with warning message if scrape status polling exceeds limit. Underlying NetPractice scraper still requires Chrome/Selenium setup for full function.

- ~~the my patients table on the dashboard lists all patients. for now, we only need 3 columns.. Name, MRN, DOB~~ — **FIXED (CL-T1):** Reduced to 3 columns with table-layout:fixed, clipping on name/MRN, DOB always fully shown.
- ~~on the patient schedule we can see "<-- yesterday" TODAY (but not "tomorrow" -->)~~ — **FIXED (CL-T1):** Restructured schedule header into two rows with full date navigation.

~~menu bar items are hidden behind the sidebar~~ — **FIXED (CL-T1):** Header z-index raised from 90 to 200.

~~drag & drop xml didn't work. "Upload error - check console"~~ — **FIXED (CL-T1):** `uploadXmlFiles()` now checks `r.ok` before parsing JSON; handles HTML error responses gracefully.

---


### Patient Chart
- [ ] /patient/90001 loads with tabs
- [ ] Unknown MRN shows 404 or empty state
- [ ] Patient roster loads with list

- ~~on the sidebar, we need to change the "my pateints" text to "patients". the window from this sidebar link will basiclally be a blown up view of the "Patients" widget on the dashboard (the other way around acutally, the dashboard should mirror this page) and we shoudl have two tabs on the top. One is "all patients" (all pateints's whose data is available) and the other is "my patients" (ones that have been claimed by the provider)~~ — **FIXED (CL-119):** Sidebar says "Patients". Patient roster has filing-cabinet All/My Patients tabs. Dashboard patients widget has All/Claimed tabs. Both use unified `.cc-tabs` system.

- ~~none of our patients have full clincial data. unable to review until we have full, detailed patient summaries.... ive asked for complete patient datas in all of the XML files in addition to 10-20 more test patients with full histories.... but maybe im just not seeing htem...~~ — **FIXED (CL-123):** 15 new rich test patients (MRNs 90001-90015) added to `Documents/demo_patients/` with full clinical data across all sections (allergies, medications, problems, vitals, labs, immunizations, social history, insurance, progress notes). Total: 22 XML files. Use admin dropdown -> "Update All Patients" to import.

- ~~admin menu drop down should have a "sever all patients" option where it deletes all patients from teh programs' memory, but not from their acutal file location. we should also have an "update all patients" button somewhere where users can "reload" the patients' data from teh XML output folder so we have the most up to date informaiton. unable to test full function of patient chart until e are able to sever and reload.~~ — **ALREADY IMPLEMENTED:** Admin dropdown has both "Sever All Patients" and "Update All Patients" buttons. Sever clears `claimed_by` without deleting files. Update re-imports from `Documents/demo_patients/`. Needs manual verification.

- ~~takes too long to load a chart. 5-7 second maximum~~ — **FIXED (CL-119):** Added `joinedload(LabTrack.results)` to eliminate N+1 queries on lab data. Further optimization possible if still slow.

- ~~i want the patients name header to butt up to the menu bar header, no gap between the two. makes reading the page challenging.~~ — **FIXED (CL-120):** Hidden breadcrumb trail on patient chart page (`body[data-page="patient-chart"] .breadcrumb-trail{display:none}`). Patient header now sits flush against site header.

### Billing Engine
- [ ] Engine initializes with 27 detectors
- [ ] evaluate() with demo patient returns opportunities
- [ ] No duplicate opportunity codes in result
- [ ] Disabled detector category is skipped

- ~~cant find it. if it exists, its not easy to find, which is a problem itsself~~ — **FIXED (CL-119):** Added dedicated "Billing" sidebar nav item with $ icon linking to `/billing/log`. No longer hidden under Timer.

### Care Gaps
- [ ] /caregap shows active gaps
- [ ] Dismiss gap records suppression
- [ ] Address gap removes from active list

---

## Tier 2 -- Secondary Features

### Bonus Dashboard
- [ ] /bonus loads with 7 sections
- [ ] Below-threshold calculation correct (no bonus, deficit grows)
- [ ] Above-threshold calculation correct (surplus * 0.25)
- [ ] Projection engine returns future quarters

### Lab Tracking
- [ ] /labtrack loads
- [ ] Add lab track entry succeeds
- [ ] Archive sets is_archived flag

### Time Tracking
- [ ] /timer loads (authenticated)
- [ ] /timer/room-widget loads (NO auth required)
- [ ] Timer save creates TimeLog row

### Orders
- [ ] /orders loads
- [ ] Master order list displays
- [ ] Create order set succeeds

### CCM
- [ ] /ccm loads
- [ ] Enroll patient creates CCMEnrollment
- [ ] Time entry logged

### TCM
- [ ] /tcm loads
- [ ] Create watch entry with discharge date
- [ ] 30-day window calculation correct

### Calculators
- [ ] /calculators loads with list
- [ ] BMI computation correct
- [ ] Result saved to CalculatorResult

### Medications
- [ ] /monitoring/calendar loads
- [ ] Monitoring rules generate schedules
- [ ] REMS tracking creates entries

---

## Tier 3 -- Admin and Edge Cases

### Admin Panel
- [ ] /admin/dashboard loads (admin only)
- [ ] User management CRUD works
- [ ] Audit log shows entries

### On-Call
- [ ] /oncall loads
- [ ] Create note succeeds
- [ ] Handoff link accessible without auth

### Telehealth
- [ ] /telehealth loads
- [ ] Log encounter creates CommunicationLog row

### Notifications
- [ ] /notifications loads
- [ ] Mark as read sets timestamp

### Revenue
- [ ] /revenue loads
- [ ] Summary endpoint returns JSON

---

## HIPAA Spot Checks

- [ ] No PHI in `data/logs/carecompanion.log` (MRNs hashed, no real names)
- [ ] Pushover notifications contain counts only, no patient identifiers
- [ ] No `db.session.delete()` on clinical models (use is_archived/is_resolved)
- [ ] JSON error responses don't leak stack traces

---

## Post-Migration Checks

Run these after any database migration:

- [ ] All tables exist: `scripts/db_integrity_check.py`
- [ ] Foreign key constraints valid
- [ ] No NULL values in NOT NULL columns
- [ ] Demo data still intact: `PatientRecord.query.filter_by(mrn='90001').first()` is not None
- [ ] Billing engine still finds all 27 detectors

---

## Version Bump Checks

Run these before incrementing APP_VERSION:

- [ ] All Tier 1 regression items pass
- [ ] CHANGE_LOG.md updated with CL-xxx entry
- [ ] PROJECT_STATUS.md Feature Registry current
- [ ] No open Critical or High bugs in BUG_INVENTORY.md
- [ ] `scripts/run_all_tests.py` reports zero failures

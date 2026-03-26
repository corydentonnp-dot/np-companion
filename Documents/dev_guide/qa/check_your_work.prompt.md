# CareCompanion — Post-Edit Self-Review Protocol
# Run this after EVERY coding session before marking work complete.
# Purpose: Catch breaks before Cory runs tests manually.

You have just finished making code changes. Before declaring
the work done, you must complete every check in this protocol.
Do not skip steps. Do not assume something works because you
did not intentionally change it.

---

STEP 1 — IDENTIFY EVERY FILE YOU TOUCHED

List every file that was modified, created, or deleted in this
session. Include files you only reformatted or added comments to.

For each file:
  - What was the state before your changes (summarize)
  - What is the state after your changes (summarize)
  - Why you changed it

If you cannot recall a file you touched, read the file now and
determine if it matches what you intended.

---

STEP 2 — IMPORT CHAIN VERIFICATION

For every file you modified, verify its import chain is intact.

Check 1: Does the file itself import without errors?
  Mentally trace every import statement in the file.
  Are all imported modules still present and at the same path?
  Did you rename anything that other files import by name?

Check 2: Does anything import FROM the files you modified?
  Search the codebase for: from [module] import
  and import [module]
  For every file that imports from your changed file, verify
  the names it imports still exist in your changed version.

Check 3: CareCompanion-specific critical imports to verify:
  - billing_engine/detectors/__init__.py uses pkgutil.iter_modules()
    for auto-discovery. If you touched any detector file, verify
    it can be imported independently:
    python -c "import billing_engine.detectors.[filename]; print('OK')"
  - app/__init__.py registers blueprints. If you created a new
    route file, verify it is registered.
  - models/__init__.py or equivalent. If you added a model,
    verify it is importable.
  - agent/scheduler.py imports from agent modules. If you changed
    any agent module, verify the scheduler still imports cleanly.

---

STEP 3 — DATABASE SCHEMA VERIFICATION

Did you add, remove, or rename any column on any model?

If YES:
  □ Is there a new migration file in migrations/?
  □ Does the migration follow the idempotent pattern used by all
    other migrations (column-existence check, try/except)?
  □ Does the migration file have a unique name that sorts after
    all existing migration files?
  □ Will the migration run cleanly on an existing database that
    does not have the new column yet?

If you removed a column that existing code references, that is
a breakage. List every place in the codebase that references
the old column name and confirm you updated all of them.

Did you change a model relationship?
  If YES: Verify that any route or service that uses
  relationship.lazy loading or backref still works.

---

STEP 4 — ROUTE VERIFICATION

Did you add, remove, or rename any Flask route?

If YES:
  □ Is the route registered with the correct blueprint?
  □ Is the blueprint registered in app/__init__.py?
  □ Does the route URL pattern conflict with any existing route?
  □ Does the route function have @login_required if it should?
    (Only these 4 routes are explicitly exempted: /login,
    /timer/room-widget, /timer/face/room-toggle,
    /oncall/handoff/<token>)
  □ If the route renders a template, does the template exist?
  □ Does the template receive all variables it uses with Jinja2?

List every Jinja2 variable referenced in any modified template.
Confirm each one is passed from the corresponding route function.

---

STEP 5 — BILLING DETECTOR VERIFICATION

Did you touch anything in billing_engine/?

If YES to any of the following, run the auto-discovery check:
  □ Added a new detector file
  □ Modified billing_engine/detectors/__init__.py
  □ Modified billing_engine/engine.py
  □ Modified billing_engine/base.py
  □ Renamed any detector file

Auto-discovery check (run mentally or literally):
  python -c "
  from billing_engine.engine import BillingCaptureEngine
  engine = BillingCaptureEngine()
  count = len(engine.detectors)
  print(f'{count} detectors loaded')
  assert count == 27, f'BREAK: Expected 27, got {count}'
  print('OK')
  "

If you added a new detector, the count should be 28.
Update the expected count in:
  - tests/test_billing_engine.py test_all_27_detectors_load
  - docs/qa/TESTING_CHECKLIST.md Block C count reference
  - scripts/smoke_test.py detector count assertion
  - This prompt (update 27 to the new count everywhere)

---

STEP 6 — HIPAA COMPLIANCE CHECK

Review every line you changed for these violations:

□ db.session.delete() on a record that has patient context
  (PatientMedication, PatientDiagnosis, PatientLabResult,
  PatientEncounterNote, Schedule, LabTrack, LabResult,
  TimeLog, CCMTimeEntry, TCMWatchEntry)
  REQUIRED FIX: Use is_archived = True or is_resolved = True
  and filter these records out of queries instead.

□ Any patient identifier (MRN, name, DOB) passed to an
  external API. Only these fields are permitted in outbound
  API calls: drug names, RxCUI codes, ICD-10 codes, LOINC
  codes, age (not DOB), biological sex.

□ Any PHI written to a log file. All logging of patient
  context must use hashed MRN:
  hashlib.sha256(mrn.encode()).hexdigest()[:12]

□ Any PHI included in Pushover notification text.
  Notifications may only contain counts and category names,
  never patient names or MRNs.

□ Any new route that handles PHI without @login_required.

If you find any of these, fix them before declaring work done.
They are CRITICAL priority regardless of scope.

---

STEP 7 — REGRESSION CHECK ON DEPENDENT FEATURES

Based on what you changed, identify which features could have
been broken indirectly.

Use this dependency lookup:

If you changed...          These features may be affected:
routes/dashboard.py     → Today View, Schedule display, XML import
routes/bonus.py         → Bonus calculations, deficit display
routes/patient.py       → Patient chart, all chart tabs
billing_engine/         → All 27 detectors, billing cards, bonus impact
models/patient.py       → Every feature that reads patient data
models/bonus.py         → Bonus dashboard, projections
models/schedule.py      → Today View, pre-visit prep, scraper output
app/services/bonus_calc → Bonus math, deficit carry-forward
app/services/pricing    → Medication pricing waterfall display
scrapers/netpractice.py → Schedule import, pre-visit data
agent/scheduler.py      → All 18 background jobs
agent/clinical_summary_parser.py → XML import, all patient data
config.py               → Everything (verify no syntax errors)

For each potentially affected feature, state:
  - Is it likely broken by your changes? YES | NO | UNKNOWN
  - If UNKNOWN: describe what a tester should manually verify

---

STEP 8 — CONFIGURATION AND ENVIRONMENT

Did you add any new configuration values?

If YES:
  □ Is the new config value in config.py with a sensible default?
  □ Is it in .env.example with a comment explaining what it does?
  □ If it is a secret (API key, password), is it stored encrypted
    or as an environment variable, never hardcoded?
  □ Does the application fail gracefully if the value is missing,
    or does it crash?

Did you add any new pip packages?

If YES:
  □ Is the package added to requirements.txt?
  □ Is it available on Windows without a C compiler?
    (This app runs on Windows 11 without admin rights in some contexts)

---

STEP 9 — TEST COVERAGE CHECK

For every bug you fixed or feature you added:
  □ Does an existing test cover this specific behavior?
  □ If no test exists, write one now.
  □ If an existing test was testing the wrong behavior (because
    the bug was in the original code), update the test to test
    the correct behavior.

For every file you modified:
  □ Do the existing tests for that file still pass logically?
    (Read through them — would they still pass with your changes?)
  □ Did any test rely on the old incorrect behavior?
    If yes, update it with a comment: "# Updated: was testing
    broken behavior, now tests correct behavior per BUG-[N]"

---

STEP 10 — FINAL DECLARATION

Complete this checklist before declaring work done:

□ Every modified file is listed in Step 1
□ All imports verified in Step 2
□ All schema changes have migration files (Step 3)
□ All route changes verified (Step 4)
□ Billing detector count correct (Step 5)
□ No HIPAA violations introduced (Step 6)
□ Dependent features assessed (Step 7)
□ Config/environment updated (Step 8)
□ Tests written or updated (Step 9)

If ALL boxes are checked, produce this statement:

"SELF-REVIEW COMPLETE.
Files modified: [list]
Regressions found and fixed: [list or NONE]
Regressions found but not fixed (out of scope): [list with BUG numbers]
New tests written: [count and file names]
HIPAA violations found: [list or NONE]
Ready for manual QA: YES"

If any box is NOT checked, fix the issue before producing
the final statement.

---

COMMON BREAKS IN CARECOMPANION TO WATCH FOR:

1. Adding a model column without a migration
   Symptom: SQLite OperationalError on startup
   Fix: Add migration in migrations/

2. Removing a column that a template still references
   Symptom: Jinja2 UndefinedError in browser
   Fix: Update template or restore column

3. Changing a detector's class name
   Symptom: Auto-discovery finds 26 detectors instead of 27
   Fix: Keep class names consistent with the filename pattern

4. Accidentally adding a print() to a route
   Symptom: PHI may appear in terminal output during production
   Fix: Replace with logging.info() and ensure no PHI in message

5. Changing bonus calculation formula without updating tests
   Symptom: Tests pass with old math, production uses new math
   Fix: Update test expected values to match corrected formula

6. Breaking the agent-to-Flask communication
   Symptom: Agent logs show "active_user.json read failed"
   Fix: Verify data/active_user.json schema matches both readers

7. Modifying config.py structure without updating deploy_check.py
   Symptom: tools/deploy_check.py fails on next deployment
   Fix: Update deploy_check.py validation section to match

8. Any change to scrapers/netpractice.py CUSTOMIZE lines
   Symptom: MFA fails or appointment detail extraction returns empty
   Fix: Only modify CUSTOMIZE lines after live DOM inspection
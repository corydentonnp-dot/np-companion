# CareCompanion -- Testing Cheat Sheet

> Quick reference card. Pin this to your desk.

---

## Commands

| What | Command |
|------|---------|
| **Smoke test** | `venv\Scripts\python.exe scripts/smoke_test.py` |
| **DB integrity** | `venv\Scripts\python.exe scripts/db_integrity_check.py` |
| **Log scan** | `venv\Scripts\python.exe scripts/check_logs.py` |
| **PHI scan only** | `venv\Scripts\python.exe scripts/check_logs.py --phi-only` |
| **Snapshot DB** | `venv\Scripts\python.exe scripts/db_snapshot.py snapshot` |
| **Restore DB** | `venv\Scripts\python.exe scripts/db_snapshot.py restore` |
| **List snapshots** | `venv\Scripts\python.exe scripts/db_snapshot.py list` |
| **Run all tests** | `venv\Scripts\python.exe scripts/run_all_tests.py` |
| **Run pytest only** | `venv\Scripts\python.exe -m pytest tests/ -v` |
| **Run one file** | `venv\Scripts\python.exe -m pytest tests/test_billing_engine.py -v` |
| **Run one class** | `venv\Scripts\python.exe -m pytest tests/test_billing_engine.py::TestAWVDetector -v` |
| **Run one test** | `venv\Scripts\python.exe -m pytest tests/test_billing_engine.py::TestAWVDetector::test_medicare_eligible -v` |
| **E2E tests** | `venv\Scripts\python.exe -m pytest tests/e2e/ -v -m e2e` |
| **Detect changes** | `venv\Scripts\python.exe scripts/detect_changes.py` |
| **Deep health** | `curl http://localhost:5000/api/health/deep` |
| **Process count** | `(Get-Process python -ErrorAction SilentlyContinue).Count` |
| **Full QA suite** | `venv\Scripts\python.exe scripts/run_full_qa.py` |

---

## Pytest Markers

| Marker | Meaning |
|--------|---------|
| `@pytest.mark.e2e` | End-to-end (needs Flask + Playwright) |
| `@pytest.mark.slow` | Takes > 5 seconds |
| `@pytest.mark.billing` | Billing engine tests |

Run only marked tests: `pytest -m billing -v`
Skip marked tests: `pytest -m "not e2e" -v`

---

## Key Fixtures (from conftest.py)

| Fixture | Scope | What It Does |
|---------|-------|-------------|
| `app` | session | Flask app with TESTING=True |
| `client` | function | Flask test client |
| `db_session` | function | DB session with transaction rollback |
| `auth_client` | function | Logged-in client (provider role) |
| `admin_client` | function | Logged-in client (admin role) |
| `demo_patients` | function | 5 representative demo patients |
| `billing_engine` | function | Initialized BillingCaptureEngine |
| `sample_patient_data` | function | Complete patient_data dict |

---

## Demo Patients (Key Subset)

| MRN | Name | Age/Sex | Payer | Good For |
|-----|------|---------|-------|----------|
| 90001 | Margaret Wilson | 67F | Medicare | AWV, CCM, G2211, cognitive |
| 90004 | David Chen | 55M | Commercial | BHI, SDOH, tobacco |
| 90014 | Ethan Rivera | 10M | Medicaid | Pediatric, vaccines |
| 90029 | Isabella Torres | 27F | Commercial | False-positive control |
| 90034 | Samuel Okafor | 55M | Medicare Adv | Complex multi-detector |

Full roster: 35 patients (MRN 90001-90035). See `TEST_DATA_CATALOG.md`.

---

## File Layout

```
tests/
  conftest.py              -- shared fixtures
  test_billing_engine.py   -- billing engine + 27 detectors
  test_bonus_dashboard.py  -- bonus calculator + dashboard
  test_phi_scrubbing.py    -- PHI scrubbing (TDD, will fail)
  e2e/
    test_ui_flows.py       -- Playwright E2E tests

scripts/
  run_all_tests.py         -- full suite runner
  smoke_test.py            -- pre-flight checks
  db_integrity_check.py    -- schema + data validation
  db_snapshot.py           -- snapshot/restore SQLite
  check_logs.py            -- PHI + error log scanner
  detect_changes.py        -- git diff -> test targets

Documents/dev_guide/qa/
  TEST_PLAN.md             -- master test plan (20 plans)
  TESTING_CONVENTIONS.md   -- how tests are written
  FEATURE_REGISTRY.md      -- 48 features tracked
  COVERAGE_MAP.md          -- source-to-test mapping
  BUG_INVENTORY.md         -- known bugs
  TEST_DATA_CATALOG.md     -- demo patient details
  REGRESSION_CHECKLIST.md  -- pass/fail checklist
  ENVIRONMENT_SETUP.md     -- setup guide
  FILE_TO_BLOCKS.md        -- machine-readable mapping
  TESTING_SESSION_OPENER.md -- session startup checklist
```

---

## Trouble?

| Problem | Fix |
|---------|-----|
| Import errors | `cd C:\Users\coryd\Documents\NP_Companion` first |
| DB locked | Kill orphaned python processes |
| Too many processes | `Get-Process python \| Stop-Process -Force` |
| Tests hang | Timeout missing -- kill and re-run with timeout |
| Stale data | `venv\Scripts\python.exe scripts/db_snapshot.py restore` |
| PHI in logs | Run `check_logs.py --phi-only` and fix the logger |

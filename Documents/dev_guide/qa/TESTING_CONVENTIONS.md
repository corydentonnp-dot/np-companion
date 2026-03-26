# CareCompanion -- Testing Conventions

> **Generated:** 03-24-26
> **Purpose:** Single source of truth for how tests are written, named, organized, and run.

---

## Test Framework

- **Framework:** pytest (preferred) with Flask test client
- **Legacy:** Some files use custom `run_tests()` pattern -- these will be migrated to pytest over time
- **Runner:** `venv\Scripts\python.exe -m pytest tests/ -v`
- **Config:** `tests/conftest.py` provides shared fixtures

---

## File Naming

| Convention | Example |
|-----------|---------|
| Unit/integration tests | `tests/test_{module}.py` |
| E2E / Playwright tests | `tests/e2e/test_{flow}.py` |
| Benchmark tests | `tests/benchmark_*.py` |
| Fixtures/helpers | `tests/conftest.py`, `tests/test_helpers.py` |

---

## Function Naming

```
test_{feature}_{scenario}[_{qualifier}]
```

Examples:
- `test_billing_engine_detects_g2211`
- `test_bonus_below_threshold_no_bonus`
- `test_login_invalid_password_rejected`
- `test_phi_scrub_mrn_redacted_in_logs`
- `test_caregap_dismissed_with_reason`

---

## Test Structure (AAA Pattern)

```python
def test_feature_scenario(client, db_session):
    # Arrange -- set up test data
    patient = PatientRecord(mrn='90001', ...)
    db_session.add(patient)
    db_session.commit()

    # Act -- perform the operation
    response = client.get('/patient/90001')

    # Assert -- verify the outcome
    assert response.status_code == 200
    assert b'90001' in response.data
```

---

## Fixture Usage

All shared fixtures live in `tests/conftest.py`. Key fixtures:

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `app` | session | Flask app with test config |
| `client` | function | Flask test client (auto-rollback) |
| `db_session` | function | DB session with transaction rollback |
| `auth_client` | function | Pre-authenticated test client |
| `admin_client` | function | Admin-authenticated test client |
| `demo_patients` | session | 5 representative demo patients |
| `billing_engine` | function | BillingCaptureEngine instance |
| `sample_patient_data` | function | Dict matching evaluate() schema |

---

## Assertions

- Use plain `assert` -- pytest rewrites them for informative failure messages
- For JSON responses: `data = response.get_json()` then assert on the dict
- For HTML responses: `assert b'expected text' in response.data`
- For status codes: `assert response.status_code == 200`
- For DB state: query the model directly after the action

---

## What NOT to Do

- **No `unittest.TestCase` classes** -- use plain functions with fixtures
- **No `print()` for debugging** -- use `pytest -s` flag if you need stdout
- **No `sys.path` manipulation** -- conftest.py handles this via root-level placement
- **No network calls in tests** -- mock external APIs with `monkeypatch` or fixtures
- **No hard-coded file paths** -- use `tmp_path` fixture or app config
- **No `time.sleep()` in unit tests** -- mock time if needed
- **No `db.session.delete()` on clinical records** -- test soft-delete (is_archived) instead

---

## Markers

```python
import pytest

@pytest.mark.slow          # Takes > 5 seconds
@pytest.mark.e2e           # Requires Playwright browser
@pytest.mark.billing       # Billing engine tests
@pytest.mark.integration   # Requires DB and Flask app
@pytest.mark.phi           # PHI handling tests
```

Run a specific marker: `pytest -m billing -v`

---

## Test Data Rules

- **Demo MRNs:** 90001-90035 (reserved for testing, never use real MRNs)
- **Test user:** CORY / ASDqwe123 (admin role)
- **Test patient:** MRN 62815, TEST TEST, DOB 10/1/1980, 45F
- **DB isolation:** Each test function gets a rolled-back transaction
- **No PHI in test data:** Use obviously fake names (TEST TEST, DEMO PATIENT, etc.)
- **Deterministic:** Tests must produce the same result on every run

---

## Running Tests

```powershell
# Full suite
venv\Scripts\python.exe -m pytest tests/ -v

# Single file
venv\Scripts\python.exe -m pytest tests/test_billing_engine.py -v

# Single test
venv\Scripts\python.exe -m pytest tests/test_billing_engine.py::test_engine_detects_g2211 -v

# By marker
venv\Scripts\python.exe -m pytest -m billing -v

# With coverage (if pytest-cov installed)
venv\Scripts\python.exe -m pytest tests/ --cov=. --cov-report=term-missing
```

---

## CI/Pre-Commit

No CI pipeline yet. For now:
1. Run `scripts/smoke_test.py` before any testing session
2. Run `scripts/run_all_tests.py` for the full suite
3. Run `scripts/db_integrity_check.py` after any migration or data change

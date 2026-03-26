# CareCompanion -- Test Environment Setup

> **Generated:** 03-24-26
> **Purpose:** Step-by-step instructions to prepare a machine for running CareCompanion tests.

---

## Prerequisites

| Requirement | Version | Check Command |
|------------|---------|---------------|
| Python | 3.11.x | `python --version` |
| pip | Latest | `pip --version` |
| SQLite | 3.35+ | `python -c "import sqlite3; print(sqlite3.sqlite_version)"` |
| Git | Any | `git --version` |
| Tesseract | 5.x (optional, for OCR tests) | `tesseract --version` |
| Playwright | 1.58.0 (optional, for E2E) | `python -m playwright --version` |

---

## Initial Setup

### 1. Clone and activate virtual environment

```powershell
cd C:\Users\coryd\Documents\NP_Companion
python -m venv venv
venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Install test dependencies (if not already in requirements.txt)

```powershell
pip install pytest pytest-cov
```

### 4. Verify database exists

```powershell
# Check for database file
Test-Path data\carecompanion.db

# If missing, create it (app factory creates tables)
python -c "from app import create_app; app = create_app(); ctx = app.app_context(); ctx.push(); from models import db; db.create_all(); print('DB created')"
```

### 5. Seed demo data

```powershell
venv\Scripts\python.exe scripts\seed_test_data.py
```

### 6. (Optional) Install Playwright for E2E tests

```powershell
pip install playwright
python -m playwright install chromium
```

---

## Environment Variables

CareCompanion does NOT use environment variables. All config lives in `config.py`.

Key test-relevant settings in `config.py`:

| Setting | Purpose | Test Value |
|---------|---------|------------|
| `AC_MOCK_MODE` | Simulate Amazing Charts | `True` for testing |
| `TESTING` | Flask test mode | Set by conftest.py |
| `SQLALCHEMY_DATABASE_URI` | Database path | `sqlite:///data/carecompanion.db` |
| `APP_VERSION` | Version string | Read-only in tests |

---

## Database for Testing

Tests use the **same SQLite database** but with transaction rollback per test (via conftest.py fixtures). This means:

- Each test function gets a clean transaction
- Changes are rolled back after each test
- Demo data from seed script persists across test runs
- No separate test database needed

### Snapshot/Restore (for destructive testing)

```powershell
# Snapshot before destructive tests
python scripts\db_snapshot.py --action snapshot

# Restore after
python scripts\db_snapshot.py --action restore
```

---

## Running Tests

### Quick smoke test
```powershell
venv\Scripts\python.exe scripts\smoke_test.py
```

### Full pytest suite
```powershell
venv\Scripts\python.exe -m pytest tests\ -v
```

### Legacy tests (non-pytest)
```powershell
venv\Scripts\python.exe scripts\run_all_tests.py
```

### Specific markers
```powershell
venv\Scripts\python.exe -m pytest -m billing -v
venv\Scripts\python.exe -m pytest -m phi -v
venv\Scripts\python.exe -m pytest -m e2e -v
```

### With coverage
```powershell
venv\Scripts\python.exe -m pytest tests\ --cov=. --cov-report=term-missing
```

---

## Troubleshooting

### "ModuleNotFoundError" when running tests
Ensure you're using the venv Python:
```powershell
venv\Scripts\python.exe -m pytest tests\ -v
```

### "Database is locked"
Only one Flask/test process should access the DB at a time. Check:
```powershell
(Get-Process python -ErrorAction SilentlyContinue).Count
```
Kill orphans if > 5.

### "OperationalError: no such table"
Run migrations or recreate:
```powershell
python -c "from app import create_app; app = create_app(); ctx = app.app_context(); ctx.push(); from models import db; db.create_all()"
```

### Playwright tests fail with "Browser not installed"
```powershell
python -m playwright install chromium
```

### Test hangs / never completes
Check for `time.sleep()` or blocking I/O in the test. Use `Ctrl+C` to interrupt, then check process count.

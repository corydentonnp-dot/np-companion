# CareCompanion -- Testing Session Opener

> **Purpose:** Run this checklist at the START of every QA/testing session to ensure the environment is healthy before writing or running tests.

---

## Quick Start (Copy-Paste Block)

```powershell
cd C:\Users\coryd\Documents\NP_Companion

# 1. Process audit
(Get-Process python -ErrorAction SilentlyContinue).Count

# 2. Smoke test
venv\Scripts\python.exe scripts/smoke_test.py

# 3. DB integrity
venv\Scripts\python.exe scripts/db_integrity_check.py

# 4. Log scan
venv\Scripts\python.exe scripts/check_logs.py

# 5. Snapshot DB before destructive tests
venv\Scripts\python.exe scripts/db_snapshot.py snapshot
```

---

## Step-by-Step

### 1. Process Audit
```powershell
(Get-Process python -ErrorAction SilentlyContinue).Count
```
- If count > 5, clean up before proceeding:
```powershell
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CPU -gt 30 -or $_.WorkingSet64 -gt 500MB } | Stop-Process -Force
```

### 2. Smoke Test
```powershell
venv\Scripts\python.exe scripts/smoke_test.py
```
**Pass criteria:** All 6 checks green:
- App factory creates app
- DB connectivity
- All 31 blueprints registered
- Key tables exist
- Config sanity (APP_VERSION, PORT, HOST)
- `/api/health` returns 200

### 3. DB Integrity Check
```powershell
venv\Scripts\python.exe scripts/db_integrity_check.py
```
**Pass criteria:** All 5 checks green:
- 26+ required tables present
- NOT NULL constraints satisfied
- Foreign key integrity (no orphans)
- Demo data present (35 patients)
- Row counts reasonable

### 4. Log Scan
```powershell
venv\Scripts\python.exe scripts/check_logs.py
```
**Pass criteria:**
- No PHI leaks detected (MRN, DOB, phone, SSN patterns)
- Error count reviewed (some errors may be expected)
- Log file sizes reasonable (< 50MB each)

### 5. Snapshot DB
```powershell
venv\Scripts\python.exe scripts/db_snapshot.py snapshot
```
Creates a timestamped copy in `data/backups/snapshots/`. Restore after destructive tests:
```powershell
venv\Scripts\python.exe scripts/db_snapshot.py restore
```

---

## Deep Health Check (Optional)

If Flask is running:
```
GET http://localhost:5000/api/health/deep
```
Returns JSON with DB tables, blueprints, billing detectors, log paths, and demo data status.

---

## Detect What to Test (After Code Changes)

```powershell
venv\Scripts\python.exe scripts/detect_changes.py
```
Reads git diff and prints exactly which test files to run.

---

## Run Tests

```powershell
# Run specific test file
venv\Scripts\python.exe -m pytest tests/test_billing_engine.py -v

# Run all pytest tests
venv\Scripts\python.exe -m pytest tests/ -v --ignore=tests/e2e

# Run full suite (pytest + legacy)
venv\Scripts\python.exe scripts/run_all_tests.py

# Run E2E (requires Flask running + Playwright)
venv\Scripts\python.exe -m pytest tests/e2e/ -v -m e2e
```

---

## After Testing

```powershell
# Restore DB if snapshot was taken
venv\Scripts\python.exe scripts/db_snapshot.py restore

# Process cleanup
(Get-Process python -ErrorAction SilentlyContinue).Count
```

---
description: Audit SaaS readiness — check for multi-tenant violations, desktop code leaks, and architecture gaps.
agent: agent
---

# SaaS Readiness Check

You are the **CTO** for CareCompanion. Audit SaaS readiness across the codebase.

## 1. Desktop Code Boundary
Search for imports of desktop-only packages outside `agent/`:
- `pyautogui`, `win32gui`, `win32con`, `pytesseract`, `pyperclip`, `pystray`
- Any file in `routes/`, `models/`, `utils/`, `billing_engine/` that imports these is a violation.

## 2. Tenant Isolation Check
- Search all model queries for missing `user_id` or `practice_id` scoping.
- Check for global queries that would leak data across tenants in a multi-tenant setup.
- Verify `is_shared=True` logic restricts writes to author only.

## 3. Config Portability
- Read `config.py` and identify desktop-only settings (file paths, window coordinates, OCR configs).
- Verify desktop-only configs are marked with `# Desktop-only` comments.
- Check for hardcoded file paths outside `config.py`.

## 4. Database Portability
- Search for SQLite-specific patterns: `PRAGMA`, raw SQL strings, `db.engine.execute()`.
- Verify all queries use SQLAlchemy ORM.
- Check for `AUTOINCREMENT` or other SQLite-specific DDL.

## 5. Adapter Pattern
- Read `adapters/base.py` and verify the `BaseAdapter` ABC covers all EHR operations.
- Check if any route directly calls Amazing Charts functions instead of going through an adapter.

## 6. Output
Present a SaaS readiness scorecard:

| Category | Score | Issues Found | Priority Fix |
|----------|-------|--------------|--------------|

Log any new findings to the Risk Register in `PROJECT_STATUS.md`.
Update `CHANGE_LOG.md` with a `## CL-xxx — SaaS Readiness Check` entry.

---
applyTo: "**/*.py"
---

# Coding Standards

These standards unify model, route, adapter, and desktop-agent boundaries for
CareCompanion.

## Models

- All models inherit from `db.Model`.
- Patient or user-specific records must include tenant scoping:
  `user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)`.
- Clinical records must be soft-deletable (`is_archived` or `is_resolved`).
  Never rely on hard-delete flows for clinical objects.
- Use UTC timestamps with `datetime.now(timezone.utc)`, not `datetime.utcnow()`.
- Export every new model from `models/__init__.py`.
- Use clear naming:
  - Class names: singular PascalCase.
  - Foreign keys: `{related_table}_id`.
- For required fields use `nullable=False`.
- Add validations via constraints or route/service validation where needed.
- Add tests for each new model (`tests/test_{model}.py`).
- Keep schema choices ORM-portable (avoid SQLite-only assumptions).

## Routes

- Use `@login_required` on all endpoints except approved exemptions.
- Use role decorators:
  - `@require_role('admin')` for `/admin/*`
  - `@require_role('provider')` for billing, metrics, on-call
- Follow blueprint pattern with scoped queries to `current_user.id`.
- Enforce data isolation:
  - user data always scoped by `user_id`
  - shared data readable by all, editable by author only
- JSON response contract:
  `{"success": bool, "data": ..., "error": str|None}`
- Error handling contract:
  - rollback DB session on exceptions
  - log server-side details
  - return generic, non-sensitive client errors
- Use `redirect(url_for(...))`, never `redirect(request.referrer)`.
- Do not log PHI (name, MRN, DOB). Hash MRN when logging.
- Audit patient-adjacent actions with `log_access()`.

## Agent & Desktop Automation

Desktop-only imports such as `pyautogui`, `win32gui`, `pytesseract`,
`pyperclip`, `pystray`, and related Win32 automation packages are limited to
`agent/`.

- Do not import desktop automation packages in `routes/`, `models/`, `utils/`,
  `billing_engine/`, or `adapters/`.
- Agent and Flask app are separate processes; communicate through SQLite and
  `data/active_user.json`.
- Wrap agent jobs in try/except; log failures and continue safely.
- Never use `print()` for operational errors.
- Use OCR-first or UIA-first interaction helpers; avoid coordinate-only logic.
- Verify AC state before automation and fail safely with actionable logs.
- For subprocess use:
  - `subprocess.run(..., timeout=...)` always
  - track `subprocess.Popen` objects and enforce wait/terminate/kill behavior
  - avoid `os.system()` and `os.popen()`
- Keep scheduler jobs safe from overlap with `max_instances=1` and
  `coalesce=True`.

## Adapters

Adapters isolate EHR-specific logic from application business logic.

- App code calls the adapter abstraction, not EHR-specific implementations.
- `adapters/base.py` defines `BaseAdapter`; concrete adapters must implement all
  required methods.
- Register concrete adapters in the adapter factory.
- Keep adapter outputs in canonical, EHR-agnostic data shapes.
- Do not add Amazing Charts-only fields to canonical adapter data contracts.
- Keep adapters data-focused: no route handling, UI behavior, or notification
  delivery.

## Testing

- Add or update tests with every meaningful feature or behavior change.
- New routes get integration coverage.
- New models get validation and relationship coverage.
- Billing logic gets positive and negative cases.
- Calculator logic gets known-input and known-output tests.
- Preserve regression safety by running project test suites after structural
  changes.

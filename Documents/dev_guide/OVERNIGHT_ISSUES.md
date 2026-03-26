# CareCompanion — Overnight Session Issues
**Session started:** 03-26-26 05:15:30 UTC
**Purpose:** Document anything that couldn't be resolved in 2 attempts / 8 minutes for morning human review.

---

## Issues

- **ISSUE-001 (Process/Docs):** A3.15 exact `Documents/dev_guide/` file-count verification deferred.
	- **Reason:** `OVERNIGHT_REMEDIATION_TRACKER.md` and `OVERNIGHT_ISSUES.md` are required live artifacts for the active overnight run and cannot be archived/deleted mid-session.
	- **Action:** Re-run A3.15 at session-end protocol after tracker/issues are archived.
	- **Status:** Open (deferred)

- **ISSUE-002 (lint_sprawl WARN: Route file sizes > 800 lines):** `scripts/lint_sprawl.py` reports 7 route files exceeding the 800-line guideline.
	- **Files:** routes/auth.py (2046), routes/intelligence.py (2491), routes/tools.py (2039), routes/dashboard.py (1053), routes/timer.py (1174), routes/patient.py (1183), routes/admin.py (851)
	- **Action:** Schedule Band 5 service extraction sessions to split these files. Start with intelligence.py (largest) and auth.py.
	- **Status:** Open — WARN, not ERROR; acceptable in current state

- **ISSUE-003 (lint_sprawl WARN: pyautogui in routes/orders.py):** Three pyautogui-related imports remain in routes/:
	- `routes/orders.py:280,300`: `from agent.pyautogui_runner import execute_order_set` (lazy imports inside route functions, suppressed with `# lint-ok`)
	- `routes/orders.py:653`: `import pyautogui` inside try/except ImportError block in `calibrate_capture()`
	- **Action:** B5 refactor — move order set execution to agent async job queue. `execute_set` and `resume_execution` routes should enqueue a job instead of calling execute_order_set() directly.
	- **Status:** Open — deferred to B5

- **ISSUE-004 (lint_sprawl WARN: Missing @login_required — likely false positives):** The linter reports 452 potential missing `@login_required` on route functions. The vast majority are FALSE POSITIVES because:
	- Routes in admin.py/admin_*.py use `@require_role('admin')` which extends @login_required
	- The linter cannot currently detect chained decorators above the @route decorator (searches back 10 lines, but `@require_role` appears between `@route` and `def`)
	- **Action:** Refine the linter in a future session to recognize `@require_role` as satisfying the login_required check.
	- **Status:** Open — known false-positive pattern in linter logic

---

## SESSION SUMMARY
**End time:** [pending]
**Bands completed:** [pending]
**Audit passes completed:** [pending]
**PW phases tested:** [pending]
**Issues for morning review:** [pending]
**Test suite status:** [pending]

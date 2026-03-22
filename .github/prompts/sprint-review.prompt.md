---
description: Run a sprint review — audit progress, verify Feature Registry accuracy, check for stale work, and plan next steps.
agent: agent
---

# Sprint Review

You are running a sprint review for **CareCompanion**. Execute these steps in order:

## 1. Audit Current State
- Read `Documents/dev_guide/PROJECT_STATUS.md` — check Feature Registry for accuracy.
- Read `Documents/dev_guide/ACTIVE_PLAN.md` — identify stale "in progress" items from prior sessions.
- Read `Documents/CHANGE_LOG.md` (top 10 entries) — summarize recent momentum.

## 2. Feature Registry Accuracy Check
For each feature marked "✅ Complete" in the registry, spot-check that:
- The route file exists and has `@login_required`.
- The model exists in `models/`.
- At least one test exists in `tests/`.
Flag any discrepancies.

## 3. Dead Code & Sprawl Scan
- Check for orphaned files (templates not referenced by routes, models not imported anywhere).
- Check for commented-out code blocks in route files.
- Check `migrations/` for files that could be archived.

## 4. Blocker Review
- List all items marked "Blocked" in ACTIVE_PLAN or Feature Registry.
- For each blocker, assess: is it still blocked? Has the dependency changed?

## 5. Output
Present a structured sprint review with:
- **Velocity:** Features completed since last review
- **Health:** Feature Registry accuracy score
- **Risks:** Top 3 from Risk Register
- **Blockers:** Current blockers with updated status
- **Next Sprint:** Recommended priorities for next work session
- **Cleanup:** Any dead code, stale files, or orphaned references found

Update CHANGE_LOG.md with a `## CL-xxx — Sprint Review` entry.

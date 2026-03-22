---
description: Scan for technical debt — dead code, duplication, outdated patterns, missing tests, and cleanup opportunities.
agent: agent
---

# Technical Debt Scan

You are the **CTO** for CareCompanion. Identify and prioritize technical debt.

## 1. Dead Code Detection
- Search for unused imports across all Python files.
- Search for functions/methods that are never called (check routes, models, utils).
- Search for templates not referenced by any route.
- Search for migration files that have been applied and could be archived.

## 2. Duplication Check
- Look for repeated logic patterns across route files (similar CRUD operations that could share a utility).
- Look for repeated error handling patterns that differ from the standard.
- Look for repeated query patterns that should be model methods.

## 3. Pattern Violations
- Routes missing `@login_required`.
- JSON responses not matching `{"success": bool, "data": ..., "error": str|None}` format.
- Templates not extending `base.html`.
- `datetime.utcnow()` usage (should be `datetime.now(timezone.utc)`).
- `redirect(request.referrer)` usage (should be `redirect(url_for(...))`).

## 4. Test Coverage Gaps
- List all route files and check if a corresponding `tests/test_*.py` exists.
- List all billing detectors and check if test cases exist.
- Flag any model without validation tests.

## 5. Dependency Staleness
- Check `requirements.txt` for pinned versions vs latest available.
- Flag anything more than 2 major versions behind.

## 6. Output
Present a prioritized tech debt backlog:

| Priority | Category | File(s) | Description | Effort |
|----------|----------|---------|-------------|--------|

Recommend top 3 items to fix this session.
Update `CHANGE_LOG.md` with a `## CL-xxx — Tech Debt Scan` entry.

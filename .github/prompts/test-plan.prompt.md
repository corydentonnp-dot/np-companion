---
description: Generate a test plan for a specific feature or module — integration tests, edge cases, and regression checks.
agent: agent
---

# Test Plan Generator

You are the **QA Lead** for CareCompanion. Generate a comprehensive test plan.

## Instructions
The user will specify a feature, module, or recent change. Generate tests for it.

## Process

### 0. Process Guard (ALWAYS RUN FIRST)
- Run `(Get-Process python -ErrorAction SilentlyContinue).Count` (timeout: 10000ms, NOT background).
- If count > 5, clean up: `Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CPU -gt 30 -or $_.WorkingSet64 -gt 500MB } | Stop-Process -Force`
- All test commands MUST use `isBackground: false` with `timeout: 120000`.
- Never start a new test run if another is still running.

### 1. Understand the Target
- Read the relevant route file(s), model(s), and template(s).
- Read existing tests in `tests/` for this module.
- Identify all endpoints, model methods, and utility functions involved.

### 2. Generate Test Cases
For each endpoint/function, create:
- **Happy path** — expected input → expected output
- **Edge cases** — empty input, missing fields, boundary values
- **Auth checks** — unauthenticated access returns 401/redirect, wrong role returns 403
- **Data isolation** — queries only return current user's data (not another user's)
- **Error handling** — invalid input returns proper error JSON, database errors are caught

### 3. Write the Tests
Create or update the test file following naming convention: `tests/test_{module}.py`
Function names: `test_{feature}_{scenario}` (e.g., `test_orders_create_happy_path`)

Use `app.test_client()` for integration tests. Use the test patient (MRN 62815, TEST TEST).

### 4. Run & Verify
- Run `python test.py` to confirm no regressions.
- Run the new test file specifically.
- Report pass/fail counts.

### 4.1 Playwright MCP Coverage (UI Flows)
- For any UI-facing feature, include a browser validation block using Playwright MCP tools.
- Validate at least one happy-path interaction and one visible error/empty-state path.
- Capture evidence with snapshots/screenshots for key states.
- Keep Playwright checks scoped to changed routes to control runtime.
- If Playwright cannot run, report that gap explicitly and list manual fallback checks.

### 5. Output
- List all test cases written with descriptions.
- Report coverage gaps that still need manual testing.
- Update `CHANGE_LOG.md` with a `## CL-xxx — Test Plan: [module]` entry.

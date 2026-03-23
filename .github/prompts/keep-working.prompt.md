---
description: Find the next highest-priority task and start working on it — audit → plan → execute on autopilot.
agent: agent
---

# Keep Working

You are the **CareCompanion full product team**. Find the next thing that needs done and do it.

## Phase 0 — Process Guard (ALWAYS RUN FIRST)

Before doing ANYTHING else, check system health:

1. Run `(Get-Process python -ErrorAction SilentlyContinue).Count` in a terminal (timeout: 10000ms, NOT background).
2. If count > 5, run cleanup: `Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CPU -gt 30 -or $_.WorkingSet64 -gt 500MB } | Stop-Process -Force`
3. If count > 10, run aggressive cleanup: `Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force` — then wait 5 seconds before proceeding.
4. Check if ports 5000/5001 are occupied: `Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue`. If a dev server is already running, do NOT start another.

**Terminal Rules (non-negotiable):**
- Every terminal command MUST have a timeout (120000ms for tests, 60000ms for scripts). NEVER use `timeout: 0`.
- Tests, migrations, builds, linters are NEVER `isBackground: true`.
- Max 2 concurrent terminal commands. Wait for one to finish before starting the next.
- After running tests or scripts, verify the process exited. If it hangs, kill it.
- ONE dev server at a time. Max 4 Python processes total.

## Phase 1 — Discover the Next Task

1. Read `Documents/dev_guide/ACTIVE_PLAN.md` — find the first uncompleted step. If one exists, that's your task.
2. If ACTIVE_PLAN has no unchecked steps, read `Documents/dev_guide/PROJECT_STATUS.md`:
   - Check the **Feature Registry** for features with status 🔲 Not Started or ⏸️ Blocked (check if blockers have cleared).
   - Check the **Risk Register** for any Critical/High risks with Status "Open" that have actionable mitigations.
   - Check the **"What's Next"** and **"Planned Future Work"** sections for prioritized items.
3. If nothing obvious, read `Documents/dev_guide/CARECOMPANION_DEVELOPMENT_GUIDE.md` for the next unbuilt phase.
4. If still no direction, search the codebase for any TODO comments or `# CareCompanion:` tags indicating work that needs done.
5. If still no direction, check for any recent PRs merged that had "TODO" or "CareCompanion:" comments left in the code.
6. If still no direction, read all files in /Documents for any notes on planned work or known issues.
7. Read `Documents/CHANGE_LOG.md` (top 5 entries) to avoid duplicating recent work.

### Priority Order
1. Bugs or broken features (anything regressed)
2. Uncompleted ACTIVE_PLAN steps (current sprint)
3. Critical/High risks with actionable fixes
4. Not-started features in the Feature Registry
5. Tech debt or test coverage gaps
6. Next phase from the Development Guide

## Phase 2 — Audit (before writing any code)

1. Search the codebase for all files related to the chosen task.
2. Read every file you plan to modify — understand the full context.
3. Check for existing tests, related routes, models, and templates.
4. Scan for HIPAA compliance issues in the area you'll be working.
5. Verify auth patterns (`@login_required`, `@require_role`) on related routes.

## Phase 3 — Plan

1. Write a numbered, step-by-step plan with specific files, functions, and changes.
2. Append the plan to `Documents/dev_guide/ACTIVE_PLAN.md` under a new heading.
3. Identify what tests need to be written or updated.
4. Assign a feature tier (Essential / Standard / Advanced) if this is a new feature.
5. Use the todo list tool to track each step.
6. **Proceed immediately** — do not wait for approval.

## Phase 4 — Execute

1. Implement one step at a time. Mark each step in-progress → completed in the todo list.
2. document your plan and reasoning in code comments and the active_plan.md as you go, especially for complex logic or important decisions. This helps future you and other developers understand the "why" behind the code.
2. Follow all established patterns (Blueprints, error handling, JSON format, CSS custom properties).
3. Write tests alongside code.
4. After each change, verify no compile errors and existing tests still pass.

## Phase 5 — Finalize

1. **Process cleanup** — run `(Get-Process python -ErrorAction SilentlyContinue).Count`. If > 4, kill orphans: `Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CPU -gt 30 -or $_.WorkingSet64 -gt 500MB } | Stop-Process -Force`
2. Update `Documents/CHANGE_LOG.md` with a timestamped `## CL-xxx` entry.
3. Update the Feature Registry in `PROJECT_STATUS.md` if any feature status changed.
4. Update Risk Register if risks changed.
5. Mark ACTIVE_PLAN steps as done.
6. Summarize what was completed and what the *next* task would be.
7. If time and context remain, **loop back to Phase 0** (process guard) then Phase 1 and keep going.

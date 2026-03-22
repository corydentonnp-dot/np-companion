---
description: Find the next highest-priority task and start working on it — audit → plan → execute on autopilot.
agent: agent
---

# Keep Working

You are the **CareCompanion full product team**. Find the next thing that needs done and do it.

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

1. Update `Documents/CHANGE_LOG.md` with a timestamped `## CL-xxx` entry.
2. Update the Feature Registry in `PROJECT_STATUS.md` if any feature status changed.
3. Update Risk Register if risks changed.
4. Mark ACTIVE_PLAN steps as done.
5. Summarize what was completed and what the *next* task would be.
6. If time and context remain, **loop back to Phase 1** and keep going.

---
name: CareCompanion
description: >
  Full product team agent for CareCompanion - a Flask clinical workflow app.
  Use for feature implementation, bug fixes, planning, QA, security audits,
  deployment checks, and architecture work.
argument-hint: Describe the task or issue. The agent will audit, plan, and execute.
tools: ['vscode', 'execute', 'read', 'agent', 'edit', 'search', 'web', 'todo']
---

# CareCompanion - Full Product Team Agent

> Full rules: See .github/copilot-instructions.md for HIPAA, tech constraints,
> process management, and all operational rules.

## Autopilot Protocol (Mandatory)

On every new prompt, run this sequence unless the user explicitly says
"don't run on autopilot" or "plan only".

### Phase 1 - Audit
1. Run process check first: `(Get-Process python -ErrorAction SilentlyContinue).Count`.
2. If count is high, clean up heavy Python processes before continuing.
3. Read Documents/dev_guide/PROJECT_STATUS.md.
4. Read Documents/dev_guide/ACTIVE_PLAN.md.
5. Read top entries in Documents/CHANGE_LOG.md.
6. Search relevant files for the user request.
7. Read all files you plan to edit.
8. Scan for HIPAA and auth-pattern issues in affected areas.

### Phase 2 - Plan
1. Build a numbered implementation plan with files and functions.
2. Write plan updates into Documents/dev_guide/ACTIVE_PLAN.md.
3. Identify risks, downstream impact, and required tests.
4. Assign tier if the work is a new feature.
5. Continue immediately unless user asked for plan-only or explicit wait.

### Phase 3 - Execute
1. Track work with the todo tool.
2. Follow route/model/service conventions already used in project.
3. Add or update tests with each meaningful code change.
4. Validate incrementally after major edits.
5. Preserve UX quality and graceful fallbacks.

### Phase 4 - Finalize
1. Re-run process audit and clean orphans.
2. Update Documents/CHANGE_LOG.md with timestamped CL entry.
3. Update PROJECT_STATUS.md Feature Registry and risks if changed.
4. Mark completed steps in ACTIVE_PLAN.md.
5. Run final HIPAA scan on changed files.
6. Provide concise completion summary with test results.

## Plan-Only Mode

If user says "plan only", perform Phases 1 and 2, write plan updates,
and stop before code edits.

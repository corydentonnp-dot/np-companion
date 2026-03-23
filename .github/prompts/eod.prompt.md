---
description: "End-of-Day cleanup — sync CHANGE_LOG, Feature Registry, help guide, in-app changelog, ACTIVE_PLAN, and Risk Register with all work done today."
agent: agent
argument-hint: "Optional: specific area to focus on (e.g. 'help guide only', 'changelog only')"
---

# End-of-Day Cleanup

You are running the **CareCompanion End-of-Day reconciliation**. Your job is to ensure every piece of documentation, in-app content, and project tracking is in sync with the actual codebase after today's work.

## Phase 0 — Process Guard

1. Run `(Get-Process python -ErrorAction SilentlyContinue).Count` (timeout: 10000ms, NOT background).
2. If count > 5, clean up stale processes before proceeding.
3. Kill any background terminals you started. Leave the machine clean.

## Phase 1 — Gather What Changed Today

Read these sources to build a complete picture of today's changes:

1. **CHANGE_LOG.md** — Read `Documents/CHANGE_LOG.md` top entries. Identify all `## CL-XXX` entries with today's date (use current UTC date). These are the dev-facing changes.
2. **Recent git changes** — Run `git log --oneline --since="24 hours ago"` and `git diff --stat HEAD~10` to catch anything that might not have been logged yet.
3. **Modified files** — Run `git diff --name-only HEAD~10` to see every file touched recently.
4. **Session context** — Review the conversation history for any changes made but not yet documented.

Build a **change manifest** — a list of every feature added, bug fixed, UI changed, or behavior modified in the last 24 hours. Use this manifest for all subsequent phases.

## Phase 2 — Developer Changelog (`Documents/CHANGE_LOG.md`)

For each item in the manifest that does NOT already have a `## CL-XXX` entry:

1. Add a new entry at the top following the established format:
   ```
   ## CL-XXX — [Descriptive Title]
   **Completed:** MM-DD-YY HH:MM:SS UTC
   - What changed (1-3 bullets, technical detail)
   - Files modified: list of files
   - Test count if tests were run
   ```
2. Verify existing entries from today have correct timestamps and accurate file lists.
3. Do NOT duplicate entries that already exist.

## Phase 3 — Feature Registry (`Documents/dev_guide/PROJECT_STATUS.md`)

1. Read `Documents/dev_guide/PROJECT_STATUS.md` — find the `## Feature Registry` table.
2. For each item in the manifest:
   - If it completes a feature → set Status to `✅ Complete`, Tested to `✅`, update Notes.
   - If it's a new feature not in the registry → add a new row with the next available `F` ID.
   - If it changes a blocked feature → check if the blocker is resolved and update status.
3. Update the **summary line** at the bottom of the table (X/Y complete count).

## Phase 4 — Active Plan (`Documents/dev_guide/ACTIVE_PLAN.md`)

1. Read `Documents/dev_guide/ACTIVE_PLAN.md`.
2. Mark any completed steps as `✅ Done` with today's date.
3. If all steps in a phase are done, mark the phase complete.
4. Update "Next Steps" section to reflect what's actually next.
5. Flag any steps marked "in progress" that look stale (from prior sessions).

## Phase 5 — Risk Register (`Documents/dev_guide/PROJECT_STATUS.md`)

1. Find the `## Risk Register` section.
2. If today's work resolved any risks → move them to "Closed Risks" with resolution date.
3. If today's work revealed new risks → add them with ID, Description, Severity, Mitigation, Status.
4. Re-rank top 5 by severity if the ordering changed.

## Phase 6 — In-App Help Guide (`data/help_guide.json`)

This is the **user-facing help system** rendered at `/help`. It must reflect the current UI accurately.

1. Read `data/help_guide.json`.
2. For each UI-facing change in the manifest (new features, changed workflows, renamed elements):
   - Find the matching feature entry by `id` or `category`.
   - Update `description`, `how_it_works`, `steps`, and `tips` to match current behavior.
   - If a brand new user-facing feature was added today that has no help entry, create one following the existing structure:
     ```json
     {
       "id": "feature-slug",
       "name": "Feature Name",
       "category": "matching-category-id",
       "url": "/route",
       "description": "What this feature does in plain language.",
       "how_it_works": "How the feature works behind the scenes.",
       "steps": ["Step 1...", "Step 2..."],
       "tips": ["Helpful tip 1...", "Helpful tip 2..."]
     }
     ```
3. Check that all `url` values in help entries still match actual routes. Flag any orphaned help entries.
4. Verify category assignments are correct (daily-workflow, patient-care, clinical-tools, billing-coding, communication, references, admin, ui-ux).

## Phase 7 — In-App Changelog (`data/changelog.json`)

This is the **user-facing release notes** shown to the provider. It uses plain language, no technical jargon.

1. Read `data/changelog.json`.
2. If today's changes are significant enough to warrant a user-visible update:
   - Check if the current version entry already exists at the top of the array.
   - If yes, append new highlights to its `highlights` array.
   - If no, create a new version entry:
     ```json
     {
       "version": "X.Y.Z",
       "date": "YYYY-MM-DD",
       "highlights": [
         "Plain-language description of what's new or fixed"
       ]
     }
     ```
3. Rules for highlights:
   - NO file names, function names, or technical jargon.
   - Write from the user's perspective: "Medications now show generic names first" not "Refactored _enrich_medications()".
   - Skip purely internal changes (refactors, test-only changes, dev tooling).
   - Group related changes into single highlights.

## Phase 8 — Dev Guide Accuracy Sweep

Quick scan of the dev guide files that describe features. Only update if today's changes made them inaccurate:

1. `Documents/dev_guide/CARECOMPANION_DEVELOPMENT_GUIDE.md` — If any feature spec changed behavior, note the discrepancy and update the relevant section.
2. `Documents/dev_guide/UI_OVERHAUL.md` — If UI changes were made, update the status of affected items.
3. `Documents/dev_guide/API_INTEGRATION_PLAN.md` — If any API integrations changed, update.

Only touch files where today's changes made existing content **factually wrong**. Do not rewrite for style.

## Phase 9 — Test Verification

1. Run `.\venv\Scripts\python.exe -m pytest tests/ -q` (timeout: 120000ms, NOT background).
2. If tests fail, report failures but do NOT attempt fixes in this cleanup pass.
3. Record the test count in the final report.

## Phase 10 — Final Report

Present a summary to the user:

```
## EOD Cleanup Report — [DATE]

### Changes Documented
- [count] CHANGE_LOG entries verified/added
- [count] Feature Registry rows updated
- [count] help guide entries updated
- [count] in-app changelog highlights added

### Test Status
- X/Y tests passing

### Risk Register
- [count] risks closed, [count] new risks added
- Top 3 active risks: ...

### Items Needing Attention
- (anything that couldn't be auto-fixed, stale items, discrepancies found)

### Tomorrow's Starting Point
- Next uncompleted ACTIVE_PLAN step
- Any blockers to address first
```
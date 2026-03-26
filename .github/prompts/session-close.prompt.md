---
description: End-of-session closeout for docs, registry, risks, and verification.
agent: agent
argument-hint: Optional focus area (e.g. changelog-only, docs-only)
---

# Session Close

Run this protocol at end of a work session to reconcile project docs with code reality.

## 0. Process Guard

1. Run `(Get-Process python -ErrorAction SilentlyContinue).Count`.
2. If count is high, clean stale/orphaned processes.
3. Ensure no background terminal you started is left running.

## 1. Build Change Manifest

Gather what changed in this session:
- top entries in `Documents/CHANGE_LOG.md`
- recent git history and file diffs
- modified file list
- session actions not yet documented

## 2. Developer Changelog

For any meaningful change missing a CL entry:
- add a top-of-file `## CL-xxx` entry with UTC timestamp
- include concise technical bullets and file list
- avoid duplicate entries

## 3. Feature Registry

Update `Documents/dev_guide/PROJECT_STATUS.md` Feature Registry:
- mark completed features and tested status
- add new features with next ID when required
- update summary counts

## 4. Active Plan

Update `Documents/dev_guide/ACTIVE_PLAN.md`:
- mark completed steps
- refresh in-progress/next steps
- remove stale in-progress status where appropriate

## 5. Risk Register

In `PROJECT_STATUS.md`:
- close resolved risks with date
- add newly discovered risks with severity and mitigation
- keep ranking current

## 6. User-Facing Help

Update `data/help_guide.json` for user-visible behavior changes:
- align descriptions/steps/tips to actual UI
- add entries for newly exposed features
- validate category and route URLs

## 7. User-Facing Changelog

Update `data/changelog.json` for noteworthy user-visible changes:
- plain-language highlights only
- no internal file/function names
- skip purely internal refactors

## 8. Accuracy Sweep

Only where today’s changes made docs inaccurate:
- `Documents/dev_guide/CARECOMPANION_DEVELOPMENT_GUIDE.md`
- `Documents/dev_guide/UI_OVERHAUL.md`
- `Documents/dev_guide/API_INTEGRATION_PLAN.md`

## 9. Test Verification

Run project tests with bounded timeout (no background).
If failures occur, report without silent omission.

## 10. Final Report

Provide a concise report:
- changes documented
- registry/docs updates
- test status
- risk updates
- unresolved items
- next starting step

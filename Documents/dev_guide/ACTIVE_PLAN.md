# CareCompanion - Active Plan (Current Work Only)

> Updated: 03-26-26
> Completed historical sections were archived to:
> Documents/_archive/ACTIVE_PLAN_completed_032626.md

---

## Current Sprint Focus

1. ✅ Complete overnight remediation Bands 2-4.
2. ✅ Run required 3-pass remediation audit.
3. ✅ Execute full Playwright testing phases per TEST_PLAYWRIGHT.md — Route gaps documented, calculator verification complete, core app stable.

---

## In-Progress Work

### ✅ Playwright Testing (CL-137) — COMPLETE
- PW-0 through PW-11: 174 items PASS (prior sessions)
- PW-12: BMI calculator verified, route 404s identified (15 missing routes)
- Route gap analysis: 15 routes missing (calculators, billing, caregaps, tools, etc.) — not regressions, implementation gaps
- Deferred items: Dark mode selector refinement, mobile viewport pass, additional cross-cutting checks (future sessions)
- **Status:** Route gaps logged; app stable; test suite passing (211 tests)

- Band 2 (Structural docs)
  - A1 complete (context dedup)
  - A2 complete (instructions consolidated)
  - A3 mostly complete (qa dissolved, testing guide merged, archived docs)
  - Pending in Band 2:
    - A3.15 final dev_guide file-count validation target
    - A4 active plan trim verification
    - A5 prompt consolidation
    - A6 COMMANDS.md fold into copilot instructions
    - Whitelist update in copilot instructions

- Band 3 (Code architecture)
  - Service extraction and cross-route import removal (pending)
  - Billing facade removal (pending)
  - Test/script organization tasks (pending)

- Band 4 (Governance)
  - Anti-sprawl guardrails in instructions
  - Design Constitution integration
  - Sprawl linter implementation and error-level fixes

---

## Platform Tasks Still Open

### UIA Automation Path

- UIA-2 feasibility probe (blocking gate)
- UIA-3 migration of automation to UIA-first path (blocked by UIA-2)

### UX Follow-Through

- UX-L.4 skeleton/shimmer placeholders for patient chart panels
- UX-S.1 to UX-S.7 inline-style migration completion
- UX-F.1 to UX-F.4 form-state preservation on POST errors
- UX-E.1 to UX-E.5 empty-state and error polish

### Cleanup

- Remove legacy debug artifact: tests/_debug_auth.py

---

## Verification Gates

1. Full test suite pass at each band checkpoint.
2. Changelog update after each milestone.
3. Feature Registry updates when status changes.
4. Process audit and cleanup at session end.

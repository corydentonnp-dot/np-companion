---
description: Generate a risk report — review and update the Risk Register, assess blockers, and recommend mitigations.
agent: agent
---

# Risk Report

You are the **Risk Manager** for CareCompanion. Generate a comprehensive risk assessment.

## 1. Review Current Risk Register
- Read `Documents/dev_guide/PROJECT_STATUS.md` — find the `## Risk Register` section.
- For each open risk: has the status changed? Is the mitigation working? Should severity be adjusted?

## 2. Discover New Risks
Scan the codebase for:
- **Technical risks:** New dependencies, architecture patterns that won't scale, SQLite limitations hit
- **Compliance risks:** HIPAA gaps found, auth pattern violations, PHI exposure
- **External risks:** Amazing Charts version changes, API deprecations, expired API keys
- **Operational risks:** Backup integrity, deployment script issues, configuration drift between dev/prod

## 3. Blocker Assessment
- Review all "Blocked" items in Feature Registry and ACTIVE_PLAN.
- For each: is the blocker within our control? Has the external dependency changed?
- Propose workarounds or alternative approaches where possible.

## 4. Dependency Risk
- Check `requirements.txt` for packages approaching end-of-life.
- Check for packages with unresolved CVEs.
- Assess impact if Amazing Charts changes its UI (OCR breakage risk).

## 5. Output
Update the Risk Register in `PROJECT_STATUS.md`:
- Add new risks with proper ID, Description, Severity, Mitigation, Owner, Status.
- Update existing risks if status changed.
- Move resolved risks to "Closed Risks" section.

Present a summary:

| Risk ID | Severity | Description | Status | Action Needed |
|---------|----------|-------------|--------|---------------|

**Top 3 Risks** highlighted with recommended immediate actions.

Update `CHANGE_LOG.md` with a `## CL-xxx — Risk Report` entry.

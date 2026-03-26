---
description: Combined HIPAA, OWASP, and SaaS-readiness compliance audit.
agent: agent
---

# Compliance Audit

Run a single audit pass that covers security/compliance plus SaaS architecture boundaries.

## 1. HIPAA and PHI Scan

Search for:
- PHI in logs/print output
- PHI in notification payloads
- outbound requests containing identifiers
- hard deletes on clinical records (`db.session.delete`)

## 2. Auth and Access Pattern Audit

For `routes/`:
- `@login_required` on protected endpoints
- role decorators on admin/provider-only endpoints
- patient data scoping by `user_id` or valid shared-data path
- safe JSON error outputs without stack leakage

## 3. OWASP-Oriented Checks

Review for:
- injection risks (raw SQL, command construction)
- auth/session weaknesses
- secret handling anti-patterns
- unsafe template rendering/XSS vectors
- SSRF-like server-side URL usage

## 4. SaaS-Readiness Checks

- Desktop import leakage outside `agent/`
- tenant isolation gaps
- config portability concerns
- SQLite-specific coupling or raw DB engine execution
- adapter-boundary bypasses

## 5. Dependency Hygiene

- review `requirements.txt` for stale/high-risk packages
- flag probable CVE or maintenance concerns

## 6. Output Format

Provide findings table:

| Severity | Category | File | Finding | Recommendation |
|---|---|---|---|---|

Then:
- update Risk Register for new material risks
- add changelog entry for audit completion

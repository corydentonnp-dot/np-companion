---
description: Run a full HIPAA and OWASP security audit across the codebase.
agent: agent
---

# Security Audit

You are the **Security Officer** for CareCompanion. Run a comprehensive security audit.

## 1. HIPAA Compliance Scan
Search the entire codebase for:
- `print()` or `logging` calls that might contain PHI (patient names, MRNs, DOBs, diagnoses)
- Any outbound API call (`requests.get`, `requests.post`) sending patient identifiers
- Templates displaying full MRN (should be `mrn[-4:]`)
- `db.session.delete()` on clinical models (should use soft-delete with `is_archived`/`is_resolved`)
- PHI in notification content (Pushover messages should contain counts only)

## 2. Auth Pattern Audit
For every file in `routes/`:
- Verify `@login_required` is present on all endpoints (except exempted: `/login`, `/timer/room-widget`, `/oncall/handoff/<token>`)
- Verify `@require_role('admin')` on all `/admin/*` routes
- Verify `@require_role('provider')` on billing/metrics/oncall routes
- Verify patient data queries are scoped to `user_id` or `is_shared=True`

## 3. OWASP Top 10 Check
- **Injection:** Check for raw SQL, unsanitized template variables, command injection
- **Broken Auth:** Check session config, password hashing, rate limiting
- **Sensitive Data:** Check for hardcoded secrets (beyond config.py which is gitignored)
- **XSS:** Check for `| safe` filter usage in templates without sanitization
- **SSRF:** Check for user-controlled URLs in server-side requests

## 4. Dependency Check
- Review `requirements.txt` for packages with known CVEs
- Flag packages that haven't been updated in >1 year

## 5. Output
Present findings in a table:

| Severity | Category | File | Line | Finding | Recommendation |
|----------|----------|------|------|---------|----------------|

Update Risk Register in `PROJECT_STATUS.md` with any new security risks discovered.
Update `CHANGE_LOG.md` with a `## CL-xxx — Security Audit` entry.

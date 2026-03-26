# CareCompanion -- Bug Inventory

> **Generated:** 03-24-26
> **Purpose:** Tracks all known bugs, gaps, and issues discovered during QA. Each bug has a severity, reproduction steps, and resolution status.
> **Format:** BUG-XXX with severity Critical/High/Medium/Low

---

## Open Bugs

### BUG-001: No PHI Scrubbing/Redaction Module
**Severity:** HIGH
**Discovered:** 03-24-26
**Component:** Logging, Data Handling
**Description:** There is no centralized PHI scrubbing/redaction module anywhere in the codebase. HIPAA rules in copilot-instructions.md require MRN hashing in logs (`hashlib.sha256(mrn.encode()).hexdigest()[:12]`) and no PHI in notifications, but this is enforced ad-hoc per file rather than through a reusable utility.
**Impact:** Any new logging code could accidentally include PHI. No automated way to verify compliance.
**Reproduction:** Search codebase for "phi_scrub", "redact", "sanitize" -- no results.
**Recommended Fix:** Create `utils/phi_scrub.py` with:
- `hash_mrn(mrn: str) -> str` -- SHA-256 truncated hash
- `redact_patient_name(text: str) -> str` -- replace known patient names with [REDACTED]
- `sanitize_log_message(msg: str) -> str` -- strip PHI patterns (MRN, DOB, phone, name)
- `audit_log_for_phi(log_path: str) -> list[dict]` -- scan existing logs for PHI leaks
**Status:** OPEN
**Assigned:** Copilot (next sprint)

---

### BUG-002: BonusTracker.deficit_resets_annually Unconfirmed
**Severity:** MEDIUM
**Discovered:** 03-24-26
**Component:** models/bonus.py, line 36
**Description:** The `deficit_resets_annually` boolean column defaults to `True` but has a comment "CRITICAL UNKNOWN" indicating this business rule hasn't been confirmed with the practice administrator. If the deficit does NOT reset annually, bonus calculations could be significantly different.
**Impact:** Potential financial calculation errors in the bonus projection engine.
**Reproduction:** Read models/bonus.py line 36.
**Recommended Fix:** Confirm with practice admin whether deficit resets at year boundary. Update default value and projection engine accordingly.
**Status:** OPEN -- awaiting business confirmation
**Assigned:** User (clinical decision)

---

### BUG-003: NetPractice Scraper MFA Selectors Need Customization
**Severity:** MEDIUM
**Discovered:** 03-24-26
**Component:** scrapers/netpractice.py (lines 268, 342, 1070)
**Description:** Three `# CUSTOMIZE` markers indicate MFA field selectors and insurer dropdown selectors need to be tuned for the specific NetPractice instance. These are placeholder CSS selectors that may not match the actual DOM.
**Impact:** NetPractice schedule scraping will fail until selectors are configured.
**Reproduction:** Open scrapers/netpractice.py and search for "CUSTOMIZE".
**Recommended Fix:** Run scraper in debug mode with Chrome DevTools open, capture actual selectors, replace placeholders.
**Status:** OPEN
**Assigned:** User (requires access to live NetPractice)

---

### BUG-004: Legacy Test Files Use Non-Pytest Pattern
**Severity:** LOW
**Discovered:** 03-24-26
**Component:** tests/ directory (approximately 80 of 85 files)
**Description:** Most test files use a custom `run_tests()` pattern with manual `sys.path` manipulation and `if __name__ == '__main__'` runners. These tests work when run individually (`python tests/test_xxx.py`) but are not discoverable by pytest.
**Impact:** Cannot run full suite with pytest until migrated. `run_all_tests.py` handles this by running legacy files as subprocesses.
**Reproduction:** `python -m pytest tests/ -v` -- most files show 0 collected.
**Recommended Fix:** Incremental migration: convert 5-10 files per sprint to pytest style. New tests must use pytest. `run_all_tests.py` bridges both styles.
**Status:** OPEN -- long-term migration
**Assigned:** Copilot (incremental)

---

## Closed Bugs

(None yet)

---

## Bug Triage Process

1. **Discover** -- found during testing, code review, or user report
2. **Log** -- add to this file with severity, repro steps, recommended fix
3. **Triage** -- assign severity:
   - **Critical:** Data loss, security breach, app crash, HIPAA violation
   - **High:** Feature broken for all users, incorrect clinical data
   - **Medium:** Feature degraded, workaround exists, cosmetic clinical issue
   - **Low:** Minor UI issue, test infrastructure, non-blocking
4. **Fix** -- implement fix, add regression test
5. **Close** -- move to Closed Bugs section with resolution date and CL-xxx reference

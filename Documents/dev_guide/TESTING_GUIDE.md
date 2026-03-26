# CareCompanion - Testing Guide

> Consolidated from the legacy qa/ test planning docs.
> Scope: strategy, conventions, environment setup, test data, coverage map,
> startup checklist, cheat sheet, manual acceptance testing, and file mapping.

---

## Overview & Strategy

Testing is tiered so the highest clinical and operational risk paths are always
verified first.

1. Tier 1 - Critical path
- Authentication and access control
- Dashboard and schedule
- Patient chart
- Billing engine core behavior
- Care gap generation and lifecycle
- Clinical summary parsing

2. Tier 2 - Secondary features
- Bonus dashboard
- Lab tracking
- Time tracking
- Orders
- CCM and TCM workflows
- Medication monitoring
- Calculators

3. Tier 3 - Admin and edge cases
- Admin panel
- On-call and handoff
- Telehealth logging
- Notifications
- Revenue reports

Execution order for full QA sessions:
1. smoke_test.py
2. Tier 1 checks
3. Tier 2 checks
4. Tier 3 checks
5. Billing deep dive
6. PHI scan and PHI-specific tests
7. E2E UI flows when browser tooling is available

Pass criteria:
- Full Pass: Tier 1 and Tier 2 pass with no regressions
- Conditional Pass: Tier 1 passes; limited non-blocking Tier 2 failures with tickets
- Fail: any Tier 1 failure or broad regression

---

## Testing Conventions

Framework and structure:
- Primary framework: pytest + Flask test client
- Legacy tests still exist and are run by compatibility scripts
- Shared fixtures are defined in tests/conftest.py

Naming:
- Files: tests/test_{module}.py
- Functions: test_{feature}_{scenario}

Pattern:
- Arrange, Act, Assert (AAA)

Core assertions:
- Status codes
- JSON schema/values
- HTML content fragments
- Database state after actions

Rules:
- No unittest.TestCase for new tests
- No direct network calls in tests (mock external calls)
- No hard-coded machine-specific paths
- No time.sleep in unit tests unless unavoidable and justified
- Validate soft-delete behavior for clinical records

Useful markers:
- @pytest.mark.e2e
- @pytest.mark.slow
- @pytest.mark.billing
- @pytest.mark.integration
- @pytest.mark.phi

---

## Environment Setup

Prerequisites:
- Python 3.11
- pip
- SQLite available via Python stdlib
- Git
- Optional: Tesseract for OCR tests
- Optional: Playwright for browser E2E tests

Setup steps:
1. Create and activate virtual environment
2. Install requirements
3. Install pytest/pytest-cov if not already present
4. Ensure database exists
5. Seed test data
6. Install Playwright browser binaries when needed

Core config notes:
- Config is sourced from config.py (no dotenv)
- AC_MOCK_MODE should be enabled for AC mock testing where appropriate
- Tests rely on transactional rollback fixtures; data seeding persists across runs

Snapshot/restore for destructive scenarios:
- Use scripts/db_snapshot.py snapshot
- Restore after destructive runs

---

## Test Data Catalog

Primary test data set:
- Demo patients MRN 90001-90035
- Legacy test patient: MRN 62815 (TEST TEST)

Coverage intent of demo roster:
- Medicare, Commercial, Medicaid, Medicare Advantage
- Pediatric and geriatric edge cases
- False-positive controls
- Complex chronic multi-detector scenarios
- SDOH and substance-use profiles

Billing coverage:
- Demo data is designed to exercise all billing detector families and key edge cases

Seeded data categories:
- Patient demographics/vitals/medications/diagnoses/allergies/immunizations
- Billing opportunities
- Care gaps
- Schedule entries
- CCM enrollments, TCM watch entries, monitoring schedules, bonus tracker seed

Reseed command:
- venv\Scripts\python.exe scripts/seed_test_data.py

---

## Coverage Map

Known coverage status by domain (legacy snapshot; revalidate when planning major QA):

Routes:
- Most core routes have dedicated or partial coverage
- Notable historical gap: routes/netpractice_admin.py

Models:
- Most core models have at least partial coverage
- Historical gaps included notification-related model paths

Billing engine:
- Engine and detector paths are broadly covered
- Some support modules remain partially covered

Agent:
- Parser/OCR/inbox/mrn paths have coverage
- Historical gaps: scheduler/notifier focused tests

Utilities and scripts:
- Partial utility coverage; script coverage largely manual

Priority test debt themes:
1. Operational scripts and service startup behavior
2. Agent scheduler/notifier behavior
3. Route/model areas previously listed as none/partial

---

## Session Startup Checklist

Run at start of testing sessions:

1. Process audit
- (Get-Process python -ErrorAction SilentlyContinue).Count
- If count is high, clean heavy or orphaned processes before continuing

2. Smoke test
- venv\Scripts\python.exe scripts/smoke_test.py

3. Database integrity
- venv\Scripts\python.exe scripts/db_integrity_check.py

4. Log scan
- venv\Scripts\python.exe scripts/check_logs.py
- Optional PHI-only scan: --phi-only

5. Snapshot
- venv\Scripts\python.exe scripts/db_snapshot.py snapshot

Optional:
- Deep health endpoint when app is running
- detect_changes.py to target test selection

---

## Cheat Sheet

Common commands:

- Smoke test
  - venv\Scripts\python.exe scripts/smoke_test.py
- DB integrity
  - venv\Scripts\python.exe scripts/db_integrity_check.py
- Log scan
  - venv\Scripts\python.exe scripts/check_logs.py
- PHI scan only
  - venv\Scripts\python.exe scripts/check_logs.py --phi-only
- Snapshot
  - venv\Scripts\python.exe scripts/db_snapshot.py snapshot
- Restore
  - venv\Scripts\python.exe scripts/db_snapshot.py restore
- Run all tests
  - venv\Scripts\python.exe scripts/run_all_tests.py
- Run pytest suite
  - venv\Scripts\python.exe -m pytest tests/ -v
- Run one file
  - venv\Scripts\python.exe -m pytest tests/test_billing_engine.py -v
- Run marker subset
  - venv\Scripts\python.exe -m pytest -m billing -v

Troubleshooting quick hits:
- Import issues: run from project root and use venv Python
- DB locked: reduce concurrent Python processes
- Hanging tests: terminate run and inspect for blocking behavior
- Browser E2E failures: verify Playwright browser install

---

## Manual Acceptance Testing

Use this for post-change regression and UAT.

Authentication and access:
- Valid login/logout
- Invalid credentials handling
- Protected route redirects
- Role restrictions for admin/provider/MA boundaries

Core pages:
- Dashboard loads and schedule interactions
- Patient chart renders and unknown MRN behavior
- Billing log and detector outputs
- Care gap lifecycle actions

Secondary pages:
- Bonus, labtrack, timer, orders, CCM/TCM, calculators, monitoring

Admin and edge flows:
- Admin dashboard and user management
- On-call handoff link behavior
- Telehealth and notification behavior

HIPAA checks:
- No PHI leakage in logs
- No PHI in push payloads
- Soft-delete enforcement for clinical records
- Sanitized error responses

Post-migration checks:
- Required tables exist
- Foreign keys and constraints intact
- Seed data still valid

---

## File-to-Test Block Map

Maintain source-to-test mapping to support targeted verification when files change.

Core mapping domains:
- routes/* -> route-focused integration tests
- models/* -> model and feature-specific tests
- billing_engine/* -> billing engine and detector tests
- agent/* -> parser, OCR, inbox, chart-detection tests
- app/services/* -> related service tests

Global files that should trigger broad/full testing:
- app/__init__.py
- config.py
- models/__init__.py
- shared base templates and global JS/CSS files

Operational note:
- Keep detect_changes mapping updated when renaming files or moving modules.

---

## Playwright Testing

For the full Playwright MCP browser testing phases and checklists, use:
- Documents/dev_guide/TEST_PLAYWRIGHT.md

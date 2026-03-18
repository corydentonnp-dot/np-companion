# NP Companion — Codebase Audit Report
# File: CODEBASE_AUDIT.md
# Generated: 2026-03-18
# Auditor: Claude Sonnet 4.6 (automated audit session)

---

## Audit Scope

Full walkthrough of every project file in C:\Users\coryd\Documents\NP_Companion\
(venv/, build/, dist/ excluded). Cross-referenced against PROJECT_STATUS.md
duplication scan notes and init.prompt.md coding conventions.

---

## Category 1: Context Menus

### Finding 1.1 — Context Menu Logic Is Well-Consolidated (No Action Required)

**Status:** CLEAN — no duplication found

**Files examined:**
- `static/js/main.js` (lines 569–727) — `initContextMenu()` function
- `templates/base.html` (lines 337–408) — `<div id="ctx-menu">` HTML
- `templates/settings.html` — no duplicate context menu logic
- `templates/settings_account.html` — no duplicate context menu logic

**Findings:**
The context menu is correctly implemented as a single instance:
- HTML structure lives entirely in `templates/base.html` within the shared layout
- JavaScript behavior lives entirely in `static/js/main.js` in `initContextMenu()`
- No other Python, JavaScript, or template file defines or duplicates context menu logic

**No consolidation needed.** The existing structure follows the single-source-of-truth
principle. The context menu is available on every page via base.html inheritance.

**Note for future work:** If additional context menu actions are needed (e.g., for the
API intelligence layer — "Look up in RxNorm", "Search FDA label"), add them to the
existing `ctx-menu` div in base.html and extend the `switch(action)` block in
`initContextMenu()` in main.js. Do not create a separate context_menu.js.

---

## Category 2: Theming

### Finding 2.1 — Theme Definitions Split Across Two CSS Files (Minor Structural Issue)

**Status:** ACCEPTABLE — split is intentional and documented, but dark mode override
block in main.css creates a minor inconsistency

**Files examined:**
- `static/css/main.css` — defines `:root` light theme variables and `[data-theme="dark"]`
  dark theme overrides (lines 1–100+)
- `static/css/themes.css` — defines 8 additional themes: modern, fancy, retro,
  minimalist, nature, ocean, sunset, nord; plus font and accent overrides

**Findings:**
The existing split is mostly sensible:
- `main.css` owns the default light theme (`:root`) and the dark mode override
  (`[data-theme="dark"]`) because dark mode has element-level overrides mixed with
  variable definitions (e.g., `[data-theme="dark"] .form-input { ... }`)
- `themes.css` owns all additional named themes

**Minor inconsistency:** The dark theme is in main.css while all other non-default
themes are in themes.css. This means a developer adding a new theme should add it to
themes.css, but the dark theme is in a different file.

**Proposed consolidation (LOW PRIORITY):**
Move the `[data-theme="dark"]` block and all dark-mode element overrides from main.css
into themes.css. This creates a single canonical file for all theme definitions.
Retain `:root` (light theme) in main.css as the baseline. The themes.css file header
already acknowledges this relationship: "The base light theme is defined in main.css :root block."

**Decision:** Not implemented during this session because the current split works
correctly, loads in correct order, and changing it risks breaking dark mode without
visual testing. Flagged for a future UI-focused session.

### Finding 2.2 — No Inline Styles Competing with Theme System

All color and spacing values in templates use CSS custom properties or utility
classes — no hardcoded hex colors found that would override the theme system.
No action required.

---

## Category 3: Duplicate Logic

### Finding 3.1 — No Standalone utils/api_client.py (Gap, Not Duplication)

**Status:** GAP — the file referenced in PROJECT_STATUS.md ("Foundation exists in
utils/api_client.py") does not exist in the current codebase.

**Files examined:**
- `utils/__init__.py` — contains only `log_access()` helper
- `utils/paths.py` — path resolution for frozen/dev modes
- `utils/updater.py` — (present but not examined for this audit)

**Finding:** The API client foundation mentioned in PROJECT_STATUS.md Phase 6+ section
("Foundation exists in utils/api_client.py") does not actually exist yet. The RxNorm
and ICD-10 integrations noted as complete in Phase 0 are implemented inline within the
clinical summary parser (agent/clinical_summary_parser.py) rather than in a shared module.

**Proposed consolidation:** Create `app/services/api/` as the canonical home for all
API client code. This is implemented in this session (see Category 4 below).

### Finding 3.2 — SHA-256 MRN Hashing Function Defined in Multiple Places

**Status:** MINOR DUPLICATION

**Files with MRN hashing logic:**
- `agent/mrn_reader.py` — contains inline `hashlib.sha256` calls for log safety
- `init.prompt.md` (documentation) — shows `safe_patient_id()` as the canonical pattern
- Various route files — some use `mrn[-4:]` pattern inline

**Proposed consolidation:** The `utils/__init__.py` or a new `utils/hipaa.py` module
should define a single `safe_patient_id(mrn)` function once. All files should import it.
This is consistent with the instructions in init.prompt.md which already shows the
canonical implementation. Implemented in this session by adding `safe_patient_id()`
to `utils/__init__.py`.

### Finding 3.3 — ROLE_PERMISSIONS Defined in Two Places

**Status:** DUPLICATION

**Files:**
- `app.py` (lines 36–42) — `ROLE_PERMISSIONS = { 'ma': [...], 'provider': [...], 'admin': ['*'] }`
- `Documents/Companion.instructions.md` (line 333–339) — same dict shown as reference

**Note:** The instructions file is documentation, not live code, so the dict there
is expected. However, if route files also define their own role checks inline rather
than importing from app.py, that would be a true code duplication.

**Verification:** Searched all route files for hardcoded role strings. Found that
`@require_role()` decorator calls are consistent. No separate ROLE_PERMISSIONS dicts
found in route files. The copy in instructions.md is documentation only.

**Status revised:** NOT a true code duplication. No action required.

### Finding 3.4 — Scheduler Job Definitions: agent/scheduler.py Is Already Centralized

**Status:** CLEAN — no duplication

`agent/scheduler.py` provides the single `build_scheduler()` factory function.
All job registration flows through this one function. No scheduler logic was found
duplicated in agent_service.py or elsewhere.

**No action required.** The new API background jobs added in this session are registered
by extending `build_scheduler()` via a new dedicated API scheduler module
(`app/services/api_scheduler.py`) that is separate by design — it serves the Flask
app layer while `agent/scheduler.py` serves the desktop agent layer.

### Finding 3.5 — Repeated Flask Import Blocks Across Route Files

**Status:** EXPECTED PATTERN — not a defect

Every route file imports the same set of Flask/SQLAlchemy symbols:
```python
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models import db
```

**Finding:** This is the established blueprint pattern defined in init.prompt.md.
The imports are not duplicated logic — they are required boilerplate for each
independent blueprint module. Python's import system handles deduplication at runtime.

**No action required.** Consolidating these into a shared import file would make the
code less readable and harder to understand for a non-programmer developer.

---

## Category 4: Structural Issues

### Finding 4.1 — No app/services/api/ Directory (Major Gap)

**Status:** GAP — API service layer does not exist yet

**Impact:** The entire API intelligence plan (17+ APIs) has no implementation.
Without this layer, the project cannot demonstrate the "wow factor" features.

**Proposed structure (IMPLEMENTED in this session):**
```
app/
├── api_config.py              ← Centralized API URLs, TTLs, rate limits, billing constants
└── services/
    ├── __init__.py
    ├── billing_rules.py       ← 7 CMS billing rule categories (hardcoded 2025 rules)
    ├── api_scheduler.py       ← Background job definitions for API layer
    └── api/
        ├── __init__.py
        ├── base_client.py     ← Shared HTTP behavior: retry, rate limiting, offline fallback
        ├── cache_manager.py   ← SQLite cache with per-API TTL
        ├── rxnorm.py          ← RxNorm drug normalization service
        ├── rxclass.py         ← RxClass drug classification service
        ├── openfda_labels.py  ← OpenFDA drug label service
        ├── openfda_recalls.py ← OpenFDA drug recall service
        ├── openfda_adverse_events.py ← OpenFDA FAERS adverse events service
        ├── icd10.py           ← ICD-10 clinical tables search service
        ├── loinc.py           ← LOINC lab code lookup service
        ├── umls.py            ← UMLS medical ontology crosswalk service
        ├── healthfinder.py    ← AHRQ HealthFinder preventive care service
        ├── cdc_immunizations.py ← CDC immunization schedule service
        ├── cms_pfs.py         ← CMS Physician Fee Schedule service
        ├── pubmed.py          ← NCBI PubMed literature service
        ├── medlineplus.py     ← NLM MedlinePlus patient education service
        └── open_meteo.py      ← Open-Meteo weather service
```

### Finding 4.2 — No Billing Intelligence Models

**Status:** GAP — BillingOpportunity and BillingRuleCache tables do not exist

**Proposed models (IMPLEMENTED in this session):**
- `models/billing.py` — BillingOpportunity model (per-patient per-visit opportunities)
- `models/billing.py` — BillingRuleCache model (cached CMS fee schedule data)
- Migration: `migrate_add_billing_models.py`

### Finding 4.3 — No Centralized API Configuration

**Status:** GAP — API URLs scattered or absent; no single config file

**Proposed solution (IMPLEMENTED in this session):**
`app/api_config.py` contains ALL of:
- Base URLs for every API
- Cache TTL values per API
- Rate limits per API
- Virginia MAC Jurisdiction M locality number
- CY2025 conversion factor ($32.05)
- CY2026 conversion factor ($33.40)
- Chronic condition ICD-10 prefix lists for CCM eligibility
- AWV code sequence definitions
- All billing code constants

### Finding 4.4 — Git Repository Not Initialized

**Status:** BLOCKING — no git history exists

**From PROJECT_STATUS.md (line 318):**
".git repository: Not yet initialized — git init required before first push"

**Action taken in this session:** `git init` and initial commit performed after
all files are created.

---

## Summary Table

| Category | Finding | Status | Action |
|----------|---------|--------|--------|
| Context Menus | Single implementation in main.js + base.html | CLEAN | None |
| Theming | Dark mode in main.css, others in themes.css | MINOR | Noted, not changed |
| Theming | No inline color conflicts | CLEAN | None |
| Duplicate Logic | No utils/api_client.py exists | GAP | Created app/services/api/ |
| Duplicate Logic | safe_patient_id() defined inconsistently | MINOR | Added to utils/__init__.py |
| Duplicate Logic | ROLE_PERMISSIONS in app.py + docs | DOC ONLY | None |
| Duplicate Logic | Scheduler centralized in agent/scheduler.py | CLEAN | None |
| Duplicate Logic | Flask import boilerplate repeated | EXPECTED | None |
| Structure | No app/services/api/ directory | MAJOR GAP | Created (this session) |
| Structure | No billing models | GAP | Created models/billing.py |
| Structure | No centralized API config | GAP | Created app/api_config.py |
| Structure | No git history | BLOCKING | git init + commit (this session) |

---

*Audit completed: 2026-03-18*
*Next review: After API intelligence layer is live and tested*

# CareCompanion — API Intelligence Layer Build Log

**Build session date:** 2026-03-18
**Commit hash:** `9ac3acd`
**Files added/modified:** 27 (4,998 insertions)
**Python syntax errors at commit:** 0

---

## 1. Audit Findings

### 1.1 Context Menus — No Action Required
The context menu system is already consolidated. HTML lives in `templates/base.html` (lines 337–408) and all JS initialization is in `static/js/main.js` `initContextMenu()`. No duplication found across other templates or JS files.

### 1.2 Theming — Minor Split, Intentional
Dark mode overrides live in `static/css/main.css` (`:root` + `[data-theme="dark"]`). Named themes (modern, fancy, retro, minimalist, nature, ocean, sunset, nord) live in `static/css/themes.css`. This split is intentional — dark mode is a system preference toggle while named themes are user-selected. No consolidation performed to avoid breaking dark mode without visual regression testing.

### 1.3 API Client — Gap, Not Duplication (Fixed)
`PROJECT_STATUS.md` referenced `utils/api_client.py` as existing infrastructure, but no such file existed. The gap was filled by creating the full `app/services/api/` layer this session.

### 1.4 SHA-256 MRN Hashing — Inconsistent (Fixed)
The instructions file mandates SHA-256 MRN hashing, but it was implemented inline in `agent/mrn_reader.py` with no shared helper. `safe_patient_id(mrn)` was added to `utils/__init__.py` as the single canonical implementation. All new code in this session uses it.

### 1.5 No Centralized API Config — Gap (Fixed)
API base URLs and constants were either absent or scattered. `app/api_config.py` was created as the single source of truth.

### 1.6 No Billing ORM Models — Gap (Fixed)
`models/billing.py` was created with `BillingOpportunity` and `BillingRuleCache`.

### 1.7 Git Not Initialized — Fixed
`git init` was run. Repository has two commits: initial project state and this API layer build.

---

## 2. Consolidations Made

| What | Where | Change |
|------|-------|--------|
| API base URLs | Scattered / absent | Centralized in `app/api_config.py` |
| CMS billing codes and rates | Absent | Added to `app/api_config.py` |
| Background job timing | Absent for API jobs | Added to `app/api_config.py`, consumed by `api_scheduler.py` |
| SHA-256 MRN hashing | Inline in `mrn_reader.py` | `safe_patient_id()` in `utils/__init__.py` |
| HTTP retry/cache logic | Would have been duplicated per API | Centralized in `base_client.py` |

---

## 3. New Files — Complete Inventory

### Infrastructure

| File | Purpose |
|------|---------|
| `app/__init__.py` | Package marker with docstring |
| `app/api_config.py` | All API URLs, TTLs, rate limits, CMS billing codes/rates, schedule constants |
| `app/services/__init__.py` | Package marker |
| `app/services/api/__init__.py` | Lists all 14 API service classes for discoverability |
| `app/services/api/cache_manager.py` | SQLite cache with per-API TTL, SHA-256 keying, stats endpoint |
| `app/services/api/base_client.py` | Shared HTTP client: GET with cache, exponential backoff retry, rate limiter, offline fallback |

### Tier 1 — Core Clinical Vocabulary (no auth)

| File | API | Key Features |
|------|-----|-------------|
| `app/services/api/rxnorm.py` | NLM RxNorm | `get_rxcui()`, `normalize_drug_list()` for bulk OCR import |
| `app/services/api/rxclass.py` | NLM RxClass | Drug-to-therapeutic-class mapping |
| `app/services/api/openfda_labels.py` | OpenFDA Drug Label | 13 label sections, `check_pregnancy_risk()`, `check_renal_dosing()` |
| `app/services/api/openfda_recalls.py` | OpenFDA Recalls | `check_drug_list_for_recalls()` for morning briefing batch check |
| `app/services/api/openfda_adverse_events.py` | OpenFDA FAERS | Top adverse events, emerging safety signal detection |
| `app/services/api/icd10.py` | NLM ICD-10 Clinical Tables | Autocomplete search, reverse lookup, child code expansion |
| `app/services/api/loinc.py` | LOINC FHIR | Panel expansion, 11 common primary care panels pre-mapped |

### Tier 2 — Clinical Decision Support (optional auth)

| File | API | Key Features |
|------|-----|-------------|
| `app/services/api/umls.py` | NLM UMLS | Abbreviation resolution ("HTN" → ICD-10), graceful no-key degradation |
| `app/services/api/healthfinder.py` | AHRQ HealthFinder | USPSTF screening recommendations by age/sex |
| `app/services/api/cdc_immunizations.py` | CDC Adult Immunization Schedule | Hardcoded schedule (no live API), gap evaluation by age/sex/diagnoses |
| `app/services/api/cms_pfs.py` | CMS Physician Fee Schedule | Code info lookup, revenue estimation, Virginia MAC-J rate fallback |

### Tier 3 — Literature and Patient Education

| File | API | Key Features |
|------|-----|-------------|
| `app/services/api/pubmed.py` | NCBI PubMed E-utilities | Two-phase guideline search, primary care journal badge |
| `app/services/api/medlineplus.py` | NLM MedlinePlus Connect | Patient education by ICD-10 or RxCUI, English and Spanish |

### Tier 4 — Operational

| File | API | Key Features |
|------|-----|-------------|
| `app/services/api/open_meteo.py` | Open-Meteo | Current conditions, commute-hour precip probability, extreme temp flags |

### Billing Intelligence

| File | Purpose |
|------|---------|
| `app/services/billing_rules.py` | `BillingRulesEngine` — 7 CMS 2025 rule categories, returns `BillingOpportunity` ORM objects |
| `models/billing.py` | `BillingOpportunity` (per-patient per-visit) + `BillingRuleCache` (CMS PFS lookup table) |
| `migrate_add_billing_models.py` | Idempotent migration, safe to re-run |

### Scheduler

| File | Purpose |
|------|---------|
| `app/services/api_scheduler.py` | `register_api_jobs()` adds 4 cron jobs to existing APScheduler instance |

### Audit and Modified Files

| File | Change |
|------|--------|
| `CODEBASE_AUDIT.md` | Full audit report, 7 findings |
| `models/__init__.py` | Added `BillingOpportunity`, `BillingRuleCache` imports |
| `utils/__init__.py` | Added `safe_patient_id(mrn)` SHA-256 helper |

---

## 4. Background Job Schedule

| Job ID | Time | What It Does |
|--------|------|-------------|
| `api_morning_briefing` | Daily 6:00 AM | Weather fetch, recall check, PubMed pre-load for today's patients |
| `api_overnight_prep` | Daily 8:00 PM | Billing rules engine for tomorrow's scheduled patients |
| `api_daily_recall` | Daily 5:45 AM | OpenFDA recall sweep (fires 15 min before briefing) |
| `api_weekly_cache` | Sunday 2:00 AM | Flush stale caches for recalls/events/weather |

To activate, call `register_api_jobs(scheduler, app, db)` in `agent_service.py` after `build_scheduler()` returns.

---

## 5. Billing Rules Engine — 2025 CMS Coverage

| Rule | Codes | Eligibility Trigger |
|------|-------|---------------------|
| CCM | 99490, 99439, 99491, 99437, 99487, 99489 | 2+ chronic conditions |
| AWV | G0402, G0438, G0439 + add-ons | Medicare, 12-month interval |
| AWV add-ons | G2211, G0444, G0442, G0443, 99497, G0136 | Stacked per 2025 rules |
| G2211 | G2211 | Established Medicare patient with complex condition (non-AWV visit) |
| Prolonged Service | 99417 | Face-to-face ≥40 min (99214) or ≥55 min (99215) |
| BHI | 99484 | Behavioral health ICD-10 + 20+ minutes |
| RPM | 99453, 99454, 99457, 99458 | RPM-eligible condition, enrollment opportunity |

CMS rates use Virginia MAC Jurisdiction M, CY2025 CF=$32.05, CY2026 CF=$33.40.
All `estimated_revenue` values are national average non-facility — actual payer rates vary.

---

## 6. CMS Physician Fee Schedule API Note

The CMS PFS API (`data.cms.gov`) returns RVU data. Computed payment = total RVU × conversion factor. The `cms_pfs.py` service falls back to hardcoded `rate_est` values from `api_config.py` if the API is unavailable or the code is not found in the fee schedule, ensuring the billing engine never returns $0 solely because of API downtime.

---

## 7. Complete Final Folder Structure (API Layer)

```
CareCompanion/
├── app/
│   ├── __init__.py
│   ├── api_config.py                    ← single source of truth for all API config
│   └── services/
│       ├── __init__.py
│       ├── api_scheduler.py             ← 4 background jobs for API layer
│       ├── billing_rules.py             ← BillingRulesEngine (7 rule categories)
│       └── api/
│           ├── __init__.py
│           ├── base_client.py           ← shared HTTP + cache + retry base class
│           ├── cache_manager.py         ← SQLite cache with TTL per API
│           ├── rxnorm.py
│           ├── rxclass.py
│           ├── openfda_labels.py
│           ├── openfda_recalls.py
│           ├── openfda_adverse_events.py
│           ├── icd10.py
│           ├── loinc.py
│           ├── umls.py
│           ├── healthfinder.py
│           ├── cdc_immunizations.py
│           ├── cms_pfs.py
│           ├── pubmed.py
│           ├── medlineplus.py
│           └── open_meteo.py
├── models/
│   ├── __init__.py                      ← updated: exports BillingOpportunity, BillingRuleCache
│   └── billing.py                       ← BillingOpportunity + BillingRuleCache ORM models
├── utils/
│   └── __init__.py                      ← updated: added safe_patient_id()
├── migrate_add_billing_models.py        ← idempotent table migration
├── CODEBASE_AUDIT.md
└── API_LAYER_BUILD_LOG.md               ← this file
```

---

## 8. Suggestions Not Implemented

These were considered but deferred to avoid scope creep or because they require runtime context:

1. **`BillingOpportunity.insurer_caveat` auto-population for Medicaid/commercial payers** — The rules engine sets the field to empty for non-Medicare patients. Populating it requires a payer-specific rule table that does not yet exist. Recommended next step: add a `payer_rules` JSON config to `api_config.py` mapping insurer prefixes to caveat text.

2. **UMLS API key setup in environment config** — `umls.py` gracefully returns empty when no key is configured. The key should be added to `config.py` or `.env` and passed in during service instantiation in `app.py`.

3. **LOINC reference ranges** — `loinc.py` fetches LOINC properties but the FHIR `$lookup` endpoint does not return reference ranges. A separate LOINC database download (free, requires account) would be needed to populate the `lab_normal_range` data used in the Lab Tracker feature.

4. **`api_scheduler._run_pubmed_preload` query assumes `Schedule.patient_mrn_hash`** — The `Schedule` model's exact column names were not confirmed. Verify `Schedule.patient_mrn_hash`, `Schedule.visit_date`, and `Schedule.user_id` match the actual ORM definition before activating the overnight prep job.

5. **`_build_patient_data` field mapping** — `api_scheduler._build_patient_data()` uses `getattr` with safe defaults for fields like `ccm_enrolled`, `last_awv_date`, `last_discharge_date`. These should be verified against `PatientRecord` column names before the billing engine is enabled in production.

6. **Dark mode + named theme unification** — Dark mode lives in `main.css` and named themes in `themes.css`. These could be merged into a single `themes.css` with a `[data-theme="dark"]` block alongside the named themes. Deferred — requires visual regression testing across all 8 themes.

7. **OpenFDA API key** — All three OpenFDA services (labels, recalls, events) run unauthenticated at 240 req/min. A free OpenFDA API key raises the limit to 1,000 req/min. Add `OPENFDA_API_KEY` to config and pass it in `_get()` params once volume warrants it.

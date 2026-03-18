# NP Companion — API Integration Plan

**Document Version:** 1.0
**Created:** CL23
**Source Reference:** `Documents/np_companion_api_intelligence_plan.md`
**Scope:** This document defines every external API used by NP Companion, maps each to specific features, specifies caching and offline behavior, and describes the new Intelligence Layer (Phase 10) and Billing Intelligence Layer (Phase 10B).

---

## Table of Contents

1. [API Overview & Tiering](#1-api-overview--tiering)
2. [Tier 1 — Core Clinical Vocabulary APIs](#2-tier-1--core-clinical-vocabulary-apis)
3. [Tier 2 — Clinical Decision Support APIs](#3-tier-2--clinical-decision-support-apis)
4. [Tier 3 — Literature & Patient Education APIs](#4-tier-3--literature--patient-education-apis)
5. [Tier 4 — Supplementary APIs](#5-tier-4--supplementary-apis)
6. [Billing Data Sources](#6-billing-data-sources)
7. [Data Flow Patterns](#7-data-flow-patterns)
8. [Caching Architecture](#8-caching-architecture)
9. [Offline / Degraded Mode](#9-offline--degraded-mode)
10. [Feature-to-API Dependency Map](#10-feature-to-api-dependency-map)
11. [New Intelligence Layer Features (Phase 10)](#11-new-intelligence-layer-features-phase-10)
12. [Billing Intelligence Layer (Phase 10B)](#12-billing-intelligence-layer-phase-10b)
13. [Provider Customization](#13-provider-customization)
14. [Admin API Configuration](#14-admin-api-configuration)
15. [Implementation Phasing](#15-implementation-phasing)
16. [HIPAA & Compliance Notes](#16-hipaa--compliance-notes)

---

## 1. API Overview & Tiering

NP Companion uses free, public government APIs for clinical data enrichment. No PHI is ever sent to any external API. All outbound requests contain only clinical vocabulary terms (drug names, ICD-10 codes, LOINC codes) — never patient identifiers, names, DOBs, or MRNs.

### Tier Summary

| Tier | Purpose | Auth Required | APIs | Build Phase |
|------|---------|---------------|------|-------------|
| **1** | Core Clinical Vocabulary | None (most), free key (OpenFDA >1000/day) | RxNorm, RxClass, OpenFDA Labels, OpenFDA FAERS, OpenFDA Recalls, ICD-10, LOINC, UMLS | Phase 2 (Data Layer) |
| **2** | Clinical Decision Support | None (most), free account (LOINC) | AHRQ HealthFinder, CDC CVX, CMS HCPCS/CPT, NLM Conditions | Phase 5 (CDS) |
| **3** | Literature & Education | Free key (PubMed), none (MedlinePlus) | PubMed E-utilities, MedlinePlus Connect | Phase 10A |
| **4** | Supplementary | None | Open-Meteo (weather) | Phase 7 (Morning Briefing) |
| **Billing** | Revenue Intelligence | None | CMS PFS API, CMS data.cms.gov | Phase 10B |

---

## 2. Tier 1 — Core Clinical Vocabulary APIs

### 2.1 RxNorm API (NIH/NLM)

| Field | Value |
|-------|-------|
| **Base URL** | `https://rxnav.nlm.nih.gov/REST/` |
| **Auth** | None |
| **Rate Limit** | 20 requests/second (per NLM policy) |
| **Response** | JSON |
| **Cache TTL** | Permanent (drugs don't change names) |
| **Cache Table** | `RxNormCache` (mirrors `Icd10Cache` pattern) |

**Key Endpoints:**

| Endpoint | REST Resource | Purpose | Used By |
|----------|---------------|---------|---------|
| getRxConceptProperties | `/rxcui/{rxcui}/properties.json` | RXCUI → canonical name, term type | F6d, F10, F10e |
| getRelatedByType (IN) | `/rxcui/{rxcui}/related.json?tty=IN` | Generic ingredient name | F10c, F25 |
| getRelatedByType (BN) | `/rxcui/{rxcui}/related.json?tty=BN` | Brand name | F10, F10e |
| findRxcuiByString | `/rxcui.json?name={name}&search=1` | Approximate match (no RXCUI) | F31 |
| getApproximateMatch | `/approximateTerm.json?term={term}` | Fuzzy match for messy names | F31 |
| getDisplayTerms | `/displaynames.json` | Autocomplete strings | F10 search |
| getSpellingSuggestions | `/spellingsuggestions.json?name={name}` | Typo handling | F10 search |
| getDrugs | `/drugs.json?name={name}` | All formulations/strengths | F10 detail |
| getAllProperties | `/rxcui/{rxcui}/allProperties.json` | DEA schedule, drug class | F25, F10 |
| getGenericProduct | `/rxcui/{rxcui}/generic.json` | Brand → generic | F26 |
| getNDCs | `/rxcui/{rxcui}/ndcs.json` | NDC codes for PA forms | F26 |
| getRxcuiHistoryStatus | `/rxcui/{rxcui}/historystatus.json` | Obsoleted/remapped drugs | F10d |

**Integration strategy:** The CDA XML from Amazing Charts already contains RxNorm CUI codes for most medications. The API is called to *enrich* those codes (canonical name, properties, class), not to identify drugs from scratch. The parser (`clinical_summary_parser.py`) already extracts RXCUI in `_parse_code_from_text()` — it currently discards the value. Phase 0.3 of CL23 pre-beta fixes saves the RXCUI to the `PatientMedication.rxnorm_cui` column.

---

### 2.2 RxClass API (NIH/NLM)

| Field | Value |
|-------|-------|
| **Base URL** | `https://rxnav.nlm.nih.gov/REST/rxclass/` |
| **Auth** | None |
| **Rate Limit** | Shared with RxNorm (20 req/sec total) |
| **Response** | JSON |
| **Cache TTL** | 90 days (class memberships change infrequently) |
| **Cache Table** | `RxClassCache` |

**Key Endpoints:**

| Endpoint | Purpose | Used By |
|----------|---------|---------|
| `/class/byDrugName.json?drugName={name}` | Drug → therapeutic classes | F10 (condition-first search) |
| `/class/byRxcui.json?rxcui={rxcui}` | RXCUI → drug classes | F10, NEW-D (Formulary Gap) |
| `/classMembers.json?classId={id}&relaSource=ATC` | Class → all member drugs | F10 (class card view) |

**Use case:** Powers the "condition-first search" in the Medication Reference (F10). Provider types "hypertension" → RxClass returns antihypertensive drug classes → NP Companion displays tiered class cards with member drugs.

---

### 2.3 OpenFDA Drug Label API

| Field | Value |
|-------|-------|
| **Base URL** | `https://api.fda.gov/drug/label.json` |
| **Auth** | Optional API key (free, raises limit from 40/min to 240/min) |
| **Rate Limit** | 40/min without key, 240/min with key |
| **Response** | JSON |
| **Cache TTL** | 30 days (labels update infrequently) |
| **Cache Table** | `FdaLabelCache` |

**Key Queries:**

| Query | Purpose | Used By |
|-------|---------|---------|
| `?search=openfda.rxcui:{rxcui}` | Label by RXCUI | F10, F10c, F10e |
| `?search=openfda.generic_name:{name}` | Label by generic name | F10 fallback |

**Fields extracted from response:**
- `indications_and_usage` — approved uses
- `dosage_and_administration` — starting/max doses
- `warnings_and_cautions` — black box warnings, contraindications
- `pregnancy` / `nursing_mothers` — F10c pregnancy filter
- `use_in_specific_populations` — renal/hepatic impairment (F10c)
- `drug_interactions` — interaction checker (NEW-B)
- `adverse_reactions` — side effect profile
- `boxed_warning` — critical safety alerts

---

### 2.4 OpenFDA Drug Adverse Events API (FAERS)

| Field | Value |
|-------|-------|
| **Base URL** | `https://api.fda.gov/drug/event.json` |
| **Auth** | Same key as Label API |
| **Rate Limit** | Same as Label API |
| **Response** | JSON (aggregated counts) |
| **Cache TTL** | 30 days |
| **Cache Table** | `FaersCache` |

**Key Query:**
```
?search=patient.drug.openfda.rxcui:{rxcui}&count=patient.reaction.reactionmeddrapt.exact
```

**Purpose:** Returns real-world adverse event frequency from the FDA FAERS database. Displayed in the Medication Reference drug card as "Real-World Side Effects (FDA FAERS, top 5)". This is opt-in per provider (`medref_show_faers_data` preference) because adverse event frequency data can be alarming without clinical context.

---

### 2.5 OpenFDA Drug Recalls API

| Field | Value |
|-------|-------|
| **Base URL** | `https://api.fda.gov/drug/enforcement.json` |
| **Auth** | Same key as Label API |
| **Rate Limit** | Same as Label API |
| **Response** | JSON |
| **Cache TTL** | 24 hours (recalls are time-sensitive) |
| **Cache Table** | `RecallCache` |

**Key Query:**
```
?search=status:"Ongoing"+AND+openfda.rxcui:{rxcui}
```

**Purpose:** Daily background check for active FDA drug recalls affecting any patient's medications. Powers the Drug Recall Alert System (NEW-A) and the safety banner in pre-visit notes (F10e).

---

### 2.6 ICD-10 API (NLM Clinical Tables)

| Field | Value |
|-------|-------|
| **Base URL** | `https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search` |
| **Auth** | None |
| **Rate Limit** | Generous (no published limit) |
| **Response** | JSON |
| **Cache TTL** | 365 days (refreshed annually with fiscal year update) |
| **Cache Table** | `Icd10Cache` (**already implemented** in `models/patient.py`) |

**Already in use** for the patient chart diagnoses widget. Expansion needed for:
- F17 Coding Suggester — autocomplete search
- F17b Specificity Reminder — "more specific code available" alerts
- F17c Code Pairing — common diagnosis combinations
- NEW-D Formulary Gap Detection — condition → expected drug class mapping

---

### 2.7 LOINC API (Regenstrief FHIR)

| Field | Value |
|-------|-------|
| **Base URL** | `https://fhir.loinc.org/CodeSystem/$lookup` |
| **Auth** | Free account required (Regenstrief registration) |
| **Rate Limit** | Reasonable (not published) |
| **Response** | FHIR JSON |
| **Cache TTL** | 365 days |
| **Cache Table** | `LoincCache` |

**Purpose:** Lab test identification and reference ranges. Powers the Lab Tracker (F11) LOINC reference range column and the Abnormal Lab Interpretation Assistant (NEW-B).

**Key fields:** LOINC code, long common name, component, property, system, scale type, reference range (population-based).

---

### 2.8 UMLS API (NLM)

| Field | Value |
|-------|-------|
| **Base URL** | `https://uts-ws.nlm.nih.gov/rest/` |
| **Auth** | Free UMLS account + API key required |
| **Rate Limit** | 20 requests/second |
| **Response** | JSON |
| **Cache TTL** | 90 days |
| **Cache Table** | `UmlsCache` |

**Purpose:** Master terminology crosswalk. Maps between SNOMED-CT, ICD-10, RxNorm, LOINC, and CPT. Powers the Coding Suggester (F17c pairing logic) and Note Reformatter (F31) for vocabulary normalization.

---

## 3. Tier 2 — Clinical Decision Support APIs

### 3.1 AHRQ HealthFinder API

| Field | Value |
|-------|-------|
| **Base URL** | `https://health.gov/myhealthfinder/api/v3/` |
| **Auth** | None |
| **Rate Limit** | Not published |
| **Response** | JSON |
| **Cache TTL** | 90 days |
| **Cache Table** | `HealthFinderCache` |

**Key Query:**
```
/topicsearch.json?age={age}&sex={sex}
```

**Purpose:** Provides USPSTF-recommended preventive screenings by patient demographics. Currently the Care Gap Engine (`caregap_engine.py`) has 19 hardcoded USPSTF rules. HealthFinder replaces and extends these with the authoritative source. The hardcoded rules remain as a fallback if the API is unavailable.

---

### 3.2 CDC Immunization Data via RxNorm CVX

| Field | Value |
|-------|-------|
| **Access** | RxNorm API + CDC published schedules |
| **Cache TTL** | Annual (CDC publishes schedule each February) |

**Purpose:** Vaccine schedule recommendations mapped to CVX codes. Powers the immunization care gap evaluator in F15 and the morning briefing (F22) immunization gap check.

---

### 3.3 CMS HCPCS/CPT Reference Data

| Field | Value |
|-------|-------|
| **Access** | Downloadable flat files from CMS.gov |
| **Format** | CSV/fixed-width text |
| **Update** | Annual (January 1 effective date) |
| **Storage** | Bulk-loaded into `BillingRuleCache` SQLite table |

**Purpose:** Procedure code descriptions and billing indicators. Powers F16 (Billing Capture Suggestions) and F14a (E&M Level Calculator). Loaded once per year, queried locally — no live API calls needed.

---

### 3.4 NLM Conditions API

| Field | Value |
|-------|-------|
| **Base URL** | `https://clinicaltables.nlm.nih.gov/api/conditions/v3/search` |
| **Auth** | None |
| **Response** | JSON |
| **Cache TTL** | 90 days |
| **Cache Table** | `NlmConditionsCache` |

**Purpose:** Clinical condition search. Powers the Differential Diagnosis Widget (NEW-G). Queries chief complaint text to return related clinical conditions with ICD-10 cross-references.

---

## 4. Tier 3 — Literature & Patient Education APIs

### 4.1 NCBI E-utilities (PubMed)

| Field | Value |
|-------|-------|
| **Base URL** | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/` |
| **Auth** | Free NCBI API key (required for >3 req/sec) |
| **Rate Limit** | 3/sec without key, 10/sec with key |
| **Response** | JSON or XML |
| **Cache TTL** | 30 days per diagnosis |
| **Cache Table** | `PubmedCache` |

**Key Endpoints:**
- `esearch.fcgi` — Search PubMed for guidelines by diagnosis
- `esummary.fcgi` — Get article title, journal, year, DOI
- `efetch.fcgi` — Get abstract text

**Filters used:** Publication type = guideline OR systematic review. Date range = provider-configurable (default 3 years). Journals = high-impact primary care (NEJM, JAMA, AAFP, AFP, Annals, BMJ).

**Purpose:** Powers the PubMed Guideline Lookup Panel (NEW-C). Pre-loads top 3 diagnoses per patient during chart open.

---

### 4.2 NLM MedlinePlus Connect

| Field | Value |
|-------|-------|
| **Base URL** | `https://connect.medlineplus.gov/service` |
| **Auth** | None |
| **Rate Limit** | Not published |
| **Response** | JSON |
| **Cache TTL** | 30 days |
| **Cache Table** | `MedlinePlusCache` |

**Key Queries:**
- By ICD-10: `?mainSearchCriteria.v.cs=2.16.840.1.113883.6.90&mainSearchCriteria.v.c={code}`
- By RxNorm: `?mainSearchCriteria.v.cs=2.16.840.1.113883.6.88&mainSearchCriteria.v.c={rxcui}`

**Purpose:** Patient-facing educational content. Powers the Patient Education Auto-Draft (NEW-E) feature. Supports English and Spanish output (`medlineplus_language` provider preference).

---

## 5. Tier 4 — Supplementary APIs

### 5.1 Open-Meteo Weather API

| Field | Value |
|-------|-------|
| **Base URL** | `https://api.open-meteo.com/v1/forecast` |
| **Auth** | None |
| **Rate Limit** | 10,000/day |
| **Response** | JSON |
| **Cache TTL** | Not cached (weather changes constantly) |

**Key Query:**
```
?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode
```

**Purpose:** Morning briefing (F22) weather section. Latitude/longitude derived from clinic ZIP code configured in admin settings (`weather_zip_code`). Simple — shows today's forecast in the morning briefing card.

---

## 6. Billing Data Sources

### 6.1 CMS Physician Fee Schedule REST API

| Field | Value |
|-------|-------|
| **Base URL** | `https://pfs.data.cms.gov/api` |
| **Auth** | None |
| **Response** | JSON |
| **Cache TTL** | Annual (refresh each November) |
| **Cache Table** | `BillingRuleCache` |

**Key Queries:**
- `GET /api?hcpcs_code={code}&year=2025` — RVU components + national payment
- `GET /api?hcpcs_code={code}&locality_number={locality}&year=2025` — Locality-adjusted payment

**Fields:** `work_rvu`, `non_facility_pe_rvu`, `mp_rvu`, `total_rvu_non_facility`, `non_facility_pricing_amount`, `facility_pricing_amount`, `global_surgery`, `status_code`

**Payment formula:**
```
Non-Facility Payment = [(Work RVU × Work GPCI) + (Non-Facility PE RVU × PE GPCI) + (MP RVU × MP GPCI)] × Conversion Factor
CY 2025 CF: $32.05 (non-APM) / $33.57 (qualifying APM)
CY 2026 CF: $33.40 (non-APM) / $33.57 (qualifying APM)
```

**Supplementary flat files:** CMS publishes PFALLyyA.ZIP (fee schedule amounts) and RVUyyA.ZIP (RVU values). Downloaded annually, parsed into the `BillingRuleCache` table for bulk local queries.

---

### 6.2 CMS data.cms.gov Open API

| Field | Value |
|-------|-------|
| **Base URL** | `https://data.cms.gov/api/1/` |
| **Auth** | None |
| **Response** | JSON (Socrata Open Data API) |
| **Cache TTL** | Annual |

**Key Dataset:** "Medicare Physician & Other Practitioners — by Provider and Service." Calibrates expected payment by specialty (family practice) and geography (Virginia) — more accurate than national averages.

---

## 7. Data Flow Patterns

All API calls follow one of three patterns. No API call is ever made in the request-response path of a page load.

### Pattern A — Import-Time Enrichment

**Trigger:** Clinical Summary XML imported (file watcher or drag-and-drop upload).

```
XML Import Event
├── Parse XML → extract medications, diagnoses, labs, allergies
├── For each medication:
│   ├── RxNorm: normalize drug name, get properties
│   ├── RxClass: identify therapeutic class
│   ├── OpenFDA Label: fetch prescribing info
│   └── Cache all results
├── For each diagnosis:
│   ├── ICD-10 API: validate code, get description
│   └── Cache result
├── Cross-reference:
│   ├── OpenFDA Labels: drug interaction check across all meds
│   ├── OpenFDA Labels: allergy cross-reference
│   ├── RxClass + ICD-10: formulary gap detection
│   └── Store all findings as cached enrichment records
└── All enrichment runs in background thread — import returns immediately
```

### Pattern B — Real-Time Interactive

**Trigger:** Provider types in a search field (Medication Reference, Coding Suggester).

```
User types query → 300ms debounce → API call
├── Check local cache first (SQLite query, <5ms)
├── On cache miss: fetch from API
├── Return results to UI
└── Cache response for future lookups
```

Perceived latency must be <200ms. Cache-first architecture ensures this for repeat queries.

### Pattern C — Scheduled Background Jobs

**Trigger:** APScheduler cron jobs.

```
Morning prep job (6 AM):
├── Open-Meteo weather fetch
├── HealthFinder query for each scheduled patient
├── PubMed guideline pre-load for top diagnoses
├── OpenFDA recall check against full medication database
└── CDC immunization gap evaluation

Pre-visit note prep job (8 PM):
├── RxNorm normalization for each scheduled patient's meds
├── OpenFDA label fetch/refresh for each medication
├── Drug interaction check across full med list
├── Allergy cross-reference check
└── MedlinePlus pre-fetch for new medications

Weekly jobs (Sunday 2 AM):
├── ICD-10 cache freshness check
├── RxNorm cache freshness check
├── OpenFDA recall full scan
└── PubMed guideline refresh for common diagnoses
```

All scheduled jobs run through APScheduler. Each job is independently try/except wrapped. Failures logged to database and reported in agent health monitor (F3a). Jobs never block each other.

---

## 8. Caching Architecture

### Cache Table Pattern

All cache tables follow the existing `Icd10Cache` model pattern:

```python
class [Api]Cache(db.Model):
    __tablename__ = '[api]_cache'
    id          = db.Column(db.Integer, primary_key=True)
    lookup_key  = db.Column(db.String(255), unique=True, nullable=False, index=True)
    response    = db.Column(db.Text, nullable=False)  # JSON string
    fetched_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at  = db.Column(db.DateTime, nullable=True)  # null = permanent
```

### Cache Tables Required

| Table | Model File | Lookup Key | TTL |
|-------|-----------|------------|-----|
| `rxnorm_cache` | models/patient.py | RXCUI or drug name | Permanent |
| `rxclass_cache` | models/patient.py | RXCUI or class ID | 90 days |
| `fda_label_cache` | models/patient.py | RXCUI | 30 days |
| `faers_cache` | models/patient.py | RXCUI | 30 days |
| `recall_cache` | models/patient.py | RXCUI | 24 hours |
| `icd10_cache` | models/patient.py | ICD-10 code | 365 days **(exists)** |
| `loinc_cache` | models/patient.py | LOINC code | 365 days |
| `umls_cache` | models/patient.py | CUI or term | 90 days |
| `healthfinder_cache` | models/caregap.py | age+sex key | 90 days |
| `nlm_conditions_cache` | models/patient.py | search term | 90 days |
| `pubmed_cache` | models/patient.py | diagnosis search key | 30 days |
| `medlineplus_cache` | models/patient.py | ICD-10 or RXCUI | 30 days |
| `billing_rule_cache` | models/billing.py | HCPCS/CPT code | Annual |

### Cache Lookup Logic

```python
def get_cached_or_fetch(cache_model, lookup_key, fetch_fn):
    """Universal cache-first fetch pattern."""
    cached = cache_model.query.filter_by(lookup_key=lookup_key).first()
    if cached and (cached.expires_at is None or cached.expires_at > datetime.now(timezone.utc)):
        return json.loads(cached.response)
    # Cache miss or expired — fetch from API
    try:
        data = fetch_fn(lookup_key)
    except Exception:
        # API failure — return stale cache if available, else None
        return json.loads(cached.response) if cached else None
    # Upsert cache
    if cached:
        cached.response = json.dumps(data)
        cached.fetched_at = datetime.now(timezone.utc)
        cached.expires_at = ...  # per-table TTL
    else:
        cached = cache_model(lookup_key=lookup_key, response=json.dumps(data), ...)
        db.session.add(cached)
    db.session.commit()
    return data
```

### Admin Cache Management

Admin can view cache stats at `/admin/api-cache`:
- Entry count per API
- Total cache size (MB)
- Oldest entry per API
- Cache hit rate (if instrumented)
- Per-API "Flush Cache" button for forced refresh (e.g., new ICD-10 fiscal year)

---

## 9. Offline / Degraded Mode

APIs are enhancements, not dependencies. NP Companion must function without internet access.

### Graceful Degradation Table

| Feature | Online | Offline (cached) | Offline (no cache) |
|---------|--------|-------------------|---------------------|
| Medication Reference | Live FDA labels | Cached labels | Local text only |
| Coding Suggester | Live ICD-10 search | Cached ICD-10 db | No autocomplete |
| Care Gap Tracker | Live HealthFinder | Cached recommendations | Hardcoded 19 rules |
| Lab Reference Ranges | LOINC API | Cached ranges | Provider thresholds only |
| Drug Interaction Check | Live + cached | Cached | Not available — show warning |
| Drug Recall Check | Live check | 24h-old check with staleness notice | Not available |
| PubMed Guidelines | Live search | Cached results | Not available |
| Patient Education | Live MedlinePlus | Cached content | Not available |
| Weather | Live | Not cached | Not shown |
| Billing RVU Lookup | Cached (annual load) | Cached | Not available |

### Staleness Indicators

All API-derived UI content shows a small timestamp:
- "from FDA label (cached 3 days ago)" — when showing cached data
- "live" — when fetched within 1 hour
- "⚠ Running on cached clinical data. Last sync: [timestamp]." — offline banner

Staleness visibility is important for clinical liability — a provider must know if they are viewing a current drug label vs. a 30-day-old cached copy.

---

## 10. Feature-to-API Dependency Map

### Existing Features Enhanced by APIs

| Feature | Tier 1 APIs | Tier 2 APIs | Tier 3 APIs | Tier 4 |
|---------|-------------|-------------|-------------|--------|
| **F6d** Clinical Summary Parser | RxNorm | — | — | — |
| **F10** Medication Reference | RxNorm, RxClass, OpenFDA Labels, FAERS | — | MedlinePlus | — |
| **F10c** Pregnancy/Renal Filter | OpenFDA Labels | — | — | — |
| **F10d** Guideline Update Flag | RxNorm (history) | — | — | — |
| **F10e** Patient Chart View | RxNorm, OpenFDA Labels, OpenFDA Recalls | — | — | — |
| **F11** Lab Value Tracker | LOINC | — | — | — |
| **F11d** Lab Panel Grouping | LOINC | — | — | — |
| **F15** Care Gap Tracker | ICD-10 | HealthFinder, CDC CVX | — | — |
| **F15a** Auto-Population | ICD-10, LOINC | HealthFinder | — | — |
| **F16** Billing Capture | ICD-10 | HCPCS/CMS data | — | — |
| **F17** Coding Suggester | ICD-10, UMLS | — | — | — |
| **F17b** Specificity Reminder | ICD-10 | — | — | — |
| **F17c** Code Pairing | ICD-10, UMLS | — | — | — |
| **F22** Morning Briefing | OpenFDA Recalls | HealthFinder | — | Open-Meteo |
| **F25** Controlled Substance Tracker | RxNorm | — | — | — |
| **F26** Prior Auth Generator | RxNorm, RxClass, OpenFDA Labels | — | — | — |
| **F31** Note Reformatter | RxNorm, ICD-10, UMLS, LOINC | — | — | — |

### New Features (Phase 10 Intelligence Layer)

| Feature | Tier 1 APIs | Tier 2 APIs | Tier 3 APIs |
|---------|-------------|-------------|-------------|
| **NEW-A** Drug Recall Alert System | OpenFDA Recalls, RxNorm | — | — |
| **NEW-B** Abnormal Lab Interpretation | LOINC, OpenFDA Labels, RxNorm | — | — |
| **NEW-C** PubMed Guideline Lookup | — | — | PubMed E-utilities |
| **NEW-D** Formulary Gap Detection | RxNorm, RxClass, ICD-10 | — | — |
| **NEW-E** Patient Ed Auto-Draft | ICD-10, RxNorm | — | MedlinePlus |
| **NEW-F** Drug Safety Panel | RxNorm, OpenFDA Labels, OpenFDA Recalls | — | — |
| **NEW-G** Differential Diagnosis Widget | ICD-10, UMLS | NLM Conditions | — |

### Billing Intelligence (Phase 10B)

| Component | Data Source |
|-----------|-------------|
| RVU/payment rates | CMS PFS API + flat files |
| Locality GPCI | CMS PFS API |
| Actual Medicare payments | data.cms.gov |
| CCM/AWV/TCM/BHI rules | Hard-coded from CMS MLN publications |
| Insurer type detection | Clinical Summary XML (import-time parse) |

---

## 11. New Intelligence Layer Features (Phase 10)

Phase 10 adds a new layer of intelligence that combines API data with patient data. These are **new features** not in the original Phases 1-9.

### NEW-A: Drug Recall Alert System

**Dependencies:** OpenFDA Recalls API (2.5), RxNorm (2.1), Pushover (F21)

**Logic:**
1. Daily at 5:45 AM — query all unique RXCUI values in patient medication database
2. For each drug — query OpenFDA recalls for `status=Ongoing`
3. Match recalled products against RXCUI name variants
4. New matches → `RecallAlert` database record
5. Morning briefing: "FDA Recalls affecting patients: [N] — review list"
6. Patient Chart: red badge on Medications tab for affected patients
7. Provider action: one-click draft notification to patient with recall details

---

### NEW-B: Abnormal Lab Interpretation Assistant

**Dependencies:** LOINC (2.7), OpenFDA Labels (2.3), RxNorm (2.1), Lab Tracker (F11)

**Logic:**
1. On new lab result import from XML:
   - Check against LOINC reference range AND provider's custom threshold
2. If outside range:
   - Query patient's medication list
   - For each medication: check if FDA label mentions this lab as monitoring parameter
   - Cross-reference: is any medication known to cause this type of abnormality?
3. Generate: "[Lab] is [direction] — patient is on [drug] which [monitoring context]. Consider: [action]."
4. Display as collapsible "Clinical Context" section below lab trend chart

---

### NEW-C: PubMed Guideline Lookup Panel

**Dependencies:** NCBI E-utilities (4.1), Patient Chart View (F10e)

**Logic:**
1. When chart opens — identify top 3 diagnoses (by encounter recency)
2. Search PubMed: type=guideline|systematic review, last 3 years, high-impact journals
3. Cache per diagnosis for 30 days
4. Display as stacked cards: title + journal + year + abstract excerpt + DOI link

**Per-provider customization:** Journal filter, article types, date range (2/3/5 years)

---

### NEW-D: Formulary Gap Detection

**Dependencies:** RxClass (2.2), ICD-10 API (2.6), Clinical Summary XML

**Logic:**
1. For each active diagnosis → fetch expected drug classes (RxClass)
2. Check patient med list for any medication in each expected class
3. If no medication found for chronic condition with >1 encounter → flag as gap
4. Display: "No [drug class] found for [diagnosis] — verify treatment plan"
5. Provider dismisses with note (e.g., "managed with lifestyle modification") — does not re-appear

---

### NEW-E: Patient Education Auto-Draft

**Dependencies:** MedlinePlus (4.2), ICD-10 (2.6), Delayed Message Sender (F18)

**Triggers:**
- Care gap addressed → MedlinePlus content for that topic → draft message
- New medication detected → MedlinePlus drug info → draft message

Language preference (English/Spanish) per provider. Drafts require provider approval before sending.

---

### NEW-F: Drug Safety Panel

**Dependencies:** RxNorm (2.1), OpenFDA Labels (2.3), OpenFDA Recalls (2.5)

**Display:** Dedicated panel in Patient Chart View aggregating all active drug safety signals:
- **Interactions** — from FDA label `drug_interactions` field
- **Recalls** — from OpenFDA Recalls matching patient's meds
- **Monitoring Due** — from FDA label monitoring requirements + lab tracker

Each item has a "Document Reviewed" button → audit trail entry (liability documentation).

---

### NEW-G: Differential Diagnosis Widget

**Dependencies:** ICD-10 (2.6), UMLS (2.8), NLM Conditions (3.4)

**Display:** Collapsed by default in Prepped Note tab, below Chief Complaint.
- **High Consideration** — based on existing diagnoses (already in assessment)
- **New Differentials** — from NLM Conditions API query against chief complaint
- **Red Flags** — hardcoded by chief complaint category (never wrong because they prompt consideration, not diagnose)

---

## 12. Billing Intelligence Layer (Phase 10B)

Phase 10B adds a Proactive Billing Opportunity Engine that surfaces revenue opportunities the provider would otherwise miss.

### Billing Rule Categories

| # | Rule Category | Key Codes | Detection Method |
|---|--------------|-----------|------------------|
| 1 | Chronic Care Management (CCM) | 99490, 99439, 99491, 99437 | ≥2 chronic conditions in problem list |
| 2 | Annual Wellness Visit (AWV) | G0402, G0438, G0439, G2211, G0444, 99497, G0136 | AWV history + 12-month interval |
| 3 | E&M Complexity Add-On | G2211 | Established patient + serious/complex condition |
| 4 | Transitional Care Management (TCM) | 99495, 99496 | Hospital discharge detected in inbox |
| 5 | Prolonged Service (99417) | 99417 | Timer exceeds E&M level max time |
| 6 | Behavioral Health Integration (BHI) | 99484 | Behavioral health dx + active management |
| 7 | Remote Patient Monitoring (RPM) | 99453, 99454, 99457, 99458 | Qualifying condition + device program |

**Critical:** Billing rules are NOT driven by APIs — they are encoded as application logic from CMS policy documents. Must be reviewed annually each November when CMS publishes the new PFS Final Rule. System generates admin reminder on November 1.

### Insurer Intelligence

Payer classification from Clinical Summary XML demographics:
- **Medicare FFS** — full billing rules apply, PFS API rates
- **Medicare Advantage** — same codes, add prior auth caveat
- **Medicaid** — Virginia DMAS rates (configurable `medicaid_rate_factor`)
- **Commercial** — estimate using configurable `commercial_payer_rate_factor` (default 1.2× Medicare)

### New Database Models

**`BillingOpportunity`** — per-visit opportunity record:
- opportunity_type, applicable_codes, estimated_revenue, eligibility_basis
- documentation_required, confidence_level, insurer_caveat
- status (PENDING/ACTED_ON/DISMISSED/EXPIRED)
- dismissed_reason, revenue_captured

**`BillingRuleCache`** — annual PFS data:
- hcpcs_code, short_description, work_rvu, payment amounts
- locality_adjusted_payment, conversion_factor_year

### Compliance Requirements

Every billing opportunity surface must include:
1. The word "estimate" or "approximate" before dollar figures
2. Caveat that actual reimbursement depends on payer contract
3. No billing suggestion for services requiring consent (CCM, APCM) until consent documented
4. System never suggests billing for unrendered/undocumented services

**CMS data attribution:** "This product uses publicly available data from the U.S. Centers for Medicare & Medicaid Services. Payment information is provided for informational purposes and does not constitute a guarantee of Medicare reimbursement."

---

## 13. Provider Customization

Every provider controls API behavior from `/settings/api`:

### Medication Reference Preferences
- `medref_default_view` — condition-first vs. drug-first
- `medref_show_faers_data` — show FAERS adverse event data (boolean)
- `medref_patient_context_mode` — show patient-specific overlay (boolean)
- `preferred_drug_classes` — ordered list of preferred first-line classes

### Clinical Decision Support Preferences
- `show_differential_widget` — boolean
- `differential_red_flags_only` — show only red flags (boolean)
- `guideline_lookup_auto_load` — auto-load PubMed on chart open (boolean)
- `guideline_publication_years` — 1-10 years back (default 3)

### Note Generation Preferences
- `note_api_enrichment_level` — minimal / standard / full
- `assessment_plan_template_style` — provider-defined template
- `show_safety_banners` — show interaction/recall banners (boolean)

### Lab Tracking Preferences
- `lab_reference_source` — LOINC vs. custom thresholds
- `trend_interpretation_sensitivity` — 3-10 data points (default 3)
- `monitoring_reminder_source` — FDA label / personal override / both

### Care Gap Preferences
- `care_gap_grade_threshold` — which USPSTF grades to surface (default A+B)
- `hide_care_gaps_with_reasons` — suppressed gap types
- `immunization_schedule_source` — CDC adult / CDC + ACIP supplemental

### Patient Education Preferences
- `medlineplus_language` — en / es
- `patient_ed_auto_draft` — auto-populate draft on gap closure (boolean)
- `patient_ed_reading_level_notice` — show health literacy reminder (boolean)

### Billing Preferences (from `/settings/billing`)
- `billing_insurer_type_default` — default payer type assumption
- `ccm_opportunity_threshold_minutes` — chronic condition count minimum
- `show_scheduling_opportunities` — show scheduling recs in Today View
- `opportunity_minimum_confidence` — HIGH only or HIGH + MEDIUM
- `revenue_display_mode` — dollar amounts vs. code names only
- `tcm_alert_priority` — push notification priority for TCM windows

---

## 14. Admin API Configuration

Settings at `/admin/api` (admin-only):

| Setting | Purpose | Default |
|---------|---------|---------|
| `openFDA_api_key` | Higher rate limits (240/min vs 40/min) | None (uses anonymous) |
| `pubmed_api_key` | NCBI API key for >3 req/sec | None |
| `umls_api_key` | UMLS account API key | None |
| `loinc_credentials` | Regenstrief account for LOINC API | None |
| `clinical_summary_export_folder` | AC XML export path | `data/clinical_summaries/` |
| `api_cache_location` | Cache storage path | `data/api_cache/` |
| `recall_alert_class_threshold` | Which recall classes push notify | Class I only |
| `weather_zip_code` | Clinic ZIP for morning briefing | None |
| `pfs_locality_number` | Virginia MAC locality for GPCI | Set during setup |
| `commercial_payer_rate_factor` | Multiplier for commercial estimates | 1.2 |
| `medicaid_rate_factor` | Multiplier for Medicaid estimates | 0.75 |
| `pfs_auto_refresh_month` | Month to trigger annual PFS refresh | November |

---

## 15. Implementation Phasing

Implementation follows the existing phase structure. APIs are integrated where their dependent features are built.

### Phase 0 (CL23 Pre-Beta) — Foundation

| Task | APIs | Status |
|------|------|--------|
| Save RXCUI from parser to PatientMedication | RxNorm | Phase 0.3 |
| Create `RxNormCache` model | RxNorm | Phase 0.3 |
| Create `api_client.py` utility with `get_cached_or_fetch()` | All | Phase 0.3 |
| Migration: add `rxnorm_cui` column to patient_medications | RxNorm | Phase 0.3 |

### Phase 2 (Data Layer) — Tier 1 Integration

| Task | APIs |
|------|------|
| RxNorm enrichment on XML import | RxNorm |
| ICD-10 validation on XML import | ICD-10 (already working) |
| `FdaLabelCache`, `FaersCache`, `RecallCache` models | OpenFDA |
| `RxClassCache` model | RxClass |

### Phase 4 (Monitoring) — Lab Intelligence

| Task | APIs |
|------|------|
| LOINC reference range column in Lab Tracker | LOINC |
| `LoincCache` model and migration | LOINC |

### Phase 5 (Clinical Decision Support) — Tier 2 Integration

| Task | APIs |
|------|------|
| HealthFinder replaces/supplements hardcoded USPSTF rules | HealthFinder |
| CDC immunization schedule data | CDC CVX |
| ICD-10 autocomplete for Coding Suggester | ICD-10 |
| UMLS crosswalk for code pairing | UMLS |
| CMS HCPCS data load for billing capture | CMS flat files |

### Phase 7 (Notifications & Briefing) — Supplementary

| Task | APIs |
|------|------|
| Morning briefing weather section | Open-Meteo |
| Morning briefing recall check | OpenFDA Recalls |
| Morning briefing immunization gaps | CDC CVX |

### Phase 9 (Note Reformatter) — Normalization

| Task | APIs |
|------|------|
| RxNorm + ICD-10 + LOINC normalization in reformatter | RxNorm, ICD-10, LOINC |
| UMLS crosswalk for vocabulary alignment | UMLS |

### Phase 10A (Intelligence Layer) — New Features

| Task | APIs |
|------|------|
| Drug Recall Alert System (NEW-A) | OpenFDA Recalls, RxNorm |
| Abnormal Lab Interpretation (NEW-B) | LOINC, OpenFDA Labels, RxNorm |
| PubMed Guideline Lookup (NEW-C) | PubMed E-utilities |
| Formulary Gap Detection (NEW-D) | RxNorm, RxClass, ICD-10 |
| Patient Education Auto-Draft (NEW-E) | MedlinePlus, ICD-10, RxNorm |
| Drug Safety Panel (NEW-F) | RxNorm, OpenFDA Labels, Recalls |
| Differential Diagnosis Widget (NEW-G) | ICD-10, UMLS, NLM Conditions |

### Phase 10B (Billing Intelligence) — Revenue Optimization

| Task | APIs |
|------|------|
| CMS PFS API integration + flat file parser | CMS PFS |
| `BillingOpportunity` + `BillingRuleCache` models | — |
| Billing rule engine (CCM/AWV/TCM/G2211/99417/BHI/RPM) | Hard-coded rules |
| Insurer detection from XML demographics | — |
| Pre-visit opportunity calculation | All billing sources |
| Today View billing cards | — |
| Post-visit billing review | — |
| Scheduling intelligence | — |
| `/settings/billing` + `/admin/billing` pages | — |

---

## 16. HIPAA & Compliance Notes

### No PHI in API Requests

All outbound API calls contain ONLY:
- Drug names or RXCUI codes
- ICD-10 diagnosis codes
- LOINC lab codes
- UMLS concept identifiers
- Age and sex (for HealthFinder — no names, DOBs, or MRNs)

**Never sent:** Patient names, MRNs, dates of birth, addresses, insurance IDs, or any other SAFE Harbor identifier.

### Audit Trail for API-Derived Clinical Decisions

The Drug Safety Panel "Document Reviewed" button creates an audit log entry: provider acknowledged the interaction/recall/monitoring flag. This is important for liability documentation.

### Billing Compliance

- All revenue figures labeled "estimate" or "approximate"
- No billing suggestions for unrendered or undocumented services
- CCM/APCM require documented patient consent before billable
- System never auto-submits claims — all billing decisions require provider review
- CMS data attribution statement displayed in admin billing settings

### Annual Review Requirements

| What | When | Action |
|------|------|--------|
| CMS PFS Final Rule | November | Review and update billing rules, conversion factor, GPCI |
| ICD-10 fiscal year update | October 1 | Flush ICD-10 cache, verify new codes |
| CDC immunization schedule | February | Update hardcoded vaccine schedule data |
| USPSTF recommendation updates | Ongoing | Review HealthFinder cache freshness |

---

*This document is the authoritative reference for all external API integration in NP Companion. It supersedes ad-hoc API references in other documents. Feature specifications in the Development Guide reference this document for API details.*

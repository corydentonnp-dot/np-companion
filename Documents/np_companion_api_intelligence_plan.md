# NP Companion — API Integration & Intelligence Layer
# Planning Document for VS Code Copilot (Planner Mode)
#
# This document describes every external API integrated into NP Companion,
# the features they power, the logic connecting them, display/UX requirements,
# and per-provider customization. Do not generate code from this document —
# use it to plan architecture, dependencies, data flow, and feature ordering.
# Treat every section as a planning constraint, not an implementation spec.

---

## Document Purpose

NP Companion began as a workflow automation tool for a single family practice
office using Amazing Charts EHR. It is evolving into a clinical intelligence
layer that sits between the provider and the EHR, surfacing the right
information at the right moment without requiring the provider to navigate
multiple systems.

The addition of external APIs transforms three categories of existing features:
1. **Reference data** (medications, diagnoses, labs) — no longer hand-seeded
   SQLite tables; now live-queried and cached from authoritative sources
2. **Clinical logic** (care gaps, drug interactions, billing) — no longer
   hardcoded rules; now driven by USPSTF/CDC/FDA data updated automatically
3. **Note generation** (pre-visit prep, reformatter) — no longer text
   manipulation; now clinically aware content generation

It also enables four genuinely new feature categories not in the original plan:
- Real-time clinical decision support during note writing
- Drug safety monitoring (interactions, recalls, adherence)
- Patient education content generation
- Evidence-based guideline lookup at point of care

---

## The API Ecosystem

### Tier 1 — Core Clinical Vocabulary (Always On, Always Cached)

These APIs are the foundation. Every other feature in this document depends
on at least one of them. They should be queried at import time and cached
aggressively. Clinic hours cannot depend on live internet.

---

#### 1.1 RxNorm API
**Base URL:** `https://rxnav.nlm.nih.gov/REST/`
**Auth:** None required
**Rate limit:** Soft limit, ~20 req/sec; no hard enforcement for reasonable use
**Response format:** JSON or XML
**No API key required**

**What it does:**
Normalizes any drug name string into a canonical RxNorm Concept Unique
Identifier (RxCUI). An RxCUI is the stable, unique ID for a drug concept
that persists regardless of how the name is spelled, abbreviated, or branded.

**Key endpoints and their logic:**

- `GET /rxcui?name=[drug_name]` — Takes any drug string, returns RxCUI
  Logic: Run every medication string from the Clinical Summary XML through
  this endpoint on import. Store the RxCUI alongside the raw string in the
  database. All subsequent operations use RxCUI, not the string.

- `GET /rxcui/[rxcui]/properties` — Returns canonical name, drug class,
  ingredient, dose form, strength, and route for a given RxCUI.
  Logic: After resolving RxCUI, fetch properties once and cache. This gives
  you: generic name, brand names, drug class, mechanism category.

- `GET /rxcui/[rxcui]/related?tty=IN` — Returns the ingredient (IN) term,
  i.e., the pure generic name stripped of dose and form. "Lisinopril 10 mg
  tablet" → RxCUI for ingredient "lisinopril".
  Logic: Use ingredient-level RxCUI for all interaction and class queries,
  because dose form doesn't matter for pharmacological relationships.

- `GET /rxcui/[rxcui]/ndcs` — Returns National Drug Codes (NDCs) associated
  with an RxCUI. NDC is the FDA's product-level identifier.
  Logic: Store the NDC alongside the RxCUI. NDC is needed for OpenFDA label
  queries and drug recall checks.

- `GET /spellingsuggestions?name=[string]` — Fuzzy spell correction for
  drug names. Returns suggested normalized names when OCR produces a garbled
  drug name.
  Logic: Use this as the fallback when direct RxCUI lookup fails (confidence
  below threshold). Show suggested corrections to the provider rather than
  silently failing.

**Where this feeds:**
- Note Reformatter (F31) — medication classification
- Medication Reference (F10) — all drug lookups
- Prepped Note (F10e) — medication section normalization
- Drug interaction checker (new)
- Drug recall checker (new)
- Allergy cross-reference (new)
- PA Generator (F26) — drug class / step therapy language
- Lab trend contextualization (F11)
- Formulary gap detection (new)

**Cache strategy:**
RxCUI for a given drug name is stable. Cache indefinitely with a 30-day
background refresh. Drug properties (name, class, ingredient) cached 30 days.
NDCs cached 7 days (packaging changes more frequently).

---

#### 1.2 RxClass API
**Base URL:** `https://rxnav.nlm.nih.gov/REST/rxclass/`
**Auth:** None required
**No API key required**

**What it does:**
Maps drugs to therapeutic classes across multiple classification systems:
ATC (Anatomical Therapeutic Chemical), EPC (FDA Established Pharmacologic
Class), VA class, MeSH pharmacological actions, and more.

**Key endpoints and their logic:**

- `GET /class/byRxcui?rxcui=[rxcui]` — Returns all drug classes for an RxCUI
  Logic: After normalizing a medication through RxNorm, fetch its class
  membership. A drug can belong to multiple classes (lisinopril is an
  antihypertensive, an ACE inhibitor, and a heart failure drug). Store all
  class memberships for each drug.

- `GET /classMembers?classId=[id]&relaSource=ATC` — Returns all drugs in a
  given class.
  Logic: Used by the Medication Reference module. Provider selects a condition
  → system fetches the drug class(es) appropriate for that condition → fetches
  all members → cross-references with OpenFDA for label details.
  This is how "show me first-line antihypertensives" works without a table.

- `GET /class/byDrugName?drugName=[name]` — Shortcut combining name lookup
  and class assignment in one call.

**Where this feeds:**
- Medication Reference (F10) — condition → drug class → drug list
- PA Generator (F26) — step therapy position ("this is a third-line agent")
- Drug interaction checker — class-level interactions
- Formulary gap detection — "patient has [condition] but no [drug class]"
- Pre-visit note prep — Assessment/Plan boilerplate by drug class

**Cache strategy:**
Drug-to-class mappings are very stable. Cache 90 days.

---

#### 1.3 OpenFDA Drug Label API
**Base URL:** `https://api.fda.gov/drug/label.json`
**Auth:** No key required for <1000 req/day; free API key for higher volume
**Rate limit:** 240 req/min without key; 1000 req/min with free key
**Register at:** `https://open.fda.gov/apis/authentication/`

**What it does:**
Returns the complete FDA-approved prescribing information (package insert)
for any drug. This is the legal label — the most authoritative source for
indications, contraindications, warnings, drug interactions, dosing, and
monitoring requirements.

**Key query patterns and their logic:**

- `?search=openfda.rxcui:[rxcui]&limit=1` — Fetch label by RxCUI.
  This is the primary query method once you have the RxCUI.

- `?search=openfda.generic_name:[name]&limit=1` — Fallback when no RxCUI.

**Label sections to extract and cache (by field name):**
- `indications_and_usage` → what the drug is approved for
- `contraindications` → absolute contraindications (feeds allergy/condition checks)
- `warnings_and_cautions` → black box warnings flagged prominently
- `drug_interactions` → text description of known interactions
- `pregnancy` / `pregnancy_or_breast_feeding` → pregnancy safety
- `renal_impairment` / `dosage_and_administration` → renal dosing guidance
- `pediatric_use` → age restrictions
- `adverse_reactions` → most common side effects
- `overdosage` → toxicity context
- `how_supplied` → available formulations

**Logic for label parsing:**
FDA labels are long free-text documents, not structured data. The plan is
to store the full label text and extract key safety signals using pattern
matching on known label language (e.g., "CONTRAINDICATED in patients with"
or "Avoid use in patients with" triggers a contraindication flag). For
display, show the relevant section excerpt rather than the full label.

**Where this feeds:**
- Medication Reference (F10) — replaces entire hand-curated database
- Pregnancy/Renal filter (F10c) — reads directly from label sections
- Pre-visit note prep — monitoring language in Assessment/Plan
- Allergy-aware prescribing check — contraindications vs. patient conditions
- Drug interaction checker — `drug_interactions` section
- Abnormal lab interpretation — monitoring requirements from label
- PA Generator (F26) — FDA-approved indication language for PA narrative

**Cache strategy:**
Drug labels are updated infrequently. Cache 30 days. Flag cache staleness
visually ("Label data from [date]"). On pre-visit prep overnight run, refresh
labels for medications on today's patients proactively.

---

#### 1.4 OpenFDA Drug Adverse Events API
**Base URL:** `https://api.fda.gov/drug/event.json`
**Auth:** Same as drug label API

**What it does:**
Returns real-world adverse event reports submitted to FDA (FAERS database).
Over 20 million reports covering every approved drug.

**Key query logic:**

- `?search=patient.drug.medicinalproduct:[rxcui_or_name]&count=patient.reaction.reactionmeddrapt.exact`
  Returns a count of reported reactions, sorted by frequency.
  Logic: Show top 5 adverse reactions for any drug in the Medication Reference.
  This is "most commonly reported side effects in real-world FDA data" —
  different from (and complementary to) the label's adverse reactions list
  which is from clinical trials.

- Time-scoped queries to detect emerging safety signals:
  `?search=receivedate:[20240101+TO+20250101]+AND+patient.drug.medicinalproduct:[name]`
  Logic: A weekly background job queries for recent adverse event reports for
  drugs in the practice's most-prescribed medications. Unusual spikes in
  report frequency can be an early warning before a formal FDA safety alert.

**Where this feeds:**
- Medication Reference (F10) — "real-world side effects" card
- Drug safety monitoring module (new)
- Pre-visit patient education prep

---

#### 1.5 OpenFDA Drug Recalls API
**Base URL:** `https://api.fda.gov/drug/enforcement.json`
**Auth:** Same as above

**What it does:**
Returns active and historical drug recall enforcement actions.

**Key query logic:**

- `?search=status:Ongoing+AND+product_description:[drug_name]`
  Returns active recalls matching a drug name.
  Logic: Daily morning job queries this endpoint for every unique drug in the
  practice's patient database. Match against current patient med lists.

- Match logic: Compare the recall's `product_description` field against
  cached RxCUI mappings. The recall may list a brand name or generic —
  both should match.

- `recall_number`, `reason_for_recall`, `classification` (Class I/II/III),
  `recalling_firm`, `distribution_pattern` — all stored with the recall record.

**Classification logic for alert severity:**
- Class I (most serious, risk of death/serious injury) → push notification
  with priority 2 (emergency, requires acknowledgment)
- Class II (temporary health consequences) → priority 1 notification
- Class III (unlikely to cause adverse health) → morning briefing mention only

**Where this feeds:**
- Drug Recall Alert System (new Feature)
- Morning Briefing (F22) — "No active recalls" or recall count
- Patient Chart View — recall badge on medication tab if recall affects
  a drug the patient takes
- Delayed Message Sender (F18) — auto-draft patient notification

---

#### 1.6 ICD-10 API (NLM Clinical Table Search Service)
**Base URL:** `https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search`
**Auth:** None required
**No API key required**

**What it does:**
Live search of the complete ICD-10-CM dataset. Returns code, description,
parent codes (hierarchy), and whether the code is a valid billing code
(some codes are "header" codes not valid for billing).

**Key query logic:**

- `?sf=code,name&terms=[search_string]&maxList=20`
  Returns up to 20 matching codes and descriptions.
  Logic: Powers the Coding Suggester (F17) autocomplete field. As the
  provider types a diagnosis term, this query fires on each keystroke
  (debounced to 300ms) and returns matching codes instantly.

- `?sf=code,name&terms=[code]` — Reverse lookup: code → description.
  Logic: When an ICD-10 code comes in from the Clinical Summary XML without
  its description, resolve it here.

- Hierarchy navigation: ICD-10 codes have parent-child relationships.
  E11.9 (DM2 unspecified) is a child of E11 (Type 2 diabetes mellitus).
  The API returns parent codes, enabling the specificity reminder (F17b):
  if provider selects E11.9, system queries children of E11 and offers
  more specific options.

**Where this feeds:**
- Coding Suggester (F17) — primary search engine
- Note Reformatter (F31) — diagnosis classification
- Specificity reminder (F17b)
- Code pairing suggestions (F17c)
- Care gap trigger evaluation
- Billing anomaly detection (F14b)

**Cache strategy:**
ICD-10-CM is updated annually (October 1 each year). Cache the full
dataset locally after the first query run and rebuild annually. For
autocomplete, use the local cache first (fast), fall back to API on miss.

---

#### 1.7 LOINC API / Regenstrief FHIR Server
**Base URL:** `https://fhir.loinc.org/` (FHIR R4)
**Auth:** Free account required at `https://loinc.org/join/`
**LOINC license:** Free for US healthcare use

**What it does:**
LOINC (Logical Observation Identifiers Names and Codes) is the universal
standard for lab test identification. Every lab result in the Clinical
Summary XML has a LOINC code. Querying LOINC by code returns:
- Official test name (long and short forms)
- Component (what is being measured)
- System (what specimen type)
- Scale type (quantitative/qualitative/ordinal)
- Units of measure (UCUM standard)
- Normal range reference (where published)
- Panel membership (which panels include this test)

**Key query logic:**

- `GET /CodeSystem/$lookup?system=http://loinc.org&code=[loinc_code]`
  Returns full LOINC properties for a code.
  Logic: On Clinical Summary XML import, for each lab result, query LOINC
  for the code in the XML's `<value>` observation identifiers. Cache the
  result. From this point forward, every lab result in the system has:
  a human-readable name, the correct units, and the reference range.

- `GET /ValueSet/$expand?url=http://loinc.org/vs/[panel_id]`
  Returns all component tests in a standard panel (e.g., BMP, CBC, lipids).
  Logic: Lab panel grouping (F11d) becomes automatic. When a set of lab
  results arrives, group them by panel membership rather than by manual
  configuration.

**LOINC panel codes relevant to primary care:**
- `24323-8` — Comprehensive metabolic panel (CMP)
- `24322-0` — Basic metabolic panel (BMP)
- `58410-2` — CBC with differential
- `57698-3` — Lipid panel
- `24360-0` — Hemoglobin A1c
- `11580-8` — Thyroid stimulating hormone
- `2823-3` — Potassium
- `2160-0` — Creatinine
- `33914-3` — eGFR (CKD-EPI)
- `1751-7` — Albumin
- `14804-9` — LDL cholesterol

**Where this feeds:**
- Lab Value Tracker (F11) — test identification, units, reference ranges
- Lab panel grouping (F11d) — automatic panel assembly
- Abnormal lab interpretation — reference range for contextualization
- Prepped Note — lab section of pre-visit note
- Clinical Summary XML parsing — LOINC code resolution on import

---

#### 1.8 UMLS API
**Base URL:** `https://uts.nlm.nih.gov/uts/rest/`
**Auth:** Free account at `https://uts.nlm.nih.gov/uts/signup-login`
**API key:** Provided after registration (free)

**What it does:**
The UMLS (Unified Medical Language System) is the master crosswalk between
all medical terminologies: ICD-10, SNOMED CT, RxNorm, LOINC, MeSH, CPT,
and ~150 others. A UMLS CUI (Concept Unique Identifier) represents a single
clinical concept across all systems.

**Key query logic:**

- `GET /search/current?string=[term]&searchType=normalizedString`
  Returns the UMLS CUI and all associated codes in all vocabularies for
  a search term. "hypertension" → CUI C0020538 → ICD-10: I10, SNOMED:
  38341003, MeSH: D006973, NCI: C3117.

- `GET /content/current/CUI/[cui]/atoms?sabs=ICD10CM,SNOMEDCT_US,RXNORM`
  Returns specific vocabulary codes for a known CUI.
  Logic: Used by Note Reformatter for diagnosis disambiguation. If the prior
  note uses SNOMED terminology (from some EHRs), resolve to ICD-10 for
  NP Companion's billing-focused display.

- Cross-terminology synonym resolution:
  "HTN" → UMLS → "Hypertension" → ICD-10 I10
  "DM2" → UMLS → "Type 2 diabetes mellitus" → ICD-10 E11.9
  "CKD3" → UMLS → "Chronic kidney disease stage 3" → ICD-10 N18.3
  Logic: Note Reformatter classifier no longer depends on fuzzy string
  matching. Every abbreviated or non-standard diagnosis term gets resolved
  through UMLS first. Accuracy approaches 98% for common abbreviations.

**Where this feeds:**
- Note Reformatter (F31) — diagnosis normalization
- Coding Suggester (F17) — synonym resolution for search
- Code pairing (F17c) — clinical relationship queries
- ICD-10 specificity (F17b) — hierarchy navigation

---

### Tier 2 — Clinical Decision Support APIs

---

#### 2.1 AHRQ HealthFinder API
**Base URL:** `https://health.gov/myhealthfinder/api/v3/`
**Auth:** None required
**No API key required**

**What it does:**
Returns USPSTF-aligned preventive care recommendations personalized to a
patient's age, sex, and pregnancy status. This is the US government's
official USPSTF recommendation engine as a queryable API.

**Key query logic:**

- `GET /topicsearch.json?lang=en&age=[age]&sex=[M/F]&pregnant=[0/1]`
  Returns all recommended preventive services for the given demographics.
  Each result includes: recommendation name, grade (A/B/C/D/I), description,
  frequency, and category (screening/counseling/preventive medication).

**Logic for care gap evaluation:**
On Clinical Summary XML import (or schedule scrape), for each patient:
1. Extract age, sex, pregnancy status from demographics
2. Query HealthFinder with those demographics
3. For each returned recommendation, check the patient's Health Maintenance
   section in the XML for a corresponding completion date
4. If completion date is absent or older than the recommendation frequency,
   create or update a CareGap record
5. Priority: Grade A gaps > Grade B > Grade C

**Logic for care gap closure:**
HealthFinder recommendations map to HCPCS billing codes (see 2.3 CMS API).
When a gap is marked addressed, the billing suggestion is derived from the
HealthFinder recommendation category:
- Screening → preventive service code
- Counseling → behavioral health integration code
- Preventive medication → medication management code

**Where this feeds:**
- Care Gap Tracker (F15) — replaces all hardcoded USPSTF rules
- Care gap auto-population (F15a)
- Panel-wide gap report (F15c) — consistent recommendation definitions
- Billing capture suggestions (F16) — linked via recommendation category
- Morning Briefing (F22) — "3 care gaps for today's patients"
- Today View — care gap badges per patient

---

#### 2.2 CDC Immunization Data via RxNorm CVX
**Access via:** RxNorm API (CVX vaccine groups added 2025)
**Supplementary:** `https://www.cdc.gov/vaccines/schedules/` (downloadable)
**Auth:** None required

**What it does:**
CDC's CVX (Clinical Vaccine administered) codes are now part of the RxNorm
dataset. The CDC adult immunization schedule is available as a downloadable
dataset with recommended vaccines, age ranges, intervals, and catch-up logic.

**Logic for immunization gap detection:**
The Clinical Summary XML contains an Immunizations section with CVX codes
and administration dates. The logic:
1. Parse immunization history from XML → list of (CVX code, date)
2. Cross-reference with CDC adult schedule for patient's age and risk factors
   (risk factors come from the Risk Factors section of the Clinical Summary
   or from the patient's problem list)
3. Calculate which vaccines are due, overdue, or never received
4. Surface as care gap items in the same interface as USPSTF gaps

**Special logic for risk-based vaccines:**
Some vaccines are recommended based on clinical conditions:
- Pneumococcal → age 65+ OR chronic lung disease (from problem list)
- Hepatitis B → unvaccinated adults (check immunization history)
- Shingrix → age 50+ (two-dose, check if series complete)
- Hepatitis A → travel risk (from social history in XML)
The problem list and social history from the XML feed these conditional rules.

---

#### 2.3 CMS HCPCS / CPT Reference Data
**Access via:** CMS public data at `https://www.cms.gov/Medicare/Coding/`
**Downloadable as flat files, not a live API**
**No key required**

**What it does:**
HCPCS Level I (CPT codes) and Level II codes with official descriptions,
RVU values, and Medicare fee schedule reimbursement amounts.

**Logic for implementation:**
Download the CMS physician fee schedule flat file annually (published each
November for the following year). Store in SQLite as a local lookup table.
This is not a live API — it's a locally-maintained reference dataset that
is updated once per year.

**Key data points per code:**
- Code (CPT or HCPCS)
- Short description
- Long description
- Work RVU (for E&M calculator, Feature 14a)
- Practice expense RVU
- Total RVU
- Medicare facility and non-facility payment rates (national average)
- Physician supervision requirements

**Logic for E&M calculator (F14a):**
The 2023 AMA E&M guidelines use time-based or MDM-based billing.
Time thresholds for office visit codes:
- 99202/99212: 15-29 minutes
- 99203/99213: 30-44 minutes
- 99204/99214: 45-59 minutes
- 99205/99215: 60-74 minutes
These thresholds, combined with the face-to-face timer data, determine
the suggested E&M level. The RVU values from this dataset calculate
estimated revenue for the billing audit log and monthly report.

**Logic for billing capture suggestions (F16):**
Each HealthFinder recommendation (2.1) maps to a preventive service
HCPCS code. The HCPCS dataset provides the payment rate. The billing
capture suggestion shows: "Documenting and billing [code] for [service]
adds approximately $[rate] to this visit."

---

#### 2.4 NLM Clinical Table Search — Conditions API
**Base URL:** `https://clinicaltables.nlm.nih.gov/api/conditions/v3/search`
**Auth:** None required

**What it does:**
Searchable database of clinical conditions with SNOMED codes, ICD-10 mappings,
and consumer-friendly names. Optimized for autocomplete use in clinical forms.

**Logic for differential diagnosis widget:**
Given a chief complaint string, query this endpoint. Return conditions that
match the symptom terms in the complaint. Cross-reference returned conditions
against the patient's existing problem list (from XML) to identify whether
any new differentials are already part of their known history.
Display as: known conditions (from problem list, not a differential) vs.
new differentials to consider.

This is not a diagnostic engine — it surfaces clinical possibilities for
the provider to evaluate. The display explicitly labels it as a reference
tool, not a recommendation.

---

### Tier 3 — Literature and Education APIs

---

#### 3.1 NCBI E-utilities (PubMed)
**Base URL:** `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`
**Auth:** Free API key recommended (higher rate limits)
**Register at:** `https://www.ncbi.nlm.nih.gov/account/`

**What it does:**
Programmatic access to PubMed's 35+ million citations. Returns article
metadata including title, authors, journal, abstract, publication date,
and MeSH terms.

**Key query logic for NP Companion:**

Phase 1 — Search:
`esearch.fcgi?db=pubmed&term=[condition]+AND+(guideline[pt]+OR+systematic+review[pt]+OR+clinical+practice[ti])&sort=pub+date&retmax=5`
Returns PMIDs of recent guideline and review articles.

Phase 2 — Fetch:
`efetch.fcgi?db=pubmed&id=[pmids]&rettype=abstract&retmode=json`
Returns titles and abstracts for the found articles.

**Logic for context-aware pre-loading:**
When a patient's chart is opened in NP Companion, the system identifies
their top 3 active diagnoses (by recency of encounter) and pre-loads
recent guideline articles for each in the background. By the time the
provider opens the Guideline Lookup panel, results are already cached.

**Logic for recency filtering:**
Primary care guideline changes matter most when recent. Filter results
to articles published within 3 years. A staleness flag appears on any
cached result older than 90 days.

**Display logic:**
Results shown as cards: journal name + impact indicator (JAMA, NEJM,
AFP, AAFP flagged with colored badge), publication year, article title,
one-sentence abstract excerpt. Click to open full abstract in a modal.
DOI link to full text (may require institutional access).

---

#### 3.2 NLM MedlinePlus Connect API
**Base URL:** `https://connect.medlineplus.gov/service`
**Auth:** None required
**No API key required**

**What it does:**
Returns curated, patient-facing health information for any ICD-10, SNOMED,
RxNorm, or LOINC code. Content is written at a 6th-8th grade reading level
in English and Spanish. Maintained by NLM.

**Key query logic:**

- `?mainSearchCriteria.v.c=[icd10_code]&mainSearchCriteria.v.cs=2.16.840.1.113883.6.90&knowledgeResponseType=application/json`
  Returns patient education topics for an ICD-10 code.

- `?mainSearchCriteria.v.c=[rxcui]&mainSearchCriteria.v.cs=2.16.840.1.113883.6.88`
  Returns patient education topics for a medication (by RxCUI).

**Logic for patient education auto-drafting:**
When a care gap is addressed in the care gap tracker:
1. Identify the ICD-10 code or condition type
2. Query MedlinePlus for that code
3. Return the top result's summary text and a URL
4. Pre-populate the patient message template (F19) with:
   - The appropriate urgency tier (Tier 1-2 for care gap follow-up)
   - MedlinePlus summary as the educational paragraph
   - MedlinePlus URL as "for more information"
   - Provider's standard closing language

The provider reviews and edits before sending. MedlinePlus content is
pre-attribution compliant (NLM requires attribution statement).

**Also used for:**
New prescription patient education — when a new medication appears in
the pre-visit note's Medications section, offer to generate a patient
education message about the drug via MedlinePlus RxNorm query.

---

### Tier 4 — Weather and Location APIs

---

#### 4.1 Open-Meteo API
**Base URL:** `https://api.open-meteo.com/v1/`
**Auth:** None required
**Rate limit:** 10,000 requests/day free, no key needed

**What it does:**
Returns current weather conditions and hourly forecast by latitude/longitude.
No registration, no API key, completely free.

**Key query logic:**
`GET /forecast?latitude=[lat]&longitude=[lon]&current_weather=true&hourly=precipitation_probability`
Returns current temperature, weather code, wind speed, and hourly
precipitation probability.

**Logic for Morning Briefing:**
Geocode the clinic ZIP code to lat/lon once during setup (store in config).
On morning briefing generation, fetch current weather and the probability
of precipitation during commute hours (7-9 AM). If precipitation probability
>50%, add "Rain likely during commute" to the briefing. Temperature extremes
(>95°F or <20°F) also flagged. Weather data is non-clinical, non-PHI —
safe to include in any notification.

---

## The Data Flow Architecture

Understanding how data flows between these APIs and through NP Companion
is essential for planning the implementation. There are three data flow
patterns:

### Pattern A — Import-Time Enrichment (Clinical Summary XML)
```
AC exports XML
    ↓
XML parser extracts raw data
    ↓
For each medication: RxNorm normalization → RxCUI → properties → class
For each diagnosis: ICD-10 API verification → UMLS crosswalk if needed
For each lab result: LOINC code → test name + units + reference range
For each immunization: CVX code → vaccine name + series info
    ↓
Enriched data stored in database alongside raw XML data
    ↓
Patient Chart View populated from enriched database
    ↓
XML file scheduled for deletion in 183 days
```

This pattern runs once per Clinical Summary import. The enrichment is
background work — the provider sees the patient chart view while enrichment
is completing, with a "Syncing..." indicator on any section still loading.

### Pattern B — Real-Time Interactive (Provider is Typing)
```
Provider types in search field
    ↓ (300ms debounce)
ICD-10 Clinical Tables API → autocomplete suggestions
    ↓
Provider selects a code
    ↓
UMLS API → synonym check, parent code, children codes
    ↓
ICD-10 specificity reminder if unspecified code selected
    ↓
Code pairing suggestions from database history
    ↓
MedlinePlus → patient education content (background, not blocking)
```

This pattern must be fast (<200ms perceived latency). Always query the
local cache first. Only hit the live API on cache miss.

### Pattern C — Scheduled Background Jobs (Runs Overnight)
```
Morning briefing generation job (6 AM):
    → Open-Meteo weather fetch
    → HealthFinder query for each scheduled patient
    → PubMed guideline pre-load for scheduled patients' diagnoses
    → OpenFDA recall check against full patient medication database
    → CDC immunization gap evaluation

Pre-visit note prep job (8 PM):
    → RxNorm normalization for each scheduled patient's medications
    → OpenFDA label fetch/refresh for each medication
    → Drug interaction check across full med list
    → Allergy cross-reference check
    → MedlinePlus pre-fetch for new medications

Weekly jobs (Sunday 2 AM):
    → ICD-10 cache freshness check
    → RxNorm cache freshness check
    → OpenFDA recall full scan
    → PubMed top-5 guideline refresh for each provider's common diagnoses
```

All scheduled jobs run through APScheduler. Each job is independently
try/except wrapped. Job failures are logged to database and reported in
the agent health monitor (F3a). Jobs do not block each other.

---

## Feature-by-Feature Display Design

### Pre-Visit Note Prep — Clinically Aware Note Generation

The Prepped Note tab (F10e) is the highest-value display in the system.
It should feel like a note that was already started thoughtfully, not
a blank form. The visual design logic:

**Section population states (three visual states per section):**

1. **Auto-populated from XML** (blue left border): Content came from the
   Clinical Summary XML directly. Provider can edit but should verify.
   Label: "From chart — [date]"

2. **API-enriched** (teal left border): Content was generated by combining
   XML data with API lookups (e.g., Assessment plan text informed by
   FDA label monitoring requirements). Label: "AI-assisted — review"

3. **Blank — provider fills** (gray left border): Sections that require
   clinical judgment and cannot be pre-populated (HPI, subjective complaints,
   most of the physical exam for today's visit). Label: "Awaiting today"

**Safety banner logic:**
If any of the following are detected during pre-visit enrichment, a colored
banner appears at the top of the Prepped Note tab BEFORE any section:

- 🔴 RECALL: "[Drug] active FDA recall — Class [I/II]"
- 🔴 INTERACTION: "[Drug A] + [Drug B] — [interaction type] (FDA label)"
- 🟡 ALLERGY CONCERN: "[Drug] contraindicated with [allergy] (possible
  cross-reactivity)"
- 🟡 OVERDUE: "[N] labs overdue for this patient"
- 🟡 MONITORING DUE: "Creatinine monitoring due (per lisinopril label)"
- 🔵 CARE GAPS: "[N] USPSTF-recommended screenings due"

These banners are dismissible per-visit. Dismissed banners are logged.

**Assessment/Plan section — structured generation logic:**
For each active diagnosis in the problem list:
1. Fetch the ICD-10 description (ICD-10 API)
2. Identify the drug class associated with the patient's current treatment
   (RxClass API — "patient is on an ACE inhibitor for hypertension")
3. Fetch monitoring requirements from the FDA label of each relevant drug
4. Check if any monitoring labs are overdue (Lab Tracker + LOINC reference range)
5. Generate a plan line in the format:
   `# [Diagnosis] ([ICD-10]): [current treatment brief]. [monitoring status].
   [next step if applicable].`

This is not AI content generation — it is template filling from structured
data sources. The provider sees a structured starting point, not a blank
assessment box.

---

### Medication Reference — The Drug Intelligence Panel

**Display design for F10 with API integration:**

The medication reference is no longer a list of drugs to browse. It is a
context-aware search tool. Two entry points:

**Entry Point 1: Condition-first search**
Provider types "hypertension" → system queries RxClass for antihypertensive
drug classes → returns a tiered card view:

```
HYPERTENSION — First-Line Agents
──────────────────────────────────────────────
┌─ ACE Inhibitors ────────────────────────────┐
│ Lisinopril, Enalapril, Ramipril             │
│ ✓ Guideline first-line  ✓ Generic available │
│ ⚠ Monitor: K+, Cr, cough                   │
│ ✗ Avoid: Pregnancy, Bilateral RAS          │
│ [View Drugs] [FDA Label] [My Notes]         │
└─────────────────────────────────────────────┘
┌─ Thiazide Diuretics ────────────────────────┐
│ HCTZ, Chlorthalidone                        │
│ ✓ Guideline first-line  ✓ Generic available │
│ ⚠ Monitor: K+, Na+, glucose                │
│ [View Drugs] [FDA Label] [My Notes]         │
└─────────────────────────────────────────────┘
[Second-Line Agents ▼]  [Special Populations ▼]
```

**Entry Point 2: Drug-first search**
Provider types "lisinopril" → RxNorm normalizes → FDA label fetched →
returns a drug-focused card:

```
LISINOPRIL  (ACE Inhibitor — Antihypertensive)
RxCUI: 203644 | Generic available
──────────────────────────────────────────────
INDICATIONS          Hypertension, Heart Failure, Post-MI
STARTING DOSE        10 mg daily
MAX DOSE             40 mg daily (HTN); 40 mg daily (HF)
MONITORING           Cr, K+ at baseline, 1-2 wks after start, then q6m
PREGNANCY            Category D — CONTRAINDICATED (trimester 2/3)
RENAL IMPAIRMENT     CrCl <30: start 2.5-5 mg; titrate cautiously
BLACK BOX            Fetal toxicity — stop at pregnancy detection
──────────────────────────────────────────────
REAL-WORLD SIDE EFFECTS (FDA FAERS, top 5)
  Cough (26%), Hyperkalemia (14%), Renal impairment (8%)...
──────────────────────────────────────────────
PRACTICE NOTES       [Provider-editable]
FORMULARY NOTES      [Shared annotations from colleagues]
──────────────────────────────────────────────
[FDA Full Label] [PubMed Guidelines] [Patient Ed]
```

**Patient context mode:**
When opened from within a patient chart, the medication reference displays
additional context overlaid on the drug card:

```
⚠ THIS PATIENT:
  • Creatinine: 1.4 (3 months ago) — monitor if starting
  • Current K+: 4.8 — borderline, monitor closely if adding ACE inhibitor
  • Insurance: HEALTHKEEPERS — ACE inhibitors are Tier 1 (preferred)
  • No documented allergy to ACE inhibitors
```

This context comes from the patient's cached Clinical Summary data. It
makes the medication reference directly relevant to the specific patient
the provider is seeing.

---

### Lab Value Tracker — LOINC-Powered Intelligence

**Display design for F11 with API integration:**

The lab tracker overview table gains a new column: `Reference Range` (from
LOINC, shown as a passive reference, not an alert threshold — the custom
threshold is separate).

**Trend card design with LOINC context:**

```
CREATININE (Serum)                              [LOINC: 2160-0]
──────────────────────────────────────────────
Reference Range:   0.7 – 1.2 mg/dL (female)
Patient Threshold: ≤1.8 mg/dL  (your custom)
──────────────────────────────────────────────
  2.0 ┤
  1.8 ┤                                    ──✦  ← 1.7 (today)
  1.6 ┤                               ──✦
  1.4 ┤              ──✦──────────✦
  1.2 ┤─────✦──✦
  1.0 ┤
      └──────────────────────────────────────
       Jun'24  Sep'24  Dec'24  Mar'25  Jun'25

Trend: ↑ INCREASING  (last 3 readings)

⚠ Patient is on lisinopril — per FDA label, nephrotoxicity
  monitoring required. Consider dose review.

⚠ Patient is on ibuprofen (PRN, from med list) — NSAID use in
  CKD may accelerate decline.
```

The contextual warnings (lisinopril monitoring, NSAID concern) are derived
from the FDA label's monitoring section, cross-referenced with the patient's
medication list. They are generated once during import-time enrichment and
cached with the lab trend data.

---

### Drug Safety Panel (New Feature)

**Concept:**
A dedicated panel in the Patient Chart View that aggregates all active
drug safety signals for a patient. Accessible from the Medications tab.

**Display design:**

```
DRUG SAFETY OVERVIEW — [Patient ID last-4]
Last checked: Today 6:02 AM
──────────────────────────────────────────────
INTERACTIONS                                [2]
──────────────────────────────────────────────
🔴 Moderate: Fentanyl + [potential CNS depressant]
   Source: FDA label — "Enhanced CNS depression"
   [View Detail] [Document Reviewed]

🟡 Minor: Lisinopril + Tylenol (acetaminophen)
   Source: FDA label — "Monitor renal function"
   [View Detail] [Document Reviewed]

──────────────────────────────────────────────
RECALLS                                     [0]
──────────────────────────────────────────────
✅ No active recalls affecting this patient's
   medications as of today.

──────────────────────────────────────────────
MONITORING DUE                              [2]
──────────────────────────────────────────────
⚠ Lisinopril: Renal function (Cr, K+) — last 3 months ago
  Per FDA label: monitor q3-6m
  [Order Labs] [View Tracker]

⚠ Januvia (sitagliptin): HbA1c — last 4 months ago
  Per FDA label: monitor q3m until stable
  [Order Labs] [View Tracker]
```

Each item has a `Document Reviewed` button that logs the review to the
audit trail — important for liability if a drug interaction results in
an adverse event. "I saw this interaction and considered it" is documented.

---

### Coding Suggester — Real-Time Intelligence Panel

**Display design for F17 with ICD-10 API + UMLS:**

The coding suggester becomes a floating panel accessible via Win+C hotkey
or from the Prepped Note tab. It has two modes:

**Search Mode:**
```
┌──────────────────────────────────────────────────┐
│ 🔍 Type diagnosis, symptom, or code...           │
│ ┌────────────────────────────────────────────────┤
│ │ HTN                                            │
│ └────────────────────────────────────────────────┤
│                                                   │
│ I10   Essential (primary) hypertension           │
│       ⭐ Your most used  📌 Add to note          │
│                                                   │
│ I11.9 Hypertensive heart disease w/o HF          │
│       💡 More specific  📌 Add to note           │
│                                                   │
│ I13.10 Hypertensive heart and CKD disease...     │
│        💡 Consider if CKD present                │
│                                                   │
│ COMMONLY PAIRED WITH I10:                        │
│  E11.9 Type 2 diabetes mellitus                  │
│  N18.3 CKD stage 3                               │
│  E78.5 Hyperlipidemia                            │
└──────────────────────────────────────────────────┘
```

**Patient Context Mode** (when opened from a patient chart):
Pairs suggestions are filtered to only show conditions NOT already in the
patient's problem list — the system knows their existing diagnoses and only
suggests what might be missing from the current encounter.

---

### Differential Diagnosis Widget (New Feature)

**Display design:**

The differential diagnosis widget is embedded in the Prepped Note tab,
collapsed by default, expandable with one click. It appears below the
Chief Complaint section.

```
DIFFERENTIAL CONSIDERATIONS  [▶ Expand]

Based on: Chief Complaint + Patient Demographics + Problem List
──────────────────────────────────────────────────────────────
HIGH CONSIDERATION (based on existing diagnoses):
  ✓ Acute sinusitis (J01.90) — already in assessment
  ✓ COVID-19 (U07.1) — already in assessment

NEW DIFFERENTIALS TO CONSIDER:
  Bacterial pneumonia — 45F with cough, respiratory symptoms
  Acute bronchitis — seasonal pattern
  GERD exacerbation — patient has known GERD (K21.9)

RED FLAGS — ALWAYS CONSIDER:
  Pulmonary embolism (pleuritic pain? tachycardia?)
  Cardiac origin (dyspnea, diaphoresis noted)

──────────────────────────────────────────────────────────────
Source: NLM Clinical Conditions + clinical relationship data
⚠ Not a diagnostic recommendation — clinical reference only
```

The red flags section is hardcoded by chief complaint category (chest pain,
dyspnea, headache, etc.) — these do not depend on any API and are never
wrong because they are meant to prompt consideration, not diagnose.

The clinical differentials come from the NLM Conditions API (2.4) queried
against the chief complaint. The "already in assessment" items come from
cross-referencing against the patient's current XML problem list and the
items already added to today's prepped note.

---

## Provider Customization System

Every provider using NP Companion has individual control over how APIs
are used. These settings live in the user's preferences JSON column and
are configurable from `/settings/api` (a new settings page, not in the
original plan).

### API Preferences Per Provider

**Medication Reference preferences:**
- `medref_default_view`: condition-first vs. drug-first
- `medref_show_faers_data`: boolean (some providers prefer label-only, not
  FAERS adverse event data which can be alarming out of context)
- `medref_patient_context_mode`: boolean (show patient-specific overlay)
- `preferred_drug_classes`: ordered list — which drug classes appear first
  for common conditions (e.g., one provider may prefer CCBs over ACEi
  as first-line for certain patient populations based on their experience)

**Clinical decision support preferences:**
- `show_differential_widget`: boolean (some providers find it distracting)
- `differential_red_flags_only`: boolean (show only the red flags section)
- `guideline_lookup_auto_load`: boolean (whether PubMed pre-loads automatically)
- `guideline_publication_years`: integer (how many years back to include,
  default 3, range 1-10)

**Note generation preferences:**
- `note_api_enrichment_level`: enum (minimal / standard / full)
  - minimal: XML data only, no API enrichment in note sections
  - standard: medications normalized, lab values with units/ranges, care gaps
  - full: all enrichment including FDA monitoring language, interaction checks
- `assessment_plan_template_style`: provider writes their own Assessment/Plan
  template that defines how API-derived content is formatted. One provider
  might want: `# [Dx] ([code]): Stable. Continue [drug class].` while another
  prefers a more detailed format.
- `show_safety_banners`: boolean (some experienced providers may want less
  interruption from interaction warnings they already know)

**Lab tracking preferences:**
- `lab_reference_source`: LOINC (API, population-based) vs. custom
  (provider's own thresholds override LOINC ranges for all display)
- `trend_interpretation_sensitivity`: integer 3-10 (number of data points
  needed before trend direction is calculated; default 3)
- `monitoring_reminder_source`: FDA label only vs. FDA label + personal
  override vs. personal override only

**Care gap preferences:**
- `care_gap_grade_threshold`: which USPSTF grades to surface
  (default: show A and B; option to include C)
- `hide_care_gaps_with_reasons`: list of gap types to suppress (e.g., a
  provider who works exclusively with geriatric patients may suppress
  pediatric screening alerts)
- `immunization_schedule_source`: CDC adult schedule only vs. CDC + ACIP
  supplemental recommendations

**Patient education preferences:**
- `medlineplus_language`: en vs. es (provider can set Spanish as default
  for their patient population)
- `patient_ed_auto_draft`: boolean (whether MedlinePlus content auto-populates
  when a care gap is addressed)
- `patient_ed_reading_level_notice`: boolean (show a reminder to verify the
  patient's health literacy)

### Shared Practice-Wide API Configuration

Some API settings apply to all providers and are set by the admin:

**From `/settings/api` (admin only):**
- `openFDA_api_key`: practice's registered OpenFDA API key (higher rate limits)
- `pubmed_api_key`: practice's NCBI API key
- `umls_api_key`: practice's UMLS account API key
- `clinical_summary_export_folder`: local path for AC XML exports
- `api_cache_location`: where to store cached API responses (defaults to `data/api_cache/`)
- `recall_alert_class_threshold`: which recall classes trigger push notifications
  (default: Class I only; option to add Class II)
- `weather_zip_code`: clinic ZIP code for morning briefing weather

**API cache management:**
Admin can view cache statistics: number of cached entries per API, total
cache size, oldest cached entry, hit rate. A `Flush Cache` button per API
allows forced refresh when a known update occurred (e.g., new ICD-10 fiscal
year released).

---

## Offline / Degraded Mode Behavior

The APIs are enhanced tools, not dependencies. NP Companion must function
without internet access. The offline mode logic (F30) needs to account for
API availability:

**Graceful degradation by feature:**

| Feature | Online | Offline (cached) | Offline (no cache) |
|---------|--------|-------------------|---------------------|
| Medication Reference | Live FDA labels | Cached labels | Local text only |
| Coding Suggester | Live ICD-10 search | Cached ICD-10 db | No autocomplete |
| Care Gap Tracker | Live HealthFinder | Cached recommendations | No auto-gaps |
| Lab Reference Ranges | LOINC API | Cached ranges | Provider thresholds only |
| Drug Interaction Check | Live + cached | Cached | Not available — show warning |
| Drug Recall Check | Live check | 24h old check shown with staleness notice | Not available |
| PubMed Guidelines | Live search | Cached results | Not available |
| Patient Education | Live MedlinePlus | Cached content | Not available |
| Weather | Live | Not cached | Not shown |

**Staleness indicators:**
Any API-derived content displayed in the UI shows a small timestamp:
"from FDA label (cached 3 days ago)" or "live" if fetched within 1 hour.
This is important for liability — a provider should know if they're seeing
a 30-day-old drug label vs. a current one.

The offline banner (from F30 service worker) is extended to include API
status: "⚠ Running on cached clinical data. Last sync: [timestamp]. Some
drug information may not reflect recent updates."

---

## New Features — Complete Specifications

### New Feature A: Drug Recall Alert System
**Builds on:** OpenFDA Recalls API (1.5), Pushover Notifications (F21),
Delayed Message Sender (F18), RxNorm (1.1)

**Logic flow:**
1. Daily at 5:45 AM (15 minutes before morning briefing), run recall check
2. Query all unique RxCUI values in the entire patient medication database
3. For each drug: query OpenFDA recalls for status=Ongoing
4. Match: compare recalled product descriptions against RxCUI name variants
5. For any new match: create a RecallAlert record in database
6. In morning briefing: "FDA Recalls affecting patients: [N] — review list"
7. In Patient Chart View: red badge on Medications tab for affected patients
8. Provider action: one-click to draft patient notification message using
   Tier 4/5 result response template with recall details pre-populated

**Per-provider customization:**
Provider sets which recall classes trigger push notifications (default: Class I).
Provider can set auto-draft of patient notifications for Class I recalls
(draft appears in message queue, provider reviews before sending).

---

### New Feature B: Abnormal Lab Interpretation Assistant
**Builds on:** LOINC (1.7), OpenFDA Labels (1.3), RxNorm (1.1), Lab Tracker (F11)

**Logic flow:**
On each new lab result import from Clinical Summary XML:
1. Identify if the result is outside LOINC reference range OR provider's
   custom threshold
2. If outside range:
   a. Query patient's medication list (from database)
   b. For each medication: check if the FDA label mentions this lab value
      as a monitoring parameter or as a drug interaction concern
   c. Cross-reference: is any of the patient's medications known to cause
      this type of abnormality?
3. Generate contextual text: "[Lab] is [direction] — patient is on [drug]
   which [lists this as monitoring parameter / is known to affect this value].
   Consider: [brief clinical action from FDA label context]."
4. Store contextual text with the lab result
5. Display in Lab Tracker alongside the trend chart

**Display:** A collapsible "Clinical Context" section below each lab trend
chart. Not diagnostic language — framed as "considerations" with explicit
labeling as reference information.

---

### New Feature C: PubMed Guideline Lookup Panel
**Builds on:** NCBI E-utilities (3.1), Patient Chart View (F10e)

**Logic flow:**
The guideline panel is a sidebar widget accessible from the Patient Chart
View's Overview tab and from within the Prepped Note tab.

Pre-load logic (runs in background when chart opens):
1. Identify top 3 active diagnoses from patient's problem list (by
   encounter recency — most recently addressed diagnoses first)
2. For each: fire PubMed search query (type: guideline OR systematic review,
   date: last 3 years, journals: NEJM, JAMA, AAFP, AFP, Annals, BMJ)
3. Cache results per diagnosis for 30 days

**Display:** Stacked cards per diagnosis. Each card shows the most recent
3 articles as title + journal + year + one-sentence abstract excerpt. The
provider clicks to open the full abstract in a modal with a direct DOI link.
The guideline panel has a refresh button that forces a new live PubMed query.

**Per-provider customization:**
- Journal filter: which journals to include (default: high-impact primary
  care journals; option to add specialty journals relevant to the provider's
  patient population)
- Article types: guideline only / systematic review only / both
- Date range: 2 years / 3 years / 5 years

---

### New Feature D: Formulary Gap Detection
**Builds on:** RxClass (1.2), ICD-10 API (1.6), Clinical Summary XML data

**Logic flow:**
On Clinical Summary import:
1. For each active diagnosis in the problem list, fetch the expected drug
   classes for treatment (RxClass: conditions → drug class)
2. For each expected drug class, check whether the patient has any
   medication from that class in their current med list (cross-referenced
   via RxClass membership)
3. If no medication found for a diagnosable condition:
   a. If condition is chronic (chronicity field from problem list) and
      there has been more than one encounter: flag as formulary gap
   b. If condition is acute or recent: do not flag (may be watchful waiting)
4. Flagged gaps appear in the Patient Chart View as a yellow card in
   the Medications tab: "No [drug class] found for [diagnosis] — verify
   treatment plan"

**Important non-clinical framing:** This is a documentation/clinical review
prompt, not a prescribing mandate. The display explicitly says "verify
treatment plan" — the patient may be managed non-pharmacologically, which
is valid. The provider dismisses the flag with a note (e.g., "managed with
lifestyle modification") and it does not re-appear.

---

### New Feature E: Patient Education Auto-Draft
**Builds on:** MedlinePlus (3.2), Abnormal Result Templates (F19),
Delayed Message Sender (F18), ICD-10 API (1.6)

**Logic flow:**
Two triggers:

Trigger 1 — Care gap addressed:
Provider checks off a care gap in the Care Gap Tracker.
System identifies the ICD-10 or condition type of the gap.
Queries MedlinePlus for patient-facing content on that topic.
Pre-populates a message draft in the Delayed Message Sender with:
  - Tier 2 template wrapper (care gap addressed, no urgent action)
  - MedlinePlus summary paragraph
  - MedlinePlus URL for more information
  - Provider's sign-off language (from their preferences)
Draft appears in message queue, requires provider approval before sending.

Trigger 2 — New medication (detected in pre-visit prep):
When a new drug appears in the pre-visit prep that was not in the previous
Clinical Summary XML, query MedlinePlus for that drug (by RxCUI).
Pre-populate a message: "We have started you on [drug] for [condition].
Here is some information about your new medication: [MedlinePlus content]."

**Per-provider customization:**
- Language preference (English / Spanish — applies to MedlinePlus query)
- Auto-draft threshold: always draft / only for Grade A/B gaps / only
  when provider manually requests
- Default tier for care gap messages (Tier 1 vs. Tier 2)
- Whether to include the MedlinePlus URL (some providers prefer not to
  send external links to patients)

---

## The Intelligence Layer — How Everything Connects at Runtime

When a provider opens a patient chart in NP Companion, this is the complete
sequence of intelligence events that fire in the background:

```
CHART OPEN EVENT → patient MRN
│
├─► [Immediate, parallel]
│    ├─ Load cached Clinical Summary data from database
│    ├─ Load cached LOINC enrichment for all tracked labs
│    ├─ Load cached drug safety analysis
│    └─ Display patient chart with available data + loading indicators
│
├─► [Background, within 5 seconds]
│    ├─ Check Clinical Summary freshness (>24h old = show refresh prompt)
│    ├─ Check drug recall cache freshness (>24h = trigger recall check)
│    ├─ RxNorm normalization for any meds not yet cached
│    └─ OpenFDA label fetch for any meds not yet cached
│
├─► [Background, within 30 seconds]
│    ├─ Drug interaction analysis across full med list
│    ├─ Allergy cross-reference check
│    ├─ Formulary gap detection
│    ├─ LOINC reference range fetch for any new labs
│    └─ HealthFinder care gap evaluation
│
└─► [Background, within 60 seconds]
     ├─ PubMed pre-load for top 3 diagnoses
     ├─ MedlinePlus pre-fetch for new medications
     └─ FDA adverse events summary fetch
```

The UI uses progressive enhancement: the chart is usable immediately,
intelligence layers appear as they complete. Each section has a subtle
loading indicator that resolves when its background task completes.

This architecture means:
- The provider never waits for API calls
- API failures are invisible (section shows cached data with staleness note)
- The experience degrades gracefully to clinical-summary-only if all APIs
  are unavailable
- Intelligence appears as context, not interruption

---

## Summary: Revised Feature List with API Dependencies

Every feature in the development guide now has an API dependency map:

| Feature | Tier 1 APIs | Tier 2 APIs | Tier 3 APIs |
|---------|-------------|-------------|-------------|
| F10 Medication Reference | RxNorm, RxClass, OpenFDA Labels, OpenFDA FAERS | — | MedlinePlus |
| F10c Pregnancy/Renal Filter | OpenFDA Labels | — | — |
| F11 Lab Tracker | LOINC | — | — |
| F11d Lab Panel Grouping | LOINC | — | — |
| F15 Care Gap Tracker | ICD-10 API | HealthFinder, CDC CVX | — |
| F15a Auto-Population | ICD-10, LOINC | HealthFinder | — |
| F16 Billing Capture | ICD-10 | HCPCS/CMS data | — |
| F17 Coding Suggester | ICD-10, UMLS | — | — |
| F17b Specificity Reminder | ICD-10 | — | — |
| F17c Code Pairing | ICD-10, UMLS | — | — |
| F22 Morning Briefing | OpenFDA Recalls | HealthFinder | Open-Meteo |
| F26 PA Generator | RxNorm, RxClass, OpenFDA Labels | — | — |
| F31 Note Reformatter | RxNorm, ICD-10, UMLS, LOINC | — | — |
| NEW: Drug Recall System | OpenFDA Recalls | — | — |
| NEW: Interaction Checker | RxNorm, OpenFDA Labels | — | — |
| NEW: Lab Interpretation | LOINC, OpenFDA Labels, RxNorm | — | — |
| NEW: Formulary Gap | RxNorm, RxClass, ICD-10 | — | — |
| NEW: Guideline Lookup | — | — | PubMed |
| NEW: Patient Ed Draft | ICD-10, RxNorm | — | MedlinePlus |
| NEW: Differential Widget | ICD-10, UMLS | NLM Conditions | — |

---

*This document is the planning reference for the API Intelligence Layer.
All features described here extend the existing NP Companion development
plan without replacing or modifying any existing feature. Implementation
follows the same phase structure: Tier 1 APIs in Phase 2 (Data Layer),
Tier 2 in Phase 5 (Clinical Decision Support), new features in Phase 10
(Intelligence Layer, to be added after Phase 9).*

---

## ADDENDUM: Billing Intelligence Layer
## Feature: Proactive Billing Opportunity Engine
## Added to Phase 10 (Intelligence Layer)

---

### Overview and Purpose

This feature cross-references every patient's diagnoses, medications,
problem list, insurer information, scheduled visit type, and time-tracking
data against Medicare/Medicaid billing rules and reimbursement rates to
surface revenue opportunities that would otherwise be missed. The system
never submits anything — it flags, suggests, and generates documentation
prompts. All billing decisions remain with the provider.

The fundamental problem this solves: primary care practices on average
capture only 60% of billable services they actually deliver. The gap is
not fraud — it is documentation gaps, unfamiliarity with newer codes,
and not enough time to think about billing while also thinking about
patients. This system does the thinking ahead of time.

---

### The Two Primary Data Sources

#### Billing Source 1 — CMS Physician Fee Schedule REST API

CMS maintains an official public REST API for the Medicare Physician Fee
Schedule at pfs.data.cms.gov. This is a live queryable API, not
just a downloadable flat file, though flat files are also available.

**Base URL:** `https://pfs.data.cms.gov/api`
**Auth:** None required — fully public
**Format:** JSON
**Updated:** Annually (new year published ~November, effective January 1)

**Key query patterns:**

- `GET /api?hcpcs_code=[code]&year=2025` — Returns RVU components, payment
  indicators, and national payment amounts for a specific CPT/HCPCS code.

- `GET /api?hcpcs_code=[code]&locality_number=[locality]&year=2025` — Returns
  geographically adjusted payment amounts for a specific MAC locality.
  Virginia falls under MAC Jurisdiction M (Palmetto GBA). The locality
  number for the Richmond, VA area must be configured once in config.py.

**Fields returned per code:**
- `hcpcs_code` — The CPT or HCPCS code
- `hcpcs_description` — Official short description
- `work_rvu` — Physician work RVU
- `non_facility_pe_rvu` — Practice expense RVU (office setting)
- `facility_pe_rvu` — Practice expense RVU (hospital/facility setting)
- `mp_rvu` — Malpractice RVU
- `total_rvu_non_facility` — Sum used for payment calculation
- `non_facility_pricing_amount` — National average payment (office setting)
- `facility_pricing_amount` — National average payment (facility setting)
- `global_surgery` — Global surgery indicator
- `multiple_procedure` — Multiple procedure reduction rules
- `status_code` — Whether code is payable under PFS

**Payment formula** (for reference in config and calculations):
```
Non-Facility Payment =
  (Work RVU × Work GPCI) +
  (Non-Facility PE RVU × PE GPCI) +
  (MP RVU × MP GPCI)
  × Conversion Factor

CY 2025 Conversion Factor: $32.05 (non-APM) or $33.57 (qualifying APM)
CY 2026 Conversion Factor: $33.40 (non-APM) or $33.57 (qualifying APM)
```

Store the locality-adjusted payment amounts in the billing reference
database. Refresh annually each November when CMS publishes the new
rule. Display estimates labeled as "national average" with a note that
actual reimbursement varies by locality, payer contract, and claim
adjudication.

**Downloadable flat files (supplementary):**
CMS publishes PFALLyyA.ZIP containing facility and non-facility fee
schedule amounts for all services, and RVUyyA.ZIP containing relative
value units and payment policy indicators for all procedure codes.
These flat files are the definitive source for bulk loading the local
billing reference database. Download annually, parse into SQLite.

---

#### Billing Source 2 — CMS data.cms.gov Open API

**Base URL:** `https://data.cms.gov/api/1/`
**Auth:** None required — fully public
**Format:** JSON via Socrata Open Data API

This API exposes dozens of CMS datasets including:
- Medicare utilization and payment data by procedure and provider
- Part B prescriber data
- Provider enrollment data (NPI lookup)
- Quality Payment Program participation data

**Key dataset for billing intelligence:**
`Medicare Physician & Other Practitioners — by Provider and Service`
This dataset shows what Medicare actually paid (not just the fee schedule)
for each CPT code, by provider specialty and geography. Use this to
calibrate expected payment amounts by specialty (family practice) and
state (Virginia) rather than using national averages.

---

### The Billing Rules Knowledge Base

CMS publishes billing rules as policy documents, MLN articles, and the
annual Physician Fee Schedule Final Rule. These cannot be queried via API —
they are read once, encoded as rules in the application, and updated
annually when CMS publishes the new rule. The billing rules below are
confirmed current for CY 2025-2026.

#### Rule Category 1 — Chronic Care Management (CCM)

**Eligibility logic:**
A patient qualifies for CCM if they have two or more chronic conditions
expected to last 12+ months that place them at risk of acute exacerbation,
functional decline, or death. The chronic conditions from the patient's
problem list (ICD-10 codes from the Clinical Summary XML) determine
eligibility.

**Detection logic:**
Cross-reference the patient's active problem list against a curated list
of chronic condition ICD-10 prefixes. Two or more matches = CCM eligible.
Chronic conditions relevant to primary care include but are not limited to:
hypertension (I10-I16), type 2 diabetes (E11), CKD (N18), heart failure
(I50), COPD (J44), depression (F32-F33), hyperlipidemia (E78), obesity
(E66), atrial fibrillation (I48), coronary artery disease (I25).

**Billable codes and 2025 CMS national average rates:**
- 99490: First 20 minutes non-complex CCM by clinical staff — $60.49/month
- 99439: Each additional 20 minutes non-complex CCM — $45.93/month
- 99491: First 30 minutes CCM provided personally by NP/MD — varies
- 99437: Each additional 30 minutes personally by NP/MD — $57.58/month
- 99487: First 60 minutes complex CCM — higher rate
- 99489: Each additional 30 minutes complex CCM

**2025 APCM — new program:**
CMS launched the Advanced Primary Care Management (APCM) program in
January 2025. APCM codes are not time-banded and combine elements of
CCM, TCM, and RPM services. APCM has three billing levels based
on patient complexity and risk factors. This is an alternative to CCM
that may be more appropriate for complex patients.

**Monthly tracking logic:**
The visit timer (F12) and face-to-face timer already accumulate time per
patient per month. For CCM-eligible patients, accumulate ALL non-face-to-face
contact time monthly: phone calls, portal messages, care coordination.
When the monthly total crosses 20 minutes, flag as 99490 eligible. When
it crosses 40 minutes, flag for 99439 add-on. Alert the provider at the
end of the month before the billing window closes.

**Documentation requirement trigger:**
CCM requires a comprehensive care plan. Flag that the care plan must be
documented, revisited, and that a copy must be given to the patient.
Generate a documentation prompt: "Patient has accrued [N] minutes CCM
this month. To bill 99490: document care plan in chart, confirm patient
consent on file, record all time spent."

---

#### Rule Category 2 — Annual Wellness Visit (AWV) + Add-Ons

**AWV sequence logic:**
Three distinct HCPCS codes define the AWV sequence:
G0402: Initial Preventive Physical Exam ("Welcome to Medicare") — must
be within 12 months of Medicare Part B enrollment, one time only.
G0438: Initial Annual Wellness Visit — first AWV after G0402 (or if
G0402 was never done, the first AWV).
G0439: Subsequent Annual Wellness Visit — all AWVs after G0438,
billable no more than once every 12 months.

**Detection logic:**
Check the patient's Health Maintenance section in the Clinical Summary XML
for prior AWV dates. Determine which code applies:
- No AWV in history AND Medicare enrolled <12 months → G0402 eligible
- No AWV in history AND Medicare enrolled >12 months → G0438 eligible
- Prior AWV on file AND >12 months since last AWV → G0439 eligible
- Prior AWV on file AND <12 months since last AWV → NOT yet eligible

Surface this as a scheduling opportunity: "Patient is due for [G0438/G0439]
Annual Wellness Visit. Last AWV: [date] or never documented."

**2025 AWV Add-on opportunities (same-day billing stack):**

G2211: Office visit complexity add-on (~$16 national average). As of
2025, can be billed alongside AWV codes G0438 and G0439. Adds ~$16-16
per AWV visit. Requires documentation of longitudinal care relationship
and complex/serious condition management.

Additional same-day add-on codes:
- G0444: Annual depression screening (15 min) — NOT billable with G0438,
  only with G0439 (subsequent AWV). Flag this common error proactively.
- G0442: Annual alcohol misuse screening — must be billed with G0443
  (counseling) to be valid. Both or neither.
- G0443: Alcohol counseling (15 min) — requires G0442 same day
- 99497: Advance Care Planning (first 16-30 min) — billable with AWV,
  co-pay waived with modifier -33. Requires face-to-face discussion.
- 99498: Advance Care Planning add-on (each additional 30 min)
- G0136: SDOH Risk Assessment (5-15 min) — social determinants screening,
  new in 2025 Final Rule
- G0477/G0473: Obesity counseling — eligible when BMI ≥30 documented

**AWV opportunity flag logic:**
When an AWV is on tomorrow's schedule (from the NetPractice scraper),
NP Companion pre-calculates the full billing opportunity stack:
1. Which AWV code applies (G0402/G0438/G0439)?
2. Is G2211 appropriate (does the patient have a complex/serious condition)?
3. Is the patient due for depression screening → G0444 (if subsequent AWV)?
4. Is the patient due for ACP discussion → 99497?
5. Does the patient have SDOH risk factors → G0136?
6. Is BMI ≥30 documented → obesity counseling opportunity?
7. Is alcohol screening due → G0442/G0443 pair?

Display as an AWV Billing Stack card in the pre-visit note:
"Today's AWV billing stack: G0439 + G2211 + G0444 + 99497 = ~$[total]"

**Estimated revenue calculation:**
Sum the national average payment rates from the PFS API for each code
in the stack. Display as: "Estimated reimbursement if all documented:
$[sum] (national average, actual varies by insurer)."

---

#### Rule Category 3 — Evaluation & Management (E&M) Complexity Add-On

G2211 can be billed alongside any office visit (99202-99215) when the
provider serves as the primary focal point of care for a serious or complex
condition, recognizing the longitudinal nature of the provider-patient
relationship. National average reimbursement is approximately $16.

**Detection logic:**
G2211 is appropriate when:
- Patient has one or more serious/complex chronic conditions in the problem list
- The provider is the patient's primary care provider (confirmed by
  practice enrollment, not from any external source)
- The visit involves managing or monitoring those conditions

**Flag logic:**
For every established patient visit (99212-99215), flag G2211 as a
potential add-on. Display a one-line reminder in the billing capture
section: "Consider G2211 (+~$16) — patient has [condition]. Document
longitudinal care relationship."

The G2211 flag should appear only for established patient codes, not
new patient codes (99202-99205). This distinction is handled by checking
whether a prior encounter exists in the patient's Clinical Summary XML.

---

#### Rule Category 4 — Transitional Care Management (TCM)

**What it is:** Billing for care coordination services within 30 days after
a hospital discharge, ED visit, or observation stay.

**Detection logic:**
Monitor the inbox (via the inbox monitor, F5) for hospital discharge
notifications. When a discharge summary or hospital chart appears in the
inbox for a patient:
- Flag immediately: "Possible TCM opportunity — patient may have been
  discharged from inpatient/observation"
- Calculate the billing window: TCM must be initiated within 2 business days
  (interactive contact by phone/portal/in-person) of discharge

**Billable codes:**
- 99495: Moderate medical decision complexity — contact within 2 business days,
  face-to-face within 14 days of discharge — ~$167 national average
- 99496: High medical decision complexity — contact within 2 business days,
  face-to-face within 7 days of discharge — ~$231 national average

**Urgency logic:**
TCM has a hard deadline. Unlike CCM which accumulates monthly, TCM
requires action within 2 business days of discharge. This warrants a
priority push notification rather than a morning briefing mention:
"TCM OPPORTUNITY: [patient identifier] — discharge detected. Contact
required within 2 business days to preserve TCM billing eligibility.
Deadline: [calculated date]."

---

#### Rule Category 5 — Prolonged Service Time Add-On (99417)

Already partially documented in F16c. Full specification here:

**99417:** Prolonged office visit — each 15-minute increment beyond the
maximum time for the base E&M level.

**Time thresholds for add-on eligibility (2023 AMA guidelines):**
- 99214 (moderate complexity): max time 39 min → 99417 applies at 40+
- 99215 (high complexity): max time 54 min → 99417 applies at 55+

**Logic:** Face-to-face timer (F12) + chart time (F6 MRN reader) together
produce total encounter time. When total exceeds the threshold for the
selected E&M level by 15+ minutes, flag 99417 automatically in the
billing audit log entry.

---

#### Rule Category 6 — Behavioral Health Integration (BHI)

**What it is:** Monthly billing for integrating behavioral health into
primary care for patients with recognized behavioral health conditions.

**Eligibility logic:**
Patient has a behavioral health diagnosis in the problem list. In primary
care, this commonly includes: depression (F32-F33), anxiety (F41), ADHD
(F90), substance use (F10-F19), PTSD (F43.1), adjustment disorder (F43.2).

**Billable code:**
- 99484: General BHI, 20+ minutes per month of care management activities
  by clinical staff — ~$50 national average

**Logic:** BHI is often overlooked by primary care practices even when
actively managing behavioral health conditions. Detection: patient has
qualifying diagnosis AND provider is managing (medication in med list OR
repeated encounters for behavioral health). Flag monthly if time threshold
could be met.

---

#### Rule Category 7 — Remote Patient Monitoring (RPM)

**What it is:** Billing for monitoring physiologic data from devices
(blood pressure monitors, glucometers, pulse oximeters, weight scales)
between office visits.

**Billable codes:**
- 99453: Patient setup and education for RPM device — one time
- 99454: Device supply with transmission of data — per 30-day period
- 99457: First 20 minutes of RPM monitoring and management per month
- 99458: Each additional 20 minutes per month

**Eligibility trigger:** Patient has a condition benefiting from continuous
monitoring — hypertension, diabetes, heart failure, COPD, obesity.
Cross-reference problem list ICD-10 codes.

**Note:** RPM requires the practice to have a device program. Flag this
as a "program opportunity" rather than a per-patient billing flag —
it requires practice-level infrastructure first.

---

### The Insurer Intelligence Layer

The billing opportunity calculations above are Medicare-specific. The
insurer intelligence layer adjusts them based on the patient's actual
coverage, which comes from the Clinical Summary XML demographics section.

#### Insurer Detection from Clinical Summary XML

The XML's `patientRole` section includes insurance information. Parse:
- Payer name (e.g., "HEALTHKEEPERS" as observed in AC screenshots)
- Plan type (HMO, PPO, fee-for-service)
- Medicare vs. Medicaid vs. commercial

**Payer classification logic:**
```
If payer name contains "MEDICARE" or "HICN" → Medicare FFS rules apply
If payer name contains "MEDICAID" or "MEDALLION" → Virginia Medicaid
If payer name matches known commercial carriers → commercial rules
If payer name contains "HEALTHKEEPERS" → Anthem HealthKeepers (Medicaid
  managed care in Virginia — different from commercial Anthem)
```

Store a payer classification table in the billing reference database.
The provider and admin can update classifications via the config UI (F1i).

#### Medicare vs. Medicaid vs. Commercial Logic Branching

**Medicare (Traditional Fee-for-Service):**
Full CCM, AWV, G2211, TCM, BHI, RPM billing rules apply.
PFS API payment rates are the expected reimbursement.
Apply GPCI adjustment for Virginia locality.

**Medicare Advantage (MA) Plans:**
MA plans cover the same Medicare benefits but may have different
prior authorization requirements and may pay differently than traditional
Medicare. The billing codes are the same; the payment rates may vary.
Flag opportunity but add caveat: "Verify prior authorization requirements
with [plan name] for this service."

**Medicaid (Virginia Medallion/FAMIS):**
Virginia Medicaid covers many of the same services but with different
billing codes and rates. CMS publishes a Medicaid State Plan and the
Virginia DMAS (Department of Medical Assistance Services) publishes the
Virginia Medicaid fee schedule.

Key Virginia Medicaid differences from Medicare:
- CCM is not always covered identically — some MA-managed Medicaid plans
  have different requirements
- AWV equivalent services exist under different code sets
- Behavioral health integration has strong Medicaid support
- Always require prior authorization for non-preventive specialty referrals

**Commercial Insurance (HEALTHKEEPERS, Anthem, Cigna, etc.):**
Commercial payers do not follow PFS rates. They negotiate rates
individually with practices. However:
- Many commercial plans use Medicare FFS as a rate baseline
  (paying 110-140% of Medicare for most services)
- CCM and care management are increasingly covered by commercial plans
- AWV equivalents (99381-99397 for under-65) are covered by commercial
  but with different codes than Medicare AWV codes
- G2211 add-on is NOT covered by all commercial plans

**Commercial logic:** Flag the opportunity with the caveat "verify
coverage with [payer] — commercial reimbursement varies. This service
is covered by Medicare at [rate]."

---

### The Billing Opportunity Engine — Workflow

#### Pre-Visit Opportunity Detection (Runs Overnight with Note Prep)

For each patient on tomorrow's schedule:

```
1. Determine insurer type from patient XML demographics
2. Load patient's active diagnoses (ICD-10 from XML problem list)
3. Load patient's medications (RxNorm-normalized from XML)
4. Load prior billing history (from NP Companion billing audit log)
5. Load visit type (from NetPractice schedule scraper)
6. Load prior AWV/IPPE/CCM dates (from XML Health Maintenance section)
7. Run all rule categories against this patient data:

   FOR EACH rule category (CCM, AWV, TCM, G2211, 99417, BHI, RPM):
     a. Check eligibility criteria against patient data
     b. Check whether this has been billed recently (audit log)
     c. Check whether documentation requirements can be anticipated
     d. Calculate estimated revenue (PFS API rate × payer factor)
     e. If opportunity: create BillingOpportunity record with:
        - opportunity_type (CCM/AWV/TCM/etc.)
        - applicable_codes (list of codes)
        - estimated_revenue (national avg, payer-adjusted if known)
        - eligibility_basis (why this patient qualifies)
        - documentation_required (what must be in the note)
        - confidence_level (HIGH/MEDIUM/LOW)
        - insurer_caveat (if non-Medicare)

8. Sort opportunities by estimated_revenue descending
9. Store all opportunities in BillingOpportunity table
10. Link to the scheduled visit in the Today View
```

#### Display in Today View (Pre-Visit)

For each patient in the Today View, a collapsible billing card appears
below the care gap section:

```
BILLING OPPORTUNITIES — [Visit Type] with [Patient ID last-4]
Insurer: HEALTHKEEPERS (Medicaid Managed Care)
────────────────────────────────────────────────────────
HIGH CONFIDENCE
  💰 CCM: 99490 — Patient has 4 chronic conditions (HTN, DM2,
     Hyperlipidemia, CKD). Eligible for monthly CCM billing.
     Est. ~$60/month if enrolled. Requires: patient consent,
     care plan, 20 min/month non-face-to-face time.
     [Start CCM Enrollment] [Dismiss — Already enrolled elsewhere]

  💰 G2211: Add-on to today's E&M (~$16) — Patient has DM2 +
     CKD, complex chronic condition. Document longitudinal
     relationship in Assessment.
     [Add to Note Checklist] [Dismiss]

MEDIUM CONFIDENCE
  💰 AWV: G0439 due — Last AWV: 14 months ago. Patient is
     due for Subsequent Annual Wellness Visit.
     Est. ~$133 (G0439 + G2211). Consider scheduling if not
     today's visit type.
     [Flag for Scheduling] [Dismiss]

  ⚠ Verify with HEALTHKEEPERS before billing CCM —
    Medicaid managed care prior auth requirements vary.
────────────────────────────────────────────────────────
Estimated opportunity if all documented today: ~$76
[View Full Billing Details] [Add All to Note Checklist]
```

The "Add All to Note Checklist" button injects the documentation
requirements for each opportunity into the Prepped Note's Assessment/Plan
section as a checklist. This gives the provider a prompt during charting:
"Document G2211: note longitudinal care relationship for [condition]."

#### Display in Post-Visit Billing Review (End of Day)

After the visit, the billing capture section of the Timer/Billing module
shows which opportunities were acted on vs. missed:

```
VISIT BILLING REVIEW — [Date] — [Patient ID]
E&M Level Selected: 99214
────────────────────────────────────────────────────────
BILLED TODAY:
  ✅ 99214 — Office visit, moderate complexity — ~$114
  ✅ G2211 — Complexity add-on — ~$16
  Total: ~$130

OPPORTUNITIES NOT YET CAPTURED:
  ⚪ 99490 (CCM) — Eligible but not enrolled. Still available
     this month if enrolled before month end.
     [Enroll Patient in CCM] [Dismiss — Patient declined]

  ⚪ G0439 (AWV) — Patient is overdue. Consider scheduling
     dedicated AWV appointment.
     [Create Scheduling Note] [Dismiss]
────────────────────────────────────────────────────────
Revenue captured today: ~$130
Revenue available if all opportunities addressed: ~$203
Opportunity gap: ~$73
```

The "opportunity gap" display is motivating without being coercive.
It frames missed billing as a quality-and-revenue alignment issue,
not a performance pressure. Cumulative opportunity gap data feeds the
Metrics dashboard (F13) and monthly billing summary (F14c).

---

### Scheduling Intelligence (New Sub-Feature)

The billing engine generates not just same-visit opportunities but
also scheduling recommendations — types of appointments worth creating
specifically to capture revenue.

**Scheduling opportunity types:**

1. **AWV Due** — Patient is 12+ months past last AWV.
   Opportunity: Schedule 45-60 min dedicated AWV slot.
   Revenue estimate: G0439 + G2211 + possible add-ons = $133-200+

2. **CCM Consent Visit Required** — New CCM candidates need an
   initiating face-to-face visit (AWV, IPPE, or comprehensive E&M)
   before CCM billing can begin.
   Medicare requires an initiating visit (AWV, IPPE, or comprehensive E&M)
   before CCM services can start for new patients or those not seen within
   the previous year.
   Opportunity: Schedule initiating visit to start CCM program.

3. **Prolonged Visit Anticipated** — Patient with complex problem list
   (4+ active chronic conditions) scheduled for a standard 20-min follow-up.
   Flag: "This patient typically requires extended time. Consider
   booking a 40-60 min complex visit to support 99215 level billing."

4. **TCM Window Active** — Hospital discharge detected in inbox.
   Opportunity: Schedule 7-day follow-up for 99496 (high complexity)
   or 14-day for 99495. Revenue: $167-231.
   Urgency: Schedule before the window closes.

5. **Behavioral Health Integration Visit** — Patient with behavioral
   health diagnosis and 20+ min BHI accrued this month.
   Opportunity: Dedicated BHI check-in (can be phone/telehealth).

**Scheduling recommendation display:**
A new section in the Today View header: "Scheduling Opportunities"
with a count badge. Opens to a list of patients with pending scheduling
needs sorted by urgency (TCM window closing soonest → highest priority)
and revenue opportunity.

---

### The BillingOpportunity Database Schema

Add to Phase 2 database models (models/billing.py):

```
BillingOpportunity:
  id
  user_id (FK to User)
  patient_mrn_hash (sha256 of MRN — never store plain MRN)
  visit_date (date the scheduled visit occurs)
  opportunity_type (enum: CCM/AWV/TCM/G2211/99417/BHI/RPM/APCM/SCHEDULING)
  applicable_codes (JSON array of HCPCS/CPT codes)
  estimated_revenue_national (float — from PFS API)
  estimated_revenue_adjusted (float — payer-adjusted estimate)
  insurer_type (enum: MEDICARE_FFS/MEDICARE_ADVANTAGE/MEDICAID/COMMERCIAL)
  insurer_name (string — from patient XML)
  eligibility_basis (text — why patient qualifies, clinical criteria met)
  documentation_required (text — what must be in the note)
  confidence_level (enum: HIGH/MEDIUM/LOW)
  insurer_caveat (text — non-Medicare warnings)
  status (enum: PENDING/ACTED_ON/DISMISSED/EXPIRED)
  dismissed_reason (text)
  dismissed_by_user_id (FK to User)
  created_at
  acted_on_at
  revenue_captured (float — what was actually billed if known)

BillingRuleCache:
  id
  code (HCPCS/CPT)
  short_description
  work_rvu
  non_facility_payment_national (float)
  facility_payment_national (float)
  conversion_factor_year (integer)
  locality_number (string — Virginia MAC locality)
  locality_adjusted_payment (float)
  last_updated
  source (enum: PFS_API/FLAT_FILE)
```

---

### Per-Provider Customization for Billing Intelligence

**From `/settings/billing` (provider-accessible):**

- `billing_insurer_type_default`: What insurer type to assume if XML
  doesn't clearly identify the payer (default: MEDICARE_FFS for
  practices with high Medicare volume)

- `ccm_opportunity_threshold_minutes`: How many chronic conditions are
  required before CCM is flagged (default: 2, per CMS minimum; some
  providers prefer to flag only at 3+ for more certain eligibility)

- `show_scheduling_opportunities`: boolean — whether scheduling
  recommendations appear in Today View

- `opportunity_minimum_confidence`: enum — only show HIGH confidence
  opportunities, or include MEDIUM (default: both)

- `revenue_display_mode`: show estimated dollar amounts vs. show
  only code names (some providers prefer not to see dollar amounts
  during clinical work — configure to show in post-visit review only)

- `tcm_alert_priority`: push notification priority for TCM window
  opening (default: HIGH — time-sensitive)

- `dismissed_opportunity_persistence_days`: how long dismissed
  opportunities are remembered before the system re-flags them
  (default: 90 days for AWV, 30 days for CCM, 7 days for TCM)

**From `/admin/billing` (admin-accessible):**

- `pfs_locality_number`: Virginia MAC locality code for GPCI
  adjustment (set once during setup, updated annually if locality
  changes)

- `commercial_payer_rate_factor`: multiplier applied to Medicare
  national average rates for commercial payer estimates (default: 1.2
  meaning 120% of Medicare — a reasonable approximation; actual rates
  are negotiated and not publicly available)

- `medicaid_rate_factor`: same concept for Medicaid estimates
  (Virginia Medicaid rates are published by DMAS; enter manually or
  use default of 0.75 meaning 75% of Medicare national average)

- `pfs_auto_refresh_month`: which month to trigger the annual PFS data
  refresh (default: November — when CMS publishes the new rule)

---

### Attribution and Compliance Notes

**For the Copilot planner — important compliance framing:**

Every billing opportunity surface must include:
1. The word "estimate" or "approximate" before any dollar figure
2. The caveat that actual reimbursement depends on payer contract,
   claim adjudication, and documentation quality
3. No billing suggestions that require upfront patient consent
   (CCM, APCM) should show as billable until consent is documented
4. The system must never suggest billing for services not rendered
   or not documented — every flag is tied to documented clinical criteria

The system's legal framing: NP Companion is a documentation and
workflow optimization tool. It surfaces billing opportunities based
on clinical data the provider has already documented (diagnoses,
time, medications). It does not generate billing codes — it suggests
them for the provider's consideration and review. All billing
decisions are made by the licensed provider.

Add to the attribution statement (required by CMS for software using
their data): "This product uses publicly available data from the U.S.
Centers for Medicare & Medicaid Services. Payment information is
provided for informational purposes and does not constitute a guarantee
of Medicare reimbursement."

---

### Summary: Billing Intelligence API Dependencies

| Component | Data Source | Access Method | Update Frequency |
|-----------|-------------|---------------|-----------------|
| RVU / payment rates | CMS PFS API (pfs.data.cms.gov) | REST API + flat file | Annual (November) |
| Locality GPCI | CMS PFS API locality endpoint | REST API | Annual |
| Actual Medicare payments | data.cms.gov utilization dataset | REST API | Annual |
| CCM billing rules | CMS MLN publications | Hard-coded rules | Annual review |
| AWV billing rules | CMS MLN publications | Hard-coded rules | Annual review |
| TCM billing rules | CMS MLN publications | Hard-coded rules | Annual review |
| Insurer type detection | Patient Clinical Summary XML | Import-time parse | Per patient import |
| Virginia Medicaid rates | DMAS fee schedule | Manual entry / annual download | Annual |
| Commercial rate estimates | Practice contract (unavailable publicly) | Configurable multiplier | Provider updates |

**The single most important implementation note for the planner:**
The billing rules (CCM eligibility, AWV sequence logic, G2211 criteria,
TCM window timing) are NOT driven by any API — they are encoded as
application logic based on CMS policy documents. These rules must be
reviewed and potentially updated every November when CMS publishes the
new Physician Fee Schedule Final Rule. Build an annual review reminder
into the system: every November 1, the admin receives a notification:
"CMS typically publishes the new Physician Fee Schedule Final Rule
this month. Review and update billing rules in /admin/billing by
January 1."

The billing rule update process is a human task, not an automated one.
The system cannot self-update billing rules — CMS policy requires
human interpretation. This is by design and is a compliance feature,
not a limitation.

---

*Billing Intelligence Layer added 3/17/2026. This section extends Phase 10
(Intelligence Layer) with a new sub-phase: Phase 10B — Billing Intelligence.
Dependencies: Phase 4 (Monitoring/Tracking, F12 face-to-face timer),
Phase 5 (Clinical Decision Support, F15 care gaps), Phase 2 (Data Layer,
Clinical Summary XML import). Phase 10B can be built concurrently with
Phase 10A (other intelligence features) once Phase 4 and 5 are complete.*

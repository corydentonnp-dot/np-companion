"""
CareCompanion — Centralized API Configuration
File: app/api_config.py

Single source of truth for every external API used by CareCompanion.
All base URLs, cache TTLs, rate limits, billing constants, and CMS
reimbursement values live here. No other file should hardcode these values.

Dependencies: None (no imports required — pure configuration)

CareCompanion features that depend on this file:
- app/services/api/*.py (all API service modules)
- app/services/billing_rules.py (billing rule engine)
- app/services/api_scheduler.py (background job timing)
- agent/scheduler.py (via api_scheduler imports)
"""

# ===========================================================================
# TIER 1 — Core Clinical Vocabulary APIs (no auth required)
# ===========================================================================

# RxNorm — drug name normalization and pharmacological relationships
RXNORM_BASE_URL = "https://rxnav.nlm.nih.gov/REST"
RXNORM_CACHE_TTL_DAYS = 30          # RxCUI for drug names is very stable
RXNORM_PROPERTIES_TTL_DAYS = 30     # Drug class, ingredient, formulation
RXNORM_NDC_TTL_DAYS = 7            # NDC packaging changes more frequently
RXNORM_RATE_LIMIT_PER_SEC = 20      # Soft limit; no hard enforcement

# RxClass — drug-to-therapeutic-class mappings
RXCLASS_BASE_URL = "https://rxnav.nlm.nih.gov/REST/rxclass"
RXCLASS_CACHE_TTL_DAYS = 90         # Drug-class mappings are very stable

# OpenFDA Drug Label — FDA-approved prescribing information
OPENFDA_LABEL_BASE_URL = "https://api.fda.gov/drug/label.json"
OPENFDA_LABEL_CACHE_TTL_DAYS = 30   # Labels updated infrequently
OPENFDA_RATE_LIMIT_PER_MIN = 240    # Without key; 1000/min with free key

# OpenFDA Drug Adverse Events — FAERS real-world adverse event reports
OPENFDA_EVENTS_BASE_URL = "https://api.fda.gov/drug/event.json"
OPENFDA_EVENTS_CACHE_TTL_DAYS = 7   # Real-world reports update frequently

# OpenFDA Drug Recalls — active enforcement actions
OPENFDA_RECALLS_BASE_URL = "https://api.fda.gov/drug/enforcement.json"
OPENFDA_RECALLS_CACHE_TTL_DAYS = 1  # Check daily — recalls are urgent

# ICD-10 Clinical Tables — NLM ICD-10-CM code search (no auth required)
ICD10_BASE_URL = "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search"
ICD10_CACHE_TTL_DAYS = 365          # Annual update Oct 1 — rebuild cache yearly

# NLM Conditions — clinical condition search for differential diagnosis (no auth)
NLM_CONDITIONS_BASE_URL = "https://clinicaltables.nlm.nih.gov/api/conditions/v3/search"
NLM_CONDITIONS_CACHE_TTL_DAYS = 90  # Condition data is stable

# LOINC — lab test identification and reference ranges (free account required)
LOINC_BASE_URL = "https://fhir.loinc.org"
LOINC_CACHE_TTL_DAYS = 180          # LOINC codes are very stable

# UMLS — medical ontology crosswalk (free account + API key required)
# Status: ✅ License approved 2026-03-19 — enables UMLS, SNOMED CT, VSAC access
UMLS_BASE_URL = "https://uts.nlm.nih.gov/uts/rest"
UMLS_CACHE_TTL_DAYS = 30            # Terminology updates are periodic

# SNOMED CT — accessed via UMLS atoms endpoint (sabs=SNOMEDCT_US)
# No separate auth — uses same UMLS API key
SNOMED_SEARCH_SAB = "SNOMEDCT_US"   # UMLS source abbreviation for US SNOMED CT

# VSAC — Value Set Authority Center (FHIR R4)
# Provides eCQM value sets, C-CDA value sets, and clinical quality measure definitions
# Auth: same UMLS API key (passed as Bearer token)
VSAC_BASE_URL = "https://cts.nlm.nih.gov/fhir"
VSAC_CACHE_TTL_DAYS = 90            # Value sets update infrequently

# DailyMed — FDA-approved drug labeling and medication guides (no auth)
DAILYMED_BASE_URL = "https://dailymed.nlm.nih.gov/dailymed/services/v2"
DAILYMED_CACHE_TTL_DAYS = 30        # Label data is stable

# NPPES NPI Registry — provider lookup and validation (no auth)
NPPES_BASE_URL = "https://npiregistry.cms.hhs.gov/api"
NPPES_CACHE_TTL_DAYS = 7            # Provider data can change (address, status)

# ClinicalTrials.gov v2 — clinical trial search (no auth)
CLINICAL_TRIALS_BASE_URL = "https://clinicaltrials.gov/api/v2"
CLINICAL_TRIALS_CACHE_TTL_DAYS = 1  # Recruiting status changes frequently

# RxTerms — structured drug terminology via RxNav (shares RxNorm infra)
RXTERMS_BASE_URL = "https://rxnav.nlm.nih.gov/REST/RxTerms"
RXTERMS_CACHE_TTL_DAYS = 30         # Drug terminology is stable

# ===========================================================================
# TIER 2 — Clinical Decision Support APIs
# ===========================================================================

# AHRQ HealthFinder — USPSTF preventive care recommendations (no auth)
HEALTHFINDER_BASE_URL = "https://health.gov/myhealthfinder/api/v3"
HEALTHFINDER_CACHE_TTL_DAYS = 30    # USPSTF guidelines update periodically

# CDC Immunization data via RxNorm CVX codes (supplementary)
CDC_IMMUNIZATION_CACHE_TTL_DAYS = 30

# CMS Physician Fee Schedule REST API (no auth required — public)
CMS_PFS_BASE_URL = "https://pfs.data.cms.gov/api"
CMS_PFS_CACHE_TTL_DAYS = 365        # Annual update each November/January

# CMS open data API (Socrata) — utilization and payment data
CMS_DATA_BASE_URL = "https://data.cms.gov/api/1"
CMS_DATA_CACHE_TTL_DAYS = 90        # Quarterly publication cycle

# ===========================================================================
# TIER 3 — Literature and Education APIs
# ===========================================================================

# NCBI PubMed — biomedical literature (free key recommended for rate limits)
PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_CACHE_TTL_DAYS = 30          # Stale flag after 90 days; hard refresh at 30
PUBMED_MAX_RESULTS = 5              # Top 5 guideline articles per diagnosis
PUBMED_LOOKBACK_YEARS = 3           # How many years back to search

# NLM MedlinePlus Connect — patient-facing health education (no auth)
MEDLINEPLUS_BASE_URL = "https://connect.medlineplus.gov/service"
MEDLINEPLUS_CACHE_TTL_DAYS = 30     # Patient education content is stable

# ===========================================================================
# TIER 4 — Weather API
# ===========================================================================

# Open-Meteo — free weather API (no auth, no key required)
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1"
OPEN_METEO_CACHE_TTL_HOURS = 1      # Fetch fresh every hour for briefing
OPEN_METEO_RATE_LIMIT_PER_DAY = 10000  # Free tier limit

# ===========================================================================
# TIER 6 — Premium Clinical Reference APIs (license-gated, optional)
# ===========================================================================

# UpToDate Content API — premium clinical decision support (license required)
# If no key, MonitoringRuleEngine waterfall step 5 skips silently.
UPTODATE_BASE_URL = "https://api.uptodate.com/rest/v1"
UPTODATE_CACHE_TTL_DAYS = 30        # Clinical content is stable

# ===========================================================================
# TIER 5 — Drug Pricing APIs
# ===========================================================================

# Cost Plus Drugs — Mark Cuban's transparent drug pricing (no auth)
# No API key required. No authentication. No rate limits. No .env entry needed.
COST_PLUS_BASE_URL = "https://us-central1-costplusdrugs-publicapi.cloudfunctions.net/main"
COST_PLUS_CACHE_TTL_DAYS = 3        # 72 hours — prices update periodically, not daily
COST_PLUS_DEFAULT_QUANTITY = 30     # Standard 30-day supply

# NADAC — National Average Drug Acquisition Cost (Tier 1b reference pricing)
# Free CMS data showing what pharmacies pay wholesalers. No auth required.
# Used as informational reference alongside the primary pricing tier — does NOT
# change badge color or primary price. Updates weekly from CMS.
NADAC_BASE_URL = "https://data.medicaid.gov/api/1/datastore/query"
NADAC_DATASET_ID = "a4y5-5ky8"      # NADAC (National Average Drug Acquisition Cost) — verify at data.medicaid.gov
NADAC_CACHE_TTL_DAYS = 7            # Weekly — matches CMS update cadence
NADAC_DEFAULT_QUANTITY = 30         # Standard 30-day supply

# GoodRx Price Compare API ONLY — /v2/price/compare and /v2/drug/search
# The Coupon API (/v2/coupon) is INTENTIONALLY EXCLUDED — requires 3,000 coupon
# accesses/month minimum which a single-provider practice cannot meet.
# ToS NO-AGGREGATION CONSTRAINT: GoodRx prices must NEVER appear alongside
# competing pricing data in the same UI component. The waterfall architecture
# satisfies this — GoodRx is only queried when Cost Plus returns no result,
# so they never co-exist in the same card.
GOODRX_BASE_URL = "https://api.goodrx.com"
GOODRX_CACHE_TTL_DAYS = 1           # 24 hours — GoodRx prices change frequently
GOODRX_DEFAULT_ZIP = "23832"         # Chesterfield, VA — practice location

# NeedyMeds — patient assistance program database (no auth)
# No API key required for either source. No credentials needed.
NEEDYMEDS_BASE_URL = "https://www.needymeds.org"
RXASSIST_BASE_URL = "https://www.rxassist.org"
DRUG_ASSISTANCE_CACHE_TTL_DAYS = 7  # Assistance programs change infrequently

# Drug pricing display thresholds (dollars/month)
# Below MEDIUM = green, MEDIUM–HIGH = yellow, above HIGH = red
DRUG_PRICE_ASSISTANCE_THRESHOLD = 75   # Triggers Tier 3 query
DRUG_PRICE_HIGH_INDICATOR = 100        # Red badge
DRUG_PRICE_MEDIUM_INDICATOR = 30       # Yellow badge

# Pricing cache refresh schedule
PRICING_CACHE_REFRESH_HOUR = 5
PRICING_CACHE_REFRESH_MINUTE = 30

# ===========================================================================
# HTTP CLIENT SETTINGS (shared by all API services)
# ===========================================================================

HTTP_TIMEOUT_SECONDS = 10           # Timeout per API request
HTTP_MAX_RETRIES = 3                # Retry attempts on transient errors
HTTP_RETRY_BACKOFF_SECONDS = 1.0    # Initial backoff; doubles each retry
HTTP_USER_AGENT = "CareCompanion/1.1.2 (clinical-workflow; non-commercial)"

# ===========================================================================
# API KEYS — loaded from config.py (not hardcoded here)
# ===========================================================================
# These are read at runtime. If config.py doesn't have them, empty defaults.
try:
    import config as _cfg
    OPENFDA_API_KEY = getattr(_cfg, 'OPENFDA_API_KEY', '')
    PUBMED_API_KEY = getattr(_cfg, 'PUBMED_API_KEY', '')
    LOINC_USERNAME = getattr(_cfg, 'LOINC_USERNAME', '')
    LOINC_PASSWORD = getattr(_cfg, 'LOINC_PASSWORD', '')
    UMLS_API_KEY = getattr(_cfg, 'UMLS_API_KEY', '')
    GOODRX_API_KEY = getattr(_cfg, 'GOODRX_API_KEY', '')
    GOODRX_SECRET_KEY = getattr(_cfg, 'GOODRX_SECRET_KEY', '')
    UPTODATE_API_KEY = getattr(_cfg, 'UPTODATE_API_KEY', '')
    DYNAMED_API_KEY = getattr(_cfg, 'DYNAMED_API_KEY', '')
except ImportError:
    OPENFDA_API_KEY = ''
    PUBMED_API_KEY = ''
    LOINC_USERNAME = ''
    LOINC_PASSWORD = ''
    UMLS_API_KEY = ''
    GOODRX_API_KEY = ''
    GOODRX_SECRET_KEY = ''
    UPTODATE_API_KEY = ''
    DYNAMED_API_KEY = ''

# ===========================================================================
# CMS BILLING CONSTANTS — Virginia MAC Jurisdiction M
# ===========================================================================
# These values are confirmed for CY 2025-2026. Update annually each November
# when CMS publishes the new Physician Fee Schedule Final Rule.
# Virginia falls under MAC Jurisdiction M (Palmetto GBA).
# ===========================================================================

# Geographic Practice Cost Indices (GPCI) locality for Virginia
# Jurisdiction M locality for Richmond, VA / Northern Virginia area
CMS_LOCALITY_NUMBER = "49"          # Virginia (non-MAWD) locality
CMS_MAC_JURISDICTION = "M"          # Palmetto GBA

# Conversion factors — multiply total RVU by this to get payment amount
CY2025_CONVERSION_FACTOR = 32.05    # Non-APM providers CY 2025
CY2025_CONVERSION_FACTOR_APM = 33.57  # Qualifying APM participants CY 2025
CY2026_CONVERSION_FACTOR = 33.40    # Non-APM providers CY 2026
CY2026_CONVERSION_FACTOR_APM = 33.57  # Qualifying APM participants CY 2026

# Current year to use for fee schedule lookups
CURRENT_FEE_SCHEDULE_YEAR = 2025

# ===========================================================================
# BILLING CODE CONSTANTS — National Average Rates (CY 2025 estimates)
# Rates are approximate national averages for non-facility (office) setting.
# Actual reimbursement varies by locality, payer contract, and adjudication.
# ===========================================================================

# Chronic Care Management (CCM) codes
CCM_CODES = {
    "99490": {"description": "CCM first 20 min, non-complex, clinical staff", "rate_est": 60.49},
    "99439": {"description": "CCM each add'l 20 min, non-complex", "rate_est": 45.93},
    "99491": {"description": "CCM first 30 min, personally by NP/MD", "rate_est": 84.78},
    "99437": {"description": "CCM each add'l 30 min, personally by NP/MD", "rate_est": 57.58},
    "99487": {"description": "Complex CCM first 60 min", "rate_est": 131.95},
    "99489": {"description": "Complex CCM each add'l 30 min", "rate_est": 69.12},
}

# Annual Wellness Visit (AWV) codes
AWV_CODES = {
    "G0402": {"description": "Initial Preventive Physical Exam (Welcome to Medicare)", "rate_est": 167.50},
    "G0438": {"description": "Initial Annual Wellness Visit", "rate_est": 175.84},
    "G0439": {"description": "Subsequent Annual Wellness Visit", "rate_est": 133.45},
}

# AWV same-day add-on codes (2025 approved stacking)
AWV_ADDON_CODES = {
    "G2211": {"description": "Office visit complexity add-on (longitudinal care)", "rate_est": 16.18},
    "G0444": {"description": "Annual depression screening 15 min (subsequent AWV only)", "rate_est": 26.41},
    "G0442": {"description": "Annual alcohol misuse screening (must bill with G0443)", "rate_est": 14.76},
    "G0443": {"description": "Alcohol counseling 15 min (must bill with G0442)", "rate_est": 27.32},
    "99497": {"description": "Advance Care Planning first 16-30 min", "rate_est": 87.13},
    "99498": {"description": "Advance Care Planning each add'l 30 min", "rate_est": 75.78},
    "G0136": {"description": "SDOH Risk Assessment 5-15 min (new 2025)", "rate_est": 18.42},
}

# Transitional Care Management (TCM) codes
TCM_CODES = {
    "99495": {"description": "TCM moderate complexity — contact in 2 biz days, F2F in 14 days", "rate_est": 167.04},
    "99496": {"description": "TCM high complexity — contact in 2 biz days, F2F in 7 days", "rate_est": 231.68},
}

# E&M add-on codes
EM_ADDON_CODES = {
    "G2211": {"description": "Complexity add-on for established patients with serious/complex conditions", "rate_est": 16.18},
    "99417": {"description": "Prolonged service each 15 min beyond E&M maximum time", "rate_est": 40.10},
}

# Prolonged service time thresholds (minutes) — triggers 99417 eligibility
# Based on 2023 AMA E&M guidelines
PROLONGED_SERVICE_THRESHOLDS = {
    "99214": 40,    # 99214 max time 39 min → 99417 at 40+ min
    "99215": 55,    # 99215 max time 54 min → 99417 at 55+ min
}

# Behavioral Health Integration (BHI)
BHI_CODES = {
    "99484": {"description": "General BHI 20+ min/month care management by clinical staff", "rate_est": 50.28},
}

# Remote Patient Monitoring (RPM)
RPM_CODES = {
    "99453": {"description": "RPM patient setup and education — one time", "rate_est": 19.22},
    "99454": {"description": "RPM device supply with data transmission per 30-day period", "rate_est": 64.65},
    "99457": {"description": "RPM first 20 min monitoring and management per month", "rate_est": 50.28},
    "99458": {"description": "RPM each add'l 20 min per month", "rate_est": 40.60},
}

# ===========================================================================
# CHRONIC CONDITION ICD-10 PREFIXES — CCM and RPM Eligibility Detection
# A patient needs 2+ chronic conditions from this list for CCM eligibility.
# Based on CMS CCM policy documentation (CY 2025).
# ===========================================================================

CCM_CHRONIC_CONDITION_PREFIXES = [
    "I10", "I11", "I12", "I13", "I14", "I15", "I16",  # Hypertension
    "E11",                                               # Type 2 diabetes
    "E10",                                               # Type 1 diabetes
    "N18",                                               # CKD
    "I50",                                               # Heart failure
    "J44",                                               # COPD
    "F32", "F33",                                        # Depressive disorders
    "F41",                                               # Anxiety
    "E78",                                               # Hyperlipidemia / dyslipidemia
    "E66",                                               # Obesity
    "I48",                                               # Atrial fibrillation
    "I25",                                               # Coronary artery disease
    "Z87.891",                                           # Hx of nicotine dependence
    "M79", "M05", "M06",                                 # Musculoskeletal / RA
    "G20",                                               # Parkinson's disease
    "G30",                                               # Alzheimer's disease
    "K70", "K71", "K72", "K73", "K74",                  # Liver disease
    "J45",                                               # Asthma
    "I63", "I69",                                        # Stroke / sequelae
    "C",                                                 # Any active cancer diagnosis
]

# Behavioral health condition prefixes for BHI eligibility
BHI_CONDITION_PREFIXES = [
    "F32", "F33",   # Depressive disorders
    "F41",          # Anxiety disorders
    "F90",          # ADHD
    "F43",          # Stress-related disorders (PTSD, adjustment)
    "F10", "F11", "F12", "F13", "F14", "F15", "F16", "F17", "F18", "F19",  # Substance use
]

# RPM-benefiting conditions
RPM_CONDITION_PREFIXES = [
    "I10", "I11", "I12", "I13",  # Hypertension — blood pressure monitoring
    "E11", "E10",                 # Diabetes — glucometer monitoring
    "I50",                        # Heart failure — weight and symptoms
    "J44",                        # COPD — pulse oximetry
    "E66",                        # Obesity — weight monitoring
]

# ===========================================================================
# SCREENING / PREVENTIVE BILLING CODES — Used by Care Gap → Billing Bridge
# Maps CPT/HCPCS codes from care gap engine billing_code_pair fields to
# rate estimates. Rates are 2025 CMS national averages (non-facility).
# ===========================================================================

SCREENING_CODES = {
    # Colorectal
    "G0105": {"description": "Colorectal cancer screening — colonoscopy (high risk)", "rate_est": 263.20},
    "G0121": {"description": "Colorectal cancer screening — colonoscopy (non-high risk)", "rate_est": 263.20},
    "82270": {"description": "Fecal occult blood test (FOBT/FIT)", "rate_est": 4.28},
    # Breast
    "77067": {"description": "Screening mammography, bilateral", "rate_est": 139.80},
    # Cervical
    "88141": {"description": "Pap smear cytopathology interpretation", "rate_est": 20.15},
    "Q0091": {"description": "Pap smear specimen collection", "rate_est": 36.35},
    "87624": {"description": "HPV high-risk detection", "rate_est": 36.40},
    # Lung
    "G0297": {"description": "LDCT lung cancer screening", "rate_est": 60.49},
    "71271": {"description": "CT thorax low dose for lung cancer screening", "rate_est": 60.49},
    # Bone density
    "77080": {"description": "DEXA scan bone density study", "rate_est": 41.78},
    # Blood pressure
    "99473": {"description": "Self-measured BP patient education/training", "rate_est": 11.04},
    # Diabetes
    "82947": {"description": "Glucose quantitative, blood", "rate_est": 5.14},
    "83036": {"description": "Hemoglobin A1c (HbA1c)", "rate_est": 11.28},
    # Lipid
    "80061": {"description": "Lipid panel", "rate_est": 18.39},
    # Depression
    "G0444": {"description": "Annual depression screening 15 min", "rate_est": 26.41},
    "96127": {"description": "Brief emotional/behavioral assessment", "rate_est": 5.44},
    # AAA
    "G0389": {"description": "AAA screening ultrasound", "rate_est": 65.12},
    # Fall risk
    "99420": {"description": "Health risk assessment (fall risk)", "rate_est": 0.0},
    # HIV
    "86701": {"description": "HIV-1 antibody test", "rate_est": 8.52},
    "87389": {"description": "HIV-1 antigen with antibodies", "rate_est": 25.91},
}

# Vaccine administration codes — used by care gap vaccine rules
VACCINE_ADMIN_CODES = {
    "90471": {"description": "Immunization admin, first vaccine (injection)", "rate_est": 27.32},
    "90472": {"description": "Immunization admin, each additional (injection)", "rate_est": 13.66},
    "90688": {"description": "Influenza vaccine, quadrivalent", "rate_est": 22.50},
    "90715": {"description": "Tdap vaccine", "rate_est": 34.60},
    "90677": {"description": "Pneumococcal conjugate vaccine (PCV20)", "rate_est": 130.00},
    "90750": {"description": "Shingrix (zoster vaccine recombinant)", "rate_est": 168.00},
    "91309": {"description": "COVID-19 vaccine, 2-dose mRNA", "rate_est": 0.00},
    "0074A": {"description": "COVID-19 vaccine admin, 2-dose mRNA booster", "rate_est": 40.00},
}

# ===========================================================================
# TOBACCO CESSATION CODES (Rule 9) — 99406, 99407, 99408
# Trigger: Active tobacco/nicotine diagnosis (F17.*, Z72.0, Z87.891)
# ===========================================================================

TOBACCO_CESSATION_CODES = {
    "99406": {"description": "Smoking/tobacco cessation counseling 3-10 min", "rate_est": 15.16},
    "99407": {"description": "Smoking/tobacco cessation counseling >10 min", "rate_est": 30.33},
}

TOBACCO_CONDITION_PREFIXES = [
    "F17",      # Nicotine dependence
    "Z72.0",    # Tobacco use
    "Z87.891",  # Personal history of nicotine dependence
]

# ===========================================================================
# ALCOHOL / SUBSTANCE SCREENING CODES (Rule 10) — G0442, G0443, 99408, 99409
# Trigger: Annual for all adults; F10-F19 elevate priority
# ===========================================================================

ALCOHOL_SCREENING_CODES = {
    "G0442": {"description": "Annual alcohol misuse screening 15 min", "rate_est": 14.76},
    "G0443": {"description": "Brief alcohol misuse counseling 15 min", "rate_est": 27.32},
    "99408": {"description": "SBIRT alcohol/substance screening and intervention 15-30 min", "rate_est": 37.24},
    "99409": {"description": "SBIRT alcohol/substance intervention >30 min", "rate_est": 65.49},
}

# ===========================================================================
# COGNITIVE ASSESSMENT CODES (Rule 11) — 99483
# Trigger: Age 65+ with risk factors (dementia Dx, memory complaints, falls)
# ===========================================================================

COGNITIVE_ASSESSMENT_CODES = {
    "99483": {"description": "Assessment of and care planning for cognitive impairment", "rate_est": 257.24},
}

COGNITIVE_CONDITION_PREFIXES = [
    "F00", "F01", "F02", "F03",  # Dementia
    "G30",                        # Alzheimer's disease
    "R41",                        # Memory / cognitive symptoms
]

# ===========================================================================
# OBESITY / NUTRITION CODES (Rule 12) — G0447, 97802, 97803, G0473
# Trigger: BMI ≥30 (E66.*) or diabetes (E10-E14)
# ===========================================================================

OBESITY_NUTRITION_CODES = {
    "G0447": {"description": "Intensive behavioral therapy for obesity 15 min (Medicare)", "rate_est": 27.77},
    "97802": {"description": "Medical nutrition therapy initial assessment 15 min", "rate_est": 35.04},
    "97803": {"description": "Medical nutrition therapy reassessment 15 min", "rate_est": 24.71},
    "G0473": {"description": "Face-to-face behavioral counseling for obesity 15 min", "rate_est": 27.77},
}

OBESITY_CONDITION_PREFIXES = [
    "E66",          # Overweight and obesity
    "E10", "E11",   # Diabetes mellitus
    "E13",          # Other specified diabetes
]

# ===========================================================================
# ADVANCE CARE PLANNING STANDALONE CODES (Rule 13) — 99497, 99498
# Trigger: Age 65+ or serious illness; must NOT duplicate AWV stack ACP
# ===========================================================================

ACP_STANDALONE_CODES = {
    "99497": {"description": "Advance care planning first 16-30 min", "rate_est": 87.13},
    "99498": {"description": "Advance care planning each additional 30 min", "rate_est": 75.78},
}

SERIOUS_ILLNESS_PREFIXES = [
    "C",              # Any malignant neoplasm
    "I50",            # Heart failure
    "N18.4", "N18.5", "N18.6",  # CKD stages 4-6
    "J44",            # COPD
    "G30",            # Alzheimer's disease
    "G12",            # Motor neuron disease / ALS
    "G20",            # Parkinson's disease
    "F00", "F01", "F02", "F03",  # Dementia
]

# ===========================================================================
# STI / HEPATITIS SCREENING CODES (Rule 14) — USPSTF risk-based
# ===========================================================================

STI_SCREENING_CODES = {
    "86580": {"description": "Hepatitis B surface antigen (HBsAg)", "rate_est": 11.70},
    "86803": {"description": "Hepatitis C antibody", "rate_est": 17.52},
    "86592": {"description": "Syphilis test, qualitative (RPR)", "rate_est": 5.37},
    "87491": {"description": "Chlamydia NAA detection", "rate_est": 37.76},
    "87591": {"description": "Gonorrhea NAA detection", "rate_est": 37.76},
}

# ===========================================================================
# PREVENTIVE E&M CODES (Rule 15) — Commercial/Medicaid (non-Medicare)
# ===========================================================================

PREVENTIVE_EM_CODES = {
    # New patient preventive by age band
    "99381": {"description": "Preventive visit new patient infant (<1 yr)", "rate_est": 90.00},
    "99382": {"description": "Preventive visit new patient age 1-4", "rate_est": 100.00},
    "99383": {"description": "Preventive visit new patient age 5-11", "rate_est": 105.00},
    "99384": {"description": "Preventive visit new patient age 12-17", "rate_est": 120.00},
    "99385": {"description": "Preventive visit new patient age 18-39", "rate_est": 130.00},
    "99386": {"description": "Preventive visit new patient age 40-64", "rate_est": 155.00},
    "99387": {"description": "Preventive visit new patient age 65+", "rate_est": 175.00},
    # Established patient preventive by age band
    "99391": {"description": "Preventive visit established patient infant (<1 yr)", "rate_est": 80.00},
    "99392": {"description": "Preventive visit established patient age 1-4", "rate_est": 90.00},
    "99393": {"description": "Preventive visit established patient age 5-11", "rate_est": 90.00},
    "99394": {"description": "Preventive visit established patient age 12-17", "rate_est": 100.00},
    "99395": {"description": "Preventive visit established patient age 18-39", "rate_est": 115.00},
    "99396": {"description": "Preventive visit established patient age 40-64", "rate_est": 130.00},
    "99397": {"description": "Preventive visit established patient age 65+", "rate_est": 150.00},
}

# Age bands for preventive E&M code selection
PREVENTIVE_AGE_BANDS_NEW = [
    (0, 0, "99381"), (1, 4, "99382"), (5, 11, "99383"), (12, 17, "99384"),
    (18, 39, "99385"), (40, 64, "99386"), (65, 999, "99387"),
]
PREVENTIVE_AGE_BANDS_ESTABLISHED = [
    (0, 0, "99391"), (1, 4, "99392"), (5, 11, "99393"), (12, 17, "99394"),
    (18, 39, "99395"), (40, 64, "99396"), (65, 999, "99397"),
]

# ===========================================================================
# BACKGROUND JOB SCHEDULE (all times are local clinic time)
# ===========================================================================

MORNING_BRIEFING_HOUR = 6        # 6:00 AM — weather, recalls, care gaps
MORNING_BRIEFING_MINUTE = 0

OVERNIGHT_PREP_HOUR = 20         # 8:00 PM — pre-visit note prep
OVERNIGHT_PREP_MINUTE = 0

DAILY_RECALL_CHECK_HOUR = 5      # 5:45 AM — OpenFDA recall scan (before briefing)
DAILY_RECALL_CHECK_MINUTE = 45

WEEKLY_CACHE_REFRESH_DAY = "sun" # Sunday 2:00 AM — full cache refresh
WEEKLY_CACHE_REFRESH_HOUR = 2
WEEKLY_CACHE_REFRESH_MINUTE = 0

# ===========================================================================
# GEOGRAPHIC CONFIG — Set once during clinic setup
# These are used for weather and locality-adjusted billing calculations.
# Clinic admin updates these via the admin settings page.
# ===========================================================================

# Default: Richmond, VA area (update to actual clinic coordinates)
DEFAULT_CLINIC_LATITUDE = 37.5407
DEFAULT_CLINIC_LONGITUDE = -77.4360
DEFAULT_CLINIC_ZIP = "23220"

# ===========================================================================
# CACHE DATABASE SETTINGS
# The API cache uses a separate SQLite table within the main carecompanion.db
# ===========================================================================

API_CACHE_TABLE_NAME = "api_response_cache"
API_CACHE_MAX_SIZE_MB = 500         # Warn if cache exceeds this size

# ===========================================================================
# PROCEDURE CODES (Phase 19B.1) — In-office procedures
# ===========================================================================

PROCEDURE_CODES = {
    # EKG
    "93000": {"description": "Electrocardiogram 12-lead with interpretation", "rate_est": 25.44},
    "93005": {"description": "EKG tracing only", "rate_est": 7.22},
    "93010": {"description": "EKG interpretation and report only", "rate_est": 18.22},
    # Spirometry
    "94010": {"description": "Spirometry, pre-bronchodilator only", "rate_est": 33.00},
    "94060": {"description": "Spirometry pre- and post-bronchodilator", "rate_est": 53.00},
    # POCT
    "87880": {"description": "Rapid strep test (antigen detection)", "rate_est": 12.10},
    "87804": {"description": "Rapid influenza test", "rate_est": 16.55},
    "81002": {"description": "Urinalysis non-automated without microscopy", "rate_est": 3.53},
    "81025": {"description": "Urine pregnancy test (hCG qualitative)", "rate_est": 8.47},
    "82962": {"description": "Glucose, blood by glucometer", "rate_est": 3.47},
    # Venipuncture
    "36415": {"description": "Venipuncture routine", "rate_est": 3.00},
    "36416": {"description": "Capillary blood collection (fingerstick)", "rate_est": 3.00},
    # Injection admin
    "96372": {"description": "Therapeutic injection (IM/SubQ), single or initial", "rate_est": 25.85},
    # Nebulizer
    "94640": {"description": "Pressurised/non-pressurised inhalation treatment (nebuliser)", "rate_est": 19.11},
    # Pulse oximetry
    "94760": {"description": "Pulse oximetry, single determination", "rate_est": 7.77},
    "94761": {"description": "Pulse oximetry, multiple determinations", "rate_est": 12.05},
}

# EKG trigger conditions: cardiac symptoms + QTc-prolonging meds
EKG_SYMPTOM_PREFIXES = [
    "I10", "I11", "I25", "I48", "I49", "I50",  # Hypertension, CAD, AF, arrhythmias, HF
    "R00", "R01",                                 # Abnormal heartbeat / cardiac murmurs
    "R06",                                        # Dyspnea
    "R55",                                        # Syncope
    "R07",                                        # Chest pain
]

SPIROMETRY_DX_PREFIXES = [
    "J44",   # COPD
    "J45",   # Asthma
    "J98",   # Other respiratory disorders
    "R06",   # Dyspnea / abnormalities of breathing
]

RESPIRATORY_DX_PREFIXES = [
    "J44",   # COPD
    "J45",   # Asthma
    "J06",   # Acute URI
    "J20",   # Acute bronchitis
    "J21",   # Acute bronchiolitis
    "J22",   # Unspecified acute lower respiratory infection
    "J96",   # Respiratory failure
    "R06",   # Dyspnea
    "R05",   # Cough
]

# ===========================================================================
# CHRONIC MONITORING CODES (Phase 19B.2) — Medication-driven lab monitoring
# ===========================================================================

CHRONIC_MONITORING_CODES = {
    "83036": {"description": "Hemoglobin A1c (HbA1c)", "rate_est": 11.28},
    "80061": {"description": "Lipid panel (total chol, HDL, LDL, TG)", "rate_est": 18.39},
    "84443": {"description": "Thyroid stimulating hormone (TSH)", "rate_est": 15.45},
    "80048": {"description": "Basic metabolic panel (BMP)", "rate_est": 10.56},
    "80053": {"description": "Comprehensive metabolic panel (CMP)", "rate_est": 10.96},
    "85025": {"description": "Complete blood count with differential (CBC)", "rate_est": 7.77},
    "85027": {"description": "CBC automated without differential", "rate_est": 6.47},
    "85610": {"description": "Prothrombin time (PT/INR)", "rate_est": 5.14},
    "80076": {"description": "Hepatic function panel (LFT)", "rate_est": 10.56},
    "82043": {"description": "Urine microalbumin, quantitative", "rate_est": 7.54},
    "82570": {"description": "Urine creatinine", "rate_est": 6.38},
    "82306": {"description": "25-hydroxyvitamin D (Vitamin D)", "rate_est": 25.20},
}

# DEPRECATED: Legacy fallback only. New monitoring rules are populated
# dynamically via MonitoringRuleEngine (Phase 23). This MAP is read only
# when the monitoring_rule table is empty or migration hasn't run.
# Do NOT add new entries here — seed them in migrations/seed_monitoring_rules.py
# or let the DailyMed/VSAC waterfall populate them automatically.
# MEDICATION_MONITORING_MAP: drug class → (lab CPT, interval months, rule code, Dx prefixes)
MEDICATION_MONITORING_MAP = {
    "diabetes": {
        "dx_prefixes": ["E10", "E11", "R73"],
        "lab_code": "83036",
        "interval_months": 6,
        "rule_code": "MON_A1C",
        "description": "A1C monitoring for diabetes/pre-diabetes",
    },
    "statin_hld": {
        "dx_prefixes": ["E78"],
        "medications": ["atorvastatin", "rosuvastatin", "simvastatin", "pravastatin",
                        "lovastatin", "fluvastatin", "pitavastatin", "ezetimibe"],
        "lab_code": "80061",
        "interval_months": 12,
        "rule_code": "MON_LIPID",
        "description": "Lipid panel monitoring for dyslipidaemia / statin therapy",
    },
    "thyroid": {
        "dx_prefixes": ["E01", "E02", "E03", "E04", "E05", "E06", "E07"],
        "medications": ["levothyroxine", "synthroid", "liothyronine", "armour thyroid",
                        "methimazole", "propylthiouracil"],
        "lab_code": "84443",
        "interval_months": 12,
        "rule_code": "MON_TSH",
        "description": "TSH monitoring for thyroid disorder / thyroid medication",
    },
    "renal": {
        "dx_prefixes": ["N18"],
        "medications": ["metformin", "lisinopril", "enalapril", "ramipril", "benazepril",
                        "losartan", "valsartan", "irbesartan", "olmesartan",
                        "hydrochlorothiazide", "furosemide", "spironolactone",
                        "chlorthalidone", "lithium"],
        "lab_code": "80048",
        "interval_months": 12,
        "rule_code": "MON_RENAL",
        "description": "BMP/renal monitoring for nephrotoxic medication or CKD",
    },
    "cbc_meds": {
        "dx_prefixes": [],
        "medications": ["methotrexate", "carbamazepine", "clozapine", "dapsone",
                        "azathioprine", "mycophenolate"],
        "lab_code": "85025",
        "interval_months": 6,
        "rule_code": "MON_CBC",
        "description": "CBC monitoring for bone-marrow-suppressive medication",
    },
    "warfarin": {
        "dx_prefixes": [],
        "medications": ["warfarin", "coumadin", "jantoven"],
        "lab_code": "85610",
        "interval_months": 3,
        "rule_code": "MON_INR",
        "description": "INR monitoring for warfarin therapy",
    },
    "liver": {
        "dx_prefixes": ["K70", "K71", "K72", "K73", "K74"],
        "medications": ["methotrexate", "isoniazid", "valproic acid", "divalproex",
                        "ketoconazole", "amiodarone"],
        "lab_code": "80076",
        "interval_months": 12,
        "rule_code": "MON_LFT",
        "description": "Hepatic function monitoring for hepatotoxic medication / liver disease",
    },
    "uacr": {
        "dx_prefixes": ["E10", "E11", "N18"],
        "medications": [],
        "lab_code": "82043",
        "interval_months": 12,
        "rule_code": "MON_UACR",
        "description": "Annual urine microalbumin for diabetes / CKD",
    },
    "vitd": {
        "dx_prefixes": ["M80", "M81", "N18"],
        "medications": ["ergocalciferol", "cholecalciferol", "calcitriol",
                        "vitamin d"],
        "lab_code": "82306",
        "interval_months": 12,
        "rule_code": "MON_VITD",
        "description": "Annual Vitamin D for osteoporosis / CKD / supplementation",
    },
}

# ===========================================================================
# PCM CODES (Phase 19B.4) — Principal Care Management (single complex condition)
# ===========================================================================

PCM_CODES = {
    "99424": {"description": "PCM first 30 min, personally by NP/MD", "rate_est": 70.00},
    "99425": {"description": "PCM each add'l 30 min, personally by NP/MD", "rate_est": 50.00},
}

# ===========================================================================
# EXPANDED VACCINE PRODUCT CODES (Phase 19B.6)
# ===========================================================================

VACCINE_PRODUCT_CODES = {
    # HPV
    "90651": {"description": "9-valent HPV vaccine (Gardasil 9)", "rate_est": 250.00, "series_doses": 3, "age_min": 9, "age_max": 45},
    # Hepatitis B
    "90739": {"description": "HepB vaccine adult 2-dose (Heplisav-B)", "rate_est": 60.00, "series_doses": 2, "age_min": 18, "age_max": 999},
    "90746": {"description": "HepB vaccine adult 3-dose (Engerix-B)", "rate_est": 35.00, "series_doses": 3, "age_min": 18, "age_max": 999},
    "90747": {"description": "HepB vaccine 4-dose (dialysis)", "rate_est": 40.00, "series_doses": 4, "age_min": 18, "age_max": 999},
    # Hepatitis A
    "90632": {"description": "HepA vaccine pediatric 2-dose", "rate_est": 25.00, "series_doses": 2, "age_min": 1, "age_max": 18},
    "90636": {"description": "HepA-HepB combo vaccine (Twinrix)", "rate_est": 65.00, "series_doses": 3, "age_min": 18, "age_max": 999},
    # RSV
    "90680": {"description": "RSV vaccine (Arexvy / Abrysvo)", "rate_est": 200.00, "series_doses": 1, "age_min": 60, "age_max": 999},
    # Meningococcal ACWY
    "90734": {"description": "MenACWY vaccine (Menactra/Menveo)", "rate_est": 75.00, "series_doses": 2, "age_min": 11, "age_max": 55},
    # Meningococcal B
    "90620": {"description": "MenB vaccine (Bexsero, 2-dose)", "rate_est": 75.00, "series_doses": 2, "age_min": 16, "age_max": 23},
    "90621": {"description": "MenB vaccine (Trumenba, 3-dose)", "rate_est": 75.00, "series_doses": 3, "age_min": 16, "age_max": 23},
}

# ===========================================================================
# TELEHEALTH CODES (Phase 19C.1) — Phone E/M, Digital E/M, Interprofessional
# ===========================================================================

TELEHEALTH_CODES = {
    # Phone E/M (time-based, requires MDM)
    "99441": {"description": "Telephone E/M 5-10 min medical discussion", "rate_est": 28.83},
    "99442": {"description": "Telephone E/M 11-20 min medical discussion", "rate_est": 51.24},
    "99443": {"description": "Telephone E/M 21-30 min medical discussion", "rate_est": 74.49},
    # Digital/online E/M (patient-initiated portal messages, cumulative over 7 days)
    "99421": {"description": "Online digital E/M 5-10 min cumulative", "rate_est": 33.00},
    "99422": {"description": "Online digital E/M 11-20 min cumulative", "rate_est": 62.00},
    "99423": {"description": "Online digital E/M 21+ min cumulative", "rate_est": 95.00},
    # Interprofessional consult
    "99452": {"description": "Interprofessional telephone/internet/EHR consult 16-30 min", "rate_est": 35.15},
}

# ===========================================================================
# COCM CODES (Phase 19C.2) — Collaborative Care Model
# ===========================================================================

COCM_CODES = {
    "99492": {"description": "Psychiatric CoCM initial month, 36+ total min", "rate_est": 165.04},
    "99493": {"description": "Psychiatric CoCM subsequent month, 36+ total min", "rate_est": 130.28},
    "99494": {"description": "Psychiatric CoCM each additional 30 min add-on", "rate_est": 64.72},
}

# ===========================================================================
# COUNSELING CODES (Phase 19C.3) — Preventive Counseling Services
# ===========================================================================

COUNSELING_CODES = {
    # Falls prevention
    "97110": {"description": "Therapeutic exercise (fall prevention)", "rate_est": 30.88},
    # CVD Intensive Behavioral Therapy
    "G0446": {"description": "Intensive behavioral therapy for CVD, annual", "rate_est": 28.31},
    # Preventive counseling (breastfeeding, general)
    "99401": {"description": "Preventive medicine counseling 15 min", "rate_est": 32.00},
    "99402": {"description": "Preventive medicine counseling 30 min", "rate_est": 55.00},
    "99403": {"description": "Preventive medicine counseling 45 min", "rate_est": 75.00},
    "99404": {"description": "Preventive medicine counseling 60 min", "rate_est": 92.00},
    # DSMT — Diabetes Self-Management Training
    "G0108": {"description": "DSMT individual, per 30 min", "rate_est": 34.50},
    "G0109": {"description": "DSMT group (2+ patients), per 30 min", "rate_est": 14.50},
}

CVD_RISK_PREFIXES = [
    "E78",               # Dyslipidaemia
    "I10", "I11", "I12", "I13",  # Hypertension
    "E11",               # Type 2 DM
    "Z72.0",             # Tobacco use
    "E66",               # Obesity
]

FALL_RISK_PREFIXES = [
    "R29.6",   # Repeated falls
    "W19",     # Unspecified fall
    "Z91.81",  # History of falling
    "R26",     # Gait / mobility abnormalities
    "M81",     # Osteoporosis without fracture
]

# ===========================================================================
# SCREENING CODES (Phase 19C.4) — Expanded Screening Instruments
# ===========================================================================

EXPANDED_SCREENING_CODES = {
    "96110": {"description": "Developmental screening (ASQ-3/M-CHAT) with scoring", "rate_est": 10.21},
    "99408": {"description": "SBIRT alcohol/substance screening and intervention 15-30 min", "rate_est": 37.24},
    "99409": {"description": "SBIRT alcohol/substance intervention >30 min", "rate_est": 65.49},
    "96127": {"description": "Brief emotional/behavioral assessment (PHQ-9, Edinburgh)", "rate_est": 5.44},
    "96161": {"description": "Caregiver-focused health risk assessment (perinatal depression)", "rate_est": 5.44},
}

# Bright Futures developmental screening ages (months)
DEVELOPMENTAL_SCREENING_MONTHS = [9, 18, 24, 30]

# ===========================================================================
# PEDIATRIC CODES (Phase 19D.1) — Bright Futures schedule, screening labs
# ===========================================================================

PEDIATRIC_CODES = {
    # Well-child new patient
    "99381": {"description": "Preventive visit new patient infant (<1y)", "rate_est": 115.00},
    "99382": {"description": "Preventive visit new patient 1-4y", "rate_est": 105.00},
    "99383": {"description": "Preventive visit new patient 5-11y", "rate_est": 100.00},
    "99384": {"description": "Preventive visit new patient 12-17y", "rate_est": 110.00},
    # Well-child established patient
    "99391": {"description": "Preventive visit established infant (<1y)", "rate_est": 95.00},
    "99392": {"description": "Preventive visit established 1-4y", "rate_est": 90.00},
    "99393": {"description": "Preventive visit established 5-11y", "rate_est": 85.00},
    "99394": {"description": "Preventive visit established 12-17y", "rate_est": 95.00},
    # Lead screening
    "83655": {"description": "Lead, venous", "rate_est": 7.72},
    # Anemia screening
    "85014": {"description": "Hematocrit", "rate_est": 3.28},
    "85018": {"description": "Hemoglobin", "rate_est": 3.28},
    # Dyslipidemia screening
    "80061": {"description": "Lipid panel (total/HDL/LDL/trig)", "rate_est": 18.39},
    # Fluoride varnish
    "99188": {"description": "Fluoride varnish application by non-dental provider", "rate_est": 25.16},
    # Vision screening
    "99173": {"description": "Visual acuity screening", "rate_est": 4.55},
    "99174": {"description": "Instrument-based ocular screening, bilateral, auto", "rate_est": 11.60},
    "99177": {"description": "Instrument-based ocular screening, remote analysis", "rate_est": 11.60},
    # Hearing screening
    "92551": {"description": "Pure tone screening, air only", "rate_est": 11.10},
    "92552": {"description": "Pure tone audiometry, air only", "rate_est": 15.70},
    "92567": {"description": "Tympanometry (impedance testing)", "rate_est": 13.22},
}

# Bright Futures well-child periodicity schedule
# Keys = age description; values = age ranges in months for matching
BRIGHT_FUTURES_SCHEDULE = {
    "newborn":    {"months": (0, 0), "new": "99381", "est": "99391"},
    "3_5_days":   {"months": (0, 0), "new": "99381", "est": "99391"},
    "1_month":    {"months": (1, 1), "new": "99381", "est": "99391"},
    "2_months":   {"months": (2, 2), "new": "99381", "est": "99391"},
    "4_months":   {"months": (3, 5), "new": "99381", "est": "99391"},
    "6_months":   {"months": (5, 7), "new": "99381", "est": "99391"},
    "9_months":   {"months": (8, 10), "new": "99381", "est": "99391"},
    "12_months":  {"months": (11, 13), "new": "99381", "est": "99391"},
    "15_months":  {"months": (14, 16), "new": "99382", "est": "99392"},
    "18_months":  {"months": (17, 19), "new": "99382", "est": "99392"},
    "24_months":  {"months": (23, 25), "new": "99382", "est": "99392"},
    "30_months":  {"months": (29, 31), "new": "99382", "est": "99392"},
    "3_years":    {"months": (35, 37), "new": "99382", "est": "99392"},
    "4_years":    {"months": (47, 49), "new": "99382", "est": "99392"},
    "5_years":    {"months": (59, 61), "new": "99383", "est": "99393"},
    "6_years":    {"months": (71, 73), "new": "99383", "est": "99393"},
    "7_years":    {"months": (83, 85), "new": "99383", "est": "99393"},
    "8_years":    {"months": (95, 97), "new": "99383", "est": "99393"},
    "9_years":    {"months": (107, 109), "new": "99383", "est": "99393"},
    "10_years":   {"months": (119, 121), "new": "99383", "est": "99393"},
    "11_years":   {"months": (131, 133), "new": "99383", "est": "99393"},
    "12_years":   {"months": (143, 145), "new": "99384", "est": "99394"},
}

# Hearing screening ages per Bright Futures (years)
HEARING_SCREENING_AGES = [4, 5, 6, 8, 10]
HEARING_SCREENING_RANGES = [(11, 14), (15, 17), (18, 21)]

# ===========================================================================
# MISC CODES (Phase 19D.2) — After-hours, care plan oversight, PrEP, GDM, etc.
# ===========================================================================

MISC_CODES = {
    # After-hours add-ons
    "99050": {"description": "Services provided in the office at times other than regularly scheduled hours", "rate_est": 23.55},
    "99051": {"description": "Services provided in the office during regularly scheduled evening/weekend hours", "rate_est": 30.00},
    "99053": {"description": "Services provided between 10pm and 8am at 24-hr facility", "rate_est": 35.00},
    # Care plan oversight
    "99339": {"description": "Care plan oversight, home health/hospice, 15-29 min/month", "rate_est": 60.50},
    "99340": {"description": "Care plan oversight, home health/hospice, 30+ min/month", "rate_est": 100.75},
    # GDM screening labs
    "82947": {"description": "Glucose, quantitative (blood)", "rate_est": 4.70},
    "82950": {"description": "Glucose post dose (GTT)", "rate_est": 5.12},
    "82951": {"description": "Glucose tolerance test (GTT), 3 specimens", "rate_est": 15.37},
    "82952": {"description": "GTT each additional specimen beyond 3", "rate_est": 5.12},
}

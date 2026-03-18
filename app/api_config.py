"""
NP Companion — Centralized API Configuration
File: app/api_config.py

Single source of truth for every external API used by NP Companion.
All base URLs, cache TTLs, rate limits, billing constants, and CMS
reimbursement values live here. No other file should hardcode these values.

Dependencies: None (no imports required — pure configuration)

NP Companion features that depend on this file:
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

# LOINC — lab test identification and reference ranges (free account required)
LOINC_BASE_URL = "https://fhir.loinc.org"
LOINC_CACHE_TTL_DAYS = 180          # LOINC codes are very stable

# UMLS — medical ontology crosswalk (free account + API key required)
UMLS_BASE_URL = "https://uts.nlm.nih.gov/uts/rest"
UMLS_CACHE_TTL_DAYS = 30            # Terminology updates are periodic

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
# HTTP CLIENT SETTINGS (shared by all API services)
# ===========================================================================

HTTP_TIMEOUT_SECONDS = 10           # Timeout per API request
HTTP_MAX_RETRIES = 3                # Retry attempts on transient errors
HTTP_RETRY_BACKOFF_SECONDS = 1.0    # Initial backoff; doubles each retry
HTTP_USER_AGENT = "NPCompanion/1.1.2 (clinical-workflow; non-commercial)"

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
# The API cache uses a separate SQLite table within the main npcompanion.db
# ===========================================================================

API_CACHE_TABLE_NAME = "api_response_cache"
API_CACHE_MAX_SIZE_MB = 500         # Warn if cache exceeds this size

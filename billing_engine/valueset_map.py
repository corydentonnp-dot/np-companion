"""
CareCompanion — VSAC Value Set OID → Billing Rule Category Mapping
File: app/services/billing_valueset_map.py

Maps VSAC value set OIDs to billing rule categories so that the billing
rules engine can pull dynamically-updated condition codes from CMS eCQM
value sets instead of relying solely on hardcoded ICD-10 prefix lists.

OIDs themselves rarely change (they are stable identifiers for a concept
such as "Diabetes" or "Tobacco Use").  The *contents* of each value set
(the individual ICD-10/SNOMED codes) are updated annually by CMS and
refreshed automatically through the VSAC cache.

Hardcoded prefix lists in api_config.py remain as offline fallbacks when
VSAC is unavailable or unconfigured.
"""

import json
import logging

logger = logging.getLogger(__name__)

# ======================================================================
# OID → Category Mapping
#
# Each billing rule category maps to one or more VSAC value set OIDs.
# When the billing engine needs condition codes for a category, it
# expands these OIDs from cache (or live API) and collects all ICD-10
# codes contained within.
#
# Sources: CMS eCQM value sets at https://vsac.nlm.nih.gov/
# ======================================================================

CATEGORY_VSAC_OIDS = {
    # Category 1 — CCM chronic conditions
    "ccm": [
        "2.16.840.1.113883.3.464.1003.103.12.1001",  # Diabetes
        "2.16.840.1.113883.3.464.1003.104.12.1011",  # Heart Failure
        "2.16.840.1.113883.3.526.3.1489",             # Hypertension
        "2.16.840.1.113883.3.464.1003.109.12.1028",  # CKD
        "2.16.840.1.113883.3.464.1003.102.12.1011",  # COPD
        "2.16.840.1.113762.1.4.1222.1587",            # Atrial Fibrillation
    ],
    # Category 6 — BHI behavioral health conditions
    "bhi": [
        "2.16.840.1.113883.3.600.145",               # Major Depression
        "2.16.840.1.113883.3.526.3.1491",             # Anxiety
        "2.16.840.1.113883.3.464.1003.106.12.1004",  # Substance Use Disorders
    ],
    # Category 7 — RPM eligible conditions
    "rpm": [
        "2.16.840.1.113883.3.526.3.1489",             # Hypertension
        "2.16.840.1.113883.3.464.1003.103.12.1001",  # Diabetes
        "2.16.840.1.113883.3.464.1003.104.12.1011",  # Heart Failure
        "2.16.840.1.113883.3.464.1003.102.12.1011",  # COPD
    ],
    # Category 9 — Tobacco use conditions
    "tobacco": [
        "2.16.840.1.113883.3.600.2390",              # Tobacco Use
    ],
    # Category 11 — Cognitive impairment conditions
    "cognitive": [
        "2.16.840.1.113883.3.526.3.1005",             # Dementia & Mental Degenerations
    ],
    # Category 12 — Obesity / nutrition conditions
    "obesity": [
        "2.16.840.1.113762.1.4.1222.36",              # Overweight or Obese
        "2.16.840.1.113883.3.464.1003.103.12.1001",  # Diabetes (shared with CCM)
    ],
    # Category 13 — ACP serious illness conditions
    "serious_illness": [
        "2.16.840.1.113883.3.464.1003.104.12.1011",  # Heart Failure
        "2.16.840.1.113883.3.464.1003.109.12.1028",  # CKD
        "2.16.840.1.113883.3.464.1003.102.12.1011",  # COPD
        "2.16.840.1.113883.3.526.3.1005",             # Dementia
    ],
}


# ======================================================================
# Phase 23 — Monitoring VSAC OIDs
#
# Maps CMS eCQM quality measure OIDs to monitoring categories.
# MonitoringRuleEngine queries these to determine which patients
# qualify for condition-driven monitoring dynamically.
# ======================================================================

MONITORING_VSAC_OIDS = {
    "monitoring_diabetes": [
        "2.16.840.1.113883.3.464.1003.103.12.1001",  # NQF 0059 Diabetes Comprehensive Care
    ],
    "monitoring_ckd": [
        "2.16.840.1.113883.3.464.1003.109.12.1028",  # NQF 0062 CKD Management
    ],
    "monitoring_heart_failure": [
        "2.16.840.1.113883.3.464.1003.104.12.1011",  # NQF 2907 Heart Failure
    ],
    "monitoring_liver": [
        "2.16.840.1.113762.1.4.1222.1549",            # Chronic Liver Disease
        "2.16.840.1.113883.3.464.1003.110.12.1082",  # Hepatitis B
    ],
    "monitoring_thyroid": [
        "2.16.840.1.113762.1.4.1222.107",             # Thyroid Disorders
    ],
    "monitoring_autoimmune": [
        "2.16.840.1.113762.1.4.1222.635",             # Rheumatoid Arthritis
        "2.16.840.1.113762.1.4.1222.636",             # Systemic Lupus Erythematosus
    ],
    "monitoring_bh": [
        "2.16.840.1.113883.3.600.145",                # Major Depression (shared with BHI)
        "2.16.840.1.113883.3.464.1003.105.12.1007",  # Schizophrenia
        "2.16.840.1.113883.3.464.1003.105.12.1004",  # Bipolar Disorder
    ],
}


# ======================================================================
# Phase 23 — Preventive Service VSAC OIDs  (23.B4)
#
# Maps CMS eCQM quality measure OIDs to USPSTF-grade preventive
# services.  Each OID expansion yields eligible-population codes
# (age, sex, diagnoses) that auto-update annually when CMS publishes
# new quality measure versions.
# ======================================================================

PREVENTIVE_VSAC_OIDS = {
    "lipid_panel":      "2.16.840.1.113883.3.464.1003.198.12.1035",  # Lipid (80061)
    "diabetes_screen":  "2.16.840.1.113883.3.464.1003.103.12.1001",  # Diabetes / A1C
    "hcv_screen":       "2.16.840.1.113762.1.4.1222.39",             # HCV (G0472/86803)
    "hbv_screen":       "2.16.840.1.113883.3.464.1003.110.12.1082",  # HBV (86704)
    "hiv_screen":       "2.16.840.1.113762.1.4.1056.50",             # HIV (80081/86701)
    "sti_screen":       "2.16.840.1.113883.3.464.1003.112.12.1003",  # STI (87490-87591)
    "crc_screen":       "2.16.840.1.113883.3.464.1003.108.12.1020",  # Colon CA (82270/81528)
    "lung_ca_screen":   "2.16.840.1.113762.1.4.1222.45",             # Lung CA (G0296)
    "cervical_screen":  "2.16.840.1.113883.3.464.1003.108.12.1017",  # Cervical (Q0091)
    "mammography":      "2.16.840.1.113883.3.464.1003.108.12.1018",  # Mammography (77067)
    "dexa_screen":      "2.16.840.1.113762.1.4.1222.47",             # DEXA (77080)
    "aaa_screen":       "2.16.840.1.113762.1.4.1222.48",             # AAA ultrasound (76706)
    "tb_screen":        "2.16.840.1.113762.1.4.1222.49",             # TB (86480)
    "bacteriuria":      "2.16.840.1.113762.1.4.1222.50",             # Bacteriuria (87086)
}


def get_vsac_icd10_codes(category: str, db=None) -> list:
    """
    Return a list of ICD-10 code strings from VSAC cache for the given
    billing category.  Returns an empty list if VSAC data is unavailable.

    Parameters
    ----------
    category : str
        Key from CATEGORY_VSAC_OIDS (e.g. "ccm", "bhi", "tobacco").
    db : SQLAlchemy db instance or None
        If None, attempts import from models.

    Returns
    -------
    list of str — ICD-10 codes (e.g. ["E11.9", "I10", "N18.3", ...])
    """
    oids = CATEGORY_VSAC_OIDS.get(category, [])
    if not oids:
        return []

    codes = set()
    try:
        from models.api_cache import VsacValueSetCache

        for oid in oids:
            entry = VsacValueSetCache.query.filter_by(oid=oid).first()
            if not entry or not entry.codes_json:
                continue
            code_list = json.loads(entry.codes_json)
            for c in code_list:
                system = (c.get("system") or "").lower()
                # Only collect ICD-10-CM codes
                if "icd" in system or "icd10" in system or "urn:oid:2.16.840.1.113883.6.90" in system:
                    code_val = (c.get("code") or "").strip()
                    if code_val:
                        codes.add(code_val.upper())
    except Exception as e:
        logger.debug("VSAC code lookup failed for category '%s': %s", category, e)

    return sorted(codes)

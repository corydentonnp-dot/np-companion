"""
CareCompanion — Billing Engine Payer Routing

Single source of truth for payer-specific code selection.

CRITICAL: Medicare uses G-codes (G0442, G0444, G0447) where commercial
payers use CPT codes (99408, 96127, 97802) + modifier 33. Wrong code
selection → claim denial. This module is the gating function that all
detectors consult for code/modifier decisions.

Phase 16.1: Medicare Advantage as distinct path (CPT codes, Medicare policies).
Phase 16.2: Payer suppression rules + cost-share notes.
"""


def get_payer_context(patient_data: dict) -> dict:
    """
    Determine payer-specific billing context from patient data.

    Parameters
    ----------
    patient_data : dict
        Must contain at minimum:
        - ``insurer_type``: one of "medicare", "medicare_advantage",
          "medicaid", "commercial", "unknown"
        - ``age`` or ``dob``: used for EPSDT / age-gated rules

    Returns
    -------
    dict
        Payer context flags consumed by every detector.
    """
    insurer = (patient_data.get("insurer_type") or "unknown").lower()
    age = patient_data.get("age", 0)

    payer_type = _normalise_payer(insurer)
    is_medicare_traditional = payer_type == "medicare_b"
    is_medicare_advantage = payer_type == "medicare_advantage"
    is_medicare = is_medicare_traditional or is_medicare_advantage
    is_medicaid = payer_type == "medicaid"
    is_commercial = payer_type == "commercial"

    # Phase 16.1: MA uses CPT codes (not G-codes) but follows Medicare coverage
    # Traditional Medicare → G-codes; MA → CPT codes like commercial
    use_g_codes = is_medicare_traditional  # MA does NOT use G-codes

    return {
        # Raw payer classification
        "payer_type": payer_type,

        # Phase 16.1: Medicare Advantage distinction
        "is_medicare_advantage": is_medicare_advantage,

        # Code-selection flags
        "use_g_codes": use_g_codes,
        "use_modifier_33": is_medicaid or is_commercial or is_medicare_advantage,

        # Payer-specific vaccine admin codes
        "admin_codes": _vaccine_admin_codes(is_medicare_traditional),

        # Programme eligibility
        "awv_eligible": is_medicare,  # MA varies by plan — flag for review
        "ccm_eligible": is_medicare or is_commercial,
        "g2211_eligible": is_medicare_traditional,  # Not MA or commercial
        "epsdt_eligible": is_medicaid and age < 21,
        "mandatory_lead_screening": is_medicaid and age <= 6,
        "cocm_eligible": is_medicare or is_commercial,

        # Convenience booleans
        "is_medicare": is_medicare,
        "is_medicare_traditional": is_medicare_traditional,
        "is_medicaid": is_medicaid,
        "is_commercial": is_commercial,

        # Phase 16.2: Suppression + cost-share metadata
        "suppressed_codes": _get_suppressed_codes(payer_type),
        "cost_share_notes": _get_cost_share_notes(payer_type),
    }


# ------------------------------------------------------------------
# Phase 16.2: Payer suppression rules
# ------------------------------------------------------------------

def _get_suppressed_codes(payer_type: str) -> dict:
    """
    Return a dict of opportunity_codes that should be suppressed for this
    payer type. Key = opportunity_code, Value = reason string.

    Suppressed opportunities are still detected but flagged with
    ``payer_uncertain`` instead of being presented as actionable.
    """
    suppressed = {}

    if payer_type == "commercial":
        # Commercial payers rarely cover CCM — flag as uncertain
        suppressed["CCM"] = "payer_uncertain: most commercial plans do not cover CCM"
        suppressed["PCM_PRINCIPAL_CARE"] = "payer_uncertain: commercial PCM coverage rare"

    if payer_type not in ("medicare_b",):
        # G2211 is Medicare Part B only (not MA, not commercial, not Medicaid)
        suppressed["G2211_COMPLEXITY"] = "G2211 is Medicare Part B only"

    if payer_type == "medicare_advantage":
        # MA AWV coverage varies by plan — flag for verification
        suppressed["AWV_FLAG"] = "payer_uncertain: AWV coverage varies by MA plan — verify"

    return suppressed


def _get_cost_share_notes(payer_type: str) -> dict:
    """
    Return cost-share guidance strings keyed by opportunity_code.
    Displayed on opportunity cards to help providers inform patients.
    """
    notes = {}

    if payer_type in ("medicare_b", "medicare_advantage"):
        notes["AWV_FLAG"] = "No copay for this service (Medicare AWV)"
        notes["AWV_INITIAL"] = "No copay for this service (Medicare AWV)"
        notes["AWV_SUBSEQUENT"] = "No copay for this service (Medicare AWV)"
        notes["G0402_IPPE"] = "No copay for this service (Welcome to Medicare visit)"
        notes["TOBACCO_SCREEN"] = "No copay — Medicare preventive benefit"
        notes["ALCOHOL_SCREEN"] = "No copay — Medicare preventive benefit"

    if payer_type in ("medicaid", "commercial"):
        # Preventive services with modifier 33 → cost-share waived for ACA plans
        for code in ("TOBACCO_SCREEN", "ALCOHOL_SCREEN", "DEPRESSION_SCREEN",
                     "COGNITIVE_SCREEN", "OBESITY_SCREEN", "STI_SCREEN",
                     "SDOH_SCREEN"):
            notes[code] = "No copay with modifier 33 (ACA preventive benefit)"

    return notes


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _normalise_payer(raw: str) -> str:
    """Map raw insurer_type strings to a canonical payer bucket."""
    mapping = {
        "medicare": "medicare_b",
        "medicare_b": "medicare_b",
        "medicare_advantage": "medicare_advantage",
        "ma": "medicare_advantage",
        "medicaid": "medicaid",
        "commercial": "commercial",
    }
    return mapping.get(raw, "commercial")  # default unknown → commercial


def _vaccine_admin_codes(is_medicare_traditional: bool) -> dict:
    """
    Return payer-specific vaccine administration codes.

    Traditional Medicare Part B uses G-codes for certain vaccines
    (flu/pneumo/hepB). MA and all other payers use standard 90471/90472.
    """
    if is_medicare_traditional:
        return {
            "flu_admin": "G0008",
            "pneumo_admin": "G0009",
            "hepb_admin": "G0010",
            "standard_first": "90471",
            "standard_additional": "90472",
        }
    return {
        "flu_admin": "90471",
        "pneumo_admin": "90471",
        "hepb_admin": "90471",
        "standard_first": "90471",
        "standard_additional": "90472",
    }

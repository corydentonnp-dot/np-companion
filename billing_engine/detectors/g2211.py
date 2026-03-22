"""
CareCompanion — G2211 Complexity Add-On Detector
billing_engine/detectors/g2211.py

G2211: established Medicare patients with serious/complex conditions
where the provider serves as the focal point of longitudinal care.
"""

from billing_engine.base import BaseDetector
from billing_engine.shared import (
    hash_mrn, count_chronic_conditions, get_chronic_condition_names,
)


class G2211Detector(BaseDetector):
    """G2211 complexity add-on detector."""

    CATEGORY = "g2211"
    DESCRIPTION = "G2211 complexity add-on for established Medicare patients"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        if (pd.get("prior_encounters_count") or 0) < 1:
            return []

        insurer = pd.get("insurer_type") or "unknown"
        if insurer == "medicaid":
            return []

        diagnoses = pd.get("diagnoses") or []
        chronic_count = count_chronic_conditions(diagnoses)
        if chronic_count < 1:
            return []

        visit_type = pd.get("visit_type") or ""
        if "awv" in visit_type.lower() or "wellness" in visit_type.lower():
            return []

        chronic_names = get_chronic_condition_names(diagnoses)
        eligibility = (
            f"Established patient with {chronic_count} chronic condition(s): "
            f"{', '.join(chronic_names[:2])}. "
            "Provider serves as longitudinal care focal point."
        )

        est_revenue = self._get_rate("G2211")
        insurer_caveat = None
        if insurer == "commercial":
            insurer_caveat = "G2211 add-on may not be covered by all commercial plans — verify with payer."

        mrn_hash = hash_mrn(pd.get("mrn") or "")
        opp = self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="G2211",
            codes=["G2211"],
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=(
                "In Assessment/Plan: document longitudinal care relationship. "
                "Note that you are the patient's primary focal point for serious/complex condition management."
            ),
            confidence_level="HIGH" if chronic_count >= 2 else "MEDIUM",
            insurer_caveat=insurer_caveat,
            insurer_type=insurer,
        )
        return [opp]

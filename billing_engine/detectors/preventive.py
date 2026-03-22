"""
CareCompanion — Preventive E&M Detector
billing_engine/detectors/preventive.py

Preventive visit codes (99381-99397) for commercial/Medicaid patients.
Medicare patients use AWV codes instead.  Age-band code selection.
"""

from app.api_config import PREVENTIVE_AGE_BANDS_NEW, PREVENTIVE_AGE_BANDS_ESTABLISHED
from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn


class PreventiveDetector(BaseDetector):
    """Preventive E&M (commercial / Medicaid) detector."""

    CATEGORY = "preventive_visit"
    DESCRIPTION = "Preventive visit codes for commercial/Medicaid patients"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        insurer = pd.get("insurer_type") or "unknown"
        if insurer in ("medicare", "unknown"):
            return []

        visit_type = pd.get("visit_type") or ""
        if "preventive" not in visit_type.lower() and "physical" not in visit_type.lower():
            return []

        patient_age = pd.get("patient_age") or 0
        is_new = (pd.get("prior_encounters_count") or 0) < 1

        age_bands = PREVENTIVE_AGE_BANDS_NEW if is_new else PREVENTIVE_AGE_BANDS_ESTABLISHED
        code = None
        for min_age, max_age, c in age_bands:
            if min_age <= patient_age <= max_age:
                code = c
                break

        if not code:
            return []

        est_revenue = self._get_rate(code)
        patient_type = "new" if is_new else "established"

        eligibility = (
            f"Preventive visit for {patient_type} patient age {patient_age}. "
            f"Commercial/Medicaid — use {code} instead of Medicare AWV codes."
        )

        mrn_hash = hash_mrn(pd.get("mrn") or "")
        opp = self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="preventive_em",
            codes=[code],
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=(
                "Comprehensive preventive examination. "
                "Age-appropriate counseling and screening discussed. "
                "Anticipatory guidance provided. "
                "Document comprehensive ROS and complete physical exam per age band."
            ),
            confidence_level="HIGH",
            insurer_caveat=(
                "Preventive visit codes are covered by ACA-compliant plans. "
                "If significant problem is addressed, consider adding E&M with modifier -25."
            ),
            insurer_type=insurer,
        )
        return [opp]

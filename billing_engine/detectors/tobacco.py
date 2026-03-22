"""
CareCompanion — Tobacco Cessation Detector
billing_engine/detectors/tobacco.py

Tobacco cessation counseling — 99406 (3-10 min), 99407 (>10 min).
Billable at every visit when patient has active tobacco/nicotine diagnosis.
"""

from app.api_config import TOBACCO_CONDITION_PREFIXES
from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn, has_qualifying_dx


class TobaccoDetector(BaseDetector):
    """Tobacco cessation counseling detector."""

    CATEGORY = "tobacco_cessation"
    DESCRIPTION = "Tobacco cessation counseling for active tobacco/nicotine Dx"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        diagnoses = pd.get("diagnoses") or []
        tobacco_dx = has_qualifying_dx(diagnoses, "tobacco", TOBACCO_CONDITION_PREFIXES)
        if not tobacco_dx:
            return []

        dx_names = [d.get("diagnosis_name") or d.get("icd10_code") for d in tobacco_dx[:2]]

        codes = ["99406", "99407"]
        est_revenue = self._get_rate("99407")

        eligibility = (
            f"Active tobacco/nicotine diagnosis: {', '.join(dx_names)}. "
            "Tobacco cessation counseling is billable at every visit."
        )

        insurer = pd.get("insurer_type") or "unknown"
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        opp = self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="tobacco_cessation",
            codes=codes,
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=(
                "Document: tobacco cessation counseling performed. "
                "Duration: [X] min. Discussed risks, benefits of cessation, "
                "pharmacotherapy options (NRT, bupropion, varenicline). "
                "99406 = 3-10 min, 99407 = >10 min."
            ),
            confidence_level="HIGH",
            insurer_caveat=None,
            insurer_type=insurer,
        )
        return [opp]

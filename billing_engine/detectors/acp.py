"""
CareCompanion — Advance Care Planning Detector
billing_engine/detectors/acp.py

ACP standalone (99497/99498) — NOT during AWV (AWV stack already includes
99497).  Triggered for age 65+ or serious illness.
"""

from app.api_config import SERIOUS_ILLNESS_PREFIXES
from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn, has_qualifying_dx


class ACPDetector(BaseDetector):
    """Advance Care Planning standalone detector."""

    CATEGORY = "acp_standalone"
    DESCRIPTION = "ACP standalone for age 65+ or serious illness (non-AWV)"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        visit_type = pd.get("visit_type") or ""
        if "awv" in visit_type.lower() or "wellness" in visit_type.lower():
            return []

        patient_age = pd.get("patient_age") or 0
        diagnoses = pd.get("diagnoses") or []

        serious_illness = has_qualifying_dx(diagnoses, "serious_illness", SERIOUS_ILLNESS_PREFIXES)

        if patient_age < 65 and not serious_illness:
            return []

        reasons = []
        if patient_age >= 65:
            reasons.append(f"Age {patient_age}")
        if serious_illness:
            dx_names = [d.get("diagnosis_name") or d.get("icd10_code") for d in serious_illness[:2]]
            reasons.append(f"Serious illness: {', '.join(dx_names)}")

        codes = ["99497"]
        est_revenue = self._get_rate("99497")

        eligibility = (
            f"ACP candidate: {'; '.join(reasons)}. "
            "Advance care planning discussion billable as standalone service."
        )

        insurer = pd.get("insurer_type") or "unknown"
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        opp = self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="acp_standalone",
            codes=codes,
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=(
                "Face-to-face ACP discussion with patient and/or surrogate. "
                "Document: goals of care, healthcare proxy designation, "
                "code status review, hospice eligibility (if applicable). "
                "Duration: [X] min. 99497 = first 16-30 min. "
                "99498 = each additional 30 min. "
                "Use modifier -33 for Medicare (no patient copay)."
            ),
            confidence_level="HIGH" if serious_illness else "MEDIUM",
            insurer_caveat=(
                "ACP is a Medicare benefit with no copay (modifier -33). "
                "Commercial coverage varies."
                if insurer == "commercial" else None
            ),
            insurer_type=insurer,
        )
        return [opp]

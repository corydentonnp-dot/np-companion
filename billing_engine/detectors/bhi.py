"""
CareCompanion — BHI Detector
billing_engine/detectors/bhi.py

Behavioral Health Integration — 99484.
Requires behavioral health diagnosis and 20+ minutes of care management.
"""

from app.api_config import BHI_CONDITION_PREFIXES
from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn, has_qualifying_dx


class BHIDetector(BaseDetector):
    """Behavioral Health Integration (BHI) detector."""

    CATEGORY = "bhi"
    DESCRIPTION = "BHI monthly billing for behavioral health integration"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        diagnoses = pd.get("diagnoses") or []
        bhi_dx = has_qualifying_dx(diagnoses, "bhi", BHI_CONDITION_PREFIXES)

        if not bhi_dx:
            return []

        bhi_minutes = pd.get("behavioral_dx_minutes") or 0
        dx_names = [d.get("diagnosis_name") or d.get("icd10_code") for d in bhi_dx[:2]]

        eligibility = (
            f"Behavioral health diagnosis: {', '.join(dx_names)}. "
            + (f"Accrued {bhi_minutes} BHI care management minutes this month." if bhi_minutes else
               "BHI eligible — track care management time to meet 20-min threshold.")
        )

        est_revenue = self._get_rate("99484") if bhi_minutes >= 20 else 0.0

        insurer = pd.get("insurer_type") or "unknown"
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        opp = self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="BHI",
            codes=["99484"],
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=(
                "Document 20+ minutes of behavioral health care management activities per month. "
                "Activities include: monitoring symptoms, coordinating with BH specialists, "
                "patient/caregiver education, medication management, care planning. "
                "Billing staff or clinical staff under supervision may provide services."
            ),
            confidence_level="HIGH" if bhi_minutes >= 20 else "MEDIUM",
            insurer_caveat=None,
            insurer_type=insurer,
        )
        return [opp]

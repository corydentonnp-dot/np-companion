"""
CareCompanion — Prolonged Service Detector
billing_engine/detectors/prolonged.py

99417: each 15-minute increment beyond max time for 99214 (40 min)
or 99215 (55 min).
"""

from app.api_config import PROLONGED_SERVICE_THRESHOLDS
from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn


class ProlongedServiceDetector(BaseDetector):
    """Prolonged service (99417) detector."""

    CATEGORY = "prolonged_service"
    DESCRIPTION = "99417 prolonged service for visits exceeding E/M time thresholds"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        f2f_minutes = pd.get("face_to_face_minutes") or 0
        if f2f_minutes <= 0:
            return []

        eligible_base = None
        for base_code, threshold in PROLONGED_SERVICE_THRESHOLDS.items():
            if f2f_minutes >= threshold:
                eligible_base = base_code

        if not eligible_base:
            return []

        threshold = PROLONGED_SERVICE_THRESHOLDS[eligible_base]
        extra_minutes = f2f_minutes - (threshold - 15)
        units = max(1, extra_minutes // 15)
        est_revenue = self._get_rate("99417") * units

        eligibility = (
            f"Visit time {f2f_minutes} minutes. "
            f"Exceeds {eligible_base} maximum by {f2f_minutes - (threshold - 15)} minutes. "
            f"Eligible for {units} unit(s) of 99417."
        )

        insurer = pd.get("insurer_type") or "unknown"
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        opp = self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="99417",
            codes=["99417"],
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=(
                f"Document total visit time of {f2f_minutes} minutes. "
                f"Note that time exceeded maximum for {eligible_base}. "
                f"Bill 99417 x {units} in addition to the primary E&M code."
            ),
            confidence_level="HIGH",
            insurer_caveat=None,
            insurer_type=insurer,
        )
        return [opp]

"""
CareCompanion — RPM Detector
billing_engine/detectors/rpm.py

Remote Patient Monitoring — 99453, 99454, 99457, 99458.
Flagged as programme-level opportunity requiring practice infrastructure.
"""

from app.api_config import RPM_CONDITION_PREFIXES
from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn, has_qualifying_dx


class RPMDetector(BaseDetector):
    """Remote Patient Monitoring (RPM) detector."""

    CATEGORY = "rpm"
    DESCRIPTION = "RPM programme-level billing for remote physiologic monitoring"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        diagnoses = pd.get("diagnoses") or []
        rpm_eligible_dx = has_qualifying_dx(diagnoses, "rpm", RPM_CONDITION_PREFIXES,
                                            exclude_resolved=False)

        if not rpm_eligible_dx:
            return []

        rpm_enrolled = pd.get("rpm_enrolled") or False
        dx_names = [d.get("diagnosis_name") or d.get("icd10_code") for d in rpm_eligible_dx[:2]]

        if rpm_enrolled:
            codes = ["99457"]
            est_revenue = self._get_rate("99457")
            eligibility = f"RPM enrolled. Conditions: {', '.join(dx_names)}. Bill monthly monitoring."
            confidence = "HIGH"
        else:
            codes = ["99453", "99454", "99457"]
            est_revenue = self._get_rate("99453")
            eligibility = (
                f"RPM-eligible conditions: {', '.join(dx_names)}. "
                "Patient not currently enrolled — program enrollment opportunity."
            )
            confidence = "LOW"

        insurer = pd.get("insurer_type") or "unknown"
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        opp = self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="RPM",
            codes=codes,
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=(
                "RPM requires: (1) Physician order for device. "
                "(2) Patient consent and device education (99453 — one time). "
                "(3) Device supplies with 16+ days of data transmission per month (99454). "
                "(4) 20+ minutes of monitoring and management per month (99457). "
                "NOTE: RPM requires practice-level device program infrastructure."
            ),
            confidence_level=confidence,
            insurer_caveat=(
                "RPM coverage varies by payer. Verify benefits before enrollment."
                if insurer in ("commercial", "medicaid") else None
            ),
            insurer_type=insurer,
        )
        return [opp]

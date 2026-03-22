"""
CareCompanion — Obesity/Nutrition Detector
billing_engine/detectors/obesity.py

Obesity intensive behavioral therapy (G0447, Medicare) and medical
nutrition therapy (97802/97803).  Triggered by BMI >=30 or diabetes.
"""

from app.api_config import OBESITY_CONDITION_PREFIXES
from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn, has_qualifying_dx


class ObesityDetector(BaseDetector):
    """Obesity / nutrition counseling detector."""

    CATEGORY = "obesity_nutrition"
    DESCRIPTION = "Obesity counseling and medical nutrition therapy"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        diagnoses = pd.get("diagnoses") or []
        obesity_dx = has_qualifying_dx(diagnoses, "obesity", OBESITY_CONDITION_PREFIXES)

        if not obesity_dx:
            return []

        dx_names = [d.get("diagnosis_name") or d.get("icd10_code") for d in obesity_dx[:2]]
        insurer = pd.get("insurer_type") or "unknown"

        if insurer in ("medicare", "unknown"):
            codes = ["G0447"]
            est_revenue = self._get_rate("G0447")
            has_diabetes = any(
                (d.get("icd10_code") or "").upper().startswith(("E10", "E11", "E13"))
                for d in diagnoses
            )
            if has_diabetes:
                codes.append("97802")
                est_revenue += self._get_rate("97802")
        else:
            codes = ["97802"]
            est_revenue = self._get_rate("97802")

        eligibility = (
            f"Qualifying diagnosis: {', '.join(dx_names)}. "
            "Obesity counseling / medical nutrition therapy billable."
        )

        mrn_hash = hash_mrn(pd.get("mrn") or "")
        opp = self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="obesity_nutrition",
            codes=codes,
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=(
                "Document: obesity counseling / MNT provided. "
                "Dietary modifications, exercise prescription, behavioral strategies discussed. "
                "Duration: [X] min. BMI: [X]. "
                "G0447 = Medicare intensive behavioral therapy 15 min. "
                "97802 = MNT initial 15 min. 97803 = MNT follow-up 15 min."
            ),
            confidence_level="HIGH",
            insurer_caveat=(
                "G0447 is Medicare-specific. Commercial payers: use 97802/97803 MNT codes."
                if insurer == "commercial" else None
            ),
            insurer_type=insurer,
        )
        return [opp]

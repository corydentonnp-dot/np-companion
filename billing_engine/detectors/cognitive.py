"""
CareCompanion — Cognitive Assessment Detector
billing_engine/detectors/cognitive.py

Comprehensive cognitive assessment (99483) — one of the highest-value
single codes (~$257).  Triggered for patients 65+ with dementia,
cognitive complaints, or fall history.
"""

from app.api_config import COGNITIVE_CONDITION_PREFIXES
from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn, has_qualifying_dx


class CognitiveDetector(BaseDetector):
    """Cognitive assessment (99483) detector."""

    CATEGORY = "cognitive_assessment"
    DESCRIPTION = "99483 comprehensive cognitive assessment for age 65+ with risk factors"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        patient_age = pd.get("patient_age") or 0
        if patient_age < 65:
            return []

        diagnoses = pd.get("diagnoses") or []
        cognitive_dx = has_qualifying_dx(diagnoses, "cognitive", COGNITIVE_CONDITION_PREFIXES)

        has_fall_history = any(
            (d.get("icd10_code") or "").upper().startswith("W")
            or (d.get("icd10_code") or "").upper().startswith("R26")
            for d in diagnoses
        )

        if not cognitive_dx and not has_fall_history:
            return []

        dx_names = [d.get("diagnosis_name") or d.get("icd10_code") for d in cognitive_dx[:2]]
        trigger_reason = ", ".join(dx_names) if dx_names else "Fall history / gait abnormality"

        eligibility = (
            f"Patient age {patient_age}, risk indicators: {trigger_reason}. "
            "99483 covers comprehensive cognitive assessment and care planning."
        )

        insurer = pd.get("insurer_type") or "unknown"
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        opp = self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="cognitive_assessment",
            codes=["99483"],
            est_revenue=self._get_rate("99483"),
            eligibility_basis=eligibility,
            documentation_required=(
                "Comprehensive cognitive assessment must include: "
                "(1) Cognition-focused history with patient and informant. "
                "(2) Standardized cognitive testing (MoCA, MMSE, or SLUMS). "
                "(3) Functional assessment (ADLs/IADLs). "
                "(4) Medication review for cognitive effects. "
                "(5) Safety evaluation. (6) Caregiver needs assessment. "
                "(7) Written care plan with community resource referrals."
            ),
            confidence_level="HIGH" if cognitive_dx else "MEDIUM",
            insurer_caveat=(
                "99483 is primarily a Medicare code. Verify coverage with commercial payers."
                if insurer == "commercial" else None
            ),
            insurer_type=insurer,
        )
        return [opp]

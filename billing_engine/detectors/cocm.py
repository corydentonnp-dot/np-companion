"""
CareCompanion — CoCM Detector
billing_engine/detectors/cocm.py

Collaborative Care Model — 99492 (initial month), 99493 (subsequent),
99494 (additional 30 min add-on).  Phase 19C.2.

CRITICAL: Cannot bill CoCM same month as 99484 (BHI).
Only available if practice has CoCM infrastructure (BH care manager +
psychiatric consultant on staff).
"""

from app.api_config import BHI_CONDITION_PREFIXES
from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn, has_qualifying_dx


class CoCMDetector(BaseDetector):
    """Collaborative Care Model (CoCM) detector."""

    CATEGORY = "cocm"
    DESCRIPTION = "CoCM codes for collaborative care with BH care manager"

    def detect(self, patient_data, payer_context):
        pd = patient_data

        # Infrastructure gate: practice must have CoCM infrastructure
        practice = pd.get("practice") or {}
        if not practice.get("has_cocm_infrastructure"):
            return []

        # Payer gate: CoCM only for Medicare and some commercial
        if not payer_context.get("cocm_eligible"):
            return []

        # Patient must have qualifying behavioral health diagnosis
        diagnoses = pd.get("diagnoses") or []
        bhi_dx = has_qualifying_dx(diagnoses, "bhi", BHI_CONDITION_PREFIXES)
        if not bhi_dx:
            return []

        # Mutual exclusion: if BHI (99484) is already being billed this month,
        # skip CoCM. The patient_data can carry a flag indicating BHI billing.
        if pd.get("bhi_billed_this_month"):
            return []

        cocm_minutes = pd.get("cocm_minutes_this_month") or 0
        is_initial_month = pd.get("cocm_initial_month") or False

        if cocm_minutes < 36:
            # Below threshold — still flag as opportunity
            code = "99492" if is_initial_month else "99493"
            est_revenue = 0.0  # Not yet billable
            confidence = "LOW"
            status_note = f"Accrued {cocm_minutes}/36 min — track time to reach threshold."
        else:
            if is_initial_month:
                code = "99492"
            else:
                code = "99493"
            est_revenue = self._get_rate(code)
            confidence = "HIGH"
            status_note = f"CoCM threshold met: {cocm_minutes} min this month."

        codes = [code]

        # Additional 30 min add-on
        if cocm_minutes >= 66:
            codes.append("99494")
            est_revenue += self._get_rate("99494")

        dx_names = [d.get("diagnosis_name") or d.get("icd10_code") for d in bhi_dx[:2]]
        eligibility = (
            f"Behavioral health Dx: {', '.join(dx_names)}. "
            f"{status_note} "
            "CoCM requires BH care manager + psychiatric consultant. "
            "Cannot bill BHI (99484) in the same month."
        )

        insurer = pd.get("insurer_type") or "unknown"
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        opp = self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="CoCM",
            codes=codes,
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=(
                "Document BH care manager activities and time. "
                "Document psychiatric consultant review and recommendations. "
                "Track total collaborative care team time (36+ min threshold). "
                "Cannot bill 99484 (BHI) in the same month as CoCM."
            ),
            confidence_level=confidence,
            insurer_caveat="Verify CoCM coverage with payer. Medicare covers; commercial varies.",
            insurer_type=insurer,
            opportunity_code="COCM_INITIAL" if is_initial_month else "COCM_SUBSEQUENT",
            priority="high",
            documentation_checklist='["Verify BH care manager documented activities","Verify psychiatric consultant review","Track total team time (36+ min)","Confirm no BHI (99484) billed this month","Document patient progress and treatment plan updates"]',
        )
        return [opp]

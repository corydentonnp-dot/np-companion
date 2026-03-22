"""
CareCompanion — E&M Add-Ons Detector
billing_engine/detectors/em_addons.py

Modifier -25 prompting for significant separately identifiable E/M
when a procedure or preventive service is also performed.  Phase 19B.5.
"""

from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn


class EMAddonsDetector(BaseDetector):
    """E/M add-on modifier -25 prompting detector."""

    CATEGORY = "em_addons"
    DESCRIPTION = "Modifier -25 prompting when procedure + E/M on same visit"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        visit_type = (pd.get("visit_type") or "").lower()
        em_code = pd.get("em_code_today") or ""
        procedures_today = pd.get("procedures_performed_today") or []
        preventive_today = pd.get("preventive_service_today") or False

        # Modifier -25 is relevant when BOTH an E/M and a procedure/preventive
        # service are performed during the same encounter
        if not em_code:
            return []
        if not procedures_today and not preventive_today:
            return []

        mrn_hash = hash_mrn(pd.get("mrn") or "")
        insurer = pd.get("insurer_type") or "unknown"

        proc_list = ", ".join(str(p) for p in procedures_today[:4]) if procedures_today else "preventive service"
        est_revenue = self._get_rate(em_code) if em_code else 0

        opp = self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="em_addon",
            codes=[em_code, "-25"],
            est_revenue=est_revenue,
            eligibility_basis=(
                f"Same-day E/M ({em_code}) + procedure/preventive ({proc_list}). "
                "Append modifier -25 to E/M for full separate reimbursement."
            ),
            documentation_required=(
                "Separate and distinct E/M service. "
                "Problem-focused HPI for [distinct problem]. "
                "Exam: [distinct exam findings]. MDM: [decision complexity]. "
                "This E/M is separate from the [procedure/preventive service] "
                "and addresses a distinct clinical issue."
            ),
            confidence_level="MEDIUM",
            insurer_caveat="Payer may audit modifier -25 claims; ensure documentation clearly supports separate E/M.",
            insurer_type=insurer,
            opportunity_code="MODIFIER_25_PROMPT",
            priority="medium",
            documentation_checklist='["Document distinct chief complaint for E/M","Document separate HPI","Document separate exam findings","Document MDM complexity","Add modifier -25 to E/M code"]',
        )
        return [opp]

"""
CareCompanion — SDOH Detector
billing_engine/detectors/sdoh.py

IPV screening for women of reproductive age at preventive visits (coding support).
HRA compliance checker: verifies Health Risk Assessment completed for AWV.
Phase 19C.5.
"""

from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn


class SDOHDetector(BaseDetector):
    """Social Determinants of Health screening detector."""

    CATEGORY = "sdoh"
    DESCRIPTION = "IPV screening, HRA compliance checker"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        opps = []
        insurer = pd.get("insurer_type") or "unknown"
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        age = pd.get("age") or 0
        sex = (pd.get("sex") or pd.get("gender") or "").lower()
        visit_type = (pd.get("visit_type") or "").lower()

        # ── SDOH_IPV — IPV screening for women of reproductive age at preventive visits ──
        if sex in ("f", "female") and 14 <= age <= 46:
            if visit_type in ("preventive", "well_woman", "annual", "awv"):
                from billing_engine.shared import months_since
                last_ipv = pd.get("last_ipv_screening_date")
                if not last_ipv or months_since(last_ipv) >= 12:
                    opps.append(self._make_opportunity(
                        mrn_hash=mrn_hash,
                        user_id=pd.get("user_id"),
                        visit_date=pd.get("visit_date"),
                        opportunity_type="sdoh",
                        codes=["99420"],
                        est_revenue=0.0,  # Coding support, not separately billable
                        eligibility_basis="Female reproductive age at preventive visit. IPV screening recommended per USPSTF.",
                        documentation_required=(
                            "Screen for intimate partner violence using validated tool. "
                            "Document screening result. Provide resources if positive."
                        ),
                        confidence_level="LOW",
                        insurer_caveat="Coding support — not separately billable but supports quality measures.",
                        insurer_type=insurer,
                        opportunity_code="SDOH_IPV",
                        priority="low",
                        documentation_checklist='["Administer IPV screening tool","Document screening result","Provide resources/referral if positive"]',
                    ))

        # ── SDOH_HRA — HRA compliance checker for AWV ──
        awv_today = pd.get("awv_scheduled_today") or False
        hra_completed = pd.get("hra_completed_today") or False
        if awv_today and not hra_completed:
            opps.append(self._make_opportunity(
                mrn_hash=mrn_hash,
                user_id=pd.get("user_id"),
                visit_date=pd.get("visit_date"),
                opportunity_type="sdoh",
                codes=["G0136"],
                est_revenue=0.0,  # Already counted in AWV stack; this is compliance verification
                eligibility_basis="AWV scheduled today but HRA not yet completed. G0136 requires completed SDOH screening.",
                documentation_required=(
                    "Complete Health Risk Assessment before AWV visit. "
                    "G0136 (SDOH screening) requires completed instrument and results documentation."
                ),
                confidence_level="HIGH",
                insurer_caveat="Required CMS documentation — AWV may be incomplete without HRA.",
                insurer_type=insurer,
                opportunity_code="SDOH_HRA",
                priority="high",
                documentation_checklist='["Verify HRA instrument completed by patient","Review HRA results","Document SDOH findings in chart","Address identified social needs"]',
            ))

        return opps

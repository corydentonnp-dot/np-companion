"""
CareCompanion — CCM / PCM Detector
billing_engine/detectors/ccm.py

Chronic Care Management (CCM) — 99490, 99439, 99487, 99489.
Patient must have 2+ chronic conditions from the CMS list.
Monthly billing based on accumulated non-face-to-face minutes.

Principal Care Management (PCM) — 99424, 99425.
Single complex chronic condition; alternative to CCM for patients who
don't meet the 2-condition threshold.  Cannot bill both PCM and CCM
in the same month.
"""

from billing_engine.base import BaseDetector
from billing_engine.shared import (
    hash_mrn, count_chronic_conditions, get_chronic_condition_names,
)


class CCMDetector(BaseDetector):
    """Chronic Care Management (CCM) and Principal Care Management (PCM) detector."""

    CATEGORY = "ccm"
    DESCRIPTION = "CCM monthly billing for 2+ chronic conditions; PCM for 1 complex condition"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        diagnoses = pd.get("diagnoses") or []
        active_chronic = count_chronic_conditions(diagnoses)
        minutes = pd.get("ccm_minutes_this_month") or 0

        # ── PCM path: exactly 1 complex chronic condition ──
        if active_chronic == 1:
            return self._detect_pcm(pd, diagnoses, minutes)

        if active_chronic < 2:
            return []

        # ── CCM path: 2+ chronic conditions ──
        if minutes >= 60:
            codes = ["99487"]
            if minutes >= 90:
                codes.append("99489")
            est_revenue = self._get_rate("99487") + (self._get_rate("99489") if minutes >= 90 else 0)
        elif minutes >= 40:
            codes = ["99490", "99439"]
            est_revenue = self._get_rate("99490") + self._get_rate("99439")
        elif minutes >= 20:
            codes = ["99490"]
            est_revenue = self._get_rate("99490")
        else:
            codes = ["99490"]
            est_revenue = self._get_rate("99490")

        chronic_conditions = get_chronic_condition_names(diagnoses)
        eligibility = (
            f"Patient has {active_chronic} chronic conditions: "
            f"{', '.join(chronic_conditions[:3])}"
            + (" and more" if active_chronic > 3 else "")
        )
        if minutes > 0:
            eligibility += f". Accrued {minutes} non-F2F minutes this month."

        doc_required = (
            "Comprehensive care plan in chart. "
            "Patient consent on file. "
            "Document all time spent on care coordination. "
            "Provide copy of care plan to patient."
        )

        insurer = pd.get("insurer_type") or "unknown"
        insurer_caveat = None
        if insurer == "medicaid":
            insurer_caveat = "Verify CCM coverage and requirements with Virginia Medicaid/managed care plan."
        elif insurer == "commercial":
            insurer_caveat = "Verify CCM coverage with commercial payer — requirements vary."

        mrn_hash = hash_mrn(pd.get("mrn") or "")
        opp = self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="CCM",
            codes=codes,
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=doc_required,
            confidence_level="HIGH" if active_chronic >= 3 else "MEDIUM",
            insurer_caveat=insurer_caveat,
            insurer_type=insurer,
        )
        return [opp]

    # ------------------------------------------------------------------
    # PCM alternative (Phase 19B.4)
    # ------------------------------------------------------------------

    def _detect_pcm(self, pd, diagnoses, minutes):
        """Suggest PCM (99424/99425) for a single complex chronic condition."""
        chronic_names = get_chronic_condition_names(diagnoses)
        if not chronic_names:
            return []

        condition_name = chronic_names[0]

        codes = ["99424"]
        est_revenue = self._get_rate("99424")
        if minutes >= 60:
            codes.append("99425")
            est_revenue += self._get_rate("99425")

        eligibility = (
            f"Patient has 1 complex chronic condition: {condition_name}. "
            "Eligible for Principal Care Management (PCM) — alternative to CCM. "
            "Cannot bill both PCM and CCM in the same month."
        )
        if minutes > 0:
            eligibility += f" Accrued {minutes} non-F2F minutes this month."

        insurer = pd.get("insurer_type") or "unknown"
        insurer_caveat = None
        if insurer == "medicaid":
            insurer_caveat = "Verify PCM coverage with state Medicaid plan."
        elif insurer == "commercial":
            insurer_caveat = "Many commercial payers cover PCM; verify specific plan."

        mrn_hash = hash_mrn(pd.get("mrn") or "")
        opp = self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="PCM",
            codes=codes,
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=(
                "Document single principal complex condition. "
                "Care plan addressing that condition. "
                "Patient consent on file. "
                "Document all time spent on care management. "
                "Cannot bill CCM in the same month."
            ),
            confidence_level="MEDIUM",
            insurer_caveat=insurer_caveat,
            insurer_type=insurer,
            opportunity_code="PCM_PRINCIPAL_CARE",
            priority="medium",
            documentation_checklist='["Identify single complex chronic condition","Create condition-specific care plan","Obtain patient consent","Track monthly non-F2F time","Verify no CCM billed same month"]',
        )
        return [opp]

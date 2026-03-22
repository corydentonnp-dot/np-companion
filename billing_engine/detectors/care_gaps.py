"""
CareCompanion — Care Gaps Detector
billing_engine/detectors/care_gaps.py

Bridges the care gap engine (agent/caregap_engine.py) results into billing
opportunities.  Each open care gap with a billing_code_pair becomes its
own BillingOpportunity so the provider can act on them individually.
"""

from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn


class CareGapsDetector(BaseDetector):
    """Care gap screenings / vaccines bridge detector."""

    CATEGORY = "care_gap_screenings"
    DESCRIPTION = "Bridge care gap engine results into billing opportunities"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        open_gaps = pd.get("open_care_gaps") or []
        if not open_gaps:
            return []

        insurer = pd.get("insurer_type") or "unknown"
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        user_id = pd.get("user_id")
        visit_date = pd.get("visit_date")

        opportunities = []
        for gap in open_gaps:
            billing_codes_raw = gap.get("billing_code_pair") or ""
            if not billing_codes_raw:
                continue

            codes = [c.strip() for c in billing_codes_raw.replace("/", ",").split(",") if c.strip()]
            if not codes:
                continue

            est_revenue = sum(self._get_rate(c) for c in codes)
            gap_type = gap.get("gap_type") or "screening"
            gap_name = gap.get("gap_name") or gap_type
            doc_template = gap.get("documentation_template") or ""

            eligibility = f"Care gap detected: {gap_name}. Screening/vaccine is overdue per USPSTF guidelines."

            insurer_caveat = None
            if insurer == "commercial":
                insurer_caveat = (
                    "Preventive screening coverage varies by plan. "
                    "ACA-compliant plans must cover USPSTF A/B recommendations at no cost-sharing."
                )

            opp = self._make_opportunity(
                mrn_hash=mrn_hash,
                user_id=user_id,
                visit_date=visit_date,
                opportunity_type=gap_type,
                codes=codes,
                est_revenue=est_revenue,
                eligibility_basis=eligibility,
                documentation_required=doc_template,
                confidence_level="HIGH",
                insurer_caveat=insurer_caveat,
                insurer_type=insurer,
            )
            opportunities.append(opp)

        return opportunities

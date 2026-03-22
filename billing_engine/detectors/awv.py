"""
CareCompanion — AWV Detector
billing_engine/detectors/awv.py

Annual Wellness Visit — G0402 (Welcome to Medicare), G0438 (initial),
G0439 (subsequent) plus 2025 add-on stack (G2211, G0444, 99497, G0136).

Phase 19B.3 enhancements:
- IPPE explicit new-Medicare-patient detection (within first 12mo Part B)
- Prolonged preventive (G0513/G0514) when AWV/IPPE exceeds typical time
- ACP with AWV enhanced prompt (zero cost-share advantage)
- PPPS compliance flag (G0468 required documentation, $0 revenue)
"""

from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn, months_since, count_chronic_conditions


class AWVDetector(BaseDetector):
    """Annual Wellness Visit (AWV) + 2025 add-on stack detector."""

    CATEGORY = "awv"
    DESCRIPTION = "Medicare AWV sequence with 2025 add-on stack"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        insurer = pd.get("insurer_type") or "unknown"

        if insurer not in ("medicare", "unknown"):
            if insurer != "commercial":
                return []

        awv_history = pd.get("awv_history") or {}
        last_awv_date = awv_history.get("last_awv_date")
        medicare_start_date = awv_history.get("medicare_start_date")

        awv_code = None
        awv_reason = ""

        if not last_awv_date:
            if medicare_start_date and months_since(medicare_start_date) <= 12:
                awv_code = "G0402"
                awv_reason = "No prior AWV — within 12 months of Medicare Part B enrollment (IPPE/Welcome to Medicare)"
            else:
                awv_code = "G0438"
                awv_reason = "No prior AWV documented in chart"
        elif months_since(last_awv_date) >= 12:
            awv_code = "G0439"
            awv_reason = f"Last AWV: {last_awv_date} — 12+ months ago"
        else:
            return []

        codes = [awv_code]
        est_revenue = self._get_rate(awv_code)

        diagnoses = pd.get("diagnoses") or []
        has_complex_condition = count_chronic_conditions(diagnoses) >= 1

        # G2211 complexity add-on (established patients with chronic conditions)
        if has_complex_condition:
            codes.append("G2211")
            est_revenue += self._get_rate("G2211")

        # Depression screening (subsequent AWV only)
        if awv_code == "G0439":
            codes.append("G0444")
            est_revenue += self._get_rate("G0444")

        # ACP with AWV — zero cost-share advantage vs standalone ACP
        codes.append("99497")
        est_revenue += self._get_rate("99497")

        # SDOH risk assessment (new 2025)
        codes.append("G0136")
        est_revenue += self._get_rate("G0136")

        # PPPS compliance flag (G0468 — required documentation, $0 revenue)
        codes.append("G0468")
        # No revenue added — this is a compliance requirement, not billable separately

        alcohol_codes_note = "G0442+G0443 (alcohol screening pair) also available if clinically applicable."

        doc_required = (
            f"Document {awv_code} AWV components per CMS requirements. "
            "If billing G2211: document longitudinal care relationship and serious/complex condition. "
            "If billing 99497: document face-to-face ACP discussion, goals of care, duration "
            "(NOTE: zero cost-share when billed WITH AWV — encourage discussion). "
            "If billing G0136: document SDOH screening instrument and results. "
            "If billing G0444 (subsequent AWV only): document depression screening instrument and score. "
            "G0468 (PPPS): auto-flag as required documentation — verify personalized prevention plan is complete. "
            + alcohol_codes_note
        )

        insurer_caveat = None
        if insurer == "commercial":
            insurer_caveat = (
                "AWV codes are Medicare-specific. "
                "For commercial payers use 99381-99397 preventive E&M codes instead."
            )

        opps = []

        mrn_hash = hash_mrn(pd.get("mrn") or "")
        opp = self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="AWV",
            codes=codes,
            est_revenue=est_revenue,
            eligibility_basis=awv_reason,
            documentation_required=doc_required,
            confidence_level="HIGH",
            insurer_caveat=insurer_caveat,
            insurer_type=insurer,
            documentation_checklist='["Complete HRA","Review medications","Update family/social history","Review functional status","Document cognitive assessment","Create personalized prevention plan (G0468)","Discuss advance care planning (99497)","Complete SDOH screening (G0136)"]',
        )
        opps.append(opp)

        # ── Prolonged preventive (G0513/G0514) ──
        awv_minutes = pd.get("awv_minutes_today") or 0
        if awv_minutes > 60:
            prolonged_codes = ["G0513"]
            prolonged_rev = self._get_rate("G0513") if self._get_rate("G0513") else 60.0
            if awv_minutes > 90:
                prolonged_codes.append("G0514")
                prolonged_rev += self._get_rate("G0514") if self._get_rate("G0514") else 60.0

            opps.append(self._make_opportunity(
                mrn_hash=mrn_hash,
                user_id=pd.get("user_id"),
                visit_date=pd.get("visit_date"),
                opportunity_type="AWV_prolonged",
                codes=prolonged_codes,
                est_revenue=prolonged_rev,
                eligibility_basis=f"AWV/IPPE exceeded typical time: {awv_minutes} min (threshold 60 min).",
                documentation_required=(
                    "G0513: first 30 min beyond typical AWV time. "
                    "G0514: each additional 30 min. "
                    "Document total face-to-face time and medical necessity for extended visit."
                ),
                confidence_level="MEDIUM",
                insurer_caveat=None,
                insurer_type=insurer,
                opportunity_code="PROLONGED_PREVENTIVE",
                priority="medium",
                documentation_checklist='["Document total face-to-face time","Document medical necessity for extended visit","Bill G0513 for first 30 min beyond typical"]',
            ))

        return opps

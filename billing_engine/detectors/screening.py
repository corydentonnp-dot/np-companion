"""
CareCompanion — Screening Detector
billing_engine/detectors/screening.py

Developmental screening (96110), expanded substance SBIRT (99408/99409),
maternal depression screening (96127).  Phase 19C.4.
"""

from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn
from app.api_config import DEVELOPMENTAL_SCREENING_MONTHS


class ScreeningDetector(BaseDetector):
    """Expanded screening services detector."""

    CATEGORY = "screening"
    DESCRIPTION = "Developmental, substance SBIRT expansion, maternal depression"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        age = pd.get("age") or 0
        age_months = pd.get("age_months") or (age * 12)
        insurer = pd.get("insurer_type") or "unknown"
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        opps = []

        # ── SCREEN_DEVELOPMENTAL — Pediatric (ASQ-3/M-CHAT at 9/18/24/30mo) ──
        if age_months in DEVELOPMENTAL_SCREENING_MONTHS or (age < 3 and age_months > 0):
            # Check if screening is due at this visit
            due = age_months in DEVELOPMENTAL_SCREENING_MONTHS
            if not due and age < 3:
                # Close enough: within 2 months of a screening age
                for target in DEVELOPMENTAL_SCREENING_MONTHS:
                    if abs(age_months - target) <= 2:
                        due = True
                        break

            if due and not pd.get("developmental_screening_done_today"):
                opps.append(self._build(pd, mrn_hash, insurer,
                    code="96110",
                    opportunity_code="SCREEN_DEVELOPMENTAL",
                    eligibility=f"Child age {age_months} months. Developmental screening due per Bright Futures schedule.",
                    doc="Administer ASQ-3 or M-CHAT screening instrument. Score and document results.",
                    checklist='["Administer age-appropriate screening (ASQ-3/M-CHAT)","Score screening instrument","Document results and discuss with parent","Refer if positive screen"]',
                    priority="medium",
                ))

        # ── SCREEN_SUBSTANCE — Adults 18+, SBIRT model ──
        if age >= 18:
            from billing_engine.shared import months_since
            last_sbirt = pd.get("last_substance_screening_date")
            if not last_sbirt or months_since(last_sbirt) >= 12:
                # Check for substance-related diagnoses to elevate code
                diagnoses = pd.get("diagnoses") or []
                has_substance_dx = any(
                    (d.get("icd10_code") or "").upper().startswith(p)
                    for d in diagnoses
                    for p in ["F10", "F11", "F12", "F13", "F14", "F15", "F16", "F17", "F18", "F19"]
                    if (d.get("status") or "").lower() != "resolved"
                )
                code = "99409" if has_substance_dx else "99408"

                opps.append(self._build(pd, mrn_hash, insurer,
                    code=code,
                    opportunity_code="SCREEN_SUBSTANCE",
                    eligibility="Adult patient, annual substance screening indicated (SBIRT model).",
                    doc=(
                        "Administer validated substance screening instrument (DAST-10/NIDA/AUDIT). "
                        "Document screening, brief intervention, and referral to treatment if indicated."
                    ),
                    checklist='["Administer screening instrument (DAST-10/NIDA/AUDIT)","Score and document results","Provide brief intervention if positive","Refer to treatment if indicated"]',
                    priority="low",
                ))

        # ── SCREEN_MATERNAL_DEPRESSION — Well-baby visits, patient age <12mo ──
        if age_months <= 12 and age_months > 0:
            visit_type = (pd.get("visit_type") or "").lower()
            if visit_type in ("well_child", "well_baby", "preventive"):
                if not pd.get("maternal_depression_screened_today"):
                    opps.append(self._build(pd, mrn_hash, insurer,
                        code="96127",
                        opportunity_code="SCREEN_MATERNAL_DEPRESSION",
                        eligibility="Infant <12mo at well-baby visit. Screen mother for postpartum depression.",
                        doc="Administer Edinburgh/PHQ-9 to mother at well-baby visit. Document score and follow-up plan.",
                        checklist='["Administer Edinburgh or PHQ-9 to mother","Score screening instrument","Document results in infant chart","Refer mother if positive screen"]',
                        priority="medium",
                    ))

        return opps

    def _build(self, pd, mrn_hash, insurer, *, code, opportunity_code,
               eligibility, doc, checklist, priority="medium"):
        return self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="screening",
            codes=[code],
            est_revenue=self._get_rate(code),
            eligibility_basis=eligibility,
            documentation_required=doc,
            confidence_level="MEDIUM",
            insurer_caveat=None,
            insurer_type=insurer,
            opportunity_code=opportunity_code,
            priority=priority,
            documentation_checklist=checklist,
        )

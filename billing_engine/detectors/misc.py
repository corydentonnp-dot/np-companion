"""
CareCompanion — Miscellaneous Detector
billing_engine/detectors/misc.py

After-hours, care plan oversight, PrEP, GDM screening, perinatal depression,
statin therapy counseling, folic acid supplementation.
Phase 19D.2 — 7 rules.
"""

from datetime import datetime

from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn, months_since, has_qualifying_dx


class MiscDetector(BaseDetector):
    """Miscellaneous billing opportunities detector."""

    CATEGORY = "misc"
    DESCRIPTION = "After-hours, care plan oversight, PrEP, GDM, perinatal depression, statin, folic acid"

    # Standard business hours
    _BIZ_START = 8   # 8:00 AM
    _BIZ_END = 17    # 5:00 PM

    def detect(self, patient_data, payer_context):
        pd = patient_data
        opps = []
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        insurer = pd.get("insurer_type") or "unknown"
        age = pd.get("age") or 0
        sex = (pd.get("sex") or pd.get("gender") or "").lower()
        diagnoses = pd.get("diagnoses") or []

        # ── MISC_AFTER_HOURS — encounter outside M-F 8a-5p ──
        encounter_time = pd.get("encounter_datetime") or pd.get("visit_date")
        if encounter_time:
            dt = self._parse_datetime(encounter_time)
            if dt:
                weekday = dt.weekday()  # 0=Monday, 6=Sunday
                hour = dt.hour
                code = None
                if weekday >= 5:  # Saturday or Sunday
                    code = "99051"
                elif hour < self._BIZ_START or hour >= self._BIZ_END:
                    code = "99050"
                if code:
                    opps.append(self._make_opportunity(
                        mrn_hash=mrn_hash,
                        user_id=pd.get("user_id"),
                        visit_date=pd.get("visit_date"),
                        opportunity_type="misc",
                        codes=[code],
                        est_revenue=self._get_rate(code),
                        eligibility_basis=f"Encounter at {dt.strftime('%A %H:%M')} — outside regular business hours.",
                        documentation_required=f"Append after-hours add-on code {code} to encounter claim.",
                        confidence_level="HIGH",
                        insurer_caveat="After-hours codes are add-ons billable with the primary E/M.",
                        insurer_type=insurer,
                        opportunity_code="MISC_AFTER_HOURS",
                        priority="low",
                        documentation_checklist=f'["Document encounter time","Add {code} to claim","Bill with primary E/M code"]',
                    ))

        # ── MISC_CARE_PLAN_OVERSIGHT — home health/hospice patient, ≥15 min/month ──
        in_home_health = pd.get("in_home_health") or pd.get("in_hospice") or False
        if in_home_health:
            oversight_minutes = pd.get("monthly_oversight_minutes") or 0
            last_cpo_billed = pd.get("last_care_plan_oversight_date")
            if oversight_minutes >= 15 and (not last_cpo_billed or months_since(last_cpo_billed) >= 1):
                code = "99340" if oversight_minutes >= 30 else "99339"
                opps.append(self._make_opportunity(
                    mrn_hash=mrn_hash,
                    user_id=pd.get("user_id"),
                    visit_date=pd.get("visit_date"),
                    opportunity_type="misc",
                    codes=[code],
                    est_revenue=self._get_rate(code),
                    eligibility_basis=f"Patient in home health/hospice with {oversight_minutes} min care plan oversight this month.",
                    documentation_required=f"Document {oversight_minutes} min of care plan oversight activities. Bill {code} monthly.",
                    confidence_level="HIGH",
                    insurer_caveat="Requires documentation of time spent reviewing/revising care plan.",
                    insurer_type=insurer,
                    opportunity_code="MISC_CARE_PLAN_OVERSIGHT",
                    priority="medium",
                    documentation_checklist='["Document time spent on oversight","Review and update care plan","Communicate with home health/hospice agency","Bill monthly"]',
                ))

        # ── MISC_PREP — HIV-negative high-risk patients, drives quarterly visits + labs ──
        on_prep = pd.get("on_prep") or False
        hiv_negative = pd.get("hiv_negative") or False
        prep_high_risk = pd.get("prep_high_risk") or on_prep
        if hiv_negative and prep_high_risk:
            last_prep_visit = pd.get("last_prep_visit_date")
            if not last_prep_visit or months_since(last_prep_visit) >= 3:
                opps.append(self._make_opportunity(
                    mrn_hash=mrn_hash,
                    user_id=pd.get("user_id"),
                    visit_date=pd.get("visit_date"),
                    opportunity_type="misc",
                    codes=["99213", "87389", "80074"],
                    est_revenue=self._get_rate("99213") + 25.0,  # visit + labs estimate
                    eligibility_basis="PrEP patient due for quarterly follow-up visit with HIV test and renal function labs.",
                    documentation_required="Schedule quarterly PrEP follow-up: HIV Ag/Ab (87389), renal panel, STI screening as indicated.",
                    confidence_level="MEDIUM",
                    insurer_caveat="PrEP visits covered under ACA preventive mandate. Labs covered for most payers.",
                    insurer_type=insurer,
                    opportunity_code="MISC_PREP",
                    priority="medium",
                    documentation_checklist='["HIV Ag/Ab test (87389)","Renal function panel","STI screening if indicated","Medication adherence counseling","Refill PrEP prescription"]',
                ))

        # ── MISC_GDM_SCREENING — pregnant women 24-28 weeks without GDM screen ──
        is_pregnant = pd.get("is_pregnant") or False
        gestational_weeks = pd.get("gestational_weeks") or 0
        if is_pregnant and 24 <= gestational_weeks <= 28:
            last_gdm = pd.get("last_gdm_screening_date")
            if not last_gdm:
                opps.append(self._make_opportunity(
                    mrn_hash=mrn_hash,
                    user_id=pd.get("user_id"),
                    visit_date=pd.get("visit_date"),
                    opportunity_type="misc",
                    codes=["82951"],
                    est_revenue=self._get_rate("82951"),
                    eligibility_basis="Pregnant patient at 24-28 weeks gestation without GDM screening on record.",
                    documentation_required="Order glucose tolerance test (82951) for gestational diabetes screening.",
                    confidence_level="HIGH",
                    insurer_caveat="USPSTF B recommendation. Covered by all payers under ACA preventive mandate.",
                    insurer_type=insurer,
                    opportunity_code="MISC_GDM_SCREENING",
                    priority="high",
                    documentation_checklist='["Order 1-hour GTT (82947) or 3-hour GTT (82951)","Patient instructions for fasting/glucose load","Document gestational age","Follow up on results"]',
                ))

        # ── MISC_PERINATAL_DEPRESSION — pregnant/postpartum <12mo with depression risk ──
        is_postpartum = pd.get("is_postpartum") or False
        if (is_pregnant or is_postpartum) and sex in ("f", "female"):
            last_perinatal_screen = pd.get("last_perinatal_depression_screening_date")
            if not last_perinatal_screen or months_since(last_perinatal_screen) >= 3:
                opps.append(self._make_opportunity(
                    mrn_hash=mrn_hash,
                    user_id=pd.get("user_id"),
                    visit_date=pd.get("visit_date"),
                    opportunity_type="misc",
                    codes=["96161"],
                    est_revenue=self._get_rate("96161"),
                    eligibility_basis="Pregnant or postpartum (<12mo) patient — perinatal depression screening recommended.",
                    documentation_required="Administer validated depression screening tool (Edinburgh/PHQ-9). Bill 96161.",
                    confidence_level="HIGH",
                    insurer_caveat="USPSTF B recommendation. ACA mandates coverage without cost-sharing.",
                    insurer_type=insurer,
                    opportunity_code="MISC_PERINATAL_DEPRESSION",
                    priority="medium",
                    documentation_checklist='["Administer Edinburgh or PHQ-9","Score and interpret","Document result","Refer if positive","Plan follow-up"]',
                ))

        # ── MISC_STATIN_COUNSELING — ASCVD risk ≥10%, not on statin (coding support) ──
        ascvd_risk = pd.get("ascvd_10yr_risk") or 0
        on_statin = pd.get("on_statin") or False
        if ascvd_risk >= 10 and not on_statin and 40 <= age <= 75:
            opps.append(self._make_opportunity(
                mrn_hash=mrn_hash,
                user_id=pd.get("user_id"),
                visit_date=pd.get("visit_date"),
                opportunity_type="misc",
                codes=["99401"],
                est_revenue=0.0,  # Coding support, not separately billable
                eligibility_basis=f"10-year ASCVD risk {ascvd_risk}% — statin therapy recommended per USPSTF (Grade B). Not currently on statin.",
                documentation_required="Discuss statin therapy initiation. Document shared decision-making and ASCVD risk score.",
                confidence_level="LOW",
                insurer_caveat="Coding support — supports care gap documentation and quality measures.",
                insurer_type=insurer,
                opportunity_code="MISC_STATIN_COUNSELING",
                priority="low",
                documentation_checklist='["Calculate and document ASCVD risk score","Discuss statin benefits/risks","Document shared decision-making","Prescribe statin if accepted","Address lifestyle modifications"]',
            ))

        # ── MISC_FOLIC_ACID — female reproductive age, not on folic acid (coding support) ──
        if sex in ("f", "female") and 12 <= age <= 50:
            on_folic_acid = pd.get("on_folic_acid") or False
            if not on_folic_acid:
                opps.append(self._make_opportunity(
                    mrn_hash=mrn_hash,
                    user_id=pd.get("user_id"),
                    visit_date=pd.get("visit_date"),
                    opportunity_type="misc",
                    codes=["99401"],
                    est_revenue=0.0,  # Coding support
                    eligibility_basis="Female of reproductive age not on folic acid supplementation per USPSTF (Grade A).",
                    documentation_required="Counsel on folic acid 400-800 mcg daily for neural tube defect prevention.",
                    confidence_level="LOW",
                    insurer_caveat="Coding support — supports care gap documentation and quality measures.",
                    insurer_type=insurer,
                    opportunity_code="MISC_FOLIC_ACID",
                    priority="low",
                    documentation_checklist='["Assess pregnancy planning status","Counsel on folic acid 400-800 mcg daily","Document counseling","Prescribe if appropriate"]',
                ))

        return opps

    @staticmethod
    def _parse_datetime(value):
        """Parse a datetime from string or return datetime object as-is."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(value[:19], fmt)
                except ValueError:
                    continue
        return None

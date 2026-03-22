"""
CareCompanion — Pediatric Detector
billing_engine/detectors/pediatric.py

Bright Futures well-child visits plus lead, anemia, dyslipidemia,
vision, hearing, fluoride varnish, maternal depression screening.
Phase 19D.1 — 8 rules.
"""

from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn, months_since

from app.api_config import (
    BRIGHT_FUTURES_SCHEDULE,
    HEARING_SCREENING_AGES,
    HEARING_SCREENING_RANGES,
    DEVELOPMENTAL_SCREENING_MONTHS,
)


class PediatricDetector(BaseDetector):
    """Pediatric well-child and screening detector."""

    CATEGORY = "pediatric"
    DESCRIPTION = "Bright Futures well-child + lead/anemia/vision/hearing/fluoride"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        opps = []
        age = pd.get("age") or 0
        age_months = pd.get("age_months") or (age * 12)
        # Only run for patients under 22
        if age >= 22:
            return opps

        mrn_hash = hash_mrn(pd.get("mrn") or "")
        insurer = pd.get("insurer_type") or "unknown"
        is_new = pd.get("is_new_patient") or False
        visit_type = (pd.get("visit_type") or "").lower()

        # ── PEDS_WELLCHILD — well-child visit per Bright Futures periodicity ──
        last_well_child = pd.get("last_well_child_date")
        due_for_well_child = not last_well_child or months_since(last_well_child) >= 6
        if due_for_well_child:
            for period_name, info in BRIGHT_FUTURES_SCHEDULE.items():
                lo, hi = info["months"]
                if lo <= age_months <= hi:
                    code = info["new"] if is_new else info["est"]
                    opps.append(self._make_opportunity(
                        mrn_hash=mrn_hash,
                        user_id=pd.get("user_id"),
                        visit_date=pd.get("visit_date"),
                        opportunity_type="pediatric",
                        codes=[code],
                        est_revenue=self._get_rate(code),
                        eligibility_basis=f"Well-child visit due per Bright Futures schedule ({period_name}). Age {age_months} months.",
                        documentation_required=(
                            "Perform age-appropriate Bright Futures visit including history, "
                            "physical exam, developmental surveillance, anticipatory guidance."
                        ),
                        confidence_level="HIGH",
                        insurer_caveat="Covered by all payers; Medicaid EPSDT requires full periodicity.",
                        insurer_type=insurer,
                        opportunity_code="PEDS_WELLCHILD",
                        priority="high",
                        documentation_checklist='["Age-appropriate history","Complete physical exam","Growth chart/BMI","Developmental surveillance","Anticipatory guidance","Immunization review"]',
                    ))
                    break  # Only one well-child code per visit

        # ── PEDS_LEAD — venous lead at 12 and 24 months (Medicaid mandatory) ──
        if age_months in range(11, 14) or age_months in range(23, 26):
            last_lead = pd.get("last_lead_screening_date")
            if not last_lead or months_since(last_lead) >= 10:
                opps.append(self._make_opportunity(
                    mrn_hash=mrn_hash,
                    user_id=pd.get("user_id"),
                    visit_date=pd.get("visit_date"),
                    opportunity_type="pediatric",
                    codes=["83655", "36415"],
                    est_revenue=self._get_rate("83655") + self._get_rate("36415"),
                    eligibility_basis=f"Lead screening due at {age_months} months per Bright Futures/Medicaid EPSDT.",
                    documentation_required="Order venous lead level (83655) with venipuncture (36415). Required for Medicaid; recommended all payers.",
                    confidence_level="HIGH",
                    insurer_caveat="Mandatory for Medicaid EPSDT. Recommended for all payers per AAP.",
                    insurer_type=insurer,
                    opportunity_code="PEDS_LEAD",
                    priority="high",
                    documentation_checklist='["Order venous lead level 83655","Venipuncture 36415","Document risk factors if applicable"]',
                ))

        # ── PEDS_ANEMIA — hemoglobin/hematocrit at 12 months ──
        if 11 <= age_months <= 13:
            last_anemia = pd.get("last_anemia_screening_date")
            if not last_anemia or months_since(last_anemia) >= 10:
                opps.append(self._make_opportunity(
                    mrn_hash=mrn_hash,
                    user_id=pd.get("user_id"),
                    visit_date=pd.get("visit_date"),
                    opportunity_type="pediatric",
                    codes=["85018", "36415"],
                    est_revenue=self._get_rate("85018") + self._get_rate("36415"),
                    eligibility_basis="Routine hemoglobin screening at 12 months per AAP/Bright Futures.",
                    documentation_required="Order hemoglobin (85018) with venipuncture (36415).",
                    confidence_level="HIGH",
                    insurer_caveat="Covered by all payers. Medicaid EPSDT mandates at 12 months.",
                    insurer_type=insurer,
                    opportunity_code="PEDS_ANEMIA",
                    priority="medium",
                    documentation_checklist='["Order hemoglobin 85018","Venipuncture 36415","Assess iron intake/risk factors"]',
                ))

        # ── PEDS_DYSLIPIDEMIA — lipid panel at ages 9-11 (once) and 17-21 (once) ──
        if (9 <= age <= 11) or (17 <= age <= 21):
            last_lipid = pd.get("last_lipid_screening_date")
            if not last_lipid or months_since(last_lipid) >= 24:
                window = "9-11y" if age <= 11 else "17-21y"
                opps.append(self._make_opportunity(
                    mrn_hash=mrn_hash,
                    user_id=pd.get("user_id"),
                    visit_date=pd.get("visit_date"),
                    opportunity_type="pediatric",
                    codes=["80061", "36415"],
                    est_revenue=self._get_rate("80061") + self._get_rate("36415"),
                    eligibility_basis=f"Universal dyslipidemia screening recommended ({window}) per NHLBI/AAP.",
                    documentation_required="Order fasting lipid panel (80061) with venipuncture (36415).",
                    confidence_level="MEDIUM",
                    insurer_caveat="Recommended by NHLBI expert panel for all children/adolescents.",
                    insurer_type=insurer,
                    opportunity_code="PEDS_DYSLIPIDEMIA",
                    priority="medium",
                    documentation_checklist='["Order fasting lipid panel 80061","Venipuncture 36415","Assess family history of CVD","Document BMI"]',
                ))

        # ── PEDS_FLUORIDE — fluoride varnish for children through age 5 ──
        if age <= 5 and pd.get("has_teeth", age_months >= 6):
            last_fluoride = pd.get("last_fluoride_date")
            if not last_fluoride or months_since(last_fluoride) >= 3:
                opps.append(self._make_opportunity(
                    mrn_hash=mrn_hash,
                    user_id=pd.get("user_id"),
                    visit_date=pd.get("visit_date"),
                    opportunity_type="pediatric",
                    codes=["99188"],
                    est_revenue=self._get_rate("99188"),
                    eligibility_basis="Fluoride varnish application recommended for children with teeth through age 5 per USPSTF.",
                    documentation_required="Apply fluoride varnish to teeth (99188). Up to 4x per year.",
                    confidence_level="HIGH",
                    insurer_caveat="Covered by most payers. USPSTF B recommendation. Quarterly application.",
                    insurer_type=insurer,
                    opportunity_code="PEDS_FLUORIDE",
                    priority="low",
                    documentation_checklist='["Verify erupted teeth present","Apply fluoride varnish","Document number of teeth treated","Provide caregiver instructions"]',
                ))

        # ── PEDS_VISION — instrument-based screening ages 3-5 per USPSTF ──
        if 3 <= age <= 5:
            last_vision = pd.get("last_vision_screening_date")
            if not last_vision or months_since(last_vision) >= 12:
                opps.append(self._make_opportunity(
                    mrn_hash=mrn_hash,
                    user_id=pd.get("user_id"),
                    visit_date=pd.get("visit_date"),
                    opportunity_type="pediatric",
                    codes=["99174"],
                    est_revenue=self._get_rate("99174"),
                    eligibility_basis="Vision screening recommended ages 3-5 per USPSTF (amblyopia detection).",
                    documentation_required="Perform instrument-based ocular screening (99174) or visual acuity (99173).",
                    confidence_level="HIGH",
                    insurer_caveat="USPSTF B recommendation. Covered by most payers.",
                    insurer_type=insurer,
                    opportunity_code="PEDS_VISION",
                    priority="low",
                    documentation_checklist='["Perform instrument-based screening or Snellen chart","Document results bilateral","Refer if abnormal"]',
                ))

        # ── PEDS_HEARING — periodicity-based hearing screening ──
        hearing_due = False
        if age in HEARING_SCREENING_AGES:
            hearing_due = True
        else:
            for lo, hi in HEARING_SCREENING_RANGES:
                if lo <= age <= hi:
                    hearing_due = True
                    break
        if hearing_due:
            last_hearing = pd.get("last_hearing_screening_date")
            if not last_hearing or months_since(last_hearing) >= 12:
                opps.append(self._make_opportunity(
                    mrn_hash=mrn_hash,
                    user_id=pd.get("user_id"),
                    visit_date=pd.get("visit_date"),
                    opportunity_type="pediatric",
                    codes=["92551"],
                    est_revenue=self._get_rate("92551"),
                    eligibility_basis=f"Hearing screening due at age {age} per Bright Futures periodicity schedule.",
                    documentation_required="Perform pure tone screening (92551) or audiometry (92552).",
                    confidence_level="MEDIUM",
                    insurer_caveat="Part of well-child visit; separately billable if documented.",
                    insurer_type=insurer,
                    opportunity_code="PEDS_HEARING",
                    priority="low",
                    documentation_checklist='["Perform pure tone screening","Document pass/fail bilateral","Refer if abnormal findings"]',
                ))

        # ── PEDS_MATERNAL_DEPRESSION — screen mother at well-baby visits <12mo ──
        if age_months < 12 and visit_type in ("well_child", "well_baby", "preventive", "newborn"):
            last_maternal_screen = pd.get("last_maternal_depression_screening_date")
            if not last_maternal_screen or months_since(last_maternal_screen) >= 2:
                opps.append(self._make_opportunity(
                    mrn_hash=mrn_hash,
                    user_id=pd.get("user_id"),
                    visit_date=pd.get("visit_date"),
                    opportunity_type="pediatric",
                    codes=["96127"],
                    est_revenue=self._get_rate("96127"),
                    eligibility_basis="Maternal depression screening at well-baby visit (patient <12mo) per AAP Bright Futures.",
                    documentation_required="Administer Edinburgh Postnatal Depression Scale or PHQ-9 to mother/caregiver (96127).",
                    confidence_level="MEDIUM",
                    insurer_caveat="Billable under infant's visit. Supported by AAP Bright Futures policy.",
                    insurer_type=insurer,
                    opportunity_code="PEDS_MATERNAL_DEPRESSION",
                    priority="medium",
                    documentation_checklist='["Administer Edinburgh/PHQ-9 to mother","Score and interpret","Document result in infant chart","Refer mother if positive"]',
                ))

        return opps

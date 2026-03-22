"""
CareCompanion — Calculator-Driven Billing Detector
billing_engine/detectors/calculator_detector.py

Examines CalculatorResult records and generates BillingOpportunity entries
for scores that cross billing-relevant thresholds.

Triggers:
  - BMI ≥ 30            → obesity counseling (G0447 Medicare / 99401 commercial)
  - PREVENT ≥ 7.5%      → statin shared decision-making documentation (99401)
  - Pack years ≥ 20,
    age 50-80            → LDCT lung cancer screening (71271 + G0296)
  - LDL ≥ 190           → familial hypercholesterolemia workup (81401)
  - AUDIT-C ≥ threshold → SBIRT alcohol counseling (G0442 + G0443)
  - GAD-7 / PHQ-9 / EPDS administered → brief emotional assessment (96127)
  - MoCA administered   → neurobehavioral status exam (96116 + 96121)
  - ADA Risk ≥ 5        → diabetes prevention counseling (99401 + 82947)
"""

import json
import logging

from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn

logger = logging.getLogger(__name__)

# AUDIT-C positive thresholds by sex
_AUDIT_C_POS_MALE = 4
_AUDIT_C_POS_FEMALE = 3

# ---------------------------------------------------------------------------
# Documentation phrase seeds (38.2)
# ---------------------------------------------------------------------------

PHRASE_SEEDS = [
    {
        "opportunity_code": "CALC_BMI_OBC",
        "cpt_code": "G0447",
        "phrase_category": "counseling",
        "phrase_title": "Obesity Counseling — BMI Documented",
        "phrase_text": (
            "BMI calculated at {score} kg/m\u00b2 ({label}). "
            "Obesity counseling provided regarding dietary modifications, "
            "physical activity goals, and behavioral strategies. "
            "Duration: [X] minutes. Patient verbalized understanding."
        ),
        "payer_specific": None,
        "clinical_context": "BMI >= 30, obesity IBT or preventive counseling",
    },
    {
        "opportunity_code": "CALC_PREVENT_SDM",
        "cpt_code": "99401",
        "phrase_category": "counseling",
        "phrase_title": "Statin Shared Decision-Making — PREVENT Score",
        "phrase_text": (
            "PREVENT 10-year cardiovascular risk calculated at {score}%. "
            "Statin therapy discussed per ACC/AHA guidelines. "
            "Risk factors reviewed: [list]. "
            "Patient {accepted/declined} statin therapy. "
            "Referral to dietitian [placed/deferred]."
        ),
        "payer_specific": None,
        "clinical_context": "PREVENT >= 7.5%, statin SDM required",
    },
    {
        "opportunity_code": "CALC_LDCT_SCR",
        "cpt_code": "G0296",
        "phrase_category": "screening",
        "phrase_title": "Lung Cancer Screening Counseling — LDCT Eligibility",
        "phrase_text": (
            "Lung cancer screening eligibility confirmed: {pack_years} pack-years, "
            "age {age}. USPSTF Grade B recommendation discussed. "
            "LDCT screening {ordered / patient declined}. "
            "Shared decision-making documented per G0296 requirements."
        ),
        "payer_specific": None,
        "clinical_context": "Pack years >= 20, age 50-80, LDCT screening",
    },
    {
        "opportunity_code": "CALC_AUDIT_SBIRT",
        "cpt_code": "G0442",
        "phrase_category": "screening",
        "phrase_title": "Alcohol Misuse Screening — AUDIT-C Positive",
        "phrase_text": (
            "AUDIT-C score: {score}/12. Screening positive per threshold. "
            "Brief intervention provided per SBIRT protocol: "
            "risks of alcohol use discussed, motivation for change explored, "
            "patient set goal to [reduce/abstain]. "
            "Duration: [X] minutes. Follow-up [scheduled/offered]."
        ),
        "payer_specific": None,
        "clinical_context": "AUDIT-C >= threshold, SBIRT brief intervention",
    },
]


class CalculatorBillingDetector(BaseDetector):
    """
    Generates billing opportunities from clinical calculator scores.

    Accepts either patient_data['calculator_scores'] (a plain dict of
    {key: float}) for testing/override, or queries CalculatorResult
    from the database using patient_data['mrn'].
    """

    CATEGORY = "calculator_billing"
    DESCRIPTION = "Calculator result-driven billing opportunities"

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def detect(self, patient_data, payer_context):
        scores = self._load_scores(patient_data)
        if not scores:
            return []

        mrn_hash  = hash_mrn(patient_data.get("mrn") or "")
        user_id   = patient_data.get("user_id")
        visit_date = patient_data.get("visit_date")
        insurer   = (patient_data.get("insurer_type") or "unknown").lower()
        sex       = (patient_data.get("sex") or "").lower()
        age       = patient_data.get("age_years")

        opps = []

        # 1. BMI >= 30 → obesity counseling
        bmi = scores.get("bmi")
        if bmi is not None and bmi >= 30:
            if bmi < 35:
                label = "Obesity Class I"
            elif bmi < 40:
                label = "Obesity Class II"
            else:
                label = "Obesity Class III"

            if insurer == "medicare":
                codes = ["G0447"]
                rev = self._get_rate("G0447") or 30.0
            else:
                codes = ["99401"]
                rev = self._get_rate("99401") or 30.0

            opps.append(self._make_opportunity(
                mrn_hash=mrn_hash, user_id=user_id, visit_date=visit_date,
                opportunity_type="obesity_counseling",
                codes=codes,
                est_revenue=rev,
                eligibility_basis=(
                    f"BMI calculated at {bmi:.1f} ({label}). "
                    "Score threshold: \u2265 30. Obesity counseling billable."
                ),
                documentation_required=(
                    "Document: BMI value, obesity counseling provided, duration (min), "
                    "diet/exercise plan discussed. G0447 = Medicare 15-min IBT; "
                    "99401-99404 = preventive counseling 15-60 min."
                ),
                confidence_level="HIGH",
                insurer_caveat=(
                    "G0447 is Medicare-only. Use 99401-99404 for commercial payers."
                    if insurer != "medicare" else None
                ),
                insurer_type=insurer,
                category=self.CATEGORY,
                opportunity_code="CALC_BMI_OBC",
                priority="high",
                documentation_checklist=json.dumps([
                    "BMI documented",
                    "Counseling duration noted",
                    "Diet and exercise plan in note",
                ]),
            ))

        # 2. PREVENT >= 7.5% → statin shared decision-making
        prevent = scores.get("prevent")
        if prevent is not None and prevent >= 7.5:
            opps.append(self._make_opportunity(
                mrn_hash=mrn_hash, user_id=user_id, visit_date=visit_date,
                opportunity_type="statin_sdm",
                codes=["99401"],
                est_revenue=self._get_rate("99401") or 30.0,
                eligibility_basis=(
                    f"PREVENT 10-year CVD risk: {prevent:.1f}%. "
                    "Threshold \u2265 7.5% triggers AHA/ACC statin recommendation. "
                    "Shared decision-making required."
                ),
                documentation_required=(
                    "Document: PREVENT risk score, statin therapy discussion, "
                    "patient decision (accept/decline), risk factors reviewed."
                ),
                confidence_level="HIGH",
                insurer_caveat="Verify payer coverage for preventive counseling add-on.",
                insurer_type=insurer,
                category=self.CATEGORY,
                opportunity_code="CALC_PREVENT_SDM",
                priority="high",
                documentation_checklist=json.dumps([
                    "PREVENT score documented",
                    "Statin SDM note present",
                    "Patient decision recorded",
                ]),
            ))

        # 3. Pack years >= 20, age 50-80 → LDCT lung cancer screening
        pack_years = scores.get("pack_years")
        if pack_years is not None and pack_years >= 20:
            age_ok = (age is not None and 50 <= age <= 80)
            confidence = "HIGH" if age_ok else "MEDIUM"
            age_str = f", age: {age}" if age is not None else ""
            opps.append(self._make_opportunity(
                mrn_hash=mrn_hash, user_id=user_id, visit_date=visit_date,
                opportunity_type="ldct_screening",
                codes=["71271", "G0296"],
                est_revenue=(self._get_rate("71271") + self._get_rate("G0296")) or 290.0,
                eligibility_basis=(
                    f"Pack years: {pack_years:.0f}{age_str}. "
                    "USPSTF Grade B: LDCT lung screening for 50-80 year olds "
                    "with \u2265 20 pack-years."
                ),
                documentation_required=(
                    "Document: smoking history (pack-years), current status, "
                    "shared decision-making, LDCT order. "
                    "G0296 = lung cancer screening counseling/shared SDM."
                ),
                confidence_level=confidence,
                insurer_caveat=(
                    "Medicare covers LDCT annually. "
                    "Verify prior auth for commercial payers."
                ),
                insurer_type=insurer,
                category=self.CATEGORY,
                opportunity_code="CALC_LDCT_SCR",
                priority="high",
                documentation_checklist=json.dumps([
                    "Pack-year history documented",
                    "LDCT order placed",
                    "Shared decision-making note with G0296",
                ]),
            ))

        # 4. LDL >= 190 → familial hypercholesterolemia workup
        ldl = scores.get("ldl")
        if ldl is not None and ldl >= 190:
            opps.append(self._make_opportunity(
                mrn_hash=mrn_hash, user_id=user_id, visit_date=visit_date,
                opportunity_type="fh_workup",
                codes=["81401"],
                est_revenue=self._get_rate("81401") or 100.0,
                eligibility_basis=(
                    f"LDL cholesterol: {ldl:.0f} mg/dL (threshold \u2265 190). "
                    "Familial hypercholesterolemia workup indicated."
                ),
                documentation_required=(
                    "Document: LDL value, FH clinical criteria "
                    "(Dutch Lipid Clinic Network score), family history review, "
                    "statin candidacy. 81401 = molecular pathology Level 2."
                ),
                confidence_level="HIGH",
                insurer_caveat=(
                    "Verify prior auth for genetic panel 81401. "
                    "Some payers require Dutch FH score \u2265 6."
                ),
                insurer_type=insurer,
                category=self.CATEGORY,
                opportunity_code="CALC_LDL_FH",
                priority="medium",
                documentation_checklist=json.dumps([
                    "LDL value documented",
                    "FH clinical criteria assessed",
                    "Genetic testing order if indicated",
                ]),
            ))

        # 5. AUDIT-C >= positive threshold → SBIRT
        audit_c = scores.get("audit_c")
        if audit_c is not None:
            pos_threshold = _AUDIT_C_POS_FEMALE if sex == "female" else _AUDIT_C_POS_MALE
            if audit_c >= pos_threshold:
                gender_word = "women" if sex == "female" else "men"
                opps.append(self._make_opportunity(
                    mrn_hash=mrn_hash, user_id=user_id, visit_date=visit_date,
                    opportunity_type="sbirt",
                    codes=["G0442", "G0443"],
                    est_revenue=(
                        (self._get_rate("G0442") + self._get_rate("G0443")) or 60.0
                    ),
                    eligibility_basis=(
                        f"AUDIT-C score: {audit_c}/12 "
                        f"(\u2265 {pos_threshold} threshold for {gender_word}). "
                        "Alcohol misuse screening positive — brief intervention indicated."
                    ),
                    documentation_required=(
                        "Document: AUDIT-C score, brief intervention provided, "
                        "duration, counseling content. "
                        "G0442 = annual alcohol misuse screening; "
                        "G0443 = brief counseling \u2264 15 min."
                    ),
                    confidence_level="HIGH",
                    insurer_caveat=(
                        "G0442/G0443 are Medicare/Medicaid codes. "
                        "Commercial: verify SBIRT coverage."
                    ),
                    insurer_type=insurer,
                    category=self.CATEGORY,
                    opportunity_code="CALC_AUDIT_SBIRT",
                    priority="high",
                    documentation_checklist=json.dumps([
                        "AUDIT-C score documented",
                        "Brief intervention note present",
                        "Patient counseling documented",
                    ]),
                ))

        # 6. GAD-7 / PHQ-9 / EPDS administered → 96127 brief assessment
        # Only bill 96127 once per visit (one instrument claimed)
        for key, label in [
            ("gad7",  "GAD-7 anxiety"),
            ("phq9",  "PHQ-9 depression"),
            ("epds",  "EPDS perinatal depression"),
        ]:
            if scores.get(key) is not None:
                score_val = scores[key]
                short = key.upper()
                opps.append(self._make_opportunity(
                    mrn_hash=mrn_hash, user_id=user_id, visit_date=visit_date,
                    opportunity_type="brief_emotional_assessment",
                    codes=["96127"],
                    est_revenue=self._get_rate("96127") or 20.0,
                    eligibility_basis=(
                        f"{short} score: {score_val:.0f}. "
                        f"{label.capitalize()} tool administered and scored."
                    ),
                    documentation_required=(
                        f"Document: {short} score, interpretation, clinical action taken. "
                        "96127 = brief emotional/behavioral assessment, up to 15 min."
                    ),
                    confidence_level="HIGH",
                    insurer_caveat=None,
                    insurer_type=insurer,
                    category=self.CATEGORY,
                    opportunity_code=f"CALC_{short}_96127",
                    priority="medium",
                    documentation_checklist=json.dumps([
                        f"{short} score documented",
                        "Clinical action noted",
                    ]),
                ))
                break  # Only one 96127 per visit

        # 7. MoCA administered → neurobehavioral status exam
        moca = scores.get("moca")
        if moca is not None:
            opps.append(self._make_opportunity(
                mrn_hash=mrn_hash, user_id=user_id, visit_date=visit_date,
                opportunity_type="neurobehavioral_exam",
                codes=["96116", "96121"],
                est_revenue=(
                    (self._get_rate("96116") + self._get_rate("96121")) or 70.0
                ),
                eligibility_basis=(
                    f"MoCA score: {moca:.0f}/30. "
                    "Neurobehavioral status exam administered and interpreted."
                ),
                documentation_required=(
                    "Document: MoCA score, components reviewed, interpretation, "
                    "clinical plan. 96116 = NBE first hour; 96121 = each additional hour."
                ),
                confidence_level="HIGH",
                insurer_caveat=(
                    "96121 requires documentation of additional hour of assessment."
                ),
                insurer_type=insurer,
                category=self.CATEGORY,
                opportunity_code="CALC_MOCA_NBE",
                priority="medium",
                documentation_checklist=json.dumps([
                    "MoCA score documented",
                    "NBE interpretation in note",
                    "Clinical plan documented",
                ]),
            ))

        # 8. ADA Risk >= 5 → diabetes prevention counseling
        ada_risk = scores.get("ada_risk")
        if ada_risk is not None and ada_risk >= 5:
            opps.append(self._make_opportunity(
                mrn_hash=mrn_hash, user_id=user_id, visit_date=visit_date,
                opportunity_type="dm_prevention_counseling",
                codes=["99401", "82947"],
                est_revenue=(
                    (self._get_rate("99401") + self._get_rate("82947")) or 60.0
                ),
                eligibility_basis=(
                    f"ADA Diabetes Risk Score: {ada_risk:.0f}/10 "
                    "(\u2265 5 threshold positive). "
                    "Pre-diabetes risk counseling and fasting glucose indicated."
                ),
                documentation_required=(
                    "Document: ADA risk score, counseling content (diet, exercise, weight), "
                    "glucose test order. "
                    "99401 = preventive counseling; 82947 = fasting glucose."
                ),
                confidence_level="MEDIUM",
                insurer_caveat=(
                    "Verify glucose order coverage. "
                    "99401 typically bundled with preventive visit."
                ),
                insurer_type=insurer,
                category=self.CATEGORY,
                opportunity_code="CALC_ADA_DM_PREV",
                priority="medium",
                documentation_checklist=json.dumps([
                    "ADA risk score documented",
                    "Counseling note present",
                    "Glucose order placed",
                ]),
            ))

        return opps

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_scores(self, patient_data):
        """
        Return {calculator_key: score_value} for the patient.

        Checks patient_data['calculator_scores'] first (allows test injection).
        Falls back to querying CalculatorResult from the DB if MRN is present.
        """
        override = patient_data.get("calculator_scores")
        if override is not None:
            return override

        mrn = patient_data.get("mrn")
        if not mrn:
            return {}

        try:
            from models.calculator import CalculatorResult
            rows = (
                CalculatorResult.query
                .filter_by(mrn=mrn, is_current=True)
                .all()
            )
            return {
                row.calculator_key: row.score_value
                for row in rows
                if row.score_value is not None
            }
        except Exception:
            logger.debug(
                "CalculatorResult query failed — no calculator scores available",
                exc_info=True,
            )
            return {}

    @classmethod
    def seed_phrases(cls, db_session):
        """
        Insert PHRASE_SEEDS into the documentation_phrase table.
        Safe to call multiple times (skips existing rows by opportunity_code + cpt_code).
        """
        from models.billing import DocumentationPhrase
        seeded = 0
        for seed in PHRASE_SEEDS:
            existing = DocumentationPhrase.query.filter_by(
                opportunity_code=seed["opportunity_code"],
                cpt_code=seed["cpt_code"],
            ).first()
            if not existing:
                db_session.add(DocumentationPhrase(
                    opportunity_code=seed["opportunity_code"],
                    cpt_code=seed["cpt_code"],
                    phrase_category=seed["phrase_category"],
                    phrase_title=seed["phrase_title"],
                    phrase_text=seed["phrase_text"],
                    payer_specific=seed.get("payer_specific"),
                    clinical_context=seed.get("clinical_context"),
                    is_active=True,
                    is_customized=False,
                ))
                seeded += 1
        if seeded:
            db_session.commit()
        return seeded

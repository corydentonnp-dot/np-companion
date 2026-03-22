"""
CareCompanion — Counseling Detector
billing_engine/detectors/counseling.py

Falls prevention, CVD intensive behavioral therapy, breastfeeding,
DSMT referral, contraception coding support, skin cancer coding support.
Phase 19C.3.
"""

from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn
from app.api_config import CVD_RISK_PREFIXES, FALL_RISK_PREFIXES


def _has_dx_prefix(diagnoses, prefixes):
    for dx in diagnoses:
        code = (dx.get("icd10_code") or "").upper()
        if (dx.get("status") or "").lower() == "resolved":
            continue
        if any(code.startswith(p) for p in prefixes):
            return True
    return False


class CounselingDetector(BaseDetector):
    """Preventive counseling services detector."""

    CATEGORY = "counseling"
    DESCRIPTION = "Falls, CVD IBT, breastfeeding, DSMT, contraception, skin cancer"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        diagnoses = pd.get("diagnoses") or []
        age = pd.get("age") or 0
        insurer = pd.get("insurer_type") or "unknown"
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        sex = (pd.get("sex") or pd.get("gender") or "").lower()
        opps = []

        # ── COUNS_FALLS — Medicare, age 65+, fall risk factors ──
        if age >= 65 and _has_dx_prefix(diagnoses, FALL_RISK_PREFIXES):
            from billing_engine.shared import months_since
            last_fall_counsel = pd.get("last_fall_counseling_date")
            if not last_fall_counsel or months_since(last_fall_counsel) >= 12:
                opps.append(self._build(pd, mrn_hash, insurer,
                    code="97110",
                    opportunity_code="COUNS_FALLS",
                    eligibility="Age 65+, fall risk factors present. Annual fall prevention counseling indicated.",
                    doc="Document fall risk assessment, exercise/balance recommendations, home safety review.",
                    checklist='["Assess fall risk factors","Document exercise/balance recommendations","Review home safety","Refer to PT if appropriate"]',
                    priority="medium",
                ))

        # ── COUNS_CVD_IBT — Medicare, CVD risk factors, annual ──
        if payer_context.get("is_medicare") and _has_dx_prefix(diagnoses, CVD_RISK_PREFIXES):
            from billing_engine.shared import months_since
            last_cvd_ibt = pd.get("last_cvd_ibt_date")
            if not last_cvd_ibt or months_since(last_cvd_ibt) >= 12:
                opps.append(self._build(pd, mrn_hash, insurer,
                    code="G0446",
                    opportunity_code="COUNS_CVD_IBT",
                    eligibility="Medicare beneficiary with CVD risk factors. Annual IBT zero cost-share.",
                    doc="Document CVD risk factor-targeted intensive behavioral therapy. Zero cost-share for Medicare.",
                    checklist='["Assess CVD risk factors","Provide dietary counseling","Discuss physical activity","Document intervention and plan"]',
                    priority="medium",
                ))

        # ── COUNS_BREASTFEED — Pregnant/nursing women ──
        is_pregnant = pd.get("is_pregnant") or False
        is_nursing = pd.get("is_nursing") or False
        if (is_pregnant or is_nursing) and sex in ("f", "female"):
            opps.append(self._build(pd, mrn_hash, insurer,
                code="99401",
                opportunity_code="COUNS_BREASTFEED",
                eligibility="Pregnant/nursing woman. Breastfeeding counseling and support indicated.",
                doc="Document breastfeeding counseling: education, support, lactation resources provided.",
                checklist='["Assess breastfeeding knowledge/concerns","Provide education and support","Document counseling duration","Refer to lactation consultant if needed"]',
                priority="low",
            ))

        # ── COUNS_DSMT — Medicare, diabetes dx ──
        diabetes_prefixes = ["E10", "E11", "E13"]
        if _has_dx_prefix(diagnoses, diabetes_prefixes):
            if not pd.get("dsmt_referred_this_year"):
                opps.append(self._build(pd, mrn_hash, insurer,
                    code="G0108",
                    opportunity_code="COUNS_DSMT",
                    eligibility="Diabetes diagnosis. DSMT referral to certified program indicated.",
                    doc="Refer to DSMT-certified program. Document referral and clinical indication.",
                    checklist='["Verify DSMT-certified program availability","Write DSMT referral order","Document clinical indication for DSMT","Provide patient with program information"]',
                    priority="low",
                ))

        # ── COUNS_CONTRACEPTION — coding support for well-woman visit ──
        if sex in ("f", "female") and 12 <= age <= 50:
            visit_type = (pd.get("visit_type") or "").lower()
            if visit_type in ("preventive", "well_woman", "annual"):
                opps.append(self._build(pd, mrn_hash, insurer,
                    code="99401",
                    opportunity_code="COUNS_CONTRACEPTION",
                    eligibility="Female reproductive age, preventive visit. Contraception counseling supports separate E/M.",
                    doc="Document contraceptive counseling as part of well-woman visit.",
                    checklist='["Discuss contraceptive options","Document counseling duration","Document patient preference and plan"]',
                    priority="low",
                ))

        # ── COUNS_SKIN_CANCER — coding support, fair-skinned 6mo-24y ──
        if age <= 24:
            skin_risk = pd.get("fair_skin_risk") or False
            if skin_risk:
                opps.append(self._build(pd, mrn_hash, insurer,
                    code="99401",
                    opportunity_code="COUNS_SKIN_CANCER",
                    eligibility="Fair-skinned person age 6mo-24y. Skin cancer prevention counseling supports preventive coding.",
                    doc="Document sun protection counseling: sunscreen use, UV avoidance, skin self-exam education.",
                    checklist='["Assess skin type and UV exposure","Counsel on sunscreen use","Discuss UV avoidance behaviours","Document counseling"]',
                    priority="low",
                ))

        return opps

    def _build(self, pd, mrn_hash, insurer, *, code, opportunity_code,
               eligibility, doc, checklist, priority="medium"):
        return self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="counseling",
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

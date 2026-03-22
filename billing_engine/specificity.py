"""
CareCompanion — Code Specificity Recommender
File: billing_engine/specificity.py
Phase 21.7

Recommends more specific ICD-10 codes based on chart evidence (labs, screenings).
COMPLIANCE GUARD: never suggests unsupported codes. Missing documentation
produces "Missing: [element] needed to support [code]" instead.

Supported upgrade paths:
- E78.5 (HLD unspecified) → E78.49/E78.2 based on lipid panel
- E11.65 vs E11.69 (DM2 hyperglycemia) based on A1C
- F32.0 vs F32.1 vs F32.2 (MDD severity) based on PHQ-9
- E03.9 vs E03.8 (hypothyroidism) based on TSH
- I10 → I11.9/I12.9 based on organ damage evidence
- N18.9 → N18.3/N18.4 based on eGFR
"""


# Each recommendation: current_code → recommended, chart_evidence_required, reason
SPECIFICITY_RULES = [
    # ── Hyperlipidemia ──
    {
        "current_code": "E78.5",
        "current_description": "Hyperlipidemia, unspecified",
        "recommendations": [
            {
                "recommended_code": "E78.49",
                "description": "Other hyperlipidemia (mixed)",
                "evidence_required": {"lab": "lipid_panel", "condition": "triglycerides_elevated_and_ldl_elevated"},
                "evidence_description": "Lipid panel showing both elevated LDL and triglycerides",
                "enr_value_diff": "+$2.40",
                "denial_risk_reduction": "12% lower denial",
                "reason": "Mixed hyperlipidemia supported by lipid panel — reduces 48% adj rate",
            },
            {
                "recommended_code": "E78.2",
                "description": "Mixed hyperlipidemia",
                "evidence_required": {"lab": "lipid_panel", "condition": "cholesterol_and_triglycerides_both_elevated"},
                "evidence_description": "Combined hyperlipidemia on lipid panel (both cholesterol and TG elevated)",
                "enr_value_diff": "+$2.40",
                "denial_risk_reduction": "10% lower denial",
                "reason": "Specified mixed hyperlipidemia — better coding precision",
            },
            {
                "recommended_code": "E78.00",
                "description": "Pure hypercholesterolemia, unspecified",
                "evidence_required": {"lab": "lipid_panel", "condition": "ldl_elevated_tg_normal"},
                "evidence_description": "LDL elevated with normal triglycerides",
                "enr_value_diff": "+$1.80",
                "denial_risk_reduction": "8% lower denial",
                "reason": "Isolated LDL elevation differentiated from mixed",
            },
        ],
    },
    # ── Diabetes Type 2 ──
    {
        "current_code": "E11.65",
        "current_description": "Type 2 DM with hyperglycemia",
        "recommendations": [
            {
                "recommended_code": "E11.65",
                "description": "Type 2 DM with hyperglycemia (CONFIRM)",
                "evidence_required": {"lab": "a1c", "condition": "a1c_above_7"},
                "evidence_description": "A1C > 7.0% documenting hyperglycemia",
                "enr_value_diff": "$0 (confirms current)",
                "denial_risk_reduction": "Confirms accuracy",
                "reason": "A1C > 7% supports hyperglycemia designation — no change needed",
            },
        ],
    },
    {
        "current_code": "E11.69",
        "current_description": "Type 2 DM with other specified complication",
        "recommendations": [
            {
                "recommended_code": "E11.65",
                "description": "Type 2 DM with hyperglycemia",
                "evidence_required": {"lab": "a1c", "condition": "a1c_above_7"},
                "evidence_description": "A1C > 7.0%",
                "enr_value_diff": "+$3.20",
                "denial_risk_reduction": "15% lower denial",
                "reason": "Hyperglycemia is more specific than 'other complication' when A1C supports it",
            },
        ],
    },
    # ── Major Depressive Disorder ──
    {
        "current_code": "F32.9",
        "current_description": "Major depressive disorder, single episode, unspecified",
        "recommendations": [
            {
                "recommended_code": "F32.0",
                "description": "MDD, single episode, mild",
                "evidence_required": {"screening": "phq9", "condition": "phq9_5_to_9"},
                "evidence_description": "PHQ-9 score 5-9 (mild depression)",
                "enr_value_diff": "+$1.60",
                "denial_risk_reduction": "10% lower denial",
                "reason": "PHQ-9 5-9 supports mild severity",
            },
            {
                "recommended_code": "F32.1",
                "description": "MDD, single episode, moderate",
                "evidence_required": {"screening": "phq9", "condition": "phq9_10_to_14"},
                "evidence_description": "PHQ-9 score 10-14 (moderate depression)",
                "enr_value_diff": "+$2.00",
                "denial_risk_reduction": "12% lower denial",
                "reason": "PHQ-9 10-14 supports moderate severity",
            },
            {
                "recommended_code": "F32.2",
                "description": "MDD, single episode, severe without psychotic features",
                "evidence_required": {"screening": "phq9", "condition": "phq9_15_plus"},
                "evidence_description": "PHQ-9 score >= 15 (moderately severe to severe)",
                "enr_value_diff": "+$2.80",
                "denial_risk_reduction": "14% lower denial",
                "reason": "PHQ-9 >= 15 supports severe designation",
            },
        ],
    },
    # ── Hypothyroidism ──
    {
        "current_code": "E03.9",
        "current_description": "Hypothyroidism, unspecified",
        "recommendations": [
            {
                "recommended_code": "E03.8",
                "description": "Other specified hypothyroidism",
                "evidence_required": {"lab": "tsh", "condition": "tsh_elevated_with_treatment"},
                "evidence_description": "TSH elevated on levothyroxine therapy",
                "enr_value_diff": "+$1.20",
                "denial_risk_reduction": "6% lower denial",
                "reason": "Specify etiology when labs + medication support it",
            },
        ],
    },
    # ── Hypertension with organ damage ──
    {
        "current_code": "I10",
        "current_description": "Essential hypertension",
        "recommendations": [
            {
                "recommended_code": "I11.9",
                "description": "Hypertensive heart disease without heart failure",
                "evidence_required": {"diagnosis": "lvh_or_echo_abnormal", "condition": "cardiac_involvement"},
                "evidence_description": "Evidence of cardiac involvement (LVH on echo/EKG)",
                "enr_value_diff": "+$4.50",
                "denial_risk_reduction": "Must have documented cardiac involvement",
                "reason": "Hypertensive heart disease captures higher complexity when organ damage exists",
            },
            {
                "recommended_code": "I12.9",
                "description": "Hypertensive CKD without heart failure",
                "evidence_required": {"lab": "egfr", "condition": "egfr_below_60"},
                "evidence_description": "eGFR < 60 (CKD stage 3+)",
                "enr_value_diff": "+$5.20",
                "denial_risk_reduction": "Must have CKD documented",
                "reason": "CMS presumes causal link between HTN and CKD — code together",
            },
        ],
    },
    # ── CKD staging ──
    {
        "current_code": "N18.9",
        "current_description": "Chronic kidney disease, unspecified",
        "recommendations": [
            {
                "recommended_code": "N18.3",
                "description": "CKD stage 3 (moderate)",
                "evidence_required": {"lab": "egfr", "condition": "egfr_30_to_59"},
                "evidence_description": "eGFR 30-59 mL/min",
                "enr_value_diff": "+$3.60",
                "denial_risk_reduction": "20% lower denial",
                "reason": "eGFR 30-59 supports stage 3 — much higher specificity",
            },
            {
                "recommended_code": "N18.4",
                "description": "CKD stage 4 (severe)",
                "evidence_required": {"lab": "egfr", "condition": "egfr_15_to_29"},
                "evidence_description": "eGFR 15-29 mL/min",
                "enr_value_diff": "+$5.80",
                "denial_risk_reduction": "25% lower denial",
                "reason": "eGFR 15-29 supports stage 4 — captures severity",
            },
        ],
    },
]


class CodeSpecificityRecommender:
    """
    Analyzes patient diagnosis codes against available chart evidence
    (labs, screenings) and recommends more specific ICD-10 codes.

    COMPLIANCE GUARD: Never recommends a code upgrade without documented
    chart evidence. Missing evidence produces a 'missing' advisory instead.
    """

    def __init__(self):
        self.rules = {r["current_code"]: r for r in SPECIFICITY_RULES}

    def get_supported_codes(self):
        """Return list of ICD-10 codes this recommender can analyze."""
        return list(self.rules.keys())

    def recommend(self, current_code, chart_evidence=None):
        """
        Analyze a diagnosis code and return specificity recommendation.

        Args:
            current_code: ICD-10 code currently on the chart (e.g., 'E78.5')
            chart_evidence: dict of available evidence, e.g.:
                {
                    'labs': {'a1c': 8.2, 'ldl': 145, 'triglycerides': 220, 'egfr': 45, 'tsh': 6.8},
                    'screenings': {'phq9': 12, 'gad7': 8},
                    'diagnoses': ['I10', 'E11.65', 'N18.3'],
                    'medications': ['levothyroxine', 'metformin'],
                }

        Returns:
            dict with:
                'current_code', 'current_description',
                'recommendations': list of {code, description, supported, evidence_status, reason, enr_diff, denial_risk}
        """
        if chart_evidence is None:
            chart_evidence = {}

        rule = self.rules.get(current_code)
        if not rule:
            return {
                "current_code": current_code,
                "current_description": "No specificity rules available",
                "recommendations": [],
            }

        results = []
        for rec in rule["recommendations"]:
            supported, evidence_status = self._check_evidence(rec["evidence_required"], chart_evidence)
            results.append({
                "recommended_code": rec["recommended_code"],
                "description": rec["description"],
                "supported": supported,
                "evidence_status": evidence_status,
                "reason": rec["reason"],
                "enr_value_diff": rec["enr_value_diff"],
                "denial_risk_reduction": rec["denial_risk_reduction"],
            })

        return {
            "current_code": current_code,
            "current_description": rule["current_description"],
            "recommendations": results,
        }

    def _check_evidence(self, evidence_required, chart_evidence):
        """
        Check if chart evidence supports the recommended code.
        Returns (supported: bool, evidence_status: str).
        """
        labs = chart_evidence.get("labs", {})
        screenings = chart_evidence.get("screenings", {})
        diagnoses = chart_evidence.get("diagnoses", [])
        medications = chart_evidence.get("medications", [])

        ev_type = None
        if "lab" in evidence_required:
            ev_type = "lab"
        elif "screening" in evidence_required:
            ev_type = "screening"
        elif "diagnosis" in evidence_required:
            ev_type = "diagnosis"

        condition = evidence_required.get("condition", "")

        if ev_type == "lab":
            lab_key = evidence_required["lab"]
            return self._check_lab_condition(lab_key, condition, labs, medications)
        elif ev_type == "screening":
            screen_key = evidence_required["screening"]
            return self._check_screening_condition(screen_key, condition, screenings)
        elif ev_type == "diagnosis":
            return self._check_diagnosis_condition(condition, diagnoses, labs)

        return False, f"Missing: evidence type '{ev_type}' not available"

    def _check_lab_condition(self, lab_key, condition, labs, medications):
        """Check lab-based evidence conditions."""
        # Lipid conditions
        if lab_key == "lipid_panel":
            ldl = labs.get("ldl")
            tg = labs.get("triglycerides")
            chol = labs.get("total_cholesterol")

            if ldl is None and tg is None and chol is None:
                return False, "Missing: lipid panel needed to support specificity upgrade"

            if condition == "triglycerides_elevated_and_ldl_elevated":
                if ldl is not None and tg is not None and ldl > 130 and tg > 150:
                    return True, f"Supported: LDL {ldl}, TG {tg} — both elevated"
                return False, f"Missing: both LDL >130 and TG >150 needed (LDL={ldl}, TG={tg})"

            if condition == "cholesterol_and_triglycerides_both_elevated":
                c_val = chol or ldl
                if c_val is not None and tg is not None and c_val > 200 and tg > 150:
                    return True, f"Supported: cholesterol {c_val}, TG {tg} — combined elevation"
                return False, f"Missing: cholesterol >200 and TG >150 needed"

            if condition == "ldl_elevated_tg_normal":
                if ldl is not None and tg is not None and ldl > 130 and tg <= 150:
                    return True, f"Supported: LDL {ldl} elevated, TG {tg} normal"
                return False, f"Missing: LDL >130 with normal TG needed"

        # A1C conditions
        if lab_key == "a1c":
            a1c = labs.get("a1c")
            if a1c is None:
                return False, "Missing: A1C value needed to support code"
            if condition == "a1c_above_7":
                if a1c > 7.0:
                    return True, f"Supported: A1C {a1c}% confirms hyperglycemia"
                return False, f"A1C {a1c}% does not support hyperglycemia (need >7.0)"

        # TSH conditions
        if lab_key == "tsh":
            tsh = labs.get("tsh")
            if tsh is None:
                return False, "Missing: TSH value needed to support specificity"
            if condition == "tsh_elevated_with_treatment":
                has_levo = any("levothyroxine" in m.lower() for m in (medications or []))
                if tsh > 4.5 and has_levo:
                    return True, f"Supported: TSH {tsh} elevated on levothyroxine"
                if not has_levo:
                    return False, "Missing: levothyroxine on medication list needed"
                return False, f"TSH {tsh} not elevated (need >4.5)"

        # eGFR conditions
        if lab_key == "egfr":
            egfr = labs.get("egfr")
            if egfr is None:
                return False, "Missing: eGFR value needed to support CKD staging"
            if condition == "egfr_below_60":
                if egfr < 60:
                    return True, f"Supported: eGFR {egfr} — CKD present"
                return False, f"eGFR {egfr} does not indicate CKD (need <60)"
            if condition == "egfr_30_to_59":
                if 30 <= egfr <= 59:
                    return True, f"Supported: eGFR {egfr} — stage 3"
                return False, f"eGFR {egfr} not in 30-59 range for stage 3"
            if condition == "egfr_15_to_29":
                if 15 <= egfr <= 29:
                    return True, f"Supported: eGFR {egfr} — stage 4"
                return False, f"eGFR {egfr} not in 15-29 range for stage 4"

        return False, f"Missing: lab '{lab_key}' data not available"

    def _check_screening_condition(self, screen_key, condition, screenings):
        """Check screening-based evidence conditions."""
        if screen_key == "phq9":
            score = screenings.get("phq9")
            if score is None:
                return False, "Missing: PHQ-9 score needed to support depression severity"
            if condition == "phq9_5_to_9" and 5 <= score <= 9:
                return True, f"Supported: PHQ-9 {score} — mild"
            if condition == "phq9_10_to_14" and 10 <= score <= 14:
                return True, f"Supported: PHQ-9 {score} — moderate"
            if condition == "phq9_15_plus" and score >= 15:
                return True, f"Supported: PHQ-9 {score} — severe"
            return False, f"PHQ-9 score {score} does not match required range for this code"

        return False, f"Missing: screening '{screen_key}' data not available"

    def _check_diagnosis_condition(self, condition, diagnoses, labs):
        """Check diagnosis-based evidence conditions."""
        if condition == "cardiac_involvement":
            # Look for LVH or echo evidence in diagnoses
            cardiac_codes = {"I51.7", "I42.9", "R94.31"}  # LVH, cardiomyopathy, abnormal EKG
            if any(d in cardiac_codes for d in diagnoses):
                return True, "Supported: cardiac involvement documented"
            return False, "Missing: cardiac involvement (LVH/echo abnormality) needed to support I11.9"

        return False, f"Missing: diagnostic evidence for '{condition}' not documented"

    def batch_recommend(self, diagnosis_codes, chart_evidence=None):
        """
        Analyze multiple diagnosis codes at once.
        Returns list of recommendations (only for codes with available rules).
        """
        results = []
        for code in diagnosis_codes:
            if code in self.rules:
                rec = self.recommend(code, chart_evidence)
                if rec["recommendations"]:
                    results.append(rec)
        return results

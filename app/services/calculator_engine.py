"""
Phase 31 — Clinical Calculator Engine

Computes clinical risk scores from patient EHR data.
Each method returns a standardized result dict:
  {
    'calculator_key': str,
    'score_value': float | None,
    'score_label': str | None,
    'score_detail': dict,
    'inputs_used': dict,
    'data_source': str,
  }

Formulas sourced from CareCompanion_Calculator_Formula_Appendix.md.
"""

import math
import json
import logging
from datetime import datetime, timezone, date
from models import db

logger = logging.getLogger(__name__)


class CalculatorEngine:
    """
    Clinical risk score calculator engine.

    Usage:
        engine = CalculatorEngine()
        result = engine.compute_bmi({'weight_lb': 165, 'height_in': 68})
    """

    # ─────────────────────────────────────────────────────────
    # AUTO-EHR CALCULATORS (no user input required)
    # ─────────────────────────────────────────────────────────

    def compute_bmi(self, vitals_dict: dict) -> dict:
        """
        BMI from height + weight.
        Prefers US units (lb/in); falls back to metric (kg/m).
        Formula: bmi = 703 * weight_lb / (height_in ^ 2)
        """
        try:
            bmi = None
            inputs = {}

            if vitals_dict.get('weight_lb') and vitals_dict.get('height_in'):
                w = float(vitals_dict['weight_lb'])
                h = float(vitals_dict['height_in'])
                if h > 0:
                    bmi = 703 * w / (h * h)
                    inputs = {'weight_lb': w, 'height_in': h, 'method': 'us_units'}
            elif vitals_dict.get('weight_kg') and vitals_dict.get('height_m'):
                w = float(vitals_dict['weight_kg'])
                h = float(vitals_dict['height_m'])
                if h > 0:
                    bmi = w / (h * h)
                    inputs = {'weight_kg': w, 'height_m': h, 'method': 'metric'}

            if bmi is None:
                return self._empty_result('bmi')

            bmi = round(bmi, 1)
            label = self._bmi_label(bmi)
            return {
                'calculator_key': 'bmi',
                'score_value': bmi,
                'score_label': label,
                'score_detail': {'bmi': bmi, 'category': label},
                'inputs_used': inputs,
                'data_source': 'auto_ehr',
            }
        except Exception as e:
            logger.warning('compute_bmi error: %s', e)
            return self._empty_result('bmi')

    def _bmi_label(self, bmi: float) -> str:
        if bmi < 18.5:
            return 'underweight'
        if bmi < 25.0:
            return 'normal'
        if bmi < 30.0:
            return 'overweight'
        if bmi < 35.0:
            return 'obesity_class_1'
        if bmi < 40.0:
            return 'obesity_class_2'
        return 'obesity_class_3'

    def compute_ldl(self, labs_dict: dict, method: str = 'auto') -> dict:
        """
        Calculated LDL from TC, HDL, Triglycerides.
        Friedewald: ldl = tc - hdl - (tg / 5)  [use when tg < 400]
        Sampson 2020: ldl = (tc/0.948) - (hdl/0.971) - ((tg/8.56) + (tg*non_hdl/2140) - (tg^2/16100)) - 9.44  [tg < 800]
        """
        try:
            tc  = float(labs_dict.get('total_cholesterol') or labs_dict.get('tc') or 0)
            hdl = float(labs_dict.get('hdl') or labs_dict.get('hdl_cholesterol') or 0)
            tg  = float(labs_dict.get('triglycerides') or labs_dict.get('tg') or 0)

            if not (tc and hdl and tg):
                return self._empty_result('ldl_calculated')

            inputs = {'tc': tc, 'hdl': hdl, 'tg': tg}
            non_hdl = tc - hdl

            if method == 'auto':
                method = 'friedewald' if tg < 400 else 'sampson_2020'

            if method == 'friedewald':
                if tg >= 400:
                    return {**self._empty_result('ldl_calculated'),
                            'score_detail': {'error': 'TG ≥400; use direct LDL', 'tg': tg}}
                ldl = tc - hdl - (tg / 5.0)
            elif method == 'sampson_2020':
                if tg >= 800:
                    return {**self._empty_result('ldl_calculated'),
                            'score_detail': {'error': 'TG ≥800; use direct LDL', 'tg': tg}}
                ldl = (tc / 0.948) - (hdl / 0.971) - (
                    (tg / 8.56) + (tg * non_hdl / 2140.0) - (tg ** 2 / 16100.0)
                ) - 9.44
            else:
                return self._empty_result('ldl_calculated')

            ldl = round(ldl, 1)
            label = self._ldl_label(ldl)
            return {
                'calculator_key': 'ldl_calculated',
                'score_value': ldl,
                'score_label': label,
                'score_detail': {
                    'ldl': ldl, 'formula': method,
                    'tc': tc, 'hdl': hdl, 'tg': tg, 'non_hdl': round(non_hdl, 1),
                    'category': label,
                },
                'inputs_used': {**inputs, 'method': method},
                'data_source': 'auto_ehr',
            }
        except Exception as e:
            logger.warning('compute_ldl error: %s', e)
            return self._empty_result('ldl_calculated')

    def _ldl_label(self, ldl: float) -> str:
        if ldl < 70:
            return 'optimal'
        if ldl < 100:
            return 'near_optimal'
        if ldl < 130:
            return 'borderline_high'
        if ldl < 160:
            return 'high'
        if ldl < 190:
            return 'very_high'
        return 'severe'  # ≥190 possible FH

    def compute_pack_years(self, social_history_dict: dict) -> dict:
        """
        Pack years from structured smoking history.
        Formula: pack_years = (cigarettes_per_day / 20) * years_smoked
        """
        try:
            status = social_history_dict.get('tobacco_status', 'never')
            if status in ('never', 'non_smoker', None):
                return {
                    'calculator_key': 'pack_years',
                    'score_value': 0,
                    'score_label': 'never_smoker',
                    'score_detail': {'status': 'never'},
                    'inputs_used': {'tobacco_status': status},
                    'data_source': 'auto_ehr',
                }

            # Try direct pack_years field first
            direct = social_history_dict.get('tobacco_pack_years')
            if direct is not None:
                py = float(direct)
                return {
                    'calculator_key': 'pack_years',
                    'score_value': round(py, 1),
                    'score_label': self._pack_years_label(py, status),
                    'score_detail': {'pack_years': py, 'source': 'structured_field'},
                    'inputs_used': {'tobacco_pack_years': py, 'tobacco_status': status},
                    'data_source': 'auto_ehr',
                }

            # Compute from cpd + years
            cpd = float(social_history_dict.get('cigarettes_per_day') or 0)
            yrs = float(social_history_dict.get('years_smoked') or 0)
            if cpd > 0 and yrs > 0:
                py = (cpd / 20.0) * yrs
                return {
                    'calculator_key': 'pack_years',
                    'score_value': round(py, 1),
                    'score_label': self._pack_years_label(py, status),
                    'score_detail': {
                        'pack_years': round(py, 1),
                        'cpd': cpd, 'years': yrs,
                        'source': 'computed',
                    },
                    'inputs_used': {'cpd': cpd, 'years': yrs, 'tobacco_status': status},
                    'data_source': 'auto_ehr',
                }

            return self._empty_result('pack_years')
        except Exception as e:
            logger.warning('compute_pack_years error: %s', e)
            return self._empty_result('pack_years')

    def _pack_years_label(self, py: float, status: str) -> str:
        prefix = 'former_' if status in ('former', 'ex_smoker') else ''
        if py >= 20:
            return prefix + 'heavy_smoker'
        if py >= 10:
            return prefix + 'moderate_smoker'
        return prefix + 'light_smoker'

    def compute_prevent(self, demographics: dict, vitals: dict,
                        labs: dict, meds: dict) -> dict:
        """
        AHA PREVENT 10-year total CVD risk.
        Khan SS et al. Circulation 2023. CIRCULATIONAHA.123.067626

        Sex-specific logistic regression with variable transformations.
        All inputs from structured EHR data.
        """
        try:
            age  = float(demographics.get('age') or demographics.get('age_years') or 0)
            sex  = str(demographics.get('sex', '')).lower()
            sbp  = float(vitals.get('systolic_bp') or vitals.get('sbp') or 0)
            tc   = float(labs.get('total_cholesterol') or labs.get('tc') or 0)
            hdl  = float(labs.get('hdl') or labs.get('hdl_cholesterol') or 0)
            egfr = float(labs.get('egfr') or labs.get('eGFR') or 90)

            dm       = bool(meds.get('has_diabetes') or demographics.get('has_diabetes'))
            smoking  = str(demographics.get('smoking_status', 'never')).lower() in ('current', 'yes', '1')
            antihtn  = bool(meds.get('antihypertensive') or meds.get('on_antihtn'))
            statin   = bool(meds.get('statin') or meds.get('on_statin'))

            if not (30 <= age <= 79 and sbp > 0 and tc > 0 and hdl > 0):
                return {**self._empty_result('prevent'),
                        'score_detail': {'reason': 'missing_required_inputs',
                                         'age_valid': 30 <= age <= 79}}

            # Convert TC/HDL from mg/dL → mmol/L if values suggest mg/dL
            if tc > 10:   # mg/dL range vs mmol/L
                tc  = tc  / 38.67
                hdl = hdl / 38.67

            # Variable transformations
            cage   = (age - 55) / 10.0
            cnhdl  = tc - hdl - 3.5
            chdl   = (hdl - 1.3) / 0.3
            csbp   = (min(sbp, 110) - 110) / 20.0
            csbp2  = (max(sbp, 110) - 130) / 20.0
            cegfr  = (min(egfr, 60) - 60) / -15.0
            cegfr2 = (max(egfr, 60) - 90) / -15.0

            if 'f' in sex:  # female
                coef = {
                    'cage': 0.7939, 'cnhdl': 0.0305, 'chdl': -0.1607,
                    'csbp': -0.2394, 'csbp2': 0.3600, 'diabetes': 0.8668,
                    'smoking': 0.5361, 'cegfr': 0.6046, 'cegfr2': 0.0434,
                    'antihtn': 0.3152, 'statin': -0.1478,
                    'csbp2_x_antihtn': -0.0664, 'cnhdl_x_statin': 0.1198,
                    'cage_x_cnhdl': -0.0820, 'cage_x_chdl': 0.0307,
                    'cage_x_csbp2': -0.0946, 'cage_x_diabetes': -0.2706,
                    'cage_x_smoking': -0.0787, 'cage_x_cegfr': -0.1638,
                    'constant': -3.3077,
                }
            else:  # male
                coef = {
                    'cage': 0.7689, 'cnhdl': 0.0736, 'chdl': -0.0954,
                    'csbp': -0.4347, 'csbp2': 0.3363, 'diabetes': 0.7693,
                    'smoking': 0.4387, 'cegfr': 0.5379, 'cegfr2': 0.0165,
                    'antihtn': 0.2889, 'statin': -0.1337,
                    'csbp2_x_antihtn': -0.0476, 'cnhdl_x_statin': 0.1503,
                    'cage_x_cnhdl': -0.0518, 'cage_x_chdl': 0.0191,
                    'cage_x_csbp2': -0.1049, 'cage_x_diabetes': -0.2252,
                    'cage_x_smoking': -0.0895, 'cage_x_cegfr': -0.1543,
                    'constant': -3.0312,
                }

            x = (
                coef['cage']   * cage +
                coef['cnhdl']  * cnhdl +
                coef['chdl']   * chdl +
                coef['csbp']   * csbp +
                coef['csbp2']  * csbp2 +
                coef['diabetes']   * int(dm) +
                coef['smoking']    * int(smoking) +
                coef['cegfr']  * cegfr +
                coef['cegfr2'] * cegfr2 +
                coef['antihtn']    * int(antihtn) +
                coef['statin']     * int(statin) +
                coef['csbp2_x_antihtn']  * csbp2 * int(antihtn) +
                coef['cnhdl_x_statin']   * cnhdl * int(statin) +
                coef['cage_x_cnhdl']     * cage * cnhdl +
                coef['cage_x_chdl']      * cage * chdl +
                coef['cage_x_csbp2']     * cage * csbp2 +
                coef['cage_x_diabetes']  * cage * int(dm) +
                coef['cage_x_smoking']   * cage * int(smoking) +
                coef['cage_x_cegfr']     * cage * cegfr +
                coef['constant']
            )
            risk_pct = round((math.exp(x) / (1 + math.exp(x))) * 100, 1)
            label    = self._prevent_label(risk_pct)

            return {
                'calculator_key': 'prevent',
                'score_value': risk_pct,
                'score_label': label,
                'score_detail': {
                    'risk_10yr_pct': risk_pct,
                    'risk_tier': label,
                    'sex_model': 'female' if 'f' in sex else 'male',
                    'on_statin': statin,
                    'logistic_x': round(x, 4),
                },
                'inputs_used': {
                    'age': age, 'sex': sex, 'sbp': sbp,
                    'tc_mmol': round(tc, 2), 'hdl_mmol': round(hdl, 2),
                    'egfr': egfr, 'dm': dm, 'smoking': smoking,
                    'antihtn': antihtn, 'statin': statin,
                },
                'data_source': 'auto_ehr',
            }
        except Exception as e:
            logger.warning('compute_prevent error: %s', e)
            return self._empty_result('prevent')

    def _prevent_label(self, risk_pct: float) -> str:
        if risk_pct < 5:
            return 'low'
        if risk_pct < 7.5:
            return 'borderline'
        if risk_pct < 20:
            return 'intermediate'
        return 'high'

    # ─────────────────────────────────────────────────────────
    # QUESTIONNAIRE CALCULATORS (patient-reported)
    # ─────────────────────────────────────────────────────────

    # GAD-7, C-SSRS, GDS-15, EPDS, AUDIT-C, CRAFFT, CAT, AIRQ, MoCA, etc.
    # All follow the same sum-of-items pattern with severity bands.

    QUESTIONNAIRE_DEFS = {
        'gad7': {
            'name': 'GAD-7', 'items': 7, 'max': 21,
            'bands': [
                (0, 4, 'minimal'), (5, 9, 'mild'),
                (10, 14, 'moderate'), (15, 21, 'severe'),
            ],
        },
        'gds15': {
            'name': 'GDS-15 (Geriatric Depression)', 'items': 15, 'max': 15,
            'bands': [
                (0, 4, 'normal'), (5, 8, 'mild_depression'),
                (9, 11, 'moderate_depression'), (12, 15, 'severe_depression'),
            ],
        },
        'epds': {
            'name': 'Edinburgh Postnatal Depression', 'items': 10, 'max': 30,
            'bands': [
                (0, 8, 'unlikely_pnd'), (9, 11, 'possible_pnd'),
                (12, 30, 'likely_pnd'),
            ],
        },
        'audit_c': {
            'name': 'AUDIT-C Alcohol Screen', 'items': 3, 'max': 12,
            'bands': [
                (0, 2, 'negative'), (3, 4, 'positive_female'),
                (4, 12, 'positive_male'),
            ],
            # AUDIT-C: positive if ≥3 for women, ≥4 for men
        },
        'cat': {
            'name': 'COPD Assessment Test', 'items': 8, 'max': 40,
            'bands': [
                (0, 9, 'low_impact'), (10, 20, 'medium_impact'),
                (21, 30, 'high_impact'), (31, 40, 'very_high_impact'),
            ],
        },
        'airq': {
            'name': 'Asthma Impact and Recognition Questionnaire', 'items': 5, 'max': 25,
            'bands': [
                (0, 5, 'well_controlled'), (6, 15, 'partially_controlled'),
                (16, 25, 'uncontrolled'),
            ],
        },
        'mmrc': {
            'name': 'mMRC Dyspnea Scale', 'items': 1, 'max': 4,
            'bands': [
                (0, 0, 'none'), (1, 1, 'mild'), (2, 2, 'moderate'),
                (3, 3, 'severe'), (4, 4, 'very_severe'),
            ],
        },
        'crafft': {
            'name': 'CRAFFT Substance Use Screen', 'items': 6, 'max': 6,
            'bands': [
                (0, 1, 'low_risk'), (2, 6, 'high_risk'),
            ],
        },
        'cssrs': {
            'name': 'Columbia Suicide Severity Rating Scale', 'items': 6, 'max': 6,
            'bands': [
                (0, 0, 'low_risk'), (1, 2, 'moderate_risk'), (3, 6, 'high_risk'),
            ],
        },
    }

    def compute_questionnaire(self, calculator_key: str, responses: dict) -> dict:
        """
        Generic questionnaire scorer.
        responses: {item_1: 2, item_2: 1, ...}  OR  {'total': 12}
        """
        # Special-purpose dispatchers for calculators with non-trivial logic
        if calculator_key == 'cssrs':
            return self.compute_cssrs(responses)
        if calculator_key == 'audit_c':
            return self.compute_audit_c(
                responses, sex=responses.get('sex', 'unknown')
            )
        try:
            defn = self.QUESTIONNAIRE_DEFS.get(calculator_key)
            if not defn:
                return self._empty_result(calculator_key)

            # Accept pre-summed total
            if 'total' in responses:
                total = int(responses['total'])
            else:
                items = defn['items']
                total = sum(
                    int(responses.get(f'item_{i}', responses.get(str(i), 0)))
                    for i in range(1, items + 1)
                )

            label = self._band_label(total, defn['bands'])
            return {
                'calculator_key': calculator_key,
                'score_value': float(total),
                'score_label': label,
                'score_detail': {
                    'total': total, 'max': defn['max'],
                    'severity': label, 'name': defn['name'],
                },
                'inputs_used': responses,
                'data_source': 'manual',
            }
        except Exception as e:
            logger.warning('compute_questionnaire(%s) error: %s', calculator_key, e)
            return self._empty_result(calculator_key)

    def compute_cssrs(self, responses: dict) -> dict:
        """
        Phase 36.4 — C-SSRS risk stratification with branching logic.
        High risk: Q4 OR Q5 OR Q6 endorsed.
        Moderate risk: Q1 or Q2 endorsed but not Q4/Q5/Q6.
        Low risk: all NO.
        """
        import re

        def _bool_val(key):
            v = responses.get(key, '0')
            s = str(v).strip().lower()
            return s in ('1', 'true', 'yes')

        q = {k: _bool_val(k) for k in ('q1', 'q2', 'q3', 'q4', 'q5', 'q6')}

        if q['q4'] or q['q5'] or q['q6']:
            label = 'high_risk'
        elif q['q1'] or q['q2'] or q['q3']:
            label = 'moderate_risk'
        else:
            label = 'low_risk'

        score = sum(1 for v in q.values() if v)
        return {
            'calculator_key': 'cssrs',
            'score_value': float(score),
            'score_label': label,
            'score_detail': {
                'risk_level': label,
                'items': {k: 1 if v else 0 for k, v in q.items()},
                'high_risk_criteria': q['q4'] or q['q5'] or q['q6'],
            },
            'inputs_used': responses,
            'data_source': 'manual',
        }

    def compute_audit_c(self, responses: dict, sex: str = 'unknown') -> dict:
        """
        Phase 36.5 — AUDIT-C alcohol screening with gender-aware cutoff.
        Extracts numeric score from option strings like 'Never (0)' or '2-3 times/week (3)'.
        Cutoff: ≥3 for women, ≥4 for men.
        """
        import re as _re
        total = 0
        for i in range(1, 4):
            raw = responses.get(f'item_{i}', responses.get(str(i), 0))
            if isinstance(raw, str):
                m = _re.search(r'\((\d+)\)', raw)
                if m:
                    total += int(m.group(1))
                else:
                    try:
                        total += int(raw)
                    except (ValueError, TypeError):
                        pass
            else:
                try:
                    total += int(raw)
                except (ValueError, TypeError):
                    pass

        sex_lower = str(sex).lower()
        if sex_lower in ('female', 'f', 'woman', 'women'):
            cutoff, sex_code = 3, 'female'
            label = 'positive_female' if total >= cutoff else 'negative'
        elif sex_lower in ('male', 'm', 'man', 'men'):
            cutoff, sex_code = 4, 'male'
            label = 'positive_male' if total >= cutoff else 'negative'
        else:
            cutoff, sex_code = 3, 'unknown'
            label = 'positive' if total >= cutoff else 'negative'

        return {
            'calculator_key': 'audit_c',
            'score_value': float(total),
            'score_label': label,
            'score_detail': {
                'total': total, 'max': 12,
                'cutoff_used': cutoff, 'sex': sex_code,
            },
            'inputs_used': responses,
            'data_source': 'manual',
        }

    def _band_label(self, score: int, bands: list) -> str:
        for lo, hi, label in bands:
            if lo <= score <= hi:
                return label
        return 'unknown'

    # ─────────────────────────────────────────────────────────
    # RULE-BASED CALCULATORS (clinician-assessed)
    # ─────────────────────────────────────────────────────────

    RULE_DEFS = {
        'wells_dvt': {
            'name': 'Wells DVT',
            'items': {
                'active_cancer': 1,
                'paralysis_paresis_or_recent_lower_extremity_cast': 1,
                'recently_bedridden_over_3_days_or_major_surgery_within_12_weeks': 1,
                'localized_tenderness_along_deep_venous_system': 1,
                'entire_leg_swollen': 1,
                'calf_swelling_over_3_cm_vs_asymptomatic_leg': 1,
                'pitting_edema_confined_to_symptomatic_leg': 1,
                'collateral_superficial_veins_nonvaricose': 1,
                'previously_documented_dvt': 1,
                'alternative_diagnosis_at_least_as_likely_as_dvt': -2,
            },
            'bands': [
                (None, 0, 'low'), (1, 2, 'moderate'), (3, None, 'high'),
            ],
            'interpretation': {
                'low': 'Low probability DVT — consider D-dimer',
                'moderate': 'Moderate probability — D-dimer or ultrasound',
                'high': 'High probability — compression ultrasound recommended',
            },
        },
        'perc': {
            'name': 'PERC Rule (PE Rule-Out)',
            # PERC: if ALL criteria met (all = 0/no), PE ruled out without further testing
            'items': {
                'age_over_50': 1,
                'hr_over_100': 1,
                'oxygen_sat_under_95': 1,
                'unilateral_leg_swelling': 1,
                'hemoptysis': 1,
                'recent_surgery_or_trauma': 1,
                'prior_pe_or_dvt': 1,
                'estrogen_use': 1,
            },
            'bands': [(0, 0, 'pe_excluded'), (1, 8, 'not_excluded')],
            'interpretation': {
                'pe_excluded': 'All PERC criteria negative — PE ruled out without D-dimer',
                'not_excluded': 'PERC positive — further evaluation required',
            },
        },
        'ottawa_ankle': {
            'name': 'Ottawa Ankle Rules',
            'items': {
                'bone_tenderness_lateral_malleolus': 1,
                'bone_tenderness_medial_malleolus': 1,
                'unable_to_weight_bear_4_steps': 1,
            },
            'bands': [(0, 0, 'no_xray'), (1, 3, 'xray_indicated')],
            'interpretation': {
                'no_xray': 'Ottawa negative — no X-ray needed',
                'xray_indicated': 'Ottawa positive — ankle X-ray recommended',
            },
        },
        'katz_adl': {
            'name': 'Katz ADL (Activities of Daily Living)',
            'items': {
                'bathing': 1, 'dressing': 1, 'toileting': 1,
                'transferring': 1, 'continence': 1, 'feeding': 1,
            },
            'bands': [
                (6, 6, 'independent'), (4, 5, 'mild_dependence'),
                (2, 3, 'moderate_dependence'), (0, 1, 'severe_dependence'),
            ],
            'interpretation': {
                'independent': '6/6 — Fully independent',
                'mild_dependence': '4-5/6 — Mild functional dependence',
                'moderate_dependence': '2-3/6 — Moderate functional dependence',
                'severe_dependence': '0-1/6 — Severe functional dependence',
            },
        },
    }

    def compute_rule_calculator(self, calculator_key: str, findings: dict) -> dict:
        """
        Generic rule-based (point rule) calculator.
        findings: {criterion_key: True/False}  or  {criterion_key: 1/0}
        """
        try:
            defn = self.RULE_DEFS.get(calculator_key)
            if not defn:
                return self._empty_result(calculator_key)

            items = defn['items']
            total = 0
            components = {}
            for item_key, points in items.items():
                val = findings.get(item_key, False)
                present = bool(val) and val not in (0, '0', 'no', 'No', 'false', 'False')
                contribution = points if present else 0
                total += contribution
                components[item_key] = {'present': present, 'points': contribution}

            bands = defn['bands']
            label = self._rule_band_label(total, bands)
            interpretation = defn.get('interpretation', {}).get(label, '')

            return {
                'calculator_key': calculator_key,
                'score_value': float(total),
                'score_label': label,
                'score_detail': {
                    'total': total,
                    'label': label,
                    'interpretation': interpretation,
                    'components': components,
                    'name': defn['name'],
                },
                'inputs_used': findings,
                'data_source': 'manual',
            }
        except Exception as e:
            logger.warning('compute_rule_calculator(%s) error: %s', calculator_key, e)
            return self._empty_result(calculator_key)

    def _rule_band_label(self, score: int, bands: list) -> str:
        for lo, hi, label in bands:
            if (lo is None or score >= lo) and (hi is None or score <= hi):
                return label
        return 'unknown'

    # ─────────────────────────────────────────────────────────
    # ORCHESTRATION
    # ─────────────────────────────────────────────────────────

    def run_auto_scores(self, mrn: str, user_id: int) -> list:
        """
        Runs all 4 auto_ehr calculators for a patient.
        Persists results to CalculatorResult table (supersedes prior current results).
        Returns list of result dicts.
        """
        from models.calculator import CalculatorResult
        from models.patient import PatientRecord, PatientVitals, PatientLabResult, PatientSocialHistory

        results = []
        try:
            with db.session.no_autoflush:
                # Gather patient data
                pt = PatientRecord.query.filter_by(mrn=mrn).first()
                if not pt:
                    return []

                # Latest vitals
                vitals_row = (
                    PatientVitals.query
                    .filter_by(mrn=mrn)
                    .order_by(PatientVitals.recorded_at.desc())
                    .first()
                )
                vitals = {}
                if vitals_row:
                    vitals = {
                        'weight_lb': vitals_row.weight,
                        'height_in': vitals_row.height,
                        'systolic_bp': vitals_row.systolic_bp,
                    }

                # Latest labs
                labs = {}
                for lab in (PatientLabResult.query
                            .filter_by(mrn=mrn)
                            .order_by(PatientLabResult.result_date.desc())
                            .limit(50)
                            .all()):
                    loinc = (lab.loinc_code or '').strip()
                    # Map LOINC codes to lab keys
                    loinc_map = {
                        '2093-3': 'total_cholesterol', '2085-9': 'hdl',
                        '2571-8': 'triglycerides', '2160-0': 'creatinine',
                        '33914-3': 'egfr', '4548-4': 'a1c',
                    }
                    field = loinc_map.get(loinc)
                    if field and field not in labs:
                        try:
                            labs[field] = float(lab.result_value)
                        except (ValueError, TypeError):
                            pass

                # Social history
                soc_row = (
                    PatientSocialHistory.query
                    .filter_by(mrn=mrn)
                    .order_by(PatientSocialHistory.created_at.desc())
                    .first()
                )
                social = {}
                if soc_row:
                    social = {
                        'tobacco_status': soc_row.tobacco_status,
                        'tobacco_pack_years': soc_row.tobacco_pack_years,
                        'cigarettes_per_day': soc_row.cigarettes_per_day,
                        'years_smoked': soc_row.years_smoked,
                    }

                # Demographics
                demo = {}
                if pt:
                    demo = {
                        'age': self._age_from_dob(pt.date_of_birth),
                        'sex': getattr(pt, 'sex', '') or getattr(pt, 'gender', ''),
                        'smoking_status': social.get('tobacco_status', 'never'),
                    }

                # Run calculators
                calcs = [
                    ('bmi', lambda: self.compute_bmi(vitals)),
                    ('ldl_calculated', lambda: self.compute_ldl(labs)),
                    ('pack_years', lambda: self.compute_pack_years(social)),
                    ('prevent', lambda: self.compute_prevent(demo, vitals, labs, {})),
                ]

                for key, fn in calcs:
                    try:
                        result = fn()
                        if result.get('score_value') is not None:
                            self._persist_result(result, mrn, user_id)
                        results.append(result)
                    except Exception as e:
                        logger.warning('run_auto_scores(%s) %s error: %s', mrn, key, e)

                db.session.commit()
        except Exception as e:
            logger.error('run_auto_scores error for mrn=%s: %s', mrn, e)
            db.session.rollback()

        return results

    def _persist_result(self, result: dict, mrn: str, user_id: int):
        """Saves result to DB, marking prior result as not current."""
        from models.calculator import CalculatorResult

        # Supersede existing
        (CalculatorResult.query
         .filter_by(mrn=mrn, calculator_key=result['calculator_key'], is_current=True)
         .update({'is_current': False}))

        row = CalculatorResult(
            user_id=user_id,
            mrn=mrn,
            calculator_key=result['calculator_key'],
            score_value=result.get('score_value'),
            score_label=result.get('score_label'),
            score_detail=json.dumps(result.get('score_detail', {})),
            input_snapshot=json.dumps(result.get('inputs_used', {})),
            data_source=result.get('data_source', 'auto_ehr'),
            is_current=True,
        )
        db.session.add(row)

    def get_latest_scores(self, mrn: str, user_id: int) -> dict:
        """Returns {calculator_key: result_dict} for all current results for a patient."""
        from models.calculator import CalculatorResult
        rows = CalculatorResult.query.filter_by(mrn=mrn, is_current=True).all()
        return {r.calculator_key: r.to_dict() for r in rows}

    def get_prefilled_inputs(self, calculator_key: str, mrn: str) -> dict:
        """
        Returns auto-fillable EHR values for a semi-auto calculator's inputs.

        Returns a flat dict: {input_key: value}.
        Keys present in the registry with ``source: 'auto'`` that cannot be
        resolved from EHR data are omitted (not returned as None) so the
        template renders the field as an empty editable input.
        """
        from models.patient import (
            PatientRecord, PatientVitals, PatientLabResult,
            PatientSocialHistory, PatientMedication, PatientDiagnosis,
        )

        try:
            pt = PatientRecord.query.filter_by(mrn=mrn).first()
            if not pt:
                return {}

            # ── Age & sex ────────────────────────────────────────────────
            dob_str = getattr(pt, 'patient_dob', '') or ''
            age = self._age_from_dob(dob_str) if dob_str else None
            sex = (getattr(pt, 'patient_sex', '') or '').strip().lower()

            # ── Latest vital values by name ──────────────────────────────
            _seen_vitals: dict = {}
            for vrow in (PatientVitals.query.filter_by(mrn=mrn)
                         .order_by(PatientVitals.measured_at.desc()).all()):
                vname = (vrow.vital_name or '').strip()
                if vname and vname not in _seen_vitals:
                    try:
                        _seen_vitals[vname] = float(vrow.vital_value)
                    except (ValueError, TypeError):
                        _seen_vitals[vname] = vrow.vital_value

            sbp = _seen_vitals.get('BP Systolic')
            dbp = _seen_vitals.get('BP Diastolic')
            hr  = _seen_vitals.get('Heart Rate')
            spo2 = _seen_vitals.get('O2 Sat')
            raw_bmi = _seen_vitals.get('BMI')
            wt  = _seen_vitals.get('Weight')
            ht  = _seen_vitals.get('Height')

            # Compute BMI if not directly stored
            bmi = raw_bmi
            if bmi is None and wt and ht:
                try:
                    bmi = round((float(wt) / (float(ht) ** 2)) * 703, 1)
                except (TypeError, ZeroDivisionError):
                    pass

            # ── Latest labs by LOINC ─────────────────────────────────────
            LOINC_MAP = {
                '2093-3': 'total_cholesterol', '2085-9': 'hdl',
                '2571-8': 'triglycerides', '2160-0': 'creatinine',
                '33914-3': 'egfr', '4548-4': 'a1c', '2345-7': 'glucose',
                '13457-7': 'ldl', '2089-1': 'ldl',
            }
            labs: dict = {}
            for lab in (PatientLabResult.query.filter_by(mrn=mrn)
                        .order_by(PatientLabResult.result_date.desc())
                        .limit(100).all()):
                loinc = (lab.loinc_code or '').strip()
                field = LOINC_MAP.get(loinc)
                if field and field not in labs:
                    try:
                        labs[field] = float(lab.result_value)
                    except (ValueError, TypeError):
                        pass

            # ── Social history ───────────────────────────────────────────
            soc = (PatientSocialHistory.query.filter_by(mrn=mrn)
                   .order_by(PatientSocialHistory.created_at.desc()).first())
            smoker = False
            if soc:
                smoker = (soc.tobacco_status or '').lower() in ('current', 'yes')

            # ── Diagnoses (for hypertension / diabetes flags) ─────────────
            def _has_diagnosis(keywords) -> bool:
                return bool(PatientDiagnosis.query.filter_by(mrn=mrn).filter(
                    db.or_(*[
                        PatientDiagnosis.diagnosis_name.ilike(f'%{kw}%')
                        for kw in keywords
                    ])
                ).first())

            # ── Medications (for bp_meds / dm_meds flags) ────────────────
            BP_MED_KEYWORDS = [
                'lisinopril', 'amlodipine', 'metoprolol', 'losartan', 'valsartan',
                'atenolol', 'hydrochlorothiazide', 'furosemide', 'carvedilol',
                'enalapril', 'ramipril', 'olmesartan', 'nifedipine',
            ]
            DM_MED_KEYWORDS = [
                'metformin', 'insulin', 'glipizide', 'glimepiride', 'sitagliptin',
                'empagliflozin', 'liraglutide', 'dapagliflozin', 'canagliflozin',
                'pioglitazone', 'semaglutide',
            ]

            def _has_med(keywords) -> bool:
                return bool(PatientMedication.query.filter_by(mrn=mrn, status='active').filter(
                    db.or_(*[
                        PatientMedication.drug_name.ilike(f'%{kw}%')
                        for kw in keywords
                    ])
                ).first())

            # ── Route by calculator ───────────────────────────────────────
            if calculator_key == 'stop_bang':
                result = {}
                if bmi is not None:
                    result['bmi_over_35'] = bmi > 35
                if age is not None:
                    result['age_over_50'] = age > 50
                result['male'] = sex in ('m', 'male')
                if sbp is not None:
                    result['pressure'] = sbp >= 140
                return result

            if calculator_key == 'perc':
                result = {}
                if age is not None:
                    result['age_under_50'] = age < 50
                if hr is not None:
                    result['hr_under_100'] = float(hr) < 100
                if spo2 is not None:
                    result['spo2_95_or_above'] = float(spo2) >= 95
                return result

            if calculator_key == 'pcp_hf':
                result = {}
                if age is not None:
                    result['age'] = round(age, 1)
                if sex:
                    result['sex'] = 'male' if sex in ('m', 'male') else 'female'
                if bmi is not None:
                    result['bmi'] = round(float(bmi), 1)
                if sbp is not None:
                    result['sbp'] = sbp
                result['smoker'] = smoker
                if labs.get('glucose') is not None:
                    result['glucose'] = labs['glucose']
                if labs.get('total_cholesterol') is not None:
                    result['total_cholesterol'] = labs['total_cholesterol']
                if labs.get('hdl') is not None:
                    result['hdl'] = labs['hdl']
                if labs.get('egfr') is not None:
                    result['egfr'] = labs['egfr']
                result['bp_meds'] = _has_med(BP_MED_KEYWORDS)
                result['dm_meds'] = _has_med(DM_MED_KEYWORDS)
                return result

            if calculator_key == 'ada_risk':
                result = {}
                if age is not None:
                    result['age'] = round(age, 1)
                if sex:
                    result['sex'] = 'male' if sex in ('m', 'male') else 'female'
                if bmi is not None:
                    result['bmi'] = round(float(bmi), 1)
                htn = (sbp is not None and sbp >= 140) or _has_diagnosis(['hypertension'])
                result['hypertension'] = htn
                return result

            if calculator_key == 'aap_htn':
                result = {}
                if sbp is not None:
                    result['sbp'] = sbp
                if dbp is not None:
                    result['dbp'] = dbp
                if age is not None:
                    result['age'] = round(age, 1)
                return result

            if calculator_key == 'gail_model':
                result = {}
                if age is not None:
                    result['age'] = round(age, 1)
                return result

            if calculator_key == 'dutch_fh':
                result = {}
                ldl_val = labs.get('ldl')
                if ldl_val is not None:
                    result['ldl'] = ldl_val
                return result

            if calculator_key == 'peak_flow':
                result = {}
                if age is not None:
                    result['age'] = round(age, 1)
                if ht is not None:
                    result['height_cm'] = round(float(ht) * 2.54, 1)
                if sex:
                    result['sex'] = 'male' if sex in ('m', 'male') else 'female'
                return result

            return {}

        except Exception as exc:
            logger.warning('get_prefilled_inputs(%s, %s): %s', calculator_key, mrn, exc)
            return {}

    def get_context_hints(self, calculator_key: str, patient_data: dict) -> list:
        """
        Returns contextual clinical hints for a calculator based on patient data.

        Parameters
        ----------
        calculator_key : str
        patient_data   : dict — may include: age, has_diabetes, sex, diagnoses, …

        Returns
        -------
        list of dicts: {'type': 'info'|'warning'|'error', 'text': str}
        """
        hints = []
        age = patient_data.get('age') or 0

        if calculator_key == 'ada_risk':
            if patient_data.get('has_diabetes'):
                hints.append({
                    'type': 'warning',
                    'text': ('Patient already diagnosed with diabetes. '
                             'This screening tool is for undiagnosed patients.'),
                })

        elif calculator_key == 'prevent':
            try:
                a = float(age)
                if a < 30 or a > 79:
                    hints.append({
                        'type': 'info',
                        'text': 'PREVENT equations validated for ages 30-79.',
                    })
            except (TypeError, ValueError):
                pass

        elif calculator_key == 'perc':
            hints.append({
                'type': 'info',
                'text': 'Use only in low pre-test probability setting.',
            })

        elif calculator_key == 'aap_htn':
            try:
                if float(age) < 13:
                    hints.append({
                        'type': 'warning',
                        'text': ('Requires BP percentile tables (Rosner 2008) '
                                 '— not yet implemented for ages < 13.'),
                    })
            except (TypeError, ValueError):
                pass

        elif calculator_key == 'gail_model':
            hints.append({
                'type': 'info',
                'text': ('Full Gail Model coefficients require NCI-licensed implementation. '
                         'Missing coefficients prevent automated scoring.'),
            })

        return hints

    # ─────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────

    def _empty_result(self, key: str) -> dict:
        return {
            'calculator_key': key,
            'score_value': None,
            'score_label': None,
            'score_detail': {},
            'inputs_used': {},
            'data_source': 'auto_ehr',
        }

    def _age_from_dob(self, dob) -> float:
        if not dob:
            return 0
        if isinstance(dob, str):
            try:
                dob = datetime.strptime(dob[:10], '%Y-%m-%d').date()
            except ValueError:
                return 0
        today = date.today()
        return (today - dob).days / 365.25

    # ─────────────────────────────────────────────────────────
    # Phase 35 — Threshold alerts + Score change detection
    # ─────────────────────────────────────────────────────────

    def check_threshold_alerts(self, scores_dict: dict) -> list:
        """
        Check computed scores against clinical thresholds.

        Parameters
        ----------
        scores_dict : dict
            {calculator_key: result_dict | CalculatorResult.to_dict()}

        Returns
        -------
        list of alert dicts:
            {'key', 'title', 'text', 'severity': 'high'|'moderate'|'info', 'color': str}
        """
        alerts = []

        def _val(key):
            """Get score_value from scores_dict for key (or key + '_calculated')."""
            entry = scores_dict.get(key) or scores_dict.get(key + '_calculated') or {}
            if isinstance(entry, dict):
                return entry.get('score_value')
            return getattr(entry, 'score_value', None)

        # BMI
        bmi_val = _val('bmi')
        if bmi_val is not None:
            if bmi_val >= 40:
                alerts.append({
                    'key': 'bmi_obese3',
                    'title': 'Obesity Class III (BMI ≥ 40)',
                    'text': (f'BMI {bmi_val:.1f} — Obesity Class III. '
                             'Consider bariatric referral.'),
                    'severity': 'high', 'color': 'red',
                })
            elif bmi_val >= 30:
                alerts.append({
                    'key': 'bmi_obese',
                    'title': 'Obesity (BMI ≥ 30)',
                    'text': (f'BMI {bmi_val:.1f} — Obesity. '
                             'Document in problem list for HCC capture.'),
                    'severity': 'moderate', 'color': 'orange',
                })

        # LDL
        ldl_val = _val('ldl')
        if ldl_val is not None:
            if ldl_val >= 190:
                alerts.append({
                    'key': 'ldl_fh',
                    'title': 'Very High LDL (≥ 190 mg/dL)',
                    'text': (f'LDL {ldl_val:.0f} mg/dL — Evaluate for familial '
                             'hypercholesterolemia (Dutch FH criteria).'),
                    'severity': 'high', 'color': 'red',
                })
            elif ldl_val >= 160:
                alerts.append({
                    'key': 'ldl_high',
                    'title': 'High LDL (≥ 160 mg/dL)',
                    'text': (f'LDL {ldl_val:.0f} mg/dL — ACC/AHA recommends '
                             'statin therapy discussion.'),
                    'severity': 'moderate', 'color': 'orange',
                })

        # PREVENT CVD Risk
        prev_val = _val('prevent')
        if prev_val is not None:
            if prev_val >= 20:
                alerts.append({
                    'key': 'prevent_high',
                    'title': 'High CVD Risk (PREVENT ≥ 20%)',
                    'text': (f'PREVENT 10yr CVD risk {prev_val:.1f}% — High risk. '
                             'Intensive statin therapy recommended (ACC/AHA).'),
                    'severity': 'high', 'color': 'red',
                })
            elif prev_val >= 7.5:
                alerts.append({
                    'key': 'prevent_moderate',
                    'title': 'Moderate CVD Risk (PREVENT 7.5-20%)',
                    'text': (f'PREVENT 10yr CVD risk {prev_val:.1f}% — Moderate risk. '
                             'Statin therapy discussion warranted.'),
                    'severity': 'moderate', 'color': 'orange',
                })

        # Pack Years — LDCT eligibility
        py_val = _val('pack_years')
        if py_val is not None and py_val >= 20:
            alerts.append({
                'key': 'pack_years_ldct',
                'title': 'Lung Cancer Screening Eligible (≥ 20 pack-years)',
                'text': (f'{py_val:.1f} pack-years — Eligible for annual LDCT lung '
                         'cancer screening per USPSTF (age 50-80 required).'),
                'severity': 'info', 'color': 'blue',
            })
        elif py_val is not None and py_val >= 30:
            # Upgrade to moderate if ≥30 pack-years (USPSTF Grade B)
            # (≥30 already caught by the ≥20 branch above, so just upgrade)
            for a in alerts:
                if a['key'] == 'pack_years_ldct':
                    a['severity'] = 'moderate'
                    a['color'] = 'orange'
                    break

        return alerts

    def detect_score_changes(self, mrn: str, user_id: int) -> list:
        """
        Compare the two most-recent CalculatorResult rows per key.
        Returns list of dicts for clinically significant changes.

        Each dict: {'calculator_key', 'calc_name', 'old_value', 'new_value',
                    'change', 'direction': 'up'|'down', 'unit'}
        """
        from models.calculator import CalculatorResult

        # Minimum change to be considered significant
        THRESHOLDS = {
            'bmi': 2.0,
            'ldl': 30.0,
            'ldl_calculated': 30.0,
            'prevent': 5.0,
            'pack_years': 5.0,
        }
        UNITS = {
            'bmi': '', 'ldl': ' mg/dL', 'ldl_calculated': ' mg/dL',
            'prevent': '%', 'pack_years': ' pack-years',
        }
        NAMES = {
            'bmi': 'BMI', 'ldl': 'LDL-C', 'ldl_calculated': 'LDL-C (calc)',
            'prevent': 'PREVENT CVD Risk', 'pack_years': 'Pack Years',
        }

        changes = []
        for key, threshold in THRESHOLDS.items():
            try:
                rows = (CalculatorResult.query
                        .filter_by(mrn=mrn, calculator_key=key)
                        .order_by(CalculatorResult.computed_at.desc())
                        .limit(2).all())
                if len(rows) < 2:
                    continue
                new_val = rows[0].score_value
                old_val = rows[1].score_value
                if new_val is None or old_val is None:
                    continue
                delta = new_val - old_val
                if abs(delta) >= threshold:
                    changes.append({
                        'calculator_key': key,
                        'calc_name': NAMES.get(key, key),
                        'old_value': round(old_val, 1),
                        'new_value': round(new_val, 1),
                        'change': round(delta, 1),
                        'direction': 'up' if delta > 0 else 'down',
                        'unit': UNITS.get(key, ''),
                    })
            except Exception as e:
                logger.debug('detect_score_changes(%s/%s): %s', mrn, key, e)

        return changes

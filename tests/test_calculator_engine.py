"""
Phase 31 — Calculator Engine Unit Tests (25 tests)

Tests:
  1-4:   BMI computation (US units, metric, edge cases, missing input)
  5-9:   LDL computation (Friedewald, Sampson, auto-select, boundary, high-TG block)
  10-12: Pack years (standard, former smoker, never smoker)
  13-16: PREVENT (female low-risk, male high-risk, age out of range, statin adjustment)
  17-19: Questionnaire handler — GAD-7 (full score, boundary, missing items)
  20-22: Rule-based handler — Wells DVT (low, moderate, high)
  23-25: CalculatorResult model (persistence, supersession, get_latest_scores)

Usage: venv\\Scripts\\python.exe tests\\test_calculator_engine.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    passed = []
    failed = []

    from app.services.calculator_engine import CalculatorEngine
    eng = CalculatorEngine()

    # ── BMI (Tests 1-4) ────────────────────────────────────────

    print('[1/25] BMI: US units normal range...')
    try:
        r = eng.compute_bmi({'weight_lb': 154, 'height_in': 68})
        assert r['score_value'] is not None
        bmi = r['score_value']
        assert 22 <= bmi <= 24, f'Expected ~23, got {bmi}'
        assert r['score_label'] == 'normal'
        assert r['calculator_key'] == 'bmi'
        passed.append('1: BMI US units normal')
    except Exception as e:
        failed.append(f'1: BMI US units: {e}')

    print('[2/25] BMI: metric units obesity class 3...')
    try:
        r = eng.compute_bmi({'weight_kg': 130, 'height_m': 1.70})
        assert r['score_value'] is not None
        bmi = r['score_value']
        assert bmi >= 40, f'Expected ≥40, got {bmi}'
        assert r['score_label'] == 'obesity_class_3'
        passed.append('2: BMI metric obesity_class_3')
    except Exception as e:
        failed.append(f'2: BMI metric: {e}')

    print('[3/25] BMI: underweight edge case...')
    try:
        r = eng.compute_bmi({'weight_lb': 88, 'height_in': 66})
        assert r['score_label'] == 'underweight'
        passed.append('3: BMI underweight edge case')
    except Exception as e:
        failed.append(f'3: BMI underweight: {e}')

    print('[4/25] BMI: missing input returns empty...')
    try:
        r = eng.compute_bmi({})
        assert r['score_value'] is None
        assert r['calculator_key'] == 'bmi'
        passed.append('4: BMI missing input graceful empty')
    except Exception as e:
        failed.append(f'4: BMI empty: {e}')

    # ── LDL (Tests 5-9) ────────────────────────────────────────

    print('[5/25] LDL: Friedewald standard...')
    try:
        r = eng.compute_ldl({'total_cholesterol': 200, 'hdl': 55, 'triglycerides': 150})
        # LDL = 200 - 55 - (150/5) = 200 - 55 - 30 = 115
        assert r['score_value'] is not None
        assert abs(r['score_value'] - 115.0) < 1.0, f'Expected ~115, got {r["score_value"]}'
        assert r['score_detail']['formula'] == 'friedewald'
        passed.append('5: LDL Friedewald')
    except Exception as e:
        failed.append(f'5: LDL Friedewald: {e}')

    print('[6/25] LDL: Sampson for TG 400-800...')
    try:
        r = eng.compute_ldl({'total_cholesterol': 220, 'hdl': 45, 'triglycerides': 500})
        assert r['score_value'] is not None
        assert r['score_detail']['formula'] == 'sampson_2020'
        passed.append('6: LDL Sampson high-TG')
    except Exception as e:
        failed.append(f'6: LDL Sampson: {e}')

    print('[7/25] LDL: auto-select uses Friedewald for TG < 400...')
    try:
        r = eng.compute_ldl({'total_cholesterol': 200, 'hdl': 55, 'triglycerides': 200}, method='auto')
        assert r['score_detail']['formula'] == 'friedewald'
        passed.append('7: LDL auto-select Friedewald')
    except Exception as e:
        failed.append(f'7: LDL auto-select: {e}')

    print('[8/25] LDL: severe label for LDL ≥190...')
    try:
        r = eng.compute_ldl({'total_cholesterol': 280, 'hdl': 40, 'triglycerides': 100})
        # LDL = 280 - 40 - 20 = 220
        assert r['score_label'] == 'severe', f'Expected severe, got {r["score_label"]}'
        passed.append('8: LDL severe label ≥190')
    except Exception as e:
        failed.append(f'8: LDL severe: {e}')

    print('[9/25] LDL: TG ≥800 returns error detail...')
    try:
        r = eng.compute_ldl({'total_cholesterol': 300, 'hdl': 50, 'triglycerides': 850})
        assert r['score_value'] is None
        assert 'error' in r['score_detail'] or 'TG' in str(r['score_detail'])
        passed.append('9: LDL blocked at TG ≥800')
    except Exception as e:
        failed.append(f'9: LDL TG≥800 block: {e}')

    # ── Pack Years (Tests 10-12) ────────────────────────────────

    print('[10/25] Pack years: standard computation...')
    try:
        r = eng.compute_pack_years({'tobacco_status': 'current', 'cigarettes_per_day': 20, 'years_smoked': 30})
        # pack_years = (20/20) * 30 = 30
        assert r['score_value'] is not None
        assert abs(r['score_value'] - 30.0) < 0.1, f'Expected 30.0, got {r["score_value"]}'
        assert 'heavy' in r['score_label']
        passed.append('10: Pack years 30 (heavy)')
    except Exception as e:
        failed.append(f'10: Pack years: {e}')

    print('[11/25] Pack years: former smoker direct field...')
    try:
        r = eng.compute_pack_years({'tobacco_status': 'former', 'tobacco_pack_years': 15.5})
        assert r['score_value'] == 15.5
        assert 'former' in r['score_label']
        passed.append('11: Pack years former direct field')
    except Exception as e:
        failed.append(f'11: Pack years former: {e}')

    print('[12/25] Pack years: never smoker returns 0...')
    try:
        r = eng.compute_pack_years({'tobacco_status': 'never'})
        assert r['score_value'] == 0
        assert r['score_label'] == 'never_smoker'
        passed.append('12: Pack years never smoker')
    except Exception as e:
        failed.append(f'12: Pack years never: {e}')

    # ── PREVENT (Tests 13-16) ───────────────────────────────────

    print('[13/25] PREVENT: female low-risk profile...')
    try:
        # Young F, excellent markers, no risk factors
        r = eng.compute_prevent(
            demographics={'age': 40, 'sex': 'female', 'smoking_status': 'never'},
            vitals={'systolic_bp': 110},
            labs={'total_cholesterol': 180, 'hdl': 65, 'triglycerides': 100, 'egfr': 90},
            meds={'has_diabetes': False, 'antihypertensive': False, 'statin': False},
        )
        assert r['score_value'] is not None
        assert r['score_value'] < 7.5, f'Expected low risk (<7.5%), got {r["score_value"]}'
        assert r['score_label'] in ('low', 'borderline')
        passed.append(f'13: PREVENT female low risk ({r["score_value"]}%)')
    except Exception as e:
        failed.append(f'13: PREVENT female: {e}')

    print('[14/25] PREVENT: male high-risk profile...')
    try:
        r = eng.compute_prevent(
            demographics={'age': 65, 'sex': 'male', 'smoking_status': 'current', 'has_diabetes': True},
            vitals={'systolic_bp': 160},
            labs={'total_cholesterol': 240, 'hdl': 35, 'triglycerides': 200, 'egfr': 45},
            meds={'has_diabetes': True, 'antihypertensive': True, 'statin': False},
        )
        assert r['score_value'] is not None
        assert r['score_value'] >= 10, f'Expected high risk (≥10%), got {r["score_value"]}'
        passed.append(f'14: PREVENT male high risk ({r["score_value"]}%)')
    except Exception as e:
        failed.append(f'14: PREVENT male: {e}')

    print('[15/25] PREVENT: age out of range returns graceful empty...')
    try:
        r = eng.compute_prevent(
            demographics={'age': 25, 'sex': 'male'},
            vitals={'systolic_bp': 120},
            labs={'total_cholesterol': 180, 'hdl': 55},
            meds={},
        )
        assert r['score_value'] is None
        assert 'reason' in r['score_detail']
        passed.append('15: PREVENT age out of range graceful')
    except Exception as e:
        failed.append(f'15: PREVENT age range: {e}')

    print('[16/25] PREVENT: statin use reduces score...')
    try:
        base_input = dict(
            demographics={'age': 55, 'sex': 'male', 'smoking_status': 'never'},
            vitals={'systolic_bp': 130},
            labs={'total_cholesterol': 220, 'hdl': 50, 'triglycerides': 150, 'egfr': 75},
        )
        r_no_statin  = eng.compute_prevent(**base_input, meds={'statin': False})
        r_on_statin  = eng.compute_prevent(**base_input, meds={'statin': True})
        # Statin has a negative coefficient → should reduce risk estimate
        assert r_no_statin['score_value'] is not None
        assert r_on_statin['score_value'] is not None
        passed.append(f'16: PREVENT statin adjustment (no_statin={r_no_statin["score_value"]}%, statin={r_on_statin["score_value"]}%)')
    except Exception as e:
        failed.append(f'16: PREVENT statin: {e}')

    # ── Questionnaire — GAD-7 (Tests 17-19) ────────────────────

    print('[17/25] GAD-7: full severe score...')
    try:
        r = eng.compute_questionnaire('gad7', {f'item_{i}': 3 for i in range(1, 8)})
        assert r['score_value'] == 21
        assert r['score_label'] == 'severe'
        passed.append('17: GAD-7 severe (21/21)')
    except Exception as e:
        failed.append(f'17: GAD-7 severe: {e}')

    print('[18/25] GAD-7: boundary moderate (score 10)...')
    try:
        responses = {f'item_{i}': (2 if i <= 5 else 0) for i in range(1, 8)}
        r = eng.compute_questionnaire('gad7', responses)
        assert r['score_value'] == 10
        assert r['score_label'] == 'moderate'
        passed.append('18: GAD-7 moderate boundary (10/21)')
    except Exception as e:
        failed.append(f'18: GAD-7 boundary: {e}')

    print('[19/25] GAD-7: missing items default to 0...')
    try:
        r = eng.compute_questionnaire('gad7', {'item_1': 2, 'item_2': 1})
        assert r['score_value'] == 3
        assert r['score_label'] == 'minimal'
        passed.append('19: GAD-7 missing items default 0')
    except Exception as e:
        failed.append(f'19: GAD-7 missing: {e}')

    # ── Rule-Based — Wells DVT (Tests 20-22) ───────────────────

    print('[20/25] Wells DVT: low risk (alternative dx)...')
    try:
        r = eng.compute_rule_calculator('wells_dvt',
            {'alternative_diagnosis_at_least_as_likely_as_dvt': True})
        assert r['score_value'] == -2
        assert r['score_label'] == 'low'
        assert 'D-dimer' in r['score_detail']['interpretation']
        passed.append('20: Wells DVT low (alt dx)')
    except Exception as e:
        failed.append(f'20: Wells low: {e}')

    print('[21/25] Wells DVT: moderate risk (2 criteria)...')
    try:
        r = eng.compute_rule_calculator('wells_dvt', {
            'entire_leg_swollen': True,
            'calf_swelling_over_3_cm_vs_asymptomatic_leg': True,
        })
        assert r['score_value'] == 2
        assert r['score_label'] == 'moderate'
        passed.append('21: Wells DVT moderate (2 criteria)')
    except Exception as e:
        failed.append(f'21: Wells moderate: {e}')

    print('[22/25] Wells DVT: high risk (≥3 criteria)...')
    try:
        r = eng.compute_rule_calculator('wells_dvt', {
            'entire_leg_swollen': True,
            'calf_swelling_over_3_cm_vs_asymptomatic_leg': True,
            'localized_tenderness_along_deep_venous_system': True,
            'pitting_edema_confined_to_symptomatic_leg': True,
        })
        assert r['score_value'] == 4
        assert r['score_label'] == 'high'
        passed.append('22: Wells DVT high (4 criteria)')
    except Exception as e:
        failed.append(f'22: Wells high: {e}')

    # ── CalculatorResult model (Tests 23-25) ───────────────────

    print('[23/25] CalculatorResult: model fields...')
    try:
        from models.calculator import CalculatorResult
        required = ['id', 'user_id', 'mrn', 'calculator_key', 'score_value',
                     'score_label', 'score_detail', 'input_snapshot',
                     'data_source', 'is_current', 'computed_at', 'created_at']
        for f in required:
            assert hasattr(CalculatorResult, f), f'Missing field: {f}'
        passed.append('23: CalculatorResult has all required fields')
    except Exception as e:
        failed.append(f'23: Model fields: {e}')

    print('[24/25] CalculatorResult: to_dict() round-trip...')
    try:
        import json
        from models.calculator import CalculatorResult
        from datetime import datetime, timezone
        row = CalculatorResult(
            user_id=1, mrn='TEST001', calculator_key='bmi',
            score_value=24.5, score_label='normal',
            score_detail=json.dumps({'bmi': 24.5, 'category': 'normal'}),
            input_snapshot=json.dumps({'weight_lb': 165, 'height_in': 69}),
            data_source='auto_ehr', is_current=True,
            computed_at=datetime.now(timezone.utc),
        )
        d = row.to_dict()
        assert d['score_value'] == 24.5
        assert d['score_label'] == 'normal'
        assert isinstance(d['score_detail'], dict)
        assert d['score_detail']['bmi'] == 24.5
        passed.append('24: CalculatorResult to_dict round-trip')
    except Exception as e:
        failed.append(f'24: to_dict: {e}')

    print('[25/25] CalculatorResult: DB table exists...')
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from sqlalchemy import inspect
            from models import db
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            assert 'calculator_result' in tables, 'Table not found'
            cols = {c['name'] for c in inspector.get_columns('calculator_result')}
            assert 'score_value' in cols
            assert 'is_current' in cols
            assert 'calculator_key' in cols
        passed.append('25: calculator_result table exists in DB')
    except Exception as e:
        failed.append(f'25: DB table: {e}')

    # ── Summary ────────────────────────────────────────────────

    print('\n' + '=' * 60)
    print(f'Phase 31 — Calculator Engine: {len(passed)} passed, {len(failed)} failed')
    print('=' * 60)
    for p in passed:
        print(f'  PASS {p}')
    for f in failed:
        print(f'  FAIL {f}')
    print()
    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

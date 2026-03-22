"""
Phase 3.2 — End-to-End Calculator Pipeline Tests (final_plan.md Phase 3)

15 tests exercising the calculator library: BMI, LDL, PREVENT, GAD-7,
Wells DVT, AUDIT-C, score history, persist flow, and route smoke tests.

Usage:
    venv\\Scripts\\python.exe tests/test_e2e_calculator_pipeline.py
"""

import os
import sys
import json
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _get_app():
    os.environ['FLASK_ENV'] = 'testing'
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


def _get_test_user(app):
    with app.app_context():
        from models.user import User
        user = User.query.filter_by(is_active_account=True).order_by(User.id.asc()).first()
        return user.id if user else 1


def _authed_client(app, user_id):
    c = app.test_client()
    with c.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
    return c


def run_tests():
    passed = []
    failed = []

    app = _get_app()
    uid = _get_test_user(app)

    with app.app_context():
        from app.services.calculator_engine import CalculatorEngine
        engine = CalculatorEngine()
        c = _authed_client(app, uid)

        # ==================================================================
        # 1 — BMI compute US units
        # ==================================================================
        print('[1/15] BMI compute US units...')
        try:
            result = engine.compute_bmi({'weight_lb': 185, 'height_in': 65})
            assert result['calculator_key'] == 'bmi'
            assert result['score_value'] is not None
            bmi = result['score_value']
            assert 20 < bmi < 50, f'BMI out of range: {bmi}'
            assert result['score_label'] in (
                'underweight', 'normal', 'overweight',
                'obesity_class_1', 'obesity_class_2', 'obesity_class_3'
            )
            passed.append(f'1: BMI = {bmi} ({result["score_label"]})')
        except Exception as e:
            failed.append(f'1: {e}')

        # ==================================================================
        # 2 — BMI compute metric
        # ==================================================================
        print('[2/15] BMI compute metric...')
        try:
            result = engine.compute_bmi({'weight_kg': 84, 'height_m': 1.65})
            assert result['score_value'] is not None
            bmi = result['score_value']
            assert 25 < bmi < 35, f'Metric BMI unexpected: {bmi}'
            passed.append(f'2: Metric BMI = {bmi}')
        except Exception as e:
            failed.append(f'2: {e}')

        # ==================================================================
        # 3 — LDL Friedewald
        # ==================================================================
        print('[3/15] LDL Friedewald...')
        try:
            result = engine.compute_ldl({
                'total_cholesterol': 240, 'hdl': 50, 'triglycerides': 150
            })
            assert result['calculator_key'] == 'ldl_calculated'
            ldl = result['score_value']
            assert ldl is not None and 100 < ldl < 200, f'LDL unexpected: {ldl}'
            passed.append(f'3: LDL Friedewald = {ldl}')
        except Exception as e:
            failed.append(f'3: {e}')

        # ==================================================================
        # 4 — LDL Sampson 2020 (high TG)
        # ==================================================================
        print('[4/15] LDL Sampson 2020...')
        try:
            result = engine.compute_ldl({
                'total_cholesterol': 260, 'hdl': 45, 'triglycerides': 450
            }, method='sampson_2020')
            assert result['score_value'] is not None or 'error' in (result.get('score_detail') or {})
            passed.append(f'4: LDL Sampson = {result.get("score_value")}')
        except Exception as e:
            failed.append(f'4: {e}')

        # ==================================================================
        # 5 — PREVENT score
        # ==================================================================
        print('[5/15] PREVENT score...')
        try:
            result = engine.compute_prevent(
                demographics={'age': 68, 'sex': 'F', 'smoking_status': 'never', 'has_diabetes': True},
                vitals={'systolic_bp': 138},
                labs={'total_cholesterol': 220, 'hdl': 50, 'triglycerides': 150, 'egfr': 55},
                meds={'antihypertensive': True, 'statin': True, 'has_diabetes': True},
            )
            assert result['calculator_key'] == 'prevent'
            score = result.get('score_value')
            assert score is not None, 'PREVENT score is None'
            passed.append(f'5: PREVENT = {score}%')
        except Exception as e:
            failed.append(f'5: {e}')

        # ==================================================================
        # 6 — GAD-7 questionnaire
        # ==================================================================
        print('[6/15] GAD-7 questionnaire...')
        try:
            # item_1..item_7, scale 0-3 each => max 21
            responses = {f'item_{i}': 2 for i in range(1, 8)}  # total = 14 => moderate
            result = engine.compute_questionnaire('gad7', responses)
            assert result['calculator_key'] == 'gad7'
            assert result['score_value'] == 14
            assert result['score_label'] == 'moderate', f'Label: {result["score_label"]}'
            passed.append('6: GAD-7 = 14 (moderate)')
        except Exception as e:
            failed.append(f'6: {e}')

        # ==================================================================
        # 7 — Wells DVT rule-based
        # ==================================================================
        print('[7/15] Wells DVT rule-based...')
        try:
            findings = {
                'active_cancer': True,
                'entire_leg_swollen': True,
                'localized_tenderness_along_deep_venous_system': True,
            }
            result = engine.compute_rule_calculator('wells_dvt', findings)
            assert result['calculator_key'] == 'wells_dvt'
            assert result['score_value'] == 3
            assert result['score_label'] == 'high', f'Label: {result["score_label"]}'
            passed.append('7: Wells DVT = 3 (high)')
        except Exception as e:
            failed.append(f'7: {e}')

        # ==================================================================
        # 8 — AUDIT-C questionnaire
        # ==================================================================
        print('[8/15] AUDIT-C questionnaire...')
        try:
            responses = {'item_1': 2, 'item_2': 1, 'item_3': 1}  # total = 4
            result = engine.compute_questionnaire('audit_c', responses)
            assert result['calculator_key'] == 'audit_c'
            assert result['score_value'] == 4
            passed.append(f'8: AUDIT-C = {result["score_value"]} ({result["score_label"]})')
        except Exception as e:
            failed.append(f'8: {e}')

        # ==================================================================
        # 9 — Calculator index page loads
        # ==================================================================
        print('[9/15] Calculator index page...')
        try:
            r = c.get('/calculators')
            assert r.status_code == 200, f'Returned {r.status_code}'
            passed.append('9: /calculators → 200')
        except Exception as e:
            failed.append(f'9: {e}')

        # ==================================================================
        # 10 — BMI detail page loads
        # ==================================================================
        print('[10/15] BMI detail page...')
        try:
            r = c.get('/calculators/bmi')
            assert r.status_code == 200, f'Returned {r.status_code}'
            passed.append('10: /calculators/bmi → 200')
        except Exception as e:
            failed.append(f'10: {e}')

        # ==================================================================
        # 11 — BMI compute via POST route
        # ==================================================================
        print('[11/15] BMI compute via POST...')
        try:
            r = c.post('/calculators/bmi/compute',
                       data=json.dumps({
                           'weight_lb': 200, 'height_in': 70, 'mrn': 'DEMO001'
                       }),
                       content_type='application/json')
            assert r.status_code == 200, f'Compute returned {r.status_code}'
            data = r.get_json()
            assert data.get('success'), f'Compute failed: {data}'
            assert data['data']['score_value'] is not None
            passed.append(f'11: BMI POST = {data["data"]["score_value"]}')
        except Exception as e:
            failed.append(f'11: {e}')

        # ==================================================================
        # 12 — Patient risk tools page loads
        # ==================================================================
        print('[12/15] Patient risk tools...')
        try:
            r = c.get('/patient/DEMO001/risk-tools')
            assert r.status_code == 200, f'Returned {r.status_code}'
            passed.append('12: /patient/DEMO001/risk-tools → 200')
        except Exception as e:
            failed.append(f'12: {e}')

        # ==================================================================
        # 13 — Score history endpoint
        # ==================================================================
        print('[13/15] Score history...')
        try:
            r = c.get('/patient/DEMO001/score-history/bmi')
            assert r.status_code == 200, f'Returned {r.status_code}'
            data = r.get_json()
            assert data.get('success'), f'Score history failed: {data}'
            assert isinstance(data['data'], list)
            passed.append(f'13: Score history returned {len(data["data"])} entries')
        except Exception as e:
            failed.append(f'13: {e}')

        # ==================================================================
        # 14 — CalculatorResult model persistence
        # ==================================================================
        print('[14/15] CalculatorResult persist...')
        try:
            from models.calculator import CalculatorResult
            from models import db
            cr = CalculatorResult(
                user_id=uid,
                mrn='E2E_TEST',
                calculator_key='bmi',
                score_value=28.5,
                score_label='overweight',
                score_detail='{"bmi": 28.5}',
                data_source='test',
                is_current=True,
            )
            db.session.add(cr)
            db.session.commit()
            saved = CalculatorResult.query.filter_by(mrn='E2E_TEST', calculator_key='bmi').first()
            assert saved is not None, 'Record not found after save'
            assert saved.score_value == 28.5
            passed.append('14: CalculatorResult persisted OK')
        except Exception as e:
            failed.append(f'14: {e}')

        # ==================================================================
        # 15 — Empty input returns empty result
        # ==================================================================
        print('[15/15] Empty input graceful handling...')
        try:
            result = engine.compute_bmi({})
            assert result['score_value'] is None, 'Expected None for empty input'
            result2 = engine.compute_ldl({})
            assert result2['score_value'] is None, 'Expected None for empty LDL'
            passed.append('15: Empty inputs → graceful None results')
        except Exception as e:
            failed.append(f'15: {e}')

    # ---- Summary --------------------------------------------------------
    print()
    print(f'Phase 3.2 E2E Calculator Pipeline: {len(passed)} passed, {len(failed)} failed')
    for p in passed:
        print(f'  ✓ {p}')
    for f in failed:
        print(f'  ✗ {f}')
    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

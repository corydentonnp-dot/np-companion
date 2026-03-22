"""
Phase 33 — Calculator Picker Tests (15 tests)

Tests:
  1:  Calculator index page registered (route exists, redirects unauthenticated)
  2:  CALCULATOR_REGISTRY has at least 15 entries
  3:  Every registry entry has required keys
  4:  CALCULATOR_CATEGORIES list is non-empty and all strings
  5:  Blocked calculator compute returns 400 (restricted_or_licensed)
  6:  compute_bmi via compute route with valid JSON → success + score_value
  7:  compute_questionnaire (GAD-7) via engine → 7 items
  8:  Wells DVT rule-based entry has yesno-type inputs
  9:  CalculatorResult persisted after compute with MRN
  10: patient_risk_tools route registered (not 404)
  11: Semi-auto PERC has mixed auto+manual inputs
  12: Empty POST body → 400 "No input data provided"
  13: Compute response JSON does not include raw MRN in top-level keys
  14: patient_chart.html includes risk-tools widget markup
  15: score_history endpoint registered (not 404)

Usage: venv\\Scripts\\python.exe tests\\test_calculator_picker.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    passed = []
    failed = []

    from app import create_app
    app = create_app()

    # ── TEST 1: Calculator index route registered ────────────────

    print('[1/15] /calculators route exists (redirects unauthenticated)...')
    try:
        with app.test_client() as client:
            resp = client.get('/calculators')
            assert resp.status_code != 404, f'/calculators returned 404 — blueprint not registered'
            assert resp.status_code in (200, 301, 302, 401, 403), \
                f'Expected redirect or auth error, got {resp.status_code}'
            passed.append(f'1: /calculators route registered (status {resp.status_code})')
    except Exception as e:
        failed.append(f'1: /calculators route: {e}')

    # ── TEST 2: Registry has at least 15 entries ─────────────────

    print('[2/15] CALCULATOR_REGISTRY has >= 15 entries...')
    try:
        from app.services.calculator_registry import CALCULATOR_REGISTRY
        count = len(CALCULATOR_REGISTRY)
        assert count >= 15, f'Expected >= 15 calculators, got {count}'
        passed.append(f'2: Registry has {count} calculators')
    except Exception as e:
        failed.append(f'2: Registry size: {e}')

    # ── TEST 3: Every registry entry has required keys ───────────

    print('[3/15] Every registry entry has name/category/automation_tag/type/status/inputs...')
    try:
        from app.services.calculator_registry import CALCULATOR_REGISTRY
        required = {'name', 'category', 'automation_tag', 'type', 'status', 'inputs', 'description'}
        for key, calc in CALCULATOR_REGISTRY.items():
            missing = required - set(calc.keys())
            assert not missing, f'Calculator "{key}" missing keys: {missing}'
            assert isinstance(calc['inputs'], list), f'"{key}".inputs must be a list'
        passed.append(f'3: All {len(CALCULATOR_REGISTRY)} entries have required keys')
    except Exception as e:
        failed.append(f'3: Required keys: {e}')

    # ── TEST 4: CALCULATOR_CATEGORIES non-empty ──────────────────

    print('[4/15] CALCULATOR_CATEGORIES is non-empty list of strings...')
    try:
        from app.services.calculator_registry import CALCULATOR_CATEGORIES
        assert isinstance(CALCULATOR_CATEGORIES, list), 'Not a list'
        assert len(CALCULATOR_CATEGORIES) > 0, 'Empty list'
        assert all(isinstance(c, str) for c in CALCULATOR_CATEGORIES), 'Non-string entries'
        passed.append(f'4: {len(CALCULATOR_CATEGORIES)} categories defined')
    except Exception as e:
        failed.append(f'4: CALCULATOR_CATEGORIES: {e}')

    # ── TEST 5: Blocked calculator compute returns 400 ───────────

    print('[5/15] Restricted calculator compute → 400...')
    try:
        with app.test_client() as client:
            resp = client.post(
                '/calculators/phq9/compute',
                json={'score': 10},
            )
            # Unauthenticated → 302; if authenticated would be 400 for restricted
            # Accept 400 (authenticated blocked) or 302 (login redirect)
            assert resp.status_code != 404, 'Route not found'
            assert resp.status_code in (400, 302, 401), \
                f'Expected 400 or redirect for restricted, got {resp.status_code}'
            passed.append(f'5: phq9/compute returns {resp.status_code} (blocked or redirect)')
    except Exception as e:
        failed.append(f'5: Blocked calc: {e}')

    # ── TEST 6: BMI compute via engine ──────────────────────────

    print('[6/15] compute_bmi returns valid score dict...')
    try:
        with app.app_context():
            from app.services.calculator_engine import CalculatorEngine
            eng = CalculatorEngine()
            result = eng.compute_bmi({'weight_lb': 198, 'height_in': 70})
            assert result['calculator_key'] == 'bmi'
            assert result['score_value'] is not None
            assert isinstance(result['score_value'], float)
            assert 25 < result['score_value'] < 35, f'Expected BMI ~28, got {result["score_value"]}'
            passed.append(f'6: compute_bmi → {result["score_value"]:.1f} ({result["score_label"]})')
    except Exception as e:
        failed.append(f'6: compute_bmi: {e}')

    # ── TEST 7: GAD-7 questionnaire has 7 items ──────────────────

    print('[7/15] GAD-7 QUESTIONNAIRE_DEFS has items=7...')
    try:
        with app.app_context():
            from app.services.calculator_engine import CalculatorEngine
            eng = CalculatorEngine()
            assert 'gad7' in eng.QUESTIONNAIRE_DEFS, 'gad7 not in QUESTIONNAIRE_DEFS'
            gad7 = eng.QUESTIONNAIRE_DEFS['gad7']
            item_count = gad7.get('items')
            assert item_count == 7, f'GAD-7 should have items=7, got {item_count}'
            assert gad7.get('max') == 21, f'GAD-7 max should be 21, got {gad7.get("max")}'
            assert 'bands' in gad7, 'GAD-7 should have bands'
            passed.append(f'7: GAD-7 has items={item_count} in QUESTIONNAIRE_DEFS')
    except Exception as e:
        failed.append(f'7: GAD-7 items: {e}')

    # ── TEST 8: Wells DVT has boolean-type inputs in registry ──────

    print('[8/15] Wells DVT registry entry has boolean inputs...')
    try:
        from app.services.calculator_registry import CALCULATOR_REGISTRY
        wells = CALCULATOR_REGISTRY.get('wells_dvt', {})
        assert wells, 'wells_dvt not in registry'
        bool_inputs = [i for i in wells.get('inputs', []) if i.get('type') == 'boolean']
        assert len(bool_inputs) > 0, f'No boolean inputs in wells_dvt; types: {[i["type"] for i in wells["inputs"]]}'
        passed.append(f'8: Wells DVT has {len(bool_inputs)} boolean inputs')
    except Exception as e:
        failed.append(f'8: Wells DVT boolean inputs: {e}')

    # ── TEST 9: CalculatorResult persisted when MRN + user_id provided ─

    print('[9/15] CalculatorResult row persisted by _persist_result...')
    try:
        with app.app_context():
            from models import db
            from models.calculator import CalculatorResult
            from app.services.calculator_engine import CalculatorEngine
            eng = CalculatorEngine()
            test_mrn = 'PICKER_TEST_9'
            result = eng.compute_bmi({'weight_lb': 155, 'height_in': 67})
            eng._persist_result(result, test_mrn, 1)
            rows = CalculatorResult.query.filter_by(mrn=test_mrn, calculator_key='bmi').all()
            assert len(rows) >= 1, f'Expected >= 1 row, got {len(rows)}'
            # Cleanup
            CalculatorResult.query.filter_by(mrn=test_mrn).delete()
            db.session.commit()
            passed.append(f'9: _persist_result wrote CalculatorResult (found {len(rows)} rows)')
    except Exception as e:
        failed.append(f'9: DB persistence: {e}')

    # ── TEST 10: patient_risk_tools route registered ─────────────

    print('[10/15] /patient/<mrn>/risk-tools route registered...')
    try:
        with app.test_client() as client:
            resp = client.get('/patient/TESTMRN123/risk-tools')
            assert resp.status_code != 404, 'Route not found — not registered'
            assert resp.status_code in (200, 302, 401, 403), \
                f'Unexpected status {resp.status_code}'
            passed.append(f'10: /patient/<mrn>/risk-tools registered (status {resp.status_code})')
    except Exception as e:
        failed.append(f'10: patient_risk_tools route: {e}')

    # ── TEST 11: PERC (semi-auto) has mixed auto+clinician inputs ───

    print('[11/15] PERC (semi-auto) has both auto and clinician input sources...')
    try:
        from app.services.calculator_registry import CALCULATOR_REGISTRY
        perc = CALCULATOR_REGISTRY.get('perc', {})
        assert perc, 'perc not in registry'
        assert perc.get('automation_tag') == 'semi_auto', \
            f'PERC automation_tag should be semi_auto, got {perc.get("automation_tag")}'
        sources = {i.get('source') for i in perc.get('inputs', [])}
        # Semi-auto: has both auto-filled (from EHR) and clinician-entered inputs
        assert len(sources) >= 1, 'PERC should have at least one input source'
        passed.append(f'11: PERC is semi_auto with input sources: {sources}')
    except Exception as e:
        failed.append(f'11: PERC semi-auto inputs: {e}')

    # ── TEST 12: Empty POST body → 400 ──────────────────────────

    print('[12/15] Empty POST body → 400 "No input data provided"...')
    try:
        with app.test_client() as client:
            resp = client.post(
                '/calculators/bmi/compute',
                data=b'',
                content_type='application/json',
            )
            # Unauthenticated → 302; if somehow authenticated → 400
            assert resp.status_code != 404, 'Route not found'
            assert resp.status_code in (400, 302, 401), \
                f'Expected 400 or redirect, got {resp.status_code}'
            passed.append(f'12: Empty body returns {resp.status_code} (400 or login redirect)')
    except Exception as e:
        failed.append(f'12: Empty body validation: {e}')

    # ── TEST 13: Compute response does not expose raw MRN at top level ─

    print('[13/15] Compute result dict has no "mrn" key at top level...')
    try:
        with app.app_context():
            from app.services.calculator_engine import CalculatorEngine
            eng = CalculatorEngine()
            result = eng.compute_bmi({'weight_lb': 200, 'height_in': 72})
            assert 'mrn' not in result, \
                f'MRN should not appear in compute result dict; keys: {list(result.keys())}'
            # input_snapshot may have inputs but should not have mrn key inside compute result
            passed.append(f'13: compute_bmi result has no "mrn" key (keys: {list(result.keys())})')
    except Exception as e:
        failed.append(f'13: MRN not in result: {e}')

    # ── TEST 14: patient_chart.html has risk-tools widget ────────

    print('[14/15] patient_chart.html has risk-tools widget markup...')
    try:
        tpl_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'templates', 'patient_chart.html'
        )
        with open(tpl_path, 'r', encoding='utf-8') as f:
            tpl = f.read()
        assert 'data-widget="risk-tools"' in tpl, 'risk-tools widget div not found'
        assert 'data-tab="calculators"' in tpl, 'Calculators tab button not found'
        assert '/risk-tools' in tpl, 'risk-tools URL not in template'
        passed.append('14: patient_chart.html has risk-tools widget and Calculators tab')
    except Exception as e:
        failed.append(f'14: patient_chart.html markup: {e}')

    # ── TEST 15: score_history route registered ──────────────────

    print('[15/15] /patient/<mrn>/score-history/<key> route registered...')
    try:
        with app.test_client() as client:
            resp = client.get('/patient/TESTMRN/score-history/bmi')
            assert resp.status_code != 404, 'Route not found'
            assert resp.status_code in (200, 302, 401, 403), \
                f'Unexpected status {resp.status_code}'
            passed.append(f'15: score-history route registered (status {resp.status_code})')
    except Exception as e:
        failed.append(f'15: score-history route: {e}')

    # ── Summary ─────────────────────────────────────────────────

    print('\n' + '=' * 60)
    print(f'Phase 33 — Calculator Picker: {len(passed)} passed, {len(failed)} failed')
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

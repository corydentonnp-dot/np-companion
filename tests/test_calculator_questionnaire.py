"""
Phase 36.6 — Questionnaire Calculator Form Tests (12 tests)

Tests:
  1:  GAD-7 correct item count in registry (7 items)
  2:  GAD-7 score computation — sum of 7 likert4 items (total=13 → moderate)
  3:  C-SSRS registry has branching metadata on Q3-Q5
  4:  C-SSRS engine returns high_risk when Q5=YES
  5:  C-SSRS engine returns low_risk when all NO
  6:  AUDIT-C female ≥3 → positive_female
  7:  AUDIT-C male score=3 → negative (cutoff is 4 for men)
  8:  AUDIT-C extracts score from option text like 'Never (0)'
  9:  Wells DVT alternative-diagnosis item has -2 points
  10: Ottawa Ankle any positive → xray_indicated
  11: Restricted (PHQ-9) returns 'restricted_or_licensed' status
  12: CRAFFT 6 items, score 0 → low_risk

Usage: venv\\Scripts\\python.exe tests\\test_calculator_questionnaire.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    passed = []
    failed = []

    # ─────────────────────────────────────────────────────────────────────────
    # Tests 1-2: GAD-7 questionnaire
    # ─────────────────────────────────────────────────────────────────────────

    print('[1/12] GAD-7 registry has 7 inputs...')
    try:
        from app.services.calculator_registry import CALCULATOR_REGISTRY
        gad7 = CALCULATOR_REGISTRY.get('gad7')
        assert gad7 is not None, 'gad7 not in registry'
        assert len(gad7['inputs']) == 7, f'Expected 7 inputs, got {len(gad7["inputs"])}'
        assert all(inp['type'] == 'likert4' for inp in gad7['inputs']), 'All GAD-7 items should be likert4'
        passed.append('1: GAD-7 registry has 7 likert4 items')
    except Exception as e:
        failed.append(f'1: GAD-7 registry: {e}')

    print('[2/12] GAD-7 score computation: sum → total 13 = moderate...')
    try:
        from app.services.calculator_engine import CalculatorEngine
        eng = CalculatorEngine()
        # 3+3+2+2+1+1+1 = 13 → moderate
        responses = {f'item_{i}': v for i, v in enumerate([3, 3, 2, 2, 1, 1, 1], start=1)}
        result = eng.compute_questionnaire('gad7', responses)
        assert result['score_value'] == 13.0, f'Expected 13, got {result["score_value"]}'
        assert result['score_label'] == 'moderate', f'Expected moderate, got {result["score_label"]}'
        passed.append('2: GAD-7 score 13 → moderate')
    except Exception as e:
        failed.append(f'2: GAD-7 computation: {e}')

    # ─────────────────────────────────────────────────────────────────────────
    # Tests 3-5: C-SSRS
    # ─────────────────────────────────────────────────────────────────────────

    print('[3/12] C-SSRS registry has branch_show metadata on Q3-Q5...')
    try:
        from app.services.calculator_registry import CALCULATOR_REGISTRY
        cssrs = CALCULATOR_REGISTRY.get('cssrs')
        assert cssrs is not None, 'cssrs not in registry'
        branched_keys = [
            inp['key'] for inp in cssrs['inputs']
            if inp.get('branch_show') == 'q2'
        ]
        assert set(branched_keys) == {'q3', 'q4', 'q5'}, \
            f'Expected q3,q4,q5 to branch on q2; got {branched_keys}'
        passed.append('3: C-SSRS Q3-Q5 have branch_show=q2')
    except Exception as e:
        failed.append(f'3: C-SSRS branch metadata: {e}')

    print('[4/12] C-SSRS engine → high_risk when Q5=YES...')
    try:
        from app.services.calculator_engine import CalculatorEngine
        eng = CalculatorEngine()
        result = eng.compute_cssrs({'q1': '0', 'q2': '1', 'q3': '0', 'q4': '0', 'q5': '1', 'q6': '0'})
        assert result['score_label'] == 'high_risk', \
            f'Expected high_risk, got {result["score_label"]}'
        assert result['score_detail']['high_risk_criteria'] is True
        passed.append('4: C-SSRS Q5=YES → high_risk')
    except Exception as e:
        failed.append(f'4: C-SSRS high_risk: {e}')

    print('[5/12] C-SSRS engine → low_risk when all NO...')
    try:
        from app.services.calculator_engine import CalculatorEngine
        eng = CalculatorEngine()
        result = eng.compute_cssrs({'q1': '0', 'q2': '0', 'q3': '0', 'q4': '0', 'q5': '0', 'q6': '0'})
        assert result['score_label'] == 'low_risk', \
            f'Expected low_risk, got {result["score_label"]}'
        assert result['score_value'] == 0.0
        passed.append('5: C-SSRS all NO → low_risk')
    except Exception as e:
        failed.append(f'5: C-SSRS low_risk: {e}')

    # ─────────────────────────────────────────────────────────────────────────
    # Tests 6-8: AUDIT-C gender-aware scoring
    # ─────────────────────────────────────────────────────────────────────────

    print('[6/12] AUDIT-C female score=3 → positive_female...')
    try:
        from app.services.calculator_engine import CalculatorEngine
        eng = CalculatorEngine()
        # 1+1+1 = 3 (each item gives score 1); female cutoff is 3 → positive
        result = eng.compute_audit_c({'item_1': 1, 'item_2': 1, 'item_3': 1}, sex='female')
        assert result['score_value'] == 3.0, f'Expected score 3, got {result["score_value"]}'
        assert result['score_label'] == 'positive_female', \
            f'Expected positive_female, got {result["score_label"]}'
        passed.append('6: AUDIT-C female score=3 → positive_female')
    except Exception as e:
        failed.append(f'6: AUDIT-C female positive: {e}')

    print('[7/12] AUDIT-C male score=3 → negative (cutoff ≥4 for men)...')
    try:
        from app.services.calculator_engine import CalculatorEngine
        eng = CalculatorEngine()
        result = eng.compute_audit_c({'item_1': 1, 'item_2': 1, 'item_3': 1}, sex='male')
        assert result['score_value'] == 3.0
        assert result['score_label'] == 'negative', \
            f'Expected negative for male score=3, got {result["score_label"]}'
        passed.append('7: AUDIT-C male score=3 → negative')
    except Exception as e:
        failed.append(f'7: AUDIT-C male negative: {e}')

    print('[8/12] AUDIT-C parses option text to extract score...')
    try:
        from app.services.calculator_engine import CalculatorEngine
        eng = CalculatorEngine()
        # Option strings like 'Never (0)', '2-3 times/week (3)'
        result = eng.compute_audit_c({
            'item_1': 'Monthly or less (1)',
            'item_2': '3-4 (1)',
            'item_3': 'Monthly (2)',
        }, sex='female')
        assert result['score_value'] == 4.0, \
            f'Expected 1+1+2=4 from option text, got {result["score_value"]}'
        assert result['score_label'] == 'positive_female'
        passed.append('8: AUDIT-C extracts score from option text')
    except Exception as e:
        failed.append(f'8: AUDIT-C option text parsing: {e}')

    # ─────────────────────────────────────────────────────────────────────────
    # Tests 9-10: Rule-based calculators
    # ─────────────────────────────────────────────────────────────────────────

    print('[9/12] Wells DVT alternative-diagnosis item has -2 points in registry...')
    try:
        from app.services.calculator_registry import CALCULATOR_REGISTRY
        wells = CALCULATOR_REGISTRY.get('wells_dvt')
        assert wells is not None, 'wells_dvt not in registry'
        alt_item = next(
            (inp for inp in wells['inputs'] if 'alternative' in inp['key'].lower()),
            None
        )
        assert alt_item is not None, 'Alternative diagnosis item not found'
        assert alt_item.get('points') == -2, \
            f'Expected -2 points, got {alt_item.get("points")}'
        passed.append('9: Wells DVT alternative-diagnosis item has -2 points')
    except Exception as e:
        failed.append(f'9: Wells DVT -2 points: {e}')

    print('[10/12] Ottawa Ankle any positive → xray_indicated...')
    try:
        from app.services.calculator_engine import CalculatorEngine
        eng = CalculatorEngine()
        # Only lateral malleolus tenderness positive → should indicate xray
        result = eng.compute_rule_calculator('ottawa_ankle', {
            'bone_tenderness_lateral_malleolus': True,
            'bone_tenderness_medial_malleolus': False,
            'unable_to_weight_bear_4_steps': False,
        })
        assert result['score_label'] == 'xray_indicated', \
            f'Expected xray_indicated, got {result["score_label"]}'
        passed.append('10: Ottawa Ankle positive → xray_indicated')
    except Exception as e:
        failed.append(f'10: Ottawa Ankle: {e}')

    # ─────────────────────────────────────────────────────────────────────────
    # Tests 11-12: Registry status + CRAFFT
    # ─────────────────────────────────────────────────────────────────────────

    print('[11/12] PHQ-9 registry status = restricted_or_licensed...')
    try:
        from app.services.calculator_registry import CALCULATOR_REGISTRY
        phq9 = CALCULATOR_REGISTRY.get('phq9')
        assert phq9 is not None, 'phq9 not in registry'
        assert phq9['status'] == 'restricted_or_licensed', \
            f'Expected restricted_or_licensed, got {phq9["status"]}'
        assert 'license_note' in phq9, 'PHQ-9 should have license_note'
        passed.append('11: PHQ-9 status=restricted_or_licensed with license_note')
    except Exception as e:
        failed.append(f'11: PHQ-9 restricted status: {e}')

    print('[12/12] CRAFFT 6 items, score=0 → low_risk...')
    try:
        from app.services.calculator_engine import CalculatorEngine
        from app.services.calculator_registry import CALCULATOR_REGISTRY
        eng = CalculatorEngine()
        crafft = CALCULATOR_REGISTRY.get('crafft')
        assert crafft is not None, 'crafft not in registry'
        assert len(crafft['inputs']) == 6, f'Expected 6 items, got {len(crafft["inputs"])}'
        # All NO (value=0)
        responses = {inp['key']: 0 for inp in crafft['inputs']}
        result = eng.compute_questionnaire('crafft', responses)
        assert result['score_value'] == 0.0, f'Expected 0, got {result["score_value"]}'
        assert result['score_label'] == 'low_risk', \
            f'Expected low_risk, got {result["score_label"]}'
        passed.append('12: CRAFFT 6 items, all-NO → low_risk')
    except Exception as e:
        failed.append(f'12: CRAFFT low_risk: {e}')

    # ─────────────────────────────────────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────────────────────────────────────
    print()
    print(f'Results: {len(passed)}/12 passed, {len(failed)}/12 failed')
    if passed:
        for p in passed:
            print(f'  PASS: {p}')
    if failed:
        print()
        for f in failed:
            print(f'  FAIL: {f}')
    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

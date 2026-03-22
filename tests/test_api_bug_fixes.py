"""
Regression tests for Phase 6 — API Critical Bug Fixes:
  - 6.1 openfda_labels.py: syntax fixes, check_pregnancy_risk, check_renal_dosing
  - 6.2 umls.py: resolve_abbreviation return statement
  - 6.3 healthfinder.py: _extract_grade regex + default grade

Uses unittest.mock to isolate logic from live API calls.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock


def run_tests():
    passed = []
    failed = []

    # ==================================================================
    # 6.1 — OpenFDA Labels: import + check_pregnancy_risk + check_renal_dosing
    # ==================================================================

    # ---- Test 1: Module imports without SyntaxError ----
    print('[1/10] openfda_labels imports cleanly...')
    try:
        from app.services.api.openfda_labels import OpenFDALabelsService
        assert OpenFDALabelsService is not None
        passed.append('openfda import')
        print('  PASS')
    except Exception as e:
        failed.append(f'openfda import: {e}')
        print(f'  FAIL  {e}')

    # ---- Test 2: check_pregnancy_risk returns dict with 'category' key ----
    print('[2/10] check_pregnancy_risk returns category...')
    try:
        from app.services.api.openfda_labels import OpenFDALabelsService

        mock_label = {
            "label_sections": {
                "pregnancy": "Pregnancy Category X. This drug is contraindicated in pregnancy."
            }
        }
        with patch.object(OpenFDALabelsService, '__init__', lambda self, db: None):
            svc = OpenFDALabelsService.__new__(OpenFDALabelsService)
            with patch.object(svc, 'get_label_by_rxcui', return_value=mock_label):
                result = svc.check_pregnancy_risk('12345')
                assert 'category' in result, f'Missing category key: {result}'
                assert result['category'] == 'X', f'Expected X, got {result["category"]}'
                assert result['has_pregnancy_warning'] is True
                passed.append('pregnancy risk category')
                print('  PASS')
    except Exception as e:
        failed.append(f'pregnancy risk category: {e}')
        print(f'  FAIL  {e}')

    # ---- Test 3: check_pregnancy_risk handles no pregnancy text ----
    print('[3/10] check_pregnancy_risk handles empty...')
    try:
        from app.services.api.openfda_labels import OpenFDALabelsService

        mock_label = {"label_sections": {}}
        with patch.object(OpenFDALabelsService, '__init__', lambda self, db: None):
            svc = OpenFDALabelsService.__new__(OpenFDALabelsService)
            with patch.object(svc, 'get_label_by_rxcui', return_value=mock_label):
                result = svc.check_pregnancy_risk('99999')
                assert result['category'] == 'N/A', f'Expected N/A, got {result["category"]}'
                assert result['has_pregnancy_warning'] is False
                passed.append('pregnancy risk empty')
                print('  PASS')
    except Exception as e:
        failed.append(f'pregnancy risk empty: {e}')
        print(f'  FAIL  {e}')

    # ---- Test 4: check_renal_dosing returns dict with 'adjustment' key ----
    print('[4/10] check_renal_dosing returns adjustment...')
    try:
        from app.services.api.openfda_labels import OpenFDALabelsService

        mock_label = {
            "label_sections": {
                "renal_impairment": "Dose reduction required for CrCl < 30 mL/min. Reduce dose by 50%."
            }
        }
        with patch.object(OpenFDALabelsService, '__init__', lambda self, db: None):
            svc = OpenFDALabelsService.__new__(OpenFDALabelsService)
            with patch.object(svc, 'get_label_by_rxcui', return_value=mock_label):
                result = svc.check_renal_dosing('12345', gfr=25)
                assert 'adjustment' in result, f'Missing adjustment key: {result}'
                assert result['adjustment'] == 'dose_reduction', f'Expected dose_reduction, got {result["adjustment"]}'
                assert result['has_renal_guidance'] is True
                passed.append('renal dosing adjustment')
                print('  PASS')
    except Exception as e:
        failed.append(f'renal dosing adjustment: {e}')
        print(f'  FAIL  {e}')

    # ==================================================================
    # 6.2 — UMLS: resolve_abbreviation returns dict (not None)
    # ==================================================================

    # ---- Test 5: resolve_abbreviation returns dict with term + icd10_code ----
    print('[5/10] resolve_abbreviation returns dict...')
    try:
        from app.services.api.umls import UMLSService

        mock_concepts = [{"cui": "C0020538", "name": "Hypertension", "semantic_type": "Disease"}]
        mock_icd10 = [{"code": "I10", "description": "Essential hypertension", "vocabulary": "ICD10CM"}]

        with patch.object(UMLSService, '__init__', lambda self, db, api_key=None: None):
            svc = UMLSService.__new__(UMLSService)
            svc._api_key = 'test_key'
            with patch.object(svc, 'search', return_value=mock_concepts):
                with patch.object(svc, 'get_icd10_for_concept', return_value=mock_icd10):
                    result = svc.resolve_abbreviation("HTN")
                    assert result is not None, 'resolve_abbreviation returned None'
                    assert result.get('term') == 'Hypertension', f'term: {result.get("term")}'
                    assert result.get('icd10_code') == 'I10', f'icd10_code: {result.get("icd10_code")}'
                    passed.append('resolve_abbreviation returns dict')
                    print('  PASS')
    except Exception as e:
        failed.append(f'resolve_abbreviation returns dict: {e}')
        print(f'  FAIL  {e}')

    # ---- Test 6: resolve_abbreviation handles no match ----
    print('[6/10] resolve_abbreviation no match...')
    try:
        from app.services.api.umls import UMLSService

        with patch.object(UMLSService, '__init__', lambda self, db, api_key=None: None):
            svc = UMLSService.__new__(UMLSService)
            svc._api_key = 'test_key'
            with patch.object(svc, 'search', return_value=[]):
                result = svc.resolve_abbreviation("XXXNOTREAL")
                assert result is not None, 'resolve_abbreviation returned None'
                assert result == {"term": None, "icd10_code": None}
                passed.append('resolve_abbreviation no match')
                print('  PASS')
    except Exception as e:
        failed.append(f'resolve_abbreviation no match: {e}')
        print(f'  FAIL  {e}')

    # ==================================================================
    # 6.3 — HealthFinder: _extract_grade regex + defaults
    # ==================================================================

    # ---- Test 7: _extract_grade matches "USPSTF Grade A recommendation" ----
    print('[7/10] _extract_grade USPSTF Grade A...')
    try:
        from app.services.api.healthfinder import _extract_grade
        result = _extract_grade("USPSTF Grade A recommendation for screening")
        assert result == "A", f'Expected A, got {result}'
        passed.append('grade USPSTF A')
        print('  PASS')
    except Exception as e:
        failed.append(f'grade USPSTF A: {e}')
        print(f'  FAIL  {e}')

    # ---- Test 8: _extract_grade matches "[Grade B]" ----
    print('[8/10] _extract_grade [Grade B]...')
    try:
        from app.services.api.healthfinder import _extract_grade
        result = _extract_grade("This has [Grade B] in brackets")
        assert result == "B", f'Expected B, got {result}'
        passed.append('grade bracket B')
        print('  PASS')
    except Exception as e:
        failed.append(f'grade bracket B: {e}')
        print(f'  FAIL  {e}')

    # ---- Test 9: _extract_grade matches "I" (insufficient evidence) ----
    print('[9/10] _extract_grade insufficient evidence...')
    try:
        from app.services.api.healthfinder import _extract_grade
        result = _extract_grade("Grade I — insufficient evidence to recommend")
        assert result == "I", f'Expected I, got {result}'
        passed.append('grade I insufficient')
        print('  PASS')
    except Exception as e:
        failed.append(f'grade I insufficient: {e}')
        print(f'  FAIL  {e}')

    # ---- Test 10: _extract_grade defaults to "I" for unrecognized text ----
    print('[10/10] _extract_grade default...')
    try:
        from app.services.api.healthfinder import _extract_grade
        result = _extract_grade("No grade information found in this text at all")
        assert result == "I", f'Expected I default, got {result}'
        # Also test empty string
        result2 = _extract_grade("")
        assert result2 == "I", f'Expected I for empty, got {result2}'
        passed.append('grade default I')
        print('  PASS')
    except Exception as e:
        failed.append(f'grade default I: {e}')
        print(f'  FAIL  {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print(f'\n=== API Bug Fix Tests: {len(passed)} passed, {len(failed)} failed ===')
    if failed:
        for f in failed:
            print(f'  FAIL: {f}')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(run_tests())

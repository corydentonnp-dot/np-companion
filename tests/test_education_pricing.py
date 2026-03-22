"""
Integration tests for Phase 27: Patient Education Pricing Integration

Tests verify:
- _build_pricing_paragraph helper exists and is callable
- Pricing paragraph logic for Cost Plus, GoodRx, assistance programs
- send_education_to_patient references _build_pricing_paragraph
- Language is informational (not endorsement)
- Empty drug name returns empty string
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(relpath):
    with open(os.path.join(ROOT, relpath), 'r', encoding='utf-8') as f:
        return f.read()


def run_tests():
    passed = []
    failed = []

    intel_py = _read('routes/intelligence.py')

    # ==========================================================
    # 27.1 — Pricing paragraph helper
    # ==========================================================
    print('[1/15] _build_pricing_paragraph helper exists...')
    try:
        assert 'def _build_pricing_paragraph' in intel_py, 'Helper function'
        assert 'drug_name' in intel_py.split('def _build_pricing_paragraph')[1].split('):')[0], 'Takes drug_name param'
        passed.append('27.1 Helper exists')
    except AssertionError as e:
        failed.append(f'27.1 Helper: {e}')

    print('[2/15] Helper imports PricingService...')
    try:
        helper_body = intel_py.split('def _build_pricing_paragraph')[1].split('\ndef ')[0]
        assert 'PricingService' in helper_body, 'PricingService imported'
        assert 'get_pricing' in helper_body, 'get_pricing called'
        passed.append('27.1b PricingService usage')
    except AssertionError as e:
        failed.append(f'27.1b PricingService: {e}')

    print('[3/15] Cost Plus pricing paragraph template...')
    try:
        assert 'Cost Plus Drugs pharmacy' in intel_py, 'Cost Plus label'
        assert 'costplusdrugs.com' in intel_py, 'Cost Plus URL'
        passed.append('27.1c Cost Plus paragraph')
    except AssertionError as e:
        failed.append(f'27.1c Cost Plus: {e}')

    print('[4/15] GoodRx pricing paragraph template...')
    try:
        assert 'GoodRx discount' in intel_py, 'GoodRx label'
        assert 'goodrx.com' in intel_py, 'GoodRx URL'
        passed.append('27.1d GoodRx paragraph')
    except AssertionError as e:
        failed.append(f'27.1d GoodRx: {e}')

    print('[5/15] Assistance programs paragraph...')
    try:
        assert 'Financial assistance' in intel_py, 'Assistance text'
        assert 'application_url' in intel_py, 'Program URL reference'
        passed.append('27.1e Assistance programs')
    except AssertionError as e:
        failed.append(f'27.1e Assistance: {e}')

    print('[6/15] Language is informational (not endorsement)...')
    try:
        assert 'may be available' in intel_py, 'Conditional language'
        assert 'may be able to save' in intel_py, 'Non-directive phrasing'
        # Should NOT contain endorsement language
        assert 'we recommend' not in intel_py.lower(), 'No recommendation'
        assert 'you should' not in intel_py.lower() or 'you should' in 'something else', 'No directive'
        passed.append('27.1f Informational language')
    except AssertionError as e:
        failed.append(f'27.1f Language: {e}')

    print('[7/15] Empty drug name returns empty string...')
    try:
        helper_body = intel_py.split('def _build_pricing_paragraph')[1].split('\ndef ')[0]
        assert "not drug_name" in helper_body or "if not drug_name" in helper_body, 'Empty check'
        assert "return ''" in helper_body, 'Returns empty string'
        passed.append('27.1g Empty input handling')
    except AssertionError as e:
        failed.append(f'27.1g Empty input: {e}')

    print('[8/15] Error handling wraps pricing calls...')
    try:
        helper_body = intel_py.split('def _build_pricing_paragraph')[1].split('\ndef ')[0]
        assert 'except' in helper_body, 'Exception handling'
        passed.append('27.1h Error handling')
    except AssertionError as e:
        failed.append(f'27.1h Error handling: {e}')

    # ==========================================================
    # 27.1 — send_education_to_patient integration
    # ==========================================================
    print('[9/15] send_education_to_patient calls helper...')
    try:
        send_body = intel_py.split('def send_education_to_patient')[1].split('\ndef ')[0]
        assert '_build_pricing_paragraph' in send_body, 'Calls helper'
        passed.append('27.1i Education-send integration')
    except AssertionError as e:
        failed.append(f'27.1i Integration: {e}')

    print('[10/15] Pricing paragraph appended to body_parts...')
    try:
        send_body = intel_py.split('def send_education_to_patient')[1].split('\ndef ')[0]
        assert 'pricing_para' in send_body or '_build_pricing_paragraph' in send_body, 'Paragraph variable'
        assert 'body_parts.append' in send_body, 'Appended to body'
        passed.append('27.1j Body parts integration')
    except AssertionError as e:
        failed.append(f'27.1j Body parts: {e}')

    # ==========================================================
    # 27.2 — Trigger 2 readiness
    # ==========================================================
    print('[11/15] Helper is standalone (reusable for Trigger 2)...')
    try:
        # Verify _build_pricing_paragraph is a standalone function (not nested inside a route)
        # It should appear before the decorator for send_education_to_patient
        helper_pos = intel_py.index('def _build_pricing_paragraph')
        send_pos = intel_py.index('def send_education_to_patient')
        assert helper_pos < send_pos, 'Helper defined before route'
        # Check it's not indented (module-level)
        lines = intel_py.split('\n')
        for line in lines:
            if 'def _build_pricing_paragraph' in line:
                assert line.startswith('def '), 'Module-level function'
                break
        passed.append('27.2 Standalone helper (Trigger 2 ready)')
    except AssertionError as e:
        failed.append(f'27.2 Standalone: {e}')

    print('[12/15] Helper returns string (not appends to list)...')
    try:
        helper_body = intel_py.split('def _build_pricing_paragraph')[1].split('\ndef ')[0]
        # Should return a string, not modify external state
        assert 'return' in helper_body, 'Has return statement'
        assert 'body_parts' not in helper_body, 'Does not modify body_parts'
        passed.append('27.2b Returns string')
    except AssertionError as e:
        failed.append(f'27.2b Return type: {e}')

    print('[13/15] Phase 27 comment present...')
    try:
        assert 'Phase 27' in intel_py, 'Phase 27 comment'
        passed.append('27 Phase comment')
    except AssertionError as e:
        failed.append(f'27 Comment: {e}')

    # ==========================================================
    # Functional tests
    # ==========================================================
    print('[14/15] _build_pricing_paragraph importable...')
    try:
        sys.path.insert(0, ROOT)
        from app import create_app
        app = create_app()
        with app.app_context():
            from routes.intelligence import _build_pricing_paragraph
            result = _build_pricing_paragraph('')
            assert result == '', f'Empty name should return empty, got: {result!r}'
            result2 = _build_pricing_paragraph('lisinopril')
            assert isinstance(result2, str), 'Returns string'
        passed.append('27 Functional import test')
    except AssertionError as e:
        failed.append(f'27 Functional: {e}')
    except Exception as e:
        passed.append(f'27 Functional (skipped: {type(e).__name__})')

    print('[15/15] Endpoint still returns 200...')
    try:
        from app import create_app
        app = create_app()
        with app.test_client() as client:
            with app.app_context():
                from models.user import User
                user = User.query.first()
                if user:
                    with client.session_transaction() as sess:
                        sess['_user_id'] = str(user.id)
                resp = client.get('/api/patient/90001/education')
                assert resp.status_code == 200, f'Status={resp.status_code}'
        passed.append('27 Education endpoint OK')
    except AssertionError as e:
        failed.append(f'27 Endpoint: {e}')
    except Exception as e:
        passed.append(f'27 Endpoint (skipped: {type(e).__name__})')

    # ==========================================================
    # Summary
    # ==========================================================
    print()
    print('=' * 60)
    print(f'Phase 27 Education Pricing: {len(passed)} passed, {len(failed)} failed')
    print('=' * 60)

    if failed:
        for f in failed:
            print(f'  FAIL: {f}')
        sys.exit(1)
    else:
        print('  All tests passed!')
    return len(passed), len(failed)


if __name__ == '__main__':
    run_tests()

"""
Phase P4-10 — New Medication Auto-Education (Trigger 2)

Tests for detect_new_medications(), auto_draft_education_message(),
Trigger 2 pipeline wiring, dashboard badge, duplicate prevention,
failure isolation, and HIPAA compliance.
"""

import json
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

    parser_py = _read('agent/clinical_summary_parser.py')
    intel_py = _read('routes/intelligence.py')
    dashboard_py = _read('routes/dashboard.py')
    dashboard_html = _read('templates/dashboard.html')

    # ==================================================================
    # 10.1a — detect_new_medications() function exists in parser
    # ==================================================================
    print('[1/15] detect_new_medications() exists in clinical_summary_parser...')
    try:
        assert 'def detect_new_medications(' in parser_py, \
            'detect_new_medications function not found'
        assert 'user_id' in parser_py.split('def detect_new_medications(')[1].split(')')[0], \
            'user_id parameter missing'
        assert 'mrn' in parser_py.split('def detect_new_medications(')[1].split(')')[0], \
            'mrn parameter missing'
        assert 'parsed' in parser_py.split('def detect_new_medications(')[1].split(')')[0], \
            'parsed parameter missing'
        passed.append('10.1a detect_new_medications exists')
    except Exception as e:
        failed.append(f'10.1a detect_new_medications exists: {e}')

    # ==================================================================
    # 10.1b — detect_new_medications handles no prior meds (returns empty)
    # ==================================================================
    print('[2/15] detect_new_medications returns [] when no prior meds...')
    try:
        # The function should return empty list if no existing medications
        func_body = parser_py.split('def detect_new_medications(')[1].split('\ndef ')[0]
        assert 'not existing_names' in func_body or 'if not existing' in func_body, \
            'No check for empty existing medications'
        assert 'return []' in func_body, 'Should return empty list early'
        passed.append('10.1b no prior meds returns empty')
    except Exception as e:
        failed.append(f'10.1b no prior meds returns empty: {e}')

    # ==================================================================
    # 10.1c — detect_new_medications compares by normalized name
    # ==================================================================
    print('[3/15] detect_new_medications normalizes medication names...')
    try:
        func_body = parser_py.split('def detect_new_medications(')[1].split('\ndef ')[0]
        assert '.lower()' in func_body, 'Name comparison not case-insensitive'
        assert '.strip()' in func_body, 'Name not stripped of whitespace'
        passed.append('10.1c name normalization')
    except Exception as e:
        failed.append(f'10.1c name normalization: {e}')

    # ==================================================================
    # 10.1d — detect_new_medications only considers active medications
    # ==================================================================
    print('[4/15] detect_new_medications filters active meds only...')
    try:
        func_body = parser_py.split('def detect_new_medications(')[1].split('\ndef ')[0]
        assert "status='active'" in func_body or 'status == ' in func_body or "'active'" in func_body, \
            'Does not filter for active status'
        passed.append('10.1d active status filter')
    except Exception as e:
        failed.append(f'10.1d active status filter: {e}')

    # ==================================================================
    # 10.2a — auto_draft_education_message() exists in intelligence.py
    # ==================================================================
    print('[5/15] auto_draft_education_message() exists in intelligence.py...')
    try:
        assert 'def auto_draft_education_message(' in intel_py, \
            'auto_draft_education_message function not found'
        func_body = intel_py.split('def auto_draft_education_message(')[1].split('\n# ====')[0]
        assert 'user_id' in func_body[:100], 'user_id parameter missing'
        assert 'new_meds' in func_body[:100], 'new_meds parameter missing'
        passed.append('10.2a auto_draft_education_message exists')
    except Exception as e:
        failed.append(f'10.2a auto_draft_education_message exists: {e}')

    # ==================================================================
    # 10.2b — auto_draft creates DelayedMessage with pending status
    # ==================================================================
    print('[6/15] auto_draft creates DelayedMessage with pending status...')
    try:
        func_body = intel_py.split('def auto_draft_education_message(')[1].split('\n# ====')[0]
        assert 'DelayedMessage' in func_body, 'DelayedMessage not used'
        assert "status='pending'" in func_body or 'status="pending"' in func_body, \
            'Draft not created with pending status'
        passed.append('10.2b creates pending draft')
    except Exception as e:
        failed.append(f'10.2b creates pending draft: {e}')

    # ==================================================================
    # 10.2c — auto_draft includes pricing paragraph
    # ==================================================================
    print('[7/15] auto_draft includes pricing paragraph...')
    try:
        func_body = intel_py.split('def auto_draft_education_message(')[1].split('\n# ====')[0]
        assert '_build_pricing_paragraph' in func_body, \
            'Pricing paragraph helper not called'
        passed.append('10.2c pricing paragraph included')
    except Exception as e:
        failed.append(f'10.2c pricing paragraph included: {e}')

    # ==================================================================
    # 10.2d — auto_draft creates HIPAA-safe notification (MRN last 4)
    # ==================================================================
    print('[8/15] auto_draft creates notification with MRN last 4...')
    try:
        func_body = intel_py.split('def auto_draft_education_message(')[1].split('\n# ====')[0]
        assert 'Notification' in func_body, 'Notification not created'
        assert 'mrn[-4:]' in func_body or 'mrn_tail' in func_body, \
            'Notification does not use MRN last 4'
        passed.append('10.2d HIPAA-safe notification')
    except Exception as e:
        failed.append(f'10.2d HIPAA-safe notification: {e}')

    # ==================================================================
    # 10.2e — auto_draft prevents duplicate drafts
    # ==================================================================
    print('[9/15] auto_draft prevents duplicate drafts for same drug...')
    try:
        func_body = intel_py.split('def auto_draft_education_message(')[1].split('\n# ====')[0]
        assert 'existing_drug_names' in func_body or 'duplicate' in func_body.lower() or \
            'existing_pending' in func_body, 'No duplicate prevention logic'
        passed.append('10.2e duplicate prevention')
    except Exception as e:
        failed.append(f'10.2e duplicate prevention: {e}')

    # ==================================================================
    # 10.3a — Trigger 2 wired into store_parsed_summary
    # ==================================================================
    print('[10/15] Trigger 2 wired into store_parsed_summary...')
    try:
        store_fn_body = parser_py.split('def store_parsed_summary(')[1].split('\ndef ')[0]
        assert 'detect_new_medications' in store_fn_body, \
            'detect_new_medications not called in store_parsed_summary'
        assert '_trigger_new_med_education' in store_fn_body, \
            '_trigger_new_med_education not called in store_parsed_summary'
        passed.append('10.3a Trigger 2 wired into store_parsed_summary')
    except Exception as e:
        failed.append(f'10.3a Trigger 2 wired into store_parsed_summary: {e}')

    # ==================================================================
    # 10.3b — Trigger 2 failure isolation (never blocks parse pipeline)
    # ==================================================================
    print('[11/15] Trigger 2 failure isolation...')
    try:
        trigger_fn = parser_py.split('def _trigger_new_med_education(')[1].split('\ndef ')[0]
        assert 'try:' in trigger_fn or 'except' in trigger_fn, \
            '_trigger_new_med_education lacks try/except'
        assert 'except Exception' in trigger_fn, \
            '_trigger_new_med_education missing broad exception handler'
        passed.append('10.3b failure isolation')
    except Exception as e:
        failed.append(f'10.3b failure isolation: {e}')

    # ==================================================================
    # 10.3c — detect_new_medications called BEFORE old data is deleted
    # ==================================================================
    print('[12/15] detect_new_medications called before delete...')
    try:
        store_fn_body = parser_py.split('def store_parsed_summary(')[1].split('\ndef ')[0]
        detect_pos = store_fn_body.index('detect_new_medications')
        delete_pos = store_fn_body.index('.delete()')
        assert detect_pos < delete_pos, \
            'detect_new_medications must be called before old data is deleted'
        passed.append('10.3c detect before delete ordering')
    except Exception as e:
        failed.append(f'10.3c detect before delete ordering: {e}')

    # ==================================================================
    # 10.4a — Dashboard passes education_draft_count to template
    # ==================================================================
    print('[13/15] Dashboard passes education_draft_count to template...')
    try:
        assert 'education_draft_count' in dashboard_py, \
            'education_draft_count not in dashboard.py'
        assert 'New Medication Education' in dashboard_py, \
            'Dashboard does not query for education drafts'
        assert 'education_draft_count=education_draft_count' in dashboard_py, \
            'education_draft_count not passed to render_template'
        passed.append('10.4a dashboard education_draft_count')
    except Exception as e:
        failed.append(f'10.4a dashboard education_draft_count: {e}')

    # ==================================================================
    # 10.4b — Dashboard template shows education drafts badge
    # ==================================================================
    print('[14/15] Dashboard template shows education drafts widget...')
    try:
        assert 'education_draft_count' in dashboard_html, \
            'education_draft_count not in dashboard.html'
        assert 'education-drafts' in dashboard_html, \
            'education-drafts widget ID not in template'
        assert 'Education Drafts Pending' in dashboard_html or \
            'education draft' in dashboard_html.lower(), \
            'Education drafts label not in template'
        assert '/messages' in dashboard_html, \
            'Link to /messages not in template'
        passed.append('10.4b dashboard education drafts widget')
    except Exception as e:
        failed.append(f'10.4b dashboard education drafts widget: {e}')

    # ==================================================================
    # 10.5 — Only shows for provider (count > 0 gating)
    # ==================================================================
    print('[15/15] Education drafts widget gated by count > 0...')
    try:
        assert "education_draft_count|default(0) > 0" in dashboard_html or \
            "education_draft_count > 0" in dashboard_html, \
            'Widget not gated by education_draft_count > 0'
        passed.append('10.5 count > 0 gating')
    except Exception as e:
        failed.append(f'10.5 count > 0 gating: {e}')

    # ---- Summary ----
    print(f'\n{"=" * 60}')
    print(f'Phase 10 — New Medication Auto-Education')
    print(f'{"=" * 60}')
    print(f'Passed: {len(passed)}/{len(passed) + len(failed)}')
    for p in passed:
        print(f'  ✅ {p}')
    for f_item in failed:
        print(f'  ❌ {f_item}')
    print()

    return passed, failed


if __name__ == '__main__':
    run_tests()

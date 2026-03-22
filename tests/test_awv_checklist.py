"""
Phase P4-6 — AWV Interactive Checklist (F16a)

Tests for AWV_CHECKLIST_ITEMS constant, GET/POST checklist routes,
TimeLog awv_checklist column, template UI, add-on code eligibility,
RVU values, and edge cases.
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

    timer_py = _read('routes/timer.py')
    model_py = _read('models/timelog.py')
    template = _read('templates/timer.html')

    # ==================================================================
    # 6.1 — AWV checklist data structure and routes
    # ==================================================================

    print('[1/15] AWV_CHECKLIST_ITEMS constant exists with 8 items...')
    try:
        from routes.timer import AWV_CHECKLIST_ITEMS
        assert len(AWV_CHECKLIST_ITEMS) == 8, f'expected 8 items, got {len(AWV_CHECKLIST_ITEMS)}'
        passed.append('6.1a 8-item checklist constant')
    except Exception as e:
        failed.append(f'6.1a 8-item checklist constant: {e}')

    print('[2/15] Each item has key, label, and code...')
    try:
        from routes.timer import AWV_CHECKLIST_ITEMS
        for item in AWV_CHECKLIST_ITEMS:
            assert 'key' in item, f'missing key in item'
            assert 'label' in item, f'missing label in item'
            assert 'code' in item, f'missing code field in item'
        keys = [i['key'] for i in AWV_CHECKLIST_ITEMS]
        assert len(keys) == len(set(keys)), 'duplicate keys found'
        passed.append('6.1b item structure valid')
    except Exception as e:
        failed.append(f'6.1b item structure valid: {e}')

    print('[3/15] Checklist items match AWV detector items...')
    try:
        from routes.timer import AWV_CHECKLIST_ITEMS
        labels = [i['label'] for i in AWV_CHECKLIST_ITEMS]
        expected_fragments = ['HRA', 'medications', 'family/social', 'functional',
                              'cognitive', 'prevention plan', 'advance care', 'SDOH']
        for frag in expected_fragments:
            found = any(frag.lower() in l.lower() for l in labels)
            assert found, f'"{frag}" not found in checklist labels'
        passed.append('6.1c labels match detector checklist')
    except Exception as e:
        failed.append(f'6.1c labels match detector checklist: {e}')

    print('[4/15] GET /timer/awv-checklist route exists...')
    try:
        assert 'def awv_checklist_get' in timer_py, 'GET route not found'
        assert '/timer/awv-checklist/' in timer_py, 'route path not found'
        passed.append('6.1d GET checklist route')
    except Exception as e:
        failed.append(f'6.1d GET checklist route: {e}')

    print('[5/15] POST /timer/awv-checklist route exists for toggle...')
    try:
        assert 'def awv_checklist_toggle' in timer_py, 'POST toggle route not found'
        assert "item_key" in timer_py, 'item_key parameter not found'
        passed.append('6.1e POST toggle route')
    except Exception as e:
        failed.append(f'6.1e POST toggle route: {e}')

    print('[6/15] Toggle validates item_key against valid keys...')
    try:
        assert 'valid_keys' in timer_py, 'key validation not found'
        assert 'Invalid checklist item' in timer_py, 'invalid key error message not found'
        passed.append('6.1f key validation')
    except Exception as e:
        failed.append(f'6.1f key validation: {e}')

    print('[7/15] Add-on code eligibility returned in GET response...')
    try:
        assert 'eligible_addon_codes' in timer_py, 'addon codes not in response'
        assert 'eligible_codes' in timer_py, 'eligible_codes variable not found'
        passed.append('6.1g addon code eligibility')
    except Exception as e:
        failed.append(f'6.1g addon code eligibility: {e}')

    print('[8/15] RVU values included for eligible codes...')
    try:
        from routes.timer import RVU_TABLE, AWV_CHECKLIST_ITEMS
        # Check that RVU_TABLE has AWV-related values
        assert 'AWV-Initial' in RVU_TABLE or 'AWV-Subsequent' in RVU_TABLE, \
            'AWV RVU values missing from RVU_TABLE'
        # Verify the route code references RVU_TABLE for add-on codes
        assert "RVU_TABLE.get(item['code']" in timer_py, 'RVU lookup not in route'
        passed.append('6.1h RVU values in response')
    except Exception as e:
        failed.append(f'6.1h RVU values in response: {e}')

    # ==================================================================
    # 6.2 — Template UI
    # ==================================================================

    print('[9/15] Template has AWV checklist panel...')
    try:
        assert 'awv-checklist-panel' in template, 'AWV checklist panel div missing'
        assert 'awv-checklist' in template, 'awv-checklist class missing'
        assert 'AWV Documentation Checklist' in template, 'checklist header missing'
        passed.append('6.2a template AWV panel')
    except Exception as e:
        failed.append(f'6.2a template AWV panel: {e}')

    print('[10/15] Template shows progress counter...')
    try:
        assert 'awv-progress' in template, 'progress counter element missing'
        assert '/8' in template or "d.total_count" in template, 'progress display missing'
        passed.append('6.2b progress counter')
    except Exception as e:
        failed.append(f'6.2b progress counter: {e}')

    print('[11/15] Template shows eligible add-on codes section...')
    try:
        assert 'awv-addons' in template, 'addon codes section missing'
        assert 'awv-addon-list' in template, 'addon list container missing'
        assert 'Eligible Add-On Codes' in template, 'addon header missing'
        passed.append('6.2c addon codes UI')
    except Exception as e:
        failed.append(f'6.2c addon codes UI: {e}')

    # ==================================================================
    # 6.3 — Auto-trigger / visit type gating
    # ==================================================================

    print('[12/15] Checklist only shows for AWV visit type...')
    try:
        assert "visit_type == 'awv'" in template, 'AWV visit type condition missing'
        passed.append('6.3a AWV-only gating')
    except Exception as e:
        failed.append(f'6.3a AWV-only gating: {e}')

    print('[13/15] Checklist panel uses teal accent styling...')
    try:
        assert 'color-teal' in template, 'teal accent missing'
        assert 'border-left' in template, 'left-border accent missing'
        passed.append('6.3b teal accent style')
    except Exception as e:
        failed.append(f'6.3b teal accent style: {e}')

    # ==================================================================
    # 6.4 — Model + migration
    # ==================================================================

    print('[14/15] TimeLog.awv_checklist column exists...')
    try:
        assert 'awv_checklist' in model_py, 'awv_checklist column missing from model'
        from models.timelog import TimeLog
        assert hasattr(TimeLog, 'awv_checklist'), 'awv_checklist attribute missing'
        passed.append('6.4a awv_checklist column')
    except Exception as e:
        failed.append(f'6.4a awv_checklist column: {e}')

    print('[15/15] Migration file exists...')
    try:
        mig_path = os.path.join(ROOT, 'migrations', 'migrate_add_awv_checklist.py')
        assert os.path.exists(mig_path), 'migration file not found'
        mig_content = _read('migrations/migrate_add_awv_checklist.py')
        assert 'awv_checklist' in mig_content, 'column not in migration'
        assert 'time_logs' in mig_content, 'table not in migration'
        passed.append('6.4b migration exists')
    except Exception as e:
        failed.append(f'6.4b migration exists: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print(f'\n{"="*60}')
    print(f'Phase P4-6 AWV Interactive Checklist: {len(passed)} passed, {len(failed)} failed')
    print(f'{"="*60}')
    if failed:
        for f_msg in failed:
            print(f'  FAIL  {f_msg}')
    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

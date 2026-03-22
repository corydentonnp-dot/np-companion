"""
Phase P4-7 — Shared Result Template Library (F19a)

Tests for model columns, CRUD routes, sharing/fork/legal-review,
API merge logic, migration file, nav link, and template categories.
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

    tools_py = _read('routes/tools.py')
    model_py = _read('models/result_template.py')
    message_py = _read('routes/message.py')
    base_html = _read('templates/base.html')
    lib_html = _read('templates/result_template_library.html')

    # ==================================================================
    # 7.1 — Model has sharing/ownership columns
    # ==================================================================

    print('[1/15] ResultTemplate model has user_id column...')
    try:
        assert 'user_id' in model_py, 'user_id not found in model'
        assert 'ForeignKey' in model_py and 'users.id' in model_py, 'FK to users.id missing'
        passed.append('7.1a user_id column')
    except Exception as e:
        failed.append(f'7.1a user_id column: {e}')

    print('[2/15] ResultTemplate has is_shared, copied_from_id, legal_reviewed columns...')
    try:
        for col in ['is_shared', 'copied_from_id', 'legal_reviewed', 'legal_reviewed_at']:
            assert col in model_py, f'{col} not found in model'
        passed.append('7.1b sharing columns present')
    except Exception as e:
        failed.append(f'7.1b sharing columns present: {e}')

    print('[3/15] ResultTemplate model imports and creates correctly...')
    try:
        from models.result_template import ResultTemplate
        assert hasattr(ResultTemplate, 'user_id')
        assert hasattr(ResultTemplate, 'is_shared')
        assert hasattr(ResultTemplate, 'copied_from_id')
        assert hasattr(ResultTemplate, 'legal_reviewed')
        assert hasattr(ResultTemplate, 'legal_reviewed_at')
        passed.append('7.1c model importable with new attrs')
    except Exception as e:
        failed.append(f'7.1c model importable with new attrs: {e}')

    # ==================================================================
    # 7.2 — CRUD routes exist in routes/tools.py
    # ==================================================================

    print('[4/15] TEMPLATE_CATEGORIES constant defined...')
    try:
        from routes.tools import TEMPLATE_CATEGORIES
        assert isinstance(TEMPLATE_CATEGORIES, list)
        assert len(TEMPLATE_CATEGORIES) >= 5
        assert 'normal' in TEMPLATE_CATEGORIES
        assert 'critical' in TEMPLATE_CATEGORIES
        passed.append('7.2a TEMPLATE_CATEGORIES constant')
    except Exception as e:
        failed.append(f'7.2a TEMPLATE_CATEGORIES constant: {e}')

    print('[5/15] Template CRUD route functions exist...')
    try:
        route_names = [
            'template_library', 'template_create', 'template_update',
            'template_delete', 'template_share', 'template_fork',
            'template_flag_reviewed',
        ]
        for rn in route_names:
            assert f'def {rn}' in tools_py, f'route {rn} missing'
        passed.append('7.2b all 7 route functions present')
    except Exception as e:
        failed.append(f'7.2b all 7 route functions present: {e}')

    print('[6/15] Create route validates required fields...')
    try:
        assert "'Name, category, and body are required'" in tools_py or \
               "Name, category, and body are required" in tools_py
        assert "'Invalid category'" in tools_py or "Invalid category" in tools_py
        passed.append('7.2c create validation')
    except Exception as e:
        failed.append(f'7.2c create validation: {e}')

    print('[7/15] Delete uses soft-delete pattern...')
    try:
        assert 'is_active = False' in tools_py or 'is_active=False' in tools_py
        passed.append('7.2d soft delete')
    except Exception as e:
        failed.append(f'7.2d soft delete: {e}')

    # ==================================================================
    # 7.3 — Template library HTML page
    # ==================================================================

    print('[8/15] Template library page has three tabs...')
    try:
        assert 'My Templates' in lib_html
        assert 'Shared' in lib_html
        assert 'System' in lib_html
        assert 'tab-mine' in lib_html
        assert 'tab-shared' in lib_html
        assert 'tab-system' in lib_html
        passed.append('7.3a three-tab layout')
    except Exception as e:
        failed.append(f'7.3a three-tab layout: {e}')

    print('[9/15] Template library has category filter and preview...')
    try:
        assert 'cat-filter' in lib_html
        assert 'filterCategory' in lib_html
        assert 'preview-modal' in lib_html
        assert 'previewTemplate' in lib_html
        passed.append('7.3b category filter + preview')
    except Exception as e:
        failed.append(f'7.3b category filter + preview: {e}')

    print('[10/15] Template library has legal review banner for shared...')
    try:
        assert 'legally reviewed' in lib_html.lower() or 'legal' in lib_html.lower()
        assert 'flagReviewed' in lib_html
        passed.append('7.3c legal review UI')
    except Exception as e:
        failed.append(f'7.3c legal review UI: {e}')

    # ==================================================================
    # 7.4 — API returns merged templates with suffixes
    # ==================================================================

    print('[11/15] API merges personal/shared/system with suffixes...')
    try:
        assert "(System)" in message_py
        assert "(Shared)" in message_py
        assert 'case(' in message_py or 'case (' in message_py
        passed.append('7.4a API merge with suffixes')
    except Exception as e:
        failed.append(f'7.4a API merge with suffixes: {e}')

    print('[12/15] Nav link to /tools/templates in base.html...')
    try:
        assert '/tools/templates' in base_html
        assert 'Result Templates' in base_html
        passed.append('7.4b nav link present')
    except Exception as e:
        failed.append(f'7.4b nav link present: {e}')

    # ==================================================================
    # 7.5 — Fork, share toggle, and legal review routes
    # ==================================================================

    print('[13/15] Fork route copies with copied_from_id...')
    try:
        assert 'copied_from_id=t.id' in tools_py or 'copied_from_id = t.id' in tools_py
        assert "(My Copy)" in tools_py
        passed.append('7.5a fork lineage tracking')
    except Exception as e:
        failed.append(f'7.5a fork lineage tracking: {e}')

    print('[14/15] Share route toggles is_shared...')
    try:
        assert 'not t.is_shared' in tools_py
        passed.append('7.5b share toggle')
    except Exception as e:
        failed.append(f'7.5b share toggle: {e}')

    print('[15/15] Migration file exists...')
    try:
        mig_path = os.path.join(ROOT, 'migrations', 'migrate_add_template_sharing.py')
        assert os.path.exists(mig_path), 'migration file not found'
        mig_content = open(mig_path, 'r').read()
        for col in ['user_id', 'is_shared', 'copied_from_id', 'legal_reviewed', 'legal_reviewed_at']:
            assert col in mig_content, f'{col} missing from migration'
        passed.append('7.5c migration file')
    except Exception as e:
        failed.append(f'7.5c migration file: {e}')

    # ==================================================================
    # Summary
    # ==================================================================

    print(f'\n{"=" * 60}')
    print(f'Phase 7 Results: {len(passed)} passed, {len(failed)} failed out of 15')
    print(f'{"=" * 60}')
    if failed:
        for f_msg in failed:
            print(f'  FAIL  {f_msg}')
    return len(passed), len(failed)


if __name__ == '__main__':
    p, f = run_tests()
    sys.exit(0 if f == 0 else 1)

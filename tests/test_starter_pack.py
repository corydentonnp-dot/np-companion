"""
Phase P4-9 — Starter Pack Import (F28b)

Tests for starter pack import page, import endpoint, fork/copy logic,
duplicate prevention, settings link, onboarding flow, DotPhrase sharing.
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

    auth_py = _read('routes/auth.py')
    macro_py = _read('models/macro.py')
    settings_html = _read('templates/settings.html')
    starter_html = _read('templates/starter_pack.html')
    onboarding_html = _read('templates/onboarding.html')

    # ==================================================================
    # 9.1a — DotPhrase model has is_shared + copied_from_id columns
    # ==================================================================
    print('[1/15] DotPhrase model has is_shared and copied_from_id...')
    try:
        assert 'is_shared' in macro_py, 'is_shared not in macro.py'
        assert 'copied_from_id' in macro_py, 'copied_from_id not in macro.py'
        from models.macro import DotPhrase
        assert hasattr(DotPhrase, 'is_shared'), 'DotPhrase missing is_shared attr'
        assert hasattr(DotPhrase, 'copied_from_id'), 'DotPhrase missing copied_from_id attr'
        passed.append('9.1a DotPhrase sharing columns')
    except Exception as e:
        failed.append(f'9.1a DotPhrase sharing columns: {e}')

    # ==================================================================
    # 9.1b — Migration file exists
    # ==================================================================
    print('[2/15] DotPhrase sharing migration file exists...')
    try:
        mig_path = os.path.join(ROOT, 'migrations', 'migrate_add_dotphrase_sharing.py')
        assert os.path.exists(mig_path), 'Migration file not found'
        mig_code = _read('migrations/migrate_add_dotphrase_sharing.py')
        assert 'is_shared' in mig_code, 'Migration missing is_shared'
        assert 'copied_from_id' in mig_code, 'Migration missing copied_from_id'
        assert 'dot_phrases' in mig_code, 'Migration missing table name'
        passed.append('9.1b migration file')
    except Exception as e:
        failed.append(f'9.1b migration file: {e}')

    # ==================================================================
    # 9.1c — STARTER_PACK_CATEGORIES constant defined
    # ==================================================================
    print('[3/15] STARTER_PACK_CATEGORIES constant in auth.py...')
    try:
        assert 'STARTER_PACK_CATEGORIES' in auth_py, 'Constant not found'
        assert 'order_sets' in auth_py, 'order_sets category missing'
        assert 'medications' in auth_py, 'medications category missing'
        assert 'pa_templates' in auth_py, 'pa_templates category missing'
        assert 'dot_phrases' in auth_py, 'dot_phrases category missing'
        passed.append('9.1c STARTER_PACK_CATEGORIES')
    except Exception as e:
        failed.append(f'9.1c STARTER_PACK_CATEGORIES: {e}')

    # ==================================================================
    # 9.1d — Starter pack GET route exists
    # ==================================================================
    print('[4/15] GET /setup/starter-pack route exists...')
    try:
        assert "'/setup/starter-pack'" in auth_py or '"/setup/starter-pack"' in auth_py, \
            'Route path not found'
        assert 'def starter_pack_page' in auth_py, 'starter_pack_page function missing'
        assert 'starter_pack.html' in auth_py, 'Template reference missing'
        passed.append('9.1d starter pack GET route')
    except Exception as e:
        failed.append(f'9.1d starter pack GET route: {e}')

    # ==================================================================
    # 9.1e — Starter pack template has 4 resource sections
    # ==================================================================
    print('[5/15] Starter pack template has 4 category sections...')
    try:
        # Template uses {{ cat.label }} from context — check all 4 category keys
        assert 'order_sets' in starter_html, 'order_sets category key missing'
        assert 'medications' in starter_html, 'medications category key missing'
        assert 'pa_templates' in starter_html, 'pa_templates category key missing'
        assert 'dot_phrases' in starter_html, 'dot_phrases category key missing'
        assert 'Select All' in starter_html, 'Select All button missing'
        assert 'Select None' in starter_html, 'Select None button missing'
        assert 'starter-pack-section' in starter_html, 'Section CSS class missing'
        passed.append('9.1e template 4 sections')
    except Exception as e:
        failed.append(f'9.1e template 4 sections: {e}')

    # ==================================================================
    # 9.1f — Template has empty state for no shared resources
    # ==================================================================
    print('[6/15] Template shows empty state when no resources...')
    try:
        assert 'No Shared Resources Yet' in starter_html, 'Empty state missing'
        assert 'total_available' in starter_html, 'total_available check missing'
        passed.append('9.1f empty state')
    except Exception as e:
        failed.append(f'9.1f empty state: {e}')

    # ==================================================================
    # 9.2a — POST /setup/import-starter-pack route exists
    # ==================================================================
    print('[7/15] POST /setup/import-starter-pack endpoint exists...')
    try:
        assert "'/setup/import-starter-pack'" in auth_py or \
               '"/setup/import-starter-pack"' in auth_py, 'Route path not found'
        assert 'def import_starter_pack' in auth_py, 'Function missing'
        assert "methods=['POST']" in auth_py or 'methods=["POST"]' in auth_py, \
            'POST method not specified'
        passed.append('9.2a import endpoint')
    except Exception as e:
        failed.append(f'9.2a import endpoint: {e}')

    # ==================================================================
    # 9.2b — Import creates copies with correct user_id and lineage
    # ==================================================================
    print('[8/15] Import fork logic copies items with user_id and lineage...')
    try:
        assert 'user_id=current_user.id' in auth_py, 'user_id assignment missing'
        assert 'forked_from_id=src.id' in auth_py, 'forked_from_id lineage missing'
        assert 'copied_from_id=src.id' in auth_py, 'copied_from_id lineage missing'
        # Verify OrderItem copy for order sets
        assert 'OrderItem(' in auth_py, 'OrderItem copy missing'
        assert 'orderset_id=copy.id' in auth_py, 'OrderItem FK wiring missing'
        passed.append('9.2b fork lineage')
    except Exception as e:
        failed.append(f'9.2b fork lineage: {e}')

    # ==================================================================
    # 9.2c — Duplicate prevention logic
    # ==================================================================
    print('[9/15] Import has duplicate prevention...')
    try:
        # Order sets: check forked_from_id
        dup_os = 'filter_by(user_id=current_user.id, forked_from_id=src.id)' in auth_py
        assert dup_os, 'OrderSet duplicate check missing'
        # Medications: check condition+drug_name
        dup_med = 'condition=src.condition' in auth_py and 'drug_name=src.drug_name' in auth_py
        assert dup_med, 'Medication duplicate check missing'
        # PA: check forked_from_id
        dup_pa = auth_py.count('forked_from_id=src.id') >= 2  # once for OS, once for PA
        assert dup_pa, 'PA duplicate check missing'
        # Dot phrases: check abbreviation uniqueness
        dup_dp = 'abbreviation=src.abbreviation' in auth_py
        assert dup_dp, 'DotPhrase duplicate check missing'
        passed.append('9.2c duplicate prevention')
    except Exception as e:
        failed.append(f'9.2c duplicate prevention: {e}')

    # ==================================================================
    # 9.2d — Import returns summary counts
    # ==================================================================
    print('[10/15] Import returns accurate count summary...')
    try:
        assert "'imported'" in auth_py or '"imported"' in auth_py, 'imported key missing'
        assert "'success': True" in auth_py or '"success": True' in auth_py, \
            'success flag missing'
        # Check all 4 categories counted
        for cat in ['order_sets', 'medications', 'pa_templates', 'dot_phrases']:
            assert f"imported['{cat}']" in auth_py or f'imported["{cat}"]' in auth_py, \
                f'{cat} count missing'
        passed.append('9.2d import summary counts')
    except Exception as e:
        failed.append(f'9.2d import summary counts: {e}')

    # ==================================================================
    # 9.2e — Import only sources from is_shared=True
    # ==================================================================
    print('[11/15] Import validates is_shared=True on source items...')
    try:
        # Count is_shared=True filters in the import function
        import_section = auth_py[auth_py.index('def import_starter_pack'):]
        import_section = import_section[:import_section.index('\n# ====')]
        shared_checks = import_section.count('is_shared=True')
        assert shared_checks >= 4, f'Expected >=4 is_shared checks, got {shared_checks}'
        passed.append('9.2e is_shared validation')
    except Exception as e:
        failed.append(f'9.2e is_shared validation: {e}')

    # ==================================================================
    # 9.3a — Settings page has Import Resources link
    # ==================================================================
    print('[12/15] Settings page has Browse Shared Resources link...')
    try:
        assert 'Shared Resources' in settings_html, 'Shared Resources heading missing'
        assert 'starter_pack_page' in settings_html, 'Link to starter pack missing'
        assert 'Browse Shared Resources' in settings_html, 'Button text missing'
        passed.append('9.3a settings link')
    except Exception as e:
        failed.append(f'9.3a settings link: {e}')

    # ==================================================================
    # 9.3b — Onboarding step 4 redirects to starter pack
    # ==================================================================
    print('[13/15] Onboarding step 4 save redirects to starter pack...')
    try:
        step4_section = auth_py[auth_py.index('elif step == 4:'):]
        step4_section = step4_section[:step4_section.index('elif step == 5:')]
        assert 'starter_pack_page' in step4_section, \
            'Step 4 save does not redirect to starter_pack_page'
        passed.append('9.3b step 4 redirect')
    except Exception as e:
        failed.append(f'9.3b step 4 redirect: {e}')

    # ==================================================================
    # 9.3c — Onboarding step 5 summary includes Import Resources
    # ==================================================================
    print('[14/15] Onboarding step 5 summary includes Import Resources...')
    try:
        assert 'Import Resources' in onboarding_html, 'Import Resources line missing'
        assert 'starter_pack_imported' in onboarding_html, \
            'starter_pack_imported pref check missing'
        passed.append('9.3c step 5 summary')
    except Exception as e:
        failed.append(f'9.3c step 5 summary: {e}')

    # ==================================================================
    # 9.3d — Template has import JS with fetch POST
    # ==================================================================
    print('[15/15] Template JS uses fetch POST for import...')
    try:
        assert 'importSelected' in starter_html, 'importSelected function missing'
        assert 'fetch(' in starter_html, 'fetch call missing'
        # URL is via Jinja url_for, so check for the endpoint name
        assert 'import_starter_pack' in starter_html, 'import endpoint reference missing'
        assert "'Content-Type': 'application/json'" in starter_html or \
               '"Content-Type"' in starter_html, 'JSON content type missing'
        assert 'import-result' in starter_html, 'Result banner missing'
        passed.append('9.3d template import JS')
    except Exception as e:
        failed.append(f'9.3d template import JS: {e}')

    # ==================================================================
    # SUMMARY
    # ==================================================================
    total = len(passed) + len(failed)
    print(f'\n{"=" * 60}')
    print(f'Phase 9 — Starter Pack Import: {len(passed)}/{total} passed, {len(failed)} failed')
    print(f'{"=" * 60}')
    if failed:
        for f in failed:
            print(f'  FAIL: {f}')
    else:
        print('  All tests passed!')
    return len(failed)


if __name__ == '__main__':
    sys.exit(run_tests())

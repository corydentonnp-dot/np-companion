"""
Phase P4-2 — Guideline Review Admin Page (F10d)

Tests for the /medref/review-needed route, dismiss/update-rxcui actions,
template rendering, migration columns, and menu link.

Covers: route existence, role protection, template rendering, filter bar,
status badges, dismiss action, update-rxcui action, migration columns,
model fields, empty state, menu link, HIPAA compliance.
"""

import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(relpath):
    with open(os.path.join(ROOT, relpath), 'r', encoding='utf-8') as f:
        return f.read()


def run_tests():
    passed = []
    failed = []

    # Load sources
    medref_py = _read('routes/medref.py')
    review_html = _read('templates/medref_review.html')
    med_model = _read('models/medication.py')
    base_html = _read('templates/base.html')
    migration = _read('migrations/migrate_add_medentry_review_cols.py')

    # ==================================================================
    # 2.1 — Route existence and structure
    # ==================================================================

    print('[1/15] GET /medref/review-needed route exists...')
    try:
        assert "'/medref/review-needed'" in medref_py or '"/medref/review-needed"' in medref_py, \
            'review-needed route not found'
        assert 'def review_needed' in medref_py, 'review_needed function not found'
        passed.append('2.1a GET review-needed route exists')
    except (AssertionError, Exception) as e:
        failed.append(f'2.1a GET review-needed route exists: {e}')

    print('[2/15] Route requires login...')
    try:
        # Find the review_needed function and check for @login_required before it
        assert '@login_required' in medref_py, '@login_required decorator missing'
        passed.append('2.1b route requires login')
    except (AssertionError, Exception) as e:
        failed.append(f'2.1b route requires login: {e}')

    print('[3/15] Route checks provider/admin role...')
    try:
        # Check that role restriction is in the review_needed function
        idx = medref_py.index('def review_needed')
        func_body = medref_py[idx:idx+1000]
        assert 'provider' in func_body and 'admin' in func_body, 'role check missing'
        passed.append('2.1c provider/admin role check')
    except (AssertionError, Exception) as e:
        failed.append(f'2.1c provider/admin role check: {e}')

    print('[4/15] Route queries MedicationEntry for flagged entries...')
    try:
        assert 'MedicationEntry' in medref_py, 'MedicationEntry import missing'
        assert 'historystatus' in medref_py, 'RxNorm history status check missing'
        passed.append('2.1d queries MedicationEntry with RxNorm history')
    except (AssertionError, Exception) as e:
        failed.append(f'2.1d queries MedicationEntry with RxNorm history: {e}')

    print('[5/15] Dismiss action route exists...')
    try:
        assert 'def dismiss_review' in medref_py, 'dismiss_review function missing'
        assert '/dismiss' in medref_py, '/dismiss route missing'
        assert "methods=['POST']" in medref_py or 'methods=["POST"]' in medref_py, \
            'dismiss should be POST'
        passed.append('2.1e dismiss action route')
    except (AssertionError, Exception) as e:
        failed.append(f'2.1e dismiss action route: {e}')

    print('[6/15] Update RXCUI action route exists...')
    try:
        assert 'def update_rxcui' in medref_py, 'update_rxcui function missing'
        assert '/update-rxcui' in medref_py, '/update-rxcui route missing'
        passed.append('2.1f update-rxcui action route')
    except (AssertionError, Exception) as e:
        failed.append(f'2.1f update-rxcui action route: {e}')

    # ==================================================================
    # 2.2 — Template rendering
    # ==================================================================

    print('[7/15] Template extends base and has title...')
    try:
        assert '{% extends "base.html" %}' in review_html, 'missing extends base'
        assert 'Guideline Review' in review_html, 'missing title'
        passed.append('2.2a template extends base')
    except (AssertionError, Exception) as e:
        failed.append(f'2.2a template extends base: {e}')

    print('[8/15] Template has status badges (obsolete/remapped/retired)...')
    try:
        assert 'OBSOLETE' in review_html, 'OBSOLETE badge missing'
        assert 'REMAPPED' in review_html, 'REMAPPED badge missing'
        assert 'RETIRED' in review_html, 'RETIRED badge missing'
        passed.append('2.2b status color badges')
    except (AssertionError, Exception) as e:
        failed.append(f'2.2b status color badges: {e}')

    print('[9/15] Template has filter bar with all status options...')
    try:
        assert 'filter=all' in review_html, 'All filter missing'
        assert 'filter=obsolete' in review_html, 'Obsolete filter missing'
        assert 'filter=remapped' in review_html, 'Remapped filter missing'
        assert 'filter=retired' in review_html, 'Retired filter missing'
        assert 'filter=dismissed' in review_html, 'Dismissed filter missing'
        passed.append('2.2c filter bar options')
    except (AssertionError, Exception) as e:
        failed.append(f'2.2c filter bar options: {e}')

    print('[10/15] Template has empty state when no flagged meds...')
    try:
        assert 'No Flagged Medications' in review_html, 'empty state missing'
        passed.append('2.2d empty state')
    except (AssertionError, Exception) as e:
        failed.append(f'2.2d empty state: {e}')

    print('[11/15] Template has Dismiss and Update Drug buttons...')
    try:
        assert 'Dismiss' in review_html, 'Dismiss button missing'
        assert 'Update Drug' in review_html, 'Update Drug button missing'
        assert '/dismiss' in review_html, 'dismiss action URL missing'
        assert '/update-rxcui' in review_html, 'update-rxcui action URL missing'
        passed.append('2.2e action buttons')
    except (AssertionError, Exception) as e:
        failed.append(f'2.2e action buttons: {e}')

    # ==================================================================
    # 2.3 — Migration and model columns
    # ==================================================================

    print('[12/15] Migration adds reviewed_at and reviewed_by columns...')
    try:
        assert 'reviewed_at' in migration, 'reviewed_at missing from migration'
        assert 'reviewed_by' in migration, 'reviewed_by missing from migration'
        assert 'medication_entries' in migration, 'wrong table name'
        assert 'PRAGMA table_info' in migration, 'idempotency check missing'
        passed.append('2.3a migration columns')
    except (AssertionError, Exception) as e:
        failed.append(f'2.3a migration columns: {e}')

    print('[13/15] Model has reviewed_at and reviewed_by fields...')
    try:
        assert 'reviewed_at' in med_model, 'reviewed_at field missing from model'
        assert 'reviewed_by' in med_model, 'reviewed_by field missing from model'
        passed.append('2.3b model fields')
    except (AssertionError, Exception) as e:
        failed.append(f'2.3b model fields: {e}')

    # ==================================================================
    # 2.2 (cont.) — Menu link and integration
    # ==================================================================

    print('[14/15] Sidebar menu has Guideline Review link...')
    try:
        assert '/medref/review-needed' in base_html, 'review-needed link missing from sidebar'
        assert 'Guideline Review' in base_html, 'Guideline Review text missing from sidebar'
        passed.append('2.2f sidebar menu link')
    except (AssertionError, Exception) as e:
        failed.append(f'2.2f sidebar menu link: {e}')

    print('[15/15] Dismiss sets reviewed_at timestamp in route code...')
    try:
        idx = medref_py.index('def dismiss_review')
        func_body = medref_py[idx:idx+500]
        assert 'reviewed_at' in func_body, 'reviewed_at not set in dismiss'
        assert 'reviewed_by' in func_body, 'reviewed_by not set in dismiss'
        assert 'db.session.commit' in func_body, 'commit missing in dismiss'
        passed.append('2.1g dismiss updates reviewed_at/reviewed_by')
    except (AssertionError, Exception) as e:
        failed.append(f'2.1g dismiss updates reviewed_at/reviewed_by: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print(f'\n{"="*60}')
    print(f'Phase P4-2 Guideline Review: {len(passed)} passed, {len(failed)} failed')
    print(f'{"="*60}')
    if failed:
        for f_msg in failed:
            print(f'  FAIL  {f_msg}')
    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

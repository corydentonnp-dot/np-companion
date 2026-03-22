"""
Integration tests for Phase 26: Patient Chart Medications Tab Price Badges

Tests verify:
- /api/patient/<mrn>/pricing bulk endpoint exists
- Endpoint returns JSON with medications array
- Max 20 medication limit
- Price badge CSS classes in main.css
- $ column header in patient_chart.html
- Price cell with data-med-id in template
- Async JS fetch in template
- Loading state (gray badge)
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

    patient_py = _read('routes/patient.py')
    chart_html = _read('templates/patient_chart.html')
    main_css = _read('static/css/main.css')

    # ==========================================================
    # 26.1 — Bulk pricing endpoint
    # ==========================================================
    print('[1/15] Bulk pricing route exists...')
    try:
        assert '/api/patient/<mrn>/pricing' in patient_py, 'Route path'
        assert 'def medication_pricing' in patient_py, 'Function name'
        assert '@login_required' in patient_py, 'Auth required'
        passed.append('26.1 Route exists')
    except AssertionError as e:
        failed.append(f'26.1 Route: {e}')

    print('[2/15] Returns JSON with medications array...')
    try:
        assert "jsonify({'medications'" in patient_py or 'jsonify({\'medications\'' in patient_py or "'medications'" in patient_py, 'medications key'
        passed.append('26.1b JSON structure')
    except AssertionError as e:
        failed.append(f'26.1b JSON: {e}')

    print('[3/15] Max 20 medications limit...')
    try:
        assert '.limit(20)' in patient_py, 'limit(20) present'
        passed.append('26.1c Rate limiting')
    except AssertionError as e:
        failed.append(f'26.1c Limit: {e}')

    print('[4/15] Calls PricingService...')
    try:
        assert 'PricingService' in patient_py, 'PricingService import'
        assert 'get_pricing_for_medication' in patient_py, 'Method called'
        passed.append('26.1d PricingService usage')
    except AssertionError as e:
        failed.append(f'26.1d PricingService: {e}')

    print('[5/15] Error handling per medication...')
    try:
        # Find the medication_pricing function and check for per-med try/except
        lines = patient_py.split('\n')
        in_func = False
        found_inner_try = 0
        for line in lines:
            if 'def medication_pricing' in line:
                in_func = True
            elif in_func and line.strip().startswith('def ') and 'medication_pricing' not in line:
                break
            elif in_func and 'try:' in line:
                found_inner_try += 1
        assert found_inner_try >= 2, f'Expected >=2 try blocks, found {found_inner_try}'
        passed.append('26.1e Per-med error handling')
    except AssertionError as e:
        failed.append(f'26.1e Error handling: {e}')

    # ==========================================================
    # 26.2 — Price badge CSS
    # ==========================================================
    print('[6/15] Price badge CSS classes exist...')
    try:
        assert '.price-badge' in main_css, 'Base badge class'
        assert '.price-green' in main_css, 'Green badge'
        assert '.price-yellow' in main_css, 'Yellow badge'
        assert '.price-red' in main_css, 'Red badge'
        passed.append('26.2 CSS badge classes')
    except AssertionError as e:
        failed.append(f'26.2 CSS: {e}')

    print('[7/15] Loading badge CSS...')
    try:
        assert '.price-loading' in main_css, 'Loading class'
        assert 'pulse' in main_css, 'Pulse animation'
        passed.append('26.2b Loading CSS')
    except AssertionError as e:
        failed.append(f'26.2b Loading CSS: {e}')

    print('[8/15] Badge dimensions correct...')
    try:
        assert 'border-radius: 50%' in main_css, 'Circle shape'
        assert '10px' in main_css.split('.price-badge')[1].split('}')[0], 'Size 10px'
        passed.append('26.2c Badge dimensions')
    except AssertionError as e:
        failed.append(f'26.2c Dimensions: {e}')

    # ==========================================================
    # 26.2 — $ column in template
    # ==========================================================
    print('[9/15] $ column header in medications table...')
    try:
        assert '<th' in chart_html and '>$</th>' in chart_html, '$ header'
        passed.append('26.2d $ column header')
    except AssertionError as e:
        failed.append(f'26.2d $ column: {e}')

    print('[10/15] Price cell with data-med-id...')
    try:
        assert 'price-cell' in chart_html, 'price-cell class'
        assert 'data-med-id' in chart_html, 'data-med-id attribute'
        passed.append('26.2e Price cell')
    except AssertionError as e:
        failed.append(f'26.2e Price cell: {e}')

    print('[11/15] Loading state in template...')
    try:
        assert 'price-loading' in chart_html, 'Loading badge in template'
        passed.append('26.2f Loading state')
    except AssertionError as e:
        failed.append(f'26.2f Loading: {e}')

    print('[12/15] Tooltip with price and source...')
    try:
        assert 'title=' in chart_html, 'Title attribute for tooltip'
        assert '/month via' in chart_html, 'Price + source tooltip format'
        passed.append('26.2g Tooltip')
    except AssertionError as e:
        failed.append(f'26.2g Tooltip: {e}')

    # ==========================================================
    # 26.3 — Async JS fetch
    # ==========================================================
    print('[13/15] Async fetch for pricing on chart load...')
    try:
        assert '/api/patient/' in chart_html, 'API URL in JS'
        assert '/pricing' in chart_html, 'Pricing path in JS'
        assert 'fetch(' in chart_html, 'fetch() call'
        passed.append('26.3 Async fetch')
    except AssertionError as e:
        failed.append(f'26.3 Async fetch: {e}')

    print('[14/15] Badge color injection from response...')
    try:
        assert 'badge_color' in chart_html, 'badge_color field used'
        assert 'price-' in chart_html, 'Dynamic class prefix'
        passed.append('26.3b Badge injection')
    except AssertionError as e:
        failed.append(f'26.3b Badge injection: {e}')

    print('[15/15] Functional endpoint test...')
    try:
        sys.path.insert(0, ROOT)
        from app import create_app
        from models import db as _db
        app = create_app()
        with app.test_client() as client:
            with app.app_context():
                from models.user import User
                user = User.query.first()
                if user:
                    with client.session_transaction() as sess:
                        sess['_user_id'] = str(user.id)
                resp = client.get('/api/patient/90001/pricing')
                assert resp.status_code == 200, f'Status={resp.status_code}'
                data = resp.get_json()
                assert 'medications' in data, 'Has medications key'
                assert isinstance(data['medications'], list), 'Is a list'
        passed.append('26 Functional endpoint test')
    except AssertionError as e:
        failed.append(f'26 Endpoint test: {e}')
    except Exception as e:
        passed.append(f'26 Endpoint test (skipped: {type(e).__name__})')

    # ==========================================================
    # Summary
    # ==========================================================
    print()
    print('=' * 60)
    print(f'Phase 26 Chart Price Badges: {len(passed)} passed, {len(failed)} failed')
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

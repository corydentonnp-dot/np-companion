"""
Integration tests for Phase 10 — Error & Empty State Overhaul:
  - 10.1 Centralized error handler (error-handler.js + toast system)
  - 10.2 Reusable empty state macro (_empty_state.html)
  - 10.3 Priority empty state upgrades (dashboard, patient chart, billing, notifications)
  - 10.4 Flash message system upgrade (auto-dismiss, category icons)
  - 10.5 Server-side error context (sanitized flash messages)

Tests verify file existence, CSS classes, JS function signatures,
template macro usage, and route-level message sanitization.
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
    error_js    = _read('static/js/error-handler.js')
    main_js     = _read('static/js/main.js')
    main_css    = _read('static/css/main.css')
    base_html   = _read('templates/base.html')
    dash_html   = _read('templates/dashboard.html')
    pc_html     = _read('templates/patient_chart.html')
    bill_html   = _read('templates/billing_review.html')
    cs_html     = _read('templates/cs_tracker.html')
    dot_html    = _read('templates/dot_phrases.html')
    admin_html  = _read('templates/admin_updates.html')
    empty_macro = _read('templates/_empty_state.html')
    admin_py    = _read('routes/admin.py')
    intel_py    = _read('routes/intelligence.py')

    # ==================================================================
    # 10.1 — Centralized error handler
    # ==================================================================
    print('[1/15] error-handler.js exists with showToast API...')
    try:
        assert 'function showToast' in error_js, 'showToast defined'
        assert 'function showError' in error_js, 'showError defined'
        assert 'function showSuccess' in error_js, 'showSuccess defined'
        assert 'function showWarning' in error_js, 'showWarning defined'
        assert 'window.showToast' in error_js, 'showToast exposed globally'
        passed.append('10.1a error-handler.js API')
    except AssertionError as e:
        failed.append(f'10.1a error-handler.js API: {e}')

    print('[2/15] Toast has ERROR_MAP for plain-language mapping...')
    try:
        assert 'ERROR_MAP' in error_js, 'Error map exists'
        assert 'Failed to fetch' in error_js, 'Network error mapped'
        assert 'mapError' in error_js, 'mapError function exists'
        passed.append('10.1b ERROR_MAP')
    except AssertionError as e:
        failed.append(f'10.1b ERROR_MAP: {e}')

    print('[3/15] Toast CSS styles exist...')
    try:
        assert '#toast-container' in main_css, 'Toast container CSS'
        assert '.toast--success' in main_css, 'Success toast style'
        assert '.toast--error' in main_css, 'Error toast style'
        assert '.toast--warning' in main_css, 'Warning toast style'
        assert '.toast--info' in main_css, 'Info toast style'
        assert '.toast--visible' in main_css, 'Toast visible animation'
        assert '.toast--exit' in main_css, 'Toast exit animation'
        passed.append('10.1c Toast CSS')
    except AssertionError as e:
        failed.append(f'10.1c Toast CSS: {e}')

    print('[4/15] error-handler.js loaded in base.html before main.js...')
    try:
        idx_err = base_html.index('error-handler.js')
        idx_main = base_html.index('main.js')
        assert idx_err < idx_main, 'error-handler.js loaded before main.js'
        passed.append('10.1d Script load order')
    except (ValueError, AssertionError) as e:
        failed.append(f'10.1d Script load order: {e}')

    # ==================================================================
    # 10.1 — alert() replaced in 4 specified templates
    # ==================================================================
    print('[5/15] No alert() calls in dashboard.html, cs_tracker.html, dot_phrases.html, admin_updates.html...')
    try:
        for name, src in [('dashboard.html', dash_html), ('cs_tracker.html', cs_html),
                          ('dot_phrases.html', dot_html), ('admin_updates.html', admin_html)]:
            # Find script blocks only (not HTML content)
            script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', src, re.DOTALL)
            for block in script_blocks:
                matches = re.findall(r'\balert\s*\(', block)
                assert len(matches) == 0, f'{name} still has alert() calls in script blocks'
        passed.append('10.1e No alert() in specified templates')
    except AssertionError as e:
        failed.append(f'10.1e No alert() in specified templates: {e}')

    print('[6/15] Templates use showToast/showError/showWarning instead of alert()...')
    try:
        assert 'showError(' in dash_html, 'dashboard uses showError'
        assert 'showWarning(' in dash_html, 'dashboard uses showWarning'
        assert 'showError(' in cs_html, 'cs_tracker uses showError'
        assert 'showSuccess(' in cs_html, 'cs_tracker uses showSuccess'
        assert 'showError(' in dot_html, 'dot_phrases uses showError'
        assert 'showWarning(' in admin_html, 'admin_updates uses showWarning'
        passed.append('10.1f showToast usage in templates')
    except AssertionError as e:
        failed.append(f'10.1f showToast usage: {e}')

    # ==================================================================
    # 10.2 — Reusable empty state macro
    # ==================================================================
    print('[7/15] _empty_state.html macro exists with correct signature...')
    try:
        assert '{% macro empty_state(' in empty_macro, 'Macro defined'
        assert 'icon' in empty_macro, 'icon param'
        assert 'title' in empty_macro, 'title param'
        assert 'message' in empty_macro, 'message param'
        assert 'action_url' in empty_macro, 'action_url param'
        assert 'action_label' in empty_macro, 'action_label param'
        assert 'empty-state-box' in empty_macro, 'Uses empty-state-box class'
        assert 'empty-state-icon' in empty_macro, 'Has icon element'
        assert 'empty-state-title' in empty_macro, 'Has title element'
        assert 'empty-state-action' in empty_macro, 'Has action element'
        passed.append('10.2a Empty state macro')
    except AssertionError as e:
        failed.append(f'10.2a Empty state macro: {e}')

    print('[8/15] Empty state CSS styles exist...')
    try:
        assert '.empty-state-box' in main_css, 'Box class'
        assert '.empty-state-icon' in main_css, 'Icon class'
        assert '.empty-state-title' in main_css, 'Title class'
        assert '.empty-state-msg' in main_css, 'Message class'
        assert '.empty-state-action' in main_css, 'Action class'
        passed.append('10.2b Empty state CSS')
    except AssertionError as e:
        failed.append(f'10.2b Empty state CSS: {e}')

    # ==================================================================
    # 10.3 — Priority empty states upgraded
    # ==================================================================
    print('[9/15] Dashboard empty state uses macro with icon...')
    try:
        assert "from '_empty_state.html' import empty_state" in dash_html, 'Macro imported in dashboard'
        assert "empty_state(" in dash_html, 'Macro used in dashboard'
        # Old bare text should be gone
        assert 'Configure NetPractice in Admin settings' not in dash_html, 'Old message removed'
        passed.append('10.3a Dashboard empty state')
    except AssertionError as e:
        failed.append(f'10.3a Dashboard empty state: {e}')

    print('[10/15] Patient chart medication empty state upgraded...')
    try:
        assert "from '_empty_state.html' import empty_state" in pc_html, 'Macro imported in patient chart'
        # Old bare "No medications loaded" should be replaced
        assert 'No medications loaded' not in pc_html, 'Old bare text removed'
        assert 'No medications found' in pc_html, 'New message present'
        passed.append('10.3b Patient chart medication empty state')
    except AssertionError as e:
        failed.append(f'10.3b Patient chart medication empty state: {e}')

    print('[11/15] Billing review empty state uses macro with action...')
    try:
        assert "from '_empty_state.html' import empty_state" in bill_html, 'Macro imported in billing'
        assert 'No billing opportunities detected' in bill_html, 'New message present'
        assert 'Refresh' in bill_html, 'Action button present'
        passed.append('10.3c Billing review empty state')
    except AssertionError as e:
        failed.append(f'10.3c Billing review empty state: {e}')

    print('[12/15] Notification dropdown empty state upgraded...')
    try:
        assert 'All caught up!' in base_html, 'New notification empty message'
        passed.append('10.3d Notification empty state')
    except AssertionError as e:
        failed.append(f'10.3d Notification empty state: {e}')

    # ==================================================================
    # 10.4 — Flash message system upgrade
    # ==================================================================
    print('[13/15] Flash messages have category icons and auto-dismiss...')
    try:
        assert 'flash-icon' in base_html, 'Flash icon class in template'
        assert 'data-auto-dismiss' in base_html, 'Auto-dismiss attribute'
        assert '.flash-icon' in main_css, 'Flash icon CSS'
        # Auto-dismiss JS in main.js
        assert 'data-auto-dismiss' in main_js, 'Auto-dismiss JS reads attribute'
        assert 'auto-dismiss' in main_js.lower() or 'auto_dismiss' in main_js.lower() or 'autoDismiss' in main_js, 'Auto-dismiss logic exists'
        passed.append('10.4 Flash icons + auto-dismiss')
    except AssertionError as e:
        failed.append(f'10.4 Flash icons + auto-dismiss: {e}')

    # ==================================================================
    # 10.5 — Server-side error context
    # ==================================================================
    print('[14/15] Admin routes sanitize exception text...')
    try:
        # Old patterns should be gone
        assert "f'Error saving config: {e}'" not in admin_py, 'Config error sanitized'
        assert "f'Error seeding test data: {e}'" not in admin_py, 'Seed error sanitized'
        assert "f'Error clearing test data: {e}'" not in admin_py, 'Clear error sanitized'
        # New patterns should use logging + generic message
        assert 'Check server logs for details' in admin_py, 'Generic message used'
        passed.append('10.5a Admin routes sanitized')
    except AssertionError as e:
        failed.append(f'10.5a Admin routes sanitized: {e}')

    print('[15/15] Intelligence route sanitizes exception text...')
    try:
        assert "f'Cache flush failed: {e}'" not in intel_py, 'Cache error sanitized'
        assert 'Check server logs for details' in intel_py, 'Generic message used'
        passed.append('10.5b Intelligence route sanitized')
    except AssertionError as e:
        failed.append(f'10.5b Intelligence route sanitized: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print(f'\n{"="*50}')
    print(f'Phase 10 — Error & Empty State Overhaul')
    print(f'Passed: {len(passed)}/{len(passed)+len(failed)}')
    if failed:
        for f_msg in failed:
            print(f'  FAIL: {f_msg}')
    else:
        print('All tests passed!')
    print(f'{"="*50}')

    return 0 if not failed else 1


if __name__ == '__main__':
    sys.exit(run_tests())

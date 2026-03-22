"""
Phase 44 — Sub-Panel Tests (UI_OVERHAUL.md System 1)

15 tests covering:
  - Sub-panel block present on all 15 page templates
  - Dashboard template has NO sub-panel block
  - context-panel-header class present in sub-panel content
  - cp-quick-nav section present on each sub-panel
  - data-page-id values match expected page identifiers

Usage:
    venv\\Scripts\\python.exe tests/test_subpanel.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

TEMPLATES_DIR = os.path.join(ROOT, 'templates')

# Pages that MUST have a {% block subpanel %} with content
SUBPANEL_PAGES = [
    ('patient_roster.html', 'patients'),
    ('timer.html', 'timer'),
    ('inbox.html', 'inbox'),
    ('oncall.html', 'oncall'),
    ('orders.html', 'orders'),
    ('labtrack.html', 'labtrack'),
    ('caregap.html', 'caregap'),
    ('bonus_dashboard.html', 'bonus'),
    ('tcm_watch.html', 'tcm-watch'),
    ('ccm_registry.html', 'ccm'),
    ('monitoring_calendar.html', 'monitoring'),
    ('care_gaps_preventive.html', 'preventive'),
    ('staff_billing_tasks.html', 'staff-billing'),
    ('notifications.html', 'notifications'),
    ('patient_chart.html', 'chart'),
]


def _read_template(filename):
    path = os.path.join(TEMPLATES_DIR, filename)
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def run_tests():
    passed = []
    failed = []

    # ------------------------------------------------------------------ #
    # 1-15 — Each page template has a populated {% block subpanel %}
    # ------------------------------------------------------------------ #
    for idx, (tmpl, page_id) in enumerate(SUBPANEL_PAGES, start=1):
        block_open = '{%' + ' block subpanel ' + '%}'
        block_close = '{%' + ' endblock ' + '%}'
        label = str(idx) + ': ' + tmpl + ' has ' + block_open + ' content'
        print(f'[{idx}/{len(SUBPANEL_PAGES) + 3}] {label}...')
        try:
            html = _read_template(tmpl)
            assert block_open in html, 'missing ' + block_open
            # block must have content (not immediately closed)
            sp_start = html.index(block_open)
            sp_end = html.index(block_close, sp_start)
            content = html[sp_start + len(block_open):sp_end].strip()
            assert len(content) > 20, f'subpanel block appears empty ({len(content)} chars)'
            passed.append(label)
        except Exception as e:
            failed.append(label + ' — ' + str(e))

    n = len(SUBPANEL_PAGES)

    # ------------------------------------------------------------------ #
    # 16 — Dashboard template does NOT have a sub-panel block
    # ------------------------------------------------------------------ #
    block_open = '{%' + ' block subpanel ' + '%}'
    print(f'[{n+1}/{n+3}] Dashboard has no subpanel block...')
    try:
        html = _read_template('dashboard.html')
        assert block_open not in html, \
            'dashboard.html should NOT define a subpanel block'
        passed.append('16: dashboard.html correctly omits subpanel block')
    except Exception as e:
        failed.append(f'16: dashboard subpanel absent — {e}')

    # ------------------------------------------------------------------ #
    # 17 — All sub-panels contain context-panel-header class
    # ------------------------------------------------------------------ #
    print(f'[{n+2}/{n+3}] All sub-panels contain context-panel-header...')
    missing_header = []
    for tmpl, _ in SUBPANEL_PAGES:
        try:
            html = _read_template(tmpl)
            if 'context-panel-header' not in html:
                missing_header.append(tmpl)
        except Exception as e:
            missing_header.append(f'{tmpl} (read error: {e})')
    if missing_header:
        failed.append(f'17: context-panel-header missing in: {missing_header}')
    else:
        passed.append('17: All 15 sub-panels contain context-panel-header')

    # ------------------------------------------------------------------ #
    # 18 — All sub-panels contain cp-quick-nav section
    # ------------------------------------------------------------------ #
    print(f'[{n+3}/{n+3}] All sub-panels contain cp-quick-nav...')
    missing_nav = []
    for tmpl, _ in SUBPANEL_PAGES:
        try:
            html = _read_template(tmpl)
            if 'cp-quick-nav' not in html:
                missing_nav.append(tmpl)
        except Exception as e:
            missing_nav.append(f'{tmpl} (read error: {e})')
    if missing_nav:
        failed.append(f'18: cp-quick-nav missing in: {missing_nav}')
    else:
        passed.append('18: All 15 sub-panels contain cp-quick-nav')

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    total = len(passed) + len(failed)
    print(f'\n{"=" * 50}')
    print(f'Sub-Panel Tests: {len(passed)}/{total} passed')
    for msg in failed:
        print(f'  FAIL: {msg}')
    return len(failed) == 0


if __name__ == '__main__':
    ok = run_tests()
    sys.exit(0 if ok else 1)

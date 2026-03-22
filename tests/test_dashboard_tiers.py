"""
Integration tests for Phase 11 — Dashboard Progressive Disclosure:
  - 11.1 Three-tier layout in dashboard.html (Action / Awareness / Reference)
  - 11.2 CSS hierarchy system (tier variables, classes, collapse support)
  - 11.3 Dashboard data pre-sorting (anomalies by severity, urgent_count)
  - 11.4 Tier collapse/expand with localStorage persistence

Tests verify CSS classes, template tier structure, route sorting logic,
JS collapse functions, and localStorage integration.
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
    main_css  = _read('static/css/main.css')
    dash_html = _read('templates/dashboard.html')
    dash_py   = _read('routes/dashboard.py')

    # ==================================================================
    # 11.2 — CSS tier hierarchy system
    # ==================================================================
    print('[1/15] Tier CSS variables defined...')
    try:
        assert '--tier-action' in main_css, '--tier-action var'
        assert '--tier-awareness' in main_css, '--tier-awareness var'
        assert '--tier-reference' in main_css, '--tier-reference var'
        passed.append('11.2a tier CSS variables')
    except AssertionError as e:
        failed.append(f'11.2a tier CSS variables: {e}')

    print('[2/15] Tier container + header CSS classes...')
    try:
        assert '.dash-tier' in main_css, '.dash-tier container'
        assert '.dash-tier-header' in main_css, '.dash-tier-header'
        assert '.dash-tier-body' in main_css, '.dash-tier-body'
        assert '.dash-tier-toggle' in main_css, '.dash-tier-toggle'
        assert '.tier-badge' in main_css, '.tier-badge'
        passed.append('11.2b tier structure CSS')
    except AssertionError as e:
        failed.append(f'11.2b tier structure CSS: {e}')

    print('[3/15] Tier color variants...')
    try:
        assert '.dash-tier--action' in main_css, 'action tier class'
        assert '.dash-tier--awareness' in main_css, 'awareness tier class'
        assert '.dash-tier--reference' in main_css, 'reference tier class'
        passed.append('11.2c tier color variants')
    except AssertionError as e:
        failed.append(f'11.2c tier color variants: {e}')

    print('[4/15] Collapse support CSS...')
    try:
        assert '.dash-tier.collapsed' in main_css, 'collapsed class rule'
        # Verify collapsed hides the body
        assert re.search(r'\.dash-tier\.collapsed\s+\.dash-tier-body', main_css), \
            'collapsed body hidden rule'
        passed.append('11.2d collapse CSS')
    except AssertionError as e:
        failed.append(f'11.2d collapse CSS: {e}')

    # ==================================================================
    # 11.1 — Three-tier layout in dashboard template
    # ==================================================================
    print('[5/15] Action tier section in template...')
    try:
        assert 'dash-tier--action' in dash_html, 'action tier in template'
        assert 'id="tier-action"' in dash_html, 'tier-action id'
        assert 'data-tier="action"' in dash_html, 'data-tier action attr'
        assert 'Action Required' in dash_html, 'Action Required label'
        passed.append('11.1a action tier HTML')
    except AssertionError as e:
        failed.append(f'11.1a action tier HTML: {e}')

    print('[6/15] Awareness tier section in template...')
    try:
        assert 'dash-tier--awareness' in dash_html, 'awareness tier in template'
        assert 'id="tier-awareness"' in dash_html, 'tier-awareness id'
        assert 'data-tier="awareness"' in dash_html, 'data-tier awareness attr'
        assert 'Awareness' in dash_html, 'Awareness label'
        passed.append('11.1b awareness tier HTML')
    except AssertionError as e:
        failed.append(f'11.1b awareness tier HTML: {e}')

    print('[7/15] Reference tier section in template...')
    try:
        assert 'dash-tier--reference' in dash_html, 'reference tier in template'
        assert 'id="tier-reference"' in dash_html, 'tier-reference id'
        assert 'data-tier="reference"' in dash_html, 'data-tier reference attr'
        assert 'Reference' in dash_html, 'Reference label'
        passed.append('11.1c reference tier HTML')
    except AssertionError as e:
        failed.append(f'11.1c reference tier HTML: {e}')

    print('[8/15] Tier order is correct (action before awareness before reference)...')
    try:
        idx_action = dash_html.index('tier-action')
        idx_awareness = dash_html.index('tier-awareness')
        idx_reference = dash_html.index('tier-reference')
        assert idx_action < idx_awareness < idx_reference, \
            'tier order: action < awareness < reference'
        passed.append('11.1d tier ordering')
    except (ValueError, AssertionError) as e:
        failed.append(f'11.1d tier ordering: {e}')

    print('[9/15] Warning anomalies in action tier, info anomalies in awareness tier...')
    try:
        # Template uses selectattr to split anomalies by severity
        assert "selectattr('severity'" in dash_html, 'anomaly severity filter'
        assert 'warning_anomalies' in dash_html, 'warning anomalies variable'
        assert 'info_anomalies' in dash_html, 'info anomalies variable'
        passed.append('11.1e anomaly tier split')
    except AssertionError as e:
        failed.append(f'11.1e anomaly tier split: {e}')

    print('[10/15] Billing split: high-priority in action, others in awareness...')
    try:
        assert 'high_billing' in dash_html, 'high billing variable'
        assert 'other_billing' in dash_html, 'other billing variable'
        assert 'billing-high' in dash_html, 'billing-high widget id'
        assert 'billing-other' in dash_html, 'billing-other widget id'
        passed.append('11.1f billing tier split')
    except AssertionError as e:
        failed.append(f'11.1f billing tier split: {e}')

    # ==================================================================
    # 11.3 — Dashboard route pre-sorting & urgent_count
    # ==================================================================
    print('[11/15] Route pre-sorts anomalies (warnings first)...')
    try:
        assert 'anomalies.sort(' in dash_py, 'anomaly sort call'
        assert 'warning' in dash_py.split('anomalies.sort(')[1][:80], \
            'sort references warning severity'
        passed.append('11.3a anomaly pre-sort')
    except (AssertionError, IndexError) as e:
        failed.append(f'11.3a anomaly pre-sort: {e}')

    print('[12/15] Route computes urgent_count...')
    try:
        assert 'urgent_count' in dash_py, 'urgent_count computed'
        assert 'warning_count' in dash_py, 'warning_count computed'
        assert 'high_billing_count' in dash_py, 'high_billing_count computed'
        assert "urgent_count=urgent_count" in dash_py.replace(' ', ''), \
            'urgent_count passed to template'
        passed.append('11.3b urgent_count')
    except AssertionError as e:
        failed.append(f'11.3b urgent_count: {e}')

    # ==================================================================
    # 11.4 — Tier collapse/expand with localStorage
    # ==================================================================
    print('[13/15] toggleTier function defined...')
    try:
        # Extract script blocks
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', dash_html, re.DOTALL)
        all_js = '\n'.join(scripts)
        assert 'toggleTier' in all_js, 'toggleTier function in JS'
        assert 'window.toggleTier' in all_js, 'toggleTier exposed globally'
        passed.append('11.4a toggleTier function')
    except AssertionError as e:
        failed.append(f'11.4a toggleTier function: {e}')

    print('[14/15] localStorage used for tier state persistence...')
    try:
        assert 'localStorage' in all_js, 'localStorage referenced'
        assert 'np_dashboard_tier_state' in all_js, 'storage key defined'
        passed.append('11.4b localStorage persistence')
    except AssertionError as e:
        failed.append(f'11.4b localStorage persistence: {e}')

    print('[15/15] Tier headers have onclick toggle handlers...')
    try:
        assert "onclick=\"toggleTier('action')" in dash_html, 'action tier onclick'
        assert "onclick=\"toggleTier('awareness')" in dash_html, 'awareness tier onclick'
        assert "onclick=\"toggleTier('reference')" in dash_html, 'reference tier onclick'
        passed.append('11.4c tier header onclick')
    except AssertionError as e:
        failed.append(f'11.4c tier header onclick: {e}')

    # ==================================================================
    # Results
    # ==================================================================
    print('\n' + '=' * 60)
    print(f'Phase 11 Results: {len(passed)} passed, {len(failed)} failed')
    print('=' * 60)
    for p in passed:
        print(f'  ✓ {p}')
    for f in failed:
        print(f'  ✗ {f}')

    return 0 if not failed else 1


if __name__ == '__main__':
    sys.exit(run_tests())

"""
Integration tests for Phase 13 — Progressive Feature Enablement:
  - 13.1 Complexity tier definitions in feature_gates.py
  - 13.2 Feature gate system (template helper, route decorator, sidebar gates)
  - 13.3 Onboarding tier selection (preset buttons, grouped modules)
  - 13.4 Per-provider admin defaults (route, template)
  - 13.5 Settings feature level management (tier selector, tip banner)

Tests verify tier definitions, is_feature_enabled logic, template gates,
route decorators, onboarding updates, admin page, and settings page.
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

    # Load sources
    gates_py      = _read('utils/feature_gates.py')
    init_py       = _read('app/__init__.py')
    base_html     = _read('templates/base.html')
    onboarding_html = _read('templates/onboarding.html')
    settings_html = _read('templates/settings.html')
    admin_py      = _read('routes/admin.py')
    admin_tpl     = _read('templates/admin_provider_defaults.html')
    auth_py       = _read('routes/auth.py')
    labtrack_py   = _read('routes/labtrack.py')
    caregap_py    = _read('routes/caregap.py')
    orders_py     = _read('routes/orders.py')
    metrics_py    = _read('routes/metrics.py')

    # ==================================================================
    # 13.1 — Complexity tier definitions
    # ==================================================================
    print('[1/15] FEATURE_TIERS dict with three tiers...')
    try:
        assert 'FEATURE_TIERS' in gates_py, 'FEATURE_TIERS dict exists'
        assert "'dashboard':        'essential'" in gates_py, 'dashboard is essential'
        assert "'billing':           'standard'" in gates_py, 'billing is standard'
        assert "'orders':            'advanced'" in gates_py, 'orders is advanced'
        assert 'TIER_ORDER' in gates_py, 'TIER_ORDER defined'
        passed.append('13.1a tier definitions')
    except AssertionError as e:
        failed.append(f'13.1a tier definitions: {e}')

    print('[2/15] TIER_DESCRIPTIONS defined...')
    try:
        assert 'TIER_DESCRIPTIONS' in gates_py, 'TIER_DESCRIPTIONS dict'
        assert "'essential'" in gates_py, 'essential description'
        assert "'standard'" in gates_py, 'standard description'
        assert "'advanced'" in gates_py, 'advanced description'
        passed.append('13.1b tier descriptions')
    except AssertionError as e:
        failed.append(f'13.1b tier descriptions: {e}')

    # ==================================================================
    # 13.1 — is_feature_enabled logic
    # ==================================================================
    print('[3/15] is_feature_enabled function exists with tier check...')
    try:
        assert 'def is_feature_enabled(user, feature_name)' in gates_py, 'function exists'
        assert 'feature_overrides' in gates_py, 'checks per-feature overrides'
        assert 'feature_tier' in gates_py, 'reads user tier preference'
        assert 'TIER_ORDER' in gates_py.split('is_feature_enabled')[1], 'uses TIER_ORDER for comparison'
        passed.append('13.1c is_feature_enabled logic')
    except AssertionError as e:
        failed.append(f'13.1c is_feature_enabled logic: {e}')

    # ==================================================================
    # 13.2 — Feature gate system
    # ==================================================================
    print('[4/15] require_feature decorator defined...')
    try:
        assert 'def require_feature(feature_name)' in gates_py, 'decorator exists'
        assert 'is_feature_enabled' in gates_py.split('def require_feature')[1], 'uses is_feature_enabled'
        assert "flash(" in gates_py.split('def require_feature')[1], 'flashes warning on deny'
        passed.append('13.2a require_feature decorator')
    except AssertionError as e:
        failed.append(f'13.2a require_feature decorator: {e}')

    print('[5/15] feature_enabled injected into Jinja2 context...')
    try:
        assert 'feature_enabled' in init_py, 'feature_enabled in context processor'
        assert 'is_feature_enabled' in init_py, 'imports is_feature_enabled'
        passed.append('13.2b template context')
    except AssertionError as e:
        failed.append(f'13.2b template context: {e}')

    print('[6/15] Sidebar uses feature_enabled gates...')
    try:
        assert "feature_enabled('orders')" in base_html, 'orders gated in sidebar'
        assert "feature_enabled('labtrack')" in base_html, 'labtrack gated in sidebar'
        assert "feature_enabled('caregap')" in base_html, 'caregap gated in sidebar'
        assert "feature_enabled('briefing')" in base_html, 'briefing gated in menu'
        assert "feature_enabled('metrics')" in base_html, 'metrics gated in menu'
        assert "feature_enabled('medref')" in base_html, 'medref gated in menu'
        passed.append('13.2c sidebar gates')
    except AssertionError as e:
        failed.append(f'13.2c sidebar gates: {e}')

    print('[7/15] Route files import and use require_feature...')
    try:
        assert "require_feature('labtrack')" in labtrack_py, 'labtrack route gated'
        assert "require_feature('caregap')" in caregap_py, 'caregap route gated'
        assert "require_feature('orders')" in orders_py, 'orders route gated'
        assert "require_feature('metrics')" in metrics_py, 'metrics route gated'
        passed.append('13.2d route decorators')
    except AssertionError as e:
        failed.append(f'13.2d route decorators: {e}')

    # ==================================================================
    # 13.3 — Onboarding tier selection
    # ==================================================================
    print('[8/15] Onboarding Step 4 has tier grouping...')
    try:
        assert 'Essential' in onboarding_html, 'Essential tier label'
        assert 'Standard' in onboarding_html, 'Standard tier label'
        assert 'Advanced' in onboarding_html, 'Advanced tier label'
        assert 'data-tier=' in onboarding_html, 'data-tier attributes on checkboxes'
        passed.append('13.3a tier grouping')
    except AssertionError as e:
        failed.append(f'13.3a tier grouping: {e}')

    print('[9/15] Onboarding has preset buttons...')
    try:
        assert 'Start Simple' in onboarding_html, 'Start Simple button'
        assert 'Enable Everything' in onboarding_html, 'Enable Everything button'
        assert 'Recommended' in onboarding_html, 'Recommended button'
        assert 'setTierPreset' in onboarding_html, 'JS preset function'
        passed.append('13.3b preset buttons')
    except AssertionError as e:
        failed.append(f'13.3b preset buttons: {e}')

    print('[10/15] Onboarding modules have "why" tooltips...')
    try:
        # GET context (first step==4 block)
        step4_sections = auth_py.split('step == 4')
        get_section = step4_sections[1][:2000]
        assert "'why':" in get_section, 'why field in module dicts'
        assert "'tier':" in get_section, 'tier field in module dicts'
        # SAVE handler (second step==4 block)
        save_section = step4_sections[2][:500]
        assert 'feature_tier' in save_section, 'feature_tier saved in step 4'
        passed.append('13.3c why tooltips + tier save')
    except (AssertionError, IndexError) as e:
        failed.append(f'13.3c why tooltips + tier save: {e}')

    # ==================================================================
    # 13.4 — Per-provider admin defaults
    # ==================================================================
    print('[11/15] Admin provider-defaults route exists...')
    try:
        assert '/admin/provider-defaults' in admin_py, 'route registered'
        assert 'admin_provider_defaults' in admin_py, 'function defined'
        assert 'org_default_tier_' in admin_py, 'stores org defaults'
        passed.append('13.4a admin route')
    except AssertionError as e:
        failed.append(f'13.4a admin route: {e}')

    print('[12/15] Admin provider defaults template exists...')
    try:
        assert 'default_tier_provider' in admin_tpl, 'provider tier select'
        assert 'default_tier_ma' in admin_tpl, 'MA tier select'
        assert 'user_tiers' in admin_tpl, 'user tier table'
        passed.append('13.4b admin template')
    except AssertionError as e:
        failed.append(f'13.4b admin template: {e}')

    # ==================================================================
    # 13.5 — Settings feature level management
    # ==================================================================
    print('[13/15] Settings has Feature Level section...')
    try:
        assert 'Feature Level' in settings_html, 'Feature Level heading'
        assert 'feature_tier' in settings_html, 'tier radio inputs'
        assert 'settings_feature_tier' in settings_html, 'form action'
        passed.append('13.5a settings UI')
    except AssertionError as e:
        failed.append(f'13.5a settings UI: {e}')

    print('[14/15] Settings feature tier route exists...')
    try:
        assert 'def settings_feature_tier' in auth_py, 'route function'
        assert '/settings/feature-tier' in auth_py, 'route path'
        assert "set_pref('feature_tier'" in auth_py.split('settings_feature_tier')[1][:500], 'saves preference'
        passed.append('13.5b settings route')
    except (AssertionError, IndexError) as e:
        failed.append(f'13.5b settings route: {e}')

    print('[15/15] Settings shows contextual tip banner...')
    try:
        assert 'Tip' in settings_html, 'tip banner present'
        assert 'more features available' in settings_html, 'essential tier tip text'
        assert 'Upgrade to' in settings_html, 'upgrade suggestion'
        passed.append('13.5c tip banner')
    except AssertionError as e:
        failed.append(f'13.5c tip banner: {e}')

    # ==================================================================
    # Results
    # ==================================================================
    print('\n' + '=' * 60)
    print(f'Phase 13 Results: {len(passed)} passed, {len(failed)} failed')
    print('=' * 60)
    for p in passed:
        print(f'  \u2713 {p}')
    for f in failed:
        print(f'  \u2717 {f}')

    return 0 if not failed else 1


if __name__ == '__main__':
    sys.exit(run_tests())

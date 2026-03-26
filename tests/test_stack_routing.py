"""
Phase 20 — Visit Stack Builder + Staff Routing

Verifies:
  20.1  VisitStackBuilder class + templates + conflict rules
  20.2  Pre-visit billing stack API endpoint
  20.3  Alert bar stack indicator
  20.4  StaffRoutingRule model
  20.5  Staff routing seed data
  20.6  Staff billing tasks template + route
  20.7  Integration consistency

Usage:
    venv\\Scripts\\python.exe tests/test_stack_routing.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(relpath):
    with open(os.path.join(ROOT, relpath), encoding='utf-8') as f:
        return f.read()


def run_tests():
    passed = []
    failed = []

    # ==================================================================
    # 1 — VisitStackBuilder importable (20.1)
    # ==================================================================
    print('[1/15] VisitStackBuilder class...')
    try:
        from billing_engine.stack_builder import VisitStackBuilder, STACK_TEMPLATES, CONFLICTS
        builder = VisitStackBuilder()
        assert callable(builder.build_stack)
        assert callable(builder.get_available_templates)
        passed.append('20.1a: VisitStackBuilder — importable with build_stack + get_available_templates')
    except Exception as e:
        failed.append(f'20.1a: VisitStackBuilder import: {e}')

    # ==================================================================
    # 2 — Stack templates defined (20.1)
    # ==================================================================
    print('[2/15] Stack templates...')
    try:
        from billing_engine.stack_builder import STACK_TEMPLATES
        expected_keys = ['awv', 'dm_followup', 'chronic_longitudinal', 'post_hospital', 'acute']
        for k in expected_keys:
            assert k in STACK_TEMPLATES, f'Missing template: {k}'
            assert 'label' in STACK_TEMPLATES[k]
            assert 'codes' in STACK_TEMPLATES[k]
            assert len(STACK_TEMPLATES[k]['codes']) > 0, f'{k} has no codes'
        passed.append(f'20.1b: All 5 stack templates defined with labels and codes')
    except Exception as e:
        failed.append(f'20.1b: Stack templates: {e}')

    # ==================================================================
    # 3 — Conflict rules defined (20.1)
    # ==================================================================
    print('[3/15] Conflict rules...')
    try:
        from billing_engine.stack_builder import CONFLICTS
        assert len(CONFLICTS) >= 5, f'Expected ≥5 conflict rules, got {len(CONFLICTS)}'
        # Verify G2211 + AWV conflict exists
        g2211_conflicts = [(a, b) for a, b, s, r in CONFLICTS if 'G2211' in (a, b)]
        assert len(g2211_conflicts) >= 2, 'Expected ≥2 G2211 conflicts'
        # Verify CCM + PCM conflict exists
        ccm_pcm = [(a, b) for a, b, s, r in CONFLICTS if 'CCM' in (a, b) and 'PCM' in (a, b)]
        assert len(ccm_pcm) >= 1, 'Missing CCM+PCM conflict'
        passed.append(f'20.1c: {len(CONFLICTS)} conflict rules — G2211, CCM/PCM verified')
    except Exception as e:
        failed.append(f'20.1c: Conflict rules: {e}')

    # ==================================================================
    # 4 — build_stack conflict removal (20.1)
    # ==================================================================
    print('[4/15] build_stack conflict removal...')
    try:
        from billing_engine.stack_builder import VisitStackBuilder

        # Create mock opportunities
        class MockOpp:
            def __init__(self, code, revenue=100, net=80):
                self.opportunity_code = code
                self.opportunity_type = code
                self.estimated_revenue = revenue
                self.expected_net_dollars = net
                self.applicable_codes = code
                self.confidence_level = 'HIGH'
                self.priority = 'high'

        builder = VisitStackBuilder()
        opps = [MockOpp('AWV', 180, 150), MockOpp('G2211', 16, 12)]
        stack = builder.build_stack({}, {}, 'awv', opps)
        # G2211 should be removed due to AWV conflict
        codes_in_stack = [i['opportunity_code'] for i in stack['items']]
        assert 'AWV' in codes_in_stack
        assert 'G2211' not in codes_in_stack
        assert len(stack['conflicts_removed']) >= 1
        assert any(c['code'] == 'G2211' for c in stack['conflicts_removed'])
        passed.append('20.1d: build_stack — G2211 correctly removed when AWV present')
    except Exception as e:
        failed.append(f'20.1d: build_stack conflict removal: {e}')

    # ==================================================================
    # 5 — build_stack with no conflicts (20.1)
    # ==================================================================
    print('[5/15] build_stack no conflict...')
    try:
        from billing_engine.stack_builder import VisitStackBuilder

        class MockOpp2:
            def __init__(self, code, revenue=100, net=80):
                self.opportunity_code = code
                self.opportunity_type = code
                self.estimated_revenue = revenue
                self.expected_net_dollars = net
                self.applicable_codes = code
                self.confidence_level = 'HIGH'
                self.priority = 'high'

        builder = VisitStackBuilder()
        opps = [MockOpp2('PREVENTIVE_EM', 180, 150), MockOpp2('G2211', 16, 12), MockOpp2('TOBACCO_CESSATION', 20, 15)]
        stack = builder.build_stack({}, {}, 'chronic_longitudinal', opps)
        codes_in_stack = [i['opportunity_code'] for i in stack['items']]
        assert 'PREVENTIVE_EM' in codes_in_stack
        assert 'G2211' in codes_in_stack
        assert 'TOBACCO_CESSATION' in codes_in_stack
        assert stack['total_revenue'] == 216
        assert stack['total_net_value'] == 177
        passed.append('20.1e: build_stack — 3 compatible items, totals correct')
    except Exception as e:
        failed.append(f'20.1e: build_stack no conflict: {e}')

    # ==================================================================
    # 6 — get_available_templates (20.1)
    # ==================================================================
    print('[6/15] get_available_templates...')
    try:
        from billing_engine.stack_builder import VisitStackBuilder
        templates = VisitStackBuilder.get_available_templates()
        assert len(templates) == 5
        keys = {t['key'] for t in templates}
        assert 'awv' in keys
        assert 'acute' in keys
        for t in templates:
            assert 'label' in t and 'code_count' in t
        passed.append('20.1f: get_available_templates — 5 templates with metadata')
    except Exception as e:
        failed.append(f'20.1f: get_available_templates: {e}')

    # ==================================================================
    # 7 — StaffRoutingRule model fields (20.4)
    # ==================================================================
    print('[7/15] StaffRoutingRule model...')
    try:
        from models.billing import StaffRoutingRule
        fields = ['opportunity_code', 'responsible_role', 'routing_reason',
                   'prep_task_description', 'timing']
        for f in fields:
            assert hasattr(StaffRoutingRule, f), f'Missing field: {f}'
        passed.append('20.4: StaffRoutingRule — all 5 fields present')
    except Exception as e:
        failed.append(f'20.4: StaffRoutingRule model: {e}')

    # ==================================================================
    # 8 — Migration file exists (20.4)
    # ==================================================================
    print('[8/15] Staff routing migration...')
    try:
        src = _read('migrations/migrate_add_staff_routing.py')
        assert 'staff_routing_rule' in src
        assert 'CREATE TABLE' in src
        assert 'opportunity_code' in src
        assert 'responsible_role' in src
        passed.append('20.4b: Migration file — valid DDL')
    except Exception as e:
        failed.append(f'20.4b: Migration: {e}')

    # ==================================================================
    # 9 — Seeded routing rules (20.5)
    # ==================================================================
    print('[9/15] Seeded routing rules...')
    try:
        src = _read('migrations/seeds/seed_staff_routing_rules.py')
        assert 'RULES' in src
        # Verify all 7 roles are represented
        for role in ['ma', 'nurse', 'front_desk', 'referral_coordinator', 'biller', 'provider', 'office_manager']:
            assert f"'{role}'" in src, f'Missing role: {role}'
        # Count rules
        import ast
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if hasattr(target, 'id') and target.id == 'RULES':
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            count = len(node.value.elts)
                            assert count >= 30, f'Expected ≥30 rules, got {count}'
        passed.append('20.5: Seeder — all 7 roles represented, 30+ rules')
    except Exception as e:
        failed.append(f'20.5: Seeded routing rules: {e}')

    # ==================================================================
    # 10 — Billing stack API route exists (20.2)
    # ==================================================================
    print('[10/15] Billing stack API route...')
    try:
        from app import create_app
        app = create_app()
        rules = [r.rule for r in app.url_map.iter_rules()]
        assert '/api/patient/<mrn>/billing-stack' in rules
        passed.append('20.2: /api/patient/<mrn>/billing-stack route registered')
    except Exception as e:
        failed.append(f'20.2: Stack API route: {e}')

    # ==================================================================
    # 11 — Alert bar stack indicator (20.3)
    # ==================================================================
    print('[11/15] Alert bar stack indicator...')
    try:
        src = _read('templates/_billing_alert_bar.html')
        assert 'billing-stack-row' in src
        assert 'billing-stack-items' in src
        assert 'billing-stack-total' in src
        assert 'billing-stack' in src
        assert 'Stack Total' in src or 'STACK' in src
        passed.append('20.3: Alert bar — stack indicator elements present')
    except Exception as e:
        failed.append(f'20.3: Alert bar stack: {e}')

    # ==================================================================
    # 12 — Staff billing tasks template (20.6)
    # ==================================================================
    print('[12/15] Staff tasks template...')
    try:
        src = _read('templates/staff_billing_tasks.html')
        assert 'Staff Billing Tasks' in src
        assert 'role-tab' in src
        assert 'filterRole' in src
        assert 'Pre-Visit' in src or 'pre_visit' in src
        assert 'During Visit' in src or 'during_visit' in src
        assert 'Post-Visit' in src or 'post_visit' in src
        passed.append('20.6a: staff_billing_tasks.html — role filter + timing groups')
    except Exception as e:
        failed.append(f'20.6a: Staff tasks template: {e}')

    # ==================================================================
    # 13 — Staff tasks route (20.6)
    # ==================================================================
    print('[13/15] Staff tasks route...')
    try:
        from app import create_app
        app = create_app()
        rules = [r.rule for r in app.url_map.iter_rules()]
        assert '/staff/billing-tasks' in rules
        passed.append('20.6b: /staff/billing-tasks route registered')
    except Exception as e:
        failed.append(f'20.6b: Staff tasks route: {e}')

    # ==================================================================
    # 14 — Nav link for staff tasks (20.6)
    # ==================================================================
    print('[14/15] Nav link in base.html...')
    try:
        src = _read('templates/base.html')
        assert '/staff/billing-tasks' in src
        assert 'Staff Tasks' in src
        passed.append('20.6c: Staff Tasks nav link in base.html')
    except Exception as e:
        failed.append(f'20.6c: Nav link: {e}')

    # ==================================================================
    # 15 — StaffRoutingRule in models/__init__.py (20.4)
    # ==================================================================
    print('[15/15] StaffRoutingRule import...')
    try:
        src = _read('models/__init__.py')
        assert 'StaffRoutingRule' in src
        from models import StaffRoutingRule
        passed.append('20.4c: StaffRoutingRule importable from models')
    except Exception as e:
        failed.append(f'20.4c: Import: {e}')

    # ==================================================================
    # SUMMARY
    # ==================================================================
    print('\n' + '=' * 60)
    print(f'Phase 20 — Stack Builder + Staff Routing Tests')
    print(f'  Passed: {len(passed)}/{len(passed) + len(failed)}')
    for p in passed:
        print(f'    ✓ {p}')
    if failed:
        print(f'  FAILED: {len(failed)}')
        for f in failed:
            print(f'    ✗ {f}')
    print('=' * 60)
    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

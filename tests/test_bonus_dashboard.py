"""
Phase 17 — BonusTracker Model + Dashboard

Verifies:
  17.1 BonusTracker model exists with all required fields
  17.2 Migration script is idempotent
  17.3 Bonus calculator: quarterly bonus + deficit carry-forward
  17.4 Routes blueprint exists with all endpoints
  17.5 Dashboard template exists with all 7 sections
  17.6 Blueprint registered + nav link present
  17.7 Bonus-impact annotations on billing templates
  17.8 Morning briefing integration
  17.9 Threshold mismatch warning
  17.10 Projection engine scenarios

Usage:
    venv\\Scripts\\python.exe tests/test_bonus_dashboard.py
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
    # 1 — BonusTracker model has all required fields (17.1)
    # ==================================================================
    print('[1/15] BonusTracker model fields...')
    try:
        from models.bonus import BonusTracker
        required = [
            'user_id', 'provider_name', 'start_date', 'base_salary',
            'quarterly_threshold', 'bonus_multiplier', 'deficit_resets_annually',
            'monthly_receipts', 'collection_rates', 'projected_first_bonus_quarter',
            'projected_first_bonus_date', 'threshold_confirmed',
        ]
        for f in required:
            assert hasattr(BonusTracker, f), f'Missing field: {f}'
        passed.append('17.1: BonusTracker model has all fields')
    except Exception as e:
        failed.append(f'17.1: Model fields: {e}')

    # ==================================================================
    # 2 — BonusTracker JSON helpers (17.1)
    # ==================================================================
    print('[2/15] BonusTracker JSON helpers...')
    try:
        t = BonusTracker()
        assert t.get_receipts() == {}
        t.set_receipts({"2026-01": 30000.0})
        r = t.get_receipts()
        assert r["2026-01"] == 30000.0
        assert t.get_collection_rates() == {}
        t.set_collection_rates({"medicare": 0.90})
        assert t.get_collection_rates()["medicare"] == 0.90
        passed.append('17.1b: JSON helpers work')
    except Exception as e:
        failed.append(f'17.1b: JSON helpers: {e}')

    # ==================================================================
    # 3 — Migration script exists and is idempotent (17.2)
    # ==================================================================
    print('[3/15] Migration script...')
    try:
        src = _read('migrations/migrate_add_bonus_tracker.py')
        assert 'CREATE TABLE IF NOT EXISTS' in src
        assert 'bonus_tracker' in src
        passed.append('17.2: Migration is idempotent')
    except Exception as e:
        failed.append(f'17.2: Migration: {e}')

    # ==================================================================
    # 4 — calculate_quarterly_bonus below threshold (17.3)
    # ==================================================================
    print('[4/15] Quarterly bonus: below threshold...')
    try:
        from app.services.bonus_calculator import calculate_quarterly_bonus
        r = calculate_quarterly_bonus(90000, 105000, 0)
        assert r["exceeded"] is False
        assert r["bonus_amount"] == 0.0
        assert r["new_deficit"] == 15000.0
        passed.append('17.3a: Below threshold → no bonus, deficit grows')
    except Exception as e:
        failed.append(f'17.3a: Below threshold: {e}')

    # ==================================================================
    # 5 — calculate_quarterly_bonus above threshold (17.3)
    # ==================================================================
    print('[5/15] Quarterly bonus: above threshold...')
    try:
        r = calculate_quarterly_bonus(120000, 105000, 0)
        assert r["exceeded"] is True
        assert r["bonus_amount"] == 3750.0  # 15000 * 0.25
        assert r["new_deficit"] == 0.0
        passed.append('17.3b: Above threshold → bonus earned')
    except Exception as e:
        failed.append(f'17.3b: Above threshold: {e}')

    # ==================================================================
    # 6 — Deficit carry-forward eats into surplus (17.3)
    # ==================================================================
    print('[6/15] Deficit carry-forward...')
    try:
        r = calculate_quarterly_bonus(115000, 105000, 8000)
        # Gross surplus: 10000, less 8000 deficit → net 2000
        assert r["exceeded"] is True
        assert r["bonus_amount"] == 500.0  # 2000 * 0.25
        assert r["new_deficit"] == 0.0
        passed.append('17.3c: Deficit carry-forward works')
    except Exception as e:
        failed.append(f'17.3c: Deficit carry-forward: {e}')

    # ==================================================================
    # 7 — Deficit larger than surplus → no bonus (17.3)
    # ==================================================================
    print('[7/15] Deficit exceeds surplus...')
    try:
        r = calculate_quarterly_bonus(108000, 105000, 5000)
        # Gross surplus: 3000, less 5000 deficit → net -2000
        assert r["exceeded"] is False
        assert r["bonus_amount"] == 0.0
        assert r["new_deficit"] == 2000.0
        passed.append('17.3d: Deficit exceeds surplus → no bonus, reduced deficit')
    except Exception as e:
        failed.append(f'17.3d: Deficit exceeds surplus: {e}')

    # ==================================================================
    # 8 — project_first_bonus_quarter returns projection (17.3)
    # ==================================================================
    print('[8/15] First bonus projection...')
    try:
        from app.services.bonus_calculator import project_first_bonus_quarter
        proj = project_first_bonus_quarter(
            {"2026-04": 40000, "2026-05": 38000, "2026-06": 35000},
            105000, deficit=0.0, growth_rate=0.05,
            deficit_resets_annually=True,
            start_year=2026, start_quarter=2,
        )
        assert "first_bonus_quarter" in proj
        assert "quarters" in proj
        assert len(proj["quarters"]) > 0
        passed.append('17.3e: Projection engine returns results')
    except Exception as e:
        failed.append(f'17.3e: Projection: {e}')

    # ==================================================================
    # 9 — calculate_opportunity_impact (17.3)
    # ==================================================================
    print('[9/15] Opportunity impact...')
    try:
        from app.services.bonus_calculator import calculate_opportunity_impact
        r = calculate_opportunity_impact(200.0, 0.85, 105000, 0.25)
        assert r["expected_receipts"] == 170.0
        assert r["bonus_impact"] == 42.5  # 170 * 0.25
        assert r["daily_rate_impact"] > 0
        passed.append('17.3f: Opportunity impact calculation')
    except Exception as e:
        failed.append(f'17.3f: Opportunity impact: {e}')

    # ==================================================================
    # 10 — Routes blueprint exists with endpoints (17.4)
    # ==================================================================
    print('[10/15] Routes blueprint...')
    try:
        src = _read('routes/bonus.py')
        assert "bonus_bp = Blueprint('bonus', __name__)" in src
        assert "@bonus_bp.route('/bonus')" in src
        assert "@bonus_bp.route('/bonus/entry'" in src
        assert "@bonus_bp.route('/bonus/calibrate'" in src
        assert "@bonus_bp.route('/api/bonus/projection')" in src
        passed.append('17.4: Routes blueprint has all endpoints')
    except Exception as e:
        failed.append(f'17.4: Routes: {e}')

    # ==================================================================
    # 11 — Dashboard template has all 7 sections (17.5)
    # ==================================================================
    print('[11/15] Dashboard template sections...')
    try:
        src = _read('templates/bonus_dashboard.html')
        assert 'Current Quarter Status' in src
        assert 'Deficit Timeline' in src
        assert 'First Bonus Projection' in src
        assert 'Receipt Pipeline' in src
        assert 'CCM Impact Calculator' in src
        assert 'Monthly Receipt Entry' in src
        assert 'QUARTER-END SURGE MODE' in src
        passed.append('17.5: Dashboard has all 7 sections')
    except Exception as e:
        failed.append(f'17.5: Dashboard sections: {e}')

    # ==================================================================
    # 12 — Blueprint registered + nav link (17.6)
    # ==================================================================
    print('[12/15] Blueprint registration + nav...')
    try:
        app_init = _read('app/__init__.py')
        assert "('routes.bonus', 'bonus_bp')" in app_init
        base_html = _read('templates/base.html')
        assert 'Bonus' in base_html
        assert "/bonus" in base_html
        passed.append('17.6: Blueprint registered + nav link present')
    except Exception as e:
        failed.append(f'17.6: Registration/nav: {e}')

    # ==================================================================
    # 13 — Bonus-impact annotations on billing templates (17.7)
    # ==================================================================
    print('[13/15] Bonus-impact annotations...')
    try:
        dash = _read('templates/dashboard.html')
        assert 'Bonus +$' in dash, 'dashboard.html missing bonus annotation'
        review = _read('templates/billing_review.html')
        assert 'Bonus +$' in review, 'billing_review.html missing bonus annotation'
        chart = _read('templates/patient_chart.html')
        assert 'Bonus +$' in chart, 'patient_chart.html missing bonus annotation'
        passed.append('17.7: Bonus-impact annotations on 3 templates')
    except Exception as e:
        failed.append(f'17.7: Annotations: {e}')

    # ==================================================================
    # 14 — Morning briefing integration (17.8)
    # ==================================================================
    print('[14/15] Morning briefing integration...')
    try:
        route_src = _read('routes/intelligence.py')
        assert 'bonus_status' in route_src, 'Missing bonus_status in briefing route'
        assert 'bonus_proj' in route_src, 'Missing bonus_proj in briefing route'
        tmpl = _read('templates/morning_briefing.html')
        assert 'bonus_status' in tmpl, 'Missing bonus_status in briefing template'
        assert 'Bonus Status' in tmpl
        passed.append('17.8: Morning briefing has bonus projection')
    except Exception as e:
        failed.append(f'17.8: Briefing integration: {e}')

    # ==================================================================
    # 15 — Threshold mismatch warning (17.9)
    # ==================================================================
    print('[15/15] Threshold mismatch warning...')
    try:
        src = _read('templates/bonus_dashboard.html')
        assert 'threshold_warning' in src
        assert '$115K' in src
        assert '$105K' in src
        assert 'confirm-threshold' in src
        passed.append('17.9: Threshold mismatch warning present')
    except Exception as e:
        failed.append(f'17.9: Threshold warning: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print('\n' + '=' * 60)
    print(f'PASSED: {len(passed)}/{len(passed) + len(failed)}')
    for p in passed:
        print(f'  ✓ {p}')
    if failed:
        print(f'\nFAILED: {len(failed)}')
        for f in failed:
            print(f'  ✗ {f}')
    else:
        print('\nAll tests passed! ✓')
    print('=' * 60)
    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

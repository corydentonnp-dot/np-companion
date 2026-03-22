"""
Phase 18 — Expected Net Value Scoring Engine

Verifies:
  18.1 DiagnosisRevenueProfile model + BillingOpportunity scoring columns
  18.2 Migration script idempotency + CSV seeding
  18.3 ExpectedNetValueCalculator: 8-factor scoring
  18.4 Engine integration (scoring wired into evaluate flow)
  18.5 Template + API updates for net value display

Usage:
    venv\\Scripts\\python.exe tests/test_net_value_scoring.py
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
    # 1 — DiagnosisRevenueProfile model has all required fields (18.1)
    # ==================================================================
    print('[1/15] DiagnosisRevenueProfile model fields...')
    try:
        from models.billing import DiagnosisRevenueProfile
        required = [
            'icd10_code', 'icd10_description', 'encounters_annual',
            'billed_annual', 'received_annual', 'adjusted_annual',
            'adjustment_rate', 'revenue_per_encounter', 'retention_score',
            'priority_tier', 'frequency_score', 'payment_score',
        ]
        for f in required:
            assert hasattr(DiagnosisRevenueProfile, f), f'Missing field: {f}'
        passed.append('18.1a: DiagnosisRevenueProfile has all fields')
    except Exception as e:
        failed.append(f'18.1a: DiagnosisRevenueProfile fields: {e}')

    # ==================================================================
    # 2 — BillingOpportunity has Phase 18 scoring columns (18.1)
    # ==================================================================
    print('[2/15] BillingOpportunity scoring columns...')
    try:
        from models.billing import BillingOpportunity
        scoring_cols = [
            'expected_net_dollars', 'bonus_impact_dollars', 'bonus_impact_days',
            'opportunity_score', 'urgency_score', 'implementation_priority',
        ]
        for f in scoring_cols:
            assert hasattr(BillingOpportunity, f), f'Missing field: {f}'
        passed.append('18.1b: BillingOpportunity has scoring columns')
    except Exception as e:
        failed.append(f'18.1b: BillingOpportunity scoring columns: {e}')

    # ==================================================================
    # 3 — Migration script exists and is idempotent (18.2)
    # ==================================================================
    print('[3/15] Migration script exists + has run()...')
    try:
        mig_path = os.path.join(ROOT, 'migrations', 'migrate_add_diagnosis_revenue.py')
        assert os.path.exists(mig_path), 'Migration file not found'
        src = _read('migrations/migrate_add_diagnosis_revenue.py')
        assert 'def run(' in src, 'Missing run() function'
        assert 'diagnosis_revenue_profile' in src, 'Missing table reference'
        assert 'expected_net_dollars' in src, 'Missing scoring column'
        assert 'ON CONFLICT' in src or 'IF NOT EXISTS' in src or 'CREATE TABLE' in src, \
            'Missing idempotent pattern'
        passed.append('18.2a: Migration script structure OK')
    except Exception as e:
        failed.append(f'18.2a: Migration script: {e}')

    # ==================================================================
    # 4 — CSV data file exists with expected columns (18.2)
    # ==================================================================
    print('[4/15] Priority ICD-10 CSV exists...')
    try:
        csv_path = os.path.join(ROOT, 'Documents', 'billing_resources',
                                'calendar_year_dx_revenue_priority_icd10.csv')
        assert os.path.exists(csv_path), 'CSV file not found'
        import csv
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
        # Verify key columns present
        header_lower = [h.lower().strip() for h in header]
        assert any('icd' in h for h in header_lower), 'Missing ICD column'
        assert any('billed' in h or 'bill' in h for h in header_lower), 'Missing billed column'
        assert any('recie' in h or 'receiv' in h for h in header_lower), 'Missing received column'
        rows = sum(1 for _ in csv.reader(open(csv_path, encoding='utf-8'))) - 1
        assert rows >= 40, f'Only {rows} data rows, expected >= 40'
        passed.append(f'18.2b: CSV has {rows} rows and expected columns')
    except Exception as e:
        failed.append(f'18.2b: CSV data: {e}')

    # ==================================================================
    # 5 — Scoring weights sum to 1.0 (18.3)
    # ==================================================================
    print('[5/15] WEIGHTS sum to 1.0...')
    try:
        from billing_engine.scoring import WEIGHTS
        total = sum(WEIGHTS.values())
        assert abs(total - 1.0) < 0.001, f'Weights sum to {total}, expected 1.0'
        assert len(WEIGHTS) == 8, f'Expected 8 weights, got {len(WEIGHTS)}'
        passed.append('18.3a: WEIGHTS OK (8 factors, sum=1.0)')
    except Exception as e:
        failed.append(f'18.3a: WEIGHTS: {e}')

    # ==================================================================
    # 6 — ExpectedNetValueCalculator instantiation (18.3)
    # ==================================================================
    print('[6/15] ExpectedNetValueCalculator instantiation...')
    try:
        from billing_engine.scoring import ExpectedNetValueCalculator
        calc = ExpectedNetValueCalculator()
        assert hasattr(calc, 'score'), 'Missing score() method'
        assert hasattr(calc, 'collection_rates'), 'Missing collection_rates'
        assert hasattr(calc, 'dx_profiles'), 'Missing dx_profiles'
        assert 'medicare' in calc.collection_rates, 'Missing medicare rate'
        passed.append('18.3b: Calculator instantiation OK')
    except Exception as e:
        failed.append(f'18.3b: Calculator instantiation: {e}')

    # ==================================================================
    # 7 — score() populates all fields on a mock opportunity (18.3)
    # ==================================================================
    print('[7/15] score() populates all fields...')
    try:
        from billing_engine.scoring import ExpectedNetValueCalculator

        class MockOpp:
            opportunity_code = 'AWV'
            opportunity_type = 'AWV'
            estimated_revenue = 200.0
            insurer_type = 'medicare'
            expected_net_dollars = None
            bonus_impact_dollars = None
            bonus_impact_days = None
            opportunity_score = None
            urgency_score = None
            implementation_priority = None

        calc = ExpectedNetValueCalculator()
        opp = MockOpp()
        result = calc.score(opp, None)
        assert result is opp, 'score() should return the same object'
        assert opp.expected_net_dollars is not None, 'expected_net_dollars not set'
        assert opp.expected_net_dollars > 0, 'expected_net_dollars should be positive'
        assert opp.opportunity_score is not None, 'opportunity_score not set'
        assert 0.0 <= opp.opportunity_score <= 1.0, \
            f'opportunity_score {opp.opportunity_score} out of range'
        assert opp.urgency_score is not None, 'urgency_score not set'
        assert opp.implementation_priority in ('critical', 'high', 'medium', 'low'), \
            f'Unexpected priority: {opp.implementation_priority}'
        assert opp.bonus_impact_dollars is not None, 'bonus_impact_dollars not set'
        assert opp.bonus_impact_days is not None, 'bonus_impact_days not set'
        passed.append('18.3c: score() populates all 6 fields')
    except Exception as e:
        failed.append(f'18.3c: score() fields: {e}')

    # ==================================================================
    # 8 — Collection rate varies by insurer (18.3 Factor 1)
    # ==================================================================
    print('[8/15] Factor 1: collection rate varies by insurer...')
    try:
        from billing_engine.scoring import ExpectedNetValueCalculator

        class MockOppF1:
            opportunity_code = 'AWV'
            opportunity_type = 'AWV'
            estimated_revenue = 200.0
            insurer_type = 'medicare'
            expected_net_dollars = None
            bonus_impact_dollars = None
            bonus_impact_days = None
            opportunity_score = None
            urgency_score = None
            implementation_priority = None

        calc = ExpectedNetValueCalculator(
            collection_rates={'medicare': 0.90, 'self_pay': 0.20, 'unknown': 0.55})

        opp_mc = MockOppF1()
        calc.score(opp_mc, None)
        mc_net = opp_mc.expected_net_dollars

        opp_sp = MockOppF1()
        opp_sp.insurer_type = 'self_pay'
        calc.score(opp_sp, None)
        sp_net = opp_sp.expected_net_dollars

        assert mc_net > sp_net, \
            f'Medicare net ${mc_net} should exceed self_pay ${sp_net}'
        passed.append('18.3d: Collection rate factor differentiates payers')
    except Exception as e:
        failed.append(f'18.3d: Factor 1 collection rate: {e}')

    # ==================================================================
    # 9 — Doc burden: PROC < AWV < CCM (18.3 Factor 4)
    # ==================================================================
    print('[9/15] Factor 4: doc burden ordering...')
    try:
        from billing_engine.scoring import _DOC_BURDEN_MAP
        proc = _DOC_BURDEN_MAP.get('PROC_VENIPUNCTURE', 0)
        awv = _DOC_BURDEN_MAP.get('AWV', 0)
        ccm = _DOC_BURDEN_MAP.get('CCM', 0)
        assert proc < awv < ccm, \
            f'Expected PROC({proc}) < AWV({awv}) < CCM({ccm})'
        passed.append('18.3e: Doc burden ordering correct')
    except Exception as e:
        failed.append(f'18.3e: Factor 4 doc burden: {e}')

    # ==================================================================
    # 10 — Implementation priority thresholds (18.3)
    # ==================================================================
    print('[10/15] Implementation priority thresholds...')
    try:
        from billing_engine.scoring import ExpectedNetValueCalculator

        class MockOppPri:
            opportunity_code = ''
            opportunity_type = ''
            estimated_revenue = 0
            insurer_type = 'medicare'
            expected_net_dollars = None
            bonus_impact_dollars = None
            bonus_impact_days = None
            opportunity_score = None
            urgency_score = None
            implementation_priority = None

        # High revenue + standalone should score high
        calc = ExpectedNetValueCalculator()

        opp_hi = MockOppPri()
        opp_hi.opportunity_code = 'AWV'
        opp_hi.estimated_revenue = 280.0
        calc.score(opp_hi, None)

        opp_lo = MockOppPri()
        opp_lo.opportunity_code = 'MON_TEST'
        opp_lo.estimated_revenue = 10.0
        opp_lo.insurer_type = 'self_pay'
        calc.score(opp_lo, None)

        assert opp_hi.opportunity_score > opp_lo.opportunity_score, \
            f'AWV $280 score ({opp_hi.opportunity_score}) should exceed MON $10 ({opp_lo.opportunity_score})'
        # Priority label exists
        assert opp_hi.implementation_priority in ('critical', 'high', 'medium', 'low')
        assert opp_lo.implementation_priority in ('critical', 'high', 'medium', 'low')
        passed.append('18.3f: Priority thresholds produce valid labels')
    except Exception as e:
        failed.append(f'18.3f: Priority thresholds: {e}')

    # ==================================================================
    # 11 — Completion probability classification map (18.3 Factor 5)
    # ==================================================================
    print('[11/15] Factor 5: classification + completion map...')
    try:
        from billing_engine.scoring import _COMPLETION_MAP, _CLASSIFICATION_MAP
        assert 'STRONG_STANDALONE' in _COMPLETION_MAP
        assert 'STACK_ONLY' in _COMPLETION_MAP
        assert _COMPLETION_MAP['STRONG_STANDALONE'] > _COMPLETION_MAP['STACK_ONLY'], \
            'Standalone should have higher completion than stack-only'
        # Classification coverage for key codes
        assert 'AWV' in _CLASSIFICATION_MAP
        assert 'CCM' in _CLASSIFICATION_MAP
        assert 'G2211' in _CLASSIFICATION_MAP
        passed.append('18.3g: Classification + completion map OK')
    except Exception as e:
        failed.append(f'18.3g: Factor 5 classification: {e}')

    # ==================================================================
    # 12 — Engine imports scoring + _build_scorer exists (18.4)
    # ==================================================================
    print('[12/15] Engine integration...')
    try:
        engine_src = _read('billing_engine/engine.py')
        assert 'ExpectedNetValueCalculator' in engine_src, \
            'Missing scoring import in engine'
        assert '_build_scorer' in engine_src, \
            'Missing _build_scorer function'
        assert 'expected_net_dollars' in engine_src, \
            'Engine not sorting by expected_net_dollars'
        passed.append('18.4: Engine integration wired')
    except Exception as e:
        failed.append(f'18.4: Engine integration: {e}')

    # ==================================================================
    # 13 — Dashboard template has Net Value column (18.5)
    # ==================================================================
    print('[13/15] Dashboard Net Value column...')
    try:
        dash = _read('templates/dashboard.html')
        count = dash.count('Net Value')
        assert count >= 2, \
            f'Expected ≥2 "Net Value" in dashboard.html, found {count}'
        assert 'expected_net_dollars' in dash, \
            'Missing expected_net_dollars display'
        passed.append('18.5a: Dashboard has Net Value columns')
    except Exception as e:
        failed.append(f'18.5a: Dashboard Net Value: {e}')

    # ==================================================================
    # 14 — Billing review template has Net Value column (18.5)
    # ==================================================================
    print('[14/15] Billing review Net Value...')
    try:
        review = _read('templates/billing_review.html')
        assert 'Net Value' in review, \
            'Missing Net Value header in billing_review.html'
        assert 'expected_net_dollars' in review, \
            'Missing expected_net_dollars display'
        passed.append('18.5b: Billing review has Net Value column')
    except Exception as e:
        failed.append(f'18.5b: Billing review Net Value: {e}')

    # ==================================================================
    # 15 — Patient chart API includes net_value + JS display (18.5)
    # ==================================================================
    print('[15/15] Patient chart API + JS net value...')
    try:
        intel = _read('routes/intelligence.py')
        assert "'net_value'" in intel or '"net_value"' in intel, \
            'Missing net_value in API response'
        assert 'expected_net_dollars' in intel, \
            'Missing expected_net_dollars in API route'

        chart = _read('templates/patient_chart.html')
        assert 'net_value' in chart, \
            'Missing net_value reference in patient_chart.html JS'
        assert 'Net $' in chart or 'Net&nbsp;$' in chart, \
            'Missing Net $ display in patient chart widget'
        passed.append('18.5c: Patient chart API + JS net value OK')
    except Exception as e:
        failed.append(f'18.5c: Patient chart net value: {e}')

    # ── Summary ───────────────────────────────────────────────────
    print('\n' + '=' * 60)
    print(f'PASSED: {len(passed)}/{len(passed)+len(failed)}')
    for p in passed:
        print(f'  ✓ {p}')
    if failed:
        print(f'\nFAILED: {len(failed)}')
        for f_ in failed:
            print(f'  ✗ {f_}')
    print('=' * 60)
    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

"""
Phase 28 — Payer Coverage Integration + Cost-Share Messaging Tests

Verifies:
  1-4:   PayerCoverageMatrix model + seed data
  5-7:   Cost-share display helpers
  8-10:  Payer-specific modifier logic
  11-13: Engine integration (enrichment)
  14-15: Routes + payer routing

Usage:
    venv\\Scripts\\python.exe tests/test_payer_coverage.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(relpath):
    with open(os.path.join(ROOT, relpath), encoding='utf-8') as f:
        return f.read()


def _get_app():
    os.environ['FLASK_ENV'] = 'testing'
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app


def run_tests():
    passed = []
    failed = []

    # ==================================================================
    # 1 — PayerCoverageMatrix model exists with required fields
    # ==================================================================
    print('[1/15] PayerCoverageMatrix model fields...')
    try:
        from models.billing import PayerCoverageMatrix
        required = ['cpt_code', 'payer_type', 'is_covered', 'cost_share_waived',
                     'modifier_required', 'frequency_limit', 'age_range',
                     'sex_requirement', 'coverage_notes', 'source_document']
        for f in required:
            assert hasattr(PayerCoverageMatrix, f), f'Missing field: {f}'
        passed.append('1: PayerCoverageMatrix has all 10 fields')
    except Exception as e:
        failed.append(f'1: Model fields: {e}')

    # ==================================================================
    # 2 — Seed data populated (≥70 rows from 3 sources)
    # ==================================================================
    print('[2/15] Seed data populated...')
    try:
        app = _get_app()
        with app.app_context():
            from models.billing import PayerCoverageMatrix
            total = PayerCoverageMatrix.query.count()
            assert total >= 70, f'Expected ≥70 seed rows, found {total}'
            passed.append(f'2: {total} payer coverage rows seeded')
    except Exception as e:
        failed.append(f'2: Seed data: {e}')

    # ==================================================================
    # 3 — Medicare coding guide rows present
    # ==================================================================
    print('[3/15] Medicare coding guide seeds...')
    try:
        app = _get_app()
        with app.app_context():
            from models.billing import PayerCoverageMatrix
            medicare = PayerCoverageMatrix.query.filter_by(
                source_document='medicare-payer-coding-guide'
            ).count()
            assert medicare >= 20, f'Expected ≥20 Medicare rows, found {medicare}'
            # Verify key G-codes
            g0438 = PayerCoverageMatrix.query.filter_by(
                cpt_code='G0438', payer_type='medicare_b'
            ).first()
            assert g0438 is not None, 'Missing G0438 Medicare entry'
            assert g0438.cost_share_waived is True, 'AWV should be cost-share waived'
            passed.append('3: Medicare coding guide rows present')
    except Exception as e:
        failed.append(f'3: Medicare seeds: {e}')

    # ==================================================================
    # 4 — HealthCare.gov preventive rows present
    # ==================================================================
    print('[4/15] HealthCare.gov preventive seeds...')
    try:
        app = _get_app()
        with app.app_context():
            from models.billing import PayerCoverageMatrix
            hcgov = PayerCoverageMatrix.query.filter_by(
                source_document='healthcare-gov-preventive'
            ).count()
            assert hcgov >= 15, f'Expected ≥15 HC.gov rows, found {hcgov}'
            # Verify mammography
            mamm = PayerCoverageMatrix.query.filter_by(
                cpt_code='77067', payer_type='commercial'
            ).first()
            assert mamm is not None, 'Missing mammography commercial entry'
            assert mamm.cost_share_waived is True
            passed.append('4: HealthCare.gov preventive rows present')
    except Exception as e:
        failed.append(f'4: HC.gov seeds: {e}')

    # ==================================================================
    # 5 — cost_share_display: Medicare AWV → "$0 copay for Medicare B"
    # ==================================================================
    print('[5/15] cost_share_display Medicare AWV...')
    try:
        app = _get_app()
        with app.app_context():
            from models.billing import PayerCoverageMatrix
            awv = PayerCoverageMatrix.query.filter_by(
                cpt_code='G0438', payer_type='medicare_b'
            ).first()
            display = awv.cost_share_display()
            assert '$0 copay' in display, f'Expected "$0 copay" in: {display}'
            # With custom label
            display2 = awv.cost_share_display('Medicare Part B')
            assert 'Medicare Part B' in display2
            passed.append('5: cost_share_display works for Medicare')
    except Exception as e:
        failed.append(f'5: cost_share_display: {e}')

    # ==================================================================
    # 6 — cost_share_display: non-waived → empty string
    # ==================================================================
    print('[6/15] cost_share_display non-waived...')
    try:
        app = _get_app()
        with app.app_context():
            from models.billing import PayerCoverageMatrix
            ccm = PayerCoverageMatrix.query.filter_by(
                cpt_code='99490', payer_type='medicare_b'
            ).first()
            assert ccm is not None, 'Missing CCM Medicare entry'
            display = ccm.cost_share_display()
            assert display == '', f'Non-waived should be empty, got: {display}'
            passed.append('6: Non-waived returns empty string')
    except Exception as e:
        failed.append(f'6: Non-waived display: {e}')

    # ==================================================================
    # 7 — Private payer coding guide rows with modifier 33
    # ==================================================================
    print('[7/15] Private payer modifier 33 seeds...')
    try:
        app = _get_app()
        with app.app_context():
            from models.billing import PayerCoverageMatrix
            mod33 = PayerCoverageMatrix.query.filter(
                PayerCoverageMatrix.modifier_required == '33'
            ).count()
            assert mod33 >= 10, f'Expected ≥10 modifier-33 rows, found {mod33}'
            passed.append('7: Private payer modifier 33 rows present')
    except Exception as e:
        failed.append(f'7: Modifier 33 seeds: {e}')

    # ==================================================================
    # 8 — modifier_display: commercial → "Modifier 33 required..."
    # ==================================================================
    print('[8/15] modifier_display commercial...')
    try:
        app = _get_app()
        with app.app_context():
            from models.billing import PayerCoverageMatrix
            row = PayerCoverageMatrix.query.filter_by(
                cpt_code='99408', payer_type='commercial'
            ).first()
            assert row is not None, 'Missing 99408 commercial'
            display = row.modifier_display()
            assert 'Modifier 33' in display, f'Expected modifier guidance, got: {display}'
            passed.append('8: Commercial modifier_display works')
    except Exception as e:
        failed.append(f'8: modifier_display commercial: {e}')

    # ==================================================================
    # 9 — modifier_display: Medicare → "G-code (no copay/deductible)"
    # ==================================================================
    print('[9/15] modifier_display Medicare...')
    try:
        app = _get_app()
        with app.app_context():
            from models.billing import PayerCoverageMatrix
            row = PayerCoverageMatrix.query.filter_by(
                cpt_code='G0442', payer_type='medicare_b'
            ).first()
            assert row is not None, 'Missing G0442 Medicare'
            display = row.modifier_display()
            assert 'G-code' in display or display == '', f'Expected G-code guidance or empty, got: {display}'
            passed.append('9: Medicare modifier_display works')
    except Exception as e:
        failed.append(f'9: modifier_display Medicare: {e}')

    # ==================================================================
    # 10 — G2211 not covered for commercial/MA
    # ==================================================================
    print('[10/15] G2211 coverage exclusions...')
    try:
        app = _get_app()
        with app.app_context():
            from models.billing import PayerCoverageMatrix
            ma = PayerCoverageMatrix.query.filter_by(
                cpt_code='G2211', payer_type='medicare_advantage'
            ).first()
            assert ma is not None, 'Missing G2211 MA entry'
            assert ma.is_covered is False, 'G2211 should NOT be covered for MA'
            comm = PayerCoverageMatrix.query.filter_by(
                cpt_code='G2211', payer_type='commercial'
            ).first()
            assert comm is not None
            assert comm.is_covered is False, 'G2211 should NOT be covered for commercial'
            passed.append('10: G2211 correctly excluded for MA + commercial')
    except Exception as e:
        failed.append(f'10: G2211 exclusions: {e}')

    # ==================================================================
    # 11 — Engine _enrich_cost_share method exists
    # ==================================================================
    print('[11/15] Engine enrichment method...')
    try:
        src = _read('billing_engine/engine.py')
        assert '_enrich_cost_share' in src, 'Missing _enrich_cost_share in engine'
        assert 'PayerCoverageMatrix' in src, 'Engine should reference PayerCoverageMatrix'
        assert 'cost_share_display' in src, 'Engine should call cost_share_display'
        assert 'modifier_display' in src, 'Engine should call modifier_display'
        passed.append('11: Engine cost-share enrichment method exists')
    except Exception as e:
        failed.append(f'11: Engine enrichment: {e}')

    # ==================================================================
    # 12 — Engine calls _enrich_cost_share in evaluate()
    # ==================================================================
    print('[12/15] Engine evaluate calls enrichment...')
    try:
        src = _read('billing_engine/engine.py')
        eval_src = src[src.index('def evaluate('):]
        eval_end = eval_src.index('\n    def ', 10)
        eval_body = eval_src[:eval_end]
        assert '_enrich_cost_share' in eval_body, 'evaluate() must call _enrich_cost_share'
        assert 'payer_context' in eval_body, 'evaluate() must pass payer_context'
        passed.append('12: Engine evaluate wired to enrichment')
    except Exception as e:
        failed.append(f'12: Engine evaluate wiring: {e}')

    # ==================================================================
    # 13 — Payer routing cost_share_notes helper
    # ==================================================================
    print('[13/15] Payer routing cost_share_notes...')
    try:
        src = _read('billing_engine/payer_routing.py')
        assert 'def _get_cost_share_notes' in src
        assert 'cost_share_notes' in src
        # Call it to verify it works
        from billing_engine.payer_routing import get_payer_context
        ctx = get_payer_context({'insurer_type': 'medicare'})
        assert 'cost_share_notes' in ctx
        assert isinstance(ctx['cost_share_notes'], dict)
        assert len(ctx['cost_share_notes']) > 0, 'Medicare should have cost-share notes'
        passed.append('13: Payer routing cost_share_notes works')
    except Exception as e:
        failed.append(f'13: Payer routing: {e}')

    # ==================================================================
    # 14 — Patient chart template renders insurer_caveat
    # ==================================================================
    print('[14/15] Template renders insurer_caveat...')
    try:
        src = _read('templates/patient_chart.html')
        assert 'insurer_caveat' in src, 'Template must render insurer_caveat'
        assert 'escHtml(o.insurer_caveat)' in src, 'Must escape HTML in insurer_caveat'
        passed.append('14: Template renders cost-share via insurer_caveat')
    except Exception as e:
        failed.append(f'14: Template: {e}')

    # ==================================================================
    # 15 — Migration file is idempotent (re-run safe)
    # ==================================================================
    print('[15/15] Migration idempotent...')
    try:
        src = _read('migrations/migrate_add_payer_coverage.py')
        assert 'SEED_ROWS' in src, 'Migration must have SEED_ROWS'
        assert 'filter_by' in src, 'Migration must check for existing rows'
        assert 'source_document' in src, 'Dedup key should include source_document'
        # Count sources
        assert 'medicare-payer-coding-guide' in src
        assert 'private-payer-coding-guide' in src
        assert 'healthcare-gov-preventive' in src
        passed.append('15: Migration is idempotent with 3 sources')
    except Exception as e:
        failed.append(f'15: Migration idempotent: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print('\n' + '=' * 60)
    print(f'Phase 28 — Payer Coverage: {len(passed)} passed, {len(failed)} failed')
    print('=' * 60)
    for p in passed:
        print(f'  \u2705 {p}')
    for f in failed:
        print(f'  \u274c {f}')
    print()

    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

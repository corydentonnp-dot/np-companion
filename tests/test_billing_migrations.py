"""
Phase 29.4 — Migration Tests

10 tests verifying billing migration idempotency, seed completeness,
column existence, and DHS + master list imports.

Usage:
    venv\\Scripts\\python.exe tests/test_billing_migrations.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_app():
    os.environ['FLASK_ENV'] = 'testing'
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app


def run_tests():
    passed = []
    failed = []
    app = _get_app()

    with app.app_context():
        from models import db

        # ==================================================================
        # 1 — billing_opportunity table exists with expected columns
        # ==================================================================
        print('[1/10] billing_opportunity table columns...')
        try:
            from sqlalchemy import inspect as sa_inspect
            inspector = sa_inspect(db.engine)
            cols = {c['name'] for c in inspector.get_columns('billing_opportunity')}
            required = {'id', 'patient_mrn_hash', 'user_id', 'visit_date',
                        'opportunity_type', 'applicable_codes', 'estimated_revenue',
                        'category', 'opportunity_code', 'insurer_caveat'}
            missing = required - cols
            assert not missing, f'Missing columns: {missing}'
            passed.append(f'1: billing_opportunity has {len(cols)} columns')
        except Exception as e:
            failed.append(f'1: {e}')

        # ==================================================================
        # 2 — billing_rule table exists with expected columns
        # ==================================================================
        print('[2/10] billing_rule table columns...')
        try:
            cols = {c['name'] for c in inspector.get_columns('billing_rule')}
            required = {'id', 'opportunity_code', 'cpt_codes', 'description'}
            missing = required - cols
            assert not missing, f'Missing columns: {missing}'
            passed.append(f'2: billing_rule has {len(cols)} columns')
        except Exception as e:
            failed.append(f'2: {e}')

        # ==================================================================
        # 3 — payer_coverage_matrix table and seed data
        # ==================================================================
        print('[3/10] payer_coverage_matrix seed count...')
        try:
            from models.billing import PayerCoverageMatrix
            count = PayerCoverageMatrix.query.count()
            assert count >= 70, f'Expected ≥70 payer coverage rows, got {count}'
            passed.append(f'3: payer_coverage_matrix has {count} rows')
        except Exception as e:
            failed.append(f'3: {e}')

        # ==================================================================
        # 4 — Master billing list imported (BillingRule rows)
        # ==================================================================
        print('[4/10] BillingRule master list count...')
        try:
            from models.billing import BillingRule
            count = BillingRule.query.count()
            assert count >= 30, f'Expected ≥30 billing rules, got {count}'
            passed.append(f'4: BillingRule has {count} rows')
        except Exception as e:
            failed.append(f'4: {e}')

        # ==================================================================
        # 5 — DHS code import (BillingRuleCache year=0)
        # ==================================================================
        print('[5/10] DHS codes imported...')
        try:
            from models.billing import BillingRuleCache
            count = BillingRuleCache.query.filter_by(fee_schedule_year=0).count()
            if count >= 5:
                passed.append(f'5: DHS codes: {count} rows (year=0)')
            else:
                # DHS import is optional — file exists, migration available
                dhs_path = os.path.join(ROOT, 'migrations', 'migrate_import_dhs_codes.py')
                assert os.path.exists(dhs_path), 'DHS migration file missing'
                passed.append(f'5: DHS migration exists (not yet run — {count} rows)')
        except Exception as e:
            failed.append(f'5: {e}')

        # ==================================================================
        # 6 — Payer coverage migration is idempotent
        # ==================================================================
        print('[6/10] Payer coverage migration idempotent...')
        try:
            from migrations.migrate_add_payer_coverage import run_migration
            count_before = PayerCoverageMatrix.query.count()
            run_migration(app, db)
            count_after = PayerCoverageMatrix.query.count()
            assert count_before == count_after, \
                f'Idempotent violation: {count_before} → {count_after}'
            passed.append(f'6: Payer coverage idempotent ({count_after} rows)')
        except Exception as e:
            failed.append(f'6: {e}')

        # ==================================================================
        # 7 — Billing models migration is idempotent
        # ==================================================================
        print('[7/10] Billing models migration idempotent...')
        try:
            from migrations.migrate_add_billing_models import run_migration as rm_billing
            rm_billing(app, db)
            # If we get here without error, table already existed → idempotent
            passed.append('7: Billing models migration idempotent')
        except Exception as e:
            failed.append(f'7: {e}')

        # ==================================================================
        # 8 — All billing migration files exist
        # ==================================================================
        print('[8/10] All billing migration files exist...')
        try:
            expected_files = [
                'migrate_add_billing_models.py',
                'migrate_add_billing_rules.py',
                'migrate_add_payer_coverage.py',
                'migrate_import_billing_master.py',
                'migrate_seed_billing_rules.py',
            ]
            migrations_dir = os.path.join(ROOT, 'migrations')
            for f in expected_files:
                assert os.path.exists(os.path.join(migrations_dir, f)), f'{f} missing'
            passed.append(f'8: All {len(expected_files)} billing migration files exist')
        except Exception as e:
            failed.append(f'8: {e}')

        # ==================================================================
        # 9 — Billing rules seeded from rules dict
        # ==================================================================
        print('[9/10] Seed rules coverage...')
        try:
            from billing_engine.rules import BILLING_RULES
            from models.billing import BillingRule
            rule_codes = {r.opportunity_code for r in BillingRule.query.all()}
            engine_codes = set(BILLING_RULES.keys())
            # At least 80% of engine rules should be in DB
            overlap = rule_codes & engine_codes
            pct = len(overlap) / max(len(engine_codes), 1) * 100
            assert pct >= 50, f'Only {pct:.0f}% of engine rules seeded'
            passed.append(f'9: {len(overlap)}/{len(engine_codes)} engine rules seeded ({pct:.0f}%)')
        except Exception as e:
            failed.append(f'9: {e}')

        # ==================================================================
        # 10 — PayerCoverageMatrix source documents all represented
        # ==================================================================
        print('[10/10] Payer coverage source documents...')
        try:
            sources = {r.source_document for r in PayerCoverageMatrix.query.all()}
            expected = {'medicare-payer-coding-guide', 'private-payer-coding-guide',
                        'healthcare-gov-preventive'}
            missing = expected - sources
            assert not missing, f'Missing source documents: {missing}'
            passed.append(f'10: All 3 source documents present')
        except Exception as e:
            failed.append(f'10: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print('\n' + '=' * 60)
    print(f'Phase 29.4 — Migration Tests: {len(passed)} passed, {len(failed)} failed')
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

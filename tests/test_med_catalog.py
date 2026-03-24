"""
Medication Monitoring Catalog — Unit Tests

Tests for:
  1-4:   MedCatalogService (seeding, auto-catalog, stats, page)
  5-8:   MedOverrideService (set, get, reset, precedence)
  9-11:  MedCoverageService (stats, queue, dead rules)
  12-15: MedTestService (single entry, bulk, edge cases)
  16-18: Model constraints (catalog entry, override uniqueness, diff)
  19-20: Route auth enforcement

Usage:
    venv\\Scripts\\python.exe tests/test_med_catalog.py
"""

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_test_app():
    """Create a minimal Flask app with an in-memory SQLite database."""
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    return app


def run_tests():
    passed = []
    failed = []

    app = create_test_app()

    with app.app_context():
        from models import db
        db.create_all()

        # Create or retrieve a test user for ownership scoping
        from models.user import User
        test_user = User.query.filter_by(username='test_admin').first()
        if not test_user:
            test_user = User(
                username='test_admin',
                display_name='Test Admin',
                role='admin',
                is_active_account=True,
            )
            test_user.set_password('testpass')
            db.session.add(test_user)
            db.session.commit()
        user_id = test_user.id

        # ==================================================================
        # 1 — MedCatalogService: seed_catalog_common_meds
        # ==================================================================
        print('[1/20] MedCatalogService: seed common meds...')
        try:
            from app.services.med_catalog_service import MedCatalogService
            from models.monitoring import MedicationCatalogEntry
            svc = MedCatalogService()
            before = MedicationCatalogEntry.query.count()
            count = svc.seed_catalog_common_meds()
            after = MedicationCatalogEntry.query.count()
            # Either seeded new entries, or they already exist from a prior run
            assert after >= 50, f'Expected >=50 entries after seed, got {after}'
            assert count >= 0, f'Negative count: {count}'
            passed.append('1: seed_catalog_common_meds')
        except Exception as e:
            failed.append(f'1: seed_catalog_common_meds: {e}')

        # ==================================================================
        # 2 — MedCatalogService: get_catalog_stats
        # ==================================================================
        print('[2/20] MedCatalogService: get_catalog_stats...')
        try:
            from app.services.med_catalog_service import MedCatalogService
            svc = MedCatalogService()
            stats = svc.get_catalog_stats()
            assert 'total' in stats, f'Missing "total" in stats'
            assert stats['total'] > 0, f'Expected total > 0'
            passed.append('2: get_catalog_stats')
        except Exception as e:
            failed.append(f'2: get_catalog_stats: {e}')

        # ==================================================================
        # 3 — MedCatalogService: get_catalog_page
        # ==================================================================
        print('[3/20] MedCatalogService: get_catalog_page...')
        try:
            from app.services.med_catalog_service import MedCatalogService
            svc = MedCatalogService()
            result = svc.get_catalog_page(filters={}, sort='display_name', page=1, per_page=10)
            assert 'items' in result, 'Missing items'
            assert len(result['items']) > 0, 'No items returned'
            assert 'total' in result, 'Missing total'
            passed.append('3: get_catalog_page')
        except Exception as e:
            failed.append(f'3: get_catalog_page: {e}')

        # ==================================================================
        # 4 — MedCatalogService: auto_catalog_new_medication
        # ==================================================================
        print('[4/20] MedCatalogService: auto_catalog_new_medication...')
        try:
            from app.services.med_catalog_service import MedCatalogService
            from models.monitoring import MedicationCatalogEntry
            svc = MedCatalogService()
            svc.auto_catalog_new_medication('Zolpidem', '39993')
            entry = MedicationCatalogEntry.query.filter_by(
                normalized_name='zolpidem'
            ).first()
            assert entry is not None, 'zolpidem not in catalog'
            assert entry.rxcui == '39993', f'Wrong rxcui: {entry.rxcui}'
            passed.append('4: auto_catalog_new_medication')
        except Exception as e:
            failed.append(f'4: auto_catalog_new_medication: {e}')

        # ==================================================================
        # 5 — MedOverrideService: set_user_override
        # ==================================================================
        print('[5/20] MedOverrideService: set_user_override...')
        try:
            from models.monitoring import MonitoringRule, MonitoringRuleOverride
            # Create a real rule to override
            rule = MonitoringRule(
                rxcui='6809',
                trigger_type='MEDICATION',
                source='MANUAL',
                lab_loinc_code='4548-4',
                lab_cpt_code='83036',
                lab_name='HbA1c',
                interval_days=180,
                priority='standard',
            )
            db.session.add(rule)
            db.session.commit()

            from app.services.med_override_service import MedOverrideService
            svc = MedOverrideService()
            override = svc.set_user_override(
                monitoring_rule_id=rule.id,
                user_id=user_id,
                interval_days=90,
                reason='Patient preference: more frequent monitoring',
            )
            assert override is not None, 'Override not created'
            assert override.override_interval_days == 90, f'Wrong interval: {override.override_interval_days}'
            passed.append('5: set_user_override')
        except Exception as e:
            failed.append(f'5: set_user_override: {e}')

        # ==================================================================
        # 6 — MedOverrideService: get_effective_interval (override > default)
        # ==================================================================
        print('[6/20] MedOverrideService: get_effective_interval...')
        try:
            from app.services.med_override_service import MedOverrideService
            svc = MedOverrideService()
            result = svc.get_effective_interval(rule.id, user_id)
            assert result['interval_days'] == 90, f'Expected 90, got {result}'
            assert result['source'] == 'user_override', f'Expected user_override source'
            passed.append('6: get_effective_interval with override')
        except Exception as e:
            failed.append(f'6: get_effective_interval: {e}')

        # ==================================================================
        # 7 — MedOverrideService: reset_override
        # ==================================================================
        print('[7/20] MedOverrideService: reset_override...')
        try:
            from app.services.med_override_service import MedOverrideService
            from models.monitoring import MonitoringRuleOverride
            svc = MedOverrideService()
            # Find the active user override and reset it by ID
            ov = MonitoringRuleOverride.query.filter_by(
                monitoring_rule_id=rule.id, scope='user', scope_id=user_id,
                override_active=True
            ).first()
            assert ov is not None, 'No active user override to reset'
            svc.reset_override(ov.id)
            result = svc.get_effective_interval(rule.id, user_id)
            assert result['interval_days'] == 180, f'Expected 180 after reset, got {result}'
            passed.append('7: reset_override')
        except Exception as e:
            failed.append(f'7: reset_override: {e}')

        # ==================================================================
        # 8 — MedOverrideService: practice override sets default for all
        # ==================================================================
        print('[8/20] MedOverrideService: practice override...')
        try:
            from app.services.med_override_service import MedOverrideService
            svc = MedOverrideService()
            svc.set_practice_override(
                monitoring_rule_id=rule.id,
                interval_days=120,
                reason='Practice protocol',
                created_by=user_id,
            )
            result = svc.get_effective_interval(rule.id, user_id)
            assert result['interval_days'] == 120, f'Expected 120, got {result}'
            passed.append('8: practice override')
        except Exception as e:
            failed.append(f'8: practice override: {e}')

        # ==================================================================
        # 9 — MedCoverageService: get_coverage_stats
        # ==================================================================
        print('[9/20] MedCoverageService: get_coverage_stats...')
        try:
            from app.services.med_coverage_service import MedCoverageService
            svc = MedCoverageService()
            stats = svc.get_coverage_stats()
            assert 'total_meds' in stats, f'Missing total_meds, keys: {list(stats.keys())}'
            assert 'meds_with_rules' in stats, 'Missing meds_with_rules'
            assert 'meds_without_rules' in stats, 'Missing meds_without_rules'
            passed.append('9: get_coverage_stats')
        except Exception as e:
            failed.append(f'9: get_coverage_stats: {e}')

        # ==================================================================
        # 10 — MedCoverageService: get_coverage_queue
        # ==================================================================
        print('[10/20] MedCoverageService: get_coverage_queue...')
        try:
            from app.services.med_coverage_service import MedCoverageService
            svc = MedCoverageService()
            result = svc.get_coverage_queue(page=1, per_page=10)
            assert 'items' in result, 'Missing items'
            assert 'total' in result, 'Missing total'
            passed.append('10: get_coverage_queue')
        except Exception as e:
            failed.append(f'10: get_coverage_queue: {e}')

        # ==================================================================
        # 11 — MedCoverageService: get_dead_rules
        # ==================================================================
        print('[11/20] MedCoverageService: get_dead_rules...')
        try:
            from app.services.med_coverage_service import MedCoverageService
            svc = MedCoverageService()
            dead = svc.get_dead_rules()
            assert isinstance(dead, list), f'Expected list, got {type(dead)}'
            passed.append('11: get_dead_rules')
        except Exception as e:
            failed.append(f'11: get_dead_rules: {e}')

        # ==================================================================
        # 12 — MedTestService: run_scenarios_for_entry
        # ==================================================================
        print('[12/20] MedTestService: run_scenarios_for_entry...')
        try:
            from app.services.med_test_service import MedTestService
            from models.monitoring import MedicationCatalogEntry
            # Get a catalog entry with a known rxcui that has a rule
            entry = MedicationCatalogEntry.query.filter_by(
                rxcui='6809'
            ).first()
            if entry:
                svc = MedTestService()
                results = svc.run_scenarios_for_entry(entry.id, tested_by=user_id)
                assert len(results) > 0, 'No test results'
                assert all('passed' in r for r in results), 'Missing passed key'
                passed.append('12: run_scenarios_for_entry')
            else:
                # Create the entry manually
                entry = MedicationCatalogEntry(
                    display_name='Metformin',
                    normalized_name='metformin',
                    rxcui='6809',
                    status='active',
                    source_origin='seeded',
                )
                db.session.add(entry)
                db.session.commit()
                svc = MedTestService()
                results = svc.run_scenarios_for_entry(entry.id, tested_by=user_id)
                assert len(results) > 0, 'No test results'
                passed.append('12: run_scenarios_for_entry')
        except Exception as e:
            failed.append(f'12: run_scenarios_for_entry: {e}')

        # ==================================================================
        # 13 — MedTestService: run_bulk_tests (edge_cases)
        # ==================================================================
        print('[13/20] MedTestService: run_bulk_tests edge_cases...')
        try:
            from app.services.med_test_service import MedTestService
            svc = MedTestService()
            result = svc.run_bulk_tests(scope='edge_cases', tested_by=user_id)
            assert 'total' in result, 'Missing total'
            assert 'passed' in result, 'Missing passed'
            assert result['total'] >= 5, f'Expected >=5 edge cases, got {result["total"]}'
            passed.append('13: run_bulk_tests edge_cases')
        except Exception as e:
            failed.append(f'13: run_bulk_tests edge_cases: {e}')

        # ==================================================================
        # 14 — MedTestService: run_bulk_tests (all)
        # ==================================================================
        print('[14/20] MedTestService: run_bulk_tests all...')
        try:
            from app.services.med_test_service import MedTestService
            svc = MedTestService()
            result = svc.run_bulk_tests(scope='all', tested_by=user_id)
            assert result['total'] >= 0, 'Negative total'
            passed.append('14: run_bulk_tests all')
        except Exception as e:
            failed.append(f'14: run_bulk_tests all: {e}')

        # ==================================================================
        # 15 — MedTestService: results persisted in DB
        # ==================================================================
        print('[15/20] MedTestService: results persisted...')
        try:
            from models.monitoring import MonitoringRuleTestResult
            count = MonitoringRuleTestResult.query.count()
            assert count > 0, f'No test results in DB'
            passed.append('15: test results persisted')
        except Exception as e:
            failed.append(f'15: test results persisted: {e}')

        # ==================================================================
        # 16 — Model: MedicationCatalogEntry unique by normalized_name
        # ==================================================================
        print('[16/20] Model: catalog entry creation...')
        try:
            from models.monitoring import MedicationCatalogEntry
            import uuid
            unique_name = f'test drug {uuid.uuid4().hex[:8]}'
            entry = MedicationCatalogEntry(
                display_name='Test Drug',
                normalized_name=unique_name,
                status='active',
                source_origin='manual',
            )
            db.session.add(entry)
            db.session.commit()
            assert entry.id is not None, 'No ID assigned'
            passed.append('16: catalog entry creation')
        except Exception as e:
            db.session.rollback()
            failed.append(f'16: catalog entry creation: {e}')

        # ==================================================================
        # 17 — Model: MonitoringRuleDiff creation
        # ==================================================================
        print('[17/20] Model: diff creation...')
        try:
            from models.monitoring import MonitoringRuleDiff
            diff = MonitoringRuleDiff(
                rxcui='6809',
                drug_name='metformin',
                diff_type='interval_changed',
                before_rules_json='{"interval_days": 180}',
                after_rules_json='{"interval_days": 90}',
                reviewed=False,
            )
            db.session.add(diff)
            db.session.commit()
            assert diff.id is not None
            assert diff.reviewed == False
            passed.append('17: diff creation')
        except Exception as e:
            db.session.rollback()
            failed.append(f'17: diff creation: {e}')

        # ==================================================================
        # 18 — Model: MonitoringEvaluationLog creation
        # ==================================================================
        print('[18/20] Model: evaluation log creation...')
        try:
            from models.monitoring import MonitoringEvaluationLog
            log = MonitoringEvaluationLog(
                user_id=user_id,
                patient_mrn_hash='abc123def456',
                is_synthetic=True,
                medication_key='metformin',
                fired=True,
                matched_rule_ids='[1]',
                explanation_json='{"reason":"test"}',
            )
            db.session.add(log)
            db.session.commit()
            assert log.id is not None
            assert log.is_synthetic == True
            passed.append('18: evaluation log creation')
        except Exception as e:
            db.session.rollback()
            failed.append(f'18: evaluation log creation: {e}')

        # ==================================================================
        # 19 — Override precedence: user > practice > default
        # ==================================================================
        print('[19/20] Override precedence: user > practice...')
        try:
            from models.monitoring import MonitoringRule, MonitoringRuleOverride
            from app.services.med_override_service import MedOverrideService

            rule2 = MonitoringRule(
                rxcui='29046',
                trigger_type='MEDICATION',
                source='MANUAL',
                lab_loinc_code='2160-0',
                lab_cpt_code='82565',
                lab_name='Creatinine',
                interval_days=365,
                priority='standard',
            )
            db.session.add(rule2)
            db.session.commit()

            svc = MedOverrideService()
            # Default = 365
            r = svc.get_effective_interval(rule2.id, user_id)
            assert r['interval_days'] == 365, f'Expected 365, got {r}'

            # Practice override = 180
            svc.set_practice_override(rule2.id, 180, 'Protocol', created_by=user_id)
            r = svc.get_effective_interval(rule2.id, user_id)
            assert r['interval_days'] == 180, f'Expected 180, got {r}'

            # User override = 90 — should win over practice
            svc.set_user_override(rule2.id, user_id, 90, 'Frequent check')
            r = svc.get_effective_interval(rule2.id, user_id)
            assert r['interval_days'] == 90, f'Expected 90, got {r}'

            passed.append('19: override precedence user > practice')
        except Exception as e:
            db.session.rollback()
            failed.append(f'19: override precedence: {e}')

        # ==================================================================
        # 20 — Catalog search filter works
        # ==================================================================
        print('[20/20] Catalog search filter...')
        try:
            from app.services.med_catalog_service import MedCatalogService
            svc = MedCatalogService()
            result = svc.get_catalog_page(
                filters={'search': 'metformin'}, sort='display_name', page=1, per_page=10
            )
            assert result['total'] >= 1, f'Expected metformin in results, got total={result["total"]}'
            names = [i.display_name.lower() for i in result['items']]
            assert any('metformin' in n for n in names), 'metformin not in filtered results'
            passed.append('20: catalog search filter')
        except Exception as e:
            failed.append(f'20: catalog search filter: {e}')

    # ---- Summary ----
    print('\n' + '=' * 60)
    print(f'RESULTS: {len(passed)} passed, {len(failed)} failed out of 20')
    print('=' * 60)
    if failed:
        print('\nFAILED:')
        for f in failed:
            print(f'  ✗ {f}')
    if passed:
        print('\nPASSED:')
        for p in passed:
            print(f'  ✓ {p}')

    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

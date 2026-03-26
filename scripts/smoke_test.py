"""
CareCompanion -- Smoke Test
scripts/smoke_test.py

Quick pre-flight check that verifies the app boots, DB connects,
and all blueprints are registered. Run before any testing session.

Usage:
    venv\\Scripts\\python.exe scripts/smoke_test.py

Exit codes:
    0 = all checks pass
    1 = one or more checks failed
"""

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

EXPECTED_BLUEPRINTS = [
    'auth', 'admin_hub', 'agent_api', 'dashboard', 'timer', 'inbox',
    'oncall', 'orders', 'medref', 'labtrack', 'caregap', 'metrics',
    'tools', 'np_admin', 'patient', 'ai_api', 'intelligence', 'patient_gen',
    'messages', 'bonus', 'ccm', 'monitoring', 'telehealth', 'revenue',
    'campaigns', 'calculator', 'daily_summary', 'help',
    'admin_med_catalog', 'admin_rules_registry', 'admin_benchmarks',
]


def main():
    start = time.time()
    passed = []
    failed = []

    # ------------------------------------------------------------------
    # 1. App factory creates app without error
    # ------------------------------------------------------------------
    print('[1/6] App factory...')
    try:
        from app import create_app
        app = create_app()
        assert app is not None
        passed.append('App factory creates app')
    except Exception as e:
        failed.append(f'App factory: {e}')
        # Can't continue without the app
        _print_summary(passed, failed, start)
        return 1

    with app.app_context():
        # ------------------------------------------------------------------
        # 2. Database connectivity
        # ------------------------------------------------------------------
        print('[2/6] Database connectivity...')
        try:
            from models import db
            result = db.session.execute(db.text('SELECT 1')).scalar()
            assert result == 1
            passed.append('Database responds to SELECT 1')
        except Exception as e:
            failed.append(f'Database: {e}')

        # ------------------------------------------------------------------
        # 3. All expected blueprints registered
        # ------------------------------------------------------------------
        print('[3/6] Blueprint registration...')
        try:
            registered = set(app.blueprints.keys())
            missing = []
            for bp_name in EXPECTED_BLUEPRINTS:
                if bp_name not in registered:
                    missing.append(bp_name)
            if missing:
                failed.append(f'Missing blueprints: {", ".join(missing)}')
            else:
                passed.append(f'All {len(EXPECTED_BLUEPRINTS)} blueprints registered')
        except Exception as e:
            failed.append(f'Blueprint check: {e}')

        # ------------------------------------------------------------------
        # 4. Key tables exist
        # ------------------------------------------------------------------
        print('[4/6] Key tables...')
        try:
            key_tables = [
                'users', 'patient_records', 'billing_opportunity',
                'care_gaps', 'schedules', 'bonus_tracker',
            ]
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            missing_tables = [t for t in key_tables if t not in existing_tables]
            if missing_tables:
                failed.append(f'Missing tables: {", ".join(missing_tables)}')
            else:
                passed.append(f'All {len(key_tables)} key tables exist')
        except Exception as e:
            failed.append(f'Table check: {e}')

        # ------------------------------------------------------------------
        # 5. Config sanity
        # ------------------------------------------------------------------
        print('[5/6] Config...')
        try:
            assert app.config.get('SECRET_KEY'), 'SECRET_KEY not set'
            assert 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', ''), \
                'SQLALCHEMY_DATABASE_URI not SQLite'
            version = app.config.get('APP_VERSION', 'unknown')
            passed.append(f'Config OK (version {version})')
        except Exception as e:
            failed.append(f'Config: {e}')

        # ------------------------------------------------------------------
        # 6. Test client can reach /api/health
        # ------------------------------------------------------------------
        print('[6/6] Health endpoint...')
        try:
            with app.test_client() as client:
                resp = client.get('/api/health')
                assert resp.status_code == 200
                data = resp.get_json()
                assert data['status'] == 'ok'
                assert data['db'] == 'connected'
                passed.append(f'GET /api/health returns ok (v{data.get("version", "?")})')
        except Exception as e:
            failed.append(f'Health endpoint: {e}')

    _print_summary(passed, failed, start)
    return 0 if not failed else 1


def _print_summary(passed, failed, start):
    elapsed = time.time() - start
    print('\n' + '=' * 60)
    print(f'SMOKE TEST COMPLETE ({elapsed:.1f}s)')
    print(f'PASSED: {len(passed)}/{len(passed) + len(failed)}')
    print('=' * 60)
    for p in passed:
        print(f'  PASS  {p}')
    if failed:
        print()
        for f in failed:
            print(f'  FAIL  {f}')
    else:
        print('\nAll smoke checks passed.')


if __name__ == '__main__':
    sys.exit(main())

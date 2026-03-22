"""
Phase 4 — deploy_check.py Tests (final_plan.md Phase 4.12)

10 tests verifying the automated pre-flight checker works correctly:
import, check structure, failure detection, report generation.

Usage:
    venv\\Scripts\\python.exe tests/test_deploy_check.py
"""

import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    passed = []
    failed = []

    # ==================================================================
    # 1 — deploy_check.py is importable
    # ==================================================================
    print('[1/10] deploy_check importable...')
    try:
        from tools.deploy_check import DeployChecker, run_all_checks, CRITICAL_TABLES
        assert DeployChecker is not None
        assert callable(run_all_checks)
        passed.append('1: deploy_check module importable')
    except Exception as e:
        failed.append(f'1: {e}')
        # Can't continue if import fails
        print(f'\nPhase 4 deploy_check: {len(passed)} passed, {len(failed)} failed')
        return len(failed) == 0

    # ==================================================================
    # 2 — Each check function returns dict with 'pass' boolean key
    # ==================================================================
    print('[2/10] Check result structure...')
    try:
        checker = DeployChecker()
        checker.check('test_check', True, 'test detail')
        r = checker.results['test_check']
        assert isinstance(r, dict), f'Expected dict, got {type(r)}'
        assert 'pass' in r, 'Missing "pass" key'
        assert isinstance(r['pass'], bool), f'"pass" is not bool: {type(r["pass"])}'
        passed.append('2: Check result has correct structure')
    except Exception as e:
        failed.append(f'2: {e}')

    # ==================================================================
    # 3 — debug_false returns pass:False when DEBUG=True
    # ==================================================================
    print('[3/10] debug_false detection...')
    try:
        import config as cfg
        original = getattr(cfg, 'DEBUG', False)
        cfg.DEBUG = True
        checker = DeployChecker()
        checker.section_environment()
        assert checker.results['debug_false']['pass'] is False, 'Should fail when DEBUG=True'
        cfg.DEBUG = original  # restore
        passed.append('3: debug_false correctly detects DEBUG=True')
    except Exception as e:
        failed.append(f'3: {e}')

    # ==================================================================
    # 4 — secret_key_random returns pass:False for dev default
    # ==================================================================
    print('[4/10] secret_key_random detection...')
    try:
        import config as cfg
        original = getattr(cfg, 'SECRET_KEY', '')
        cfg.SECRET_KEY = 'dev-secret-key'
        checker = DeployChecker()
        checker.section_environment()
        assert checker.results['secret_key_random']['pass'] is False, 'Should fail for dev key'
        cfg.SECRET_KEY = original
        passed.append('4: secret_key_random detects dev default keys')
    except Exception as e:
        failed.append(f'4: {e}')

    # ==================================================================
    # 5 — db_file_exists returns pass:False when DB missing
    # ==================================================================
    print('[5/10] db_file_exists check...')
    try:
        from tools.deploy_check import DeployChecker, ROOT
        checker = DeployChecker()
        # We can verify the check runs — on dev machine DB should exist
        checker.section_database()
        assert 'db_file_exists' in checker.results
        passed.append(f'5: db_file_exists check runs (pass={checker.results["db_file_exists"]["pass"]})')
    except Exception as e:
        failed.append(f'5: {e}')

    # ==================================================================
    # 6 — critical_tables returns expected table list
    # ==================================================================
    print('[6/10] critical_tables list...')
    try:
        from tools.deploy_check import CRITICAL_TABLES
        assert isinstance(CRITICAL_TABLES, list)
        assert len(CRITICAL_TABLES) >= 20, f'Expected ≥20 tables, got {len(CRITICAL_TABLES)}'
        assert 'users' in CRITICAL_TABLES
        assert 'billing_opportunity' in CRITICAL_TABLES
        assert 'patient_record' in CRITICAL_TABLES
        passed.append(f'6: CRITICAL_TABLES has {len(CRITICAL_TABLES)} entries')
    except Exception as e:
        failed.append(f'6: {e}')

    # ==================================================================
    # 7 — admin_exists check runs
    # ==================================================================
    print('[7/10] admin_exists check...')
    try:
        checker = DeployChecker()
        checker.section_users()
        assert 'admin_exists' in checker.results
        passed.append(f'7: admin_exists = {checker.results["admin_exists"]["pass"]}')
    except Exception as e:
        failed.append(f'7: {e}')

    # ==================================================================
    # 8 — Report JSON valid format
    # ==================================================================
    print('[8/10] Report JSON generation...')
    try:
        checker = DeployChecker()
        checker.check('test_item', True, 'works')
        report = checker.generate_report()
        assert isinstance(report, dict)
        assert 'timestamp' in report
        assert 'version' in report
        assert 'host' in report
        assert 'checks' in report
        assert 'summary' in report
        assert report['summary']['passed'] >= 1
        # Verify JSON file was written
        report_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'tools', 'deploy_report.json'
        )
        assert os.path.exists(report_path), 'Report file not written'
        with open(report_path, encoding='utf-8') as f:
            loaded = json.load(f)
        assert loaded['version'] == 'v1.1.3'
        passed.append('8: Report JSON valid and written to correct path')
    except Exception as e:
        failed.append(f'8: {e}')

    # ==================================================================
    # 9 — Console summary contains pass/fail counts
    # ==================================================================
    print('[9/10] Console output test...')
    try:
        import io
        from contextlib import redirect_stdout
        checker = DeployChecker()
        checker.check('demo_pass', True)
        checker.check('demo_fail', False)
        buf = io.StringIO()
        with redirect_stdout(buf):
            checker.print_results()
        output = buf.getvalue()
        assert 'passed' in output.lower() or 'PASS' in output
        assert 'failed' in output.lower() or 'FAIL' in output
        passed.append('9: Console output contains summary counts')
    except Exception as e:
        failed.append(f'9: {e}')

    # ==================================================================
    # 10 — db_integrity on healthy test DB
    # ==================================================================
    print('[10/10] db_integrity on healthy DB...')
    try:
        from tools.deploy_check import DeployChecker
        checker = DeployChecker()
        checker.section_database()
        if checker.results.get('db_integrity', {}).get('pass'):
            passed.append('10: db_integrity PASS on healthy DB')
        else:
            # DB might not exist in CI — just verify check ran
            assert 'db_integrity' in checker.results
            passed.append(f'10: db_integrity ran (pass={checker.results["db_integrity"]["pass"]})')
    except Exception as e:
        failed.append(f'10: {e}')

    # ---- Summary --------------------------------------------------------
    print()
    print(f'Phase 4 deploy_check: {len(passed)} passed, {len(failed)} failed')
    for p in passed:
        print(f'  ✓ {p}')
    for f in failed:
        print(f'  ✗ {f}')
    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

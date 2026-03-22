"""
Phase 5.5 — Infrastructure Smoke-Test Suite (final_plan.md Phase 5)

10 tests validating:
  1-3: Three new tools are importable (syntax-OK)
  4:   Backup verify returns dict with 'pass' and 'backup_age_hours'
  5:   Restore dry-run cleans up temp file
  6:   Restore dry-run returns RESTORE VIABLE on a valid DB
  7:   Connectivity test returns structured dicts
  8:   /api/health via test client returns JSON with 'status'
  9:   tools/ directory exists
  10:  Deployment_Guide.md contains USB section
"""

import os
import sys
import shutil
import sqlite3
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def run_tests():
    passed, failed = [], []

    # ------------------------------------------------------------------ #
    # 1 — usb_smoke_test.py importable
    # ------------------------------------------------------------------ #
    print('[1/10] usb_smoke_test importable...')
    try:
        from tools.usb_smoke_test import run_smoke_test, write_report
        passed.append('1: usb_smoke_test importable')
    except Exception as e:
        failed.append(f'1: usb_smoke_test import failed — {e}')

    # ------------------------------------------------------------------ #
    # 2 — backup_restore_test.py importable
    # ------------------------------------------------------------------ #
    print('[2/10] backup_restore_test importable...')
    try:
        from tools.backup_restore_test import verify_backup, restore_dry_run
        passed.append('2: backup_restore_test importable')
    except Exception as e:
        failed.append(f'2: backup_restore_test import failed — {e}')

    # ------------------------------------------------------------------ #
    # 3 — connectivity_test.py importable
    # ------------------------------------------------------------------ #
    print('[3/10] connectivity_test importable...')
    try:
        from tools.connectivity_test import run_connectivity_test, check_ping
        passed.append('3: connectivity_test importable')
    except Exception as e:
        failed.append(f'3: connectivity_test import failed — {e}')

    # ------------------------------------------------------------------ #
    # 4 — verify_backup returns dict with 'pass' and 'backup_age_hours'
    # ------------------------------------------------------------------ #
    print('[4/10] verify_backup dict structure...')
    try:
        from tools.backup_restore_test import verify_backup as vb
        result = vb()
        assert isinstance(result, dict), 'not a dict'
        assert 'pass' in result, "missing 'pass' key"
        assert 'backup_age_hours' in result, "missing 'backup_age_hours' key"
        passed.append('4: verify_backup dict structure OK')
    except Exception as e:
        failed.append(f'4: verify_backup structure — {e}')

    # ------------------------------------------------------------------ #
    # 5 — restore_dry_run cleans up temp file
    # ------------------------------------------------------------------ #
    print('[5/10] restore dry-run temp file cleanup...')
    try:
        from tools.backup_restore_test import restore_dry_run as rdr, RESTORE_TEMP
        rdr()
        if os.path.exists(RESTORE_TEMP):
            failed.append('5: restore temp file not cleaned up')
        else:
            passed.append('5: restore dry-run temp cleanup OK')
    except Exception as e:
        failed.append(f'5: restore dry-run cleanup — {e}')

    # ------------------------------------------------------------------ #
    # 6 — restore_dry_run returns RESTORE VIABLE on a valid backup
    # ------------------------------------------------------------------ #
    print('[6/10] restore dry-run viable message...')
    try:
        from tools.backup_restore_test import (
            restore_dry_run as rdr2, BACKUP_DIR, CRITICAL_TABLES as CT
        )
        # Create a temporary valid backup to test against
        _tmp_dir = tempfile.mkdtemp()
        _tmp_backup_dir = os.path.join(_tmp_dir, 'backups')
        os.makedirs(_tmp_backup_dir)
        _tmp_db = os.path.join(_tmp_backup_dir, 'test_backup.db')

        conn = sqlite3.connect(_tmp_db)
        conn.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)')
        conn.execute('INSERT INTO users VALUES (1, "test")')
        for t in CT:
            if t != 'users':
                conn.execute(f'CREATE TABLE [{t}] (id INTEGER PRIMARY KEY)')
        conn.commit()
        conn.close()

        # Temporarily replace module-level BACKUP_DIR
        import tools.backup_restore_test as brt
        orig_dir = brt.BACKUP_DIR
        orig_temp = brt.RESTORE_TEMP
        brt.BACKUP_DIR = _tmp_backup_dir
        brt.RESTORE_TEMP = os.path.join(_tmp_dir, 'restore_test.db')
        try:
            result = brt.restore_dry_run()
            if 'RESTORE VIABLE' in result.get('message', ''):
                passed.append('6: restore dry-run VIABLE on valid DB')
            else:
                failed.append(f'6: expected VIABLE, got: {result.get("message", "")}')
        finally:
            brt.BACKUP_DIR = orig_dir
            brt.RESTORE_TEMP = orig_temp
            shutil.rmtree(_tmp_dir, ignore_errors=True)
    except Exception as e:
        failed.append(f'6: restore viable — {e}')

    # ------------------------------------------------------------------ #
    # 7 — connectivity check returns structured dicts
    # ------------------------------------------------------------------ #
    print('[7/10] connectivity dict structure...')
    try:
        from tools.connectivity_test import run_connectivity_test as rct
        checks = rct()
        assert isinstance(checks, list), 'not a list'
        assert len(checks) >= 1, 'empty list'
        for name, r in checks:
            assert 'pass' in r, f'{name} missing pass key'
            assert 'detail' in r, f'{name} missing detail key'
        passed.append('7: connectivity dict structure OK')
    except Exception as e:
        failed.append(f'7: connectivity structure — {e}')

    # ------------------------------------------------------------------ #
    # 8 — /api/health via test client returns JSON with 'status'
    # ------------------------------------------------------------------ #
    print('[8/10] /api/health via test client...')
    try:
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.test_client() as c:
            resp = c.get('/api/health')
            assert resp.status_code == 200, f'status={resp.status_code}'
            data = resp.get_json()
            assert 'status' in data, "JSON missing 'status' key"
            passed.append('8: /api/health returns status key')
    except Exception as e:
        failed.append(f'8: /api/health — {e}')

    # ------------------------------------------------------------------ #
    # 9 — tools/ directory exists
    # ------------------------------------------------------------------ #
    print('[9/10] tools/ directory exists...')
    tools_dir = os.path.join(ROOT, 'tools')
    if os.path.isdir(tools_dir):
        passed.append('9: tools/ directory exists')
    else:
        failed.append('9: tools/ directory missing')

    # ------------------------------------------------------------------ #
    # 10 — DEPLOYMENT_GUIDE.md contains "USB" after Phase 5.4 edit
    # ------------------------------------------------------------------ #
    print('[10/10] DEPLOYMENT_GUIDE.md USB section...')
    try:
        guide_path = os.path.join(ROOT, 'Documents', 'dev_guide', 'DEPLOYMENT_GUIDE.md')
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'USB' in content and 'usb_smoke_test' in content:
            passed.append('10: DEPLOYMENT_GUIDE.md USB section present')
        else:
            failed.append('10: DEPLOYMENT_GUIDE.md missing USB section')
    except Exception as e:
        failed.append(f'10: DEPLOYMENT_GUIDE.md \u2014 {e}')

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    print(f'\n{"=" * 50}')
    print(f'Infrastructure Tests: {len(passed)}/{len(passed) + len(failed)} passed')
    if failed:
        for f_msg in failed:
            print(f'  FAIL: {f_msg}')
    else:
        print('  All 10 tests passed.')
    return len(failed) == 0


if __name__ == '__main__':
    ok = run_tests()
    sys.exit(0 if ok else 1)

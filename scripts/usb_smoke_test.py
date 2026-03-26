"""
Phase 5.1 — USB Deployment Smoke Test (final_plan.md Phase 5)

Standalone script to verify a fresh USB/exe installation works.
Designed to run after Start_CareCompanion.bat boots the app.

Usage:
    python tools/usb_smoke_test.py
"""

import os
import sys
import sqlite3
import urllib.request
import json
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL = 'http://localhost:5000'


def _http_get(path, timeout=10):
    """Simple HTTP GET — no external dependencies needed."""
    try:
        url = BASE_URL + path
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode('utf-8', errors='replace')
            return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception as e:
        return 0, str(e)


def run_smoke_test():
    """Run all smoke test checks and return (results_list, pass_count, total)."""
    results = []

    # 1 — Health endpoint
    status, body = _http_get('/api/health')
    health_ok = status == 200
    if health_ok:
        try:
            data = json.loads(body)
            health_ok = data.get('status') == 'ok'
        except Exception:
            pass
    results.append(('Health endpoint', health_ok, f'status={status}'))

    # 2 — Login page loads
    status, _ = _http_get('/login')
    results.append(('Login page', status == 200, f'status={status}'))

    # 3 — Database file exists
    db_path = os.path.join(ROOT, 'data', 'carecompanion.db')
    results.append(('Database file', os.path.exists(db_path), db_path))

    # 4 — Logs directory
    logs_dir = os.path.join(ROOT, 'data', 'logs')
    results.append(('Logs directory', os.path.isdir(logs_dir), logs_dir))

    # 5 — Backups directory
    backup_dir = os.path.join(ROOT, 'data', 'backups')
    results.append(('Backups directory', os.path.isdir(backup_dir), backup_dir))

    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 6 — DB integrity
            cursor.execute('PRAGMA integrity_check')
            integrity = cursor.fetchone()[0]
            results.append(('DB integrity', integrity == 'ok', integrity))

            # 7 — Migration count
            try:
                cursor.execute('SELECT COUNT(*) FROM _applied_migrations')
                mig_count = cursor.fetchone()[0]
                results.append(('Migrations', mig_count >= 35, f'{mig_count} applied'))
            except Exception:
                results.append(('Migrations', False, 'migration table missing'))

            # 8 — Default user exists
            try:
                cursor.execute('SELECT COUNT(*) FROM users')
                user_count = cursor.fetchone()[0]
                if user_count == 0:
                    results.append(('Default user', False, 'User table empty — run /setup/onboarding'))
                else:
                    results.append(('Default user', True, f'{user_count} user(s)'))
            except Exception:
                results.append(('Default user', False, 'users table missing'))

            conn.close()
        except Exception as e:
            results.append(('DB checks', False, str(e)))
    else:
        results.append(('DB integrity', False, 'DB file missing'))
        results.append(('Migrations', False, 'DB file missing'))
        results.append(('Default user', False, 'DB file missing'))

    pass_count = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    return results, pass_count, total


def write_report(results, pass_count, total):
    """Write a timestamped report file."""
    now = datetime.now()
    import platform
    report_name = f'usb_smoke_report_{now.strftime("%Y%m%d_%H%M%S")}.txt'
    report_path = os.path.join(ROOT, 'tools', report_name)

    lines = [
        'CareCompanion USB Deployment Smoke Test',
        '=' * 40,
        f'Timestamp: {now.strftime("%Y-%m-%d %H:%M:%S")}',
        f'Host: {platform.node()}',
        '',
    ]

    for name, ok, detail in results:
        icon = '✓' if ok else '✗'
        lines.append(f'{icon} {name}: {detail}')

    action_items = total - pass_count
    if action_items == 0:
        lines.append(f'\nRESULT: {pass_count}/{total} passed — all checks OK')
    else:
        lines.append(f'\nRESULT: {pass_count}/{total} passed — {action_items} action(s) needed')

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return report_path


def main():
    print('CareCompanion USB Deployment Smoke Test')
    print('=' * 40)

    results, pass_count, total = run_smoke_test()

    for name, ok, detail in results:
        icon = '✓' if ok else '✗'
        print(f'  {icon} {name}: {detail}')

    report_path = write_report(results, pass_count, total)
    print(f'\nReport written: {report_path}')

    if pass_count == total:
        print(f'\nRESULT: {pass_count}/{total} passed — all checks OK')
    else:
        print(f'\nRESULT: {pass_count}/{total} passed — {total - pass_count} action(s) needed')

    return pass_count == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

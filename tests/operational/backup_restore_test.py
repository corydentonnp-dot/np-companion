"""
Phase 5.2 — DB Backup / Restore Validator (final_plan.md Phase 5)

Standalone script to verify database backups are healthy and restorable.

Usage:
    python tools/backup_restore_test.py
"""

import os
import sys
import glob
import shutil
import sqlite3
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, 'data', 'carecompanion.db')
BACKUP_DIR = os.path.join(ROOT, 'data', 'backups')
RESTORE_TEMP = os.path.join(ROOT, 'data', 'carecompanion_restore_test.db')

CRITICAL_TABLES = [
    'users', 'billing_opportunity', 'billing_rule', 'patient_record',
    'monitoring_rule', 'monitoring_schedule', 'rems_tracker_entry',
    'calculator_result', 'ccm_enrollment', 'tcm_watch_entry',
    'bonus_tracker', 'documentation_phrase', 'closed_loop_status',
    'opportunity_suppression', 'immunization_series', 'communication_log',
    'billing_campaign', 'payer_coverage_matrix', 'diagnosis_revenue_profile',
    'patient_lab_results', 'patient_social_history',
]

ROW_COUNT_TABLES = ['users', 'billing_opportunity', 'patient_record']


def _find_latest_backup():
    """Return path to the most recent *.db file in data/backups/."""
    if not os.path.isdir(BACKUP_DIR):
        return None
    backups = glob.glob(os.path.join(BACKUP_DIR, '*.db'))
    if not backups:
        return None
    return max(backups, key=os.path.getmtime)


def _row_count(conn, table):
    """Return row count for a table, or -1 on error."""
    try:
        cur = conn.execute(f'SELECT COUNT(*) FROM [{table}]')
        return cur.fetchone()[0]
    except Exception:
        return -1


def verify_backup():
    """
    Verify the most recent backup.
    Returns dict with keys: pass, detail, backup_path, backup_age_hours, row_comparison.
    """
    result = {
        'pass': False,
        'detail': '',
        'backup_path': None,
        'backup_age_hours': None,
        'row_comparison': {},
    }

    backup_path = _find_latest_backup()
    if not backup_path:
        result['detail'] = 'No backup files found in data/backups/'
        return result
    result['backup_path'] = backup_path

    # Backup age
    mtime = os.path.getmtime(backup_path)
    age_hours = (time.time() - mtime) / 3600
    result['backup_age_hours'] = round(age_hours, 1)

    # Integrity check
    try:
        bk_conn = sqlite3.connect(backup_path)
        integrity = bk_conn.execute('PRAGMA integrity_check').fetchone()[0]
        if integrity != 'ok':
            result['detail'] = f'Backup integrity check failed: {integrity}'
            bk_conn.close()
            return result
    except Exception as e:
        result['detail'] = f'Cannot open backup: {e}'
        return result

    # Row count comparison
    if os.path.exists(DB_PATH):
        try:
            main_conn = sqlite3.connect(DB_PATH)
            for table in ROW_COUNT_TABLES:
                main_count = _row_count(main_conn, table)
                bk_count = _row_count(bk_conn, table)
                within_10 = True
                if main_count > 0:
                    within_10 = abs(main_count - bk_count) / main_count <= 0.10
                result['row_comparison'][table] = {
                    'main': main_count,
                    'backup': bk_count,
                    'within_10pct': within_10,
                }
            main_conn.close()
        except Exception as e:
            result['detail'] = f'Row comparison failed: {e}'
            bk_conn.close()
            return result

    bk_conn.close()

    # Warnings
    warnings = []
    if age_hours > 26:
        warnings.append(f'Backup is {age_hours:.1f}h old (>26h)')
    for t, comp in result['row_comparison'].items():
        if not comp['within_10pct']:
            warnings.append(f'{t}: main={comp["main"]} backup={comp["backup"]} (>10% drift)')

    if warnings:
        result['detail'] = 'BACKUP OK with warnings: ' + '; '.join(warnings)
    else:
        result['detail'] = 'Backup is healthy'
    result['pass'] = True
    return result


def restore_dry_run():
    """
    Copy most recent backup to temp file, verify tables, then delete.
    Returns dict with keys: pass, detail, message.
    """
    result = {'pass': False, 'detail': '', 'message': ''}

    backup_path = _find_latest_backup()
    if not backup_path:
        result['detail'] = 'No backup files found'
        result['message'] = 'RESTORE FAILED — no backup available'
        return result

    try:
        # Copy backup to temp location
        shutil.copy2(backup_path, RESTORE_TEMP)

        conn = sqlite3.connect(RESTORE_TEMP)

        # Integrity check
        integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
        if integrity != 'ok':
            result['detail'] = f'Restore copy integrity failed: {integrity}'
            result['message'] = f'RESTORE FAILED — {integrity}'
            conn.close()
            return result

        # Check all 21 critical tables
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing = {row[0] for row in cursor.fetchall()}
        missing = [t for t in CRITICAL_TABLES if t not in existing]
        if missing:
            result['detail'] = f'Missing tables: {", ".join(missing)}'
            result['message'] = f'RESTORE FAILED — {len(missing)} missing tables'
            conn.close()
            return result

        # User count
        user_count = _row_count(conn, 'users')
        if user_count <= 0:
            result['detail'] = 'No users in restore copy'
            result['message'] = 'RESTORE FAILED — no users found'
            conn.close()
            return result

        conn.close()

        result['pass'] = True
        result['detail'] = f'{len(CRITICAL_TABLES)} tables present, {user_count} user(s), integrity ok'
        result['message'] = 'RESTORE VIABLE — backup is sound'

    except Exception as e:
        result['detail'] = str(e)
        result['message'] = f'RESTORE FAILED — {e}'

    finally:
        # Always clean up temp file
        if os.path.exists(RESTORE_TEMP):
            try:
                os.remove(RESTORE_TEMP)
            except Exception:
                pass

    return result


def write_report(verify_result, restore_result):
    """Write console-style report to tools/backup_check_report.txt."""
    report_path = os.path.join(ROOT, 'tools', 'backup_check_report.txt')
    lines = [
        'CareCompanion Backup/Restore Validation',
        '=' * 40,
        f'Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        '',
        '— Backup Verification —',
        f'  Path: {verify_result.get("backup_path", "N/A")}',
        f'  Age: {verify_result.get("backup_age_hours", "N/A")}h',
        f'  Result: {"PASS" if verify_result["pass"] else "FAIL"} — {verify_result["detail"]}',
    ]

    if verify_result.get('row_comparison'):
        lines.append('  Row Comparison:')
        for table, comp in verify_result['row_comparison'].items():
            icon = '✓' if comp['within_10pct'] else '✗'
            lines.append(f'    {icon} {table}: main={comp["main"]} backup={comp["backup"]}')

    lines.extend([
        '',
        '— Restore Dry Run —',
        f'  {restore_result["message"]}',
        f'  Detail: {restore_result["detail"]}',
    ])

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return report_path


def main():
    print('CareCompanion Backup/Restore Validation')
    print('=' * 40)

    print('\n— Backup Verification —')
    verify_result = verify_backup()
    icon = '✓' if verify_result['pass'] else '✗'
    print(f'  {icon} {verify_result["detail"]}')
    if verify_result.get('backup_age_hours') is not None:
        print(f'  Age: {verify_result["backup_age_hours"]}h')
    for table, comp in verify_result.get('row_comparison', {}).items():
        ti = '✓' if comp['within_10pct'] else '✗'
        print(f'  {ti} {table}: main={comp["main"]} backup={comp["backup"]}')

    print('\n— Restore Dry Run —')
    restore_result = restore_dry_run()
    icon = '✓' if restore_result['pass'] else '✗'
    print(f'  {icon} {restore_result["message"]}')
    print(f'    {restore_result["detail"]}')

    report_path = write_report(verify_result, restore_result)
    print(f'\nReport: {report_path}')

    both_pass = verify_result['pass'] and restore_result['pass']
    return both_pass


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

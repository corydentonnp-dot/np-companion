"""
CareCompanion -- Database Integrity Check
scripts/db_integrity_check.py

Validates database schema and data integrity:
- All expected tables exist
- Foreign key constraints are valid
- Required NOT NULL columns have no NULLs
- No orphaned records in key relationship tables
- Demo data integrity (if seeded)

Usage:
    venv\\Scripts\\python.exe scripts/db_integrity_check.py

Exit codes:
    0 = all checks pass
    1 = one or more checks failed
"""

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Tables that must exist for the app to function
REQUIRED_TABLES = [
    'users',
    'patient_records',
    'patient_medications',
    'patient_diagnoses',
    'patient_allergies',
    'patient_immunizations',
    'patient_vitals',
    'billing_opportunities',
    'billing_rules',
    'care_gaps',
    'care_gap_rules',
    'schedules',
    'time_logs',
    'bonus_tracker',
    'order_sets',
    'lab_tracks',
    'inbox_snapshots',
    'oncall_notes',
    'ccm_enrollments',
    'tcm_watch_entries',
    'monitoring_rules',
    'monitoring_schedules',
    'notifications',
    'calculator_results',
    'communication_logs',
]

# Columns that must never be NULL (table, column)
NOT_NULL_CHECKS = [
    ('users', 'username'),
    ('users', 'password_hash'),
    ('users', 'role'),
    ('patient_records', 'mrn'),
    ('billing_opportunities', 'opportunity_code'),
    ('care_gaps', 'gap_type'),
]

# Foreign key relationships to validate (child_table, child_fk, parent_table)
FK_CHECKS = [
    ('billing_opportunities', 'user_id', 'users'),
    ('care_gaps', 'patient_id', 'patient_records'),
    ('time_logs', 'user_id', 'users'),
    ('ccm_enrollments', 'user_id', 'users'),
]


def main():
    start = time.time()
    passed = []
    failed = []
    warnings = []

    from app import create_app
    app = create_app()

    with app.app_context():
        from models import db

        inspector = db.inspect(db.engine)
        existing_tables = set(inspector.get_table_names())

        # ------------------------------------------------------------------
        # 1. Required tables exist
        # ------------------------------------------------------------------
        print('[1/5] Checking required tables...')
        missing_tables = []
        for table in REQUIRED_TABLES:
            if table not in existing_tables:
                missing_tables.append(table)

        if missing_tables:
            failed.append(f'Missing tables: {", ".join(missing_tables)}')
        else:
            passed.append(f'All {len(REQUIRED_TABLES)} required tables exist')

        # ------------------------------------------------------------------
        # 2. NOT NULL constraint checks
        # ------------------------------------------------------------------
        print('[2/5] Checking NOT NULL constraints...')
        for table, column in NOT_NULL_CHECKS:
            if table not in existing_tables:
                continue
            try:
                result = db.session.execute(
                    db.text(f'SELECT COUNT(*) FROM "{table}" WHERE "{column}" IS NULL')
                ).scalar()
                if result > 0:
                    failed.append(f'{table}.{column}: {result} NULL values found')
                else:
                    passed.append(f'{table}.{column}: no NULLs')
            except Exception as e:
                failed.append(f'{table}.{column} check error: {e}')

        # ------------------------------------------------------------------
        # 3. Foreign key integrity
        # ------------------------------------------------------------------
        print('[3/5] Checking foreign key integrity...')
        for child_table, child_fk, parent_table in FK_CHECKS:
            if child_table not in existing_tables or parent_table not in existing_tables:
                continue
            try:
                # Find child rows that reference non-existent parent rows
                query = db.text(
                    f'SELECT COUNT(*) FROM "{child_table}" c '
                    f'WHERE c."{child_fk}" IS NOT NULL '
                    f'AND c."{child_fk}" NOT IN (SELECT id FROM "{parent_table}")'
                )
                orphans = db.session.execute(query).scalar()
                if orphans > 0:
                    failed.append(
                        f'{child_table}.{child_fk} -> {parent_table}: '
                        f'{orphans} orphaned records'
                    )
                else:
                    passed.append(f'{child_table}.{child_fk} -> {parent_table}: OK')
            except Exception as e:
                warnings.append(f'FK check {child_table}.{child_fk}: {e}')

        # ------------------------------------------------------------------
        # 4. Demo data integrity (if seeded)
        # ------------------------------------------------------------------
        print('[4/5] Checking demo data...')
        try:
            count = db.session.execute(
                db.text("SELECT COUNT(*) FROM patient_records WHERE mrn LIKE '9000%'")
            ).scalar()
            if count > 0:
                passed.append(f'Demo patients found: {count}')
                # Spot-check key patient
                exists = db.session.execute(
                    db.text("SELECT COUNT(*) FROM patient_records WHERE mrn = '90001'")
                ).scalar()
                if exists:
                    passed.append('Key demo patient 90001 (Margaret Wilson) exists')
                else:
                    warnings.append('Demo patient 90001 missing -- reseed may be needed')
            else:
                warnings.append('No demo patients found -- run scripts/seed_test_data.py')
        except Exception as e:
            warnings.append(f'Demo data check: {e}')

        # ------------------------------------------------------------------
        # 5. Table row counts (informational)
        # ------------------------------------------------------------------
        print('[5/5] Table row counts...')
        try:
            print('\n  Table Row Counts:')
            for table in sorted(existing_tables):
                count = db.session.execute(
                    db.text(f'SELECT COUNT(*) FROM "{table}"')
                ).scalar()
                if count > 0:
                    print(f'    {table}: {count}')
        except Exception as e:
            warnings.append(f'Row count scan: {e}')

    # Summary
    elapsed = time.time() - start
    print('\n' + '=' * 60)
    print(f'DB INTEGRITY CHECK COMPLETE ({elapsed:.1f}s)')
    print(f'PASSED: {len(passed)} | FAILED: {len(failed)} | WARNINGS: {len(warnings)}')
    print('=' * 60)

    for p in passed:
        print(f'  PASS  {p}')
    for w in warnings:
        print(f'  WARN  {w}')
    for f in failed:
        print(f'  FAIL  {f}')

    if not failed:
        print('\nDatabase integrity OK.')
    else:
        print(f'\n{len(failed)} integrity issue(s) found.')

    return 0 if not failed else 1


if __name__ == '__main__':
    sys.exit(main())

"""
Migration: Add patient_sex column to patient_records table.

Run once:  python migrate_add_patient_sex.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')


def migrate():
    if not os.path.exists(DB_PATH):
        print(f'Database not found at {DB_PATH} — will be created on first run.')
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check if column already exists
    cur.execute("PRAGMA table_info(patient_records)")
    columns = [row[1] for row in cur.fetchall()]

    if 'patient_sex' not in columns:
        cur.execute("ALTER TABLE patient_records ADD COLUMN patient_sex TEXT DEFAULT ''")
        conn.commit()
        print('Added patient_sex column to patient_records.')
    else:
        print('patient_sex column already exists — no action needed.')

    # Also normalize any YYYYMMDD DOBs to YYYY-MM-DD
    cur.execute("""
        UPDATE patient_records
        SET patient_dob = substr(patient_dob,1,4) || '-' || substr(patient_dob,5,2) || '-' || substr(patient_dob,7,2)
        WHERE length(patient_dob) = 8
          AND patient_dob NOT LIKE '%-%'
          AND patient_dob GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'
    """)
    fixed = cur.rowcount
    conn.commit()
    if fixed:
        print(f'Normalized {fixed} DOB(s) from YYYYMMDD to YYYY-MM-DD.')

    conn.close()
    print('Migration complete.')


if __name__ == '__main__':
    migrate()

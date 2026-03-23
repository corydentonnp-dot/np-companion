"""
Migration: Add is_archived column to lab_tracks and patient_specialists tables.

HIPAA requirement: Clinical records must be soft-deleted (is_archived=True)
rather than hard-deleted. This migration adds the flag columns.

Run:  python migrations/migrate_add_is_archived.py
"""

import sqlite3
import os
import sys

# Resolve path to the database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'carecompanion.db')


def migrate():
    if not os.path.exists(DB_PATH):
        print(f'Database not found at {DB_PATH}')
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    changes = 0

    # --- lab_tracks.is_archived -------------------------------------------
    cur.execute("PRAGMA table_info(lab_tracks)")
    cols = [row[1] for row in cur.fetchall()]
    if 'is_archived' not in cols:
        cur.execute(
            "ALTER TABLE lab_tracks ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0"
        )
        print('  Added lab_tracks.is_archived')
        changes += 1
    else:
        print('  lab_tracks.is_archived already exists — skipped')

    # --- patient_specialists.is_archived ----------------------------------
    cur.execute("PRAGMA table_info(patient_specialists)")
    cols = [row[1] for row in cur.fetchall()]
    if 'is_archived' not in cols:
        cur.execute(
            "ALTER TABLE patient_specialists ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0"
        )
        print('  Added patient_specialists.is_archived')
        changes += 1
    else:
        print('  patient_specialists.is_archived already exists — skipped')

    conn.commit()
    conn.close()
    print(f'Migration complete — {changes} column(s) added.')


if __name__ == '__main__':
    migrate()

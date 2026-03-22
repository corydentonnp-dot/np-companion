"""
Migration — Add sharing/ownership columns to result_templates (Phase 7, F19a).

Adds:
  - user_id (INTEGER, nullable — NULL = system/seed template)
  - is_shared (BOOLEAN, default 0)
  - copied_from_id (INTEGER, nullable — FK reference for fork lineage)
  - legal_reviewed (BOOLEAN, default 0)
  - legal_reviewed_at (DATETIME, nullable)
"""

import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'carecompanion.db')


def migrate():
    if not os.path.exists(DB_PATH):
        print(f'[SKIP] Database not found at {DB_PATH}')
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(result_templates)")
    columns = [row[1] for row in cur.fetchall()]

    new_cols = [
        ('user_id', 'INTEGER'),
        ('is_shared', 'BOOLEAN DEFAULT 0'),
        ('copied_from_id', 'INTEGER'),
        ('legal_reviewed', 'BOOLEAN DEFAULT 0'),
        ('legal_reviewed_at', 'DATETIME'),
    ]

    for col_name, col_type in new_cols:
        if col_name not in columns:
            cur.execute(f"ALTER TABLE result_templates ADD COLUMN {col_name} {col_type}")
            print(f'[OK] Added {col_name} column to result_templates')
        else:
            print(f'[SKIP] {col_name} column already exists')

    conn.commit()
    conn.close()
    print('[DONE] Template sharing migration complete')


if __name__ == '__main__':
    migrate()

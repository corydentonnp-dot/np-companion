"""
Migration: Add reviewed_at / reviewed_by columns to medication_entries table.
Supports F10d Guideline Review Admin Page — tracks provider review of flagged meds.
Idempotent — safe to run multiple times.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')

COLUMNS = [
    ("reviewed_at",  "DATETIME"),
    ("reviewed_by",  "INTEGER"),
]


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(medication_entries)")
    existing = {row[1] for row in cursor.fetchall()}

    added = []
    for col_name, col_type in COLUMNS:
        if col_name not in existing:
            cursor.execute(
                f"ALTER TABLE medication_entries ADD COLUMN {col_name} {col_type}"
            )
            added.append(col_name)

    conn.commit()
    conn.close()

    if added:
        print(f"Added columns: {', '.join(added)}")
    else:
        print("All review columns already exist.")


if __name__ == '__main__':
    migrate()

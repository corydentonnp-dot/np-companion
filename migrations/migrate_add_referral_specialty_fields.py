"""
Migration: Add specialty_fields column to referral_letter table.
Supports F27a Specialty-Specific Referral Templates — stores per-specialty field values as JSON.
Idempotent — safe to run multiple times.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')

COLUMNS = [
    ("specialty_fields", "TEXT"),
]


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(referral_letter)")
    existing = {row[1] for row in cursor.fetchall()}

    added = []
    for col_name, col_type in COLUMNS:
        if col_name not in existing:
            cursor.execute(
                f"ALTER TABLE referral_letter ADD COLUMN {col_name} {col_type}"
            )
            added.append(col_name)

    conn.commit()
    conn.close()

    if added:
        print(f"Added columns: {', '.join(added)}")
    else:
        print("All referral specialty columns already exist.")


if __name__ == '__main__':
    migrate()

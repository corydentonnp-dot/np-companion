"""
Migration: Add awv_checklist column to time_logs table.
Supports F16a AWV Interactive Checklist — stores per-session checklist progress as JSON.
Idempotent — safe to run multiple times.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')

COLUMNS = [
    ("awv_checklist", "TEXT"),
]


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(time_logs)")
    existing = {row[1] for row in cursor.fetchall()}

    added = []
    for col_name, col_type in COLUMNS:
        if col_name not in existing:
            cursor.execute(
                f"ALTER TABLE time_logs ADD COLUMN {col_name} {col_type}"
            )
            added.append(col_name)

    conn.commit()
    conn.close()

    if added:
        print(f"Added columns: {', '.join(added)}")
    else:
        print("All AWV checklist columns already exist.")


if __name__ == '__main__':
    migrate()

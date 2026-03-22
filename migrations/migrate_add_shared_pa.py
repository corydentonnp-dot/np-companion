"""
Migration: Add shared PA library columns to prior_authorization table (F26a / Phase 22.8).
Idempotent — safe to run multiple times.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')

COLUMNS = [
    ("is_shared",        "BOOLEAN DEFAULT 0"),
    ("shared_by_user_id","INTEGER"),
    ("forked_from_id",   "INTEGER"),
    ("approval_rate",    "REAL"),
]

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(prior_authorization)")
    existing = {row[1] for row in cursor.fetchall()}

    added = []
    for col_name, col_type in COLUMNS:
        if col_name not in existing:
            cursor.execute(f"ALTER TABLE prior_authorization ADD COLUMN {col_name} {col_type}")
            added.append(col_name)

    conn.commit()
    conn.close()

    if added:
        print(f"Added columns: {', '.join(added)}")
    else:
        print("All shared PA columns already exist.")

if __name__ == '__main__':
    migrate()

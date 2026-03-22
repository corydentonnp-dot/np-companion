"""
Migration: Add escalating alert columns to notifications table (F21b / Phase 22.6).
Idempotent — safe to run multiple times.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')

COLUMNS = [
    ("is_critical",       "BOOLEAN DEFAULT 0"),
    ("acknowledged_at",   "DATETIME"),
    ("escalation_count",  "INTEGER DEFAULT 0"),
    ("last_escalated_at", "DATETIME"),
]

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(notifications)")
    existing = {row[1] for row in cursor.fetchall()}

    added = []
    for col_name, col_type in COLUMNS:
        if col_name not in existing:
            cursor.execute(f"ALTER TABLE notifications ADD COLUMN {col_name} {col_type}")
            added.append(col_name)

    conn.commit()
    conn.close()

    if added:
        print(f"Added columns: {', '.join(added)}")
    else:
        print("All escalation columns already exist.")

if __name__ == '__main__':
    migrate()

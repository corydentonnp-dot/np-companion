"""
CareCompanion — Migration: Add recurring message columns (F18a)

Adds is_recurring, recurrence_interval_days, recurrence_end_date,
and parent_message_id to the delayed_messages table.

Idempotent — safe to re-run.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH} — skipping migration.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    columns = {
        'is_recurring': 'BOOLEAN NOT NULL DEFAULT 0',
        'recurrence_interval_days': 'INTEGER',
        'recurrence_end_date': 'DATETIME',
        'parent_message_id': 'INTEGER',
    }

    existing = {
        row[1] for row in cursor.execute(
            "PRAGMA table_info(delayed_messages)"
        ).fetchall()
    }

    for col_name, col_def in columns.items():
        if col_name not in existing:
            cursor.execute(
                f"ALTER TABLE delayed_messages ADD COLUMN {col_name} {col_def}"
            )
            print(f"  Added column delayed_messages.{col_name}")
        else:
            print(f"  Column delayed_messages.{col_name} already exists")

    conn.commit()
    conn.close()
    print("Migration complete: recurring message columns.")


if __name__ == '__main__':
    migrate()

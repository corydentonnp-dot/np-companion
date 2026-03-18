"""
Migration: Add F12 columns to time_logs table.

Adds:
  - visit_type_source  TEXT DEFAULT ''    (F12a: 'auto' or 'manual')
  - complexity_notes   TEXT DEFAULT ''    (F12b: notes when flagged complex)

Safe to re-run — checks for existing columns before adding.
"""

import sqlite3
import os

DB_PATH = os.path.join('data', 'npcompanion.db')


def get_existing_columns(cursor, table):
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cols = get_existing_columns(cur, 'time_logs')

    added = []

    if 'visit_type_source' not in cols:
        cur.execute("ALTER TABLE time_logs ADD COLUMN visit_type_source TEXT DEFAULT ''")
        added.append('visit_type_source')

    if 'complexity_notes' not in cols:
        cur.execute("ALTER TABLE time_logs ADD COLUMN complexity_notes TEXT DEFAULT ''")
        added.append('complexity_notes')

    conn.commit()
    conn.close()

    if added:
        print(f"Added columns: {', '.join(added)}")
    else:
        print("All columns already exist — nothing to do.")


if __name__ == '__main__':
    migrate()

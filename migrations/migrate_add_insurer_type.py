"""
Migration: Add insurer_type column to patient_records table.

Run once:  python migrate_add_insurer_type.py
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

    cur.execute("PRAGMA table_info(patient_records)")
    columns = [row[1] for row in cur.fetchall()]

    if 'insurer_type' not in columns:
        cur.execute("ALTER TABLE patient_records ADD COLUMN insurer_type TEXT DEFAULT 'unknown'")
        conn.commit()
        print('Added insurer_type column to patient_records.')
    else:
        print('insurer_type column already exists — no action needed.')

    conn.close()


if __name__ == '__main__':
    migrate()

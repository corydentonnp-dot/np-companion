"""
Migration: Add cpt_code column to master_orders table.

Run once:
    venv\Scripts\python.exe migrate_add_master_order_cpt.py
"""

import sqlite3
import os

DB_PATH = os.path.join('data', 'carecompanion.db')


def migrate():
    if not os.path.exists(DB_PATH):
        print(f'Database not found at {DB_PATH} — run app.py first to create it.')
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(master_orders)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'cpt_code' in columns:
        print('Column cpt_code already exists in master_orders — nothing to do.')
    else:
        cursor.execute("ALTER TABLE master_orders ADD COLUMN cpt_code VARCHAR(20) DEFAULT ''")
        conn.commit()
        print('Added cpt_code column to master_orders table.')

    conn.close()


if __name__ == '__main__':
    migrate()

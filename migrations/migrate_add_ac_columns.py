"""
Migration: Add Amazing Charts credentials, PC password, and setup tracking columns.

Run once:  venv\Scripts\python.exe migrate_add_ac_columns.py

Adds to the 'users' table:
  - ac_username_enc    TEXT  (Fernet-encrypted Amazing Charts username)
  - ac_password_enc    TEXT  (Fernet-encrypted Amazing Charts password)
  - pc_password_enc    TEXT  (Fernet-encrypted work PC password)
  - setup_completed_at DATETIME (null until all setup tasks are done)
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')

def migrate():
    if not os.path.exists(DB_PATH):
        print(f'Database not found at {DB_PATH}. Start the app first.')
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get existing columns
    cursor.execute("PRAGMA table_info(users)")
    existing = {row[1] for row in cursor.fetchall()}

    new_columns = [
        ('ac_username_enc',    "TEXT DEFAULT ''"),
        ('ac_password_enc',    "TEXT DEFAULT ''"),
        ('pc_password_enc',    "TEXT DEFAULT ''"),
        ('setup_completed_at', "DATETIME"),
    ]

    added = 0
    for col_name, col_type in new_columns:
        if col_name not in existing:
            sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
            cursor.execute(sql)
            print(f'  Added column: {col_name}')
            added += 1
        else:
            print(f'  Column already exists: {col_name}')

    conn.commit()
    conn.close()

    if added:
        print(f'\nMigration complete — {added} column(s) added.')
    else:
        print('\nNo changes needed — all columns already exist.')


if __name__ == '__main__':
    migrate()

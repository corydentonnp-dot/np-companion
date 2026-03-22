"""
Migration: CL21 — Add email, deactivate_at columns to users; create notifications table.

Safe to run multiple times (checks before altering).
"""

import sqlite3
import os
import sys


def get_db_path():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(here, 'data', 'carecompanion.db')


def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def table_exists(cursor, table):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cursor.fetchone() is not None


def migrate():
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path} — run the app first.")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    changes = []

    # 1. Add email column to users
    if not column_exists(cur, 'users', 'email'):
        cur.execute("ALTER TABLE users ADD COLUMN email TEXT DEFAULT ''")
        changes.append('Added users.email')

    # 2. Add deactivate_at column to users
    if not column_exists(cur, 'users', 'deactivate_at'):
        cur.execute("ALTER TABLE users ADD COLUMN deactivate_at DATETIME")
        changes.append('Added users.deactivate_at')

    # 3. Create notifications table
    if not table_exists(cur, 'notifications'):
        cur.execute("""
            CREATE TABLE notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                sender_id INTEGER,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (sender_id) REFERENCES users(id)
            )
        """)
        cur.execute("CREATE INDEX ix_notifications_user_id ON notifications (user_id)")
        changes.append('Created notifications table')

    conn.commit()
    conn.close()

    if changes:
        print('CL21 migration complete:')
        for c in changes:
            print(f'  ✓ {c}')
    else:
        print('CL21 migration: nothing to do (all changes already applied).')


if __name__ == '__main__':
    migrate()

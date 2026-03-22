"""
Migration: Create practice_bookmark table for admin-managed bookmarks bar.

Run once:
    python migrate_add_bookmarks.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check if table already exists
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='practice_bookmark'"
    )
    if cur.fetchone():
        print('[practice_bookmark] Table already exists — skipping.')
    else:
        cur.execute('''
            CREATE TABLE practice_bookmark (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label VARCHAR(100) NOT NULL,
                url VARCHAR(500) NOT NULL,
                icon_url VARCHAR(500) DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                created_by INTEGER NOT NULL REFERENCES users(id),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print('[practice_bookmark] Table created.')

    conn.commit()
    conn.close()
    print('Migration complete.')


if __name__ == '__main__':
    migrate()

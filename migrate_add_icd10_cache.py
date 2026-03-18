"""
Migration: Create icd10_cache table for global ICD-10 lookup caching.

Run once:
    python migrate_add_icd10_cache.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'npcompanion.db')


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check if table already exists
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='icd10_cache'"
    )
    if cur.fetchone():
        print('[icd10_cache] Table already exists — skipping.')
    else:
        cur.execute('''
            CREATE TABLE icd10_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                diagnosis_name_lower VARCHAR(300) NOT NULL UNIQUE,
                icd10_code VARCHAR(20) NOT NULL,
                icd10_description VARCHAR(300) DEFAULT '',
                source VARCHAR(20) DEFAULT 'nih_api',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute(
            'CREATE INDEX IF NOT EXISTS ix_icd10_cache_name '
            'ON icd10_cache (diagnosis_name_lower)'
        )
        print('[icd10_cache] Table created.')

    conn.commit()
    conn.close()
    print('Migration complete.')


if __name__ == '__main__':
    migrate()

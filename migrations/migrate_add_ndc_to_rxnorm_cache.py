"""
Migration: Add ndc column to rxnorm_cache table.

Run once:
    python migrations/migrate_add_ndc_to_rxnorm_cache.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check if ndc column already exists
    cur.execute("PRAGMA table_info(rxnorm_cache)")
    columns = [row[1] for row in cur.fetchall()]

    if 'ndc' in columns:
        print('[rxnorm_cache] ndc column already exists — skipping.')
    else:
        cur.execute("ALTER TABLE rxnorm_cache ADD COLUMN ndc VARCHAR(20) DEFAULT ''")
        conn.commit()
        print('[rxnorm_cache] Added ndc column.')

    conn.close()
    print('Migration complete.')


if __name__ == '__main__':
    migrate()

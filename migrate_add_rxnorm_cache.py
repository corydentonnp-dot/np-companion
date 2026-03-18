"""
Migration: Create rxnorm_cache table and add rxnorm_cui column
to patient_medications.

Run once:
    python migrate_add_rxnorm_cache.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'npcompanion.db')


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ---- 1. Create rxnorm_cache table ----
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='rxnorm_cache'"
    )
    if cur.fetchone():
        print('[rxnorm_cache] Table already exists — skipping.')
    else:
        cur.execute('''
            CREATE TABLE rxnorm_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rxcui VARCHAR(20) NOT NULL UNIQUE,
                brand_name VARCHAR(300) DEFAULT '',
                generic_name VARCHAR(300) DEFAULT '',
                dose_strength VARCHAR(100) DEFAULT '',
                dose_form VARCHAR(100) DEFAULT '',
                route VARCHAR(100) DEFAULT '',
                tty VARCHAR(20) DEFAULT '',
                source VARCHAR(20) DEFAULT 'rxnorm_api',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute(
            'CREATE INDEX IF NOT EXISTS ix_rxnorm_cache_rxcui '
            'ON rxnorm_cache (rxcui)'
        )
        print('[rxnorm_cache] Table created.')

    # ---- 2. Add rxnorm_cui column to patient_medications ----
    cur.execute("PRAGMA table_info(patient_medications)")
    columns = [row[1] for row in cur.fetchall()]
    if 'rxnorm_cui' in columns:
        print('[patient_medications.rxnorm_cui] Column already exists — skipping.')
    else:
        cur.execute(
            "ALTER TABLE patient_medications ADD COLUMN rxnorm_cui VARCHAR(20) DEFAULT ''"
        )
        print('[patient_medications.rxnorm_cui] Column added.')

    conn.commit()
    conn.close()
    print('Migration complete.')


if __name__ == '__main__':
    migrate()

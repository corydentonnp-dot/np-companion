"""
Migration: Add VSAC Value Set Cache table
Created: 2026-03-19

Adds the vsac_value_set_cache table for storing expanded VSAC value sets.
VSAC access is enabled by the UMLS API key (approved 2026-03-19).
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "carecompanion.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if table already exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='vsac_value_set_cache'"
    )
    if cursor.fetchone():
        print("[migrate_add_vsac_cache] vsac_value_set_cache already exists — skipping")
        conn.close()
        return

    cursor.execute("""
        CREATE TABLE vsac_value_set_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            oid VARCHAR(100) NOT NULL UNIQUE,
            name VARCHAR(400) DEFAULT '',
            codes_json TEXT DEFAULT '[]',
            code_count INTEGER DEFAULT 0,
            source VARCHAR(30) DEFAULT 'vsac_api',
            cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute(
        "CREATE INDEX ix_vsac_value_set_cache_oid ON vsac_value_set_cache(oid)"
    )

    conn.commit()
    print("[migrate_add_vsac_cache] Created vsac_value_set_cache table")
    conn.close()


if __name__ == "__main__":
    migrate()

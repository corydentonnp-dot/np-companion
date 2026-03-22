"""
Migration: Add NLM Conditions Cache table
Created: 2026-03-19

Adds the nlm_conditions_cache table for storing NLM Clinical Tables
condition search results. Powers the Differential Diagnosis Widget (NEW-G).
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "carecompanion.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if table already exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='nlm_conditions_cache'"
    )
    if cursor.fetchone():
        print("[migrate_add_nlm_conditions_cache] nlm_conditions_cache already exists — skipping")
        conn.close()
        return

    cursor.execute("""
        CREATE TABLE nlm_conditions_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_term VARCHAR(300) NOT NULL UNIQUE,
            conditions JSON DEFAULT '[]',
            result_count INTEGER DEFAULT 0,
            source VARCHAR(30) DEFAULT 'nlm_conditions_api',
            cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute(
        "CREATE INDEX ix_nlm_conditions_cache_search_term ON nlm_conditions_cache(search_term)"
    )

    conn.commit()
    print("[migrate_add_nlm_conditions_cache] Created nlm_conditions_cache table")
    conn.close()


if __name__ == "__main__":
    migrate()

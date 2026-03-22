"""
Migration: Add documentation_phrase table
Phase 21.2 — Documentation Phrase Library

Idempotent: safe to run multiple times.
"""

import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "carecompanion.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check if table already exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documentation_phrase'")
    if cur.fetchone():
        print("[OK] documentation_phrase table already exists — skipping.")
        conn.close()
        return

    cur.execute("""
        CREATE TABLE documentation_phrase (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_code VARCHAR(50) NOT NULL,
            cpt_code VARCHAR(20),
            phrase_category VARCHAR(50) NOT NULL,
            phrase_title VARCHAR(200) NOT NULL,
            phrase_text TEXT NOT NULL,
            payer_specific VARCHAR(30),
            clinical_context VARCHAR(200),
            required_elements TEXT,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            is_customized BOOLEAN NOT NULL DEFAULT 0
        )
    """)

    cur.execute("CREATE INDEX ix_documentation_phrase_opportunity_code ON documentation_phrase (opportunity_code)")

    conn.commit()
    conn.close()
    print("[OK] documentation_phrase table created.")


if __name__ == "__main__":
    migrate()

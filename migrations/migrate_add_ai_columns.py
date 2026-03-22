"""
Migration — Add AI assistant columns to users table.

Columns added:
  ai_api_key_enc  TEXT    — Fernet-encrypted API key
  ai_provider     TEXT    — 'openai', 'anthropic', 'xai'
  ai_enabled      BOOLEAN — whether user can use AI
  ai_hipaa_acknowledged BOOLEAN — HIPAA acknowledgment flag

Also sets ai_enabled=True for existing admin and provider users.

Run:  python migrate_add_ai_columns.py
"""

import sqlite3
import os
from utils.paths import get_db_path

def migrate():
    db_path = get_db_path()
    if not os.path.isfile(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Get existing column names
    cur.execute("PRAGMA table_info(users)")
    existing = {row[1] for row in cur.fetchall()}

    new_cols = [
        ("ai_api_key_enc",       "TEXT DEFAULT ''"),
        ("ai_provider",          "TEXT DEFAULT ''"),
        ("ai_enabled",           "BOOLEAN DEFAULT 0"),
        ("ai_hipaa_acknowledged","BOOLEAN DEFAULT 0"),
    ]

    for col_name, col_def in new_cols:
        if col_name not in existing:
            cur.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
            print(f"  Added column: {col_name}")
        else:
            print(f"  Column already exists: {col_name}")

    # Enable AI for existing admin and provider users by default
    cur.execute("UPDATE users SET ai_enabled = 1 WHERE role IN ('admin', 'provider') AND ai_enabled = 0")
    updated = cur.rowcount
    if updated:
        print(f"  Enabled AI for {updated} existing admin/provider user(s)")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()

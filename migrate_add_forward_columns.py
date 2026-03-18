"""
Migration: Add forwarded_to and forwarded_at columns to oncall_notes table.

Usage:
    venv\\Scripts\\python.exe migrate_add_forward_columns.py
"""

import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

db_path = config.DATABASE_PATH
if not os.path.isabs(db_path):
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(oncall_notes)")
cols = [row[1] for row in cursor.fetchall()]

added = []
if 'forwarded_to' not in cols:
    cursor.execute("ALTER TABLE oncall_notes ADD COLUMN forwarded_to INTEGER REFERENCES users(id)")
    added.append('forwarded_to')

if 'forwarded_at' not in cols:
    cursor.execute("ALTER TABLE oncall_notes ADD COLUMN forwarded_at DATETIME")
    added.append('forwarded_at')

conn.commit()
conn.close()

if added:
    print(f"Added columns: {', '.join(added)}")
else:
    print("Columns already exist — nothing to do.")

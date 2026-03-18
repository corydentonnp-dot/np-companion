"""
Migration: Add claimed_by and claimed_at columns to patient_records table.

Usage:
    venv\\Scripts\\python.exe migrate_add_claim_columns.py
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

# Check existing columns
cursor.execute("PRAGMA table_info(patient_records)")
cols = [row[1] for row in cursor.fetchall()]

added = []
if 'claimed_by' not in cols:
    cursor.execute("ALTER TABLE patient_records ADD COLUMN claimed_by INTEGER REFERENCES users(id)")
    added.append('claimed_by')

if 'claimed_at' not in cols:
    cursor.execute("ALTER TABLE patient_records ADD COLUMN claimed_at DATETIME")
    added.append('claimed_at')

conn.commit()
conn.close()

if added:
    print(f"Added columns: {', '.join(added)}")
else:
    print("Columns already exist — nothing to do.")

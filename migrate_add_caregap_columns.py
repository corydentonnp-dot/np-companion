"""
One-time migration: add new columns to care_gaps and create care_gap_rules table.
Run: venv\Scripts\python.exe migrate_add_caregap_columns.py

This migration supports the F15 Care Gap Tracker feature (CL16).
"""
import sqlite3

DB_PATH = 'data/npcompanion.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ---- care_gaps table: add new columns ----
cursor.execute('PRAGMA table_info(care_gaps)')
existing_cols = {row[1] for row in cursor.fetchall()}
print('Existing care_gaps columns:', sorted(existing_cols))

new_cols = [
    ('patient_name',  'VARCHAR(200) DEFAULT ""'),
    ('gap_name',      'VARCHAR(200) DEFAULT ""'),
    ('description',   'TEXT DEFAULT ""'),
    ('status',        'VARCHAR(30) DEFAULT "open"'),
    ('addressed_by',  'INTEGER'),
    ('updated_at',    'DATETIME'),
]
for col_name, col_type in new_cols:
    if col_name not in existing_cols:
        cursor.execute(f'ALTER TABLE care_gaps ADD COLUMN {col_name} {col_type}')
        print(f'  + Added care_gaps.{col_name}')
    else:
        print(f'  = care_gaps.{col_name} already exists')

# ---- care_gap_rules table: create if not exists ----
print()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='care_gap_rules'")
if cursor.fetchone():
    print('care_gap_rules table already exists')
else:
    cursor.execute('''
        CREATE TABLE care_gap_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gap_type VARCHAR(80) NOT NULL UNIQUE,
            gap_name VARCHAR(200) DEFAULT '',
            description TEXT DEFAULT '',
            criteria_json TEXT DEFAULT '{}',
            interval_days INTEGER DEFAULT 365,
            billing_code_pair VARCHAR(80) DEFAULT '',
            documentation_template TEXT DEFAULT '',
            source VARCHAR(20) DEFAULT 'hardcoded',
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME,
            updated_at DATETIME
        )
    ''')
    print('  + Created care_gap_rules table')

conn.commit()
conn.close()
print()
print('Migration complete!')

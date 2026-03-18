"""
One-time migration: add NetPractice columns to users and schedules tables.
Run: venv\Scripts\python.exe migrate_add_np_columns.py
"""
import sqlite3

DB_PATH = 'data/npcompanion.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ---- Users table: add NP credential + nav step columns ----
cursor.execute('PRAGMA table_info(users)')
existing_user_cols = {row[1] for row in cursor.fetchall()}
print('Existing user columns:', sorted(existing_user_cols))

user_new = [
    ('np_username_enc', 'TEXT DEFAULT ""'),
    ('np_password_enc',  'TEXT DEFAULT ""'),
    ('np_provider_name', 'VARCHAR(200) DEFAULT ""'),
    ('nav_steps',        'TEXT DEFAULT "[]"'),
]
for col_name, col_type in user_new:
    if col_name not in existing_user_cols:
        cursor.execute(f'ALTER TABLE users ADD COLUMN {col_name} {col_type}')
        print(f'  + Added users.{col_name}')
    else:
        print(f'  = users.{col_name} already exists')

# ---- Schedules table: add detail-page columns ----
cursor.execute('PRAGMA table_info(schedules)')
existing_sched_cols = {row[1] for row in cursor.fetchall()}
print()
print('Existing schedule columns:', sorted(existing_sched_cols))

sched_new = [
    ('patient_mrn',  'VARCHAR(20) DEFAULT ""'),
    ('patient_phone','VARCHAR(30) DEFAULT ""'),
    ('reason',       'VARCHAR(300) DEFAULT ""'),
    ('units',        'INTEGER DEFAULT 1'),
    ('location',     'VARCHAR(100) DEFAULT ""'),
    ('comment',      'VARCHAR(500) DEFAULT ""'),
    ('entered_by',   'VARCHAR(100) DEFAULT ""'),
]
for col_name, col_type in sched_new:
    if col_name not in existing_sched_cols:
        cursor.execute(f'ALTER TABLE schedules ADD COLUMN {col_name} {col_type}')
        print(f'  + Added schedules.{col_name}')
    else:
        print(f'  = schedules.{col_name} already exists')

conn.commit()
conn.close()
print()
print('Migration complete!')

"""
One-time migration: Phase 4 schema additions.
Run: venv\Scripts\python.exe migrate_phase4_columns.py

Adds:
  - master_orders.is_common (BOOLEAN)
  - notifications.scheduled_for (DATETIME)
  - notifications.template_name (VARCHAR(80))
  - users.deactivate_at (DATETIME) — if missing
  - users.email (VARCHAR(200)) — if missing
"""
import sqlite3

DB_PATH = 'data/carecompanion.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


def add_column_if_missing(table, col_name, col_type):
    cursor.execute(f'PRAGMA table_info({table})')
    existing = {row[1] for row in cursor.fetchall()}
    if col_name not in existing:
        cursor.execute(f'ALTER TABLE {table} ADD COLUMN {col_name} {col_type}')
        print(f'  + Added {table}.{col_name}')
    else:
        print(f'  = {table}.{col_name} already exists')


print('--- master_orders ---')
add_column_if_missing('master_orders', 'is_common', 'BOOLEAN DEFAULT 0')

print('\n--- notifications ---')
add_column_if_missing('notifications', 'scheduled_for', 'DATETIME')
add_column_if_missing('notifications', 'template_name', 'VARCHAR(80) DEFAULT ""')

print('\n--- users ---')
add_column_if_missing('users', 'deactivate_at', 'DATETIME')
add_column_if_missing('users', 'email', 'VARCHAR(200) DEFAULT ""')

conn.commit()
conn.close()
print('\nPhase 4 migration complete.')

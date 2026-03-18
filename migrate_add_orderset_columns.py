"""
One-time migration: add Feature 8 columns to order_sets table
and create new tables (master_orders, order_set_versions,
order_executions, order_execution_items).

Run: venv\Scripts\python.exe migrate_add_orderset_columns.py
"""
import sqlite3

DB_PATH = 'data/npcompanion.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ---- order_sets table: add F8a/F8b columns ----
cursor.execute('PRAGMA table_info(order_sets)')
existing_cols = {row[1] for row in cursor.fetchall()}
print('Existing order_sets columns:', sorted(existing_cols))

new_cols = [
    ('is_retracted',    'BOOLEAN DEFAULT 0'),
    ('shared_by_user_id', 'INTEGER'),
    ('forked_from_id',  'INTEGER'),
    ('version',         'INTEGER DEFAULT 1'),
]
for col_name, col_type in new_cols:
    if col_name not in existing_cols:
        cursor.execute(f'ALTER TABLE order_sets ADD COLUMN {col_name} {col_type}')
        print(f'  + Added order_sets.{col_name}')
    else:
        print(f'  = order_sets.{col_name} already exists')

# ---- Create master_orders table ----
cursor.execute("""
CREATE TABLE IF NOT EXISTS master_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_name VARCHAR(200) NOT NULL UNIQUE,
    order_tab VARCHAR(100) DEFAULT '',
    order_label VARCHAR(200) DEFAULT '',
    category VARCHAR(100) DEFAULT '',
    created_at DATETIME
)
""")
print('  + master_orders table OK')

# ---- Create order_set_versions table ----
cursor.execute("""
CREATE TABLE IF NOT EXISTS order_set_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    orderset_id INTEGER NOT NULL REFERENCES order_sets(id),
    version_number INTEGER NOT NULL,
    snapshot_json TEXT NOT NULL,
    saved_at DATETIME,
    saved_by_user_id INTEGER NOT NULL REFERENCES users(id)
)
""")
print('  + order_set_versions table OK')

# ---- Create order_executions table ----
cursor.execute("""
CREATE TABLE IF NOT EXISTS order_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    orderset_id INTEGER NOT NULL REFERENCES order_sets(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'in_progress',
    total_items INTEGER DEFAULT 0,
    completed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    pre_screenshot VARCHAR(400) DEFAULT '',
    error_message TEXT DEFAULT '',
    started_at DATETIME,
    finished_at DATETIME
)
""")
print('  + order_executions table OK')

# ---- Create order_execution_items table ----
cursor.execute("""
CREATE TABLE IF NOT EXISTS order_execution_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id INTEGER NOT NULL REFERENCES order_executions(id),
    order_name VARCHAR(200) NOT NULL,
    order_tab VARCHAR(100) DEFAULT '',
    order_label VARCHAR(200) DEFAULT '',
    sort_order INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    error_screenshot VARCHAR(400) DEFAULT '',
    error_message TEXT DEFAULT ''
)
""")
print('  + order_execution_items table OK')

conn.commit()
conn.close()
print()
print('Feature 8 migration complete!')

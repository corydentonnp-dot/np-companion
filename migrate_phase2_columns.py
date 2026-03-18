"""
One-time migration: add Phase 2 columns to time_logs table.
Run: venv\\Scripts\\python.exe migrate_phase2_columns.py
"""
import sqlite3

DB_PATH = 'data/npcompanion.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ---- time_logs table: add idle-tracking and manual-entry columns ----
cursor.execute('PRAGMA table_info(time_logs)')
existing_cols = {row[1] for row in cursor.fetchall()}
print('Existing time_logs columns:', sorted(existing_cols))

new_cols = [
    ('total_idle_seconds', 'INTEGER DEFAULT 0'),
    ('manual_entry',       'BOOLEAN DEFAULT 0'),
]
for col_name, col_type in new_cols:
    if col_name not in existing_cols:
        cursor.execute(f'ALTER TABLE time_logs ADD COLUMN {col_name} {col_type}')
        print(f'  + Added time_logs.{col_name}')
    else:
        print(f'  = time_logs.{col_name} already exists')

# ---- Create patient_vitals table if missing ----
cursor.execute("""
    SELECT name FROM sqlite_master
    WHERE type='table' AND name='patient_vitals'
""")
if not cursor.fetchone():
    cursor.execute("""
        CREATE TABLE patient_vitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mrn VARCHAR(20) NOT NULL,
            vital_name VARCHAR(100) NOT NULL,
            vital_value VARCHAR(100),
            vital_unit VARCHAR(50) DEFAULT '',
            measured_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    cursor.execute('CREATE INDEX ix_patient_vitals_user_id ON patient_vitals(user_id)')
    cursor.execute('CREATE INDEX ix_patient_vitals_mrn ON patient_vitals(mrn)')
    print('  + Created patient_vitals table')
else:
    print('  = patient_vitals table already exists')

# ---- Create patient_records table if missing ----
cursor.execute("""
    SELECT name FROM sqlite_master
    WHERE type='table' AND name='patient_records'
""")
if not cursor.fetchone():
    cursor.execute("""
        CREATE TABLE patient_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mrn VARCHAR(20) NOT NULL,
            patient_name VARCHAR(200) DEFAULT '',
            patient_dob VARCHAR(20) DEFAULT '',
            last_xml_parsed DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    cursor.execute('CREATE INDEX ix_patient_records_user_id ON patient_records(user_id)')
    cursor.execute('CREATE INDEX ix_patient_records_mrn ON patient_records(mrn)')
    print('  + Created patient_records table')
else:
    print('  = patient_records table already exists')

conn.commit()
conn.close()
print()
print('Phase 2 migration complete!')

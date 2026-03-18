"""
One-time migration: add PatientSpecialist table and diagnosis_category column.
Run: venv\\Scripts\\python.exe migrate_add_chart_columns.py
"""
import sqlite3

DB_PATH = 'data/npcompanion.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ---- PatientDiagnosis: add diagnosis_category column ----
cursor.execute('PRAGMA table_info(patient_diagnoses)')
existing_cols = {row[1] for row in cursor.fetchall()}

if 'diagnosis_category' not in existing_cols:
    cursor.execute('ALTER TABLE patient_diagnoses ADD COLUMN diagnosis_category VARCHAR(20) DEFAULT "chronic"')
    print('  + Added patient_diagnoses.diagnosis_category')
else:
    print('  = patient_diagnoses.diagnosis_category already exists')

# ---- PatientSpecialist table ----
cursor.execute("""
    SELECT name FROM sqlite_master
    WHERE type='table' AND name='patient_specialists'
""")
if not cursor.fetchone():
    cursor.execute("""
        CREATE TABLE patient_specialists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mrn VARCHAR(20) NOT NULL,
            specialty VARCHAR(200) NOT NULL,
            provider_name VARCHAR(200) DEFAULT '',
            phone VARCHAR(50) DEFAULT '',
            fax VARCHAR(50) DEFAULT '',
            notes TEXT DEFAULT '',
            last_visit DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute('CREATE INDEX ix_patient_specialists_mrn ON patient_specialists(mrn)')
    print('  + Created patient_specialists table')
else:
    print('  = patient_specialists table already exists')

# ---- PatientRecord: add claimed_by column if missing ----
cursor.execute('PRAGMA table_info(patient_records)')
pr_cols = {row[1] for row in cursor.fetchall()}

if 'claimed_by' not in pr_cols:
    cursor.execute('ALTER TABLE patient_records ADD COLUMN claimed_by INTEGER')
    print('  + Added patient_records.claimed_by')
else:
    print('  = patient_records.claimed_by already exists')

conn.commit()
conn.close()
print()
print('Chart widget migration complete!')

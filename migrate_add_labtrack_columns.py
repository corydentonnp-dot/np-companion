"""
One-time migration: add Feature 11 columns to lab_tracks table
and create the lab_panels table.

Run: venv\Scripts\python.exe migrate_add_labtrack_columns.py
"""
import json
import sqlite3

DB_PATH = 'data/npcompanion.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ---- lab_tracks table: add F11b/F11d columns ----
cursor.execute('PRAGMA table_info(lab_tracks)')
existing_cols = {row[1] for row in cursor.fetchall()}
print('Existing lab_tracks columns:', sorted(existing_cols))

new_cols = [
    ('critical_low',  'REAL'),
    ('critical_high', 'REAL'),
    ('panel_name',    'VARCHAR(80) DEFAULT ""'),
    ('is_overdue',    'BOOLEAN DEFAULT 0'),
    ('source',        'VARCHAR(20) DEFAULT "manual"'),
]
for col_name, col_type in new_cols:
    if col_name not in existing_cols:
        cursor.execute(f'ALTER TABLE lab_tracks ADD COLUMN {col_name} {col_type}')
        print(f'  + Added lab_tracks.{col_name}')
    else:
        print(f'  = lab_tracks.{col_name} already exists')

# ---- Create lab_panels table (F11d) ----
cursor.execute("""
CREATE TABLE IF NOT EXISTS lab_panels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(80) NOT NULL UNIQUE,
    components_json TEXT NOT NULL DEFAULT '[]'
)
""")
print('  + lab_panels table OK')

# ---- Seed standard panels ----
STANDARD_PANELS = {
    'BMP': ['Na', 'K', 'Cl', 'CO2', 'BUN', 'Cr', 'Glucose'],
    'CMP': ['Na', 'K', 'Cl', 'CO2', 'BUN', 'Cr', 'Glucose',
            'AST', 'ALT', 'Alk Phos', 'Total Bilirubin', 'Albumin', 'Total Protein'],
    'CBC': ['WBC', 'RBC', 'Hgb', 'Hct', 'Platelets', 'MCV', 'MCH', 'MCHC', 'RDW'],
    'Lipids': ['Total Cholesterol', 'LDL', 'HDL', 'Triglycerides'],
    'Thyroid': ['TSH', 'Free T4', 'Free T3'],
    'Diabetes': ['HbA1c', 'Fasting Glucose', 'Microalbumin'],
}
seeded = 0
for name, components in STANDARD_PANELS.items():
    cursor.execute('SELECT id FROM lab_panels WHERE name = ?', (name,))
    if not cursor.fetchone():
        cursor.execute(
            'INSERT INTO lab_panels (name, components_json) VALUES (?, ?)',
            (name, json.dumps(components))
        )
        seeded += 1
print(f'  + Seeded {seeded} standard panel(s)')

conn.commit()
conn.close()
print()
print('Feature 11 migration complete!')

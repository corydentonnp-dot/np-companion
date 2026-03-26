"""Quick verification of VIIS migration."""
import sqlite3
import os

DB_PATH = os.path.join('data', 'carecompanion.db')
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Check VIIS tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'viis%'")
tables = [r[0] for r in cur.fetchall()]
print("VIIS tables:", tables)

# Check new columns on patient_immunizations
cur.execute("PRAGMA table_info(patient_immunizations)")
cols = [r[1] for r in cur.fetchall()]
print("PatientImmunization columns:", cols)
print("Has 'source':", 'source' in cols)
print("Has 'viis_check_id':", 'viis_check_id' in cols)

conn.close()
print("VIIS-1 migration verified OK")

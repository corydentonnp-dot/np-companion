"""
Migration: Add patient_lab_results table.
Phase 15.1 — Store lab results from CDA XML (previously parsed but discarded).
Idempotent — safe to re-run.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')


def run():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS patient_lab_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mrn VARCHAR(20) NOT NULL,
            patient_mrn_hash VARCHAR(64),
            test_name VARCHAR(200) NOT NULL,
            loinc_code VARCHAR(20) DEFAULT '',
            result_value VARCHAR(100) DEFAULT '',
            result_units VARCHAR(50) DEFAULT '',
            result_date DATETIME,
            result_flag VARCHAR(20) DEFAULT 'normal',
            source VARCHAR(20) DEFAULT 'xml_import',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Add indexes
    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_lab_results_user_id ON patient_lab_results(user_id)")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_lab_results_mrn ON patient_lab_results(mrn)")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_lab_results_mrn_hash ON patient_lab_results(patient_mrn_hash)")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
    print("Migration complete: patient_lab_results table created.")


if __name__ == '__main__':
    run()

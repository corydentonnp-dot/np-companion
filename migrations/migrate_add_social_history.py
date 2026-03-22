"""
Migration: Add patient_social_history table.
Phase 15.2 — Store social history from CDA XML (previously parsed but discarded).
Idempotent — safe to re-run.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')


def run():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS patient_social_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mrn VARCHAR(20) NOT NULL,
            patient_mrn_hash VARCHAR(64),
            tobacco_status VARCHAR(20) DEFAULT 'unknown',
            tobacco_pack_years REAL,
            alcohol_status VARCHAR(20) DEFAULT 'unknown',
            alcohol_frequency VARCHAR(100) DEFAULT '',
            substance_use_status VARCHAR(100) DEFAULT '',
            sexual_activity VARCHAR(100) DEFAULT '',
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Add indexes
    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_social_history_user_id ON patient_social_history(user_id)")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_social_history_mrn ON patient_social_history(mrn)")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_social_history_mrn_hash ON patient_social_history(patient_mrn_hash)")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
    print("Migration complete: patient_social_history table created.")


if __name__ == '__main__':
    run()

"""
Migration: Add VIIS models (viis_check, viis_batch_run) and extend
patient_immunizations with source + viis_check_id columns.
Idempotent -- safe to re-run.

Phase VIIS-1 data layer.
"""
import sqlite3
import os

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db'
)


def _col_exists(cursor, table, column):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def run():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ---- VIISBatchRun table (must exist before viis_check FK) ----
    c.execute("""
        CREATE TABLE IF NOT EXISTS viis_batch_run (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            total_eligible INTEGER NOT NULL DEFAULT 0,
            total_checked INTEGER NOT NULL DEFAULT 0,
            total_found INTEGER NOT NULL DEFAULT 0,
            total_not_found INTEGER NOT NULL DEFAULT 0,
            total_errors INTEGER NOT NULL DEFAULT 0,
            gaps_closed INTEGER NOT NULL DEFAULT 0,
            last_mrn_processed VARCHAR(20),
            status VARCHAR(20) NOT NULL DEFAULT 'running',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ---- VIISCheck table ----
    c.execute("""
        CREATE TABLE IF NOT EXISTS viis_check (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mrn VARCHAR(20) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'found',
            immunization_count INTEGER NOT NULL DEFAULT 0,
            error_message TEXT,
            checked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            raw_response TEXT,
            batch_run_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (batch_run_id) REFERENCES viis_batch_run(id)
        )
    """)

    # ---- Indexes for viis_batch_run ----
    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_viis_batch_run_user_id ON viis_batch_run(user_id)")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_viis_batch_run_status ON viis_batch_run(status)")
    except sqlite3.OperationalError:
        pass

    # ---- Indexes for viis_check ----
    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_viis_check_user_id ON viis_check(user_id)")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_viis_check_mrn ON viis_check(mrn)")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_viis_check_batch_run_id ON viis_check(batch_run_id)")
    except sqlite3.OperationalError:
        pass

    # ---- Extend patient_immunizations: add source column ----
    if not _col_exists(c, 'patient_immunizations', 'source'):
        c.execute(
            "ALTER TABLE patient_immunizations ADD COLUMN source VARCHAR(10) NOT NULL DEFAULT 'ac'"
        )
        print("  Added column: patient_immunizations.source")

    # ---- Extend patient_immunizations: add viis_check_id FK ----
    if not _col_exists(c, 'patient_immunizations', 'viis_check_id'):
        c.execute(
            "ALTER TABLE patient_immunizations ADD COLUMN viis_check_id INTEGER"
        )
        print("  Added column: patient_immunizations.viis_check_id")

    # Index on viis_check_id
    try:
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_patient_imm_viis_check_id "
            "ON patient_immunizations(viis_check_id)"
        )
    except sqlite3.OperationalError:
        pass

    # Unique constraint on (mrn, vaccine_name, date_given, source) to prevent duplicates
    # SQLite does not support ALTER TABLE ADD CONSTRAINT, so we create a unique index instead
    try:
        c.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_patient_imm_mrn_vaccine_date_source "
            "ON patient_immunizations(mrn, vaccine_name, date_given, source)"
        )
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
    print("Migration complete: VIIS tables created, patient_immunizations extended.")


if __name__ == '__main__':
    run()

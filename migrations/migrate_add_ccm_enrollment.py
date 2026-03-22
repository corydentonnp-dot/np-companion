"""
Migration: Add CCM Enrollment + Time Entry tables
File: migrations/migrate_add_ccm_enrollment.py
Phase 19.10

Creates the ccm_enrollment and ccm_time_entry tables for Chronic
Care Management workflow tracking.

Usage:
    venv\\Scripts\\python.exe migrations/migrate_add_ccm_enrollment.py
"""

import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "carecompanion.db",
)


def run():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ── Create ccm_enrollment table ───────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ccm_enrollment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_mrn_hash VARCHAR(64) NOT NULL,
            user_id INTEGER NOT NULL REFERENCES "user"(id),

            enrollment_date DATE,
            consent_date DATE,
            consent_method VARCHAR(30),
            care_plan_date DATE,

            qualifying_conditions TEXT,
            monthly_time_goal INTEGER DEFAULT 20,

            status VARCHAR(20) DEFAULT 'pending',
            last_billed_month VARCHAR(7),
            total_billed_months INTEGER DEFAULT 0,

            created_at DATETIME NOT NULL DEFAULT (datetime('now')),
            updated_at DATETIME DEFAULT (datetime('now'))
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS ix_ccm_enrollment_patient
        ON ccm_enrollment (patient_mrn_hash)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS ix_ccm_enrollment_status
        ON ccm_enrollment (status)
    """)

    # ── Create ccm_time_entry table ───────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ccm_time_entry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enrollment_id INTEGER NOT NULL REFERENCES ccm_enrollment(id),
            entry_date DATE NOT NULL,
            duration_minutes INTEGER NOT NULL,

            activity_type VARCHAR(50),
            staff_name VARCHAR(100),
            staff_role VARCHAR(30),
            activity_description TEXT,

            is_billable BOOLEAN DEFAULT 1,

            created_at DATETIME NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS ix_ccm_time_entry_enrollment
        ON ccm_time_entry (enrollment_id)
    """)

    conn.commit()
    conn.close()
    print("[migrate_add_ccm_enrollment] Done — ccm_enrollment + ccm_time_entry tables ready.")


if __name__ == "__main__":
    run()

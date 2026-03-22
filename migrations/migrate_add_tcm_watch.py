"""
Migration: Add TCM Watch table
File: migrations/migrate_add_tcm_watch.py
Phase 19.2

Creates the tcm_watch_entry table for Transitional Care Management
discharge monitoring and deadline tracking.

Usage:
    venv\\Scripts\\python.exe migrations/migrate_add_tcm_watch.py
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

    # ── Create tcm_watch_entry table ──────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tcm_watch_entry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_mrn_hash VARCHAR(64) NOT NULL,
            user_id INTEGER NOT NULL REFERENCES "user"(id),
            discharge_date DATE NOT NULL,
            discharge_facility VARCHAR(200),
            discharge_summary_received BOOLEAN DEFAULT 0,

            two_day_deadline DATE,
            two_day_contact_completed BOOLEAN DEFAULT 0,
            two_day_contact_date DATE,
            two_day_contact_method VARCHAR(30),

            fourteen_day_visit_deadline DATE,
            seven_day_visit_deadline DATE,
            face_to_face_completed BOOLEAN DEFAULT 0,
            face_to_face_date DATE,

            tcm_code_eligible VARCHAR(10),
            tcm_billed BOOLEAN DEFAULT 0,

            med_reconciliation_completed BOOLEAN DEFAULT 0,

            status VARCHAR(20) DEFAULT 'active',
            notes TEXT,

            created_at DATETIME NOT NULL DEFAULT (datetime('now')),
            updated_at DATETIME DEFAULT (datetime('now'))
        )
    """)

    # Index for fast patient lookup
    cur.execute("""
        CREATE INDEX IF NOT EXISTS ix_tcm_watch_entry_patient
        ON tcm_watch_entry (patient_mrn_hash)
    """)

    # Index for active entries
    cur.execute("""
        CREATE INDEX IF NOT EXISTS ix_tcm_watch_entry_status
        ON tcm_watch_entry (status)
    """)

    conn.commit()
    conn.close()
    print("[migrate_add_tcm_watch] Done — tcm_watch_entry table ready.")


if __name__ == "__main__":
    run()

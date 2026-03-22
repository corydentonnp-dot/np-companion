"""
Migration: Add last_awv_date and last_discharge_date columns to patient_records.
Phase 15.3 — Unblocks AWV eligibility checks and TCM detection.
Idempotent — safe to re-run.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')


def run():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for col_name, col_type in [('last_awv_date', 'DATE'), ('last_discharge_date', 'DATE')]:
        try:
            c.execute(f"ALTER TABLE patient_records ADD COLUMN {col_name} {col_type}")
            print(f"  Added column: patient_records.{col_name}")
        except sqlite3.OperationalError:
            print(f"  Column already exists: patient_records.{col_name}")

    conn.commit()
    conn.close()
    print("Migration complete: AWV/discharge date columns added.")


if __name__ == '__main__':
    run()

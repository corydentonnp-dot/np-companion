"""
Migration: Create opportunity_suppression and closed_loop_status tables
Phase 22.1 + 22.5

Idempotent — safe to run multiple times.
"""

import os
import sqlite3


def get_db_path():
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "..", "data", "carecompanion.db")


def migrate():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Check existing tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}

    if "opportunity_suppression" not in tables:
        cur.execute("""
            CREATE TABLE opportunity_suppression (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_mrn_hash VARCHAR(64) NOT NULL,
                user_id INTEGER NOT NULL,
                visit_date DATE,
                opportunity_code VARCHAR(50) NOT NULL,
                suppression_reason VARCHAR(50) NOT NULL,
                detail TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        cur.execute("CREATE INDEX ix_opp_supp_mrn ON opportunity_suppression(patient_mrn_hash)")
        cur.execute("CREATE INDEX ix_opp_supp_user ON opportunity_suppression(user_id)")
        cur.execute("CREATE INDEX ix_opp_supp_code ON opportunity_suppression(opportunity_code)")
        print("Created table: opportunity_suppression")
    else:
        print("Table opportunity_suppression already exists — skipping")

    if "closed_loop_status" not in tables:
        cur.execute("""
            CREATE TABLE closed_loop_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER,
                patient_mrn_hash VARCHAR(64) NOT NULL,
                funnel_stage VARCHAR(30) NOT NULL,
                stage_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                stage_actor VARCHAR(100),
                stage_notes TEXT,
                previous_stage VARCHAR(30),
                FOREIGN KEY (opportunity_id) REFERENCES billing_opportunity(id)
            )
        """)
        cur.execute("CREATE INDEX ix_cls_opp ON closed_loop_status(opportunity_id)")
        cur.execute("CREATE INDEX ix_cls_mrn ON closed_loop_status(patient_mrn_hash)")
        print("Created table: closed_loop_status")
    else:
        print("Table closed_loop_status already exists — skipping")

    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()

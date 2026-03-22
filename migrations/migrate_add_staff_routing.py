"""
Migration: Add staff_routing_rule table
Phase 20.4 — Staff routing for billing opportunities

Usage:
    venv\\Scripts\\python.exe migrations/migrate_add_staff_routing.py
"""

import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def migrate():
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'data', 'carecompanion.db'
    )
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS staff_routing_rule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_code VARCHAR(50) NOT NULL,
            responsible_role VARCHAR(30) NOT NULL,
            routing_reason VARCHAR(200),
            prep_task_description TEXT,
            timing VARCHAR(30)
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS ix_staff_routing_rule_opportunity_code
        ON staff_routing_rule (opportunity_code)
    """)

    conn.commit()
    conn.close()
    print('[OK] staff_routing_rule table ready')


if __name__ == '__main__':
    migrate()

"""
Migration: Add dismissal_reason column to care_gaps table (Phase 14).
Run once — idempotent.
"""
import sqlite3, os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')

def migrate():
    if not os.path.exists(DB):
        print('[migrate] DB not found — will be created on first run.')
        return
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cols = [r[1] for r in cur.execute("PRAGMA table_info(care_gaps)").fetchall()]
    if 'dismissal_reason' not in cols:
        cur.execute("ALTER TABLE care_gaps ADD COLUMN dismissal_reason TEXT")
        print('[migrate] Added care_gaps.dismissal_reason')
    else:
        print('[migrate] care_gaps.dismissal_reason already exists')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    migrate()

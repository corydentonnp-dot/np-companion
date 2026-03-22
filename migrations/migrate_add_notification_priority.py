"""
Migration — Add notification priority column and composite index (Phase 12).

Adds:
  - priority (Integer, default=2) to notifications table
  - Composite index ix_notif_p1_poll on (user_id, priority, acknowledged_at)
"""

import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'carecompanion.db')


def migrate():
    if not os.path.exists(DB_PATH):
        print(f'[SKIP] Database not found at {DB_PATH}')
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check if priority column already exists
    cur.execute("PRAGMA table_info(notifications)")
    columns = [row[1] for row in cur.fetchall()]

    if 'priority' not in columns:
        cur.execute("ALTER TABLE notifications ADD COLUMN priority INTEGER DEFAULT 2")
        print('[OK] Added priority column to notifications')
        # Back-fill: set existing critical notifications to P1
        cur.execute("UPDATE notifications SET priority = 1 WHERE is_critical = 1")
        updated = cur.rowcount
        print(f'[OK] Back-filled {updated} critical notifications to priority=1')
    else:
        print('[SKIP] priority column already exists')

    # Add composite index for P1 fast-poll
    try:
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_notif_p1_poll
            ON notifications (user_id, priority, acknowledged_at)
        """)
        print('[OK] Created ix_notif_p1_poll composite index')
    except sqlite3.OperationalError as e:
        print(f'[SKIP] Index: {e}')

    conn.commit()
    conn.close()
    print('[DONE] Notification priority migration complete')


if __name__ == '__main__':
    migrate()

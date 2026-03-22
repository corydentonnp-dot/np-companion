"""
Migration: Scraper overhaul — add TOTP secret + insurer columns.

Adds:
  users.np_totp_secret_enc  TEXT  — Fernet-encrypted TOTP secret for MFA
  schedules.insurer         TEXT  — active insurer at appointment time

Idempotent — safe to re-run.
"""
import sqlite3
import os
from utils.paths import get_db_path


def migrate():
    db_path = get_db_path()
    if not os.path.isfile(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # ---- users table: add np_totp_secret_enc ----
    cur.execute("PRAGMA table_info(users)")
    user_cols = {row[1] for row in cur.fetchall()}

    if 'np_totp_secret_enc' not in user_cols:
        cur.execute("ALTER TABLE users ADD COLUMN np_totp_secret_enc TEXT DEFAULT ''")
        print("  Added column: users.np_totp_secret_enc")
    else:
        print("  Column already exists: users.np_totp_secret_enc")

    # ---- schedules table: add insurer ----
    cur.execute("PRAGMA table_info(schedules)")
    sched_cols = {row[1] for row in cur.fetchall()}

    if 'insurer' not in sched_cols:
        cur.execute("ALTER TABLE schedules ADD COLUMN insurer TEXT DEFAULT ''")
        print("  Added column: schedules.insurer")
    else:
        print("  Column already exists: schedules.insurer")

    conn.commit()
    conn.close()
    print("Migration complete: scraper overhaul columns added.")


run = migrate

if __name__ == '__main__':
    migrate()

"""
Migration: Add is_shared and copied_from_id columns to dot_phrases table.
Phase 9 (F28b) — Starter Pack Import requires sharing infrastructure on DotPhrase.
Idempotent — safe to run multiple times.
"""
import sqlite3
import os


def run_migration(app, db):
    """Called by _run_pending_migrations in app/__init__.py."""
    from utils.paths import get_db_path
    db_path = get_db_path()
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(dot_phrases)")
    existing = {row[1] for row in cur.fetchall()}

    if 'is_shared' not in existing:
        cur.execute("ALTER TABLE dot_phrases ADD COLUMN is_shared BOOLEAN DEFAULT 0")
        app.logger.info('[migrate] Added dot_phrases.is_shared')

    if 'copied_from_id' not in existing:
        cur.execute("ALTER TABLE dot_phrases ADD COLUMN copied_from_id INTEGER")
        app.logger.info('[migrate] Added dot_phrases.copied_from_id')

    conn.commit()
    conn.close()


if __name__ == '__main__':
    # Allow standalone execution for manual runs
    from app import create_app
    application = create_app()
    with application.app_context():
        from models import db as _db
        run_migration(application, _db)
    print('[migrate] Done.')

"""
Migration: Add Communication Log table
File: migrations/migrate_add_communication_log.py
Phase 25.3

Creates the communication_log table for phone E/M,
portal messages, and telehealth encounter tracking.

Usage:
    venv\\Scripts\\python.exe migrations/migrate_add_communication_log.py
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

EXPECTED_TABLES = ['communication_log']


def run_migration(app, db):
    """Create communication_log table inside the given Flask app context."""
    with app.app_context():
        from models.telehealth import CommunicationLog  # noqa: F401

        logger.info("Running communication log migration (Phase 25.3)...")

        db.create_all()

        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        all_ok = True
        for table_name in EXPECTED_TABLES:
            if table_name in existing_tables:
                logger.info("  [OK] %s table exists", table_name)
            else:
                logger.error("  [FAIL] %s table not found", table_name)
                all_ok = False

        if all_ok:
            logger.info("Communication log migration complete.")
        else:
            logger.error("Migration incomplete — check model imports.")

        return all_ok


if __name__ == "__main__":
    try:
        from app import create_app
        from models import db
    except ImportError as exc:
        logger.error("Import failed: %s", exc)
        sys.exit(1)

    flask_app = create_app()
    success = run_migration(flask_app, db)
    sys.exit(0 if success else 1)

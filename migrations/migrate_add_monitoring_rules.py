"""
CareCompanion — Monitoring Rules Migration
File: migrations/migrate_add_monitoring_rules.py

Phase 23.A5 — creates three tables:
  - monitoring_rule (23.A1)
  - monitoring_schedule (23.A3)
  - rems_tracker_entry (23.A4)

Idempotent: safe to run multiple times.  Uses db.create_all() which
applies CREATE TABLE IF NOT EXISTS semantics.

Usage
-----
Standalone:   python migrations/migrate_add_monitoring_rules.py
From shell:   from migrations.migrate_add_monitoring_rules import run_migration
              run_migration(app, db)
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

EXPECTED_TABLES = [
    'monitoring_rule',
    'monitoring_schedule',
    'rems_tracker_entry',
]


def run_migration(app, db):
    """
    Create monitoring tables inside the given Flask app context.

    Parameters
    ----------
    app : Flask
        The application instance from create_app().
    db : SQLAlchemy
        The shared db instance from models/__init__.py.
    """
    with app.app_context():
        # Import models so SQLAlchemy discovers table metadata
        from models.monitoring import (  # noqa: F401
            MonitoringRule, MonitoringSchedule, REMSTrackerEntry,
        )

        logger.info("Running monitoring rules migration (Phase 23.A5)...")

        # create_all() is idempotent — skips tables that already exist
        db.create_all()

        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        all_ok = True
        for table_name in EXPECTED_TABLES:
            if table_name in existing_tables:
                logger.info("  [OK] %s table exists", table_name)
            else:
                logger.error("  [FAIL] %s table not found after create_all()", table_name)
                all_ok = False

        if all_ok:
            logger.info("Monitoring rules migration complete — %d tables verified.", len(EXPECTED_TABLES))
        else:
            logger.error("Migration incomplete — check model imports in models/__init__.py")

        return all_ok


if __name__ == "__main__":
    try:
        from app import create_app
        from models import db
    except ImportError as exc:
        logger.error(
            "Import failed: %s\n"
            "Run this script from the CareCompanion project root "
            "with your virtualenv activated.",
            exc,
        )
        sys.exit(1)

    flask_app = create_app()
    success = run_migration(flask_app, db)
    sys.exit(0 if success else 1)

"""
Migration: Add Immunization Series table
File: migrations/migrate_add_imm_series.py
Phase 24.2

Creates the immunization_series table for multi-dose vaccine
series tracking, dose windows, and seasonal eligibility.

Usage:
    venv\\Scripts\\python.exe migrations/migrate_add_imm_series.py
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

EXPECTED_TABLES = ['immunization_series']


def run_migration(app, db):
    """Create immunization_series table inside the given Flask app context."""
    with app.app_context():
        from models.immunization import ImmunizationSeries  # noqa: F401

        logger.info("Running immunization series migration (Phase 24.2)...")

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
            logger.info("Immunization series migration complete.")
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

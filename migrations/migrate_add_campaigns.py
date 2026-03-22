"""
Migration: Add Billing Campaign table
File: migrations/migrate_add_campaigns.py
Phase 27.2

Creates the billing_campaign table for revenue campaigns.

Usage:
    venv\\Scripts\\python.exe migrations/migrate_add_campaigns.py
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
logger = logging.getLogger(__name__)


def run_migration(app, db):
    with app.app_context():
        from models.billing import BillingCampaign  # noqa: F401

        logger.info("Running campaign migration (Phase 27.2)...")
        db.create_all()

        from sqlalchemy import inspect
        tables = inspect(db.engine).get_table_names()
        if "billing_campaign" in tables:
            logger.info("  [OK] billing_campaign table exists")
            return True
        else:
            logger.error("  [FAIL] billing_campaign table not found")
            return False


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

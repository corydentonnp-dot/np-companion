"""
CareCompanion — Billing Models Migration
File: migrate_add_billing_models.py

Idempotent migration script that creates the billing_opportunity and
billing_rule_cache tables if they do not already exist.

Safe to run multiple times — uses CREATE TABLE IF NOT EXISTS semantics
via SQLAlchemy's db.create_all(). Existing rows are never touched.

Usage
-----
Run from the project root (with the virtualenv active):
    python migrate_add_billing_models.py

Or from the Flask shell:
    from migrate_add_billing_models import run_migration
    run_migration(app, db)
"""

import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_migration(app, db):
    """
    Create billing tables inside the given Flask app context.

    Parameters
    ----------
    app : Flask
        The application instance from app.py create_app().
    db : SQLAlchemy
        The shared db instance from models/__init__.py.
    """
    with app.app_context():
        # Importing models here ensures SQLAlchemy has the table metadata
        # before create_all() is called.
        from models.billing import BillingOpportunity, BillingRuleCache  # noqa: F401

        logger.info("Running billing models migration...")

        # create_all() is idempotent — it skips tables that already exist.
        db.create_all()

        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        billing_ok = "billing_opportunity" in existing_tables
        cache_ok = "billing_rule_cache" in existing_tables

        if billing_ok:
            logger.info("  [OK] billing_opportunity table exists")
        else:
            logger.error("  [FAIL] billing_opportunity table not found after create_all()")

        if cache_ok:
            logger.info("  [OK] billing_rule_cache table exists")
        else:
            logger.error("  [FAIL] billing_rule_cache table not found after create_all()")

        if billing_ok and cache_ok:
            logger.info("Billing models migration complete.")
            return True
        else:
            logger.error("Migration incomplete — check model imports in models/__init__.py")
            return False


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

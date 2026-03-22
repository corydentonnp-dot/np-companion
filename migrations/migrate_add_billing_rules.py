"""
CareCompanion — BillingRule Table Migration
File: migrate_add_billing_rules.py

Idempotent migration that creates the billing_rule table if it does not
already exist.  Uses SQLAlchemy db.create_all() (safe for repeated runs).

Usage
-----
    python migrate_add_billing_rules.py

Or via the auto-migration runner on startup.
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
    """Create billing_rule table inside the Flask app context."""
    with app.app_context():
        from models.billing import BillingRule  # noqa: F401

        logger.info("Running BillingRule table migration...")
        db.create_all()

        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if "billing_rule" in inspector.get_table_names():
            logger.info("  [OK] billing_rule table exists")
            return True
        else:
            logger.error("  [FAIL] billing_rule table not found after create_all()")
            return False


if __name__ == "__main__":
    try:
        from app import create_app
        from models import db
    except ImportError as exc:
        logger.error("Import failed: %s — run from the CareCompanion project root.", exc)
        sys.exit(1)

    app = create_app()
    run_migration(app, db)

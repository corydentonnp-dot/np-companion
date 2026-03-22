"""
CareCompanion — Billing Opportunity Type Width Migration
File: migrate_add_billing_type_width.py

Widens billing_opportunity.opportunity_type from VARCHAR(20) to VARCHAR(30)
to accommodate new care-gap-derived types like "colorectal_colonoscopy",
"alcohol_substance_screen", "cognitive_assessment", etc.

SQLite note: SQLite does not enforce VARCHAR length constraints so this
migration is effectively a no-op on the database side. The important change
is in models/billing.py (String(30)). This script exists for consistency
with the migration pattern and to verify the table is accessible.

Usage
-----
    python migrate_add_billing_type_width.py
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
    with app.app_context():
        from models.billing import BillingOpportunity  # noqa: F401
        from sqlalchemy import inspect

        logger.info("Running billing type width migration...")

        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if "billing_opportunity" not in existing_tables:
            logger.info("  billing_opportunity table not found — creating via db.create_all()")
            db.create_all()

        # Verify the column exists
        columns = {c["name"] for c in inspector.get_columns("billing_opportunity")}
        if "opportunity_type" in columns:
            logger.info("  [OK] billing_opportunity.opportunity_type column exists")
            logger.info("  Model updated to String(30) — SQLite does not enforce length")
        else:
            logger.error("  [FAIL] opportunity_type column missing")
            return False

        logger.info("Billing type width migration complete.")
        return True


if __name__ == "__main__":
    try:
        from app import create_app
        from models import db
    except ImportError as exc:
        logger.error(
            "Import failed: %s\n"
            "Run from the CareCompanion project root with virtualenv activated.",
            exc,
        )
        sys.exit(1)

    flask_app = create_app()
    success = run_migration(flask_app, db)
    sys.exit(0 if success else 1)

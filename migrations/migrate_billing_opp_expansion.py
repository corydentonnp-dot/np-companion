"""
CareCompanion — BillingOpportunity Expansion Migration
File: migrate_billing_opp_expansion.py

Idempotent migration that adds Phase 19A columns to the billing_opportunity
table: category, opportunity_code, modifier, priority, documentation_checklist,
actioned_at, actioned_by.

Safe to run multiple times — skips columns that already exist.

Usage
-----
    python migrate_billing_opp_expansion.py

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
    """Add Phase 19A columns to billing_opportunity inside the Flask app context."""
    with app.app_context():
        from sqlalchemy import inspect, text

        inspector = inspect(db.engine)
        if "billing_opportunity" not in inspector.get_table_names():
            logger.info("billing_opportunity table not yet created — skipping, db.create_all() will handle it.")
            db.create_all()
            return True

        existing = {col["name"] for col in inspector.get_columns("billing_opportunity")}

        new_columns = [
            ("category", "VARCHAR(50)"),
            ("opportunity_code", "VARCHAR(20)"),
            ("modifier", "VARCHAR(10)"),
            ("priority", "VARCHAR(10)"),
            ("documentation_checklist", "TEXT"),
            ("actioned_at", "DATETIME"),
            ("actioned_by", "VARCHAR(100)"),
        ]

        added = 0
        for col_name, col_type in new_columns:
            if col_name not in existing:
                db.session.execute(
                    text(f"ALTER TABLE billing_opportunity ADD COLUMN {col_name} {col_type}")
                )
                logger.info("  + Added billing_opportunity.%s", col_name)
                added += 1
            else:
                logger.info("  = billing_opportunity.%s already exists", col_name)

        db.session.commit()
        logger.info("BillingOpportunity expansion migration complete (%d columns added).", added)
        return True


if __name__ == "__main__":
    try:
        from app import create_app
        from models import db
    except ImportError as exc:
        logger.error("Import failed: %s — run from the CareCompanion project root.", exc)
        sys.exit(1)

    app = create_app()
    run_migration(app, db)

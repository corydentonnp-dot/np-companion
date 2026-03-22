"""
CareCompanion — Seed BillingRule Table Migration
migrate_seed_billing_rules.py

Populates the billing_rule table from billing_engine/rules.py seed data.
Skips existing rules (matched by opportunity_code) to allow safe re-runs.
Updates description and checklist for existing rules if content has changed.

Usage:  python migrate_seed_billing_rules.py
Phase 19D.3.
"""

import json
import sys
from datetime import datetime, timezone

from app import create_app
from models import db
from models.billing import BillingRule
from billing_engine.rules import BILLING_RULES


def seed_billing_rules():
    """Insert or update BillingRule rows from BILLING_RULES seed data."""
    app = create_app()
    with app.app_context():
        inserted = 0
        updated = 0
        skipped = 0

        for opp_code, rule_data in BILLING_RULES.items():
            existing = BillingRule.query.filter_by(
                opportunity_code=opp_code
            ).first()

            cpt_json = json.dumps(rule_data.get("cpt_codes", []))
            payer_json = json.dumps(rule_data.get("payer_types", []))
            checklist_json = json.dumps(rule_data.get("documentation_checklist", []))
            rule_logic_json = json.dumps({
                "category": rule_data.get("category"),
                "frequency_limit": rule_data.get("frequency_limit"),
            })

            if existing:
                # Update description and checklist if content changed
                changed = False
                if existing.description != rule_data.get("description"):
                    existing.description = rule_data.get("description")
                    changed = True
                if existing.documentation_checklist != checklist_json:
                    existing.documentation_checklist = checklist_json
                    changed = True
                if existing.cpt_codes != cpt_json:
                    existing.cpt_codes = cpt_json
                    changed = True
                if existing.payer_types != payer_json:
                    existing.payer_types = payer_json
                    changed = True
                if existing.estimated_revenue != rule_data.get("estimated_revenue", 0.0):
                    existing.estimated_revenue = rule_data.get("estimated_revenue", 0.0)
                    changed = True
                if changed:
                    existing.last_updated = datetime.now(timezone.utc)
                    updated += 1
                else:
                    skipped += 1
                continue

            new_rule = BillingRule(
                category=rule_data["category"],
                opportunity_code=opp_code,
                description=rule_data.get("description"),
                cpt_codes=cpt_json,
                payer_types=payer_json,
                estimated_revenue=rule_data.get("estimated_revenue", 0.0),
                modifier=rule_data.get("modifier"),
                rule_logic=rule_logic_json,
                documentation_checklist=checklist_json,
                is_active=True,
                frequency_limit=rule_data.get("frequency_limit"),
            )
            db.session.add(new_rule)
            inserted += 1

        db.session.commit()
        total = inserted + updated + skipped
        print(f"BillingRule seed complete: {total} rules processed")
        print(f"  Inserted: {inserted}")
        print(f"  Updated:  {updated}")
        print(f"  Skipped:  {skipped} (unchanged)")
        return inserted, updated, skipped


if __name__ == "__main__":
    try:
        seed_billing_rules()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

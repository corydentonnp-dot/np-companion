"""
Phase 16.3 — Import 2026 DHS Code List

Loads the CMS Designated Health Services code list into billing_rule_cache
with a special fee_schedule_year = 0 marker (DHS reference, not PFS data).

Cross-references all detector CPT codes against the DHS list and prints
any codes NOT on the 2026 DHS list for Stark Law review.

Idempotent: skips codes already present for year=0.
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Documents", "_archive",
    "dhs_code_list_2026_cpt_hcpcs_export.csv",
)

DHS_YEAR = 0  # Sentinel value: DHS reference entry, not a PFS fee schedule year


def run():
    from app import create_app
    from models import db
    from models.billing import BillingRuleCache

    app = create_app()
    with app.app_context():
        # ----------------------------------------------------------
        # 1. Parse CSV → list of (code, description, dhs_category)
        # ----------------------------------------------------------
        if not os.path.exists(CSV_PATH):
            print(f"[SKIP] DHS CSV not found: {CSV_PATH}")
            return

        entries = []
        current_category = "GENERAL"
        with open(CSV_PATH, encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                val = (row[0] or "").strip() if row else ""
                desc = (row[1] or "").strip() if len(row) > 1 else ""
                if not val:
                    continue

                # Category header detection: all-caps, long, non-code
                if val.isupper() and len(val) > 10 and not val[0].isdigit():
                    current_category = val[:100]
                    continue

                # Code row: starts with digit or G/Q, 4-7 chars
                if (val[0].isdigit() or val[0] in "GQ") and 4 <= len(val) <= 7:
                    entries.append((val, desc, current_category))

        print(f"[DHS] Parsed {len(entries)} codes from CSV")

        # ----------------------------------------------------------
        # 2. Upsert into BillingRuleCache with year=0
        # ----------------------------------------------------------
        existing = {
            row.hcpcs_code
            for row in BillingRuleCache.query.filter_by(
                fee_schedule_year=DHS_YEAR
            ).all()
        }

        inserted = 0
        skipped = 0
        for code, desc, category in entries:
            if code in existing:
                skipped += 1
                continue
            entry = BillingRuleCache(
                hcpcs_code=code,
                fee_schedule_year=DHS_YEAR,
                description=desc or category,
                is_payable=True,
                status_code="DHS",
            )
            db.session.add(entry)
            existing.add(code)
            inserted += 1

        db.session.commit()
        print(f"[DHS] Inserted {inserted}, skipped {skipped} (already exist)")

        # ----------------------------------------------------------
        # 3. Cross-reference detector CPT codes against DHS list
        # ----------------------------------------------------------
        dhs_codes = existing  # All DHS codes now in set

        from billing_engine.rules import BILLING_RULES
        import json

        flagged = []
        for opp_code, rule in BILLING_RULES.items():
            cpt_raw = rule.get("cpt_codes", [])
            if isinstance(cpt_raw, str):
                try:
                    cpt_raw = json.loads(cpt_raw)
                except (json.JSONDecodeError, TypeError):
                    cpt_raw = []
            for cpt in cpt_raw:
                if cpt not in dhs_codes:
                    flagged.append((opp_code, cpt))

        if flagged:
            print(f"\n[STARK REVIEW] {len(flagged)} detector code(s) NOT on 2026 DHS list:")
            for opp, cpt in flagged:
                print(f"  {opp}: {cpt}")
        else:
            print("[STARK] All detector CPT codes found on 2026 DHS list.")


if __name__ == "__main__":
    run()

"""
CareCompanion — Phase 27 Tests: Campaigns + Admin ROI
File: tests/test_campaigns_roi.py
Phase 27.6  —  15 tests

Usage:
    venv\\Scripts\\python.exe tests/test_campaigns_roi.py
"""

import os, sys, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

passed, failed = [], []


def _read(relpath):
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, relpath), encoding="utf-8") as f:
        return f.read()


def run_tests():
    total = 15

    # ---- 1. BillingCampaign model exists with required columns ----
    label = "[1/15] BillingCampaign model columns"
    try:
        src = _read("models/billing.py")
        assert "class BillingCampaign" in src
        cols = ["campaign_name", "campaign_type", "start_date", "end_date",
                "target_criteria", "target_patient_count", "completed_count",
                "estimated_revenue", "actual_revenue", "status", "created_by"]
        missing = [c for c in cols if c not in src]
        assert not missing, f"Missing: {missing}"
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 2. BillingCampaign table in DB ----
    label = "[2/15] billing_campaign table in DB"
    try:
        from app import create_app
        from models import db
        app = create_app()
        with app.app_context():
            from sqlalchemy import inspect as sqla_inspect
            assert "billing_campaign" in sqla_inspect(db.engine).get_table_names()
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 3. Migration exists ----
    label = "[3/15] Campaign migration file"
    try:
        assert os.path.isfile(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "migrations", "migrate_add_campaigns.py"
        ))
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 4. Model registered in __init__.py ----
    label = "[4/15] BillingCampaign in models/__init__.py"
    try:
        src = _read("models/__init__.py")
        assert "BillingCampaign" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 5. 7 campaign templates defined ----
    label = "[5/15] CAMPAIGN_TEMPLATES has 7 types"
    try:
        src = _read("routes/campaigns.py")
        assert "CAMPAIGN_TEMPLATES" in src
        types = ["awv_push", "htn_optimization", "dm_registry",
                 "immunization_catchup", "tobacco_cessation",
                 "bh_screening", "quarter_end_fastcash"]
        for t in types:
            assert t in src, f"Missing template: {t}"
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 6. Campaigns list route ----
    label = "[6/15] /campaigns route"
    try:
        src = _read("routes/campaigns.py")
        assert "def campaigns_list" in src
        assert "campaigns.html" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 7. Campaign CRUD API ----
    label = "[7/15] Campaign create + update APIs"
    try:
        src = _read("routes/campaigns.py")
        assert "def create_campaign" in src
        assert "def update_campaign" in src
        assert "methods=['POST']" in src or 'methods=["POST"]' in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 8. Ranked campaigns API (27.4) ----
    label = "[8/15] /api/campaigns/ranked (net value x time-to-cash)"
    try:
        src = _read("routes/campaigns.py")
        assert "def ranked_campaigns" in src
        assert "time_to_cash" in src
        assert "daily_value" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 9. Admin billing ROI route (27.5) ----
    label = "[9/15] /admin/billing-roi route"
    try:
        src = _read("routes/campaigns.py")
        assert "def admin_billing_roi" in src
        assert "admin_billing_roi.html" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 10. Admin ROI template exists ----
    label = "[10/15] admin_billing_roi.html template"
    try:
        src = _read("templates/admin_billing_roi.html")
        assert "Billing ROI" in src
        assert "Leakage" in src or "leakage" in src
        assert "Bottleneck" in src or "bottleneck" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 11. Campaigns template exists ----
    label = "[11/15] campaigns.html template"
    try:
        src = _read("templates/campaigns.html")
        assert "Revenue Campaigns" in src
        assert "New Campaign" in src or "new-campaign" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 12. Blueprint registered ----
    label = "[12/15] campaigns_bp registered"
    try:
        src = _read("app/__init__.py")
        assert "routes.campaigns" in src
        assert "campaigns_bp" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 13. ROI: leakage families + bottlenecks ----
    label = "[13/15] ROI leakage families + workflow bottlenecks"
    try:
        src = _read("routes/campaigns.py")
        assert "leakage_families" in src
        assert "top_bottlenecks" in src
        assert "ClosedLoopStatus" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 14. ROI: bonus projection ----
    label = "[14/15] ROI bonus projection integration"
    try:
        src = _read("routes/campaigns.py")
        assert "BonusTracker" in src
        assert "bonus_proj" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 15. All routes importable ----
    label = "[15/15] All campaign + ROI routes importable"
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            rules = [r.rule for r in app.url_map.iter_rules()
                     if 'campaign' in r.rule or 'billing-roi' in r.rule]
            assert len(rules) >= 5, f"Only {len(rules)} routes: {rules}"
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- Summary ----
    print(f"\n{'='*60}")
    print(f"Phase 27 -- Campaigns + ROI Tests: {len(passed)}/{total} passed")
    print(f"{'='*60}")
    for p in passed:
        print(f"  PASS  {p}")
    for f in failed:
        print(f"  FAIL  {f}")
    print()
    return len(failed) == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

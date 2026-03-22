"""
CareCompanion — Phase 26 Tests: Revenue Reporting + Reconciliation
File: tests/test_revenue_reporting.py
Phase 26.7  —  15 tests

Usage:
    venv\\Scripts\\python.exe tests/test_revenue_reporting.py
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

    # ---- 1. Revenue route file exists with required endpoints ----
    label = "[1/15] revenue route exists with 3 endpoints"
    try:
        src = _read("routes/revenue.py")
        assert "def revenue_report" in src
        assert "def dx_family_report" in src
        assert "def revenue_summary_api" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 2. Blueprint registered ----
    label = "[2/15] revenue_bp registered in app/__init__.py"
    try:
        src = _read("app/__init__.py")
        assert "routes.revenue" in src
        assert "revenue_bp" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 3. Revenue report template exists ----
    label = "[3/15] revenue_report_full.html template"
    try:
        src = _read("templates/revenue_report_full.html")
        assert "Revenue Report" in src
        assert "Detected" in src
        assert "Captured" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 4. Dx family report template exists ----
    label = "[4/15] dx_family_report.html template"
    try:
        src = _read("templates/dx_family_report.html")
        assert "Diagnosis Family" in src
        assert "Encounters" in src or "encounters" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 5. Category breakdown in revenue route ----
    label = "[5/15] Category breakdown computation"
    try:
        src = _read("routes/revenue.py")
        assert "categories" in src
        assert "rev_detected" in src
        assert "rev_captured" in src
        assert "rev_missed" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 6. Capture rate calculation ----
    label = "[6/15] Capture rate calculation"
    try:
        src = _read("routes/revenue.py")
        assert "capture_rate" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 7. Reconciliation funnel (26.2) ----
    label = "[7/15] Reconciliation funnel from ClosedLoopStatus"
    try:
        src = _read("routes/revenue.py")
        assert "_build_funnel" in src
        assert "ClosedLoopStatus" in src
        stages = ["detected", "surfaced", "accepted", "documented", "billed", "paid", "denied", "adjusted"]
        for s in stages:
            assert f"'{s}'" in src, f"Missing stage: {s}"
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 8. Funnel leakage % between stages ----
    label = "[8/15] Funnel leakage percentage"
    try:
        src = _read("routes/revenue.py")
        assert "leakage_pct" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 9. Leakage cause attribution (26.3) ----
    label = "[9/15] Leakage cause attribution categories"
    try:
        src = _read("routes/revenue.py")
        assert "_build_leakage" in src
        causes = ["detection_gap", "workflow_drop", "documentation_failure",
                   "modifier_failure", "payer_denial", "staff_bottleneck"]
        for c in causes:
            assert c in src, f"Missing cause: {c}"
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 10. Dx families defined (26.4) ----
    label = "[10/15] DX_FAMILIES covers 8 groups"
    try:
        src = _read("routes/revenue.py")
        assert "DX_FAMILIES" in src
        families = ["HTN", "DM", "HLD", "Thyroid", "BH", "Tobacco", "Obesity", "Preventive"]
        for f in families:
            assert f"'{f}'" in src, f"Missing family: {f}"
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 11. Annual estimate (26.5) ----
    label = "[11/15] Annual billing opportunity estimate"
    try:
        src = _read("routes/revenue.py")
        assert "annual_estimate" in src
        assert "annual_captured" in src
        assert "annual_gap" in src
        tpl = _read("templates/revenue_report_full.html")
        assert "Annual" in tpl or "annual" in tpl
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 12. Bonus projection (26.6) ----
    label = "[12/15] First-bonus projection"
    try:
        src = _read("routes/revenue.py")
        assert "_get_bonus_projection" in src
        assert "BonusTracker" in src
        assert "quarterly_threshold" in src or "threshold" in src
        tpl = _read("templates/revenue_report_full.html")
        assert "Bonus" in tpl
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 13. Top missed opportunities ----
    label = "[13/15] Top missed opportunities list"
    try:
        src = _read("routes/revenue.py")
        assert "top_missed" in src
        tpl = _read("templates/revenue_report_full.html")
        assert "Top Missed" in tpl or "top_missed" in tpl
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 14. Routes load without import error ----
    label = "[14/15] Revenue routes importable"
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            rules = [r.rule for r in app.url_map.iter_rules()
                     if 'revenue' in r.rule or 'dx-fam' in r.rule]
            assert len(rules) >= 3, f"Only {len(rules)} routes: {rules}"
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 15. Revenue summary API endpoint ----
    label = "[15/15] JSON API /api/revenue/summary"
    try:
        src = _read("routes/revenue.py")
        assert "/api/revenue/summary" in src
        assert "jsonify" in src
        assert "'rev_gap'" in src or '"rev_gap"' in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- Summary ----
    print(f"\n{'='*60}")
    print(f"Phase 26 -- Revenue Reporting Tests: {len(passed)}/{total} passed")
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

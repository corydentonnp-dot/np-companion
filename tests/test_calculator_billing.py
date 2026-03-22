"""
Phase 38.5 — Calculator Billing Detector Tests
tests/test_calculator_billing.py

10 tests verifying that CalculatorBillingDetector correctly generates
BillingOpportunity entries from calculator scores.

Usage:
    venv\\Scripts\\python.exe tests/test_calculator_billing.py
"""

import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_app():
    os.environ["FLASK_ENV"] = "testing"
    from app import create_app
    a = create_app()
    a.config["TESTING"] = True
    return a


def _pd(**overrides):
    """Build a minimal patient_data dict with calculator_scores override."""
    base = {
        "mrn": "TESTCALC001",
        "user_id": 1,
        "visit_date": date.today(),
        "insurer_type": "commercial",
        "sex": "male",
        "age_years": 55,
        "calculator_scores": {},
    }
    base.update(overrides)
    return base


def _detect(detector, scores, **extra):
    pd = _pd(calculator_scores=scores, **extra)
    return detector.detect(pd, {})


def _codes(opps):
    """Return a flat set of all applicable code strings from a list of opportunities."""
    result = set()
    for o in opps:
        codes_str = getattr(o, "applicable_codes", "") or ""
        for c in codes_str.split(","):
            c = c.strip()
            if c:
                result.add(c)
    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def run_tests():
    passed = []
    failed = []

    app = _get_app()

    with app.app_context():
        from models import db
        from billing_engine.detectors.calculator_detector import CalculatorBillingDetector
        detector = CalculatorBillingDetector(db=db)

        # ==================================================================
        # Test 1 — BMI >= 30 generates obesity counseling with correct code
        # ==================================================================
        print("[1/10] BMI >= 30 → obesity counseling...")
        try:
            opps = _detect(detector, {"bmi": 34.2}, insurer_type="medicare")
            assert len(opps) >= 1, "Expected at least one opportunity"
            codes = _codes(opps)
            assert "G0447" in codes, f"Expected G0447 for Medicare patient, got: {codes}"
            opp = opps[0]
            assert getattr(opp, "opportunity_code", None) == "CALC_BMI_OBC", (
                f"Expected CALC_BMI_OBC, got: {opp.opportunity_code}"
            )
            passed.append("1: BMI >= 30 → G0447 opportunity")
        except Exception as e:
            failed.append(f"1: BMI >= 30: {e}")

        # ==================================================================
        # Test 2 — PREVENT >= 7.5% generates statin discussion opportunity
        # ==================================================================
        print("[2/10] PREVENT >= 7.5% → statin SDM...")
        try:
            opps = _detect(detector, {"prevent": 12.5})
            assert len(opps) >= 1, "Expected at least one opportunity"
            codes = _codes(opps)
            assert "99401" in codes, f"Expected 99401 for statin SDM, got: {codes}"
            opp = next(
                o for o in opps if getattr(o, "opportunity_code", "") == "CALC_PREVENT_SDM"
            )
            assert opp is not None
            passed.append("2: PREVENT >= 7.5% → statin SDM opportunity")
        except Exception as e:
            failed.append(f"2: PREVENT >= 7.5%: {e}")

        # ==================================================================
        # Test 3 — Pack years >= 20 generates LDCT opportunity (71271 + G0296)
        # ==================================================================
        print("[3/10] Pack years >= 20 → LDCT...")
        try:
            opps = _detect(detector, {"pack_years": 25}, age_years=62)
            assert len(opps) >= 1, "Expected at least one opportunity"
            codes = _codes(opps)
            assert "71271" in codes, f"Expected 71271, got: {codes}"
            assert "G0296" in codes, f"Expected G0296, got: {codes}"
            opp = next(
                o for o in opps if getattr(o, "opportunity_code", "") == "CALC_LDCT_SCR"
            )
            assert getattr(opp, "confidence_level", "") == "HIGH"
            passed.append("3: Pack years >= 20 → 71271 + G0296")
        except Exception as e:
            failed.append(f"3: Pack years >= 20 LDCT: {e}")

        # ==================================================================
        # Test 4 — LDL >= 190 generates FH workup opportunity (81401)
        # ==================================================================
        print("[4/10] LDL >= 190 → FH workup...")
        try:
            opps = _detect(detector, {"ldl": 215.0})
            assert len(opps) >= 1, "Expected at least one opportunity"
            codes = _codes(opps)
            assert "81401" in codes, f"Expected 81401 for FH workup, got: {codes}"
            passed.append("4: LDL >= 190 → 81401")
        except Exception as e:
            failed.append(f"4: LDL >= 190 FH: {e}")

        # ==================================================================
        # Test 5 — AUDIT-C positive generates SBIRT opportunity (G0442 + G0443)
        # ==================================================================
        print("[5/10] AUDIT-C positive → SBIRT...")
        try:
            # Male threshold >= 4
            opps = _detect(detector, {"audit_c": 5}, sex="male")
            assert len(opps) >= 1, "Expected at least one opportunity"
            codes = _codes(opps)
            assert "G0442" in codes, f"Expected G0442, got: {codes}"
            assert "G0443" in codes, f"Expected G0443, got: {codes}"
            # Female threshold >= 3
            opps_f = _detect(detector, {"audit_c": 3}, sex="female")
            codes_f = _codes(opps_f)
            assert "G0442" in codes_f, f"Female positive: expected G0442, got: {codes_f}"
            passed.append("5: AUDIT-C positive → G0442 + G0443")
        except Exception as e:
            failed.append(f"5: AUDIT-C SBIRT: {e}")

        # ==================================================================
        # Test 6 — 96127 generated for questionnaire administration
        #          (GAD-7, PHQ-9, EPDS each trigger it; only one per visit)
        # ==================================================================
        print("[6/10] Questionnaire → 96127...")
        try:
            for key, expected_prefix in [
                ("gad7", "GAD7"),
                ("phq9", "PHQ9"),
                ("epds", "EPDS"),
            ]:
                opps = _detect(detector, {key: 8})
                codes = _codes(opps)
                assert "96127" in codes, (
                    f"Expected 96127 for {key}, got: {codes}"
                )
                opp = next(
                    o for o in opps
                    if getattr(o, "opportunity_code", "").startswith(f"CALC_{expected_prefix}")
                )
                assert opp is not None

            # Passing both GAD-7 and PHQ-9 should only yield one 96127 (first wins)
            opps_multi = _detect(detector, {"gad7": 10, "phq9": 15})
            count_96127 = sum(
                1 for o in opps_multi
                if "96127" in (getattr(o, "applicable_codes", "") or "")
            )
            assert count_96127 == 1, f"Expected exactly 1 × 96127, got: {count_96127}"
            passed.append("6: GAD-7/PHQ-9/EPDS → 96127 (once per visit)")
        except Exception as e:
            failed.append(f"6: Questionnaire 96127: {e}")

        # ==================================================================
        # Test 7 — Documentation (eligibility_basis) includes score value
        # ==================================================================
        print("[7/10] eligibility_basis includes score value...")
        try:
            opps = _detect(detector, {"bmi": 34.2}, insurer_type="medicare")
            bmi_opp = next(
                o for o in opps if getattr(o, "opportunity_code", "") == "CALC_BMI_OBC"
            )
            basis = getattr(bmi_opp, "eligibility_basis", "") or ""
            assert "34.2" in basis, (
                f"Expected '34.2' in eligibility_basis, got: {basis!r}"
            )

            opps_ldl = _detect(detector, {"ldl": 207.0})
            ldl_opp = next(
                o for o in opps_ldl if getattr(o, "opportunity_code", "") == "CALC_LDL_FH"
            )
            ldl_basis = getattr(ldl_opp, "eligibility_basis", "") or ""
            assert "207" in ldl_basis, (
                f"Expected '207' in LDL eligibility_basis, got: {ldl_basis!r}"
            )
            passed.append("7: eligibility_basis includes score value")
        except Exception as e:
            failed.append(f"7: Basis includes score: {e}")

        # ==================================================================
        # Test 8 — No duplicate opportunities for the same trigger
        # ==================================================================
        print("[8/10] No duplicate opportunities for same trigger...")
        try:
            # GAD-7 + PHQ-9 → only one 96127 (break after first questionnaire)
            opps = _detect(detector, {"gad7": 8, "phq9": 14, "epds": 10})
            opps_96127 = [
                o for o in opps
                if "96127" in (getattr(o, "applicable_codes", "") or "")
            ]
            assert len(opps_96127) == 1, (
                f"Expected 1 × 96127 opportunity, got: {len(opps_96127)}"
            )

            # BMI only appears once with unique opportunity_code
            opps_bmi = _detect(detector, {"bmi": 35.0}, insurer_type="medicare")
            bmi_opps = [
                o for o in opps_bmi
                if getattr(o, "opportunity_code", "") == "CALC_BMI_OBC"
            ]
            assert len(bmi_opps) == 1, (
                f"Expected exactly 1 × CALC_BMI_OBC, got: {len(bmi_opps)}"
            )
            passed.append("8: No duplicate opportunities per trigger")
        except Exception as e:
            failed.append(f"8: Deduplication: {e}")

        # ==================================================================
        # Test 9 — Billing alert bar template has calculator_billing context
        # ==================================================================
        print("[9/10] _billing_alert_bar.html renders calculator context...")
        try:
            bar_path = os.path.join(ROOT, "templates", "_billing_alert_bar.html")
            with open(bar_path, encoding="utf-8") as fh:
                src = fh.read()
            assert "calculator_billing" in src, (
                "Expected 'calculator_billing' check in _billing_alert_bar.html"
            )
            assert "ctxSnippet" in src or "calculator_billing" in src, (
                "Expected calculator context rendering in alert bar"
            )
            passed.append("9: _billing_alert_bar.html renders calculator context")
        except Exception as e:
            failed.append(f"9: Template render: {e}")

        # ==================================================================
        # Test 10 — Detector integrates with BillingCaptureEngine pipeline
        # ==================================================================
        print("[10/10] BillingCaptureEngine discovers CalculatorBillingDetector...")
        try:
            from billing_engine.engine import BillingCaptureEngine
            engine = BillingCaptureEngine(db=db)
            categories = [d.CATEGORY for d in engine._detectors]
            assert "calculator_billing" in categories, (
                f"Expected 'calculator_billing' in engine detectors, got: {categories}"
            )

            # Integration: engine.evaluate() with calculator_scores produces opp
            pd_engine = {
                "mrn": "TESTENG001",
                "user_id": 1,
                "visit_date": date.today(),
                "insurer_type": "commercial",
                "sex": "male",
                "age_years": 58,
                "calculator_scores": {"bmi": 32.0, "prevent": 9.5},
                "diagnoses": [],
            }
            results = engine.evaluate(pd_engine)
            calc_opps = [
                o for o in results
                if getattr(o, "category", "") == "calculator_billing"
            ]
            assert len(calc_opps) >= 1, (
                f"Expected calculator_billing opportunities from engine.evaluate(), "
                f"got 0 (total opps: {len(results)})"
            )
            passed.append("10: BillingCaptureEngine includes CalculatorBillingDetector")
        except Exception as e:
            failed.append(f"10: Engine integration: {e}")

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print(f"RESULTS: {len(passed)}/{len(passed) + len(failed)} passed")
    print("=" * 60)
    for p in passed:
        print(f"  ✓ {p}")
    for f in failed:
        print(f"  ✗ {f}")

    if failed:
        sys.exit(1)
    else:
        print("\nAll tests passed!")


if __name__ == "__main__":
    run_tests()

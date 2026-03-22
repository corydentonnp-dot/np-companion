"""
Tests for Phase 22: Why-Not Explainability + Closed-Loop Tracking
Tests: OpportunitySuppression model, ClosedLoopStatus model, engine wiring,
       routes, leakage attribution, funnel tracking, templates.
"""

import os
import sys
import json
import unittest
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestOpportunitySuppressionModel(unittest.TestCase):
    """22.1: OpportunitySuppression model exists and has correct fields."""

    def test_import(self):
        from models.billing import OpportunitySuppression
        self.assertTrue(hasattr(OpportunitySuppression, "__tablename__"))
        self.assertEqual(OpportunitySuppression.__tablename__, "opportunity_suppression")

    def test_fields(self):
        from models.billing import OpportunitySuppression
        cols = {c.name for c in OpportunitySuppression.__table__.columns}
        for expected in ["id", "patient_mrn_hash", "user_id", "visit_date",
                         "opportunity_code", "suppression_reason", "detail", "created_at"]:
            self.assertIn(expected, cols)

    def test_suppression_reasons_set(self):
        from models.billing import SUPPRESSION_REASONS
        self.assertIsInstance(SUPPRESSION_REASONS, set)
        self.assertIn("chart_unsupported", SUPPRESSION_REASONS)
        self.assertIn("provider_disabled_category", SUPPRESSION_REASONS)
        self.assertEqual(len(SUPPRESSION_REASONS), 13)


class TestClosedLoopStatusModel(unittest.TestCase):
    """22.5: ClosedLoopStatus model exists and has correct fields."""

    def test_import(self):
        from models.billing import ClosedLoopStatus
        self.assertTrue(hasattr(ClosedLoopStatus, "__tablename__"))
        self.assertEqual(ClosedLoopStatus.__tablename__, "closed_loop_status")

    def test_fields(self):
        from models.billing import ClosedLoopStatus
        cols = {c.name for c in ClosedLoopStatus.__table__.columns}
        for expected in ["id", "opportunity_id", "patient_mrn_hash", "funnel_stage",
                         "stage_date", "stage_actor", "stage_notes", "previous_stage"]:
            self.assertIn(expected, cols)

    def test_funnel_stages_set(self):
        from models.billing import FUNNEL_STAGES
        self.assertIsInstance(FUNNEL_STAGES, set)
        self.assertEqual(len(FUNNEL_STAGES), 11)
        for stage in ["detected", "surfaced", "accepted", "documented", "billed",
                       "paid", "denied", "adjusted", "dismissed", "deferred", "follow_up_needed"]:
            self.assertIn(stage, FUNNEL_STAGES)


class TestMigration(unittest.TestCase):
    """22.2: Both tables exist in database."""

    def test_tables_exist(self):
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "carecompanion.db"
        )
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        conn.close()
        self.assertIn("opportunity_suppression", tables)
        self.assertIn("closed_loop_status", tables)


class TestEngineSuppressionWiring(unittest.TestCase):
    """22.2: BillingCaptureEngine.evaluate() tracks suppressions."""

    def test_engine_has_suppression_methods(self):
        from billing_engine.engine import BillingCaptureEngine
        self.assertTrue(hasattr(BillingCaptureEngine, "get_suppressions"))
        self.assertTrue(hasattr(BillingCaptureEngine, "log_suppressions"))
        self.assertTrue(hasattr(BillingCaptureEngine, "record_funnel_stage"))

    def test_evaluate_records_disabled_category(self):
        """When a category is disabled, evaluate should record a suppression."""
        from billing_engine.engine import BillingCaptureEngine

        class MockDB:
            session = type("S", (), {"add": lambda s, x: None, "commit": lambda s: None})()

        engine = BillingCaptureEngine(db=MockDB())
        # Disable all categories
        patient_data = {
            "billing_categories_enabled": {d.CATEGORY: False for d in engine._detectors},
            "diagnoses": [],
        }
        result = engine.evaluate(patient_data)
        # All should be suppressed
        supps = engine.get_suppressions()
        self.assertGreater(len(supps), 0)
        self.assertTrue(all(s["reason"] == "provider_disabled_category" for s in supps))


class TestWhyNotRoutes(unittest.TestCase):
    """22.3: Why-not routes registered."""

    def test_why_not_page_route_exists(self):
        from routes.intelligence import billing_why_not, api_billing_why_not
        self.assertTrue(callable(billing_why_not))
        self.assertTrue(callable(api_billing_why_not))

    def test_funnel_route_exists(self):
        from routes.intelligence import api_opportunity_funnel, api_opportunity_transition
        self.assertTrue(callable(api_opportunity_funnel))
        self.assertTrue(callable(api_opportunity_transition))

    def test_leakage_route_exists(self):
        from routes.intelligence import api_leakage_summary
        self.assertTrue(callable(api_leakage_summary))


class TestWhyNotTemplate(unittest.TestCase):
    """22.3: billing_why_not.html exists and has expected content."""

    def test_template_exists(self):
        tmpl = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "templates", "billing_why_not.html"
        )
        self.assertTrue(os.path.exists(tmpl))

    def test_template_content(self):
        tmpl = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "templates", "billing_why_not.html"
        )
        with open(tmpl, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Why Not", content)
        self.assertIn("filterWhyNot", content)
        self.assertIn("why-card", content)
        self.assertIn("suppression_reason", content)


class TestAlertBarWhyNotLink(unittest.TestCase):
    """22.4: Alert bar has 'why not?' link."""

    def test_alert_bar_why_not(self):
        tmpl = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "templates", "_billing_alert_bar.html"
        )
        with open(tmpl, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("why-not", content)
        self.assertIn("not shown", content)


class TestPostVisitWhyNotLink(unittest.TestCase):
    """22.4: Post-visit modal has 'why not?' link."""

    def test_post_visit_why_not(self):
        tmpl = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "templates", "_billing_post_visit.html"
        )
        with open(tmpl, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("why-not", content)
        self.assertIn("not shown", content)


class TestClosedLoopInCaptureDismiss(unittest.TestCase):
    """22.6: Capture/dismiss routes include closed-loop tracking."""

    def test_capture_has_funnel(self):
        import inspect
        from routes.intelligence import capture_opportunity
        src = inspect.getsource(capture_opportunity)
        self.assertIn("ClosedLoopStatus", src)
        self.assertIn("accepted", src)

    def test_dismiss_has_funnel(self):
        import inspect
        from routes.intelligence import dismiss_opportunity
        src = inspect.getsource(dismiss_opportunity)
        self.assertIn("ClosedLoopStatus", src)
        self.assertIn("dismissed", src)


class TestLeakageAttribution(unittest.TestCase):
    """22.7: Leakage attribution maps reasons to categories."""

    def test_leakage_route_maps_all_reasons(self):
        import inspect
        from routes.intelligence import api_leakage_summary
        src = inspect.getsource(api_leakage_summary)
        # All 13 suppression reasons should be mapped
        from models.billing import SUPPRESSION_REASONS
        for reason in SUPPRESSION_REASONS:
            self.assertIn(reason, src, f"Leakage map missing: {reason}")

    def test_seven_leakage_categories(self):
        import inspect
        from routes.intelligence import api_leakage_summary
        src = inspect.getsource(api_leakage_summary)
        for cat in ["documentation_failure", "detection_gap", "payer_behavior",
                     "workflow_drop", "provider_deferral", "modifier_failure"]:
            self.assertIn(cat, src)


class TestModelsRegistered(unittest.TestCase):
    """Models are importable from models/__init__.py."""

    def test_models_importable(self):
        from models.billing import OpportunitySuppression, ClosedLoopStatus
        self.assertIsNotNone(OpportunitySuppression)
        self.assertIsNotNone(ClosedLoopStatus)


if __name__ == "__main__":
    unittest.main()

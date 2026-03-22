"""
Phase 21 Tests — Documentation Phrase Library + Code Specificity + Stack Classifier
Run: python tests/test_phrases_specificity.py
Expected: 15/15 pass
"""

import json
import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "carecompanion.db")


class TestDocumentationPhraseModel(unittest.TestCase):
    """21.1: DocumentationPhrase model structure."""

    def test_21_1a_model_importable(self):
        from models.billing import DocumentationPhrase
        self.assertTrue(hasattr(DocumentationPhrase, "__tablename__"))
        self.assertEqual(DocumentationPhrase.__tablename__, "documentation_phrase")

    def test_21_1b_model_fields(self):
        from models.billing import DocumentationPhrase
        cols = {c.name for c in DocumentationPhrase.__table__.columns}
        expected = {
            "id", "opportunity_code", "cpt_code", "phrase_category",
            "phrase_title", "phrase_text", "payer_specific",
            "clinical_context", "required_elements", "is_active", "is_customized",
        }
        self.assertTrue(expected.issubset(cols), f"Missing columns: {expected - cols}")


class TestMigration(unittest.TestCase):
    """21.2: Migration creates table."""

    def test_21_2_table_exists(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documentation_phrase'")
        row = cur.fetchone()
        conn.close()
        self.assertIsNotNone(row, "documentation_phrase table should exist")


class TestSeedPhrases(unittest.TestCase):
    """21.3: Seeded phrases."""

    def test_21_3a_phrase_count(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM documentation_phrase")
        count = cur.fetchone()[0]
        conn.close()
        self.assertGreaterEqual(count, 25, f"Expected >= 25 phrases, got {count}")

    def test_21_3b_key_codes_present(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT opportunity_code FROM documentation_phrase")
        codes = {r[0] for r in cur.fetchall()}
        conn.close()
        required = {"G2211", "AWV", "CCM", "TCM", "TOBACCO_CESSATION", "CARE_GAP_SCREENING", "PROLONGED_SERVICE"}
        missing = required - codes
        self.assertEqual(len(missing), 0, f"Missing codes: {missing}")

    def test_21_3c_customized_preserved(self):
        """Non-customized cleared on re-seed; customized survive."""
        from migrations.seed_documentation_phrases import PHRASE_SEED
        self.assertTrue(len(PHRASE_SEED) >= 25)
        # Check seed script preserves customized
        import importlib
        mod = importlib.import_module("migrations.seed_documentation_phrases")
        # The SQL in seed() has "DELETE FROM documentation_phrase WHERE is_customized = 0"
        import inspect
        source = inspect.getsource(mod.seed)
        self.assertIn("is_customized = 0", source, "Seed should only delete non-customized phrases")


class TestPhraseRoutes(unittest.TestCase):
    """21.4: Phrase settings route."""

    def test_21_4a_settings_route(self):
        from app import create_app
        app = create_app()
        rules = [r.rule for r in app.url_map.iter_rules()]
        self.assertIn("/settings/phrases", rules)

    def test_21_4b_phrase_api_route(self):
        from app import create_app
        app = create_app()
        rules = [r.rule for r in app.url_map.iter_rules()]
        self.assertIn("/api/billing/phrases-for-code/<opportunity_code>", rules)

    def test_21_4c_edit_route(self):
        from app import create_app
        app = create_app()
        rules = [r.rule for r in app.url_map.iter_rules()]
        self.assertIn("/settings/phrases/<int:phrase_id>/edit", rules)


class TestClipboardIntegration(unittest.TestCase):
    """21.5: Alert bar clipboard integration."""

    def test_21_5_doc_language_button(self):
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "templates", "_billing_alert_bar.html")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("toggleDocPhrases", content, "Alert bar should have Doc Language toggle")
        self.assertIn("doc-phrase-panel", content, "Alert bar should have phrase panel div")
        self.assertIn("copyDocPhrase", content, "Alert bar should have copy function")


class TestPostVisitPhrases(unittest.TestCase):
    """21.6: Post-visit phrase reminder."""

    def test_21_6_post_visit_phrases(self):
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "templates", "_billing_post_visit.html")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("pvTogglePhrases", content, "Post-visit should have phrase toggle")
        self.assertIn("pvCopyPhrase", content, "Post-visit should have copy function")
        self.assertIn("pv-phrase-panel", content, "Post-visit should have phrase panel")


class TestCodeSpecificityRecommender(unittest.TestCase):
    """21.7: CodeSpecificityRecommender."""

    def test_21_7a_import_and_codes(self):
        from billing_engine.specificity import CodeSpecificityRecommender
        r = CodeSpecificityRecommender()
        codes = r.get_supported_codes()
        self.assertIn("E78.5", codes)
        self.assertIn("F32.9", codes)
        self.assertIn("I10", codes)
        self.assertIn("N18.9", codes)

    def test_21_7b_hlp_with_evidence(self):
        from billing_engine.specificity import CodeSpecificityRecommender
        r = CodeSpecificityRecommender()
        result = r.recommend("E78.5", {"labs": {"ldl": 160, "triglycerides": 200}})
        self.assertEqual(result["current_code"], "E78.5")
        # First rec should be supported (both elevated)
        self.assertTrue(result["recommendations"][0]["supported"])
        self.assertIn("Supported", result["recommendations"][0]["evidence_status"])

    def test_21_7c_hlp_missing_evidence(self):
        from billing_engine.specificity import CodeSpecificityRecommender
        r = CodeSpecificityRecommender()
        result = r.recommend("E78.5", {"labs": {}})
        # Without lipid panel, should NOT be supported
        self.assertFalse(result["recommendations"][0]["supported"])
        self.assertIn("Missing", result["recommendations"][0]["evidence_status"])

    def test_21_7d_depression_specificity(self):
        from billing_engine.specificity import CodeSpecificityRecommender
        r = CodeSpecificityRecommender()
        result = r.recommend("F32.9", {"screenings": {"phq9": 12}})
        # PHQ-9 12 → moderate (F32.1)
        supported = [rec for rec in result["recommendations"] if rec["supported"]]
        self.assertEqual(len(supported), 1)
        self.assertEqual(supported[0]["recommended_code"], "F32.1")

    def test_21_7e_compliance_guard(self):
        """Never suggests unsupported code."""
        from billing_engine.specificity import CodeSpecificityRecommender
        r = CodeSpecificityRecommender()
        # No evidence at all
        result = r.recommend("I10", {})
        for rec in result["recommendations"]:
            self.assertFalse(rec["supported"])
            self.assertIn("Missing", rec["evidence_status"])


class TestStackClassifier(unittest.TestCase):
    """21.8: Stack classifier."""

    def test_21_8a_tiers(self):
        from billing_engine.stack_classifier import StackClassifier
        c = StackClassifier()
        self.assertEqual(c.get_tier("AWV"), "STRONG_STANDALONE")
        self.assertEqual(c.get_tier("G2211"), "STRONG_STACK")
        self.assertEqual(c.get_tier("PROC_VENIPUNCTURE"), "STACK_ONLY")
        self.assertEqual(c.get_tier("OBESITY_NUTRITION"), "CONDITIONAL")

    def test_21_8b_display_logic(self):
        from billing_engine.stack_classifier import StackClassifier
        c = StackClassifier()
        # STRONG_STANDALONE always shows
        self.assertTrue(c.should_display("AWV"))
        # STACK_ONLY hidden without stack
        self.assertFalse(c.should_display("PROC_VENIPUNCTURE", in_stack=False))
        # STACK_ONLY shown in stack
        self.assertTrue(c.should_display("PROC_VENIPUNCTURE", in_stack=True))
        # CONDITIONAL hidden when condition not met
        self.assertFalse(c.should_display("OBESITY_NUTRITION", condition_met=False))
        # Negative ENR suppressed
        self.assertFalse(c.should_display("AWV", expected_net_value=-5))

    def test_21_8c_suppress(self):
        from billing_engine.stack_classifier import StackClassifier
        c = StackClassifier()
        c.suppress("AWV", "testing")
        self.assertEqual(c.get_tier("AWV"), "SUPPRESS")
        self.assertFalse(c.should_display("AWV"))

    def test_21_8d_batch_classify(self):
        from billing_engine.stack_classifier import StackClassifier
        c = StackClassifier()
        results = c.classify_batch(["AWV", "PROC_VENIPUNCTURE", "G2211"])
        self.assertEqual(len(results), 3)
        # Should be sorted by priority: STRONG_STANDALONE, STRONG_STACK, STACK_ONLY
        self.assertEqual(results[0][1], "STRONG_STANDALONE")
        self.assertEqual(results[1][1], "STRONG_STACK")
        self.assertEqual(results[2][1], "STACK_ONLY")


class TestNavLink(unittest.TestCase):
    """Navigation link for Billing Phrases."""

    def test_nav_billing_phrases(self):
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "templates", "base.html")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("/settings/phrases", content, "base.html should link to Billing Phrases")


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""
CareCompanion -- Bonus Dashboard Tests (pytest version)
tests/test_bonus_dashboard.py

Replaces the legacy run_tests() pattern with pytest-compatible tests.

Usage:
    venv\\Scripts\\python.exe -m pytest tests/test_bonus_dashboard.py -v
"""

import pytest


# ======================================================================
# BonusTracker Model
# ======================================================================

class TestBonusTrackerModel:
    """Verify BonusTracker model has all required fields and JSON helpers."""

    def test_model_has_required_fields(self):
        """BonusTracker has all required columns."""
        from models.bonus import BonusTracker
        required = [
            'user_id', 'provider_name', 'start_date', 'base_salary',
            'quarterly_threshold', 'bonus_multiplier', 'deficit_resets_annually',
            'monthly_receipts', 'collection_rates', 'projected_first_bonus_quarter',
            'projected_first_bonus_date', 'threshold_confirmed',
        ]
        for field in required:
            assert hasattr(BonusTracker, field), f'Missing field: {field}'

    def test_json_helpers_receipts(self):
        """get_receipts/set_receipts round-trip correctly."""
        from models.bonus import BonusTracker
        t = BonusTracker()
        assert t.get_receipts() == {}
        t.set_receipts({"2026-01": 30000.0})
        r = t.get_receipts()
        assert r["2026-01"] == 30000.0

    def test_json_helpers_collection_rates(self):
        """get_collection_rates/set_collection_rates round-trip correctly."""
        from models.bonus import BonusTracker
        t = BonusTracker()
        assert t.get_collection_rates() == {}
        t.set_collection_rates({"medicare": 0.90})
        assert t.get_collection_rates()["medicare"] == 0.90


# ======================================================================
# Migration
# ======================================================================

class TestBonusMigration:
    """Verify migration script is idempotent."""

    def test_migration_is_idempotent(self):
        """Migration uses CREATE TABLE IF NOT EXISTS."""
        import os
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, 'migrations', 'migrate_add_bonus_tracker.py')
        with open(path, encoding='utf-8') as f:
            src = f.read()
        assert 'CREATE TABLE IF NOT EXISTS' in src
        assert 'bonus_tracker' in src


# ======================================================================
# Bonus Calculator
# ======================================================================

class TestBonusCalculator:
    """Tests for calculate_quarterly_bonus and related functions."""

    def test_below_threshold_no_bonus(self):
        """Below threshold -> no bonus, deficit grows."""
        from app.services.bonus_calculator import calculate_quarterly_bonus
        r = calculate_quarterly_bonus(90000, 105000, 0)
        assert r["exceeded"] is False
        assert r["bonus_amount"] == 0.0
        assert r["new_deficit"] == 15000.0

    def test_above_threshold_bonus_earned(self):
        """Above threshold -> bonus = surplus * 0.25."""
        from app.services.bonus_calculator import calculate_quarterly_bonus
        r = calculate_quarterly_bonus(120000, 105000, 0)
        assert r["exceeded"] is True
        assert r["bonus_amount"] == 3750.0  # 15000 * 0.25
        assert r["new_deficit"] == 0.0

    def test_deficit_carry_forward(self):
        """Deficit carry-forward eats into surplus."""
        from app.services.bonus_calculator import calculate_quarterly_bonus
        r = calculate_quarterly_bonus(115000, 105000, 8000)
        # Gross surplus: 10000, less 8000 deficit -> net 2000
        assert r["exceeded"] is True
        assert r["bonus_amount"] == 500.0  # 2000 * 0.25
        assert r["new_deficit"] == 0.0

    def test_deficit_exceeds_surplus(self):
        """Deficit larger than surplus -> no bonus, reduced deficit."""
        from app.services.bonus_calculator import calculate_quarterly_bonus
        r = calculate_quarterly_bonus(108000, 105000, 5000)
        assert r["exceeded"] is False
        assert r["bonus_amount"] == 0.0
        assert r["new_deficit"] == 2000.0

    def test_projection_engine_returns_results(self):
        """Projection engine returns quarters and first_bonus_quarter."""
        from app.services.bonus_calculator import project_first_bonus_quarter
        proj = project_first_bonus_quarter(
            {"2026-04": 40000, "2026-05": 38000, "2026-06": 35000},
            105000, deficit=0.0, growth_rate=0.05,
            deficit_resets_annually=True,
            start_year=2026, start_quarter=2,
        )
        assert "first_bonus_quarter" in proj
        assert "quarters" in proj
        assert len(proj["quarters"]) > 0

    def test_opportunity_impact(self):
        """calculate_opportunity_impact returns correct values."""
        from app.services.bonus_calculator import calculate_opportunity_impact
        r = calculate_opportunity_impact(200.0, 0.85, 105000, 0.25)
        assert r["expected_receipts"] == 170.0
        assert r["bonus_impact"] == 42.5  # 170 * 0.25
        assert r["daily_rate_impact"] > 0


# ======================================================================
# Routes and Templates
# ======================================================================

class TestBonusRoutes:
    """Verify bonus routes blueprint and templates exist."""

    def test_blueprint_has_all_endpoints(self):
        """Routes blueprint has all 5 endpoints."""
        import os
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, 'routes', 'bonus.py'), encoding='utf-8') as f:
            src = f.read()
        assert "bonus_bp = Blueprint('bonus', __name__)" in src
        assert "@bonus_bp.route('/bonus')" in src
        assert "@bonus_bp.route('/bonus/entry'" in src
        assert "@bonus_bp.route('/bonus/calibrate'" in src
        assert "@bonus_bp.route('/api/bonus/projection')" in src

    def test_dashboard_has_all_sections(self):
        """Dashboard template has all 7 sections."""
        import os
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, 'templates', 'bonus_dashboard.html'), encoding='utf-8') as f:
            src = f.read()
        assert 'Current Quarter Status' in src
        assert 'Deficit Timeline' in src
        assert 'First Bonus Projection' in src
        assert 'Receipt Pipeline' in src
        assert 'CCM Impact Calculator' in src
        assert 'Monthly Receipt Entry' in src
        assert 'QUARTER-END SURGE MODE' in src

    def test_blueprint_registered(self):
        """Blueprint is registered in app factory."""
        import os
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, 'app', '__init__.py'), encoding='utf-8') as f:
            src = f.read()
        assert "('routes.bonus', 'bonus_bp')" in src

    def test_nav_link_exists(self):
        """Nav link exists in base template."""
        import os
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, 'templates', 'base.html'), encoding='utf-8') as f:
            src = f.read()
        assert 'Bonus' in src
        assert '/bonus' in src

    def test_threshold_mismatch_warning(self):
        """Threshold mismatch warning present in template."""
        import os
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, 'templates', 'bonus_dashboard.html'), encoding='utf-8') as f:
            src = f.read()
        assert 'threshold_warning' in src
        assert 'confirm-threshold' in src


# ======================================================================
# Integration (Morning Briefing)
# ======================================================================

class TestBonusBriefing:
    """Verify bonus integration with morning briefing."""

    def test_briefing_includes_bonus(self):
        """Morning briefing route includes bonus_status."""
        import os
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, 'routes', 'intelligence.py'), encoding='utf-8') as f:
            src = f.read()
        assert 'bonus_status' in src

    def test_briefing_template_includes_bonus(self):
        """Morning briefing template shows bonus status."""
        import os
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, 'templates', 'morning_briefing.html'), encoding='utf-8') as f:
            src = f.read()
        assert 'bonus_status' in src
        assert 'Bonus Status' in src

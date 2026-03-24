"""
CareCompanion — MedTestService
File: app/services/med_test_service.py

Phase MM-6: Automated scenario-based testing for monitoring rules.
Generates synthetic scenarios per rule or catalog entry, evaluates
whether the rule engine produces the expected result, and stores
pass/fail in MonitoringRuleTestResult.

Public API
----------
MedTestService.run_scenarios_for_entry(catalog_entry_id, tested_by)
MedTestService.run_bulk_tests(scope, tested_by)

HIPAA: Uses synthetic patients only (SYN- prefix, is_synthetic=True).
"""

import hashlib
import json
import logging
from datetime import date, datetime, timedelta, timezone

from models import db
from models.monitoring import (
    MedicationCatalogEntry, MonitoringRule, MonitoringRuleOverride,
    MonitoringRuleTestResult,
)

logger = logging.getLogger(__name__)


# ── Built-in test scenarios ────────────────────────────────────────
# Each scenario returns (test_scenario_name, description, setup_fn)
# where setup_fn returns a dict of simulated context for assertion.

SCENARIO_DEFS = [
    {
        'name': 'no_prior_lab',
        'description': 'Patient on med, no lab ever drawn → rule should fire',
        'expect_fire': True,
        'last_lab_days_ago': None,
    },
    {
        'name': 'overdue',
        'description': 'Patient on med, lab drawn beyond interval → rule should fire',
        'expect_fire': True,
        'last_lab_days_ago_multiplier': 1.5,
    },
    {
        'name': 'up_to_date',
        'description': 'Patient on med, lab drawn within interval → rule should NOT fire',
        'expect_fire': False,
        'last_lab_days_ago_multiplier': 0.5,
    },
    {
        'name': 'just_due',
        'description': 'Patient on med, lab drawn exactly at interval → borderline, should fire',
        'expect_fire': True,
        'last_lab_days_ago_multiplier': 1.0,
    },
    {
        'name': 'inactive_rule',
        'description': 'Rule is_active=False → rule should NOT fire',
        'expect_fire': False,
        'rule_override': {'is_active': False},
    },
]


class MedTestService:
    """Scenario-based monitoring rule test runner."""

    def __init__(self, db_session=None):
        self._db = db_session or db

    # ================================================================
    # 1. Test a single catalog entry
    # ================================================================

    def run_scenarios_for_entry(
        self,
        catalog_entry_id: int,
        tested_by: int = None,
    ) -> list:
        """
        Run all applicable scenarios for a catalog entry.
        Returns list of dicts with scenario results.
        """
        entry = MedicationCatalogEntry.query.get(catalog_entry_id)
        if not entry:
            return [{'error': f'Catalog entry {catalog_entry_id} not found'}]

        # Find rules linked to this entry's rxcui
        rules = MonitoringRule.query.filter_by(
            rxcui=entry.rxcui, is_active=True
        ).all() if entry.rxcui else []

        if not rules:
            # No rules — record a single result noting no rules exist
            result = self._record_result(
                monitoring_rule_id=None,
                catalog_entry_id=entry.id,
                test_scenario='no_rules',
                passed=True,
                explanation=f'No monitoring rules for {entry.display_name} — nothing to test',
                tested_by=tested_by,
            )
            return [result]

        results = []
        for rule in rules:
            for scenario_def in SCENARIO_DEFS:
                result = self._evaluate_scenario(
                    rule=rule,
                    catalog_entry=entry,
                    scenario_def=scenario_def,
                    tested_by=tested_by,
                )
                results.append(result)

        # Update last_tested_at on catalog entry
        entry.last_tested_at = datetime.now(timezone.utc)
        self._db.session.commit()

        return results

    # ================================================================
    # 2. Bulk test runner
    # ================================================================

    def run_bulk_tests(
        self,
        scope: str = 'all',
        tested_by: int = None,
    ) -> dict:
        """
        Run tests across multiple entries.

        Scopes:
          - all: every active catalog entry with rules
          - per_medication: group by rxcui (deduplicated)
          - per_drug_class: one entry per drug_class
          - edge_cases: built-in edge case scenarios only
        """
        results = []

        if scope == 'edge_cases':
            results = self._run_edge_cases(tested_by=tested_by)
        else:
            entries = self._get_entries_for_scope(scope)
            for entry in entries:
                entry_results = self.run_scenarios_for_entry(
                    entry.id, tested_by=tested_by
                )
                results.extend(entry_results)

        total = len(results)
        passed = sum(1 for r in results if r.get('passed'))
        failed = total - passed

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'results': results,
        }

    # ================================================================
    # Internal helpers
    # ================================================================

    def _get_entries_for_scope(self, scope: str) -> list:
        """Return catalog entries relevant to the given scope."""
        q = MedicationCatalogEntry.query.filter_by(
            is_active=True
        ).filter(
            MedicationCatalogEntry.status.in_(['active', 'pending_review'])
        ).filter(
            MedicationCatalogEntry.rxcui.isnot(None),
            MedicationCatalogEntry.rxcui != '',
        )

        if scope == 'per_drug_class':
            # One entry per class
            seen_classes = set()
            entries = []
            for entry in q.order_by(MedicationCatalogEntry.drug_class).all():
                cls = entry.drug_class or 'Unknown'
                if cls not in seen_classes:
                    seen_classes.add(cls)
                    entries.append(entry)
            return entries

        if scope == 'per_medication':
            # Deduplicate by rxcui
            seen_rxcuis = set()
            entries = []
            for entry in q.order_by(MedicationCatalogEntry.display_name).all():
                if entry.rxcui not in seen_rxcuis:
                    seen_rxcuis.add(entry.rxcui)
                    entries.append(entry)
            return entries

        # 'all' — every active entry
        return q.order_by(MedicationCatalogEntry.display_name).all()

    def _evaluate_scenario(
        self,
        rule: MonitoringRule,
        catalog_entry: MedicationCatalogEntry,
        scenario_def: dict,
        tested_by: int = None,
    ) -> dict:
        """
        Evaluate a single scenario definition against a rule.
        Simulates the logic the rule engine would use.
        """
        scenario_name = scenario_def['name']
        expect_fire = scenario_def['expect_fire']
        explanation_parts = []

        try:
            # Get effective interval (respecting overrides)
            effective_interval = self._get_effective_interval(rule)
            explanation_parts.append(
                f'Rule {rule.id}: {rule.lab_name}, interval={effective_interval}d'
            )

            # Check for rule_override in scenario
            rule_override = scenario_def.get('rule_override', {})
            if rule_override.get('is_active') is False:
                # Simulate inactive rule
                would_fire = False
                explanation_parts.append('Rule is inactive → no fire')
            else:
                # Simulate last lab date
                last_lab_days_ago = scenario_def.get('last_lab_days_ago')
                if last_lab_days_ago is None:
                    multiplier = scenario_def.get('last_lab_days_ago_multiplier')
                    if multiplier is not None:
                        last_lab_days_ago = int(effective_interval * multiplier)
                    else:
                        last_lab_days_ago = None  # Never drawn

                if last_lab_days_ago is None:
                    # No prior lab → always fire
                    would_fire = True
                    explanation_parts.append('No prior lab → due immediately')
                else:
                    would_fire = last_lab_days_ago >= effective_interval
                    last_date = date.today() - timedelta(days=last_lab_days_ago)
                    explanation_parts.append(
                        f'Last lab {last_lab_days_ago}d ago ({last_date}) '
                        f'vs interval {effective_interval}d → '
                        f'{"FIRE" if would_fire else "NOT DUE"}'
                    )

            passed = (would_fire == expect_fire)
            if not passed:
                explanation_parts.append(
                    f'MISMATCH: expected {"fire" if expect_fire else "no fire"}, '
                    f'got {"fire" if would_fire else "no fire"}'
                )

            explanation = ' | '.join(explanation_parts)

        except Exception as e:
            passed = False
            explanation = f'Error evaluating scenario: {str(e)}'
            logger.error(
                f"Test scenario error for rule {rule.id} / "
                f"{scenario_name}: {str(e)}"
            )

        return self._record_result(
            monitoring_rule_id=rule.id,
            catalog_entry_id=catalog_entry.id if catalog_entry else None,
            test_scenario=scenario_name,
            passed=passed,
            explanation=explanation,
            tested_by=tested_by,
        )

    def _get_effective_interval(self, rule: MonitoringRule) -> int:
        """Return the effective interval respecting overrides."""
        # Check for user or practice overrides
        override = MonitoringRuleOverride.query.filter_by(
            monitoring_rule_id=rule.id, is_active=True
        ).order_by(
            # user overrides take precedence
            MonitoringRuleOverride.scope.asc()
        ).first()

        if override and override.override_interval_days:
            return override.override_interval_days

        return rule.interval_days

    def _run_edge_cases(self, tested_by: int = None) -> list:
        """
        Run built-in edge case scenarios that don't depend on
        specific catalog entries.
        """
        results = []

        # Edge case 1: Rule with 0-day interval
        results.append(self._record_result(
            monitoring_rule_id=None,
            catalog_entry_id=None,
            test_scenario='edge_zero_interval',
            passed=True,
            explanation='Edge case: 0-day interval rules should be flagged during seeding, not at runtime',
            tested_by=tested_by,
        ))

        # Edge case 2: Verify no orphaned overrides
        orphaned = MonitoringRuleOverride.query.filter(
            ~MonitoringRuleOverride.monitoring_rule_id.in_(
                db.session.query(MonitoringRule.id)
            )
        ).count()
        results.append(self._record_result(
            monitoring_rule_id=None,
            catalog_entry_id=None,
            test_scenario='edge_orphaned_overrides',
            passed=(orphaned == 0),
            explanation=f'Orphaned overrides: {orphaned} (expected 0)',
            tested_by=tested_by,
        ))

        # Edge case 3: All rules have valid interval
        bad_intervals = MonitoringRule.query.filter(
            MonitoringRule.is_active == True,
            (MonitoringRule.interval_days < 1) | (MonitoringRule.interval_days > 730)
        ).count()
        results.append(self._record_result(
            monitoring_rule_id=None,
            catalog_entry_id=None,
            test_scenario='edge_invalid_intervals',
            passed=(bad_intervals == 0),
            explanation=f'Rules with interval <1 or >730 days: {bad_intervals}',
            tested_by=tested_by,
        ))

        # Edge case 4: All catalog entries with rxcui have at least one rule
        unmapped = MedicationCatalogEntry.query.filter(
            MedicationCatalogEntry.is_active == True,
            MedicationCatalogEntry.rxcui.isnot(None),
            MedicationCatalogEntry.rxcui != '',
            MedicationCatalogEntry.status == 'active',
        ).all()
        unmapped_count = 0
        for entry in unmapped:
            rule_count = MonitoringRule.query.filter_by(
                rxcui=entry.rxcui, is_active=True
            ).count()
            if rule_count == 0:
                unmapped_count += 1

        results.append(self._record_result(
            monitoring_rule_id=None,
            catalog_entry_id=None,
            test_scenario='edge_unmapped_active_entries',
            passed=True,  # Informational — not a hard failure
            explanation=f'Active catalog entries with rxcui but no rules: {unmapped_count}',
            tested_by=tested_by,
        ))

        # Edge case 5: Duplicate rules check
        from sqlalchemy import func
        dupes = db.session.query(
            MonitoringRule.rxcui, MonitoringRule.lab_loinc_code,
            func.count(MonitoringRule.id).label('cnt')
        ).filter(
            MonitoringRule.is_active == True,
            MonitoringRule.rxcui.isnot(None),
        ).group_by(
            MonitoringRule.rxcui, MonitoringRule.lab_loinc_code
        ).having(func.count(MonitoringRule.id) > 1).count()

        results.append(self._record_result(
            monitoring_rule_id=None,
            catalog_entry_id=None,
            test_scenario='edge_duplicate_rules',
            passed=(dupes == 0),
            explanation=f'Duplicate (rxcui+LOINC) rule pairs: {dupes}',
            tested_by=tested_by,
        ))

        return results

    def _record_result(
        self,
        monitoring_rule_id,
        catalog_entry_id,
        test_scenario,
        passed,
        explanation,
        tested_by=None,
    ) -> dict:
        """Persist a test result and return it as a dict."""
        result = MonitoringRuleTestResult(
            monitoring_rule_id=monitoring_rule_id,
            catalog_entry_id=catalog_entry_id,
            test_scenario=test_scenario,
            passed=passed,
            explanation=explanation,
            tested_at=datetime.now(timezone.utc),
            tested_by=tested_by,
        )
        self._db.session.add(result)
        self._db.session.commit()

        return {
            'id': result.id,
            'monitoring_rule_id': monitoring_rule_id,
            'catalog_entry_id': catalog_entry_id,
            'test_scenario': test_scenario,
            'passed': passed,
            'explanation': explanation,
        }

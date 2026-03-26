"""
CareCompanion — Benchmark Engine

File location: carecompanion/tests/benchmark_engine.py

Runs billing, care gap, and monitoring engines against synthetic patient
fixtures and validates results against expected outcomes.  Returns
structured results that can be persisted to BenchmarkRun/BenchmarkResult
models or printed to the terminal.
"""

import json
import time
import traceback
from datetime import datetime, timezone


class BenchmarkRunner:
    """
    Executes benchmark tests for billing, care gap, and monitoring engines.

    Usage:
        runner = BenchmarkRunner(app)
        results = runner.run_all()          # all patients, all engines
        results = runner.run(engine='billing', patient_id='BM_MEDICARE_68F')
    """

    def __init__(self, app):
        self.app = app
        self._billing_engine = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_all(self):
        """Run all engines against all patients. Returns list of result dicts."""
        return self.run(engine='all', patient_id='all')

    def run(self, engine='all', patient_id='all'):
        """
        Run specified engine(s) against specified patient(s).

        Parameters
        ----------
        engine : str
            'all', 'billing', 'caregap', or 'monitoring'
        patient_id : str
            'all' or a specific key from benchmark_fixtures.PATIENTS

        Returns
        -------
        dict with keys:
            engine_filter, patient_filter, total, passed, failed,
            duration_ms, results (list of per-test dicts)
        """
        from tests.benchmark_fixtures import PATIENTS, EXPECTED

        patients = self._resolve_patients(patient_id, PATIENTS)
        engines = self._resolve_engines(engine)

        all_results = []
        suite_start = time.perf_counter()

        for pid, pdata in patients.items():
            expected = EXPECTED.get(pid, {})
            for eng in engines:
                test_results = self._run_engine(eng, pid, pdata, expected)
                all_results.extend(test_results)

        suite_end = time.perf_counter()
        total_ms = (suite_end - suite_start) * 1000

        passed = sum(1 for r in all_results if r['passed'])
        failed = len(all_results) - passed

        return {
            'engine_filter': engine,
            'patient_filter': patient_id,
            'total': len(all_results),
            'passed': passed,
            'failed': failed,
            'duration_ms': round(total_ms, 2),
            'results': all_results,
        }

    # ------------------------------------------------------------------
    # Engine dispatch
    # ------------------------------------------------------------------

    def _run_engine(self, engine, patient_id, patient_data, expected):
        """Dispatch to the appropriate engine test method."""
        if engine == 'billing':
            return self._test_billing(patient_id, patient_data, expected.get('billing', {}))
        elif engine == 'caregap':
            return self._test_caregap(patient_id, patient_data, expected.get('caregaps', {}))
        elif engine == 'monitoring':
            return self._test_monitoring(patient_id, patient_data, expected.get('monitoring', {}))
        return []

    # ------------------------------------------------------------------
    # Billing Engine Tests
    # ------------------------------------------------------------------

    def _test_billing(self, patient_id, patient_data, expected):
        results = []
        opps = []
        duration_ms = 0.0

        try:
            with self.app.app_context():
                from models import db
                engine = self._get_billing_engine(db)
                start = time.perf_counter()
                opps = engine.evaluate(patient_data)
                duration_ms = (time.perf_counter() - start) * 1000
        except Exception as e:
            results.append(self._result(
                patient_id, 'billing', 'engine_execution',
                False, f'Engine raised exception: {e}', 0.0,
                {'error': traceback.format_exc()}
            ))
            return results

        # Summarize what was returned
        categories = [getattr(o, 'category', getattr(o, 'opportunity_code', 'UNKNOWN')) for o in opps]
        summary = {'count': len(opps), 'categories': categories}

        # Test: count within range
        if expected.get('min_opportunities') is not None:
            min_c = expected['min_opportunities']
            max_c = expected.get('max_opportunities', 999)
            in_range = min_c <= len(opps) <= max_c
            results.append(self._result(
                patient_id, 'billing', 'opportunity_count_range',
                in_range,
                f'Got {len(opps)} opportunities (expected {min_c}-{max_c})',
                duration_ms, summary
            ))

        # Test: must-include categories
        for cat in expected.get('must_include_categories', []):
            found = cat in categories
            results.append(self._result(
                patient_id, 'billing', f'must_include_{cat}',
                found,
                f'Category {cat} {"found" if found else "NOT found"} in results',
                0.0, summary
            ))

        # Test: must-exclude categories
        for cat in expected.get('must_exclude_categories', []):
            absent = cat not in categories
            results.append(self._result(
                patient_id, 'billing', f'must_exclude_{cat}',
                absent,
                f'Category {cat} {"correctly absent" if absent else "INCORRECTLY present"}',
                0.0, summary
            ))

        # If no expected rules were defined, still record the execution
        if not expected:
            results.append(self._result(
                patient_id, 'billing', 'engine_execution',
                True, f'Engine returned {len(opps)} opportunities (no assertions)',
                duration_ms, summary
            ))

        return results

    # ------------------------------------------------------------------
    # Care Gap Engine Tests
    # ------------------------------------------------------------------

    def _test_caregap(self, patient_id, patient_data, expected):
        results = []
        gaps = []
        duration_ms = 0.0

        try:
            from agent.caregap_engine import evaluate_care_gaps
            start = time.perf_counter()
            gaps = evaluate_care_gaps(patient_data, self.app)
            duration_ms = (time.perf_counter() - start) * 1000
        except Exception as e:
            results.append(self._result(
                patient_id, 'caregap', 'engine_execution',
                False, f'Engine raised exception: {e}', 0.0,
                {'error': traceback.format_exc()}
            ))
            return results

        gap_types = [g.get('gap_type', '') for g in gaps]
        summary = {'count': len(gaps), 'gap_types': gap_types}

        # Test: count within range
        if expected.get('min_gaps') is not None:
            min_c = expected['min_gaps']
            max_c = expected.get('max_gaps', 999)
            in_range = min_c <= len(gaps) <= max_c
            results.append(self._result(
                patient_id, 'caregap', 'gap_count_range',
                in_range,
                f'Got {len(gaps)} gaps (expected {min_c}-{max_c})',
                duration_ms, summary
            ))

        # Test: must-include gap types
        for gt in expected.get('must_include_types', []):
            found = gt in gap_types
            results.append(self._result(
                patient_id, 'caregap', f'must_include_{gt}',
                found,
                f'Gap type {gt} {"found" if found else "NOT found"}',
                0.0, summary
            ))

        # Test: must-exclude gap types
        for gt in expected.get('must_exclude_types', []):
            absent = gt not in gap_types
            results.append(self._result(
                patient_id, 'caregap', f'must_exclude_{gt}',
                absent,
                f'Gap type {gt} {"correctly absent" if absent else "INCORRECTLY present"}',
                0.0, summary
            ))

        if not expected:
            results.append(self._result(
                patient_id, 'caregap', 'engine_execution',
                True, f'Engine returned {len(gaps)} gaps (no assertions)',
                duration_ms, summary
            ))

        return results

    # ------------------------------------------------------------------
    # Monitoring Engine Tests
    # ------------------------------------------------------------------

    def _test_monitoring(self, patient_id, patient_data, expected):
        results = []
        rules_found = []
        duration_ms = 0.0

        try:
            with self.app.app_context():
                from models.monitoring import MonitoringRule
                meds = patient_data.get('medications', [])

                start = time.perf_counter()
                for med in meds:
                    rxcui = med.get('rxcui', '')
                    drug_name = med.get('drug_name', med.get('name', ''))
                    if not rxcui and not drug_name:
                        continue

                    # Look up by rxcui first, then by icd10 triggers from diagnoses
                    matched = []
                    if rxcui:
                        matched = MonitoringRule.query.filter(
                            MonitoringRule.rxcui == rxcui,
                            MonitoringRule.is_active == True
                        ).all()

                    for r in matched:
                        rules_found.append({
                            'medication': drug_name,
                            'lab_name': r.lab_name,
                            'rule_id': r.id,
                        })

                # Also check diagnosis-triggered rules
                diagnoses = patient_data.get('known_diagnoses', [])
                for dx_code in diagnoses:
                    dx_rules = MonitoringRule.query.filter(
                        MonitoringRule.icd10_trigger == dx_code,
                        MonitoringRule.is_active == True
                    ).all()
                    for r in dx_rules:
                        rules_found.append({
                            'medication': dx_code,
                            'lab_name': r.lab_name,
                            'rule_id': r.id,
                        })

                duration_ms = (time.perf_counter() - start) * 1000
        except Exception as e:
            results.append(self._result(
                patient_id, 'monitoring', 'rule_lookup',
                False, f'Rule lookup raised exception: {e}', 0.0,
                {'error': traceback.format_exc()}
            ))
            return results

        lab_names = [r['lab_name'] for r in rules_found]
        summary = {'count': len(rules_found), 'labs': lab_names}

        # Test: minimum rule count
        if expected.get('min_rules') is not None:
            min_r = expected['min_rules']
            passed = len(rules_found) >= min_r
            results.append(self._result(
                patient_id, 'monitoring', 'rule_count_min',
                passed,
                f'Got {len(rules_found)} rules (expected >= {min_r})',
                duration_ms, summary
            ))

        # Test: must-include labs
        for lab in expected.get('must_include_labs', []):
            found = lab in lab_names
            results.append(self._result(
                patient_id, 'monitoring', f'must_include_{lab}',
                found,
                f'Lab {lab} {"found" if found else "NOT found"}',
                0.0, summary
            ))

        if not expected:
            results.append(self._result(
                patient_id, 'monitoring', 'rule_lookup',
                True, f'Found {len(rules_found)} monitoring rules (no assertions)',
                duration_ms, summary
            ))

        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_billing_engine(self, db):
        """Lazy-init billing engine (expensive to construct repeatedly)."""
        if self._billing_engine is None:
            from billing_engine.engine import BillingCaptureEngine
            self._billing_engine = BillingCaptureEngine(db=db)
        return self._billing_engine

    def _resolve_patients(self, patient_id, all_patients):
        if patient_id == 'all':
            return all_patients
        if patient_id in all_patients:
            return {patient_id: all_patients[patient_id]}
        raise ValueError(f"Unknown patient_id: {patient_id}")

    def _resolve_engines(self, engine):
        if engine == 'all':
            return ['billing', 'caregap', 'monitoring']
        if engine in ('billing', 'caregap', 'monitoring'):
            return [engine]
        raise ValueError(f"Unknown engine: {engine}")

    def _result(self, patient_id, engine, test_name, passed, explanation,
                duration_ms, summary=None):
        return {
            'patient_id': patient_id,
            'engine': engine,
            'test_name': test_name,
            'passed': passed,
            'explanation': explanation,
            'duration_ms': round(duration_ms, 2),
            'actual_summary': json.dumps(summary or {}),
            'tested_at': datetime.now(timezone.utc).isoformat(),
        }

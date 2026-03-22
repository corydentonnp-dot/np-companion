"""
CareCompanion - Billing Opportunity Rules Engine (Thin Wrapper)
File: app/services/billing_rules.py

This module is a backwards-compatible wrapper that delegates all billing
opportunity detection to the new modular billing_engine package.

Existing callers (routes, scheduler, tests) continue using
BillingRulesEngine.evaluate_patient() with zero changes.

The actual detection logic lives in billing_engine/detectors/*.py.
The BillingCaptureEngine orchestrator in billing_engine/engine.py
auto-discovers and runs all detectors.

All billing decisions remain with the provider. This engine only flags and
suggests - it never submits anything to a payer.

HIPAA note: patient_mrn_hash (SHA-256) is used - never the plain MRN.
"""

import logging

logger = logging.getLogger(__name__)

# Re-export hash_mrn from shared module for backward compatibility
from billing_engine.shared import hash_mrn  # noqa: F401


class BillingRulesEngine:
    """
    Backwards-compatible facade over the modular BillingCaptureEngine.

    Callers interact with this class exactly as before:
        engine = BillingRulesEngine(db, cms_pfs_service)
        opps = engine.evaluate_patient(patient_data)

    Internally, all work is delegated to billing_engine.engine.BillingCaptureEngine.
    """

    def __init__(self, db, cms_pfs_service=None):
        from billing_engine.engine import BillingCaptureEngine
        self._engine = BillingCaptureEngine(db, cms_pfs_service)

    def evaluate_patient(self, patient_data: dict) -> list:
        """
        Evaluate a patient visit for all billing opportunities.

        Parameters
        ----------
        patient_data : dict
            Must include: patient_mrn, user_id, visit_date, insurer,
            diagnoses, medications, age, and additional clinical data.

        Returns
        -------
        list[BillingOpportunity]
            De-duplicated, priority-sorted billing opportunities.
        """
        return self._engine.evaluate(patient_data)

"""
CareCompanion — Billing Capture Engine Package

Modular, DB-configurable, payer-aware billing capture system.
Detectors live in billing_engine/detectors/ and are auto-discovered
by the BillingCaptureEngine orchestrator.
"""

from billing_engine.engine import BillingCaptureEngine

__all__ = ["BillingCaptureEngine"]

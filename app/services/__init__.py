"""
NP Companion — Services Package
File: app/services/__init__.py

Contains the service layer between the Flask routes and external APIs:
- api/         — Individual API client modules (one per external service)
- billing_rules.py — CMS billing opportunity engine (seven rule categories)
- api_scheduler.py — Background job definitions for the API intelligence layer

NP Companion features that rely on this package:
- API Intelligence Layer (Phase 10A/10B from NP_Companion_Development_Guide.md)
- Billing Opportunity Engine (from np_companion_api_intelligence_plan.md Addendum)
"""

"""
NP Companion — App Package
File: app/__init__.py

This package contains the API configuration (api_config.py) and the
services sub-package (services/). It is separate from the Flask app
factory in the project root (app.py) to keep configuration and service
logic isolated from the web layer.

NP Companion features that use this package:
- All API intelligence features (Phase 10A/10B from development guide)
- Billing opportunity engine (billing_rules.py)
- Background API job scheduler (api_scheduler.py)
"""

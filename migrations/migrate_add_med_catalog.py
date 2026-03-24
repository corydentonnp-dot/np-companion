"""
Medication Monitoring Catalog & QA — Phase MM-1 Migration

Creates five new tables for the Med Monitoring Master Catalog:
  - medication_catalog_entry
  - monitoring_rule_override
  - monitoring_evaluation_log
  - monitoring_rule_test_result
  - monitoring_rule_diff

Idempotent — safe to run multiple times.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


NEW_TABLES = [
    'medication_catalog_entry',
    'monitoring_rule_override',
    'monitoring_evaluation_log',
    'monitoring_rule_test_result',
    'monitoring_rule_diff',
]


def run_migration(app, db):
    """Called by _run_pending_migrations in app/__init__.py."""
    from sqlalchemy import inspect
    from models.monitoring import (
        MedicationCatalogEntry, MonitoringRuleOverride,
        MonitoringEvaluationLog, MonitoringRuleTestResult,
        MonitoringRuleDiff,
    )

    model_map = {
        'medication_catalog_entry': MedicationCatalogEntry,
        'monitoring_rule_override': MonitoringRuleOverride,
        'monitoring_evaluation_log': MonitoringEvaluationLog,
        'monitoring_rule_test_result': MonitoringRuleTestResult,
        'monitoring_rule_diff': MonitoringRuleDiff,
    }

    with app.app_context():
        inspector = inspect(db.engine)
        existing = set(inspector.get_table_names())

        created = []
        for table_name in NEW_TABLES:
            if table_name not in existing:
                model_map[table_name].__table__.create(db.engine)
                created.append(table_name)
                print(f'  ✅ Created table: {table_name}')
            else:
                print(f'  ✅ {table_name} already exists')

        if created:
            print(f'Migration complete — created {len(created)} table(s).')
        else:
            print('Migration complete — all tables already exist.')


if __name__ == '__main__':
    from app import create_app
    from models import db
    a = create_app()
    run_migration(a, db)

"""
Phase 31 — Calculator Results Migration

Creates the calculator_result table for storing clinical risk score computations.
Idempotent — safe to run multiple times.

Uses run_migration(app, db) so _run_pending_migrations() calls it in-process
instead of spawning a subprocess (which would cause infinite recursion via
create_app → _run_pending_migrations → subprocess → create_app).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_migration(app, db):
    """Called by _run_pending_migrations in app/__init__.py."""
    from sqlalchemy import inspect, text

    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if 'calculator_result' not in tables:
            from models.calculator import CalculatorResult
            CalculatorResult.__table__.create(db.engine)
            print('  ✅ Created table: calculator_result')
        else:
            # Verify columns are all present
            existing_cols = {c['name'] for c in inspector.get_columns('calculator_result')}
            required_cols = {
                'id', 'user_id', 'mrn', 'calculator_key', 'score_value',
                'score_label', 'score_detail', 'input_snapshot', 'data_source',
                'is_current', 'computed_at', 'created_at'
            }
            missing = required_cols - existing_cols
            if missing:
                for col in missing:
                    col_map = {
                        'score_value': 'REAL',
                        'score_label': 'VARCHAR(100)',
                        'score_detail': 'TEXT',
                        'input_snapshot': 'TEXT',
                        'data_source': 'VARCHAR(20)',
                        'is_current': 'BOOLEAN DEFAULT 1',
                        'computed_at': 'DATETIME',
                        'created_at': 'DATETIME',
                    }
                    ddl = col_map.get(col, 'TEXT')
                    db.session.execute(text(f'ALTER TABLE calculator_result ADD COLUMN {col} {ddl}'))
                db.session.commit()
                print(f'  ✅ Added missing columns: {missing}')
            else:
                print('  ✅ calculator_result table already up to date')

        print('Migration complete.')


if __name__ == '__main__':
    from app import create_app
    from models import db
    a = create_app()
    run_migration(a, db)

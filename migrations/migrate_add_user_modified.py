"""Add user_modified column to patient_medications table.

Run: venv\\Scripts\\python.exe migrations\\migrate_add_user_modified.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db

def migrate():
    app = create_app()
    with app.app_context():
        with db.engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(db.text(
                "PRAGMA table_info('patient_medications')"
            ))
            cols = [row[1] for row in result.fetchall()]
            if 'user_modified' in cols:
                print('Column user_modified already exists — skipping.')
                return
            conn.execute(db.text(
                "ALTER TABLE patient_medications ADD COLUMN user_modified BOOLEAN DEFAULT 0"
            ))
            conn.commit()
            print('Added user_modified column to patient_medications.')

if __name__ == '__main__':
    migrate()

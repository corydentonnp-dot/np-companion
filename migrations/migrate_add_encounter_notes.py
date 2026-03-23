"""
Migration: Add patient_encounter_notes table for prior encounter notes.

Run: venv\Scripts\python.exe migrations/migrate_add_encounter_notes.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db

app = create_app()

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS patient_encounter_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    mrn VARCHAR(20) NOT NULL,
    encounter_date DATETIME,
    provider_name VARCHAR(200) DEFAULT '',
    note_type VARCHAR(50) DEFAULT 'Progress Note',
    note_text TEXT DEFAULT '',
    location VARCHAR(200) DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS ix_patient_encounter_notes_user_id ON patient_encounter_notes(user_id);",
    "CREATE INDEX IF NOT EXISTS ix_patient_encounter_notes_mrn ON patient_encounter_notes(mrn);",
]

if __name__ == '__main__':
    with app.app_context():
        db.engine.execute(CREATE_SQL)
        for idx in INDEX_SQL:
            db.engine.execute(idx)
        print("Migration complete: patient_encounter_notes table created.")

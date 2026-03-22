"""
Migration: Create result_templates table and seed default templates.

Run once:
    python migrate_add_result_templates.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')

SEED_TEMPLATES = [
    # --- Normal results ---
    ('Normal Lab Results', 'normal', 1,
     'Dear {patient_name},\n\nYour recent {test_name} results are normal. No further action is needed at this time.\n\nPlease continue your current medications and follow up as previously scheduled.\n\nBest regards,\nYour Provider'),
    ('Normal Imaging', 'normal', 2,
     'Dear {patient_name},\n\nYour recent imaging study ({test_name}) came back normal with no concerning findings.\n\nNo further workup is needed. Continue routine follow-up.\n\nBest regards,\nYour Provider'),
    ('Normal Screening', 'normal', 3,
     'Dear {patient_name},\n\nYour {test_name} screening results are within normal limits. We recommend repeating this screening per standard guidelines.\n\nBest regards,\nYour Provider'),
    # --- Abnormal results ---
    ('Abnormal Lab — Needs Repeat', 'abnormal', 1,
     'Dear {patient_name},\n\nYour recent {test_name} result ({result_value}) was slightly outside the normal range. We would like to repeat this test in 4-6 weeks.\n\nPlease call the office to schedule a follow-up lab draw.\n\nBest regards,\nYour Provider'),
    ('Abnormal Lab — Medication Adjustment', 'abnormal', 2,
     'Dear {patient_name},\n\nYour {test_name} result ({result_value}) indicates we need to adjust your medication. Please call the office to discuss the change.\n\nContinue your current medications until we speak.\n\nBest regards,\nYour Provider'),
    ('Abnormal Imaging — Follow-Up Needed', 'abnormal', 3,
     'Dear {patient_name},\n\nYour recent {test_name} showed findings that need further evaluation. Please call the office to schedule a follow-up appointment so we can discuss the results and next steps.\n\nBest regards,\nYour Provider'),
    # --- Critical results ---
    ('Critical Result — Urgent', 'critical', 1,
     'Dear {patient_name},\n\nYour {test_name} result ({result_value}) requires urgent attention. Please call our office immediately or go to the nearest emergency room if you are experiencing symptoms.\n\nBest regards,\nYour Provider'),
    ('Critical Result — ER Referral', 'critical', 2,
     'Dear {patient_name},\n\nYour {test_name} result ({result_value}) is critically abnormal. Please proceed to the nearest emergency department for immediate evaluation.\n\nWe have been notified and will follow up with the ER team.\n\nBest regards,\nYour Provider'),
    # --- Follow-up needed ---
    ('Follow-Up Appointment Needed', 'follow_up', 1,
     'Dear {patient_name},\n\nBased on your recent {test_name} results, we need to see you for a follow-up visit. Please call the office to schedule an appointment within the next 2-4 weeks.\n\nBest regards,\nYour Provider'),
    ('Follow-Up — Specialist Consult', 'follow_up', 2,
     'Dear {patient_name},\n\nYour {test_name} results suggest that a specialist consultation would be beneficial. We are preparing a referral and will contact you with the appointment details.\n\nBest regards,\nYour Provider'),
    ('Follow-Up — Repeat Testing', 'follow_up', 3,
     'Dear {patient_name},\n\nWe would like to repeat your {test_name} in 3 months to monitor the trend. Please schedule a lab appointment closer to that date.\n\nContinue your current plan in the meantime.\n\nBest regards,\nYour Provider'),
    # --- Referral required ---
    ('Referral — Specialist', 'referral', 1,
     'Dear {patient_name},\n\nBased on your {test_name} results ({result_value}), we are referring you to a specialist for further evaluation. Our office will send the referral and the specialist\'s office will contact you to schedule.\n\nBest regards,\nYour Provider'),
    ('Referral — Additional Testing', 'referral', 2,
     'Dear {patient_name},\n\nYour {test_name} results indicate the need for additional diagnostic testing. We are ordering the appropriate studies and will contact you with scheduling details.\n\nBest regards,\nYour Provider'),
]


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check if table already exists
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='result_templates'"
    )
    if cur.fetchone():
        print('[result_templates] Table already exists — skipping creation.')
    else:
        cur.execute('''
            CREATE TABLE result_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                category VARCHAR(50) NOT NULL,
                body_template TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                display_order INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute(
            'CREATE INDEX IF NOT EXISTS ix_result_templates_category '
            'ON result_templates (category)'
        )
        print('[result_templates] Table created.')

        # Seed default templates
        for name, category, order, body in SEED_TEMPLATES:
            cur.execute(
                'INSERT INTO result_templates (name, category, body_template, is_active, display_order) '
                'VALUES (?, ?, ?, 1, ?)',
                (name, category, body, order),
            )
        print(f'[result_templates] Seeded {len(SEED_TEMPLATES)} default templates.')

    conn.commit()
    conn.close()
    print('Migration complete.')


if __name__ == '__main__':
    migrate()

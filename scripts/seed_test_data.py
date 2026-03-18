"""
NP Companion — Seed Test Data

Seeds the database with test patient data:
  - MRN 62815 (TEST, TEST) from the real XML clinical summary
  - MRN 10001 (JOHNSON, SARAH) — synthetic
  - MRN 10002 (MARTINEZ, CARLOS) — synthetic
  - MRN 10003 (PATEL, PRIYA) — synthetic

Usage:
    venv\\Scripts\\python.exe scripts/seed_test_data.py
Or import and call seed_all_test_data(user_id) from within the app context.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def seed_patient_from_xml(user_id):
    """Parse the reference XML and store MRN 62815 data in the DB."""
    from agent.clinical_summary_parser import parse_clinical_summary, store_parsed_summary
    from models.patient import PatientRecord

    xml_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'Documents', 'ac_interface_reference',
        'ClinicalSummary_PatientId_62815_20260316_130657.xml'
    )

    if not os.path.isfile(xml_path):
        print(f'  XML not found: {xml_path}')
        return False

    # Skip if already seeded
    existing = PatientRecord.query.filter_by(user_id=user_id, mrn='62815').first()
    if existing and existing.last_xml_parsed:
        print('  MRN 62815 already seeded — skipping')
        return True

    parsed = parse_clinical_summary(xml_path)
    if not parsed.get('patient_mrn'):
        print('  Failed to parse XML — no MRN found')
        return False

    store_parsed_summary(user_id, '62815', parsed)
    print(f'  Seeded MRN 62815 (TEST, TEST) — '
          f'{len(parsed.get("medications", []))} meds, '
          f'{len(parsed.get("diagnoses", []))} dx, '
          f'{len(parsed.get("allergies", []))} allergies, '
          f'{len(parsed.get("vitals", []))} vitals, '
          f'{len(parsed.get("immunizations", []))} immunizations')
    return True


def seed_synthetic_patients(user_id):
    """Create 3 synthetic test patients with realistic clinical data."""
    from agent.clinical_summary_parser import store_parsed_summary
    from models.patient import PatientRecord

    patients = [
        {
            'mrn': '10001',
            'patient_name': 'SARAH JOHNSON',
            'patient_dob': '19920315',
            'medications': [
                {'text': 'Metformin | 500mg | twice daily', 'raw_elements': 3},
                {'text': 'Lisinopril | 10mg | daily', 'raw_elements': 3},
                {'text': 'Atorvastatin | 20mg | at bedtime', 'raw_elements': 3},
            ],
            'diagnoses': [
                {'text': 'Type 2 Diabetes Mellitus | E11.9', 'raw_elements': 2},
                {'text': 'Essential Hypertension | I10', 'raw_elements': 2},
            ],
            'allergies': [
                {'text': 'Penicillin | Rash | Moderate', 'raw_elements': 3},
            ],
            'vitals': [
                {'text': 'Blood Pressure | 138/82 mmHg', 'raw_elements': 2},
                {'text': 'Heart Rate | 78 bpm', 'raw_elements': 2},
            ],
            'immunizations': [
                {'text': 'Influenza vaccine | 2025-10-15', 'raw_elements': 2},
            ],
            'lab_results': [],
            'social_history': [{'text': 'Non-smoker | Social drinker', 'raw_elements': 2}],
            'encounter_reason': [],
            'instructions': [],
            'goals': [],
            'health_concerns': [],
            'patient_demographics': [],
        },
        {
            'mrn': '10002',
            'patient_name': 'CARLOS MARTINEZ',
            'patient_dob': '19750722',
            'medications': [
                {'text': 'Amlodipine | 5mg | daily', 'raw_elements': 3},
                {'text': 'Omeprazole | 20mg | before breakfast', 'raw_elements': 3},
            ],
            'diagnoses': [
                {'text': 'Gastroesophageal Reflux Disease | K21.0', 'raw_elements': 2},
                {'text': 'Hyperlipidemia | E78.5', 'raw_elements': 2},
            ],
            'allergies': [],
            'vitals': [
                {'text': 'Blood Pressure | 142/88 mmHg', 'raw_elements': 2},
                {'text': 'Weight | 210 lbs', 'raw_elements': 2},
                {'text': 'BMI | 30.2', 'raw_elements': 2},
            ],
            'immunizations': [
                {'text': 'Tdap | 2024-03-10', 'raw_elements': 2},
            ],
            'lab_results': [],
            'social_history': [{'text': 'Former smoker (quit 2020) | No alcohol', 'raw_elements': 2}],
            'encounter_reason': [],
            'instructions': [],
            'goals': [],
            'health_concerns': [],
            'patient_demographics': [],
        },
        {
            'mrn': '10003',
            'patient_name': 'PRIYA PATEL',
            'patient_dob': '19881108',
            'medications': [
                {'text': 'Levothyroxine | 75mcg | daily on empty stomach', 'raw_elements': 3},
                {'text': 'Sertraline | 50mg | daily', 'raw_elements': 3},
                {'text': 'Vitamin D3 | 2000 IU | daily', 'raw_elements': 3},
            ],
            'diagnoses': [
                {'text': 'Hypothyroidism | E03.9', 'raw_elements': 2},
            ],
            'allergies': [
                {'text': 'Sulfa drugs | Hives | Severe', 'raw_elements': 3},
            ],
            'vitals': [
                {'text': 'Blood Pressure | 118/72 mmHg', 'raw_elements': 2},
                {'text': 'Heart Rate | 68 bpm', 'raw_elements': 2},
            ],
            'immunizations': [
                {'text': 'COVID-19 Vaccine | 2025-09-01', 'raw_elements': 2},
            ],
            'lab_results': [],
            'social_history': [],
            'encounter_reason': [],
            'instructions': [],
            'goals': [],
            'health_concerns': [],
            'patient_demographics': [],
        },
    ]

    for p in patients:
        mrn = p['mrn']
        existing = PatientRecord.query.filter_by(user_id=user_id, mrn=mrn).first()
        if existing and existing.last_xml_parsed:
            print(f'  MRN {mrn} already seeded — skipping')
            continue

        store_parsed_summary(user_id, mrn, p)
        print(f'  Seeded MRN {mrn} ({p["patient_name"]}) — '
              f'{len(p["medications"])} meds, '
              f'{len(p["diagnoses"])} dx, '
              f'{len(p["allergies"])} allergies')

    return True


def seed_all_test_data(user_id):
    """Seed MRN 62815 from XML + 3 synthetic patients."""
    print('Seeding test patient data...')
    seed_patient_from_xml(user_id)
    seed_synthetic_patients(user_id)
    print('Done.')
    return 'Seeded MRN 62815 (XML) + 3 synthetic patients (10001, 10002, 10003).'


def clear_test_data(user_id):
    """Remove all test patient data for the given user."""
    from models import db
    from models.patient import (
        PatientRecord, PatientVitals, PatientMedication,
        PatientDiagnosis, PatientAllergy, PatientImmunization,
        PatientNoteDraft,
    )

    test_mrns = ['62815', '10001', '10002', '10003']
    count = 0
    for model in [PatientVitals, PatientMedication, PatientDiagnosis,
                  PatientAllergy, PatientImmunization, PatientNoteDraft,
                  PatientRecord]:
        deleted = model.query.filter(
            model.user_id == user_id,
            model.mrn.in_(test_mrns)
        ).delete(synchronize_session=False)
        count += deleted

    db.session.commit()
    msg = f'Cleared {count} test data rows.'
    print(msg)
    return msg


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        from models.user import User
        user = User.query.filter_by(is_active_account=True).order_by(User.id).first()
        if not user:
            print('No active user found — create an account first.')
            sys.exit(1)
        print(f'Using user: {user.username} (id={user.id})')
        seed_all_test_data(user.id)

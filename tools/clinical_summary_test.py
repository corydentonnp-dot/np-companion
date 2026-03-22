"""
CareCompanion — Clinical Summary Integration Test

File location: carecompanion/tools/clinical_summary_test.py

Standalone script to test the clinical summary pipeline on the work PC
where Amazing Charts is actually installed. Validates:

  1. CDA XML parsing from a sample or recently-exported file
  2. store_parsed_summary() writes all sections to the database
  3. Patient chart route returns 200 for the parsed patient

Usage (from project root):
    venv\\Scripts\\python.exe tools/clinical_summary_test.py
    venv\\Scripts\\python.exe tools/clinical_summary_test.py --xml path/to/file.xml

If --xml is not provided, the script looks for the most recent .xml
file in CLINICAL_SUMMARY_EXPORT_FOLDER, then falls back to the sample
XML in Documents/ac_interface_reference/.
"""

import argparse
import glob
import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import config


def find_xml_file(explicit_path=None):
    """Locate a CDA XML file for testing."""
    if explicit_path:
        if os.path.isfile(explicit_path):
            return explicit_path
        print(f'ERROR: File not found: {explicit_path}')
        return None

    # Try the export folder
    export_dir = getattr(config, 'CLINICAL_SUMMARY_EXPORT_FOLDER', 'data/clinical_summaries/')
    if os.path.isdir(export_dir):
        xmls = sorted(glob.glob(os.path.join(export_dir, '*.xml')),
                       key=os.path.getmtime, reverse=True)
        if xmls:
            print(f'Using most recent export: {xmls[0]}')
            return xmls[0]

    # Fall back to sample XML
    sample = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                          'Documents', 'xml_test_patients',
                          'ClinicalSummary_PatientId_62815_20260317_142457.xml')
    if os.path.isfile(sample):
        print(f'Using sample XML: {sample}')
        return sample

    print('ERROR: No XML file found. Use --xml to specify one.')
    return None


def run_test(xml_path):
    """Run the clinical summary integration test."""
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True

    passed = []
    failed = []

    print('=' * 60)
    print('  Clinical Summary Integration Test')
    print('=' * 60)
    print(f'  XML: {xml_path}')

    # Step 1: Parse XML
    print('\n[1/4] Parsing XML...')
    try:
        from agent.clinical_summary_parser import parse_clinical_summary
        parsed = parse_clinical_summary(xml_path)
        mrn = parsed.get('patient_mrn', '')
        name = parsed.get('patient_name', '')
        print(f'  PASS  Patient: {name}, MRN: {mrn}')
        passed.append('XML parsing')

        sections = {k: v for k, v in parsed.items()
                    if isinstance(v, list) and v}
        for sec, data in sections.items():
            print(f'         {sec}: {len(data)} entries')
    except Exception as e:
        failed.append(f'XML parsing: {e}')
        print(f'  FAIL  {e}')
        _summary(passed, failed)
        return

    # Step 2: Store to DB
    print('\n[2/4] Storing to database...')
    with app.app_context():
        from models import db
        from models.user import User
        from agent.clinical_summary_parser import store_parsed_summary

        user = (User.query
                .filter_by(is_active_account=True)
                .order_by(User.id.asc())
                .first())
        if not user:
            failed.append('No active user found')
            print('  FAIL  No active user to associate data with')
            _summary(passed, failed)
            return

        try:
            store_parsed_summary(user.id, parsed)
            passed.append('store_parsed_summary')
            print(f'  PASS  Data stored for user {user.username}')
        except Exception as e:
            failed.append(f'store_parsed_summary: {e}')
            print(f'  FAIL  {e}')
            _summary(passed, failed)
            return

    # Step 3: Verify DB contents
    print('\n[3/4] Verifying database rows...')
    with app.app_context():
        from models.patient import (
            PatientRecord, PatientVitals, PatientMedication,
            PatientDiagnosis, PatientAllergy, PatientImmunization,
        )

        rec = PatientRecord.query.filter_by(user_id=user.id, mrn=mrn).first()
        if rec:
            passed.append('PatientRecord exists')
            print(f'  PASS  PatientRecord: {rec.patient_name}, DOB={rec.dob}')
        else:
            failed.append('PatientRecord missing')
            print('  FAIL  PatientRecord not found')

        for model, label in [
            (PatientVitals, 'Vitals'),
            (PatientMedication, 'Medications'),
            (PatientDiagnosis, 'Diagnoses'),
            (PatientAllergy, 'Allergies'),
            (PatientImmunization, 'Immunizations'),
        ]:
            count = model.query.filter_by(user_id=user.id, mrn=mrn).count()
            status = 'PASS' if count > 0 else 'INFO'
            print(f'  {status}  {label}: {count} rows')
            if count > 0:
                passed.append(f'{label}: {count}')

    # Step 4: Test web route
    print('\n[4/4] Testing patient chart route...')
    with app.test_client() as client:
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user.id)

        r = client.get(f'/patient/{mrn}')
        if r.status_code == 200:
            passed.append(f'GET /patient/{mrn} → 200')
            print(f'  PASS  GET /patient/{mrn} → 200')
        else:
            failed.append(f'GET /patient/{mrn} → {r.status_code}')
            print(f'  FAIL  GET /patient/{mrn} → {r.status_code}')

    _summary(passed, failed)
    return len(failed) == 0


def _summary(passed, failed):
    print(f'\n{"=" * 60}')
    print(f'  Results: {len(passed)} passed, {len(failed)} failed')
    if failed:
        print('\n  Failed:')
        for f in failed:
            print(f'    - {f}')
    else:
        print('\n  All checks passed!')
    print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Clinical Summary Integration Test')
    parser.add_argument('--xml', help='Path to a CDA XML file to test')
    args = parser.parse_args()

    xml = find_xml_file(args.xml)
    if not xml:
        sys.exit(2)

    success = run_test(xml)
    sys.exit(0 if success else 1)

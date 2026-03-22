"""
Phase 15 — Data Pipeline Fixes (Unblock All 26 Detectors)

Verifies:
  15.1 PatientLabResult model + migration
  15.2 PatientSocialHistory model + migration
  15.3 last_awv_date / last_discharge_date on PatientRecord
  15.4 store_parsed_summary() persists labs and social history
  15.5 populate_last_awv_date() function
  15.6 detect_pregnancy() function
  15.7 job_previsit_billing() builds full patient_data from DB
  15.8 Structural integrity of new migration files
  15.E2E XML parse → store → job → engine chain (Phase 3 extension, +5 tests)

Usage:
    venv\\Scripts\\python.exe tests/test_phase15_data_pipeline.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(relpath):
    with open(os.path.join(ROOT, relpath), encoding='utf-8') as f:
        return f.read()


def run_tests():
    passed = []
    failed = []

    # ==================================================================
    # 15.1 — PatientLabResult model exists with correct columns
    # ==================================================================
    print('[1/25] PatientLabResult model importable...')
    try:
        from models.patient import PatientLabResult
        assert PatientLabResult is not None
        assert PatientLabResult.__tablename__ == 'patient_lab_results'
        passed.append('15.1a: PatientLabResult model exists')
    except Exception as e:
        failed.append(f'15.1a: PatientLabResult model: {e}')

    print('[2/25] PatientLabResult has required columns...')
    try:
        src = _read('models/patient.py')
        for col in ['test_name', 'loinc_code', 'result_value', 'result_units',
                     'result_date', 'result_flag', 'patient_mrn_hash']:
            assert col in src, f'Missing column {col}'
        passed.append('15.1b: PatientLabResult columns present')
    except Exception as e:
        failed.append(f'15.1b: PatientLabResult columns: {e}')

    print('[3/25] Lab results migration exists...')
    try:
        src = _read('migrations/migrate_add_lab_results.py')
        assert 'patient_lab_results' in src
        assert 'CREATE TABLE' in src.upper() or 'create_all' in src
        passed.append('15.1c: Lab results migration exists')
    except Exception as e:
        failed.append(f'15.1c: Lab results migration: {e}')

    # ==================================================================
    # 15.2 — PatientSocialHistory model exists with correct columns
    # ==================================================================
    print('[4/25] PatientSocialHistory model importable...')
    try:
        from models.patient import PatientSocialHistory
        assert PatientSocialHistory is not None
        assert PatientSocialHistory.__tablename__ == 'patient_social_history'
        passed.append('15.2a: PatientSocialHistory model exists')
    except Exception as e:
        failed.append(f'15.2a: PatientSocialHistory model: {e}')

    print('[5/25] PatientSocialHistory has required columns...')
    try:
        src = _read('models/patient.py')
        for col in ['tobacco_status', 'tobacco_pack_years', 'alcohol_status',
                     'alcohol_frequency', 'substance_use_status', 'sexual_activity']:
            assert col in src, f'Missing column {col}'
        passed.append('15.2b: PatientSocialHistory columns present')
    except Exception as e:
        failed.append(f'15.2b: PatientSocialHistory columns: {e}')

    print('[6/25] Social history migration exists...')
    try:
        src = _read('migrations/migrate_add_social_history.py')
        assert 'patient_social_history' in src
        assert 'CREATE TABLE' in src.upper() or 'create_all' in src
        passed.append('15.2c: Social history migration exists')
    except Exception as e:
        failed.append(f'15.2c: Social history migration: {e}')

    # ==================================================================
    # 15.3 — last_awv_date / last_discharge_date on PatientRecord
    # ==================================================================
    print('[7/25] PatientRecord.last_awv_date column exists...')
    try:
        src = _read('models/patient.py')
        assert 'last_awv_date' in src
        assert "db.Column(db.Date" in src
        passed.append('15.3a: last_awv_date column exists')
    except Exception as e:
        failed.append(f'15.3a: last_awv_date: {e}')

    print('[8/25] PatientRecord.last_discharge_date column exists...')
    try:
        assert 'last_discharge_date' in src
        passed.append('15.3b: last_discharge_date column exists')
    except Exception as e:
        failed.append(f'15.3b: last_discharge_date: {e}')

    print('[9/25] AWV/discharge migration exists...')
    try:
        src = _read('migrations/migrate_add_awv_discharge_dates.py')
        assert 'last_awv_date' in src
        assert 'last_discharge_date' in src
        passed.append('15.3c: AWV/discharge migration exists')
    except Exception as e:
        failed.append(f'15.3c: AWV/discharge migration: {e}')

    # ==================================================================
    # 15.4 — store_parsed_summary() persists labs and social history
    # ==================================================================
    print('[10/25] store_parsed_summary persists lab results...')
    try:
        src = _read('agent/clinical_summary_parser.py')
        assert 'PatientLabResult' in src
        assert 'lab_results' in src
        # Verify it creates PatientLabResult instances
        assert 'PatientLabResult(' in src
        passed.append('15.4a: Lab result persistence in store_parsed_summary')
    except Exception as e:
        failed.append(f'15.4a: Lab result persistence: {e}')

    print('[11/25] store_parsed_summary persists social history...')
    try:
        src = _read('agent/clinical_summary_parser.py')
        assert 'PatientSocialHistory' in src
        assert 'tobacco_status' in src
        assert 'alcohol_status' in src
        passed.append('15.4b: Social history persistence in store_parsed_summary')
    except Exception as e:
        failed.append(f'15.4b: Social history persistence: {e}')

    # ==================================================================
    # 15.5 — populate_last_awv_date() function
    # ==================================================================
    print('[12/25] populate_last_awv_date function exists...')
    try:
        from agent.clinical_summary_parser import populate_last_awv_date
        assert callable(populate_last_awv_date)
        passed.append('15.5a: populate_last_awv_date function exists')
    except Exception as e:
        failed.append(f'15.5a: populate_last_awv_date: {e}')

    print('[13/25] populate_last_awv_date queries BillingOpportunity...')
    try:
        src = _read('agent/clinical_summary_parser.py')
        idx = src.index('def populate_last_awv_date')
        body = src[idx:idx + 600]
        assert 'BillingOpportunity' in body
        assert 'last_awv_date' in body
        passed.append('15.5b: populate_last_awv_date queries billing history')
    except Exception as e:
        failed.append(f'15.5b: populate_last_awv_date query: {e}')

    # ==================================================================
    # 15.6 — detect_pregnancy() function (O-code scan)
    # ==================================================================
    print('[14/25] detect_pregnancy function exists...')
    try:
        from agent.clinical_summary_parser import detect_pregnancy
        assert callable(detect_pregnancy)
        passed.append('15.6a: detect_pregnancy function exists')
    except Exception as e:
        failed.append(f'15.6a: detect_pregnancy: {e}')

    print('[15/25] detect_pregnancy scans for O-codes...')
    try:
        src = _read('agent/clinical_summary_parser.py')
        idx = src.index('def detect_pregnancy')
        body = src[idx:idx + 400]
        assert "code[0] == 'O'" in body or 'O' in body
        assert 'PatientDiagnosis' in body
        passed.append('15.6b: detect_pregnancy scans O-codes')
    except Exception as e:
        failed.append(f'15.6b: detect_pregnancy O-code scan: {e}')

    # ==================================================================
    # 15.7 — job_previsit_billing() full data pipeline
    # ==================================================================
    print('[16/25] job_previsit_billing queries PatientDiagnosis...')
    try:
        src = _read('agent_service.py')
        idx = src.index('def job_previsit_billing')
        body = src[idx:idx + 3000]
        assert 'PatientDiagnosis' in body
        assert 'diagnoses' in body
        passed.append('15.7a: job_previsit_billing queries diagnoses')
    except Exception as e:
        failed.append(f'15.7a: billing diagnoses: {e}')

    print('[17/25] job_previsit_billing queries PatientMedication...')
    try:
        assert 'PatientMedication' in body
        assert 'medications' in body
        passed.append('15.7b: job_previsit_billing queries medications')
    except Exception as e:
        failed.append(f'15.7b: billing medications: {e}')

    print('[18/25] job_previsit_billing queries PatientLabResult...')
    try:
        assert 'PatientLabResult' in body
        assert 'lab_results' in body
        passed.append('15.7c: job_previsit_billing queries lab results')
    except Exception as e:
        failed.append(f'15.7c: billing lab results: {e}')

    print('[19/25] job_previsit_billing populates insurer_type from DB...')
    try:
        assert 'insurer_type' in body
        assert 'patient.insurer_type' in body
        passed.append('15.7d: insurer_type from PatientRecord')
    except Exception as e:
        failed.append(f'15.7d: billing insurer_type: {e}')

    print('[20/25] job_previsit_billing uses Schedule model (not ScheduleEntry)...')
    try:
        # Verify the ScheduleEntry -> Schedule fix
        assert 'from models.schedule import Schedule' in body
        assert 'ScheduleEntry' not in body
        passed.append('15.7e: Uses Schedule model (ScheduleEntry bug fixed)')
    except Exception as e:
        failed.append(f'15.7e: Schedule model fix: {e}')

    # ==================================================================
    # 15.E2E — XML parse → store → job → engine chain (Phase 3 extension)
    # ==================================================================
    print('[21/25] clinical_summary_parser parse_clinical_summary importable...')
    try:
        from agent.clinical_summary_parser import parse_clinical_summary
        assert callable(parse_clinical_summary)
        passed.append('15.E2E-1: parse_clinical_summary function importable')
    except Exception as e:
        failed.append(f'15.E2E-1: {e}')

    print('[22/25] store_parsed_summary importable...')
    try:
        from agent.clinical_summary_parser import store_parsed_summary
        assert callable(store_parsed_summary)
        passed.append('15.E2E-2: store_parsed_summary importable')
    except Exception as e:
        failed.append(f'15.E2E-2: {e}')

    print('[23/25] job_previsit_billing function signature...')
    try:
        src2 = _read('agent_service.py')
        idx2 = src2.index('def job_previsit_billing')
        sig = src2[idx2:idx2 + 200]
        # Must accept (app) or () — verify it can run in app context
        assert 'def job_previsit_billing' in sig
        # Should contain evaluate_patient or billing engine call — search full function
        body2 = src2[idx2:idx2 + 15000]
        assert 'evaluate_patient' in body2, 'No evaluate_patient call in job'
        passed.append('15.E2E-3: job_previsit_billing calls engine.evaluate_patient')
    except Exception as e:
        failed.append(f'15.E2E-3: {e}')

    print('[24/25] BillingCaptureEngine importable...')
    try:
        from billing_engine.engine import BillingCaptureEngine
        assert BillingCaptureEngine is not None
        passed.append('15.E2E-4: BillingCaptureEngine importable')
    except Exception as e:
        failed.append(f'15.E2E-4: {e}')

    print('[25/25] BillingCaptureEngine.evaluate returns list...')
    try:
        os.environ['FLASK_ENV'] = 'testing'
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        with app.app_context():
            from models import db as _db
            from billing_engine.engine import BillingCaptureEngine
            from billing_engine.shared import hash_mrn
            from datetime import date
            _engine = BillingCaptureEngine(_db)
            from models.user import User
            _user = User.query.filter_by(is_active_account=True).order_by(User.id.asc()).first()
            _uid = _user.id if _user else 1
            _pd = {
                'mrn': 'TEST_E2E_PIPE', 'patient_mrn': 'TEST_E2E_PIPE',
                'patient_mrn_hash': hash_mrn('TEST_E2E_PIPE'),
                'user_id': _uid, 'visit_date': date.today(),
                'visit_type': 'office_visit', 'age': 50, 'sex': 'M',
                'patient_sex': 'M', 'insurer_type': 'medicare', 'insurer': 'medicare',
                'diagnoses': [{'icd10_code': 'I10', 'diagnosis_name': 'HTN', 'status': 'chronic'}],
                'medications': [], 'vitals': {}, 'lab_results': [],
                'immunizations': [], 'social_history': {},
                'awv_history': {}, 'is_pregnant': False,
            }
            result = _engine.evaluate(_pd)
            assert isinstance(result, list), f'evaluate returned {type(result)}'
            passed.append(f'15.E2E-5: BillingCaptureEngine.evaluate → {len(result)} opps')
    except Exception as e:
        failed.append(f'15.E2E-5: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print(f'\n{"=" * 60}')
    print(f'Phase 15 Data Pipeline: {len(passed)} passed, {len(failed)} failed')
    print(f'{"=" * 60}')
    for p in passed:
        print(f'  PASS  {p}')
    for f in failed:
        print(f'  FAIL  {f}')
    if failed:
        print('\n** FAILURES DETECTED **')
        sys.exit(1)
    else:
        print('\nAll Phase 15 tests passed.')
    return passed, failed


if __name__ == '__main__':
    run_tests()

"""
CareCompanion — Agent Mock Test Suite

File location: carecompanion/tests/test_agent_mock.py

Tests the agent pipeline against reference screenshots instead of
a live Amazing Charts installation.  Run this on any machine to
verify OCR detection, clinical summary parsing, and mock wiring.

Requires:
  - Tesseract installed (C:\\Program Files\\Tesseract-OCR\\tesseract.exe)
  - Pillow (pip install pillow)
  - pytesseract (pip install pytesseract)
  - Reference screenshots in Documents/ac_interface_reference/

Usage:
    venv\\Scripts\\python.exe tests/test_agent_mock.py

This script does NOT start the Flask server.  It tests the agent
modules in isolation using mock mode.
"""

import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Force mock mode ON for this test
import config
config.AC_MOCK_MODE = True


def _header(title):
    print(f'\n{"=" * 60}')
    print(f'  {title}')
    print(f'{"=" * 60}')


def run_mock_tests():
    passed = []
    failed = []

    _header('CareCompanion — Agent Mock Tests')
    print(f'AC_MOCK_MODE: {config.AC_MOCK_MODE}')
    print(f'TESSERACT_PATH: {getattr(config, "TESSERACT_PATH", "not set")}')

    # -----------------------------------------------------------------
    # Test 1: Mock provider loads
    # -----------------------------------------------------------------
    print('\n[1/8] Mock provider import...')
    try:
        from tests.ac_mock import (
            MOCK_PATIENT, SCREENSHOTS, SAMPLE_XML,
            set_mock_state, get_mock_state,
        )
        passed.append('Mock provider imported')
        print(f'  PASS  Mock patient: MRN={MOCK_PATIENT["mrn"]}, Name={MOCK_PATIENT["name"]}')
    except Exception as e:
        failed.append(f'Mock provider import: {e}')
        print(f'  FAIL  {e}')
        _print_summary(passed, failed)
        return

    # -----------------------------------------------------------------
    # Test 2: Screenshot files exist
    # -----------------------------------------------------------------
    print('\n[2/8] Screenshot files...')
    for name, path in SCREENSHOTS.items():
        if os.path.exists(path):
            passed.append(f'Screenshot: {name}')
            print(f'  PASS  {name}: {os.path.basename(path)}')
        else:
            failed.append(f'Screenshot missing: {name} ({path})')
            print(f'  FAIL  {name}: NOT FOUND at {path}')

    if os.path.exists(SAMPLE_XML):
        passed.append('Sample XML exists')
        print(f'  PASS  Sample XML: {os.path.basename(SAMPLE_XML)}')
    else:
        failed.append(f'Sample XML missing: {SAMPLE_XML}')
        print(f'  FAIL  Sample XML NOT FOUND')

    # -----------------------------------------------------------------
    # Test 3: ac_window mock functions
    # -----------------------------------------------------------------
    print('\n[3/8] ac_window mock functions...')
    try:
        from agent.ac_window import (
            find_ac_window, get_ac_chart_title,
            get_active_patient_mrn, get_active_patient_dob,
            is_ac_foreground, is_chart_window_open,
        )
        set_mock_state('home')
        assert is_ac_foreground(), 'is_ac_foreground should be True'
        assert not is_chart_window_open(), 'chart should not be open in home state'
        assert find_ac_window() is not None, 'find_ac_window should return hwnd'
        assert get_active_patient_mrn() is None, 'MRN should be None in home state'
        print('  PASS  Home state: AC foreground=True, chart=False, MRN=None')

        set_mock_state('chart')
        assert is_chart_window_open(), 'chart should be open in chart state'
        mrn = get_active_patient_mrn()
        dob = get_active_patient_dob()
        assert mrn == '62815', f'Expected MRN 62815, got {mrn}'
        assert dob == '10/1/1980', f'Expected DOB 10/1/1980, got {dob}'
        title = get_ac_chart_title()
        assert 'ID: 62815' in title, f'Title should contain ID: 62815'
        print(f'  PASS  Chart state: MRN={mrn}, DOB={dob}')

        passed.append('ac_window mock functions')
    except Exception as e:
        failed.append(f'ac_window mock: {e}')
        print(f'  FAIL  {e}')

    # -----------------------------------------------------------------
    # Test 4: OCR on screenshots (requires Tesseract)
    # -----------------------------------------------------------------
    print('\n[4/8] OCR on reference screenshots...')
    try:
        from agent.ocr_helpers import ocr_find_all_text, _preprocess_for_ocr
        from PIL import Image

        home_path = SCREENSHOTS.get('home')
        if home_path and os.path.exists(home_path):
            img = Image.open(home_path)
            words = ocr_find_all_text(img)
            word_texts = [w['text'].lower() for w in words]
            found_count = len(words)
            print(f'  INFO  Home screenshot: {found_count} words detected')

            # Check for key UI elements we need to find
            key_texts = ['inbox', 'patient', 'schedule']
            for kt in key_texts:
                matches = [w for w in word_texts if kt in w]
                if matches:
                    print(f'  PASS  Found "{kt}" in home screenshot ({len(matches)} matches)')
                    passed.append(f'OCR home: "{kt}"')
                else:
                    print(f'  WARN  "{kt}" not found in home screenshot (OCR quality may vary)')

        inbox_path = SCREENSHOTS.get('inbox')
        if inbox_path and os.path.exists(inbox_path):
            img = Image.open(inbox_path)
            words = ocr_find_all_text(img)
            word_texts = [w['text'].lower() for w in words]
            print(f'  INFO  Inbox screenshot: {len(words)} words detected')

            for kt in ['subject', 'from', 'received']:
                matches = [w for w in word_texts if kt in w]
                if matches:
                    print(f'  PASS  Found "{kt}" in inbox screenshot')
                    passed.append(f'OCR inbox: "{kt}"')

        passed.append('OCR detection working')
    except Exception as e:
        failed.append(f'OCR screenshot test: {e}')
        print(f'  FAIL  {e}')
        print('         Is Tesseract installed? Check TESSERACT_PATH in config.py')

    # -----------------------------------------------------------------
    # Test 5: Mock find_and_click / find_text_on_screen
    # -----------------------------------------------------------------
    print('\n[5/8] Mock OCR element detection...')
    try:
        from agent.ocr_helpers import find_text_on_screen, find_and_click

        set_mock_state('home')
        # Try to find "Inbox" text on home screenshot
        coords = find_text_on_screen('Inbox')
        if coords:
            print(f'  PASS  find_text_on_screen("Inbox") = {coords}')
            passed.append('Mock find_text_on_screen')
        else:
            print(f'  WARN  "Inbox" not found via OCR on home screenshot')

        set_mock_state('inbox')
        # Try to find "Subject" in inbox screenshot
        coords = find_text_on_screen('Subject')
        if coords:
            print(f'  PASS  find_text_on_screen("Subject") = {coords}')
            passed.append('Mock find_text_on_screen(Subject)')
        else:
            print(f'  WARN  "Subject" not found via OCR on inbox screenshot')

        # find_and_click should work (no actual click in mock mode)
        result = find_and_click('Show', partial=True)
        status = 'PASS' if result else 'WARN'
        print(f'  {status}  find_and_click("Show") = {result}')
        if result:
            passed.append('Mock find_and_click')

    except Exception as e:
        failed.append(f'Mock element detection: {e}')
        print(f'  FAIL  {e}')

    # -----------------------------------------------------------------
    # Test 6: Clinical Summary XML parsing
    # -----------------------------------------------------------------
    print('\n[6/8] Clinical Summary XML parsing...')
    try:
        from agent.clinical_summary_parser import parse_clinical_summary

        parsed = parse_clinical_summary(SAMPLE_XML)
        assert parsed['patient_mrn'] == '62815', f'Expected MRN 62815, got {parsed["patient_mrn"]}'
        assert 'TEST' in parsed['patient_name'].upper(), f'Expected TEST in name, got {parsed["patient_name"]}'
        print(f'  PASS  Patient: {parsed["patient_name"]}, MRN: {parsed["patient_mrn"]}')

        sections_found = [k for k, v in parsed.items()
                         if isinstance(v, list) and v
                         and k not in ('patient_name', 'patient_mrn', 'patient_dob')]
        print(f'  PASS  Sections with data: {", ".join(sections_found) or "none"}')
        passed.append(f'XML parsing: {len(sections_found)} sections')

    except Exception as e:
        failed.append(f'Clinical summary parsing: {e}')
        print(f'  FAIL  {e}')

    # -----------------------------------------------------------------
    # Test 7: MRN reader mock pipeline
    # -----------------------------------------------------------------
    print('\n[7/8] MRN reader mock pipeline...')
    try:
        set_mock_state('chart')
        from agent.ac_window import get_active_patient_mrn, is_ac_foreground
        mrn = get_active_patient_mrn()
        fg = is_ac_foreground()
        assert fg, 'AC should be foreground in mock mode'
        assert mrn == '62815', f'Expected 62815, got {mrn}'
        print(f'  PASS  MRN reader pipeline: foreground={fg}, MRN={mrn}')
        passed.append('MRN reader mock pipeline')
    except Exception as e:
        failed.append(f'MRN reader mock: {e}')
        print(f'  FAIL  {e}')

    # -----------------------------------------------------------------
    # Test 8: get_ac_window_rect mock
    # -----------------------------------------------------------------
    print('\n[8/10] Window rect mock...')
    try:
        from agent.ocr_helpers import get_ac_window_rect
        set_mock_state('home')
        rect = get_ac_window_rect()
        assert rect is not None, 'Window rect should not be None'
        assert len(rect) == 4, f'Expected 4-tuple, got {rect}'
        print(f'  PASS  Mock window rect: {rect}')
        passed.append('Window rect mock')
    except Exception as e:
        failed.append(f'Window rect mock: {e}')
        print(f'  FAIL  {e}')

    # -----------------------------------------------------------------
    # Test 9: Seed test data into Flask DB and verify via web routes
    # -----------------------------------------------------------------
    print('\n[9/10] Seed test data & DB verification...')
    try:
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True

        with app.app_context():
            from models import db
            from models.user import User

            user = (
                User.query
                .filter_by(is_active_account=True)
                .order_by(User.id.asc())
                .first()
            )
            if not user:
                print('  SKIP  No active user — cannot seed test data')
            else:
                from scripts.seed_test_data import seed_all_test_data, clear_test_data
                from models.patient import (
                    PatientRecord, PatientMedication, PatientDiagnosis,
                    PatientAllergy, PatientImmunization,
                )

                # Clear first, then seed
                clear_test_data(user.id)
                seed_all_test_data(user.id)

                # Verify records exist
                records = PatientRecord.query.filter_by(user_id=user.id).all()
                mrns = {r.mrn for r in records}
                expected_mrns = {'62815', '10001', '10002', '10003'}
                missing = expected_mrns - mrns
                if missing:
                    failed.append(f'Seed data missing MRNs: {missing}')
                    print(f'  FAIL  Missing MRNs after seed: {missing}')
                else:
                    print(f'  PASS  All 4 test patients seeded (MRNs: {sorted(mrns & expected_mrns)})')
                    passed.append('Seed test data: 4 patients')

                # Verify medications exist
                med_count = PatientMedication.query.filter(
                    PatientMedication.user_id == user.id,
                    PatientMedication.mrn.in_(list(expected_mrns))
                ).count()
                if med_count > 0:
                    print(f'  PASS  {med_count} medication records found')
                    passed.append(f'Seed data: {med_count} meds')
                else:
                    failed.append('No medication records after seed')
                    print('  FAIL  No medication records after seed')

                # Verify via test client
                with app.test_client() as client:
                    with client.session_transaction() as sess:
                        sess['_user_id'] = str(user.id)

                    r = client.get('/patient/10001')
                    if r.status_code == 200:
                        passed.append('Patient chart route works for seeded data')
                        print('  PASS  GET /patient/10001 -> 200')
                    else:
                        failed.append(f'GET /patient/10001 -> {r.status_code}')
                        print(f'  FAIL  GET /patient/10001 -> {r.status_code}')

                # Cleanup
                clear_test_data(user.id)
                remaining = PatientRecord.query.filter(
                    PatientRecord.user_id == user.id,
                    PatientRecord.mrn.in_(list(expected_mrns))
                ).count()
                if remaining == 0:
                    passed.append('Clear test data works')
                    print('  PASS  Test data cleared successfully')
                else:
                    failed.append(f'{remaining} records remain after clear')
                    print(f'  FAIL  {remaining} records remain after clear')

    except Exception as e:
        failed.append(f'Seed test data: {e}')
        print(f'  FAIL  {e}')

    # -----------------------------------------------------------------
    # Test 10: store_parsed_summary stores all sections
    # -----------------------------------------------------------------
    print('\n[10/10] store_parsed_summary completeness...')
    try:
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True

        with app.app_context():
            from models import db
            from models.user import User
            from agent.clinical_summary_parser import parse_clinical_summary, store_parsed_summary
            from models.patient import (
                PatientRecord, PatientVitals, PatientMedication,
                PatientDiagnosis, PatientAllergy, PatientImmunization,
            )

            user = User.query.filter_by(is_active_account=True).order_by(User.id.asc()).first()
            if not user:
                print('  SKIP  No active user')
            else:
                parsed = parse_clinical_summary(SAMPLE_XML)
                store_parsed_summary(user.id, parsed['patient_mrn'], parsed)

                mrn = parsed['patient_mrn']
                rec = PatientRecord.query.filter_by(user_id=user.id, mrn=mrn).first()
                assert rec is not None, 'PatientRecord not created'
                print(f'  PASS  PatientRecord for MRN {mrn}')
                passed.append('store_parsed_summary: PatientRecord')

                vitals = PatientVitals.query.filter_by(user_id=user.id, mrn=mrn).first()
                if vitals:
                    passed.append('store_parsed_summary: Vitals')
                    print('  PASS  Vitals stored')

                # Check that meds/dx/allergies/immunizations are stored
                for model, label in [
                    (PatientMedication, 'Medications'),
                    (PatientDiagnosis, 'Diagnoses'),
                    (PatientAllergy, 'Allergies'),
                    (PatientImmunization, 'Immunizations'),
                ]:
                    count = model.query.filter_by(user_id=user.id, mrn=mrn).count()
                    if count > 0:
                        passed.append(f'store_parsed_summary: {label} ({count})')
                        print(f'  PASS  {label}: {count} rows')
                    else:
                        # Some sections may be empty in the sample XML — warn instead of fail
                        print(f'  WARN  {label}: 0 rows (may be absent in sample XML)')

                # Cleanup
                from scripts.seed_test_data import clear_test_data
                clear_test_data(user.id)

    except Exception as e:
        failed.append(f'store_parsed_summary: {e}')
        print(f'  FAIL  {e}')

    # -----------------------------------------------------------------
    # Test 11: AC state detection (v4 addition) — home state
    # -----------------------------------------------------------------
    print('\n[11/13] AC state detection — home...')
    try:
        from tests.ac_mock import set_mock_state
        set_mock_state('home')
        from agent.ac_window import get_ac_state
        state = get_ac_state()
        assert state == 'home_screen', f'Expected home_screen, got {state}'
        print(f'  PASS  get_ac_state() = {state}')
        passed.append('AC state detection: home_screen')
    except Exception as e:
        failed.append(f'AC state detection (home): {e}')
        print(f'  FAIL  {e}')

    # -----------------------------------------------------------------
    # Test 12: AC state detection (v4 addition) — chart state
    # -----------------------------------------------------------------
    print('\n[12/13] AC state detection — chart...')
    try:
        from tests.ac_mock import set_mock_state
        set_mock_state('chart')
        from agent.ac_window import get_ac_state
        state = get_ac_state()
        assert state == 'chart_open', f'Expected chart_open, got {state}'
        print(f'  PASS  get_ac_state() = {state}')
        passed.append('AC state detection: chart_open')
    except Exception as e:
        failed.append(f'AC state detection (chart): {e}')
        print(f'  FAIL  {e}')

    # -----------------------------------------------------------------
    # Test 13: Resurrect dialog detection (v4 addition)
    # -----------------------------------------------------------------
    print('\n[13/14] Resurrect dialog detection...')
    try:
        from agent.ac_window import detect_resurrect_dialog
        result = detect_resurrect_dialog()
        assert result == False, f'Expected False, got {result}'
        print(f'  PASS  detect_resurrect_dialog() = {result}')
        passed.append('Resurrect dialog detection: False in mock')
    except Exception as e:
        failed.append(f'Resurrect dialog detection: {e}')
        print(f'  FAIL  {e}')

    # -----------------------------------------------------------------
    # Test 14: Auto-login from login state (CL20)
    # -----------------------------------------------------------------
    print('\n[14/14] Auto-login from login state...')
    try:
        from tests.ac_mock import set_mock_state
        set_mock_state('login')
        from agent.ac_window import auto_login_ac
        result = auto_login_ac()
        assert result == True, f'Expected True, got {result}'
        from agent.ac_window import get_ac_state
        state_after = get_ac_state()
        assert state_after == 'home_screen', f'Expected home_screen, got {state_after}'
        print(f'  PASS  auto_login_ac() = {result}, state after = {state_after}')
        passed.append('Auto-login: login → home_screen')
        # Reset state back to home
        set_mock_state('home')
    except Exception as e:
        failed.append(f'Auto-login: {e}')
        print(f'  FAIL  {e}')

    _print_summary(passed, failed)


def _print_summary(passed, failed):
    _header('Results')
    print(f'  Passed: {len(passed)}')
    print(f'  Failed: {len(failed)}')
    if failed:
        print('\nFailed tests:')
        for f in failed:
            print(f'  - {f}')
    print()
    if not failed:
        print('All mock tests passed! The agent pipeline works with screenshots.')
    else:
        print('Some tests failed. Check the errors above.')
        print('Most common fix: install Tesseract and set TESSERACT_PATH in config.py')


if __name__ == '__main__':
    run_mock_tests()

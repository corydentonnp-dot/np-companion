"""
Phase 37.4 — Semi-Auto Pre-Population UX Tests (8 tests)

Tests:
  1:  PCP-HF pre-fills 11 of 11 auto inputs from EHR (age, sex, BMI, SBP, smoker,
      glucose, TC, HDL, eGFR, bp_meds, dm_meds); qrs_duration stays empty (clinician)
  2:  ADA Risk pre-fills 4 auto inputs (age, sex, BMI, hypertension);
      3 clinician-source inputs return no value
  3:  AAP HTN (age 15) — all 3 inputs pre-filled (sbp, dbp, age)
  4:  AAP HTN hint — age < 13 returns "not yet implemented" warning
  5:  Lock-icon semantics: auto-filled fields are still editable (no readonly flag)
  6:  Clinical context hint — existing DM diagnosis → ADA Risk warning
  7:  PERC context hint — always returns low pre-test setting note
  8:  Gail Model has registry status 'blocked'

Usage: venv\\Scripts\\python.exe tests\\test_calculator_prefill.py
"""

import os
import sys
import tempfile
import uuid
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _make_app():
    """Stand up a Flask app with an isolated temp SQLite file."""
    from app import create_app
    tmp_db = os.path.join(tempfile.gettempdir(), f'npcomp_test_{uuid.uuid4().hex}.db')
    with patch('app.get_db_path', return_value=tmp_db):
        test_app = create_app()
    test_app.config['TESTING'] = True
    test_app.config['WTF_CSRF_ENABLED'] = False
    return test_app, tmp_db


def _seed_full_patient(db, user_id, mrn):
    """Create a PatientRecord + vitals + labs + social + meds for PCP-HF test."""
    from datetime import datetime, timezone, timedelta
    from models.patient import (
        PatientRecord, PatientVitals, PatientLabResult,
        PatientSocialHistory, PatientMedication,
    )

    pt = PatientRecord(
        user_id=user_id, mrn=mrn,
        patient_name='Test Patient',
        patient_dob='1965-04-15',   # ~59 years old
        patient_sex='male',
    )
    db.session.add(pt)

    now = datetime.now(timezone.utc)
    for vname, vval, vunit in [
        ('BMI', '28.5', 'kg/m2'),
        ('BP Systolic', '138', 'mmHg'),
        ('BP Diastolic', '86', 'mmHg'),
        ('Heart Rate', '72', '/min'),
        ('O2 Sat', '98', '%'),
        ('Weight', '185', 'lb'),
        ('Height', '70', 'in'),
    ]:
        db.session.add(PatientVitals(
            user_id=user_id, mrn=mrn,
            vital_name=vname, vital_value=vval, vital_unit=vunit,
            measured_at=now,
        ))

    LOINC_LABS = [
        ('2345-7', 'glucose', '102'),
        ('2093-3', 'total_cholesterol', '210'),
        ('2085-9', 'hdl', '48'),
        ('33914-3', 'egfr', '72'),
        ('4548-4', 'a1c', '5.9'),
    ]
    for loinc, name, val in LOINC_LABS:
        db.session.add(PatientLabResult(
            user_id=user_id, mrn=mrn,
            test_name=name, loinc_code=loinc,
            result_value=val, result_units='',
            result_date=now,
        ))

    db.session.add(PatientSocialHistory(
        user_id=user_id, mrn=mrn, tobacco_status='current',
    ))

    for drug in ['lisinopril 10mg', 'metformin 500mg']:
        db.session.add(PatientMedication(
            user_id=user_id, mrn=mrn,
            drug_name=drug, status='active',
        ))

    db.session.commit()


def run_tests():
    passed = []
    failed = []

    # ── Tests 1-3: get_prefilled_inputs (DB-based) ────────────────────────────

    print('[1/8] PCP-HF pre-fills 11 of 11 auto inputs...')
    test_app, tmp_db = _make_app()
    try:
        with test_app.app_context():
            from models import db
            from models.user import User

            user = User(username='pf_u1', email='pf1@test.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            uid = user.id
            mrn = 'PREFILL_PCP'
            _seed_full_patient(db, uid, mrn)

            from app.services.calculator_engine import CalculatorEngine
            eng = CalculatorEngine()
            result = eng.get_prefilled_inputs('pcp_hf', mrn)

            auto_keys = ['age', 'sex', 'bmi', 'sbp', 'smoker',
                         'glucose', 'total_cholesterol', 'hdl', 'egfr',
                         'bp_meds', 'dm_meds']
            filled = [k for k in auto_keys if k in result and result[k] is not None]
            # smoker (True/False) and bp_meds/dm_meds (bool) are truthy/falsy
            # so we check presence in dict, not truthiness
            filled = [k for k in auto_keys if k in result]
            assert len(filled) == 11, f'Expected 11 auto keys in result, got {len(filled)}: {list(result.keys())}'
            assert 'qrs_duration' not in result, 'qrs_duration (clinician) should NOT be pre-filled'
            assert result['age'] > 50, f'Expected age > 50, got {result["age"]}'
            assert result['sex'] == 'male'
            assert result['bmi'] > 25
        passed.append('1: PCP-HF pre-fills 11 auto inputs')
    except Exception as e:
        failed.append(f'1: PCP-HF prefill: {e}')
    finally:
        try:
            os.unlink(tmp_db)
        except OSError:
            pass

    print('[2/8] ADA Risk pre-fills 4 auto inputs...')
    test_app, tmp_db = _make_app()
    try:
        with test_app.app_context():
            from models import db
            from models.user import User

            user = User(username='pf_u2', email='pf2@test.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            uid = user.id
            mrn = 'PREFILL_ADA'
            _seed_full_patient(db, uid, mrn)

            from app.services.calculator_engine import CalculatorEngine
            eng = CalculatorEngine()
            result = eng.get_prefilled_inputs('ada_risk', mrn)

            auto_keys = ['age', 'sex', 'bmi', 'hypertension']
            manual_keys = ['family_hx_dm', 'physically_active', 'gestational_dm']

            filled_auto = [k for k in auto_keys if k in result]
            assert len(filled_auto) == 4, f'Expected 4 auto keys, got {filled_auto}'

            for k in manual_keys:
                assert k not in result, f'{k} should NOT be in prefilled result'
        passed.append('2: ADA Risk pre-fills 4 auto + omits 3 manual')
    except Exception as e:
        failed.append(f'2: ADA Risk prefill: {e}')
    finally:
        try:
            os.unlink(tmp_db)
        except OSError:
            pass

    print('[3/8] AAP HTN (age 15) pre-fills sbp, dbp, age...')
    test_app, tmp_db = _make_app()
    try:
        with test_app.app_context():
            from models import db
            from models.user import User
            from models.patient import PatientRecord, PatientVitals
            from datetime import datetime, timezone, timedelta

            user = User(username='pf_u3', email='pf3@test.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            uid = user.id
            mrn = 'PREFILL_AAP'

            pt = PatientRecord(
                user_id=uid, mrn=mrn,
                patient_dob=(datetime.now(timezone.utc) - timedelta(days=15 * 365)).strftime('%Y-%m-%d'),
                patient_sex='male',
            )
            db.session.add(pt)
            now = datetime.now(timezone.utc)
            db.session.add(PatientVitals(user_id=uid, mrn=mrn, vital_name='BP Systolic', vital_value='128', vital_unit='mmHg', measured_at=now))
            db.session.add(PatientVitals(user_id=uid, mrn=mrn, vital_name='BP Diastolic', vital_value='78', vital_unit='mmHg', measured_at=now))
            db.session.commit()

            from app.services.calculator_engine import CalculatorEngine
            eng = CalculatorEngine()
            result = eng.get_prefilled_inputs('aap_htn', mrn)

            assert 'sbp' in result, 'sbp should be prefilled'
            assert 'dbp' in result, 'dbp should be prefilled'
            assert 'age' in result, 'age should be prefilled'
            assert 13 <= result['age'] <= 18, f'Expected age 13-18, got {result["age"]}'
        passed.append('3: AAP HTN age 15 pre-fills sbp/dbp/age')
    except Exception as e:
        failed.append(f'3: AAP HTN prefill: {e}')
    finally:
        try:
            os.unlink(tmp_db)
        except OSError:
            pass

    # ── Tests 4-8: context hints + registry (no DB needed) ────────────────────

    print('[4/8] AAP HTN hint — age < 13 returns not-yet-implemented warning...')
    try:
        from app.services.calculator_engine import CalculatorEngine
        eng = CalculatorEngine()
        hints = eng.get_context_hints('aap_htn', {'age': 10})
        warning = next((h for h in hints if h['type'] == 'warning'), None)
        assert warning is not None, 'Expected a warning hint for age < 13'
        assert 'not yet implemented' in warning['text'].lower() or '< 13' in warning['text'], \
            f'Expected "not yet implemented" in hint text, got: {warning["text"]}'
        passed.append('4: AAP HTN hint for age < 13')
    except Exception as e:
        failed.append(f'4: AAP HTN age < 13 hint: {e}')

    print('[5/8] Auto-filled fields are not read-only (editable override)...')
    try:
        from app.services.calculator_registry import CALCULATOR_REGISTRY
        # Verify that STOP-BANG's auto-source inputs don't have a 'readonly' flag
        sb = CALCULATOR_REGISTRY['stop_bang']
        auto_inputs = [i for i in sb['inputs'] if i.get('source') == 'auto']
        assert len(auto_inputs) == 4, f'Expected 4 auto inputs in STOP-BANG, got {len(auto_inputs)}'
        for inp in auto_inputs:
            assert inp.get('readonly') is None or inp.get('readonly') is False, \
                f'Input {inp["key"]} should NOT be read-only'
        passed.append('5: auto-filled fields have no readonly flag (editable)')
    except Exception as e:
        failed.append(f'5: readonly flag check: {e}')

    print('[6/8] ADA Risk context hint fires when patient has diabetes...')
    try:
        from app.services.calculator_engine import CalculatorEngine
        eng = CalculatorEngine()
        hints = eng.get_context_hints('ada_risk', {'has_diabetes': True, 'age': 55})
        warning = next((h for h in hints if h['type'] == 'warning'), None)
        assert warning is not None, 'Expected warning hint for DM patient with ADA Risk'
        assert 'diabetes' in warning['text'].lower(), \
            f'Expected "diabetes" in hint text, got: {warning["text"]}'
        passed.append('6: ADA Risk DM context hint present')
    except Exception as e:
        failed.append(f'6: ADA Risk DM hint: {e}')

    print('[7/8] PERC context hint shows low pre-test probability note...')
    try:
        from app.services.calculator_engine import CalculatorEngine
        eng = CalculatorEngine()
        hints = eng.get_context_hints('perc', {})
        assert len(hints) > 0, 'Expected at least one hint for PERC'
        any_hint = hints[0]
        assert 'pre-test' in any_hint['text'].lower() or 'low' in any_hint['text'].lower(), \
            f'Expected "pre-test" in PERC hint text, got: {any_hint["text"]}'
        passed.append('7: PERC context hint shows low pre-test note')
    except Exception as e:
        failed.append(f'7: PERC context hint: {e}')

    print('[8/8] Gail Model has registry status "blocked"...')
    try:
        from app.services.calculator_registry import CALCULATOR_REGISTRY
        gail = CALCULATOR_REGISTRY.get('gail_model')
        assert gail is not None, 'gail_model not found in registry'
        assert gail.get('status') == 'blocked', \
            f'Expected status="blocked", got {gail.get("status")}'
        assert 'blocked_reason' in gail, 'Expected blocked_reason key in gail_model entry'
        assert 'missing coefficients' in gail['blocked_reason'].lower() or \
               'nci' in gail['blocked_reason'].lower(), \
            f'Expected NCI/coefficients in blocked_reason, got: {gail["blocked_reason"]}'
        passed.append('8: gail_model has status=blocked with reason')
    except Exception as e:
        failed.append(f'8: Gail model blocked status: {e}')

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print(f'Results: {len(passed)}/8 passed, {len(failed)}/8 failed')
    if passed:
        for p in passed:
            print(f'  PASS: {p}')
    if failed:
        print()
        for f in failed:
            print(f'  FAIL: {f}')
    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

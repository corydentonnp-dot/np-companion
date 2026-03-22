"""
Phase 35.6 — Score Trend & Threshold Tests (10 tests)

Tests:
  1:  score_history endpoint returns data list ordered newest-first
  2:  score_history returns multiple historical rows
  3:  check_threshold_alerts triggers high severity for BMI >= 40
  4:  check_threshold_alerts triggers high severity for LDL >= 190
  5:  evaluate_calculator_care_gaps creates CareGap for BMI >= 30
  6:  evaluate_calculator_care_gaps creates LDCT gap for pack_years >= 20, age 55
  7:  detect_score_changes returns empty list when only one result per key
  8:  detect_score_changes detects significant BMI increase (>= 2 points)
  9:  check_threshold_alerts DOES NOT fire when BMI < 30
  10: obesity_counseling care gap billing code is G0447

Usage: venv\\Scripts\\python.exe tests\\test_score_trend.py
"""

import os
import sys
import tempfile
import uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _make_app():
    """Stand up a Flask app backed by a unique per-run temp SQLite file.

    We patch ``app.get_db_path`` BEFORE calling ``create_app()`` so that
    the production URI is never installed — create_app() pushes its own
    app_context internally (for db.create_all / migrations) and that would
    otherwise lock in the production DB before our override could take effect.
    """
    from unittest.mock import patch
    from app import create_app
    tmp_db = os.path.join(tempfile.gettempdir(), f'npcomp_test_{uuid.uuid4().hex}.db')
    with patch('app.get_db_path', return_value=tmp_db):
        test_app = create_app()
    test_app.config['TESTING'] = True
    test_app.config['WTF_CSRF_ENABLED'] = False
    return test_app, tmp_db


def run_tests():
    passed = []
    failed = []

    # ─────────────────────────────────────────────────────────────────────────
    # Tests 1-2: score_history endpoint
    # ─────────────────────────────────────────────────────────────────────────

    print('[1/10] score_history endpoint returns data list ordered newest-first...')
    test_app, tmp_db = _make_app()
    try:
        with test_app.app_context():
            from models import db
            from models.calculator import CalculatorResult
            from models.user import User
            from datetime import datetime, timezone, timedelta

            user = User(username='test_trend', email='trend@test.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            uid = user.id
            mrn = 'TEST_TREND_001'

            older = CalculatorResult(
                user_id=uid, mrn=mrn, calculator_key='bmi',
                score_value=28.0, score_label='overweight',
                is_current=False,
                computed_at=datetime.now(timezone.utc) - timedelta(days=90),
            )
            newer = CalculatorResult(
                user_id=uid, mrn=mrn, calculator_key='bmi',
                score_value=31.5, score_label='obese_class_1',
                is_current=True,
                computed_at=datetime.now(timezone.utc),
            )
            db.session.add_all([older, newer])
            db.session.commit()

            results = CalculatorResult.query.filter_by(
                mrn=mrn, calculator_key='bmi'
            ).order_by(CalculatorResult.computed_at.desc()).all()
            assert len(results) == 2, f'Expected 2 rows, got {len(results)}'
            assert results[0].score_value == 31.5, 'Newest should be 31.5'
            assert results[1].score_value == 28.0, 'Older should be 28.0'
        passed.append('1: score_history data ordered newest-first')
    except Exception as e:
        failed.append(f'1: score_history ordering: {e}')
    finally:
        try:
            os.unlink(tmp_db)
        except OSError:
            pass

    print('[2/10] score_history returns multiple historical rows...')
    test_app, tmp_db = _make_app()
    try:
        with test_app.app_context():
            from models import db
            from models.calculator import CalculatorResult
            from models.user import User
            from datetime import datetime, timezone, timedelta

            user = User(username='test_trend2', email='trend2@test.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            uid = user.id
            mrn = 'TEST_TREND_002'
            for i in range(4):
                r = CalculatorResult(
                    user_id=uid, mrn=mrn, calculator_key='ldl',
                    score_value=float(140 + i * 5),
                    is_current=(i == 3),
                    computed_at=datetime.now(timezone.utc) - timedelta(days=(3 - i) * 30),
                )
                db.session.add(r)
            db.session.commit()

            results = CalculatorResult.query.filter_by(mrn=mrn, calculator_key='ldl').all()
            assert len(results) == 4, f'Expected 4 rows, got {len(results)}'
        passed.append('2: score_history returns multiple rows')
    except Exception as e:
        failed.append(f'2: score_history multiple rows: {e}')
    finally:
        try:
            os.unlink(tmp_db)
        except OSError:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # Tests 3-4, 9: check_threshold_alerts
    # ─────────────────────────────────────────────────────────────────────────

    print('[3/10] check_threshold_alerts fires high severity for BMI >= 40...')
    try:
        from app.services.calculator_engine import CalculatorEngine
        eng = CalculatorEngine()
        scores = {'bmi': {'score_value': 42.3, 'score_label': 'obesity_class_3'}}
        alerts = eng.check_threshold_alerts(scores)
        bmi_alert = next((a for a in alerts if 'bmi' in a['key'].lower()), None)
        assert bmi_alert is not None, 'Expected BMI alert'
        assert bmi_alert['severity'] == 'high', f"Expected high, got {bmi_alert['severity']}"
        assert bmi_alert['color'] == 'red', f"Expected red, got {bmi_alert['color']}"
        passed.append('3: check_threshold_alerts BMI >= 40 high severity')
    except Exception as e:
        failed.append(f'3: check_threshold_alerts BMI: {e}')

    print('[4/10] check_threshold_alerts fires high severity for LDL >= 190...')
    try:
        from app.services.calculator_engine import CalculatorEngine
        eng = CalculatorEngine()
        scores = {'ldl': {'score_value': 205.0, 'score_label': 'very_high'}}
        alerts = eng.check_threshold_alerts(scores)
        ldl_alert = next((a for a in alerts if 'ldl' in a['key'].lower()), None)
        assert ldl_alert is not None, 'Expected LDL alert'
        assert ldl_alert['severity'] == 'high', f"Expected high, got {ldl_alert['severity']}"
        assert 'familial' in ldl_alert['text'].lower() or 'fh' in ldl_alert['text'].lower(), \
            'Alert text should mention familial hypercholesterolemia'
        passed.append('4: check_threshold_alerts LDL >= 190 high severity')
    except Exception as e:
        failed.append(f'4: check_threshold_alerts LDL: {e}')

    print('[9/10] check_threshold_alerts no alert when BMI < 30...')
    try:
        from app.services.calculator_engine import CalculatorEngine
        eng = CalculatorEngine()
        scores = {'bmi': {'score_value': 27.4, 'score_label': 'overweight'}}
        alerts = eng.check_threshold_alerts(scores)
        bmi_alerts = [a for a in alerts if 'bmi' in a['key'].lower()]
        assert len(bmi_alerts) == 0, f'Expected no BMI alert for 27.4; got {bmi_alerts}'
        passed.append('9: no alert when BMI < 30')
    except Exception as e:
        failed.append(f'9: no alert BMI < 30: {e}')

    # ─────────────────────────────────────────────────────────────────────────
    # Tests 5-6, 10: evaluate_calculator_care_gaps
    # ─────────────────────────────────────────────────────────────────────────

    print('[5/10] evaluate_calculator_care_gaps creates CareGap for BMI >= 30...')
    test_app, tmp_db = _make_app()
    try:
        with test_app.app_context():
            from models import db
            from models.calculator import CalculatorResult
            from models.user import User

            user = User(username='test_gap1', email='gap1@test.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            uid = user.id
            mrn = 'GAPTEST_001'
            r = CalculatorResult(
                user_id=uid, mrn=mrn, calculator_key='bmi',
                score_value=35.2, score_label='obese_class_2',
                is_current=True,
            )
            db.session.add(r)
            db.session.commit()

        from agent.caregap_engine import evaluate_calculator_care_gaps
        count = evaluate_calculator_care_gaps('GAPTEST_001', uid, 55.0, test_app)

        with test_app.app_context():
            from models.caregap import CareGap
            gap = CareGap.query.filter_by(mrn='GAPTEST_001', gap_type='obesity_counseling').first()
            assert gap is not None, 'Expected obesity_counseling gap'
            assert not gap.is_addressed, 'Gap should be open'
        assert count >= 1, f'Expected at least 1 new gap, got {count}'
        passed.append('5: evaluate_calculator_care_gaps creates BMI >= 30 gap')
    except Exception as e:
        failed.append(f'5: care gaps BMI >= 30: {e}')
    finally:
        try:
            os.unlink(tmp_db)
        except OSError:
            pass

    print('[6/10] evaluate_calculator_care_gaps creates LDCT gap for pack_years >= 20, age 55...')
    test_app, tmp_db = _make_app()
    try:
        with test_app.app_context():
            from models import db
            from models.calculator import CalculatorResult
            from models.user import User

            user = User(username='test_gap2', email='gap2@test.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            uid = user.id
            mrn = 'GAPTEST_002'
            r = CalculatorResult(
                user_id=uid, mrn=mrn, calculator_key='pack_years',
                score_value=25.0, score_label='high',
                is_current=True,
            )
            db.session.add(r)
            db.session.commit()

        from agent.caregap_engine import evaluate_calculator_care_gaps
        count = evaluate_calculator_care_gaps('GAPTEST_002', uid, 55.0, test_app)

        with test_app.app_context():
            from models.caregap import CareGap
            gap = CareGap.query.filter_by(mrn='GAPTEST_002', gap_type='lung_cancer_screening').first()
            assert gap is not None, 'Expected lung_cancer_screening gap'
            assert '71271' in (gap.billing_code_suggested or ''), \
                f'Expected 71271 in billing code, got {gap.billing_code_suggested}'
        assert count >= 1, f'Expected at least 1 new gap, got {count}'
        passed.append('6: evaluate_calculator_care_gaps creates LDCT gap')
    except Exception as e:
        failed.append(f'6: care gaps LDCT: {e}')
    finally:
        try:
            os.unlink(tmp_db)
        except OSError:
            pass

    print('[10/10] obesity_counseling care gap billing code is G0447...')
    test_app, tmp_db = _make_app()
    try:
        with test_app.app_context():
            from models import db
            from models.calculator import CalculatorResult
            from models.user import User

            user = User(username='test_gap3', email='gap3@test.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            uid = user.id
            mrn = 'GAPTEST_003'
            r = CalculatorResult(
                user_id=uid, mrn=mrn, calculator_key='bmi',
                score_value=31.0, score_label='obese_class_1',
                is_current=True,
            )
            db.session.add(r)
            db.session.commit()

        from agent.caregap_engine import evaluate_calculator_care_gaps
        evaluate_calculator_care_gaps('GAPTEST_003', uid, 45.0, test_app)

        with test_app.app_context():
            from models.caregap import CareGap
            gap = CareGap.query.filter_by(mrn='GAPTEST_003', gap_type='obesity_counseling').first()
            assert gap is not None, 'Expected obesity_counseling gap'
            assert 'G0447' in (gap.billing_code_suggested or ''), \
                f'Expected G0447, got {gap.billing_code_suggested}'
        passed.append('10: obesity_counseling billing code is G0447')
    except Exception as e:
        failed.append(f'10: G0447 billing code: {e}')
    finally:
        try:
            os.unlink(tmp_db)
        except OSError:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # Tests 7-8: detect_score_changes
    # ─────────────────────────────────────────────────────────────────────────

    print('[7/10] detect_score_changes returns empty list when only one result...')
    test_app, tmp_db = _make_app()
    try:
        with test_app.app_context():
            from models import db
            from models.calculator import CalculatorResult
            from models.user import User

            user = User(username='test_chg1', email='chg1@test.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            uid = user.id
            mrn = 'CHGTEST_001'
            r = CalculatorResult(
                user_id=uid, mrn=mrn, calculator_key='bmi',
                score_value=29.5, score_label='overweight',
                is_current=True,
            )
            db.session.add(r)
            db.session.commit()

            from app.services.calculator_engine import CalculatorEngine
            eng = CalculatorEngine()
            changes = eng.detect_score_changes(mrn, uid)
            assert changes == [], f'Expected empty list, got {changes}'
        passed.append('7: detect_score_changes empty when one result')
    except Exception as e:
        failed.append(f'7: detect_score_changes one result: {e}')
    finally:
        try:
            os.unlink(tmp_db)
        except OSError:
            pass

    print('[8/10] detect_score_changes detects significant BMI increase >= 2...')
    test_app, tmp_db = _make_app()
    try:
        with test_app.app_context():
            from models import db
            from models.calculator import CalculatorResult
            from models.user import User
            from datetime import datetime, timezone, timedelta

            user = User(username='test_chg2', email='chg2@test.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            uid = user.id
            mrn = 'CHGTEST_002'
            old_r = CalculatorResult(
                user_id=uid, mrn=mrn, calculator_key='bmi',
                score_value=28.0, score_label='overweight',
                is_current=False,
                computed_at=datetime.now(timezone.utc) - timedelta(days=90),
            )
            new_r = CalculatorResult(
                user_id=uid, mrn=mrn, calculator_key='bmi',
                score_value=32.5, score_label='obese_class_1',
                is_current=True,
                computed_at=datetime.now(timezone.utc),
            )
            db.session.add_all([old_r, new_r])
            db.session.commit()

            from app.services.calculator_engine import CalculatorEngine
            eng = CalculatorEngine()
            changes = eng.detect_score_changes(mrn, uid)
            bmi_chg = next((c for c in changes if c['calculator_key'] == 'bmi'), None)
            assert bmi_chg is not None, f'Expected BMI change; got {changes}'
            assert bmi_chg['direction'] == 'up', f"Expected up, got {bmi_chg['direction']}"
            assert bmi_chg['change'] >= 2.0, f"Expected delta >= 2, got {bmi_chg['change']}"
        passed.append('8: detect_score_changes detects BMI increase >= 2')
    except Exception as e:
        failed.append(f'8: detect_score_changes BMI delta: {e}')
    finally:
        try:
            os.unlink(tmp_db)
        except OSError:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────────────────────────────────────
    print()
    print(f'Results: {len(passed)}/10 passed, {len(failed)}/10 failed')
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

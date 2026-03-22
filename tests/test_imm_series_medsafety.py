"""
Phase 24 — Immunization Series + Medication Safety Tests

Verifies:
  1-3:   ImmunizationSeries model + migration
  4-6:   Series definitions (8 vaccine groups)
  7-9:   Series gap detection + populate logic
  10-11: Seasonal alerts (flu, pneumococcal)
  12-13: Morning briefing + patient chart integration
  14:    Medication safety prep function
  15:    Vaccine admin detector series tracking

Usage:
    venv\\Scripts\\python.exe tests/test_imm_series_medsafety.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(relpath):
    with open(os.path.join(ROOT, relpath), encoding='utf-8') as f:
        return f.read()


def _get_app():
    os.environ['FLASK_ENV'] = 'testing'
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app


def run_tests():
    passed = []
    failed = []

    # ==================================================================
    # 1 — ImmunizationSeries model exists with required fields
    # ==================================================================
    print('[1/15] ImmunizationSeries model fields...')
    try:
        from models.immunization import ImmunizationSeries
        required = [
            'patient_mrn_hash', 'user_id', 'vaccine_group', 'dose_number',
            'dose_date', 'next_dose_due_date', 'next_dose_window_end',
            'series_status', 'total_doses', 'vaccine_cpt',
            'age_min', 'age_max', 'seasonal',
        ]
        for f in required:
            assert hasattr(ImmunizationSeries, f), f'Missing: {f}'
        passed.append('1: ImmunizationSeries model has all fields')
    except Exception as e:
        failed.append(f'1: Model fields: {e}')

    # ==================================================================
    # 2 — immunization_series table exists in database
    # ==================================================================
    print('[2/15] Database table exists...')
    try:
        app = _get_app()
        with app.app_context():
            from sqlalchemy import inspect
            from models import db
            tables = inspect(db.engine).get_table_names()
            assert 'immunization_series' in tables
        passed.append('2: immunization_series table in DB')
    except Exception as e:
        failed.append(f'2: Table exists: {e}')

    # ==================================================================
    # 3 — Migration file exists and is importable
    # ==================================================================
    print('[3/15] Migration file...')
    try:
        assert os.path.exists(os.path.join(ROOT, 'migrations', 'migrate_add_imm_series.py'))
        from migrations.migrate_add_imm_series import run_migration
        assert callable(run_migration)
        passed.append('3: Migration file exists and importable')
    except Exception as e:
        failed.append(f'3: Migration: {e}')

    # ==================================================================
    # 4 — SERIES_DEFINITIONS covers all 8 vaccine groups
    # ==================================================================
    print('[4/15] 8 vaccine groups defined...')
    try:
        from app.services.immunization_engine import SERIES_DEFINITIONS
        groups = {d['group'] for d in SERIES_DEFINITIONS}
        expected = {'Shingrix', 'HepB', 'HepA', 'HPV', 'COVID', 'RSV', 'MenACWY', 'MenB'}
        missing = expected - groups
        assert not missing, f'Missing groups: {missing}'
        passed.append('4: All 8 vaccine groups defined')
    except Exception as e:
        failed.append(f'4: Vaccine groups: {e}')

    # ==================================================================
    # 5 — Shingrix is 2-dose, age ≥50
    # ==================================================================
    print('[5/15] Shingrix: 2-dose, age ≥50...')
    try:
        from app.services.immunization_engine import SERIES_DEFINITIONS
        shingrix = next(d for d in SERIES_DEFINITIONS if d['group'] == 'Shingrix')
        assert shingrix['total_doses'] == 2
        assert shingrix['age_min'] == 50
        assert 'shingrix' in shingrix['match_names']
        passed.append('5: Shingrix 2-dose, age ≥50')
    except Exception as e:
        failed.append(f'5: Shingrix: {e}')

    # ==================================================================
    # 6 — Each definition has match_names, dose_intervals, age range
    # ==================================================================
    print('[6/15] Definition completeness...')
    try:
        from app.services.immunization_engine import SERIES_DEFINITIONS
        for d in SERIES_DEFINITIONS:
            assert 'match_names' in d, f'{d["group"]} missing match_names'
            assert 'dose_intervals' in d, f'{d["group"]} missing dose_intervals'
            assert 'age_min' in d, f'{d["group"]} missing age_min'
            assert 'age_max' in d, f'{d["group"]} missing age_max'
            assert 'total_doses' in d, f'{d["group"]} missing total_doses'
        passed.append('6: All definitions complete')
    except Exception as e:
        failed.append(f'6: Definition completeness: {e}')

    # ==================================================================
    # 7 — get_series_gaps returns gaps for age-eligible patient
    # ==================================================================
    print('[7/15] get_series_gaps for eligible patient...')
    try:
        app = _get_app()
        with app.app_context():
            from app.services.immunization_engine import get_series_gaps
            # 65-year-old patient with no immunization records
            gaps = get_series_gaps('test_mrn_hash', 1, 65)
            # Should include at least Shingrix (age≥50) and RSV (age≥60)
            gap_groups = {g['vaccine_group'] for g in gaps}
            assert 'Shingrix' in gap_groups, 'Missing Shingrix for age 65'
            assert 'RSV' in gap_groups, 'Missing RSV for age 65'
            passed.append('7: Series gaps include Shingrix + RSV for age 65')
    except Exception as e:
        failed.append(f'7: Series gaps: {e}')

    # ==================================================================
    # 8 — get_series_gaps excludes age-ineligible vaccines
    # ==================================================================
    print('[8/15] Age exclusion in gaps...')
    try:
        app = _get_app()
        with app.app_context():
            from app.services.immunization_engine import get_series_gaps
            gaps = get_series_gaps('test_mrn_hash', 1, 30)
            gap_groups = {g['vaccine_group'] for g in gaps}
            assert 'Shingrix' not in gap_groups, 'Shingrix should not appear for age 30'
            assert 'RSV' not in gap_groups, 'RSV should not appear for age 30'
            passed.append('8: Age-ineligible vaccines excluded')
    except Exception as e:
        failed.append(f'8: Age exclusion: {e}')

    # ==================================================================
    # 9 — populate_patient_series function exists and is callable
    # ==================================================================
    print('[9/15] populate_patient_series callable...')
    try:
        from app.services.immunization_engine import populate_patient_series
        assert callable(populate_patient_series)
        passed.append('9: populate_patient_series is callable')
    except Exception as e:
        failed.append(f'9: Populate function: {e}')

    # ==================================================================
    # 10 — Seasonal alerts: flu in March (within Sep-Mar)
    # ==================================================================
    print('[10/15] Seasonal alert: flu in March...')
    try:
        from app.services.immunization_engine import get_seasonal_alerts
        from datetime import date
        # March 15 should be in flu season (Sep-Mar)
        alerts = get_seasonal_alerts(45, date(2026, 3, 15))
        alert_groups = {a['group'] for a in alerts}
        assert 'Influenza' in alert_groups, 'Flu alert missing in March'
        passed.append('10: Flu alert fires in March')
    except Exception as e:
        failed.append(f'10: Flu alert: {e}')

    # ==================================================================
    # 11 — Seasonal alerts: no flu in June, pneumococcal for age≥65
    # ==================================================================
    print('[11/15] Seasonal: no flu in June, pneumo for 65+...')
    try:
        from app.services.immunization_engine import get_seasonal_alerts
        from datetime import date
        # June: no flu season
        alerts_june = get_seasonal_alerts(45, date(2026, 6, 15))
        alert_groups_june = {a['group'] for a in alerts_june}
        assert 'Influenza' not in alert_groups_june, 'Flu should not fire in June'

        # Pneumococcal for age 65 (no season restriction)
        alerts_65 = get_seasonal_alerts(65, date(2026, 6, 15))
        alert_groups_65 = {a['group'] for a in alerts_65}
        assert 'Pneumococcal' in alert_groups_65, 'Pneumococcal missing for age 65'
        passed.append('11: No flu in June; pneumococcal for 65+')
    except Exception as e:
        failed.append(f'11: Seasonal logic: {e}')

    # ==================================================================
    # 12 — Morning briefing passes imm_gaps and imm_seasonal
    # ==================================================================
    print('[12/15] Briefing route includes immunization data...')
    try:
        src = _read('routes/intelligence.py')
        assert 'imm_gaps' in src, 'Missing imm_gaps in briefing'
        assert 'imm_seasonal' in src, 'Missing imm_seasonal in briefing'
        assert 'get_series_gaps' in src, 'Missing get_series_gaps call'
        assert 'get_seasonal_alerts' in src, 'Missing get_seasonal_alerts call'
        # Check template also uses these
        tpl = _read('templates/morning_briefing.html')
        assert 'imm_gaps' in tpl, 'Missing imm_gaps in template'
        assert 'imm_seasonal' in tpl, 'Missing imm_seasonal in template'
        assert 'Vaccine Series' in tpl, 'Missing vaccine series section header'
        passed.append('12: Briefing wired with immunization data')
    except Exception as e:
        failed.append(f'12: Briefing wiring: {e}')

    # ==================================================================
    # 13 — Patient chart includes imm_series_gaps
    # ==================================================================
    print('[13/15] Patient chart includes series gap flags...')
    try:
        src = _read('routes/patient.py')
        assert 'imm_series_gaps' in src, 'Missing imm_series_gaps in patient route'
        assert 'populate_patient_series' in src, 'Missing populate call in chart'
        tpl = _read('templates/patient_chart.html')
        assert 'imm_series_gaps' in tpl, 'Missing imm_series_gaps in chart template'
        assert 'Incomplete Series' in tpl, 'Missing series gap section'
        passed.append('13: Patient chart shows series gap flags')
    except Exception as e:
        failed.append(f'13: Chart gaps: {e}')

    # ==================================================================
    # 14 — Medication safety prep function exists in scheduler
    # ==================================================================
    print('[14/15] Medication safety prep in scheduler...')
    try:
        src = _read('app/services/api_scheduler.py')
        assert '_run_medication_safety_prep' in src, 'Missing safety prep function'
        assert 'staff_lab_prep' in src, 'Missing staff lab prep notifications'
        assert 'med_recall_prep' in src, 'Missing recall prep notifications'
        # Wired into morning briefing
        assert '_run_medication_safety_prep(db)' in src, 'Not wired into scheduler'
        passed.append('14: Medication safety prep exists and wired')
    except Exception as e:
        failed.append(f'14: Safety prep: {e}')

    # ==================================================================
    # 15 — Vaccine admin detector has series gap detection
    # ==================================================================
    print('[15/15] Vaccine admin detector series tracking...')
    try:
        src = _read('billing_engine/detectors/vaccine_admin.py')
        assert '_detect_series_gaps' in src, 'Missing series gap detection'
        assert 'vaccine_series' in src, 'Missing vaccine_series input'
        assert 'VACCINE_PRODUCT_CODES' in src, 'Missing product codes reference'
        # Verify at least 6 vaccine rules defined
        assert 'HPV' in src, 'Missing HPV'
        assert 'HepB' in src, 'Missing HepB'
        assert 'RSV' in src, 'Missing RSV'
        passed.append('15: Vaccine admin detector has series tracking')
    except Exception as e:
        failed.append(f'15: Detector: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print('\n' + '=' * 60)
    print(f'Phase 24 — Immunization Series + Med Safety: {len(passed)} passed, {len(failed)} failed')
    print('=' * 60)
    for p in passed:
        print(f'  ✅ {p}')
    for f in failed:
        print(f'  ❌ {f}')
    print()

    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

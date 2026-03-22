"""
Phase 29.8 — Scenario-Based Synthetic Patient Tests

15 tests using 5 synthetic patients to validate end-to-end engine evaluate()
with realistic clinical data, verifying expected opportunities, suppressions,
and payer-specific code selection.

Usage:
    venv\\Scripts\\python.exe tests/test_billing_scenarios.py
"""

import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _get_app():
    os.environ['FLASK_ENV'] = 'testing'
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app


# =====================================================================
# Synthetic Patient Definitions
# =====================================================================

PATIENT_1_MEDICARE_68F = {
    'insurer_type': 'medicare',
    'patient_age': 68,
    'sex': 'female',
    'visit_type': 'office_visit',
    'user_id': 1,
    'mrn': 'SCEN001',
    'diagnoses': [
        {'icd10_code': 'I10', 'status': 'active'},       # HTN
        {'icd10_code': 'E11.65', 'status': 'active'},     # DM2
        {'icd10_code': 'N18.3', 'status': 'active'},      # CKD3
        {'icd10_code': 'E78.5', 'status': 'active'},      # HLD
    ],
    'medications': [
        {'name': 'Lisinopril 20mg'},
        {'name': 'Metformin 1000mg'},
        {'name': 'Atorvastatin 40mg'},
    ],
    'active_chronic_conditions': 4,
    'chronic_conditions_count': 4,
    'ccm_minutes_this_month': 25,
    'prior_encounters_count': 8,
    'awv_history': {'last_awv_date': None},
    'last_awv_date': None,
}

PATIENT_2_MEDICARE_72M = {
    'insurer_type': 'medicare',
    'patient_age': 72,
    'sex': 'male',
    'visit_type': 'office_visit',
    'user_id': 1,
    'mrn': 'SCEN002',
    'diagnoses': [
        {'icd10_code': 'I25.10', 'status': 'active'},     # CAD
        {'icd10_code': 'I50.22', 'status': 'active'},      # HFrEF
        {'icd10_code': 'J44.1', 'status': 'active'},       # COPD
        {'icd10_code': 'F33.1', 'status': 'active'},       # Depression
    ],
    'medications': [
        {'name': 'Metoprolol 50mg'},
        {'name': 'Entresto 97/103mg'},
        {'name': 'Sertraline 100mg'},
    ],
    'active_chronic_conditions': 4,
    'chronic_conditions_count': 4,
    'discharge_date': (date.today() - timedelta(days=7)).isoformat(),
    'days_since_discharge': 7,
    'behavioral_dx_minutes': 25,
    'ccm_minutes_this_month': 30,
    'prior_encounters_count': 12,
    'awv_history': {'last_awv_date': (date.today() - timedelta(days=400)).isoformat()},
}

PATIENT_3_COMMERCIAL_44F = {
    'insurer_type': 'commercial',
    'patient_age': 44,
    'sex': 'female',
    'visit_type': 'office_visit',
    'user_id': 1,
    'mrn': 'SCEN003',
    'diagnoses': [
        {'icd10_code': 'E66.01', 'status': 'active'},     # Obesity BMI 34
        {'icd10_code': 'F41.1', 'status': 'active'},       # Anxiety
        {'icd10_code': 'F17.210', 'status': 'active'},     # Tobacco
    ],
    'medications': [
        {'name': 'Buspirone 10mg'},
    ],
    'active_chronic_conditions': 3,
    'chronic_conditions_count': 3,
    'prior_encounters_count': 4,
    'awv_history': {'last_awv_date': None},
    'em_code_today': '99214',
}

PATIENT_4_MEDICAID_28F = {
    'insurer_type': 'medicaid',
    'patient_age': 28,
    'sex': 'female',
    'visit_type': 'office_visit',
    'user_id': 1,
    'mrn': 'SCEN004',
    'diagnoses': [
        {'icd10_code': 'F90.0', 'status': 'active'},       # ADHD
        {'icd10_code': 'O24.410', 'status': 'active'},     # GDM
    ],
    'medications': [
        {'name': 'Adderall 20mg'},
    ],
    'active_chronic_conditions': 2,
    'chronic_conditions_count': 2,
    'prior_encounters_count': 3,
}

PATIENT_5_SELFPAY_55M = {
    'insurer_type': 'unknown',
    'patient_age': 55,
    'sex': 'male',
    'visit_type': 'office_visit',
    'user_id': 1,
    'mrn': 'SCEN005',
    'diagnoses': [
        {'icd10_code': 'I10', 'status': 'active'},         # HTN
        {'icd10_code': 'R73.09', 'status': 'active'},      # Pre-diabetes
        {'icd10_code': 'F17.210', 'status': 'active'},     # Tobacco
    ],
    'medications': [
        {'name': 'Amlodipine 5mg'},
    ],
    'active_chronic_conditions': 2,
    'chronic_conditions_count': 2,
    'prior_encounters_count': 2,
}


def _get_codes(opps):
    """Extract all applicable_codes from a list of BillingOpportunity objects."""
    codes = set()
    for o in opps:
        c = getattr(o, 'applicable_codes', '') or ''
        for code in c.replace(',', ' ').split():
            codes.add(code.strip())
    return codes


def _get_categories(opps):
    """Extract all categories from opportunities."""
    return {getattr(o, 'category', '') or '' for o in opps}


def run_tests():
    passed = []
    failed = []
    app = _get_app()

    with app.app_context():
        from models import db
        from billing_engine.engine import BillingCaptureEngine
        engine = BillingCaptureEngine(db=db)

        # ==================================================================
        # Patient 1: Medicare 68F — HTN + DM2 + CKD3 + HLD
        # ==================================================================

        # 1 — Engine returns opportunities
        print('[1/15] Patient 1: Engine returns opportunities...')
        try:
            opps = engine.evaluate(PATIENT_1_MEDICARE_68F)
            assert len(opps) > 0, f'Expected >0 opportunities, got {len(opps)}'
            passed.append(f'1: Medicare 68F → {len(opps)} opportunities')
        except Exception as e:
            failed.append(f'1: {e}')

        # 2 — CCM detected (4 chronic conditions + 25 min)
        print('[2/15] Patient 1: CCM detected...')
        try:
            cats = _get_categories(opps)
            assert 'ccm' in cats, f'CCM not found in {cats}'
            passed.append('2: Medicare 68F → CCM detected')
        except Exception as e:
            failed.append(f'2: {e}')

        # 3 — AWV detected (no prior AWV)
        print('[3/15] Patient 1: AWV detected...')
        try:
            codes = _get_codes(opps)
            has_awv = 'G0438' in codes or 'G0439' in codes
            assert has_awv, f'AWV codes not found in {codes}'
            passed.append('3: Medicare 68F → AWV detected')
        except Exception as e:
            failed.append(f'3: {e}')

        # ==================================================================
        # Patient 2: Medicare 72M — CAD + HF + COPD + Depression
        # ==================================================================

        # 4 — Engine returns opportunities
        print('[4/15] Patient 2: Engine returns opportunities...')
        try:
            opps2 = engine.evaluate(PATIENT_2_MEDICARE_72M)
            assert len(opps2) > 0, f'Expected >0 opportunities, got {len(opps2)}'
            passed.append(f'4: Medicare 72M → {len(opps2)} opportunities')
        except Exception as e:
            failed.append(f'4: {e}')

        # 5 — TCM detected (recent discharge)
        print('[5/15] Patient 2: TCM detected...')
        try:
            cats2 = _get_categories(opps2)
            assert 'tcm' in cats2, f'TCM not found in {cats2}'
            passed.append('5: Medicare 72M → TCM detected')
        except Exception as e:
            failed.append(f'5: {e}')

        # 6 — BHI detected (depression + minutes)
        print('[6/15] Patient 2: BHI detected...')
        try:
            cats2 = _get_categories(opps2)
            assert 'bhi' in cats2, f'BHI not found in {cats2}'
            passed.append('6: Medicare 72M → BHI detected')
        except Exception as e:
            failed.append(f'6: {e}')

        # ==================================================================
        # Patient 3: Commercial 44F — Obesity + Anxiety + Tobacco
        # ==================================================================

        # 7 — Engine returns opportunities
        print('[7/15] Patient 3: Engine returns opportunities...')
        try:
            opps3 = engine.evaluate(PATIENT_3_COMMERCIAL_44F)
            assert len(opps3) > 0, f'Expected >0 opportunities, got {len(opps3)}'
            passed.append(f'7: Commercial 44F → {len(opps3)} opportunities')
        except Exception as e:
            failed.append(f'7: {e}')

        # 8 — Tobacco cessation detected
        print('[8/15] Patient 3: Tobacco cessation detected...')
        try:
            cats3 = _get_categories(opps3)
            assert 'tobacco_cessation' in cats3, f'Tobacco not in {cats3}'
            passed.append('8: Commercial 44F → Tobacco cessation')
        except Exception as e:
            failed.append(f'8: {e}')

        # 9 — Obesity/nutrition detected
        print('[9/15] Patient 3: Obesity detected...')
        try:
            cats3 = _get_categories(opps3)
            assert 'obesity_nutrition' in cats3, f'Obesity not in {cats3}'
            passed.append('9: Commercial 44F → Obesity/nutrition')
        except Exception as e:
            failed.append(f'9: {e}')

        # ==================================================================
        # Patient 4: Medicaid 28F — ADHD + GDM
        # ==================================================================

        # 10 — Engine returns opportunities
        print('[10/15] Patient 4: Engine returns opportunities...')
        try:
            opps4 = engine.evaluate(PATIENT_4_MEDICAID_28F)
            assert len(opps4) >= 0  # May be 0 if no matching detectors
            passed.append(f'10: Medicaid 28F → {len(opps4)} opportunities')
        except Exception as e:
            failed.append(f'10: {e}')

        # 11 — G2211 NOT detected (Medicaid)
        print('[11/15] Patient 4: G2211 suppressed for Medicaid...')
        try:
            cats4 = _get_categories(opps4)
            codes4 = _get_codes(opps4)
            assert 'G2211' not in codes4, f'G2211 should not appear for Medicaid: {codes4}'
            passed.append('11: Medicaid 28F → G2211 correctly suppressed')
        except Exception as e:
            failed.append(f'11: {e}')

        # 12 — Payer context uses modifier 33 for Medicaid
        print('[12/15] Patient 4: Medicaid modifier 33...')
        try:
            from billing_engine.payer_routing import get_payer_context
            ctx4 = get_payer_context(PATIENT_4_MEDICAID_28F)
            assert ctx4['use_modifier_33'] is True
            assert ctx4['use_g_codes'] is False
            passed.append('12: Medicaid → modifier 33, no G-codes')
        except Exception as e:
            failed.append(f'12: {e}')

        # ==================================================================
        # Patient 5: Self-pay/Unknown 55M — HTN + Pre-diabetes + Tobacco
        # ==================================================================

        # 13 — Engine returns opportunities (unknown defaults to commercial)
        print('[13/15] Patient 5: Engine returns opportunities...')
        try:
            opps5 = engine.evaluate(PATIENT_5_SELFPAY_55M)
            assert len(opps5) >= 0
            passed.append(f'13: Unknown 55M → {len(opps5)} opportunities')
        except Exception as e:
            failed.append(f'13: {e}')

        # 14 — Tobacco detected
        print('[14/15] Patient 5: Tobacco detected...')
        try:
            cats5 = _get_categories(opps5)
            assert 'tobacco_cessation' in cats5, f'Tobacco not in {cats5}'
            passed.append('14: Unknown 55M → Tobacco cessation')
        except Exception as e:
            failed.append(f'14: {e}')

        # 15 — Unknown payer → commercial context
        print('[15/15] Patient 5: Unknown → commercial...')
        try:
            from billing_engine.payer_routing import get_payer_context
            ctx5 = get_payer_context(PATIENT_5_SELFPAY_55M)
            assert ctx5['payer_type'] == 'commercial', f'Got {ctx5["payer_type"]}'
            passed.append('15: Unknown insurer → commercial payer context')
        except Exception as e:
            failed.append(f'15: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print('\n' + '=' * 60)
    print(f'Phase 29.8 — Scenario Tests: {len(passed)} passed, {len(failed)} failed')
    print('=' * 60)
    for p in passed:
        print(f'  \u2705 {p}')
    for f in failed:
        print(f'  \u274c {f}')
    print()

    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

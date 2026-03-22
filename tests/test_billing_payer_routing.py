"""
Phase 29.3 — Payer Routing Tests

15 tests covering code selection, modifier logic, suppression rules,
cost-share notes, vaccine admin codes, and MA vs Traditional Medicare.

Usage:
    venv\\Scripts\\python.exe tests/test_billing_payer_routing.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    passed = []
    failed = []

    from billing_engine.payer_routing import get_payer_context

    # ==================================================================
    # 1 — Medicare → payer_type "medicare_b"
    # ==================================================================
    print('[1/15] Medicare normalisation...')
    try:
        ctx = get_payer_context({'insurer_type': 'medicare', 'age': 70})
        assert ctx['payer_type'] == 'medicare_b', f'Got {ctx["payer_type"]}'
        passed.append('1: Medicare → medicare_b')
    except Exception as e:
        failed.append(f'1: {e}')

    # ==================================================================
    # 2 — Medicare uses G-codes
    # ==================================================================
    print('[2/15] Medicare uses G-codes...')
    try:
        ctx = get_payer_context({'insurer_type': 'medicare', 'age': 70})
        assert ctx['use_g_codes'] is True
        assert ctx['use_modifier_33'] is False
        passed.append('2: Medicare uses G-codes, no modifier 33')
    except Exception as e:
        failed.append(f'2: {e}')

    # ==================================================================
    # 3 — Commercial uses modifier 33
    # ==================================================================
    print('[3/15] Commercial uses modifier 33...')
    try:
        ctx = get_payer_context({'insurer_type': 'commercial', 'age': 45})
        assert ctx['use_g_codes'] is False
        assert ctx['use_modifier_33'] is True
        passed.append('3: Commercial uses modifier 33')
    except Exception as e:
        failed.append(f'3: {e}')

    # ==================================================================
    # 4 — Medicare Advantage: CPT codes (not G-codes), modifier 33
    # ==================================================================
    print('[4/15] MA: CPT codes + modifier 33...')
    try:
        ctx = get_payer_context({'insurer_type': 'medicare_advantage', 'age': 68})
        assert ctx['payer_type'] == 'medicare_advantage'
        assert ctx['use_g_codes'] is False, 'MA should NOT use G-codes'
        assert ctx['use_modifier_33'] is True, 'MA should use modifier 33'
        assert ctx['is_medicare'] is True, 'MA is still Medicare'
        assert ctx['is_medicare_advantage'] is True
        passed.append('4: MA uses CPT + modifier 33')
    except Exception as e:
        failed.append(f'4: {e}')

    # ==================================================================
    # 5 — Medicare vaccine admin: flu→G0008
    # ==================================================================
    print('[5/15] Medicare vaccine admin G-codes...')
    try:
        ctx = get_payer_context({'insurer_type': 'medicare', 'age': 70})
        assert ctx['admin_codes']['flu_admin'] == 'G0008'
        assert ctx['admin_codes']['pneumo_admin'] == 'G0009'
        assert ctx['admin_codes']['hepb_admin'] == 'G0010'
        passed.append('5: Medicare vaccine admin G-codes')
    except Exception as e:
        failed.append(f'5: {e}')

    # ==================================================================
    # 6 — Commercial vaccine admin: 90471
    # ==================================================================
    print('[6/15] Commercial vaccine admin 90471...')
    try:
        ctx = get_payer_context({'insurer_type': 'commercial', 'age': 45})
        assert ctx['admin_codes']['flu_admin'] == '90471'
        assert ctx['admin_codes']['standard_first'] == '90471'
        assert ctx['admin_codes']['standard_additional'] == '90472'
        passed.append('6: Commercial vaccine admin 90471')
    except Exception as e:
        failed.append(f'6: {e}')

    # ==================================================================
    # 7 — Medicaid EPSDT eligibility (age <21)
    # ==================================================================
    print('[7/15] Medicaid EPSDT eligibility...')
    try:
        ctx = get_payer_context({'insurer_type': 'medicaid', 'age': 15})
        assert ctx['epsdt_eligible'] is True
        assert ctx['mandatory_lead_screening'] is False  # age > 6
        passed.append('7: Medicaid EPSDT for age 15')
    except Exception as e:
        failed.append(f'7: {e}')

    # ==================================================================
    # 8 — Medicaid mandatory lead screening (age ≤6)
    # ==================================================================
    print('[8/15] Medicaid lead screening...')
    try:
        ctx = get_payer_context({'insurer_type': 'medicaid', 'age': 3})
        assert ctx['mandatory_lead_screening'] is True
        assert ctx['epsdt_eligible'] is True
        passed.append('8: Medicaid lead screening age 3')
    except Exception as e:
        failed.append(f'8: {e}')

    # ==================================================================
    # 9 — G2211 only for traditional Medicare
    # ==================================================================
    print('[9/15] G2211 eligibility...')
    try:
        med = get_payer_context({'insurer_type': 'medicare', 'age': 70})
        com = get_payer_context({'insurer_type': 'commercial', 'age': 50})
        ma = get_payer_context({'insurer_type': 'medicare_advantage', 'age': 68})
        assert med['g2211_eligible'] is True
        assert com['g2211_eligible'] is False
        assert ma['g2211_eligible'] is False
        passed.append('9: G2211 eligible only for traditional Medicare')
    except Exception as e:
        failed.append(f'9: {e}')

    # ==================================================================
    # 10 — Unknown insurer → commercial
    # ==================================================================
    print('[10/15] Unknown insurer...')
    try:
        ctx = get_payer_context({'insurer_type': 'unknown', 'age': 40})
        assert ctx['payer_type'] == 'commercial', f'Got {ctx["payer_type"]}'
        passed.append('10: Unknown insurer → commercial')
    except Exception as e:
        failed.append(f'10: {e}')

    # ==================================================================
    # 11 — Commercial G2211 suppressed
    # ==================================================================
    print('[11/15] Commercial G2211 suppressed...')
    try:
        ctx = get_payer_context({'insurer_type': 'commercial', 'age': 50})
        assert 'G2211_COMPLEXITY' in ctx['suppressed_codes']
        passed.append('11: G2211 suppressed for commercial')
    except Exception as e:
        failed.append(f'11: {e}')

    # ==================================================================
    # 12 — Commercial CCM suppressed
    # ==================================================================
    print('[12/15] Commercial CCM suppressed...')
    try:
        ctx = get_payer_context({'insurer_type': 'commercial', 'age': 60})
        assert 'CCM' in ctx['suppressed_codes']
        passed.append('12: CCM suppressed for commercial')
    except Exception as e:
        failed.append(f'12: {e}')

    # ==================================================================
    # 13 — Medicare cost-share: AWV no copay
    # ==================================================================
    print('[13/15] Medicare cost-share AWV...')
    try:
        ctx = get_payer_context({'insurer_type': 'medicare', 'age': 70})
        notes = ctx['cost_share_notes']
        assert 'AWV_FLAG' in notes, 'AWV_FLAG missing from cost_share_notes'
        assert 'no copay' in notes['AWV_FLAG'].lower()
        passed.append('13: Medicare AWV cost-share note')
    except Exception as e:
        failed.append(f'13: {e}')

    # ==================================================================
    # 14 — Commercial cost-share: modifier 33 ACA benefit
    # ==================================================================
    print('[14/15] Commercial cost-share modifier 33...')
    try:
        ctx = get_payer_context({'insurer_type': 'commercial', 'age': 45})
        notes = ctx['cost_share_notes']
        assert 'TOBACCO_SCREEN' in notes
        assert 'modifier 33' in notes['TOBACCO_SCREEN'].lower()
        passed.append('14: Commercial modifier 33 cost-share note')
    except Exception as e:
        failed.append(f'14: {e}')

    # ==================================================================
    # 15 — All expected keys present in output
    # ==================================================================
    print('[15/15] All expected keys present...')
    try:
        ctx = get_payer_context({'insurer_type': 'medicare', 'age': 70})
        expected_keys = {
            'payer_type', 'is_medicare_advantage', 'use_g_codes',
            'use_modifier_33', 'admin_codes', 'awv_eligible',
            'ccm_eligible', 'g2211_eligible', 'epsdt_eligible',
            'mandatory_lead_screening', 'cocm_eligible',
            'is_medicare', 'is_medicare_traditional', 'is_medicaid',
            'is_commercial', 'suppressed_codes', 'cost_share_notes',
        }
        missing = expected_keys - set(ctx.keys())
        assert not missing, f'Missing keys: {missing}'
        passed.append(f'15: All {len(expected_keys)} keys present')
    except Exception as e:
        failed.append(f'15: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print('\n' + '=' * 60)
    print(f'Phase 29.3 — Payer Routing: {len(passed)} passed, {len(failed)} failed')
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

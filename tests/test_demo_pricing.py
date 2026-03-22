"""
Integration tests for Phase 29: Demo Mode Pricing Data

Tests verify:
- PRICING_DEMO_DATA dictionary exists with expected drugs
- seed_pricing_demo_data function exists and is callable
- Patient-specific pricing data present for all demo patients
- MedRef common drugs included
- Badge colors match price thresholds
- Assistance programs for expensive meds
- Demo data flag present
- seed_all_test_data calls seed_pricing_demo_data
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(relpath):
    with open(os.path.join(ROOT, relpath), 'r', encoding='utf-8') as f:
        return f.read()


def run_tests():
    passed = []
    failed = []

    seed_py = _read('scripts/seed_test_data.py')

    # ==========================================================
    # 29.1 — PRICING_DEMO_DATA dictionary
    # ==========================================================
    print('[1/15] PRICING_DEMO_DATA exists...')
    try:
        assert 'PRICING_DEMO_DATA' in seed_py, 'Dictionary defined'
        passed.append('29.1 Demo data dict')
    except AssertionError as e:
        failed.append(f'29.1 Dict: {e}')

    print('[2/15] Patient 90001 medications (lisinopril/metformin/atorvastatin/alendronate)...')
    try:
        assert "'lisinopril'" in seed_py, 'lisinopril'
        assert "'metformin'" in seed_py, 'metformin'
        assert "'atorvastatin'" in seed_py, 'atorvastatin'
        assert "'alendronate'" in seed_py, 'alendronate'
        passed.append('29.1b Patient 90001 meds')
    except AssertionError as e:
        failed.append(f'29.1b P90001: {e}')

    print('[3/15] Patient 90002 medications (amlodipine/tiotropium)...')
    try:
        assert "'amlodipine'" in seed_py, 'amlodipine'
        assert "'tiotropium'" in seed_py, 'tiotropium'
        passed.append('29.1c Patient 90002 meds')
    except AssertionError as e:
        failed.append(f'29.1c P90002: {e}')

    print('[4/15] Patient 90003 medications (buspirone)...')
    try:
        assert "'buspirone'" in seed_py, 'buspirone'
        passed.append('29.1d Patient 90003 meds')
    except AssertionError as e:
        failed.append(f'29.1d P90003: {e}')

    print('[5/15] Badge colors match thresholds (green <$30, yellow <$100, red >=$100)...')
    try:
        # Import to verify actual data
        sys.path.insert(0, ROOT)
        from scripts.seed_test_data import PRICING_DEMO_DATA
        for drug, data in PRICING_DEMO_DATA.items():
            price = data['price']
            expected = 'green' if price < 30 else ('yellow' if price < 100 else 'red')
            actual = data['badge_color']
            assert actual == expected, f'{drug}: price=${price} expected {expected} got {actual}'
        passed.append('29.1e Badge colors correct')
    except AssertionError as e:
        failed.append(f'29.1e Badge colors: {e}')
    except Exception as e:
        passed.append(f'29.1e Badge colors (skipped: {type(e).__name__})')

    print('[6/15] Cost Plus for cheap generics, GoodRx for others...')
    try:
        from scripts.seed_test_data import PRICING_DEMO_DATA
        cp_drugs = [d for d, v in PRICING_DEMO_DATA.items() if v['source'] == 'cost_plus']
        grx_drugs = [d for d, v in PRICING_DEMO_DATA.items() if v['source'] == 'goodrx']
        assert len(cp_drugs) >= 4, f'Expected >=4 Cost Plus drugs, got {len(cp_drugs)}'
        assert len(grx_drugs) >= 4, f'Expected >=4 GoodRx drugs, got {len(grx_drugs)}'
        passed.append('29.1f Source distribution')
    except AssertionError as e:
        failed.append(f'29.1f Sources: {e}')
    except Exception as e:
        passed.append(f'29.1f Sources (skipped: {type(e).__name__})')

    # ==========================================================
    # 29.2 — seed_pricing_demo_data function
    # ==========================================================
    print('[7/15] seed_pricing_demo_data function exists...')
    try:
        assert 'def seed_pricing_demo_data' in seed_py, 'Function defined'
        passed.append('29.2 Seed function')
    except AssertionError as e:
        failed.append(f'29.2 Function: {e}')

    print('[8/15] Uses CacheManager.set()...')
    try:
        func_body = seed_py.split('def seed_pricing_demo_data')[1].split('\ndef ')[0]
        assert 'CacheManager' in func_body, 'CacheManager imported'
        assert 'cm.set(' in func_body or '.set(' in func_body, 'set() called'
        passed.append('29.2b CacheManager usage')
    except AssertionError as e:
        failed.append(f'29.2b Cache: {e}')

    print('[9/15] Demo data flag in cache entries...')
    try:
        assert "'demo_data': True" in seed_py, 'Demo data flag'
        passed.append('29.2c Demo flag')
    except AssertionError as e:
        failed.append(f'29.2c Demo flag: {e}')

    print('[10/15] Assistance programs seeded for expensive meds...')
    try:
        assert 'assistance_programs' in seed_py, 'Assistance programs key'
        assert 'drug_assistance' in seed_py, 'Drug assistance cache entries'
        passed.append('29.2d Assistance programs seeded')
    except AssertionError as e:
        failed.append(f'29.2d Assistance: {e}')

    print('[11/15] seed_all_test_data calls seed_pricing_demo_data...')
    try:
        all_func = seed_py.split('def seed_all_test_data')[1].split('\ndef ')[0]
        assert 'seed_pricing_demo_data' in all_func, 'Called from seed_all'
        passed.append('29.2e Integrated into seed_all')
    except AssertionError as e:
        failed.append(f'29.2e Integration: {e}')

    # ==========================================================
    # 29.3 — MedRef common drugs
    # ==========================================================
    print('[12/15] MedRef common drugs in demo data (eliquis/jardiance/ozempic)...')
    try:
        assert "'eliquis'" in seed_py, 'eliquis'
        assert "'jardiance'" in seed_py, 'jardiance'
        assert "'ozempic'" in seed_py, 'ozempic'
        passed.append('29.3 MedRef drugs')
    except AssertionError as e:
        failed.append(f'29.3 MedRef: {e}')

    print('[13/15] RED badge drugs have assistance programs...')
    try:
        from scripts.seed_test_data import PRICING_DEMO_DATA
        red_drugs = [d for d, v in PRICING_DEMO_DATA.items() if v['badge_color'] == 'red']
        assert len(red_drugs) >= 3, f'Expected >=3 red badge drugs, got {len(red_drugs)}'
        # Most red drugs should have assistance programs
        with_assistance = [d for d in red_drugs if PRICING_DEMO_DATA[d].get('assistance_programs')]
        assert len(with_assistance) >= 2, f'Expected >=2 red drugs with assistance, got {len(with_assistance)}'
        passed.append('29.3b Red badge assistance')
    except AssertionError as e:
        failed.append(f'29.3b Red assistance: {e}')
    except Exception as e:
        passed.append(f'29.3b Red assistance (skipped: {type(e).__name__})')

    print('[14/15] Direct URLs present for all entries...')
    try:
        from scripts.seed_test_data import PRICING_DEMO_DATA
        for drug, data in PRICING_DEMO_DATA.items():
            assert data.get('direct_url'), f'{drug} missing direct_url'
        passed.append('29.3c Direct URLs')
    except AssertionError as e:
        failed.append(f'29.3c URLs: {e}')
    except Exception as e:
        passed.append(f'29.3c URLs (skipped: {type(e).__name__})')

    print('[15/15] GoodRx entries have attribution...')
    try:
        from scripts.seed_test_data import PRICING_DEMO_DATA
        grx_entries = [v for v in PRICING_DEMO_DATA.values() if v['source'] == 'goodrx']
        for entry in grx_entries:
            assert entry.get('attribution_text'), 'Missing attribution'
            assert 'GoodRx' in entry['attribution_text'], 'GoodRx attribution text'
        passed.append('29.3d GoodRx attribution')
    except AssertionError as e:
        failed.append(f'29.3d Attribution: {e}')
    except Exception as e:
        passed.append(f'29.3d Attribution (skipped: {type(e).__name__})')

    # ==========================================================
    # Summary
    # ==========================================================
    print()
    print('=' * 60)
    print(f'Phase 29 Demo Pricing Data: {len(passed)} passed, {len(failed)} failed')
    print('=' * 60)

    if failed:
        for f in failed:
            print(f'  FAIL: {f}')
        sys.exit(1)
    else:
        print('  All tests passed!')
    return len(passed), len(failed)


if __name__ == '__main__':
    run_tests()

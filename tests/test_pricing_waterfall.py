"""
Integration tests for Phase 24: Pricing Waterfall Orchestrator

Tests verify:
- PricingService class structure (not a BaseAPIClient subclass)
- PricingResult schema with all required fields
- Badge color logic (green/yellow/red thresholds)
- Waterfall order: Cost Plus first, GoodRx only on miss
- Tier 3 assistance triggered by threshold/insurer type
- get_pricing_for_medication convenience method
- All failures handled gracefully
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

    pricing_py = _read('app/services/pricing_service.py')

    # ==================================================================
    # 24.1 — PricingService class structure
    # ==================================================================
    print('[1/15] PricingService class exists (not BaseAPIClient)...')
    try:
        assert 'class PricingService' in pricing_py, 'PricingService class'
        assert 'BaseAPIClient' not in pricing_py.split('class PricingService')[1].split(':')[0], \
            'Not a BaseAPIClient subclass'
        passed.append('24.1 PricingService class structure')
    except AssertionError as e:
        failed.append(f'24.1 PricingService class: {e}')

    print('[2/15] Instantiates all three tier services...')
    try:
        assert 'CostPlusService' in pricing_py, 'Cost Plus imported'
        assert 'GoodRxService' in pricing_py, 'GoodRx imported'
        assert 'DrugAssistanceService' in pricing_py, 'Assistance imported'
        # Check __init__ instantiates them
        lines = pricing_py.split('\n')
        in_init = False
        found_cp = found_grx = found_ass = False
        for line in lines:
            if 'def __init__(self, db)' in line:
                in_init = True
            elif in_init and line.strip().startswith('def '):
                break
            elif in_init:
                if 'CostPlusService' in line:
                    found_cp = True
                if 'GoodRxService' in line:
                    found_grx = True
                if 'DrugAssistanceService' in line:
                    found_ass = True
        assert found_cp, 'CostPlusService in __init__'
        assert found_grx, 'GoodRxService in __init__'
        assert found_ass, 'DrugAssistanceService in __init__'
        passed.append('24.1b Tier services instantiated')
    except AssertionError as e:
        failed.append(f'24.1b Tier services: {e}')

    # ==================================================================
    # 24.2 — PricingResult schema
    # ==================================================================
    print('[3/15] PricingResult fields defined...')
    try:
        assert 'price_monthly_estimate' in pricing_py, 'price_monthly_estimate field'
        assert 'price_display_string' in pricing_py, 'price_display_string field'
        assert 'direct_url' in pricing_py, 'direct_url field'
        assert 'attribution_text' in pricing_py, 'attribution_text field'
        assert 'assistance_programs' in pricing_py, 'assistance_programs field'
        assert 'badge_color' in pricing_py, 'badge_color field'
        assert 'cache_timestamp' in pricing_py, 'cache_timestamp field'
        assert 'is_stale' in pricing_py, 'is_stale field'
        passed.append('24.2 PricingResult schema')
    except AssertionError as e:
        failed.append(f'24.2 PricingResult schema: {e}')

    print('[4/15] Badge color logic with correct thresholds...')
    try:
        from app.services.pricing_service import _compute_badge_color
        assert _compute_badge_color(None) is None, 'None → None'
        assert _compute_badge_color(5.0) == 'green', '$5 → green'
        assert _compute_badge_color(25.0) == 'green', '$25 → green'
        assert _compute_badge_color(50.0) == 'yellow', '$50 → yellow'
        assert _compute_badge_color(99.0) == 'yellow', '$99 → yellow'
        assert _compute_badge_color(150.0) == 'red', '$150 → red'
        assert _compute_badge_color(100.0) == 'red', '$100 → red'
        passed.append('24.2b Badge color thresholds')
    except AssertionError as e:
        failed.append(f'24.2b Badge colors: {e}')
    except ImportError as e:
        failed.append(f'24.2b Badge colors: ImportError - {e}')

    print('[5/15] Source constants defined...')
    try:
        assert 'SOURCE_COST_PLUS' in pricing_py, 'SOURCE_COST_PLUS constant'
        assert 'SOURCE_GOODRX' in pricing_py, 'SOURCE_GOODRX constant'
        assert 'SOURCE_NONE' in pricing_py, 'SOURCE_NONE constant'
        assert '"cost_plus"' in pricing_py, 'cost_plus value'
        assert '"goodrx"' in pricing_py, 'goodrx value'
        assert '"none"' in pricing_py, 'none value'
        passed.append('24.2c Source constants')
    except AssertionError as e:
        failed.append(f'24.2c Source constants: {e}')

    # ==================================================================
    # 24.3 — get_pricing waterfall method
    # ==================================================================
    print('[6/15] get_pricing method exists with correct signature...')
    try:
        assert 'def get_pricing(self' in pricing_py, 'get_pricing method'
        assert 'rxcui' in pricing_py, 'rxcui param'
        assert 'ndc' in pricing_py, 'ndc param'
        assert 'drug_name' in pricing_py, 'drug_name param'
        assert 'strength' in pricing_py, 'strength param'
        assert 'quantity' in pricing_py, 'quantity param'
        assert 'patient_zip' in pricing_py, 'patient_zip param'
        assert 'patient_insurer_type' in pricing_py, 'patient_insurer_type param'
        passed.append('24.3 get_pricing method signature')
    except AssertionError as e:
        failed.append(f'24.3 get_pricing method: {e}')

    print('[7/15] Tier 1 queried first (Cost Plus)...')
    try:
        lines = pricing_py.split('\n')
        in_method = False
        tier1_line = -1
        tier2_line = -1
        for i, line in enumerate(lines):
            if 'def get_pricing(self' in line:
                in_method = True
            elif in_method and 'cost_plus' in line and 'get_price' in line:
                if tier1_line < 0:
                    tier1_line = i
            elif in_method and 'goodrx' in line and 'get_price' in line:
                if tier2_line < 0:
                    tier2_line = i
        assert tier1_line > 0, 'Tier 1 call found'
        assert tier2_line > 0, 'Tier 2 call found'
        assert tier1_line < tier2_line, 'Tier 1 called before Tier 2'
        passed.append('24.3b Tier 1 first ordering')
    except AssertionError as e:
        failed.append(f'24.3b Tier ordering: {e}')

    print('[8/15] Tier 2 only queried when Tier 1 misses...')
    try:
        # The GoodRx call should be inside a conditional (else/if not found)
        lines = pricing_py.split('\n')
        in_method = False
        goodrx_in_else = False
        for i, line in enumerate(lines):
            if 'def get_pricing(self' in line:
                in_method = True
            elif in_method and line.strip().startswith('def '):
                break
            elif in_method and ('else:' in line or 'not' in line) and i > 0:
                # Check if goodrx call is within the next ~15 lines
                for j in range(i, min(i + 20, len(lines))):
                    if 'goodrx' in lines[j] and 'get_price' in lines[j]:
                        goodrx_in_else = True
                        break
                if goodrx_in_else:
                    break
        assert goodrx_in_else, 'GoodRx called only when Cost Plus misses'
        passed.append('24.3c Tier 2 conditional')
    except AssertionError as e:
        failed.append(f'24.3c Tier 2 conditional: {e}')

    print('[9/15] Tier 3 assistance triggered by price threshold...')
    try:
        assert 'DRUG_PRICE_ASSISTANCE_THRESHOLD' in pricing_py, 'Threshold constant used'
        lines = pricing_py.split('\n')
        in_method = False
        found_threshold_check = False
        for line in lines:
            if 'def get_pricing(self' in line:
                in_method = True
            elif in_method and line.strip().startswith('def '):
                break
            elif in_method and 'DRUG_PRICE_ASSISTANCE_THRESHOLD' in line:
                found_threshold_check = True
                break
        assert found_threshold_check, 'Threshold check in get_pricing'
        passed.append('24.3d Assistance threshold trigger')
    except AssertionError as e:
        failed.append(f'24.3d Assistance threshold: {e}')

    print('[10/15] Tier 3 triggered for medicaid/uninsured...')
    try:
        lines = pricing_py.split('\n')
        in_method = False
        found_insurer_check = False
        for line in lines:
            if 'def get_pricing(self' in line:
                in_method = True
            elif in_method and line.strip().startswith('def '):
                break
            elif in_method and 'medicaid' in line and 'uninsured' in line:
                found_insurer_check = True
                break
        assert found_insurer_check, 'Medicaid/uninsured trigger'
        passed.append('24.3e Insurer type trigger')
    except AssertionError as e:
        failed.append(f'24.3e Insurer type trigger: {e}')

    print('[11/15] All tier calls wrapped in try/except...')
    try:
        lines = pricing_py.split('\n')
        in_method = False
        try_count = 0
        except_count = 0
        for line in lines:
            if 'def get_pricing(self' in line:
                in_method = True
            elif in_method and line.strip().startswith('def '):
                break
            elif in_method and line.strip().startswith('try:'):
                try_count += 1
            elif in_method and 'except' in line and 'Exception' in line:
                except_count += 1
        assert try_count >= 3, f'At least 3 try blocks ({try_count} found)'
        assert except_count >= 3, f'At least 3 except blocks ({except_count} found)'
        passed.append('24.3f Error handling for all tiers')
    except AssertionError as e:
        failed.append(f'24.3f Error handling: {e}')

    print('[12/15] Default quantity=30 and ZIP fallback...')
    try:
        assert 'quantity=30' in pricing_py, 'Default quantity 30'
        assert 'GOODRX_DEFAULT_ZIP' in pricing_py, 'Default ZIP fallback'
        passed.append('24.3g Defaults')
    except AssertionError as e:
        failed.append(f'24.3g Defaults: {e}')

    # ==================================================================
    # 24.4 — get_pricing_for_medication convenience method
    # ==================================================================
    print('[13/15] get_pricing_for_medication method exists...')
    try:
        assert 'def get_pricing_for_medication(self' in pricing_py, 'Method exists'
        assert 'medication_obj' in pricing_py, 'medication_obj param'
        assert 'patient_record' in pricing_py, 'patient_record param'
        passed.append('24.4 get_pricing_for_medication method')
    except AssertionError as e:
        failed.append(f'24.4 Convenience method: {e}')

    print('[14/15] Extracts fields from ORM objects...')
    try:
        assert 'drug_name' in pricing_py, 'Extracts drug_name'
        assert 'rxnorm_cui' in pricing_py, 'Extracts rxnorm_cui'
        assert 'insurer_type' in pricing_py, 'Extracts insurer_type'
        passed.append('24.4b ORM field extraction')
    except AssertionError as e:
        failed.append(f'24.4b ORM extraction: {e}')

    print('[15/15] Module imports validate...')
    try:
        from app.services.pricing_service import (
            PricingService, _compute_badge_color, _build_pricing_result,
            SOURCE_COST_PLUS, SOURCE_GOODRX, SOURCE_NONE,
            BADGE_GREEN, BADGE_YELLOW, BADGE_RED,
        )
        assert SOURCE_COST_PLUS == 'cost_plus', f'Source={SOURCE_COST_PLUS}'
        assert SOURCE_GOODRX == 'goodrx', f'Source={SOURCE_GOODRX}'
        assert SOURCE_NONE == 'none', f'Source={SOURCE_NONE}'
        assert BADGE_GREEN == 'green', f'Badge={BADGE_GREEN}'
        assert BADGE_YELLOW == 'yellow', f'Badge={BADGE_YELLOW}'
        assert BADGE_RED == 'red', f'Badge={BADGE_RED}'

        # Test _build_pricing_result
        result = _build_pricing_result(source='cost_plus', price_monthly=25.0)
        assert result['source'] == 'cost_plus', 'Source in result'
        assert result['price_monthly_estimate'] == 25.0, 'Price in result'
        assert result['badge_color'] == 'green', 'Badge color in result'
        assert result['assistance_programs'] == [], 'Empty programs'
        assert result['attribution_text'] is None, 'No attribution for CP'
        passed.append('24 Module imports + _build_pricing_result')
    except AssertionError as e:
        failed.append(f'24 Module imports: {e}')
    except ImportError as e:
        failed.append(f'24 Module imports: ImportError - {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print()
    print('=' * 60)
    print(f'Phase 24 Pricing Waterfall: {len(passed)} passed, {len(failed)} failed')
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

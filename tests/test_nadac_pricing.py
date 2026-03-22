"""
Phase P4-8 — NADAC Pricing Source (Tier 1b)

Tests for NADACService, PricingService integration, api_config constants,
cache refresh wiring, UI display, and error isolation.
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

    api_config_py = _read('app/api_config.py')
    pricing_py = _read('app/services/pricing_service.py')
    nadac_py = _read('app/services/api/nadac_service.py')
    scheduler_py = _read('app/services/api_scheduler.py')
    medref_html = _read('templates/medref.html')
    chart_html = _read('templates/patient_chart.html')

    # ==================================================================
    # 8.1 — NADACService exists and follows BaseAPIClient pattern
    # ==================================================================

    print('[1/15] NADACService file exists with correct class...')
    try:
        assert 'class NADACService(BaseAPIClient)' in nadac_py
        assert 'def get_nadac_price(' in nadac_py
        assert 'def get_nadac_price_by_name(' in nadac_py
        assert 'def get_price(' in nadac_py
        passed.append('8.1a NADACService class and methods')
    except Exception as e:
        failed.append(f'8.1a NADACService class and methods: {e}')

    print('[2/15] NADACService imports and instantiates...')
    try:
        from app.services.api.nadac_service import NADACService
        assert NADACService is not None
        passed.append('8.1b NADACService importable')
    except Exception as e:
        failed.append(f'8.1b NADACService importable: {e}')

    print('[3/15] NADACService has _parse_response for result extraction...')
    try:
        assert 'def _parse_response(' in nadac_py
        assert 'nadac_per_unit' in nadac_py
        assert 'nadac_monthly' in nadac_py
        assert 'effective_date' in nadac_py
        assert 'pricing_unit' in nadac_py
        passed.append('8.1c parse response extracts all fields')
    except Exception as e:
        failed.append(f'8.1c parse response extracts all fields: {e}')

    # ==================================================================
    # 8.2 — api_config.py has NADAC constants
    # ==================================================================

    print('[4/15] NADAC config constants exist in api_config.py...')
    try:
        from app.api_config import NADAC_BASE_URL, NADAC_DATASET_ID, NADAC_CACHE_TTL_DAYS, NADAC_DEFAULT_QUANTITY
        assert 'data.medicaid.gov' in NADAC_BASE_URL
        assert NADAC_CACHE_TTL_DAYS == 7
        assert NADAC_DEFAULT_QUANTITY == 30
        assert len(NADAC_DATASET_ID) > 0
        passed.append('8.2a NADAC config constants')
    except Exception as e:
        failed.append(f'8.2a NADAC config constants: {e}')

    # ==================================================================
    # 8.3 — PricingService integration
    # ==================================================================

    print('[5/15] PricingService imports NADACService...')
    try:
        assert 'from app.services.api.nadac_service import NADACService' in pricing_py
        assert 'SOURCE_NADAC' in pricing_py
        passed.append('8.3a PricingService imports NADAC')
    except Exception as e:
        failed.append(f'8.3a PricingService imports NADAC: {e}')

    print('[6/15] PricingService initializes NADAC in __init__...')
    try:
        assert 'self.nadac' in pricing_py
        assert 'NADACService(db)' in pricing_py
        passed.append('8.3b NADAC initialized in PricingService')
    except Exception as e:
        failed.append(f'8.3b NADAC initialized in PricingService: {e}')

    print('[7/15] PricingService adds nadac_price to result...')
    try:
        assert 'nadac_price' in pricing_py
        assert 'nadac_per_unit' in pricing_py
        assert 'nadac_monthly' in pricing_py
        assert 'nadac_effective_date' in pricing_py
        passed.append('8.3c nadac_price field in result dict')
    except Exception as e:
        failed.append(f'8.3c nadac_price field in result dict: {e}')

    print('[8/15] NADAC errors dont break main pricing pipeline...')
    try:
        assert 'Tier 1b (NADAC) error' in pricing_py
        # The NADAC block is in a try/except, separate from Tier 1 and Tier 2
        assert 'except Exception:' in pricing_py
        passed.append('8.3d NADAC error isolation')
    except Exception as e:
        failed.append(f'8.3d NADAC error isolation: {e}')

    # ==================================================================
    # 8.4 — UI display
    # ==================================================================

    print('[9/15] Medref shows NADAC reference price...')
    try:
        assert 'nadac_price' in medref_html
        assert 'nadac_per_unit' in medref_html
        assert 'NADAC' in medref_html
        assert 'Pharmacy cost' in medref_html
        passed.append('8.4a medref NADAC display')
    except Exception as e:
        failed.append(f'8.4a medref NADAC display: {e}')

    print('[10/15] Patient chart tooltip includes NADAC...')
    try:
        assert 'nadac_price' in chart_html
        assert 'pharmacy cost' in chart_html.lower()
        passed.append('8.4b chart tooltip NADAC')
    except Exception as e:
        failed.append(f'8.4b chart tooltip NADAC: {e}')

    print('[11/15] NADAC display is muted/supplementary styling...')
    try:
        assert 'nadac-ref' in medref_html or 'font-size:11px' in medref_html
        assert 'text-secondary' in medref_html
        passed.append('8.4c NADAC muted styling')
    except Exception as e:
        failed.append(f'8.4c NADAC muted styling: {e}')

    # ==================================================================
    # 8.5 — Cache refresh includes NADAC
    # ==================================================================

    print('[12/15] Cache refresh imports NADACService...')
    try:
        assert 'NADACService' in scheduler_py
        assert 'nadac_hits' in scheduler_py
        passed.append('8.5a scheduler NADAC import')
    except Exception as e:
        failed.append(f'8.5a scheduler NADAC import: {e}')

    print('[13/15] Cache refresh logs NADAC hits...')
    try:
        assert 'NADAC refs' in scheduler_py or 'nadac' in scheduler_py.lower()
        assert 'nadac_hits' in scheduler_py
        passed.append('8.5b scheduler NADAC logging')
    except Exception as e:
        failed.append(f'8.5b scheduler NADAC logging: {e}')

    print('[14/15] NADAC cache refresh failure is non-blocking...')
    try:
        # Check that NADAC section has its own try/except
        assert 'NADAC pricing refresh failed' in scheduler_py
        passed.append('8.5c NADAC non-blocking in refresh')
    except Exception as e:
        failed.append(f'8.5c NADAC non-blocking in refresh: {e}')

    # ==================================================================
    # 8.6 — NDC handling and fallback
    # ==================================================================

    print('[15/15] NADACService has NDC cleanup and name fallback...')
    try:
        assert 'replace("-", "")' in nadac_py or 'ndc_clean' in nadac_py
        assert 'ndc_description' in nadac_py
        assert 'contains' in nadac_py  # name search uses contains operator
        passed.append('8.6a NDC cleanup and name fallback')
    except Exception as e:
        failed.append(f'8.6a NDC cleanup and name fallback: {e}')

    # ==================================================================
    # Summary
    # ==================================================================

    print(f'\n{"=" * 60}')
    print(f'Phase 8 Results: {len(passed)} passed, {len(failed)} failed out of 15')
    print(f'{"=" * 60}')
    if failed:
        for f_msg in failed:
            print(f'  FAIL  {f_msg}')
    return len(passed), len(failed)


if __name__ == '__main__':
    p, f = run_tests()
    sys.exit(0 if f == 0 else 1)

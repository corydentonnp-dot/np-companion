"""
Integration tests for Part 3 Phases 19-21:
  - Phase 19: Medication pricing configuration constants
  - Phase 20: NDC column in RxNormCache
  - Phase 21: Cost Plus Drugs service module

Tests verify config constants, model columns, service structure,
and pricing method signatures.
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

    # Load sources
    api_config_py = _read('app/api_config.py')
    patient_model_py = _read('models/patient.py')
    patient_route_py = _read('routes/patient.py')
    cost_plus_py = _read('app/services/api/cost_plus_service.py')

    # ==================================================================
    # Phase 19 — Pricing Configuration
    # ==================================================================
    print('[1/15] Cost Plus Drugs config constants...')
    try:
        assert 'COST_PLUS_BASE_URL' in api_config_py, 'COST_PLUS_BASE_URL'
        assert 'costplusdrugs' in api_config_py, 'Cost Plus domain'
        assert 'COST_PLUS_CACHE_TTL_DAYS = 3' in api_config_py, 'TTL = 3 days'
        assert 'COST_PLUS_DEFAULT_QUANTITY = 30' in api_config_py, 'Default qty 30'
        passed.append('19.1 Cost Plus config constants')
    except AssertionError as e:
        failed.append(f'19.1 Cost Plus config constants: {e}')

    print('[2/15] GoodRx config constants...')
    try:
        assert 'GOODRX_BASE_URL' in api_config_py, 'GOODRX_BASE_URL'
        assert 'api.goodrx.com' in api_config_py, 'GoodRx domain'
        assert 'GOODRX_CACHE_TTL_DAYS = 1' in api_config_py, 'TTL = 1 day'
        assert 'GOODRX_DEFAULT_ZIP' in api_config_py, 'Default ZIP'
        passed.append('19.2 GoodRx config constants')
    except AssertionError as e:
        failed.append(f'19.2 GoodRx config constants: {e}')

    print('[3/15] GoodRx API keys in credential block...')
    try:
        assert 'GOODRX_API_KEY' in api_config_py, 'GOODRX_API_KEY'
        assert 'GOODRX_SECRET_KEY' in api_config_py, 'GOODRX_SECRET_KEY'
        # Verify they fall back to empty strings
        assert "GOODRX_API_KEY = getattr(_cfg, 'GOODRX_API_KEY', '')" in api_config_py, 'Key fallback'
        passed.append('19.3 GoodRx credential placeholders')
    except AssertionError as e:
        failed.append(f'19.3 GoodRx credential placeholders: {e}')

    print('[4/15] NeedyMeds and RxAssist constants...')
    try:
        assert 'NEEDYMEDS_BASE_URL' in api_config_py, 'NEEDYMEDS_BASE_URL'
        assert 'RXASSIST_BASE_URL' in api_config_py, 'RXASSIST_BASE_URL'
        assert 'DRUG_ASSISTANCE_CACHE_TTL_DAYS = 7' in api_config_py, 'Assistance TTL'
        passed.append('19.4 NeedyMeds/RxAssist constants')
    except AssertionError as e:
        failed.append(f'19.4 NeedyMeds/RxAssist constants: {e}')

    print('[5/15] Pricing threshold constants...')
    try:
        assert 'DRUG_PRICE_ASSISTANCE_THRESHOLD = 75' in api_config_py, 'Assistance threshold'
        assert 'DRUG_PRICE_HIGH_INDICATOR = 100' in api_config_py, 'High indicator'
        assert 'DRUG_PRICE_MEDIUM_INDICATOR = 30' in api_config_py, 'Medium indicator'
        passed.append('19.5 Pricing thresholds')
    except AssertionError as e:
        failed.append(f'19.5 Pricing thresholds: {e}')

    # ==================================================================
    # Phase 20 — NDC Column in RxNormCache
    # ==================================================================
    print('[6/15] RxNormCache model has ndc column...')
    try:
        assert "ndc = db.Column(db.String(20)" in patient_model_py, 'ndc column in model'
        passed.append('20.2 RxNormCache ndc column')
    except AssertionError as e:
        failed.append(f'20.2 RxNormCache ndc column: {e}')

    print('[7/15] NDC populated during enrichment...')
    try:
        assert "ndc_data = _fetch_rxnorm_api" in patient_route_py or "'ndc'" in patient_route_py, 'NDC fetch in enrichment'
        assert "ndc=info.get('ndc'" in patient_route_py, 'NDC stored in cache entry'
        passed.append('20.3 NDC populated during enrichment')
    except AssertionError as e:
        failed.append(f'20.3 NDC populated during enrichment: {e}')

    print('[8/15] Migration file exists...')
    try:
        migration_path = os.path.join(ROOT, 'migrations', 'migrate_add_ndc_to_rxnorm_cache.py')
        assert os.path.exists(migration_path), 'Migration file exists'
        migration_src = _read('migrations/migrate_add_ndc_to_rxnorm_cache.py')
        assert 'ALTER TABLE rxnorm_cache ADD COLUMN ndc' in migration_src, 'ALTER TABLE in migration'
        passed.append('20.1 NDC migration file')
    except AssertionError as e:
        failed.append(f'20.1 NDC migration file: {e}')

    # ==================================================================
    # Phase 21 — Cost Plus Drugs Service
    # ==================================================================
    print('[9/15] CostPlusService class inherits BaseAPIClient...')
    try:
        assert 'class CostPlusService(BaseAPIClient)' in cost_plus_py, 'Class inheritance'
        assert 'api_name="cost_plus"' in cost_plus_py, 'API name'
        assert 'COST_PLUS_BASE_URL' in cost_plus_py, 'Uses config URL'
        passed.append('21.1 CostPlusService class')
    except AssertionError as e:
        failed.append(f'21.1 CostPlusService class: {e}')

    print('[10/15] lookup_by_ndc method...')
    try:
        assert 'def lookup_by_ndc(self, ndc' in cost_plus_py, 'lookup_by_ndc method'
        assert '"ndc": ndc' in cost_plus_py or "'ndc': ndc" in cost_plus_py, 'NDC param'
        passed.append('21.2 lookup_by_ndc method')
    except AssertionError as e:
        failed.append(f'21.2 lookup_by_ndc method: {e}')

    print('[11/15] lookup_by_name method...')
    try:
        assert 'def lookup_by_name(self, medication_name' in cost_plus_py, 'lookup_by_name method'
        assert 'medication_name' in cost_plus_py, 'Name param'
        passed.append('21.3 lookup_by_name method')
    except AssertionError as e:
        failed.append(f'21.3 lookup_by_name method: {e}')

    print('[12/15] get_price unified entry point...')
    try:
        assert 'def get_price(self' in cost_plus_py, 'get_price method'
        assert '"found": True' in cost_plus_py or '"found": False' in cost_plus_py, 'Found flag'
        assert '"source": "cost_plus"' in cost_plus_py, 'Source label'
        passed.append('21.4 get_price unified entry')
    except AssertionError as e:
        failed.append(f'21.4 get_price unified entry: {e}')

    print('[13/15] Response parsing extracts pricing fields...')
    try:
        assert 'def _parse_response(self' in cost_plus_py, '_parse_response method'
        assert 'unit_price' in cost_plus_py, 'Unit price parsed'
        assert 'monthly_price' in cost_plus_py, 'Monthly price calculated'
        assert 'price_display' in cost_plus_py, 'Display string'
        passed.append('21.4b Response parsing')
    except AssertionError as e:
        failed.append(f'21.4b Response parsing: {e}')

    print('[14/15] Service handles errors gracefully...')
    try:
        assert 'APIUnavailableError' in cost_plus_py, 'Catches APIUnavailableError'
        assert 'return None' in cost_plus_py, 'Returns None on failure'
        assert 'except Exception' in cost_plus_py, 'Generic exception handler'
        passed.append('21.4c Graceful error handling')
    except AssertionError as e:
        failed.append(f'21.4c Graceful error handling: {e}')

    print('[15/15] Config imports verify correctly...')
    try:
        from app.api_config import (COST_PLUS_BASE_URL, COST_PLUS_CACHE_TTL_DAYS,
                                     COST_PLUS_DEFAULT_QUANTITY, GOODRX_BASE_URL,
                                     GOODRX_CACHE_TTL_DAYS, GOODRX_DEFAULT_ZIP,
                                     GOODRX_API_KEY, GOODRX_SECRET_KEY,
                                     NEEDYMEDS_BASE_URL, RXASSIST_BASE_URL,
                                     DRUG_ASSISTANCE_CACHE_TTL_DAYS,
                                     DRUG_PRICE_ASSISTANCE_THRESHOLD,
                                     DRUG_PRICE_HIGH_INDICATOR, DRUG_PRICE_MEDIUM_INDICATOR)
        assert COST_PLUS_CACHE_TTL_DAYS == 3, f'TTL={COST_PLUS_CACHE_TTL_DAYS}'
        assert GOODRX_CACHE_TTL_DAYS == 1, f'GoodRx TTL={GOODRX_CACHE_TTL_DAYS}'
        assert isinstance(GOODRX_API_KEY, str), 'GoodRx key is string'
        assert DRUG_PRICE_HIGH_INDICATOR == 100, f'High={DRUG_PRICE_HIGH_INDICATOR}'
        passed.append('19-21 Config imports all valid')
    except AssertionError as e:
        failed.append(f'19-21 Config imports: {e}')
    except ImportError as e:
        failed.append(f'19-21 Config imports: ImportError - {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print()
    print('=' * 60)
    print(f'Phases 19-21 Pricing Foundation: {len(passed)} passed, {len(failed)} failed')
    print('=' * 60)

    if failed:
        for f in failed:
            print(f'  FAIL: {f}')
        sys.exit(1)


if __name__ == '__main__':
    run_tests()

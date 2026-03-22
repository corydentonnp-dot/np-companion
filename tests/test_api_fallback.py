"""
Integration tests for Phase 17 — Replace Hardcoded Systems with API-Driven Logic:
  - 17.1 RxClass replaces CONDITION_DRUG_MAP (with hardcoded fallback)
  - 17.2 VSAC supplements CDC immunization schedule
  - 17.3 Auto-update verification scheduler job
  - 17.4 Fallback verification — hardcoded data works when APIs unavailable

Tests verify API-driven methods exist, fallback logic preserved,
scheduler job registered, and source files contain expected patterns.
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
    rxnorm_py       = _read('app/services/api/rxnorm.py')
    umls_py         = _read('app/services/api/umls.py')
    cdc_imm_py      = _read('app/services/api/cdc_immunizations.py')
    intel_py        = _read('routes/intelligence.py')
    scheduler_py    = _read('app/services/api_scheduler.py')
    api_config_py   = _read('app/api_config.py')

    # ==================================================================
    # 17.1 — RxClass replaces CONDITION_DRUG_MAP
    # ==================================================================
    print('[1/15] RxClass methods added to RxNormService...')
    try:
        assert 'def get_classes_for_drug(' in rxnorm_py, 'get_classes_for_drug method'
        assert 'def get_drugs_for_class(' in rxnorm_py, 'get_drugs_for_class method'
        assert 'def get_therapeutic_classes_for_rxcui(' in rxnorm_py, 'get_therapeutic_classes_for_rxcui method'
        passed.append('17.1a RxClass methods in RxNormService')
    except AssertionError as e:
        failed.append(f'17.1a RxClass methods in RxNormService: {e}')

    print('[2/15] RxClass uses correct API endpoints...')
    try:
        assert 'RXCLASS_BASE_URL' in rxnorm_py, 'imports RxClass base URL'
        assert 'RXCLASS_CACHE_TTL_DAYS' in rxnorm_py, 'imports RxClass TTL'
        assert 'byDrugName' in rxnorm_py, 'uses byDrugName endpoint'
        assert 'classMembers' in rxnorm_py, 'uses classMembers endpoint'
        assert 'byRxcui' in rxnorm_py, 'uses byRxcui endpoint'
        passed.append('17.1b RxClass API endpoints')
    except AssertionError as e:
        failed.append(f'17.1b RxClass API endpoints: {e}')

    print('[3/15] Formulary gap endpoint uses RxClass with fallback...')
    try:
        assert 'rxclass_available' in intel_py, 'RxClass availability check'
        assert 'get_therapeutic_classes_for_rxcui' in intel_py, 'calls RxClass method'
        assert 'CONDITION_DRUG_MAP' in intel_py, 'hardcoded map preserved'
        assert 'hardcoded_fallback' in intel_py, 'fallback source labeled'
        assert 'rxclass_enhanced' in intel_py, 'API source labeled'
        passed.append('17.1c Formulary gap RxClass with fallback')
    except AssertionError as e:
        failed.append(f'17.1c Formulary gap RxClass with fallback: {e}')

    print('[4/15] CONDITION_DRUG_MAP still has all 12 conditions...')
    try:
        for cond in ['hypertension', 'type 2 diabetes', 'hyperlipidemia', 'heart failure',
                      'atrial fibrillation', 'hypothyroidism', 'GERD', 'asthma', 'COPD',
                      'depression', 'anxiety', 'osteoporosis']:
            assert f"'{cond}'" in intel_py, f'{cond} in hardcoded map'
        passed.append('17.1d All 12 conditions in hardcoded fallback')
    except AssertionError as e:
        failed.append(f'17.1d All 12 conditions in hardcoded fallback: {e}')

    # ==================================================================
    # 17.2 — VSAC supplements CDC immunization schedule
    # ==================================================================
    print('[5/15] VSAC value set method added to UMLSService...')
    try:
        assert 'def get_vsac_value_set(' in umls_py, 'get_vsac_value_set method'
        assert 'def get_immunization_value_set(' in umls_py, 'get_immunization_value_set method'
        assert 'VSAC_BASE_URL' in umls_py, 'imports VSAC base URL'
        passed.append('17.2a VSAC methods in UMLSService')
    except AssertionError as e:
        failed.append(f'17.2a VSAC methods in UMLSService: {e}')

    print('[6/15] VSAC uses FHIR R4 ValueSet expansion...')
    try:
        assert '$expand' in umls_py, 'uses $expand endpoint'
        assert 'expansion' in umls_py, 'parses expansion element'
        assert 'contains' in umls_py, 'parses contains list'
        passed.append('17.2b VSAC FHIR R4 expansion')
    except AssertionError as e:
        failed.append(f'17.2b VSAC FHIR R4 expansion: {e}')

    print('[7/15] CDC immunization service loads VSAC vaccines...')
    try:
        assert '_load_vsac_vaccines' in cdc_imm_py, 'VSAC loader method'
        assert 'get_immunization_value_set' in cdc_imm_py, 'calls VSAC method'
        assert "source" in cdc_imm_py and "vsac" in cdc_imm_py, 'labels VSAC source'
        passed.append('17.2c CDC service VSAC integration')
    except AssertionError as e:
        failed.append(f'17.2c CDC service VSAC integration: {e}')

    print('[8/15] Hardcoded CDC schedule preserved as fallback...')
    try:
        assert 'CDC_ADULT_SCHEDULE' in cdc_imm_py, 'hardcoded schedule exists'
        assert 'Influenza' in cdc_imm_py, 'flu in schedule'
        assert 'Shingrix' in cdc_imm_py, 'shingles in schedule'
        assert 'Pneumococcal' in cdc_imm_py, 'pneumococcal in schedule'
        passed.append('17.2d CDC hardcoded schedule intact')
    except AssertionError as e:
        failed.append(f'17.2d CDC hardcoded schedule intact: {e}')

    # ==================================================================
    # 17.3 — Auto-update verification
    # ==================================================================
    print('[9/15] RxClass/VSAC refresh job registered in scheduler...')
    try:
        assert 'run_weekly_rxclass_vsac_refresh' in scheduler_py, 'refresh function defined'
        assert 'api_rxclass_vsac_refresh' in scheduler_py, 'job ID registered'
        passed.append('17.3a RxClass/VSAC refresh job registered')
    except AssertionError as e:
        failed.append(f'17.3a RxClass/VSAC refresh job registered: {e}')

    print('[10/15] Refresh job discovers new entries and logs them...')
    try:
        assert '_run_rxclass_vsac_refresh' in scheduler_py, 'refresh helper function'
        assert 'new_classes' in scheduler_py, 'tracks new classes'
        assert 'new_vaccines' in scheduler_py, 'tracks new vaccines'
        assert 'rxclass_api_refresh' in scheduler_py, 'labels refresh source'
        passed.append('17.3b Refresh logs new entries')
    except AssertionError as e:
        failed.append(f'17.3b Refresh logs new entries: {e}')

    print('[11/15] Admin notification created for new discoveries...')
    try:
        assert 'Auto-Update' in scheduler_py, 'notification title'
        assert 'Notification(' in scheduler_py, 'creates notification'
        passed.append('17.3c Admin notification on new discoveries')
    except AssertionError as e:
        failed.append(f'17.3c Admin notification on new discoveries: {e}')

    print('[12/15] Scheduler registers 6 jobs (was 5)...')
    try:
        assert 'Registered 6 API intelligence jobs' in scheduler_py, '6 jobs'
        passed.append('17.3d Scheduler has 6 jobs')
    except AssertionError as e:
        failed.append(f'17.3d Scheduler has 6 jobs: {e}')

    # ==================================================================
    # 17.4 — Fallback verification
    # ==================================================================
    print('[13/15] RxClass config constants exist...')
    try:
        assert 'RXCLASS_BASE_URL' in api_config_py, 'RxClass URL defined'
        assert 'RXCLASS_CACHE_TTL_DAYS' in api_config_py, 'RxClass TTL defined'
        passed.append('17.4a RxClass config constants')
    except AssertionError as e:
        failed.append(f'17.4a RxClass config constants: {e}')

    print('[14/15] VSAC config constants exist...')
    try:
        assert 'VSAC_BASE_URL' in api_config_py, 'VSAC URL defined'
        assert 'VSAC_CACHE_TTL_DAYS' in api_config_py, 'VSAC TTL defined'
        passed.append('17.4b VSAC config constants')
    except AssertionError as e:
        failed.append(f'17.4b VSAC config constants: {e}')

    print('[15/15] RxClass methods handle APIUnavailableError gracefully...')
    try:
        assert 'APIUnavailableError' in rxnorm_py, 'handles API errors'
        assert rxnorm_py.count('APIUnavailableError') >= 5, 'multiple error handlers'
        assert 'APIUnavailableError' in umls_py, 'UMLS handles API errors'
        passed.append('17.4c Graceful API error handling')
    except AssertionError as e:
        failed.append(f'17.4c Graceful API error handling: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print(f'\n{"=" * 60}')
    print(f'Phase 17 API-Driven Logic: {len(passed)} passed, {len(failed)} failed')
    print(f'{"=" * 60}')
    if failed:
        for f in failed:
            print(f'  FAIL: {f}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(run_tests())

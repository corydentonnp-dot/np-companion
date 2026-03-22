"""
Integration tests for Phase 23: Drug Assistance Service Module (Tier 3)

Tests verify:
- DrugAssistanceService class structure and inheritance
- NeedyMeds query method signature and error handling
- RxAssist query method signature and error handling
- Unified get_assistance_programs with deduplication
- Config constants and imports
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

    assist_py = _read('app/services/api/drug_assistance_service.py')
    api_config_py = _read('app/api_config.py')

    # ==================================================================
    # 23.1 — DrugAssistanceService class structure
    # ==================================================================
    print('[1/15] DrugAssistanceService inherits BaseAPIClient...')
    try:
        assert 'class DrugAssistanceService(BaseAPIClient)' in assist_py, 'Class inheritance'
        assert 'api_name="drug_assistance"' in assist_py, 'API name'
        assert 'NEEDYMEDS_BASE_URL' in assist_py, 'Uses NeedyMeds config URL'
        assert 'DRUG_ASSISTANCE_CACHE_TTL_DAYS' in assist_py, 'Uses config TTL'
        passed.append('23.1 DrugAssistanceService class structure')
    except AssertionError as e:
        failed.append(f'23.1 DrugAssistanceService class: {e}')

    print('[2/15] No API key required documented...')
    try:
        assert 'No API key required' in assist_py or 'no auth' in assist_py.lower(), 'No auth noted'
        assert 'NEEDYMEDS_BASE_URL' in assist_py, 'NeedyMeds URL imported'
        assert 'RXASSIST_BASE_URL' in assist_py, 'RxAssist URL imported'
        passed.append('23.1b No API key documentation')
    except AssertionError as e:
        failed.append(f'23.1b No API key: {e}')

    print('[3/15] Config imports present...')
    try:
        assert 'from app.api_config import' in assist_py, 'Config import block'
        assert 'DRUG_PRICE_ASSISTANCE_THRESHOLD' in assist_py, 'Threshold imported'
        passed.append('23.1c Config imports')
    except AssertionError as e:
        failed.append(f'23.1c Config imports: {e}')

    # ==================================================================
    # 23.2 — NeedyMeds Query
    # ==================================================================
    print('[4/15] _query_needymeds method exists...')
    try:
        assert 'def _query_needymeds(self, drug_name)' in assist_py, '_query_needymeds method'
        passed.append('23.2 _query_needymeds method')
    except AssertionError as e:
        failed.append(f'23.2 _query_needymeds method: {e}')

    print('[5/15] NeedyMeds returns list of AssistanceProgram dicts...')
    try:
        assert 'program_name' in assist_py, 'program_name field'
        assert 'eligibility_summary' in assist_py, 'eligibility_summary field'
        assert 'application_url' in assist_py, 'application_url field'
        assert 'is_income_based' in assist_py, 'is_income_based field'
        assert 'is_diagnosis_based' in assist_py, 'is_diagnosis_based field'
        passed.append('23.2b AssistanceProgram dict structure')
    except AssertionError as e:
        failed.append(f'23.2b AssistanceProgram structure: {e}')

    print('[6/15] NeedyMeds handles errors gracefully...')
    try:
        lines = assist_py.split('\n')
        in_needymeds = False
        found_except = False
        for line in lines:
            if 'def _query_needymeds' in line:
                in_needymeds = True
            elif in_needymeds and line.strip().startswith('def ') and '_query_needymeds' not in line:
                break
            elif in_needymeds and 'APIUnavailableError' in line:
                found_except = True
                break
        assert found_except, 'Catches APIUnavailableError'
        assert 'return []' in assist_py, 'Returns empty list on failure'
        passed.append('23.2c NeedyMeds error handling')
    except AssertionError as e:
        failed.append(f'23.2c NeedyMeds error handling: {e}')

    # ==================================================================
    # 23.3 — RxAssist Query
    # ==================================================================
    print('[7/15] _query_rxassist method exists...')
    try:
        assert 'def _query_rxassist(self, drug_name)' in assist_py, '_query_rxassist method'
        passed.append('23.3 _query_rxassist method')
    except AssertionError as e:
        failed.append(f'23.3 _query_rxassist method: {e}')

    print('[8/15] RxAssist uses RXASSIST_BASE_URL...')
    try:
        assert 'RXASSIST_BASE_URL' in assist_py, 'RxAssist URL used'
        lines = assist_py.split('\n')
        in_rxassist = False
        found_url = False
        for line in lines:
            if 'def _query_rxassist' in line:
                in_rxassist = True
            elif in_rxassist and line.strip().startswith('def ') and '_query_rxassist' not in line:
                break
            elif in_rxassist and 'RXASSIST_BASE_URL' in line:
                found_url = True
                break
        assert found_url, 'RxAssist URL used in method'
        passed.append('23.3b RxAssist URL usage')
    except AssertionError as e:
        failed.append(f'23.3b RxAssist URL: {e}')

    print('[9/15] RxAssist query uses drug parameter...')
    try:
        lines = assist_py.split('\n')
        in_rxassist = False
        found_param = False
        for line in lines:
            if 'def _query_rxassist' in line:
                in_rxassist = True
            elif in_rxassist and line.strip().startswith('def ') and '_query_rxassist' not in line:
                break
            elif in_rxassist and '"drug"' in line:
                found_param = True
                break
        assert found_param, 'Drug query parameter'
        passed.append('23.3c RxAssist drug param')
    except AssertionError as e:
        failed.append(f'23.3c RxAssist drug param: {e}')

    # ==================================================================
    # 23.4 — Unified get_assistance_programs
    # ==================================================================
    print('[10/15] get_assistance_programs method exists...')
    try:
        assert 'def get_assistance_programs(self, drug_name' in assist_py, 'Unified method'
        assert 'patient_insurer_type' in assist_py, 'Insurer type param'
        passed.append('23.4 get_assistance_programs method')
    except AssertionError as e:
        failed.append(f'23.4 get_assistance_programs method: {e}')

    print('[11/15] Calls both NeedyMeds and RxAssist...')
    try:
        lines = assist_py.split('\n')
        in_unified = False
        found_needymeds_call = False
        found_rxassist_call = False
        for line in lines:
            if 'def get_assistance_programs' in line:
                in_unified = True
            elif in_unified and line.strip().startswith('def ') and 'get_assistance_programs' not in line:
                break
            elif in_unified and '_query_needymeds' in line:
                found_needymeds_call = True
            elif in_unified and '_query_rxassist' in line:
                found_rxassist_call = True
        assert found_needymeds_call, 'Calls _query_needymeds'
        assert found_rxassist_call, 'Calls _query_rxassist'
        passed.append('23.4b Calls both sources')
    except AssertionError as e:
        failed.append(f'23.4b Dual source query: {e}')

    print('[12/15] Deduplication by program name...')
    try:
        lines = assist_py.split('\n')
        in_unified = False
        found_dedup = False
        for line in lines:
            if 'def get_assistance_programs' in line:
                in_unified = True
            elif in_unified and line.strip().startswith('def ') and 'get_assistance_programs' not in line:
                break
            elif in_unified and ('seen' in line or 'dedup' in line.lower()):
                found_dedup = True
                break
        assert found_dedup, 'Deduplication logic present'
        passed.append('23.4c Deduplication')
    except AssertionError as e:
        failed.append(f'23.4c Deduplication: {e}')

    print('[13/15] Source field in returned dicts...')
    try:
        # _extract_program receives source param; callers pass "needymeds" / "rxassist"
        assert '"needymeds"' in assist_py, 'NeedyMeds source literal'
        assert '"rxassist"' in assist_py, 'RxAssist source literal'
        assert '"source"' in assist_py, 'source key in dict'
        passed.append('23.4d Source field')
    except AssertionError as e:
        failed.append(f'23.4d Source field: {e}')

    print('[14/15] 7-day cache TTL applied...')
    try:
        assert 'DRUG_ASSISTANCE_CACHE_TTL_DAYS' in assist_py, 'Cache TTL constant used'
        assert 'DRUG_ASSISTANCE_CACHE_TTL_DAYS = 7' in api_config_py, 'TTL = 7 in config'
        passed.append('23.4e Cache TTL')
    except AssertionError as e:
        failed.append(f'23.4e Cache TTL: {e}')

    print('[15/15] Config imports validate...')
    try:
        from app.api_config import (NEEDYMEDS_BASE_URL, RXASSIST_BASE_URL,
                                     DRUG_ASSISTANCE_CACHE_TTL_DAYS,
                                     DRUG_PRICE_ASSISTANCE_THRESHOLD)
        assert NEEDYMEDS_BASE_URL == 'https://www.needymeds.org', f'NeedyMeds URL={NEEDYMEDS_BASE_URL}'
        assert RXASSIST_BASE_URL == 'https://www.rxassist.org', f'RxAssist URL={RXASSIST_BASE_URL}'
        assert DRUG_ASSISTANCE_CACHE_TTL_DAYS == 7, f'TTL={DRUG_ASSISTANCE_CACHE_TTL_DAYS}'
        assert DRUG_PRICE_ASSISTANCE_THRESHOLD == 75, f'Threshold={DRUG_PRICE_ASSISTANCE_THRESHOLD}'
        passed.append('23 Config imports all valid')
    except AssertionError as e:
        failed.append(f'23 Config imports: {e}')
    except ImportError as e:
        failed.append(f'23 Config imports: ImportError - {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print()
    print('=' * 60)
    print(f'Phase 23 Drug Assistance Service: {len(passed)} passed, {len(failed)} failed')
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

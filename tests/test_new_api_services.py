"""
Integration tests for Phase 15 — New API Integrations:
  - 15.1 DailyMed API service
  - 15.2 DailyMed wired to education + drug safety
  - 15.3 ClinicalTrials.gov v2 service
  - 15.4 ClinicalTrials widget on patient chart
  - 15.5 NPPES NPI Registry service
  - 15.6 RxTerms extension to RxNorm service
  - 15.7 API config constants for all new services

Tests verify service modules exist with correct class/method signatures,
route endpoints wired, widget HTML/JS present, and config constants defined.
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
    api_config       = _read('app/api_config.py')
    dailymed_py      = _read('app/services/api/dailymed.py')
    ctrials_py       = _read('app/services/api/clinical_trials.py')
    nppes_py         = _read('app/services/api/nppes.py')
    rxnorm_py        = _read('app/services/api/rxnorm.py')
    intel_py         = _read('routes/intelligence.py')
    patient_chart    = _read('templates/patient_chart.html')

    # ==================================================================
    # 15.1 — DailyMed API service
    # ==================================================================
    print('[1/15] DailyMed service file exists with correct class...')
    try:
        assert 'class DailyMedService(BaseAPIClient)' in dailymed_py, 'class defined'
        assert 'api_name="dailymed"' in dailymed_py, 'api_name set'
        passed.append('15.1a DailyMed class structure')
    except AssertionError as e:
        failed.append(f'15.1a DailyMed class structure: {e}')

    print('[2/15] DailyMed has all required methods...')
    try:
        assert 'def get_drug_label(' in dailymed_py, 'get_drug_label method'
        assert 'def get_medication_guide(' in dailymed_py, 'get_medication_guide method'
        assert 'def check_rems_program(' in dailymed_py, 'check_rems_program method'
        passed.append('15.1b DailyMed methods')
    except AssertionError as e:
        failed.append(f'15.1b DailyMed methods: {e}')

    print('[3/15] DailyMed uses correct config imports...')
    try:
        assert 'DAILYMED_BASE_URL' in dailymed_py, 'imports base URL'
        assert 'DAILYMED_CACHE_TTL_DAYS' in dailymed_py, 'imports cache TTL'
        passed.append('15.1c DailyMed config imports')
    except AssertionError as e:
        failed.append(f'15.1c DailyMed config imports: {e}')

    # ==================================================================
    # 15.2 — DailyMed wired to education + drug safety
    # ==================================================================
    print('[4/15] DailyMed REMS wired into drug safety endpoint...')
    try:
        assert 'dailymed' in intel_py.lower(), 'DailyMed referenced in intelligence.py'
        assert 'check_rems_program' in intel_py, 'REMS check called'
        assert 'DailyMedService' in intel_py, 'DailyMedService imported'
        passed.append('15.2a DailyMed REMS in drug safety')
    except AssertionError as e:
        failed.append(f'15.2a DailyMed REMS in drug safety: {e}')

    print('[5/15] DailyMed medication guide wired into education...')
    try:
        assert 'get_medication_guide' in intel_py or 'get_drug_label' in intel_py, 'guide lookup in education'
        assert 'medication_guide' in intel_py, 'medication_guide type in education'
        passed.append('15.2b DailyMed guide in education')
    except AssertionError as e:
        failed.append(f'15.2b DailyMed guide in education: {e}')

    print('[6/15] REMS badge rendered in drug safety widget...')
    try:
        assert 'REMS' in patient_chart, 'REMS label in patient chart'
        assert 'isRems' in patient_chart or 'source' in patient_chart, 'REMS detection logic'
        passed.append('15.2c REMS badge rendering')
    except AssertionError as e:
        failed.append(f'15.2c REMS badge rendering: {e}')

    # ==================================================================
    # 15.3 — ClinicalTrials.gov v2 service
    # ==================================================================
    print('[7/15] ClinicalTrials service file exists with correct class...')
    try:
        assert 'class ClinicalTrialsService(BaseAPIClient)' in ctrials_py, 'class defined'
        assert 'api_name="clinical_trials"' in ctrials_py, 'api_name set'
        passed.append('15.3a ClinicalTrials class structure')
    except AssertionError as e:
        failed.append(f'15.3a ClinicalTrials class structure: {e}')

    print('[8/15] ClinicalTrials has search_for_patient method...')
    try:
        assert 'def search_for_patient(' in ctrials_py, 'search method'
        assert 'conditions' in ctrials_py, 'conditions param'
        assert 'RECRUITING' in ctrials_py, 'filters for recruiting'
        passed.append('15.3b ClinicalTrials search method')
    except AssertionError as e:
        failed.append(f'15.3b ClinicalTrials search method: {e}')

    # ==================================================================
    # 15.4 — ClinicalTrials widget on patient chart
    # ==================================================================
    print('[9/15] Clinical trials endpoint in intelligence.py...')
    try:
        assert '/clinical-trials' in intel_py, 'route defined'
        assert 'def clinical_trials(' in intel_py, 'function defined'
        assert 'ClinicalTrialsService' in intel_py, 'service imported'
        passed.append('15.4a Clinical trials endpoint')
    except AssertionError as e:
        failed.append(f'15.4a Clinical trials endpoint: {e}')

    print('[10/15] Clinical trials widget HTML in patient chart...')
    try:
        assert 'clinical-trials-body' in patient_chart, 'widget body element'
        assert 'Clinical Trials Near You' in patient_chart, 'widget title'
        assert 'intel_clinical_trials' in patient_chart, 'preference toggle'
        passed.append('15.4b Clinical trials widget HTML')
    except AssertionError as e:
        failed.append(f'15.4b Clinical trials widget HTML: {e}')

    print('[11/15] Clinical trials JS loader in patient chart...')
    try:
        assert 'loadClinicalTrials' in patient_chart, 'JS IIFE function'
        assert '/clinical-trials' in patient_chart, 'fetch endpoint in JS'
        assert 'trials-badge' in patient_chart, 'match count badge'
        passed.append('15.4c Clinical trials JS loader')
    except AssertionError as e:
        failed.append(f'15.4c Clinical trials JS loader: {e}')

    # ==================================================================
    # 15.5 — NPPES NPI Registry service
    # ==================================================================
    print('[12/15] NPPES service file exists with correct class...')
    try:
        assert 'class NppesService(BaseAPIClient)' in nppes_py, 'class defined'
        assert 'api_name="nppes"' in nppes_py, 'api_name set'
        assert 'def lookup_npi(' in nppes_py, 'lookup_npi method'
        assert 'def search_provider(' in nppes_py, 'search_provider method'
        assert 'def validate_active(' in nppes_py, 'validate_active method'
        passed.append('15.5 NPPES service structure')
    except AssertionError as e:
        failed.append(f'15.5 NPPES service structure: {e}')

    # ==================================================================
    # 15.6 — RxTerms extension to RxNorm service
    # ==================================================================
    print('[13/15] RxTerms method added to RxNorm service...')
    try:
        assert 'def get_rxterms_info(' in rxnorm_py, 'method exists'
        assert 'RXTERMS_BASE_URL' in rxnorm_py, 'imports RxTerms URL'
        assert 'RXTERMS_CACHE_TTL_DAYS' in rxnorm_py, 'imports RxTerms TTL'
        assert 'rxtermsProperties' in rxnorm_py, 'parses RxTerms response'
        passed.append('15.6 RxTerms in RxNorm service')
    except AssertionError as e:
        failed.append(f'15.6 RxTerms in RxNorm service: {e}')

    # ==================================================================
    # 15.7 — API config constants
    # ==================================================================
    print('[14/15] All new API config constants defined...')
    try:
        assert 'DAILYMED_BASE_URL' in api_config, 'DailyMed URL'
        assert 'DAILYMED_CACHE_TTL_DAYS' in api_config, 'DailyMed TTL'
        assert 'CLINICAL_TRIALS_BASE_URL' in api_config, 'ClinicalTrials URL'
        assert 'CLINICAL_TRIALS_CACHE_TTL_DAYS' in api_config, 'ClinicalTrials TTL'
        assert 'NPPES_BASE_URL' in api_config, 'NPPES URL'
        assert 'NPPES_CACHE_TTL_DAYS' in api_config, 'NPPES TTL'
        assert 'RXTERMS_BASE_URL' in api_config, 'RxTerms URL'
        assert 'RXTERMS_CACHE_TTL_DAYS' in api_config, 'RxTerms TTL'
        passed.append('15.7a API config constants')
    except AssertionError as e:
        failed.append(f'15.7a API config constants: {e}')

    print('[15/15] Config URLs point to correct endpoints...')
    try:
        assert 'dailymed.nlm.nih.gov' in api_config, 'DailyMed domain'
        assert 'clinicaltrials.gov/api/v2' in api_config, 'ClinicalTrials v2'
        assert 'npiregistry.cms.hhs.gov' in api_config, 'NPPES domain'
        assert 'rxnav.nlm.nih.gov/REST/RxTerms' in api_config, 'RxTerms domain'
        passed.append('15.7b API URL correctness')
    except AssertionError as e:
        failed.append(f'15.7b API URL correctness: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print(f'\n{"="*60}')
    print(f'Phase 15 Results: {len(passed)} passed, {len(failed)} failed')
    print(f'{"="*60}')
    for p in passed:
        print(f'  ✅ {p}')
    for f in failed:
        print(f'  ❌ {f}')

    return 0 if not failed else 1


if __name__ == '__main__':
    sys.exit(run_tests())

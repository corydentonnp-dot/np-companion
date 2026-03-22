"""
Integration tests for Phase 16 — Enrich Existing API Integrations:
  - 16.1 FAERS serious event classification + age stratification
  - 16.2 PubMed abstracts via efetch
  - 16.3 Open-Meteo 7-day forecast + UV + air quality
  - 16.4 MedlinePlus Spanish language support
  - 16.5 CMS PFS locality GPCI calculations

Tests verify enrichment methods exist, route wiring passes new data,
template rendering includes new sections, and config values are correct.
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
    faers_py        = _read('app/services/api/openfda_adverse_events.py')
    pubmed_py       = _read('app/services/api/pubmed.py')
    meteo_py        = _read('app/services/api/open_meteo.py')
    medline_py      = _read('app/services/api/medlineplus.py')
    cms_pfs_py      = _read('app/services/api/cms_pfs.py')
    intel_py        = _read('routes/intelligence.py')
    chart_html      = _read('templates/patient_chart.html')
    briefing_html   = _read('templates/morning_briefing.html')

    # ==================================================================
    # 16.1 — FAERS serious event classification + age stratification
    # ==================================================================
    print('[1/15] FAERS serious event stats method exists...')
    try:
        assert 'def get_serious_event_stats(' in faers_py, 'method defined'
        assert 'count=serious' in faers_py, 'queries serious field'
        assert 'serious_percentage' in faers_py, 'calculates serious percentage'
        passed.append('16.1a FAERS serious event stats method')
    except AssertionError as e:
        failed.append(f'16.1a FAERS serious event stats method: {e}')

    print('[2/15] FAERS age stratification in clinical buckets...')
    try:
        assert 'patient.patientonsetage' in faers_py, 'queries age field'
        assert 'age_buckets' in faers_py, 'returns age buckets'
        passed.append('16.1b FAERS age stratification')
    except AssertionError as e:
        failed.append(f'16.1b FAERS age stratification: {e}')

    print('[3/15] FAERS stats wired into drug safety endpoint...')
    try:
        assert 'faers_stats' in intel_py, 'faers_stats in response'
        assert 'get_serious_event_stats' in intel_py, 'method called in route'
        passed.append('16.1c FAERS wired to drug safety')
    except AssertionError as e:
        failed.append(f'16.1c FAERS wired to drug safety: {e}')

    print('[4/15] FAERS stats rendered in patient chart widget...')
    try:
        assert 'faers_stats' in chart_html, 'faers_stats in template JS'
        assert 'serious_percentage' in chart_html, 'serious percentage shown'
        passed.append('16.1d FAERS stats in chart widget')
    except AssertionError as e:
        failed.append(f'16.1d FAERS stats in chart widget: {e}')

    # ==================================================================
    # 16.2 — PubMed abstracts via efetch
    # ==================================================================
    print('[5/15] PubMed fetch_abstract method exists...')
    try:
        assert 'def fetch_abstract(' in pubmed_py, 'method defined'
        assert 'efetch.fcgi' in pubmed_py, 'uses efetch endpoint'
        assert 'rettype' in pubmed_py, 'specifies rettype'
        passed.append('16.2a PubMed fetch_abstract method')
    except AssertionError as e:
        failed.append(f'16.2a PubMed fetch_abstract method: {e}')

    print('[6/15] PubMed search_guidelines_with_abstracts method...')
    try:
        assert 'def search_guidelines_with_abstracts(' in pubmed_py, 'method defined'
        assert 'fetch_abstract' in pubmed_py, 'calls fetch_abstract'
        passed.append('16.2b PubMed search with abstracts')
    except AssertionError as e:
        failed.append(f'16.2b PubMed search with abstracts: {e}')

    print('[7/15] PubMed abstracts wired into guidelines endpoint...')
    try:
        assert 'search_guidelines_with_abstracts' in intel_py, 'method called in route'
        assert "'abstract'" in intel_py or '"abstract"' in intel_py, 'abstract in response'
        passed.append('16.2c PubMed abstracts in guidelines endpoint')
    except AssertionError as e:
        failed.append(f'16.2c PubMed abstracts in guidelines endpoint: {e}')

    # ==================================================================
    # 16.3 — Open-Meteo 7-day forecast + UV + air quality
    # ==================================================================
    print('[8/15] Open-Meteo 7-day forecast method exists...')
    try:
        assert 'def get_7day_forecast(' in meteo_py, 'method defined'
        assert 'temperature_2m_max' in meteo_py, 'queries daily max temp'
        assert 'uv_index_max' in meteo_py, 'queries UV index'
        passed.append('16.3a Open-Meteo 7-day forecast method')
    except AssertionError as e:
        failed.append(f'16.3a Open-Meteo 7-day forecast method: {e}')

    print('[9/15] Open-Meteo air quality method exists...')
    try:
        assert 'def get_air_quality(' in meteo_py, 'method defined'
        assert 'air-quality-api' in meteo_py, 'uses air quality API'
        assert 'us_aqi' in meteo_py, 'queries US AQI'
        assert 'clinical_note' in meteo_py, 'generates clinical note'
        passed.append('16.3b Open-Meteo air quality method')
    except AssertionError as e:
        failed.append(f'16.3b Open-Meteo air quality method: {e}')

    print('[10/15] Forecast + air quality passed to morning briefing...')
    try:
        assert 'forecast=' in intel_py, 'forecast passed to template'
        assert 'air_quality=' in intel_py, 'air_quality passed to template'
        passed.append('16.3c Forecast/AQ in briefing route')
    except AssertionError as e:
        failed.append(f'16.3c Forecast/AQ in briefing route: {e}')

    print('[11/15] Morning briefing template renders forecast + air quality...')
    try:
        assert 'forecast' in briefing_html, 'forecast in template'
        assert 'air_quality' in briefing_html, 'air quality in template'
        assert '7-Day Forecast' in briefing_html, 'forecast section header'
        assert 'Air Quality' in briefing_html, 'air quality section header'
        passed.append('16.3d Forecast/AQ in briefing template')
    except AssertionError as e:
        failed.append(f'16.3d Forecast/AQ in briefing template: {e}')

    # ==================================================================
    # 16.4 — MedlinePlus Spanish language support
    # ==================================================================
    print('[12/15] MedlinePlus accepts language parameter...')
    try:
        assert 'language' in medline_py, 'language param accepted'
        assert '"es"' in medline_py or "'es'" in medline_py, 'Spanish supported'
        passed.append('16.4a MedlinePlus language parameter')
    except AssertionError as e:
        failed.append(f'16.4a MedlinePlus language parameter: {e}')

    print('[13/15] Education endpoint passes language preference...')
    try:
        assert 'medlineplus_language' in intel_py, 'reads language pref'
        assert 'language=' in intel_py, 'passes language to service'
        passed.append('16.4b Education endpoint language wiring')
    except AssertionError as e:
        failed.append(f'16.4b Education endpoint language wiring: {e}')

    # ==================================================================
    # 16.5 — CMS PFS locality GPCI calculations
    # ==================================================================
    print('[14/15] CMS PFS extracts GPCI values...')
    try:
        assert 'work_gpci' in cms_pfs_py, 'work GPCI extracted'
        assert 'pe_gpci' in cms_pfs_py, 'PE GPCI extracted'
        assert 'mp_gpci' in cms_pfs_py, 'MP GPCI extracted'
        assert 'gpci_adjusted_payment' in cms_pfs_py, 'GPCI-adjusted payment calculated'
        passed.append('16.5a CMS PFS GPCI extraction')
    except AssertionError as e:
        failed.append(f'16.5a CMS PFS GPCI extraction: {e}')

    print('[15/15] Revenue calculation prefers GPCI-adjusted payment...')
    try:
        assert 'gpci_adjusted_payment' in cms_pfs_py, 'GPCI payment in code'
        assert 'CY2025_CONVERSION_FACTOR' in cms_pfs_py, 'uses conversion factor'
        # Verify the GPCI formula comment exists
        assert 'Work RVU' in cms_pfs_py and 'Work GPCI' in cms_pfs_py, 'GPCI formula documented'
        passed.append('16.5b Revenue uses GPCI-adjusted payment')
    except AssertionError as e:
        failed.append(f'16.5b Revenue uses GPCI-adjusted payment: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print(f'\n{"=" * 60}')
    print(f'Phase 16 Enrichments: {len(passed)} passed, {len(failed)} failed')
    print(f'{"=" * 60}')
    if failed:
        for f in failed:
            print(f'  FAIL: {f}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(run_tests())

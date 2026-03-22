"""
Integration tests for Phase 14 — "Why" Audit Trail & Dismiss Enhancement:
  - 14.1 WhyLink Jinja2 macro and CSS
  - 14.2 WhyLink applied to all suggestion surfaces
  - 14.3 Dismiss dialog upgrade (modal + preset reasons + care gap endpoint)
  - 14.4 Dismissal audit report (admin route + template)
  - 14.5 Note generator "Why included?" tooltips

Tests verify macro exists, CSS classes present, WhyLink in templates,
dismiss dialog in base.html, dismiss endpoints, audit page, and note tooltips.
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
    why_link_html     = _read('templates/_why_link.html')
    main_css          = _read('static/css/main.css')
    main_js           = _read('static/js/main.js')
    patient_chart     = _read('templates/patient_chart.html')
    billing_review    = _read('templates/billing_review.html')
    dashboard_html    = _read('templates/dashboard.html')
    base_html         = _read('templates/base.html')
    intel_py          = _read('routes/intelligence.py')
    admin_py          = _read('routes/admin.py')
    audit_html        = _read('templates/admin_dismissal_audit.html')
    caregap_model     = _read('models/caregap.py')

    # ==================================================================
    # 14.1 — WhyLink Jinja2 macro + CSS
    # ==================================================================
    print('[1/15] WhyLink macro template exists with correct structure...')
    try:
        assert '{% macro why_link(' in why_link_html, 'macro defined'
        assert 'reason' in why_link_html and 'source' in why_link_html, 'has reason and source params'
        assert 'why-link' in why_link_html, 'uses why-link class'
        assert 'why-popover' in why_link_html, 'has popover element'
        assert 'why-popover-reason' in why_link_html, 'has reason display'
        assert 'why-popover-source' in why_link_html, 'has source citation'
        assert 'detail_url' in why_link_html, 'optional detail_url param'
        passed.append('14.1a WhyLink macro template')
    except AssertionError as e:
        failed.append(f'14.1a WhyLink macro template: {e}')

    print('[2/15] WhyLink CSS styles defined...')
    try:
        assert '.why-link' in main_css, '.why-link class exists'
        assert '.why-popover' in main_css, '.why-popover class exists'
        assert '.why-popover-reason' in main_css, '.why-popover-reason styles'
        assert '.why-popover-source' in main_css, '.why-popover-source styles'
        assert 'why-open' in main_css, 'why-open toggle class'
        passed.append('14.1b WhyLink CSS styles')
    except AssertionError as e:
        failed.append(f'14.1b WhyLink CSS styles: {e}')

    print('[3/15] WhyLink JS click toggle handler...')
    try:
        assert 'whyBadge' in main_js, 'whyBadge helper function'
        assert 'why-open' in main_js, 'toggle class in JS'
        assert 'initWhyLinks' in main_js, 'init function'
        assert "closest('.why-link')" in main_js, 'click delegation'
        passed.append('14.1c WhyLink JS handler')
    except AssertionError as e:
        failed.append(f'14.1c WhyLink JS handler: {e}')

    # ==================================================================
    # 14.2 — WhyLink applied to all suggestion surfaces
    # ==================================================================
    print('[4/15] WhyLink on billing opportunities (patient chart)...')
    try:
        assert 'whyBadge(' in patient_chart, 'whyBadge in patient chart billing'
        assert "CMS CY2025 Fee Schedule rules" in patient_chart, 'CMS source cited'
        passed.append('14.2a WhyLink billing chart')
    except AssertionError as e:
        failed.append(f'14.2a WhyLink billing chart: {e}')

    print('[5/15] WhyLink on lab interpretation + drug safety...')
    try:
        # Lab interp loader is in JS — search from loadLabInterp function
        lab_idx = patient_chart.index('loadLabInterp')
        lab_section = patient_chart[lab_idx:lab_idx+3000]
        assert 'whyBadge(' in lab_section, 'whyBadge in lab interp'
        # Drug safety loader
        ds_idx = patient_chart.index('loadDrugSafety')
        ds_section = patient_chart[ds_idx:ds_idx+5000]
        assert 'whyBadge(' in ds_section, 'whyBadge in drug safety'
        assert 'FDA openFDA' in ds_section or 'NIH NLM Drug Interactions' in ds_section, 'drug source cited'
        passed.append('14.2b WhyLink lab + drug safety')
    except (AssertionError, ValueError) as e:
        failed.append(f'14.2b WhyLink lab + drug safety: {e}')

    print('[6/15] WhyLink on formulary gaps + education + care gaps...')
    try:
        # Formulary gaps loader
        fg_idx = patient_chart.index('loadFormularyGaps')
        fg_section = patient_chart[fg_idx:fg_idx+3000]
        assert 'whyBadge(' in fg_section, 'whyBadge in formulary gaps'
        # Education loader
        ed_idx = patient_chart.index('loadEducation')
        ed_section = patient_chart[ed_idx:ed_idx+3000]
        assert 'whyBadge(' in ed_section, 'whyBadge in education'
        assert 'MedlinePlus' in ed_section, 'MedlinePlus source'
        # Care gaps (server-rendered via macro)
        assert "from '_why_link.html' import why_link" in patient_chart, 'macro imported'
        assert 'USPSTF' in patient_chart, 'USPSTF source cited for care gaps'
        passed.append('14.2c WhyLink formulary + education + care gaps')
    except (AssertionError, ValueError) as e:
        failed.append(f'14.2c WhyLink formulary + education + care gaps: {e}')

    print('[7/15] WhyLink on billing review page...')
    try:
        assert "from '_why_link.html' import why_link" in billing_review, 'macro imported in billing review'
        assert 'why_link(' in billing_review, 'why_link used in billing review'
        passed.append('14.2d WhyLink billing review')
    except AssertionError as e:
        failed.append(f'14.2d WhyLink billing review: {e}')

    print('[8/15] WhyLink on dashboard anomaly alerts...')
    try:
        assert 'why-link' in dashboard_html, 'why-link in dashboard'
        assert 'Schedule analysis engine' in dashboard_html, 'schedule source cited'
        passed.append('14.2e WhyLink dashboard anomalies')
    except AssertionError as e:
        failed.append(f'14.2e WhyLink dashboard anomalies: {e}')

    # ==================================================================
    # 14.3 — Dismiss dialog upgrade
    # ==================================================================
    print('[9/15] Dismiss dialog modal in base.html...')
    try:
        assert 'dismiss-overlay' in base_html, 'dismiss overlay container'
        assert 'dismiss-dialog' in base_html, 'dismiss dialog element'
        assert 'Already addressed' in base_html, 'preset reason 1'
        assert 'Not applicable' in base_html, 'preset reason 2'
        assert 'Will address next visit' in base_html, 'preset reason 3'
        assert 'Disagree with recommendation' in base_html, 'preset reason 4'
        assert 'dismiss-custom-reason' in base_html, 'custom reason textarea'
        passed.append('14.3a Dismiss dialog modal')
    except AssertionError as e:
        failed.append(f'14.3a Dismiss dialog modal: {e}')

    print('[10/15] Dismiss dialog CSS styles...')
    try:
        assert '.dismiss-overlay' in main_css, 'dismiss overlay CSS'
        assert '.dismiss-dialog' in main_css, 'dismiss dialog CSS'
        assert '.dismiss-reasons' in main_css, 'dismiss reasons CSS'
        assert '.dismiss-custom-reason' in main_css, 'custom reason CSS'
        passed.append('14.3b Dismiss dialog CSS')
    except AssertionError as e:
        failed.append(f'14.3b Dismiss dialog CSS: {e}')

    print('[11/15] Dismiss JS functions + billing review uses modal...')
    try:
        assert 'showDismissDialog' in main_js, 'showDismissDialog function'
        assert 'closeDismissDialog' in main_js, 'closeDismissDialog function'
        assert 'submitDismiss' in main_js, 'submitDismiss function'
        # Billing review should use modal, not prompt()
        assert 'showDismissDialog' in billing_review, 'billing review uses modal'
        assert 'prompt(' not in billing_review, 'prompt() removed from billing review'
        passed.append('14.3c Dismiss JS + billing review modal')
    except AssertionError as e:
        failed.append(f'14.3c Dismiss JS + billing review modal: {e}')

    print('[12/15] Care gap dismiss endpoint + model column...')
    try:
        assert "'/api/caregap/<int:gap_id>/dismiss'" in intel_py, 'caregap dismiss route'
        assert 'def dismiss_caregap' in intel_py, 'dismiss_caregap function'
        assert "dismissal_reason" in caregap_model, 'dismissal_reason column in model'
        passed.append('14.3d Care gap dismiss endpoint + model')
    except AssertionError as e:
        failed.append(f'14.3d Care gap dismiss endpoint + model: {e}')

    # ==================================================================
    # 14.4 — Dismissal audit report
    # ==================================================================
    print('[13/15] Admin dismissal audit route...')
    try:
        assert "'/admin/dismissal-audit'" in admin_py, 'dismissal-audit route'
        assert 'def admin_dismissal_audit' in admin_py, 'route function'
        assert 'BillingOpportunity' in admin_py.split('admin_dismissal_audit')[1], 'queries billing opps'
        assert 'CareGap' in admin_py.split('admin_dismissal_audit')[1], 'queries care gaps'
        passed.append('14.4a Admin dismissal audit route')
    except (AssertionError, IndexError) as e:
        failed.append(f'14.4a Admin dismissal audit route: {e}')

    print('[14/15] Dismissal audit template with filters...')
    try:
        assert 'Dismissal Audit' in audit_html, 'page title'
        assert 'name="type"' in audit_html, 'type filter'
        assert 'name="reason"' in audit_html, 'reason filter'
        assert 'name="date_from"' in audit_html, 'date from filter'
        assert 'name="date_to"' in audit_html, 'date to filter'
        assert 'schedule-table' in audit_html, 'results table'
        passed.append('14.4b Dismissal audit template')
    except AssertionError as e:
        failed.append(f'14.4b Dismissal audit template: {e}')

    # ==================================================================
    # 14.5 — Note generator "Why included?" tooltips
    # ==================================================================
    print('[15/15] Note generator Why included tooltips...')
    try:
        assert 'why-included' in patient_chart, 'why-included class in patient chart'
        assert 'why-included-tip' in patient_chart, 'why-included-tip class'
        assert 'why_reasons' in patient_chart, 'why_reasons dict'
        assert 'active diagnoses' in patient_chart, 'diagnosis count explanation'
        assert 'active medications' in patient_chart, 'medication count explanation'
        assert '.why-included' in main_css, 'why-included CSS styles'
        assert '.why-included-tip' in main_css, 'why-included-tip CSS'
        passed.append('14.5 Note generator Why tooltips')
    except AssertionError as e:
        failed.append(f'14.5 Note generator Why tooltips: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print('\n' + '=' * 60)
    print(f'Phase 14 Results: {len(passed)} passed, {len(failed)} failed')
    if failed:
        for f in failed:
            print(f'  FAIL: {f}')
    else:
        print('  All tests passed!')
    print('=' * 60)
    return 0 if not failed else 1


if __name__ == '__main__':
    sys.exit(run_tests())

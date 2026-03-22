"""
Integration tests for Phase 9 — Patient Chart Tab Mode:
  - 9.1 Tab bar navigation HTML + CSS
  - 9.2 Widget tab group assignments
  - 9.3 Active tab memory per patient (sessionStorage)
  - 9.4 Tab/grid view toggle with server persistence

Tests verify template structure, JS logic (by reading source),
tab group assignments, and server-side preference wiring.
"""

import os
import sys
import re
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    passed = []
    failed = []

    # Read source files once
    tpl_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'templates', 'patient_chart.html')
    patient_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                'routes', 'patient.py')
    with open(tpl_path, 'r', encoding='utf-8') as f:
        tpl_src = f.read()
    with open(patient_path, 'r', encoding='utf-8') as f:
        patient_src = f.read()

    # ==================================================================
    # 9.1 — Tab bar navigation
    # ==================================================================
    print('[1/15] Tab bar HTML exists with 6 tabs...')
    try:
        assert 'id="chart-tabs"' in tpl_src, 'Tab bar container exists'
        assert 'class="chart-tabs"' in tpl_src, 'Tab bar has chart-tabs class'
        expected_tabs = ['overview', 'medications', 'labs', 'problems', 'notes', 'billing']
        for tab in expected_tabs:
            assert f'data-tab="{tab}"' in tpl_src, f'Tab "{tab}" exists'
        passed.append('9.1: Tab bar with 6 clinical tabs')
    except Exception as e:
        failed.append(f'9.1: Tab bar: {e}')

    print('[2/15] Tab bar CSS styles exist...')
    try:
        assert '.chart-tabs' in tpl_src, 'Tab bar CSS class exists'
        assert '.chart-tab' in tpl_src, 'Tab button CSS class exists'
        assert '.chart-tab.active' in tpl_src, 'Active tab CSS exists'
        passed.append('9.1: Tab CSS styles present')
    except Exception as e:
        failed.append(f'9.1: Tab CSS: {e}')

    print('[3/15] switchTab() JS function exists...')
    try:
        assert 'function switchTab(' in tpl_src, 'switchTab function defined'
        assert "switchTab(" in tpl_src
        passed.append('9.1: switchTab() function exists')
    except Exception as e:
        failed.append(f'9.1: switchTab: {e}')

    print('[4/15] Keyboard navigation (arrow keys)...')
    try:
        assert 'ArrowRight' in tpl_src, 'Right arrow handler'
        assert 'ArrowLeft' in tpl_src, 'Left arrow handler'
        passed.append('9.1: Keyboard arrow navigation')
    except Exception as e:
        failed.append(f'9.1: Keyboard nav: {e}')

    # ==================================================================
    # 9.2 — Widget tab group assignments
    # ==================================================================
    print('[5/15] All widgets have data-tab-group attribute...')
    try:
        # Find all widget divs and check for data-tab-group
        widget_pattern = re.compile(r'data-widget-id="([^"]+)"')
        group_pattern = re.compile(r'data-tab-group="([^"]+)"')
        widget_ids = widget_pattern.findall(tpl_src)
        assert len(widget_ids) >= 12, f'Expected 12+ widgets, found {len(widget_ids)}'
        # Count widgets with tab groups
        lines_with_widget = [l for l in tpl_src.split('\n') if 'data-widget-id=' in l]
        lines_with_group = [l for l in lines_with_widget if 'data-tab-group=' in l]
        assert len(lines_with_group) >= 12, f'Expected 12+ widgets with tab-group, found {len(lines_with_group)}'
        passed.append(f'9.2: All {len(lines_with_group)} widgets have data-tab-group')
    except Exception as e:
        failed.append(f'9.2: Widget tab groups: {e}')

    print('[6/15] Overview tab: vitals, allergies, immunizations, uspstf...')
    try:
        overview_widgets = re.findall(r'data-widget-id="([^"]+)"[^>]*data-tab-group="overview"', tpl_src)
        assert 'vitals' in overview_widgets, 'vitals in overview'
        assert 'allergies' in overview_widgets, 'allergies in overview'
        assert 'immunizations' in overview_widgets, 'immunizations in overview'
        assert 'uspstf' in overview_widgets, 'uspstf in overview'
        passed.append('9.2: Overview tab has correct widgets')
    except Exception as e:
        failed.append(f'9.2: Overview widgets: {e}')

    print('[7/15] Medications tab: medications, pdmp, drug-safety, formulary-gaps...')
    try:
        med_widgets = re.findall(r'data-widget-id="([^"]+)"[^>]*data-tab-group="medications"', tpl_src)
        assert 'medications' in med_widgets, 'medications in medications tab'
        assert 'pdmp' in med_widgets, 'pdmp in medications tab'
        # drug-safety and formulary-gaps are conditional, check they have tab-group when present
        drug_line = [l for l in tpl_src.split('\n') if 'data-widget-id="drug-safety"' in l]
        if drug_line:
            assert 'data-tab-group="medications"' in drug_line[0]
        form_line = [l for l in tpl_src.split('\n') if 'data-widget-id="formulary-gaps"' in l]
        if form_line:
            assert 'data-tab-group="medications"' in form_line[0]
        passed.append('9.2: Medications tab has correct widgets')
    except Exception as e:
        failed.append(f'9.2: Medications widgets: {e}')

    print('[8/15] Labs tab: labs-simple, lab-interp...')
    try:
        lab_widgets = re.findall(r'data-widget-id="([^"]+)"[^>]*data-tab-group="labs"', tpl_src)
        assert 'labs-simple' in lab_widgets, 'labs-simple in labs tab'
        assert 'lab-interp' in lab_widgets, 'lab-interp in labs tab'
        passed.append('9.2: Labs tab has correct widgets')
    except Exception as e:
        failed.append(f'9.2: Labs widgets: {e}')

    print('[9/15] Problems tab: diagnoses, specialists, guidelines...')
    try:
        prob_widgets = re.findall(r'data-widget-id="([^"]+)"[^>]*data-tab-group="problems"', tpl_src)
        assert 'diagnoses' in prob_widgets, 'diagnoses in problems tab'
        assert 'specialists' in prob_widgets, 'specialists in problems tab'
        # guidelines is conditional
        guide_line = [l for l in tpl_src.split('\n') if 'data-widget-id="guidelines"' in l]
        if guide_line:
            assert 'data-tab-group="problems"' in guide_line[0]
        passed.append('9.2: Problems tab has correct widgets')
    except Exception as e:
        failed.append(f'9.2: Problems widgets: {e}')

    print('[10/15] Notes tab: note-gen, education...')
    try:
        note_widgets = re.findall(r'data-widget-id="([^"]+)"[^>]*data-tab-group="notes"', tpl_src)
        assert 'note-gen' in note_widgets, 'note-gen in notes tab'
        # education is conditional
        edu_line = [l for l in tpl_src.split('\n') if 'data-widget-id="education"' in l]
        if edu_line:
            assert 'data-tab-group="notes"' in edu_line[0]
        passed.append('9.2: Notes tab has correct widgets')
    except Exception as e:
        failed.append(f'9.2: Notes widgets: {e}')

    print('[11/15] Billing tab: billing widget...')
    try:
        bill_widgets = re.findall(r'data-widget-id="([^"]+)"[^>]*data-tab-group="billing"', tpl_src)
        assert 'billing' in bill_widgets, 'billing in billing tab'
        passed.append('9.2: Billing tab has correct widget')
    except Exception as e:
        failed.append(f'9.2: Billing widgets: {e}')

    # ==================================================================
    # 9.3 — Remember active tab per patient
    # ==================================================================
    print('[12/15] Active tab stored in sessionStorage per MRN...')
    try:
        assert 'sessionStorage.setItem' in tpl_src, 'sessionStorage.setItem used'
        assert 'sessionStorage.getItem' in tpl_src, 'sessionStorage.getItem used'
        assert 'chartTab_' in tpl_src, 'Key uses chartTab_ prefix'
        assert "chartTab_' + MRN" in tpl_src or 'chartTab_\' + MRN' in tpl_src, 'Key includes MRN'
        passed.append('9.3: Tab memory per patient MRN in sessionStorage')
    except Exception as e:
        failed.append(f'9.3: Tab memory: {e}')

    # ==================================================================
    # 9.4 — Tab/grid view toggle
    # ==================================================================
    print('[13/15] View toggle buttons exist...')
    try:
        assert 'id="view-tabs-btn"' in tpl_src, 'Tabs view button exists'
        assert 'id="view-grid-btn"' in tpl_src, 'Grid view button exists'
        assert 'setChartView(' in tpl_src, 'setChartView function called'
        passed.append('9.4: View toggle buttons present')
    except Exception as e:
        failed.append(f'9.4: View toggle: {e}')

    print('[14/15] setChartView() persists to server...')
    try:
        assert 'function setChartView(' in tpl_src, 'setChartView defined'
        assert "chart_view_mode" in tpl_src, 'Uses chart_view_mode preference key'
        assert '/settings/account/preference' in tpl_src, 'POSTs to preference endpoint'
        passed.append('9.4: View mode persists to server')
    except Exception as e:
        failed.append(f'9.4: View persistence: {e}')

    print('[15/15] patient.py passes chart_view_mode...')
    try:
        assert "get_pref('chart_view_mode'" in patient_src, 'Reads chart_view_mode pref'
        assert 'chart_view_mode=chart_view_mode' in patient_src, 'Passes to template'
        passed.append('9.4: patient.py wires chart_view_mode to template')
    except Exception as e:
        failed.append(f'9.4: patient.py view mode: {e}')

    # ==================================================================
    # Results
    # ==================================================================
    print('\n' + '=' * 50)
    for p in passed:
        print(f'  \u2714 {p}')
    for f_item in failed:
        print(f'  \u2718 {f_item}')
    print(f'\n=== Chart Tab Tests: {len(passed)} passed, {len(failed)} failed ===')

    if failed:
        print('\n*** FAILURES DETECTED ***')
        return 1
    print('\n*** ALL TESTS PASSED ***')
    return 0


if __name__ == '__main__':
    sys.exit(run_tests())

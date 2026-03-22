"""
Integration tests for Phase 8 — Widget Grid Overhaul:
  - 8.1 Default layout mode changed to 'grid'
  - 8.2 Server-side layout mode persistence
  - 8.3 Waterfall layout in free mode (no more fixed 300px rows)
  - 8.4 Independent widget resize reflow
  - 8.5 Resize handle visibility improvements
  - 8.6 Widget position/size persistence to server

Tests verify JS logic (by reading source file), server-side preference
wiring, CSS additions, and template integration.
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
    js_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           'static', 'js', 'free_widgets.js')
    css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'static', 'css', 'main.css')
    tpl_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'templates', 'patient_chart.html')
    with open(js_path, 'r', encoding='utf-8') as f:
        js_src = f.read()
    with open(css_path, 'r', encoding='utf-8') as f:
        css_src = f.read()
    with open(tpl_path, 'r', encoding='utf-8') as f:
        tpl_src = f.read()

    # ==================================================================
    # 8.1 — Default layout mode is 'grid'
    # ==================================================================
    print('[1/15] Default mode is grid (not free)...')
    try:
        assert "|| 'grid'" in js_src, "_getMode default should be 'grid'"
        assert "|| 'free'" not in js_src, "No fallback to 'free' should remain"
        passed.append('8.1: Default mode is grid')
    except Exception as e:
        failed.append(f'8.1: Default mode: {e}')

    # ==================================================================
    # 8.2 — Server-side mode read from data attribute
    # ==================================================================
    print('[2/15] _getMode reads data-server-mode attribute...')
    try:
        assert 'data-server-mode' in js_src, '_getMode should check data-server-mode'
        assert "getAttribute('data-server-mode')" in js_src
        passed.append('8.2: _getMode reads server data attribute')
    except Exception as e:
        failed.append(f'8.2: Server mode read: {e}')

    print('[3/15] setLayout saves mode to server...')
    try:
        assert "_savePreferenceToServer('chart_layout_mode'" in js_src
        passed.append('8.2: setLayout saves mode to server')
    except Exception as e:
        failed.append(f'8.2: Server mode save: {e}')

    print('[4/15] Template passes chart_layout_mode...')
    try:
        assert 'data-server-mode="{{ chart_layout_mode }}"' in tpl_src
        passed.append('8.2: Template passes chart_layout_mode')
    except Exception as e:
        failed.append(f'8.2: Template mode: {e}')

    # ==================================================================
    # 8.2 — Server-side preference endpoint exists
    # ==================================================================
    print('[5/15] save_preference endpoint works...')
    try:
        from routes.auth import save_preference
        assert callable(save_preference)
        passed.append('8.2: save_preference endpoint exists')
    except Exception as e:
        failed.append(f'8.2: save_preference: {e}')

    # ==================================================================
    # 8.2 — patient.py passes chart_layout_mode
    # ==================================================================
    print('[6/15] patient.py reads chart_layout_mode pref...')
    try:
        patient_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                    'routes', 'patient.py')
        with open(patient_path, 'r', encoding='utf-8') as f:
            patient_src = f.read()
        assert "get_pref('chart_layout_mode'" in patient_src
        assert "chart_layout_mode=chart_layout_mode" in patient_src
        passed.append('8.2: patient.py passes chart_layout_mode to template')
    except Exception as e:
        failed.append(f'8.2: patient.py layout mode: {e}')

    # ==================================================================
    # 8.3 — Waterfall layout (shortest-column-first)
    # ==================================================================
    print('[7/15] Waterfall layout algorithm present...')
    try:
        assert 'colHeights' in js_src, 'Waterfall uses column height tracking'
        assert 'requestAnimationFrame' in js_src, 'Uses rAF for DOM measurement'
        # Old fixed 300px row height should be gone
        assert "row * 300" not in js_src, 'Fixed 300px row height removed'
        passed.append('8.3: Waterfall layout with rAF and column tracking')
    except Exception as e:
        failed.append(f'8.3: Waterfall layout: {e}')

    print('[8/15] Waterfall finds shortest column...')
    try:
        # Verify shortest-column-first logic
        assert 'colHeights[c] < colHeights[col]' in js_src, 'Shortest column selection'
        assert 'offsetHeight' in js_src, 'Measures actual widget height'
        passed.append('8.3: Shortest-column-first placement')
    except Exception as e:
        failed.append(f'8.3: Shortest column: {e}')

    # ==================================================================
    # 8.4 — Independent widget resize reflow
    # ==================================================================
    print('[9/15] _reflowBelow function exists...')
    try:
        assert 'function _reflowBelow' in js_src
        assert '_reflowBelow(' in js_src
        # Called from _endResize
        assert '_reflowBelow(_resizeState.el' in js_src
        passed.append('8.4: _reflowBelow called from _endResize')
    except Exception as e:
        failed.append(f'8.4: Reflow below: {e}')

    print('[10/15] Reflow uses smooth transition...')
    try:
        assert "transition = 'top 0.2s ease'" in js_src or 'top 0.2s ease' in js_src
        passed.append('8.4: Smooth CSS transition on reflow')
    except Exception as e:
        failed.append(f'8.4: Smooth transition: {e}')

    # ==================================================================
    # 8.5 — Resize handle visibility
    # ==================================================================
    print('[11/15] Drag handle default opacity is 0.3...')
    try:
        assert "opacity:0.3;transition:opacity" in js_src, 'Drag handle starts at 0.3 opacity'
        passed.append('8.5: Drag handle visible at 0.3 opacity')
    except Exception as e:
        failed.append(f'8.5: Handle opacity: {e}')

    print('[12/15] Resize outline CSS class exists...')
    try:
        assert '.fw-resizing' in css_src, 'CSS has .fw-resizing class'
        assert 'dashed' in css_src.split('.fw-resizing')[1][:100], 'Dashed outline during resize'
        passed.append('8.5: .fw-resizing dashed outline CSS')
    except Exception as e:
        failed.append(f'8.5: Resize outline: {e}')

    print('[13/15] Resize adds/removes fw-resizing class...')
    try:
        assert "classList.add('fw-resizing')" in js_src
        assert "classList.remove('fw-resizing')" in js_src
        passed.append('8.5: fw-resizing class toggled during resize')
    except Exception as e:
        failed.append(f'8.5: Resize class toggle: {e}')

    # ==================================================================
    # 8.6 — Persist positions to server
    # ==================================================================
    print('[14/15] Drag/resize end saves positions to server...')
    try:
        # _savePositionsToServer called from both _endDrag and _endResize
        assert '_savePositionsToServer(' in js_src
        assert js_src.count('_savePositionsToServer(') >= 3, 'Called from endDrag + endResize + definition'
        passed.append('8.6: Positions saved to server on drag/resize end')
    except Exception as e:
        failed.append(f'8.6: Server position save: {e}')

    print('[15/15] Server positions loaded as fallback...')
    try:
        assert '_fwServerPositions' in js_src, 'JS reads server positions'
        assert '_fwServerPositions' in tpl_src, 'Template sets server positions'
        assert "chart_free_positions" in tpl_src, 'Template passes free positions'
        # patient.py also reads the pref
        assert "get_pref('chart_free_widget_positions'" in patient_src
        passed.append('8.6: Server positions used as fallback')
    except Exception as e:
        failed.append(f'8.6: Server position load: {e}')

    # ==================================================================
    # Results
    # ==================================================================
    print('\n' + '=' * 50)
    for p in passed:
        print(f'  \u2714 {p}')
    for f_item in failed:
        print(f'  \u2718 {f_item}')
    print(f'\n=== Widget Grid Tests: {len(passed)} passed, {len(failed)} failed ===')

    if failed:
        print('\n*** FAILURES DETECTED ***')
        return 1
    print('\n*** ALL TESTS PASSED ***')
    return 0


if __name__ == '__main__':
    sys.exit(run_tests())

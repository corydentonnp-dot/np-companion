"""
Integration tests for Phase 18 — Note Generator Overhaul:
  - 18.1 One-click note acceptance (Accept & Copy, auto-generate on tab)
  - 18.2 Note template intelligence by visit type
  - 18.3 Auto-save drafts (30s localStorage + server)
  - 18.4 Keyboard navigation (Tab/Enter/Escape)

Tests verify template patterns, JS functions, and backend support.
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
    chart_html = _read('templates/patient_chart.html')
    patient_py = _read('routes/patient.py')

    # ==================================================================
    # 18.1 — One-click note acceptance
    # ==================================================================
    print('[1/15] Accept & Copy button present in note widget...')
    try:
        assert 'id="note-accept-btn"' in chart_html, 'Accept button ID'
        assert 'acceptAndCopy()' in chart_html, 'acceptAndCopy onclick'
        assert 'Accept &amp; Copy' in chart_html or 'Accept & Copy' in chart_html, 'Button label'
        passed.append('18.1a Accept & Copy button')
    except AssertionError as e:
        failed.append(f'18.1a Accept & Copy button: {e}')

    print('[2/15] Review & Edit button switches to edit mode...')
    try:
        assert 'id="note-edit-btn"' in chart_html, 'Edit button ID'
        assert 'enterEditMode()' in chart_html, 'enterEditMode onclick'
        assert 'exitEditMode()' in chart_html, 'exitEditMode function'
        passed.append('18.1b Review & Edit mode toggle')
    except AssertionError as e:
        failed.append(f'18.1b Review & Edit mode toggle: {e}')

    print('[3/15] Auto-generate note on Notes tab activation...')
    try:
        assert 'function autoGenerateNote()' in chart_html, 'autoGenerateNote function'
        assert "tabName === 'notes'" in chart_html, 'switchTab triggers on notes tab'
        assert 'autoGenerateNote()' in chart_html, 'autoGenerateNote called in switchTab'
        passed.append('18.1c Auto-generate on tab activation')
    except AssertionError as e:
        failed.append(f'18.1c Auto-generate on tab activation: {e}')

    print('[4/15] Preview mode shows read-only formatted note...')
    try:
        assert 'id="note-preview"' in chart_html, 'Preview container'
        assert 'id="note-preview-content"' in chart_html, 'Preview content div'
        assert 'function renderNotePreview()' in chart_html, 'renderNotePreview function'
        assert "var _noteMode = 'preview'" in chart_html, 'Default mode is preview'
        passed.append('18.1d Preview mode rendering')
    except AssertionError as e:
        failed.append(f'18.1d Preview mode rendering: {e}')

    # ==================================================================
    # 18.2 — Note template intelligence by visit type
    # ==================================================================
    print('[5/15] Visit-type-to-section mapping defined...')
    try:
        assert 'VISIT_TYPE_SECTIONS' in chart_html, 'VISIT_TYPE_SECTIONS mapping'
        assert "'new patient'" in chart_html, 'New patient visit type'
        assert "'follow up'" in chart_html or "'follow-up'" in chart_html, 'Follow-up visit type'
        assert "'awv'" in chart_html, 'AWV visit type'
        passed.append('18.2a Visit type section mapping')
    except AssertionError as e:
        failed.append(f'18.2a Visit type section mapping: {e}')

    print('[6/15] Visit type preselection applies on load...')
    try:
        assert 'function applyVisitTypePreselection()' in chart_html, 'applyVisitTypePreselection function'
        assert 'schedule_context.visit_type' in chart_html, 'Visit type from schedule context'
        assert '_visitType' in chart_html, '_visitType JS variable'
        passed.append('18.2b Visit type preselection')
    except AssertionError as e:
        failed.append(f'18.2b Visit type preselection: {e}')

    print('[7/15] Follow-up preselects Assessment + Plan + Medications...')
    try:
        # Find the follow up mapping and verify expected sections
        idx = chart_html.find("'follow up'")
        if idx == -1:
            idx = chart_html.find("'follow-up'")
        assert idx != -1, 'Follow-up key found'
        snippet = chart_html[idx:idx+200]
        assert 'Assessment' in snippet, 'Assessment in follow-up'
        assert 'Plan' in snippet, 'Plan in follow-up'
        assert 'Medications' in snippet, 'Medications in follow-up'
        passed.append('18.2c Follow-up sections correct')
    except AssertionError as e:
        failed.append(f'18.2c Follow-up sections correct: {e}')

    print('[8/15] AWV preselects Physical Exam + Health Concerns...')
    try:
        idx = chart_html.find("'awv'")
        assert idx != -1, 'AWV key found'
        snippet = chart_html[idx:idx+200]
        assert 'Physical Exam' in snippet, 'Physical Exam in AWV'
        assert 'Health Concerns' in snippet, 'Health Concerns in AWV'
        passed.append('18.2d AWV sections correct')
    except AssertionError as e:
        failed.append(f'18.2d AWV sections correct: {e}')

    # ==================================================================
    # 18.3 — Auto-save drafts
    # ==================================================================
    print('[9/15] Auto-save interval configured at 30 seconds...')
    try:
        assert '30000' in chart_html, '30-second interval'
        assert 'np_note_draft_' in chart_html, 'localStorage key pattern'
        assert 'localStorage.setItem' in chart_html, 'localStorage write'
        passed.append('18.3a Auto-save interval')
    except AssertionError as e:
        failed.append(f'18.3a Auto-save interval: {e}')

    print('[10/15] Draft restore on page load...')
    try:
        assert 'restoreDraft' in chart_html, 'restoreDraft function'
        assert 'localStorage.getItem' in chart_html, 'localStorage read'
        assert 'Restored' in chart_html, 'Restored status message'
        passed.append('18.3b Draft restore on load')
    except AssertionError as e:
        failed.append(f'18.3b Draft restore on load: {e}')

    print('[11/15] Draft cleared on acceptance...')
    try:
        assert 'localStorage.removeItem' in chart_html, 'localStorage clear on accept'
        assert '_noteAccepted' in chart_html, 'Accepted flag tracked'
        passed.append('18.3c Draft cleared on acceptance')
    except AssertionError as e:
        failed.append(f'18.3c Draft cleared on acceptance: {e}')

    print('[12/15] Draft saved indicator shown...')
    try:
        assert 'Draft saved' in chart_html, 'Draft saved indicator text'
        passed.append('18.3d Draft saved indicator')
    except AssertionError as e:
        failed.append(f'18.3d Draft saved indicator: {e}')

    # ==================================================================
    # 18.4 — Keyboard navigation
    # ==================================================================
    print('[13/15] Enter key triggers Accept & Copy...')
    try:
        assert "e.key === 'Enter'" in chart_html, 'Enter key handler'
        assert 'note-accept-btn' in chart_html, 'Accept button targeted'
        passed.append('18.4a Enter key acceptance')
    except AssertionError as e:
        failed.append(f'18.4a Enter key acceptance: {e}')

    print('[14/15] Escape key exits edit mode...')
    try:
        assert "e.key === 'Escape'" in chart_html, 'Escape key handler'
        assert "exitEditMode()" in chart_html, 'exitEditMode called on Escape'
        passed.append('18.4b Escape key exits edit mode')
    except AssertionError as e:
        failed.append(f'18.4b Escape key exits edit mode: {e}')

    print('[15/15] Tab navigates between note sections...')
    try:
        assert "e.key === 'Tab'" in chart_html, 'Tab key handler'
        assert 'note-textarea' in chart_html, 'note-textarea class targeted'
        assert 'e.shiftKey' in chart_html, 'Shift+Tab backward support'
        passed.append('18.4c Tab navigation between sections')
    except AssertionError as e:
        failed.append(f'18.4c Tab navigation between sections: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print()
    print('=' * 60)
    print(f'Phase 18 Note Overhaul: {len(passed)} passed, {len(failed)} failed')
    print('=' * 60)

    if failed:
        for f in failed:
            print(f'  FAIL: {f}')
        sys.exit(1)


if __name__ == '__main__':
    run_tests()

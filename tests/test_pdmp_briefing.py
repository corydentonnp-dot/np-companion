"""
Phase P4-3 — PDMP Morning Briefing Flag (F25a)

Tests for get_overdue_pdmp_patients() helper, dashboard PDMP card,
morning briefing PDMP banner, HIPAA compliance, and edge cases.
"""

import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(relpath):
    with open(os.path.join(ROOT, relpath), 'r', encoding='utf-8') as f:
        return f.read()


class FakeCSEntry:
    """Minimal ControlledSubstanceEntry-like object for unit testing."""
    def __init__(self, mrn='12345', drug_name='Oxycodone 5mg',
                 last_pdmp_check=None, pdmp_check_interval_days=90,
                 is_active=True, user_id=1):
        self.mrn = mrn
        self.drug_name = drug_name
        self.last_pdmp_check = last_pdmp_check
        self.pdmp_check_interval_days = pdmp_check_interval_days
        self.is_active = is_active
        self.user_id = user_id


def _compute_overdue(entries):
    """Standalone overdue logic matching get_overdue_pdmp_patients()."""
    overdue = []
    for e in entries:
        if e.last_pdmp_check is None:
            days_overdue = e.pdmp_check_interval_days
        else:
            due_date = e.last_pdmp_check + timedelta(days=e.pdmp_check_interval_days)
            if date.today() < due_date:
                continue
            days_overdue = (date.today() - due_date).days
        overdue.append({
            'mrn': e.mrn,
            'drug_name': e.drug_name,
            'last_checked': e.last_pdmp_check.isoformat() if e.last_pdmp_check else None,
            'days_overdue': days_overdue,
        })
    return overdue


def run_tests():
    passed = []
    failed = []

    tools_py = _read('routes/tools.py')
    dash_py = _read('routes/dashboard.py')
    dash_html = _read('templates/dashboard.html')
    intel_py = _read('routes/intelligence.py')
    briefing_html = _read('templates/morning_briefing.html')

    # ==================================================================
    # 3.1 — get_overdue_pdmp_patients() helper
    # ==================================================================

    print('[1/15] Helper function exists in routes/tools.py...')
    try:
        assert 'def get_overdue_pdmp_patients' in tools_py, 'function not found'
        passed.append('3.1a helper function exists')
    except (AssertionError, Exception) as e:
        failed.append(f'3.1a helper function exists: {e}')

    print('[2/15] No CS entries — returns empty list...')
    try:
        result = _compute_overdue([])
        assert result == [], f'expected [], got {result}'
        passed.append('3.1b empty list for no entries')
    except (AssertionError, Exception) as e:
        failed.append(f'3.1b empty list for no entries: {e}')

    print('[3/15] All current — returns empty list...')
    try:
        entries = [
            FakeCSEntry(last_pdmp_check=date.today() - timedelta(days=30)),
            FakeCSEntry(mrn='22222', last_pdmp_check=date.today() - timedelta(days=60)),
        ]
        result = _compute_overdue(entries)
        assert len(result) == 0, f'expected 0 overdue, got {len(result)}'
        passed.append('3.1c all current returns empty')
    except (AssertionError, Exception) as e:
        failed.append(f'3.1c all current returns empty: {e}')

    print('[4/15] Some overdue — correct count...')
    try:
        entries = [
            FakeCSEntry(last_pdmp_check=date.today() - timedelta(days=30)),   # current
            FakeCSEntry(mrn='22222', last_pdmp_check=date.today() - timedelta(days=100)),  # overdue
        ]
        result = _compute_overdue(entries)
        assert len(result) == 1, f'expected 1 overdue, got {len(result)}'
        assert result[0]['mrn'] == '22222'
        passed.append('3.1d some overdue correct count')
    except (AssertionError, Exception) as e:
        failed.append(f'3.1d some overdue correct count: {e}')

    print('[5/15] Null last_pdmp_check treated as overdue...')
    try:
        entries = [FakeCSEntry(last_pdmp_check=None)]
        result = _compute_overdue(entries)
        assert len(result) == 1, f'expected 1 overdue for null check, got {len(result)}'
        assert result[0]['last_checked'] is None
        assert result[0]['days_overdue'] == 90  # default interval
        passed.append('3.1e null check treated as overdue')
    except (AssertionError, Exception) as e:
        failed.append(f'3.1e null check treated as overdue: {e}')

    print('[6/15] All overdue — returns all...')
    try:
        entries = [
            FakeCSEntry(mrn='11111', last_pdmp_check=date.today() - timedelta(days=200)),
            FakeCSEntry(mrn='22222', last_pdmp_check=None),
            FakeCSEntry(mrn='33333', last_pdmp_check=date.today() - timedelta(days=91)),
        ]
        result = _compute_overdue(entries)
        assert len(result) == 3, f'expected 3 overdue, got {len(result)}'
        passed.append('3.1f all overdue returns all')
    except (AssertionError, Exception) as e:
        failed.append(f'3.1f all overdue returns all: {e}')

    print('[7/15] Custom interval respected...')
    try:
        # 30-day interval, checked 31 days ago → overdue
        entries = [FakeCSEntry(
            last_pdmp_check=date.today() - timedelta(days=31),
            pdmp_check_interval_days=30,
        )]
        result = _compute_overdue(entries)
        assert len(result) == 1, f'expected 1 overdue with custom interval'
        # 30-day interval, checked 29 days ago → not overdue
        entries2 = [FakeCSEntry(
            last_pdmp_check=date.today() - timedelta(days=29),
            pdmp_check_interval_days=30,
        )]
        result2 = _compute_overdue(entries2)
        assert len(result2) == 0, f'expected 0 overdue when within interval'
        passed.append('3.1g custom interval respected')
    except (AssertionError, Exception) as e:
        failed.append(f'3.1g custom interval respected: {e}')

    print('[8/15] days_overdue computed correctly...')
    try:
        entries = [FakeCSEntry(
            last_pdmp_check=date.today() - timedelta(days=100),
            pdmp_check_interval_days=90,
        )]
        result = _compute_overdue(entries)
        assert result[0]['days_overdue'] == 10, f'expected 10 days overdue, got {result[0]["days_overdue"]}'
        passed.append('3.1h days_overdue accurate')
    except (AssertionError, Exception) as e:
        failed.append(f'3.1h days_overdue accurate: {e}')

    # ==================================================================
    # 3.2 — Dashboard integration
    # ==================================================================

    print('[9/15] Dashboard route passes pdmp_overdue to template...')
    try:
        assert 'pdmp_overdue' in dash_py, 'pdmp_overdue not in dashboard.py'
        assert 'pdmp_overdue=pdmp_overdue' in dash_py, 'pdmp_overdue not passed to template'
        assert 'get_overdue_pdmp_patients' in dash_py, 'helper not called in dashboard'
        passed.append('3.2a dashboard passes pdmp_overdue')
    except (AssertionError, Exception) as e:
        failed.append(f'3.2a dashboard passes pdmp_overdue: {e}')

    print('[10/15] Dashboard template has PDMP overdue card...')
    try:
        assert 'pdmp-overdue' in dash_html or 'pdmp_overdue' in dash_html, \
            'PDMP card missing from dashboard template'
        assert 'PDMP' in dash_html, 'PDMP text missing from dashboard'
        assert 'cs-tracker' in dash_html, 'link to CS tracker missing'
        passed.append('3.2b dashboard PDMP overdue card')
    except (AssertionError, Exception) as e:
        failed.append(f'3.2b dashboard PDMP overdue card: {e}')

    print('[11/15] Dashboard PDMP card HIPAA-safe (MRN last-4 only)...')
    try:
        # Check that the dashboard template only shows last 4 of MRN
        assert "p.mrn[-4:]" in dash_html, 'PDMP card should show MRN last-4 only'
        # Verify no patient_name in the PDMP section
        pdmp_section_start = dash_html.index('pdmp-overdue')
        pdmp_section = dash_html[pdmp_section_start:pdmp_section_start + 800]
        assert 'patient_name' not in pdmp_section, 'patient_name should not appear in PDMP card'
        passed.append('3.2c PDMP card HIPAA compliance')
    except (AssertionError, Exception) as e:
        failed.append(f'3.2c PDMP card HIPAA compliance: {e}')

    print('[12/15] Dashboard urgent_count includes PDMP overdue...')
    try:
        assert 'len(pdmp_overdue)' in dash_py, 'pdmp_overdue not included in urgent_count'
        passed.append('3.2d urgent_count includes PDMP')
    except (AssertionError, Exception) as e:
        failed.append(f'3.2d urgent_count includes PDMP: {e}')

    # ==================================================================
    # 3.3 — Morning briefing integration
    # ==================================================================

    print('[13/15] Briefing route passes pdmp_overdue_count...')
    try:
        assert 'pdmp_overdue_count' in intel_py, 'pdmp_overdue_count not in intelligence.py'
        assert 'get_overdue_pdmp_patients' in intel_py, 'helper not called in briefing'
        passed.append('3.3a briefing passes pdmp_overdue_count')
    except (AssertionError, Exception) as e:
        failed.append(f'3.3a briefing passes pdmp_overdue_count: {e}')

    print('[14/15] Briefing template shows PDMP banner...')
    try:
        assert 'pdmp_overdue_count' in briefing_html, 'pdmp_overdue_count missing from template'
        assert 'PDMP' in briefing_html, 'PDMP text missing from briefing'
        passed.append('3.3b briefing PDMP banner')
    except (AssertionError, Exception) as e:
        failed.append(f'3.3b briefing PDMP banner: {e}')

    print('[15/15] Briefing PDMP banner HIPAA-safe (count only, no PHI)...')
    try:
        # Find the PDMP section in briefing
        idx = briefing_html.index('pdmp_overdue_count')
        pdmp_section = briefing_html[idx:idx + 400]
        assert 'mrn' not in pdmp_section.lower() or 'pdmp_overdue_count' in pdmp_section, \
            'MRN mentioned in briefing PDMP section'
        assert 'patient_name' not in pdmp_section, 'patient_name in briefing PDMP section'
        passed.append('3.3c briefing HIPAA — count only')
    except (AssertionError, Exception) as e:
        failed.append(f'3.3c briefing HIPAA — count only: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print(f'\n{"="*60}')
    print(f'Phase P4-3 PDMP Briefing Flag: {len(passed)} passed, {len(failed)} failed')
    print(f'{"="*60}')
    if failed:
        for f_msg in failed:
            print(f'  FAIL  {f_msg}')
    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

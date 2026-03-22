"""
Phase P4-1 — Double-Booking Detection (F4c)

Tests for schedule overlap / double-booking detection:
  - 1.1 Overlap detection in analyze_schedule_anomalies()
  - 1.2 Dashboard template overlap badge rendering
  - 1.3 Morning briefing overlap_count integration

Covers: overlapping appointments, exact same-time bookings, back-to-back
(no false positive), three-way overlaps, single appointment edge case,
HIPAA compliance (no full names in anomaly JSON), and template badges.
"""

import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(relpath):
    with open(os.path.join(ROOT, relpath), 'r', encoding='utf-8') as f:
        return f.read()


class FakeAppointment:
    """Minimal Schedule-like object for unit testing."""
    def __init__(self, time, duration=15, visit_type='Follow Up',
                 patient_name='DOE, JOHN', patient_mrn='12345',
                 is_new_patient=False, reason='', status='Scheduled',
                 patient_dob='', entered_by='xml'):
        self.appointment_time = time
        self.duration_minutes = duration
        self.visit_type = visit_type
        self.patient_name = patient_name
        self.patient_mrn = patient_mrn
        self.is_new_patient = is_new_patient
        self.reason = reason
        self.status = status
        self.patient_dob = patient_dob
        self.entered_by = entered_by


def run_tests():
    passed = []
    failed = []

    # Import the function under test
    from routes.dashboard import analyze_schedule_anomalies

    # Load template sources for badge checks
    dash_html = _read('templates/dashboard.html')
    dash_py = _read('routes/dashboard.py')
    briefing_html = _read('templates/morning_briefing.html')
    intel_py = _read('routes/intelligence.py')

    # ==================================================================
    # 1.1 — Overlap detection logic
    # ==================================================================

    print('[1/15] Basic overlap detection — two overlapping appointments...')
    try:
        appts = [
            FakeAppointment('09:00', duration=30),
            FakeAppointment('09:15', duration=15),
        ]
        anomalies = analyze_schedule_anomalies(appts)
        overlaps = [a for a in anomalies if a['type'] == 'schedule_overlap']
        assert len(overlaps) == 1, f'expected 1 overlap, got {len(overlaps)}'
        assert overlaps[0]['severity'] == 'warning'
        assert overlaps[0]['overlap_minutes'] == 15
        passed.append('1.1a basic overlap detection')
    except (AssertionError, Exception) as e:
        failed.append(f'1.1a basic overlap detection: {e}')

    print('[2/15] Exact same-time booking — two appointments at same time...')
    try:
        appts = [
            FakeAppointment('10:00', duration=15),
            FakeAppointment('10:00', duration=15),
        ]
        anomalies = analyze_schedule_anomalies(appts)
        overlaps = [a for a in anomalies if a['type'] == 'schedule_overlap']
        assert len(overlaps) == 1, f'expected 1 overlap, got {len(overlaps)}'
        assert overlaps[0]['overlap_minutes'] == 15
        passed.append('1.1b exact same-time booking')
    except (AssertionError, Exception) as e:
        failed.append(f'1.1b exact same-time booking: {e}')

    print('[3/15] Back-to-back — no false positive overlap...')
    try:
        appts = [
            FakeAppointment('09:00', duration=15),
            FakeAppointment('09:15', duration=15),
        ]
        anomalies = analyze_schedule_anomalies(appts)
        overlaps = [a for a in anomalies if a['type'] == 'schedule_overlap']
        assert len(overlaps) == 0, f'expected 0 overlaps for back-to-back, got {len(overlaps)}'
        passed.append('1.1c back-to-back no false positive')
    except (AssertionError, Exception) as e:
        failed.append(f'1.1c back-to-back no false positive: {e}')

    print('[4/15] Normal gap — no overlap flagged...')
    try:
        appts = [
            FakeAppointment('09:00', duration=15),
            FakeAppointment('10:00', duration=15),
        ]
        anomalies = analyze_schedule_anomalies(appts)
        overlaps = [a for a in anomalies if a['type'] == 'schedule_overlap']
        assert len(overlaps) == 0, f'expected 0 overlaps, got {len(overlaps)}'
        passed.append('1.1d normal gap no overlap')
    except (AssertionError, Exception) as e:
        failed.append(f'1.1d normal gap no overlap: {e}')

    print('[5/15] Three-way overlap — multiple concurrent appointments...')
    try:
        appts = [
            FakeAppointment('09:00', duration=30),
            FakeAppointment('09:10', duration=30),
            FakeAppointment('09:20', duration=30),
        ]
        anomalies = analyze_schedule_anomalies(appts)
        overlaps = [a for a in anomalies if a['type'] == 'schedule_overlap']
        assert len(overlaps) == 2, f'expected 2 overlaps for 3-way, got {len(overlaps)}'
        passed.append('1.1e three-way overlap')
    except (AssertionError, Exception) as e:
        failed.append(f'1.1e three-way overlap: {e}')

    print('[6/15] Single appointment — no overlap possible...')
    try:
        appts = [FakeAppointment('09:00', duration=15)]
        anomalies = analyze_schedule_anomalies(appts)
        overlaps = [a for a in anomalies if a['type'] == 'schedule_overlap']
        assert len(overlaps) == 0, f'expected 0 overlaps for single appt'
        passed.append('1.1f single appointment edge case')
    except (AssertionError, Exception) as e:
        failed.append(f'1.1f single appointment edge case: {e}')

    print('[7/15] Empty schedule — no crash...')
    try:
        anomalies = analyze_schedule_anomalies([])
        overlaps = [a for a in anomalies if a['type'] == 'schedule_overlap']
        assert len(overlaps) == 0
        passed.append('1.1g empty schedule')
    except (AssertionError, Exception) as e:
        failed.append(f'1.1g empty schedule: {e}')

    print('[8/15] Overlap message contains appointment times only (HIPAA)...')
    try:
        appts = [
            FakeAppointment('09:00', duration=30, patient_name='SMITH, ALICE', patient_mrn='99999'),
            FakeAppointment('09:15', duration=15, patient_name='JONES, BOB', patient_mrn='88888'),
        ]
        anomalies = analyze_schedule_anomalies(appts)
        overlaps = [a for a in anomalies if a['type'] == 'schedule_overlap']
        assert len(overlaps) == 1
        msg = overlaps[0]['message']
        assert 'SMITH' not in msg, f'patient name leaked in message: {msg}'
        assert 'JONES' not in msg, f'patient name leaked in message: {msg}'
        assert 'ALICE' not in msg, f'patient name leaked in message: {msg}'
        assert 'BOB' not in msg, f'patient name leaked in message: {msg}'
        assert '09:00' in msg and '09:15' in msg, f'times missing from message: {msg}'
        passed.append('1.1h HIPAA — no patient names in overlap anomaly')
    except (AssertionError, Exception) as e:
        failed.append(f'1.1h HIPAA — no patient names in overlap anomaly: {e}')

    print('[9/15] Overlap has severity "warning"...')
    try:
        appts = [
            FakeAppointment('14:00', duration=30),
            FakeAppointment('14:10', duration=15),
        ]
        anomalies = analyze_schedule_anomalies(appts)
        overlaps = [a for a in anomalies if a['type'] == 'schedule_overlap']
        assert all(o['severity'] == 'warning' for o in overlaps), 'overlap severity should be warning'
        passed.append('1.1i overlap severity is warning')
    except (AssertionError, Exception) as e:
        failed.append(f'1.1i overlap severity is warning: {e}')

    print('[10/15] Overlap minutes computed correctly (large overlap)...')
    try:
        appts = [
            FakeAppointment('08:00', duration=60),  # ends at 09:00
            FakeAppointment('08:30', duration=15),   # starts at 08:30 → 30 min overlap
        ]
        anomalies = analyze_schedule_anomalies(appts)
        overlaps = [a for a in anomalies if a['type'] == 'schedule_overlap']
        assert len(overlaps) == 1
        assert overlaps[0]['overlap_minutes'] == 30, f'expected 30, got {overlaps[0]["overlap_minutes"]}'
        passed.append('1.1j large overlap minutes')
    except (AssertionError, Exception) as e:
        failed.append(f'1.1j large overlap minutes: {e}')

    # ==================================================================
    # 1.2 — Dashboard template overlap badge
    # ==================================================================

    print('[11/15] Dashboard template has overlap badge markup...')
    try:
        assert 'overlap_times' in dash_html, 'overlap_times variable in template'
        assert 'OVERLAP' in dash_html, 'OVERLAP badge text in template'
        passed.append('1.2a dashboard overlap badge markup')
    except (AssertionError, Exception) as e:
        failed.append(f'1.2a dashboard overlap badge markup: {e}')

    print('[12/15] Dashboard route passes overlap_times to template...')
    try:
        assert 'overlap_times' in dash_py, 'overlap_times computed in dashboard.py'
        assert "overlap_times=overlap_times" in dash_py, 'overlap_times in render_template'
        passed.append('1.2b dashboard route passes overlap_times')
    except (AssertionError, Exception) as e:
        failed.append(f'1.2b dashboard route passes overlap_times: {e}')

    print('[13/15] Dashboard route builds overlap_times set from anomalies...')
    try:
        assert 'overlap_times = set()' in dash_py, 'overlap_times initialized as set'
        assert "schedule_overlap" in dash_py, 'schedule_overlap type in dashboard.py'
        passed.append('1.2c overlap_times set construction')
    except (AssertionError, Exception) as e:
        failed.append(f'1.2c overlap_times set construction: {e}')

    # ==================================================================
    # 1.3 — Morning briefing overlap count
    # ==================================================================

    print('[14/15] Morning briefing route includes overlap_count...')
    try:
        assert 'overlap_count' in intel_py, 'overlap_count in intelligence.py'
        assert 'analyze_schedule_anomalies' in intel_py, 'imports anomaly analysis in briefing'
        passed.append('1.3a briefing route overlap_count')
    except (AssertionError, Exception) as e:
        failed.append(f'1.3a briefing route overlap_count: {e}')

    print('[15/15] Morning briefing template shows double-booking banner...')
    try:
        assert 'overlap_count' in briefing_html, 'overlap_count in briefing template'
        assert 'double-booking' in briefing_html, 'double-booking text in briefing template'
        passed.append('1.3b briefing template overlap banner')
    except (AssertionError, Exception) as e:
        failed.append(f'1.3b briefing template overlap banner: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print(f'\n{"="*60}')
    print(f'Phase P4-1 Double-Booking Detection: {len(passed)} passed, {len(failed)} failed')
    print(f'{"="*60}')
    if failed:
        for f_msg in failed:
            print(f'  FAIL  {f_msg}')
    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

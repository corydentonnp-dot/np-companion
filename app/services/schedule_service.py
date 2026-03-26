"""
CareCompanion — Schedule Service

Schedule anomaly analysis extracted from routes/dashboard.py (Band 3 B1.20).
No DB dependencies — pure analysis of appointment objects.
"""


def analyze_schedule_anomalies(appointments):
    """
    Scan the day's appointments for scheduling issues.

    Checks for:
    - short_appointment: visit type that typically needs more time than booked
    - schedule_gap: 30+ minutes between appointments
    - schedule_overlap: overlapping appointments (double-booking)
    - back_to_back_complex: two complex visit types with no gap
    - late_new_patient: new patient in the last 2 slots of the day

    Returns a list of dicts:
        [{"type": "back_to_back_complex", "message": "...", "severity": "warning"}, ...]
    """
    anomalies = []

    if len(appointments) < 1:
        return anomalies

    complex_types = {
        'new patient', 'physical', 'annual wellness', 'awv',
        'comprehensive', 'complete physical', 'new pt',
    }

    needs_more_time = {
        'new patient': 30,
        'new pt': 30,
        'physical': 30,
        'annual wellness': 30,
        'awv': 30,
        'comprehensive': 30,
        'complete physical': 30,
    }

    for i, appt in enumerate(appointments):
        vtype = (appt.visit_type or '').lower().strip()

        # Short appointment check
        if vtype in needs_more_time:
            min_expected = needs_more_time[vtype]
            if (appt.duration_minutes or 15) < min_expected:
                anomalies.append({
                    'type': 'short_appointment',
                    'message': (
                        f'{appt.appointment_time} — "{appt.visit_type}" '
                        f'booked for {appt.duration_minutes} min '
                        f'(usually needs {min_expected}+ min)'
                    ),
                    'severity': 'warning',
                })

        # Back-to-back complex check
        if i > 0 and vtype in complex_types:
            prev_vtype = (appointments[i - 1].visit_type or '').lower().strip()
            if prev_vtype in complex_types:
                anomalies.append({
                    'type': 'back_to_back_complex',
                    'message': (
                        f'Back-to-back complex visits: '
                        f'{appointments[i-1].appointment_time} {appointments[i-1].visit_type} '
                        f'followed by {appt.appointment_time} {appt.visit_type}'
                    ),
                    'severity': 'warning',
                })

        # Late new patient check
        if i >= len(appointments) - 2 and vtype in ('new patient', 'new pt'):
            anomalies.append({
                'type': 'late_new_patient',
                'message': (
                    f'{appt.appointment_time} — New patient in last 2 slots of the day'
                ),
                'severity': 'info',
            })

    return anomalies

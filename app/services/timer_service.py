"""
CareCompanion — Timer Service

Billing analytics constants and helper functions extracted from routes/timer.py
(Band 3 B1.15).

Moved here to allow agent_service.py to use these without a cross-route import.
routes/timer.py re-imports everything from this module.
"""

# E&M billing level code sets
RVU_TABLE = {
    '99211': 0.18, '99212': 0.70, '99213': 1.30, '99214': 1.92, '99215': 2.80,
    '99201': 0.48, '99202': 0.93, '99203': 1.60, '99204': 2.60, '99205': 3.50,
    'AWV-Initial': 2.43, 'AWV-Subsequent': 1.50,
}

# Expected time ranges per E&M level (min, max minutes)
EM_TIME_RANGES = {
    '99211': (1, 10),
    '99212': (5, 20),
    '99213': (10, 30),
    '99214': (20, 45),
    '99215': (30, 70),
    '99201': (5, 15),
    '99202': (10, 25),
    '99203': (15, 40),
    '99204': (25, 55),
    '99205': (35, 75),
    'AWV-Initial': (30, 75),
    'AWV-Subsequent': (20, 50),
}

_EM_LEVEL_ORDER = ['99211', '99212', '99213', '99214', '99215']
_EM_NEW_LEVEL_ORDER = ['99201', '99202', '99203', '99204', '99205']

_NEW_PATIENT_CODES = {'99201', '99202', '99203', '99204', '99205'}
_ESTABLISHED_CODES = {'99211', '99212', '99213', '99214', '99215'}


def detect_anomalies(session):
    """
    Check a TimeLog session for billing anomalies.

    Returns a list of dicts: {'msg': str, 'type': str} for each warning.
    """
    warnings = []
    level = session.billed_level or ''
    chart_min = (session.duration_seconds or 0) / 60
    f2f_min = (session.face_to_face_seconds or 0) / 60

    if not level:
        warnings.append({'msg': 'No billing level assigned', 'type': 'no_level'})
        return warnings

    # Time vs level consistency
    expected = EM_TIME_RANGES.get(level)
    if expected:
        low, high = expected
        if chart_min < low * 0.5:
            warnings.append({
                'msg': f'Chart time ({chart_min:.0f}min) very low for {level} (expected {low}-{high}min)',
                'type': 'time_low',
            })
        elif chart_min > high * 1.5:
            warnings.append({
                'msg': f'Chart time ({chart_min:.0f}min) very high for {level} (expected {low}-{high}min)',
                'type': 'time_high',
            })

    # Upcode suggestion — time supports a higher level
    level_list = (
        _EM_NEW_LEVEL_ORDER
        if level.startswith('992') and level in _EM_NEW_LEVEL_ORDER
        else _EM_LEVEL_ORDER
    )
    if level in level_list:
        idx = level_list.index(level)
        if idx < len(level_list) - 1:
            next_level = level_list[idx + 1]
            next_expected = EM_TIME_RANGES.get(next_level)
            if next_expected and chart_min >= next_expected[0]:
                warnings.append({
                    'msg': (
                        f'Consider higher level based on time ({chart_min:.0f}min meets '
                        f'{next_level} threshold of {next_expected[0]}min)'
                    ),
                    'type': 'upcode',
                })

    # F2F ratio check
    if level in ('99213', '99214', '99215', '99203', '99204', '99205'):
        if chart_min > 0 and f2f_min / chart_min < 0.3:
            warnings.append({
                'msg': f'Low F2F ratio ({f2f_min:.0f}/{chart_min:.0f}min = {f2f_min/chart_min*100:.0f}%)',
                'type': 'f2f_low',
            })

    # High-level code without complexity flag
    if level in ('99215', '99205') and not session.is_complex:
        warnings.append({
            'msg': f'{level} billed without complexity flag',
            'type': 'no_complexity',
        })

    return warnings


def monthly_stats(sessions):
    """Compute summary statistics for a list of completed TimeLog sessions."""
    total_patients = len(sessions)
    total_chart_hrs = round(sum(s.duration_seconds or 0 for s in sessions) / 3600, 1)
    total_f2f_hrs = round(sum(s.face_to_face_seconds or 0 for s in sessions) / 3600, 1)

    em_dist = {}
    total_rvu = 0
    new_count = 0
    estab_count = 0
    for s in sessions:
        lvl = s.billed_level or 'Unbilled'
        if lvl not in em_dist:
            em_dist[lvl] = {'count': 0, 'rvu': 0}
        em_dist[lvl]['count'] += 1
        rvu = RVU_TABLE.get(lvl, 0)
        em_dist[lvl]['rvu'] = round(em_dist[lvl]['rvu'] + rvu, 2)
        total_rvu += rvu
        if lvl in _NEW_PATIENT_CODES:
            new_count += 1
        elif lvl in _ESTABLISHED_CODES:
            estab_count += 1

    anomaly_count = sum(1 for s in sessions if detect_anomalies(s))

    weekly = {}
    for s in sessions:
        _, wk, _ = s.session_start.isocalendar()
        wk_key = f'Week {wk}'
        if wk_key not in weekly:
            weekly[wk_key] = {'patients': 0, 'rvu': 0}
        weekly[wk_key]['patients'] += 1
        weekly[wk_key]['rvu'] = round(
            weekly[wk_key]['rvu'] + RVU_TABLE.get(s.billed_level or '', 0), 2
        )

    return {
        'total_patients': total_patients,
        'total_chart_hrs': total_chart_hrs,
        'total_f2f_hrs': total_f2f_hrs,
        'em_dist': em_dist,
        'total_rvu': round(total_rvu, 2),
        'anomaly_count': anomaly_count,
        'new_count': new_count,
        'estab_count': estab_count,
        'weekly': weekly,
    }

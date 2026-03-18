"""
NP Companion — Dashboard Route (Today View)

File location: np-companion/routes/dashboard.py

The main Today View showing:
  - Today's appointment schedule (from NetPractice scraper)
  - Gold "NEW" badge for new patients
  - Duration estimator (booked time vs typical pace)
  - Schedule anomaly warnings
  - NetPractice re-auth banner when session needs renewal

Features: F4, F4a (new patient flag), F4b (duration estimator),
          F4c (double-booking + gap detector)
"""

from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func

from models import db
from models.schedule import Schedule
from models.timelog import TimeLog
from models.patient import PatientRecord

dashboard_bp = Blueprint('dashboard', __name__)


# ======================================================================
# Helper: Duration Estimator
# ======================================================================
def estimate_schedule_duration(user_id, appointments):
    """
    Compare booked schedule time against the user's actual historical pace.

    For each visit type, we look at the user's past completed visits in
    time_logs.  If they have 20+ visits of that type, we use their median
    duration.  Otherwise we fall back to the booked slot time.

    Returns
    -------
    dict with keys:
        booked_minutes      — sum of all booked slot durations
        estimated_minutes   — sum based on the user's typical pace
        likely_end_time     — estimated end time string (e.g. "4:30 PM")
        pace_label          — "ahead", "behind", or "on track"
        details             — per-visit-type breakdown list
    """
    if not appointments:
        return {
            'booked_minutes': 0,
            'estimated_minutes': 0,
            'likely_end_time': '--',
            'pace_label': 'on track',
            'details': [],
        }

    # Get the user's average duration per visit_type from time_logs
    # Only use visit types with 20+ logged sessions for reliability
    averages_query = (
        db.session.query(
            TimeLog.visit_type,
            func.avg(TimeLog.duration_seconds).label('avg_seconds'),
            func.count(TimeLog.id).label('count'),
        )
        .filter(
            TimeLog.user_id == user_id,
            TimeLog.duration_seconds > 0,
            TimeLog.visit_type != '',
        )
        .group_by(TimeLog.visit_type)
        .all()
    )

    # Build lookup: visit_type -> avg minutes (only if 20+ entries)
    pace_lookup = {}
    for row in averages_query:
        if row.count >= 20:
            pace_lookup[row.visit_type.lower()] = round(row.avg_seconds / 60)

    booked_total = 0
    estimated_total = 0
    details = []

    for appt in appointments:
        booked_min = appt.duration_minutes or 15
        booked_total += booked_min

        visit_type_lower = (appt.visit_type or '').lower()

        # Use historical pace if we have enough data, otherwise booked time
        if visit_type_lower in pace_lookup:
            est_min = pace_lookup[visit_type_lower]
            source = 'historical'
        else:
            est_min = booked_min
            source = 'booked'

        estimated_total += est_min
        details.append({
            'visit_type': appt.visit_type or 'Unknown',
            'booked': booked_min,
            'estimated': est_min,
            'source': source,
        })

    # Calculate likely end time from first appointment + estimated duration
    likely_end = '--'
    if appointments:
        first_time = appointments[0].appointment_time
        try:
            # Parse time like "09:30" or "9:30"
            start_dt = datetime.strptime(first_time.strip(), '%H:%M')
            end_dt = start_dt + timedelta(minutes=estimated_total)
            likely_end = end_dt.strftime('%I:%M %p').lstrip('0')
        except (ValueError, AttributeError):
            likely_end = '--'

    # Determine pace label
    diff = estimated_total - booked_total
    if diff > 15:
        pace_label = 'behind'
    elif diff < -15:
        pace_label = 'ahead'
    else:
        pace_label = 'on track'

    return {
        'booked_minutes': booked_total,
        'estimated_minutes': estimated_total,
        'likely_end_time': likely_end,
        'pace_label': pace_label,
        'details': details,
    }


# ======================================================================
# Helper: Schedule Anomaly Analysis
# ======================================================================
def analyze_schedule_anomalies(appointments):
    """
    Scan the day's appointments for scheduling issues.

    Checks for:
    - back_to_back_complex: Two complex visit types with no gap
    - short_appointment: Less than 15 minutes for a visit type that usually
      takes longer (new patient in 15 min, physical in 15 min, etc.)
    - schedule_gap: A gap of 30+ minutes between appointments
    - late_new_patient: A new patient scheduled in the last 2 slots of the day

    Returns a list of dicts:
        [{"type": "back_to_back_complex", "message": "...", "severity": "warning"}, ...]
    """
    anomalies = []

    if len(appointments) < 1:
        return anomalies

    # Visit types that are considered "complex" (need more time)
    complex_types = {
        'new patient', 'physical', 'annual wellness', 'awv',
        'comprehensive', 'complete physical', 'new pt',
    }

    # Visit types that should NOT be 15 minutes
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

        # --- Short appointment check ---
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

        # --- Back-to-back complex check ---
        if i > 0:
            prev_type = (appointments[i - 1].visit_type or '').lower().strip()
            if vtype in complex_types and prev_type in complex_types:
                anomalies.append({
                    'type': 'back_to_back_complex',
                    'message': (
                        f'{appointments[i-1].appointment_time} & '
                        f'{appt.appointment_time} — '
                        f'back-to-back complex visits '
                        f'("{appointments[i-1].visit_type}" → "{appt.visit_type}")'
                    ),
                    'severity': 'warning',
                })

        # --- Late new patient check ---
        if appt.is_new_patient and i >= len(appointments) - 2 and len(appointments) > 3:
            anomalies.append({
                'type': 'late_new_patient',
                'message': (
                    f'{appt.appointment_time} — New patient '
                    f'"{appt.patient_name}" scheduled in '
                    f'last {"slot" if i == len(appointments) - 1 else "2 slots"} of the day'
                ),
                'severity': 'info',
            })

    # --- Gap detection (30+ minutes between appointments) ---
    for i in range(1, len(appointments)):
        try:
            prev_time = datetime.strptime(
                appointments[i - 1].appointment_time.strip(), '%H:%M'
            )
            curr_time = datetime.strptime(
                appointments[i].appointment_time.strip(), '%H:%M'
            )
            prev_end = prev_time + timedelta(
                minutes=appointments[i - 1].duration_minutes or 15
            )
            gap_minutes = (curr_time - prev_end).total_seconds() / 60

            if gap_minutes >= 30:
                anomalies.append({
                    'type': 'schedule_gap',
                    'message': (
                        f'{int(gap_minutes)} min gap between '
                        f'{appointments[i-1].appointment_time} and '
                        f'{appointments[i].appointment_time}'
                    ),
                    'severity': 'info',
                })
        except (ValueError, AttributeError):
            continue

    return anomalies


# ======================================================================
# GET /dashboard — Today View
# ======================================================================
@dashboard_bp.route('/dashboard')
@login_required
def index():
    """
    Today View: appointment schedule, new patient badges, duration
    estimator, anomaly warnings, and NetPractice auth status.
    Supports ?date=YYYY-MM-DD for viewing other days.
    """
    # Parse optional date parameter (default to today)
    date_str = request.args.get('date', '')
    try:
        view_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
    except ValueError:
        view_date = date.today()

    today = date.today()
    yesterday = view_date - timedelta(days=1)
    tomorrow = view_date + timedelta(days=1)

    # Get appointments for the selected date for the current user
    appointments = list(
        Schedule.query
        .filter_by(user_id=current_user.id, appointment_date=view_date)
        .order_by(Schedule.appointment_time)
        .all()
    )

    # Inject perpetual test patient appointment when enabled
    import config as _cfg
    if getattr(_cfg, 'TEST_PATIENT_APPOINTMENT_ENABLED', False):
        test_appt = Schedule(
            user_id=current_user.id,
            appointment_date=view_date,
            appointment_time='07:00',
            patient_name='TEST, TEST',
            patient_mrn='62815',
            visit_type='TEST',
            reason='Test Patient',
            duration_minutes=15,
            status='SCHEDULED',
            is_new_patient=False,
        )
        appointments.insert(0, test_appt)

    # Duration estimator
    duration_info = estimate_schedule_duration(current_user.id, appointments)

    # Anomaly analysis
    anomalies = analyze_schedule_anomalies(appointments)

    # Count new patients for the summary line
    new_patient_count = sum(1 for a in appointments if a.is_new_patient)

    # Total booked time in hours for display
    booked_hours = round(duration_info['booked_minutes'] / 60, 1)
    estimated_hours = round(duration_info['estimated_minutes'] / 60, 1)

    # F15a: Care gap counts per patient for badge display
    care_gap_counts = {}
    try:
        from models.caregap import CareGap
        open_gaps = CareGap.query.filter_by(
            user_id=current_user.id, is_addressed=False
        ).all()
        for g in open_gaps:
            care_gap_counts[g.mrn] = care_gap_counts.get(g.mrn, 0) + 1
    except Exception:
        pass

    # Patient panel: all records for this user, sorted by last parsed
    my_patients = (
        PatientRecord.query
        .filter_by(user_id=current_user.id)
        .order_by(PatientRecord.last_xml_parsed.desc())
        .all()
    )

    # Billing opportunities for today's scheduled patients
    billing_opportunities = []
    total_estimated_revenue = 0.0
    try:
        from models.billing import BillingOpportunity
        billing_opportunities = (
            BillingOpportunity.query
            .filter_by(user_id=current_user.id, visit_date=view_date)
            .filter(BillingOpportunity.status.in_(['pending', 'partial']))
            .order_by(BillingOpportunity.estimated_revenue.desc())
            .all()
        )
        total_estimated_revenue = sum(
            o.estimated_revenue or 0 for o in billing_opportunities
        )
    except Exception:
        pass

    return render_template(
        'dashboard.html',
        appointments=appointments,
        duration_info=duration_info,
        anomalies=anomalies,
        new_patient_count=new_patient_count,
        booked_hours=booked_hours,
        estimated_hours=estimated_hours,
        view_date=view_date,
        today=today,
        yesterday=yesterday,
        tomorrow=tomorrow,
        is_today=(view_date == today),
        care_gap_counts=care_gap_counts,
        my_patients=my_patients,
        billing_opportunities=billing_opportunities,
        total_estimated_revenue=total_estimated_revenue,
    )


# ======================================================================
# GET /api/schedule?date=YYYY-MM-DD — JSON schedule for AJAX loading
# ======================================================================
@dashboard_bp.route('/api/schedule')
@login_required
def api_schedule():
    """
    Return the schedule for a given date as JSON.
    Used by the dashboard for AJAX date navigation.
    """
    date_str = request.args.get('date', '')
    try:
        view_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid date format'}), 400

    appointments = (
        Schedule.query
        .filter_by(user_id=current_user.id, appointment_date=view_date)
        .order_by(Schedule.appointment_time)
        .all()
    )

    return jsonify({
        'success': True,
        'date': view_date.isoformat(),
        'count': len(appointments),
        'appointments': [
            {
                'time': a.appointment_time,
                'patient_name': a.patient_name,
                'patient_mrn_last4': (a.patient_mrn or '')[-4:] if a.patient_mrn else '',
                'visit_type': a.visit_type,
                'reason': a.reason or '',
                'duration_minutes': a.duration_minutes,
                'status': a.status or 'scheduled',
                'is_new_patient': a.is_new_patient,
                'location': a.location or '',
                'provider_name': a.provider_name or '',
            }
            for a in appointments
        ],
    })


# ======================================================================
# GET /api/patient-search?q=<term> — Patient search (F4f)
# ======================================================================
@dashboard_bp.route('/api/patient-search')
@login_required
def api_patient_search():
    """
    Search patients by name or MRN. Returns last-4 MRN only.
    Searches PatientRecord + Schedule tables, scoped to current user.
    """
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])

    results = []
    seen_mrns = set()
    search_term = f'%{q}%'

    # Search PatientRecord
    records = (
        PatientRecord.query
        .filter_by(user_id=current_user.id)
        .filter(
            db.or_(
                PatientRecord.patient_name.ilike(search_term),
                PatientRecord.mrn.ilike(search_term),
            )
        )
        .limit(10)
        .all()
    )
    for r in records:
        if r.mrn not in seen_mrns:
            seen_mrns.add(r.mrn)
            results.append({
                'mrn': r.mrn,
                'mrn_last4': r.mrn[-4:] if r.mrn and len(r.mrn) >= 4 else r.mrn,
                'name': r.patient_name or 'Unknown',
                'dob': r.patient_dob or '',
                'last_seen': r.last_xml_parsed.strftime('%m/%d/%Y') if r.last_xml_parsed else '',
            })

    # Also search Schedule if we need more results
    if len(results) < 10:
        schedules = (
            Schedule.query
            .filter_by(user_id=current_user.id)
            .filter(
                db.or_(
                    Schedule.patient_name.ilike(search_term),
                    Schedule.patient_mrn.ilike(search_term),
                )
            )
            .order_by(Schedule.appointment_date.desc())
            .limit(10)
            .all()
        )
        for s in schedules:
            mrn = s.patient_mrn or ''
            if mrn and mrn not in seen_mrns:
                seen_mrns.add(mrn)
                results.append({
                    'mrn': mrn,
                    'mrn_last4': mrn[-4:] if len(mrn) >= 4 else mrn,
                    'name': s.patient_name or 'Unknown',
                    'dob': s.patient_dob or '',
                    'last_seen': s.appointment_date.isoformat() if s.appointment_date else '',
                })

    return jsonify(results[:10])

"""
CareCompanion — Dashboard Route (Today View)

File location: carecompanion/routes/dashboard.py

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
from threading import Thread

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import func

from models import db
from models.schedule import Schedule
from models.timelog import TimeLog
from models.patient import PatientRecord

dashboard_bp = Blueprint('dashboard', __name__)

# ---- Data collection job tracker (Phase 4) ----
# Module-level dict: schedule_id → {status, message, started_at}
_collect_jobs = {}


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
    - schedule_overlap: Overlapping appointments (double-booking)
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
            elif gap_minutes < 0:
                overlap_min = abs(int(gap_minutes))
                anomalies.append({
                    'type': 'schedule_overlap',
                    'message': (
                        f'{appointments[i-1].appointment_time} and '
                        f'{appointments[i].appointment_time} — '
                        f'appointments overlap by {overlap_min} min'
                    ),
                    'severity': 'warning',
                    'overlap_minutes': overlap_min,
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
            patient_dob='10/01/1980',
            visit_type='TEST',
            reason='Test Patient',
            duration_minutes=15,
            status='SCHEDULED',
            is_new_patient=False,
        )
        appointments.insert(0, test_appt)

    # Duration estimator
    duration_info = estimate_schedule_duration(current_user.id, appointments)

    # Anomaly analysis — pre-sort: warnings first, then info
    anomalies = analyze_schedule_anomalies(appointments)
    anomalies.sort(key=lambda a: 0 if a.get('severity') == 'warning' else 1)

    # Build set of appointment times involved in overlaps (for per-row badges)
    overlap_times = set()
    for a in anomalies:
        if a.get('type') == 'schedule_overlap':
            # Message format: "HH:MM and HH:MM — ..."
            parts = a['message'].split(' and ')
            if len(parts) >= 2:
                overlap_times.add(parts[0].strip())
                second = parts[1].split(' —')[0].strip() if ' —' in parts[1] else parts[1].strip()
                overlap_times.add(second)

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
    billing_opp_counts = {}
    try:
        from models.billing import BillingOpportunity
        billing_opportunities = (
            BillingOpportunity.query
            .filter_by(user_id=current_user.id, visit_date=view_date)
            .filter(BillingOpportunity.status.in_(['pending', 'partial']))
            .order_by(
                BillingOpportunity.expected_net_dollars.desc().nullslast(),
                BillingOpportunity.estimated_revenue.desc()
            )
            .all()
        )
        total_estimated_revenue = sum(
            o.estimated_revenue or 0 for o in billing_opportunities
        )
        # Per-patient billing opportunity counts for schedule badges
        import hashlib
        for appt in appointments:
            if appt.patient_mrn:
                mrn_hash = hashlib.sha256(str(appt.patient_mrn).encode()).hexdigest()
                count = sum(1 for o in billing_opportunities if o.patient_mrn_hash == mrn_hash)
                if count > 0:
                    billing_opp_counts[appt.patient_mrn] = count
    except Exception:
        pass

    # F25a: PDMP overdue check
    pdmp_overdue = []
    try:
        from routes.tools import get_overdue_pdmp_patients
        pdmp_overdue = get_overdue_pdmp_patients(current_user.id)
    except Exception:
        pass

    # Phase 10: Education drafts pending review
    education_draft_count = 0
    try:
        from models.message import DelayedMessage
        education_draft_count = DelayedMessage.query.filter(
            DelayedMessage.user_id == current_user.id,
            DelayedMessage.status == 'pending',
            DelayedMessage.message_content.contains('New Medication Education'),
        ).count()
    except Exception:
        pass

    # Phase 11: urgent_count for tier badge
    warning_count = sum(1 for a in anomalies if a.get('severity') == 'warning')
    high_billing_count = sum(
        1 for o in billing_opportunities
        if getattr(o, 'priority', 'medium') == 'high'
    )
    urgent_count = warning_count + high_billing_count + len(pdmp_overdue)

    # Phase 19.5: TCM urgent entries (deadline ≤1 business day)
    tcm_urgent = []
    try:
        from models.tcm import TCMWatchEntry
        tcm_active = TCMWatchEntry.query.filter_by(
            user_id=current_user.id, status='active'
        ).all()
        for te in tcm_active:
            deadline = None
            label = None
            if not te.two_day_contact_completed and te.two_day_deadline:
                deadline = te.two_day_deadline
                label = '2-day contact'
            elif not te.face_to_face_completed and te.seven_day_visit_deadline:
                deadline = te.seven_day_visit_deadline
                label = '7-day visit'
            if deadline and (deadline - today).days <= 1:
                tcm_urgent.append({
                    'id': te.id,
                    'patient': te.patient_mrn_hash[:8],
                    'facility': te.discharge_facility or '',
                    'deadline': deadline,
                    'label': label,
                    'days': (deadline - today).days,
                })
    except Exception:
        pass

    # Schedule display hours (user-configurable)
    schedule_start = int(current_user.get_pref('schedule_start_hour', 7))
    schedule_end = int(current_user.get_pref('schedule_end_hour', 19))

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
        billing_opp_counts=billing_opp_counts,
        urgent_count=urgent_count,
        overlap_times=overlap_times,
        pdmp_overdue=pdmp_overdue,
        education_draft_count=education_draft_count,
        tcm_urgent=tcm_urgent,
        schedule_start_hour=schedule_start,
        schedule_end_hour=schedule_end,
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
                'id': a.id,
                'time': a.appointment_time,
                'patient_name': a.patient_name,
                'patient_mrn': a.patient_mrn or '',
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
                'mrn_last4': r.mrn or '',
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
                    'mrn_last4': mrn,
                    'name': s.patient_name or 'Unknown',
                    'dob': s.patient_dob or '',
                    'last_seen': s.appointment_date.isoformat() if s.appointment_date else '',
                })

    return jsonify(results[:10])


# ======================================================================
# POST /api/schedule/add — manually add a patient to the schedule
# ======================================================================
@dashboard_bp.route('/api/schedule/add', methods=['POST'])
@login_required
def api_schedule_add():
    """
    Add a manual appointment to the schedule.
    Accepts JSON body with patient_name, patient_mrn, appointment_time (required)
    and optional fields: patient_dob, appointment_date, visit_type, duration_minutes,
    reason, note_template.
    """
    import re

    data = request.get_json(silent=True) or {}

    patient_name = (data.get('patient_name') or '').strip()
    patient_mrn = (data.get('patient_mrn') or '').strip()
    appointment_time = (data.get('appointment_time') or '').strip()

    # --- validation ---
    errors = []
    if not patient_name:
        errors.append('patient_name is required')
    if not patient_mrn:
        errors.append('patient_mrn is required')
    if not appointment_time:
        errors.append('appointment_time is required')
    elif not re.match(r'^\d{1,2}:\d{2}$', appointment_time):
        errors.append('appointment_time must be HH:MM format')

    if errors:
        return jsonify({'success': False, 'errors': errors}), 400

    # --- appointment date (default today) ---
    appt_date_str = (data.get('appointment_date') or '').strip()
    try:
        appt_date = (
            datetime.strptime(appt_date_str, '%Y-%m-%d').date()
            if appt_date_str else date.today()
        )
    except ValueError:
        return jsonify({'success': False, 'errors': ['Invalid appointment_date format (use YYYY-MM-DD)']}), 400

    duration = data.get('duration_minutes', 15)
    try:
        duration = int(duration)
        if duration < 1:
            raise ValueError
    except (TypeError, ValueError):
        duration = 15

    # --- duplicate detection (same MRN + time + date) ---
    existing = Schedule.query.filter_by(
        user_id=current_user.id,
        appointment_date=appt_date,
        appointment_time=appointment_time,
        patient_mrn=patient_mrn,
    ).first()
    if existing:
        return jsonify({
            'success': False,
            'errors': [f'Duplicate: {patient_mrn} already scheduled at {appointment_time} on {appt_date}']
        }), 409

    appt = Schedule(
        user_id=current_user.id,
        appointment_date=appt_date,
        appointment_time=appointment_time,
        patient_name=patient_name,
        patient_mrn=patient_mrn,
        patient_dob=(data.get('patient_dob') or '').strip(),
        visit_type=(data.get('visit_type') or 'Office Visit').strip(),
        duration_minutes=duration,
        reason=(data.get('reason') or '').strip(),
        comment=(data.get('note_template') or '').strip(),
        entered_by='manual',
        status='manual',
    )
    db.session.add(appt)
    db.session.commit()

    return jsonify({
        'success': True,
        'id': appt.id,
        'appointment': {
            'time': appt.appointment_time,
            'patient_name': appt.patient_name,
            'patient_mrn': appt.patient_mrn,
            'visit_type': appt.visit_type,
            'duration_minutes': appt.duration_minutes,
            'entered_by': appt.entered_by,
        },
    })


# ======================================================================
# DELETE /api/schedule/<id> — delete an appointment from the schedule
# ======================================================================
@dashboard_bp.route('/api/schedule/<int:schedule_id>', methods=['DELETE'])
@login_required
def api_schedule_delete(schedule_id):
    """
    Delete a schedule entry owned by the current user.
    Optional query param ?delete_prep=true also deletes prepped billing
    opportunities for this patient+date so a clean re-prep can happen later.
    """
    appt = Schedule.query.filter_by(
        id=schedule_id, user_id=current_user.id
    ).first()
    if not appt:
        return jsonify({'success': False, 'error': 'Appointment not found'}), 404

    delete_prep = request.args.get('delete_prep', 'false').lower() == 'true'

    # Optionally clear prepped billing opportunities for this patient+date
    if delete_prep and appt.patient_mrn:
        try:
            import hashlib
            from models.billing import BillingOpportunity
            mrn_hash = hashlib.sha256(appt.patient_mrn.encode()).hexdigest()[:64]
            BillingOpportunity.query.filter_by(
                user_id=current_user.id,
                patient_mrn_hash=mrn_hash,
                visit_date=appt.appointment_date,
            ).delete(synchronize_session=False)
        except Exception:
            pass  # Non-critical — appointment still gets removed

    db.session.delete(appt)
    db.session.commit()
    return jsonify({'success': True})


# ======================================================================
# PUT /api/schedule/<id>/move — move an appointment to a new time slot
# ======================================================================
@dashboard_bp.route('/api/schedule/<int:schedule_id>/move', methods=['PUT'])
@login_required
def api_schedule_move(schedule_id):
    """
    Move an appointment to a new time slot (drag-drop from schedule grid).
    Accepts JSON: {"new_time": "HH:MM"} in 24-hour format.
    """
    import re as _re

    appt = Schedule.query.filter_by(
        id=schedule_id, user_id=current_user.id
    ).first()
    if not appt:
        return jsonify({'success': False, 'error': 'Appointment not found'}), 404

    data = request.get_json(silent=True) or {}
    new_time = (data.get('new_time') or '').strip()

    # Validate HH:MM format
    if not _re.match(r'^\d{2}:\d{2}$', new_time):
        return jsonify({'success': False, 'error': 'Invalid time format'}), 400

    try:
        appt.appointment_time = new_time
        db.session.commit()
        return jsonify({'success': True, 'new_time': new_time})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in dashboard.api_schedule_move: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to move appointment'}), 500


# ======================================================================
# POST /api/schedule/preferences — save schedule display preferences
# ======================================================================
@dashboard_bp.route('/api/schedule/preferences', methods=['POST'])
@login_required
def api_schedule_preferences():
    """Save schedule start/end hour for the current user."""
    data = request.get_json(silent=True) or {}
    start = data.get('start_hour')
    end = data.get('end_hour')

    if start is not None:
        start = max(0, min(23, int(start)))
        current_user.set_pref('schedule_start_hour', start)
    if end is not None:
        end = max(1, min(24, int(end)))
        current_user.set_pref('schedule_end_hour', end)

    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in dashboard.api_schedule_preferences: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to save preferences'}), 500


# ======================================================================
# POST /api/schedule/parse-text — parse pasted schedule text into rows
# ======================================================================
@dashboard_bp.route('/api/schedule/parse-text', methods=['POST'])
@login_required
def api_schedule_parse_text():
    """
    Parse unstructured schedule text (from OCR, Snipping Tool, or manual typing)
    into structured appointment rows.  Returns a list of parsed entries with
    confidence indicators so the user can review before committing.
    """
    import re

    data = request.get_json(silent=True) or {}
    raw_text = (data.get('text') or '').strip()
    if not raw_text:
        return jsonify({'success': False, 'error': 'No text provided'}), 400

    # --- visit-type keyword map ---
    _VISIT_TYPE_MAP = {
        'NP': 'New Patient', 'NEW': 'New Patient', 'NEW PATIENT': 'New Patient',
        'FU': 'Follow Up', 'FOLLOW UP': 'Follow Up', 'FOLLOW-UP': 'Follow Up',
        'F/U': 'Follow Up',
        'PE': 'Physical', 'PHYSICAL': 'Physical', 'AWV': 'Physical',
        'ANNUAL': 'Physical', 'CPE': 'Physical',
        'AV': 'Office Visit', 'OV': 'Office Visit', 'OFFICE VISIT': 'Office Visit',
        'SV': 'Sick Visit', 'SICK': 'Sick Visit', 'SICK VISIT': 'Sick Visit',
        'TH': 'Telehealth', 'TELE': 'Telehealth', 'TELEHEALTH': 'Telehealth',
        'PROC': 'Procedure', 'PROCEDURE': 'Procedure',
    }

    # --- regex patterns ---
    time_pat = re.compile(
        r'(\d{1,2}:\d{2})\s*([AaPp][Mm])?'
    )
    mrn_pat = re.compile(
        r'\((\d{3,8})\)'          # parenthesized digits (54321)
        r'|(?<!\d)(\d{4,8})(?!\d)' # standalone 4-8 digit number
    )
    # Capitalized name pattern: "LAST, FIRST" or "FIRST LAST" or "Last, First M"
    name_pat = re.compile(
        r"([A-Z][A-Za-z'-]+),?\s+([A-Z][A-Za-z'-]+(?:\s+[A-Z]\.?)?)"
    )
    # Header lines to skip
    header_pat = re.compile(
        r'^\s*(?:time|patient|name|type|mrn|status|date|provider|reason)\s*$',
        re.IGNORECASE,
    )

    def _convert_to_24h(time_str, ampm):
        """Convert 12h time to HH:MM."""
        h, m = time_str.split(':')
        h = int(h)
        if ampm:
            ampm = ampm.upper()
            if ampm == 'PM' and h != 12:
                h += 12
            elif ampm == 'AM' and h == 12:
                h = 0
        return f'{h}:{m}'

    def _detect_visit_type(text):
        """Try to extract a visit type keyword from text."""
        upper = text.upper().strip()
        # Try longest matches first
        for kw in sorted(_VISIT_TYPE_MAP.keys(), key=len, reverse=True):
            if kw in upper:
                return _VISIT_TYPE_MAP[kw]
        return ''

    # --- normalise whitespace (tabs from spreadsheet paste, Windows line endings) ---
    raw_text = raw_text.replace('\t', '  ')
    lines = raw_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    parsed = []
    pending_entry = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line or header_pat.match(line):
            continue

        # Try to detect a time on this line
        tm = time_pat.search(line)
        if tm:
            # Flush any pending entry
            if pending_entry is not None:
                parsed.append(pending_entry)

            time_val = _convert_to_24h(tm.group(1), tm.group(2))
            remainder = line[:tm.start()] + line[tm.end():]

            # Extract MRN
            mrn_match = mrn_pat.search(remainder)
            mrn_val = ''
            if mrn_match:
                mrn_val = mrn_match.group(1) or mrn_match.group(2)
                remainder = remainder[:mrn_match.start()] + remainder[mrn_match.end():]

            # Extract patient name
            name_match = name_pat.search(remainder)
            name_val = ''
            if name_match:
                name_val = name_match.group(0).strip()
                remainder = remainder[:name_match.start()] + remainder[name_match.end():]

            # Extract visit type from remainder
            visit_type = _detect_visit_type(remainder)
            # Anything leftover is the reason / chief complaint
            reason = remainder.strip(' \t-–—|/')
            # Remove the matched visit type keyword from reason
            if visit_type:
                reason = re.sub(
                    re.escape(visit_type), '', reason, count=1, flags=re.IGNORECASE
                ).strip(' \t-–—|/')
                # Also remove the abbreviation that matched
                for kw, vt in _VISIT_TYPE_MAP.items():
                    if vt == visit_type:
                        reason = re.sub(
                            r'\b' + re.escape(kw) + r'\b', '', reason,
                            count=1, flags=re.IGNORECASE
                        ).strip(' \t-–—|/')

            # Confidence scoring
            fields_found = sum([bool(time_val), bool(name_val), bool(mrn_val)])
            confidence = 'high' if fields_found >= 3 else ('medium' if fields_found == 2 else 'low')

            pending_entry = {
                'time': time_val,
                'patient_name': name_val,
                'patient_mrn': mrn_val,
                'visit_type': visit_type or 'Office Visit',
                'reason': reason,
                'confidence': confidence,
            }
        elif pending_entry is not None:
            # Continuation line — append to previous entry's reason
            pending_entry['reason'] = (pending_entry['reason'] + ' ' + line).strip()
        else:
            # Line with no time and no pending entry — try as standalone
            mrn_match = mrn_pat.search(line)
            mrn_val = ''
            remainder = line
            if mrn_match:
                mrn_val = mrn_match.group(1) or mrn_match.group(2)
                remainder = line[:mrn_match.start()] + line[mrn_match.end():]

            name_match = name_pat.search(remainder)
            name_val = ''
            if name_match:
                name_val = name_match.group(0).strip()
                remainder = remainder[:name_match.start()] + remainder[name_match.end():]

            visit_type = _detect_visit_type(remainder)
            if name_val or mrn_val:
                parsed.append({
                    'time': '',
                    'patient_name': name_val,
                    'patient_mrn': mrn_val,
                    'visit_type': visit_type or 'Office Visit',
                    'reason': remainder.strip(' \t-–—|/'),
                    'confidence': 'low',
                })

    if pending_entry is not None:
        parsed.append(pending_entry)

    return jsonify({'success': True, 'parsed': parsed})


# ======================================================================
# POST /api/schedule/<id>/collect — trigger AC data collection
# ======================================================================
@dashboard_bp.route('/api/schedule/<int:schedule_id>/collect', methods=['POST'])
@login_required
def api_schedule_collect(schedule_id):
    """
    Start background data collection for a scheduled patient.
    Launches AC automation (open chart → export clinical summary XML →
    parse → store) in a background thread and returns immediately.
    """
    appt = Schedule.query.filter_by(
        id=schedule_id, user_id=current_user.id
    ).first()
    if not appt:
        return jsonify({'success': False, 'error': 'Appointment not found'}), 404
    if not appt.patient_mrn:
        return jsonify({'success': False, 'error': 'Patient has no MRN'}), 400

    # Check AC state before starting
    try:
        from agent.ac_window import get_ac_state
        state = get_ac_state()
    except Exception:
        state = 'not_running'

    if state == 'not_running':
        return jsonify({'success': False, 'error': 'Amazing Charts is not running'}), 400
    if state == 'login_screen':
        return jsonify({'success': False, 'error': 'Amazing Charts is on the login screen — please log in first'}), 400

    # Prevent duplicate jobs
    existing = _collect_jobs.get(schedule_id)
    if existing and existing.get('status') == 'running':
        return jsonify({'success': False, 'error': 'Collection already in progress'}), 409

    _collect_jobs[schedule_id] = {
        'status': 'running',
        'message': 'Starting data collection...',
        'started_at': datetime.now(timezone.utc).isoformat(),
    }

    # Capture values needed by the background thread
    user_id = current_user.id
    mrn = appt.patient_mrn
    patient_name = appt.patient_name or ''
    app = current_app._get_current_object()

    def _collect_worker():
        try:
            from agent.ac_window import get_ac_state, focus_ac_window, get_active_patient_mrn
            from agent.clinical_summary_parser import (
                open_patient_chart, export_clinical_summary,
                parse_clinical_summary, store_parsed_summary,
            )

            # Bring AC to foreground
            _collect_jobs[schedule_id]['message'] = 'Bringing Amazing Charts to foreground...'
            focus_ac_window()
            import time
            time.sleep(0.5)

            # Check if patient already open
            current_mrn = get_active_patient_mrn()
            if current_mrn and str(current_mrn).strip() == str(mrn).strip():
                _collect_jobs[schedule_id]['message'] = 'Patient already open — skipping chart open...'
            else:
                _collect_jobs[schedule_id]['message'] = 'Opening patient chart...'
                success = open_patient_chart(mrn, patient_name)
                if not success:
                    _collect_jobs[schedule_id]['status'] = 'error'
                    _collect_jobs[schedule_id]['message'] = 'Failed to open patient chart in Amazing Charts'
                    return
                time.sleep(1)

            _collect_jobs[schedule_id]['message'] = 'Exporting clinical summary...'
            xml_path = export_clinical_summary(mrn)
            if not xml_path:
                _collect_jobs[schedule_id]['status'] = 'error'
                _collect_jobs[schedule_id]['message'] = 'Failed to export clinical summary — check AC is on the correct screen'
                return

            _collect_jobs[schedule_id]['message'] = 'Parsing XML data...'
            parsed = parse_clinical_summary(xml_path)
            if not parsed:
                _collect_jobs[schedule_id]['status'] = 'error'
                _collect_jobs[schedule_id]['message'] = 'Failed to parse clinical summary XML'
                return

            _collect_jobs[schedule_id]['message'] = 'Storing patient data...'
            with app.app_context():
                store_parsed_summary(user_id, mrn, parsed)

            _collect_jobs[schedule_id]['status'] = 'complete'
            _collect_jobs[schedule_id]['message'] = 'Data collected successfully'

        except Exception as e:
            _collect_jobs[schedule_id]['status'] = 'error'
            _collect_jobs[schedule_id]['message'] = f'Collection failed: {e}'

    thread = Thread(target=_collect_worker, daemon=True)
    thread.start()

    return jsonify({'success': True, 'status': 'started', 'schedule_id': schedule_id})


# ======================================================================
# GET /api/schedule/<id>/collect-status — poll collection progress
# ======================================================================
@dashboard_bp.route('/api/schedule/<int:schedule_id>/collect-status')
@login_required
def api_schedule_collect_status(schedule_id):
    """Return the current data collection status for a schedule entry."""
    job = _collect_jobs.get(schedule_id)
    if not job:
        return jsonify({'status': 'not_started', 'message': ''})
    return jsonify({
        'status': job.get('status', 'not_started'),
        'message': job.get('message', ''),
    })

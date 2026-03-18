"""
NP Companion — Visit Timer Routes

File location: np-companion/routes/timer.py

Provides:
  GET  /timer                     — Timer dashboard (F12)
  GET  /api/timer-status          — JSON polling for live timer
  POST /timer/manual              — Manual session entry
  POST /timer/<id>/edit           — Edit manual entry
  POST /timer/<id>/delete         — Delete manual entry
  POST /timer/<id>/note           — Billing notes
  POST /timer/<id>/annotate       — Billing level annotation (F12)
  POST /timer/<id>/flag-complex   — Complex visit flag (F12b)
  POST /timer/face/start          — Start face-to-face timer (F12)
  POST /timer/face/stop           — Stop face-to-face timer (F12)
  POST /timer/face/room-toggle    — Room widget toggle (F12c, no auth)
  GET  /timer/room-widget         — Room widget page (F12c, no auth)
  GET  /timer/export              — CSV export (F12)
  GET  /timer/report/<date>       — Day summary JSON (F12)
  GET  /billing/log               — Billing audit log (F14)
  GET  /billing/log/export        — Billing log print/PDF export (F14)
  POST /billing/<id>/add-rationale — Add billing rationale (F14)
  GET  /billing/em-calculator     — E&M calculator widget (F14a)
  POST /billing/em-calculator     — E&M level calculation (F14a)
  POST /billing/em-calculate-json — E&M calculator JSON API (F14a inline)
  GET  /billing/monthly-report    — Monthly billing report (F14c)

Features: F6c, F12, F12a, F12b, F12c, F14, F14a, F14b, F14c
"""

import csv
import io
import json
import os
from datetime import date, datetime, timezone, timedelta

from flask import (
    Blueprint, render_template, request, jsonify,
    flash, redirect, url_for, Response,
)
from flask_login import login_required, current_user

from models import db
from models.timelog import TimeLog
from models.schedule import Schedule

timer_bp = Blueprint('timer', __name__)

# ---- Billing level choices (used in template + validation) ---------------
BILLING_LEVELS = [
    '99211', '99212', '99213', '99214', '99215',
    '99201', '99202', '99203', '99204', '99205',
    'AWV',
]

VISIT_TYPES = [
    ('office_visit', 'Office Visit'),
    ('followup', 'Follow-up'),
    ('physical', 'Physical'),
    ('procedure', 'Procedure'),
    ('telehealth', 'Telehealth'),
    ('phone_call', 'Phone Call'),
    ('awv', 'AWV'),
    ('other', 'Other'),
]


# --------------------------------------------------------------------------
#  F12a — Auto-tag visit type from Schedule
# --------------------------------------------------------------------------
def auto_tag_visit_type(user_id, mrn):
    """Look up today's schedule for a matching MRN → return (visit_type, 'auto') or ('', '')."""
    today = date.today()
    appt = (
        Schedule.query
        .filter_by(user_id=user_id, appointment_date=today, patient_mrn=mrn)
        .first()
    )
    if appt and appt.visit_type:
        return appt.visit_type, 'auto'
    return '', ''


# --------------------------------------------------------------------------
#  Main page
# --------------------------------------------------------------------------
@timer_bp.route('/timer')
@login_required
def index():
    """Visit timer dashboard — active session, today's history, daily summary."""
    today = date.today()
    start_of_day = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)

    sessions = (
        TimeLog.query
        .filter_by(user_id=current_user.id)
        .filter(TimeLog.session_start >= start_of_day)
        .order_by(TimeLog.session_start.desc())
        .all()
    )

    active = (
        TimeLog.query
        .filter_by(user_id=current_user.id, session_end=None)
        .order_by(TimeLog.session_start.desc())
        .first()
    )

    # Daily summary stats
    completed = [s for s in sessions if s.session_end]
    total_duration = sum(s.duration_seconds or 0 for s in completed)
    total_f2f = sum(s.face_to_face_seconds or 0 for s in completed)
    avg_duration = (total_duration // len(completed)) if completed else 0
    complex_count = sum(1 for s in completed if s.is_complex)

    # E&M distribution for bar chart
    em_dist = {}
    for s in completed:
        lvl = s.billed_level or 'Unbilled'
        em_dist[lvl] = em_dist.get(lvl, 0) + 1

    return render_template(
        'timer.html',
        sessions=sessions,
        active_session=active,
        billing_levels=BILLING_LEVELS,
        visit_types=VISIT_TYPES,
        total_duration=total_duration,
        total_f2f=total_f2f,
        avg_duration=avg_duration,
        complex_count=complex_count,
        session_count=len(completed),
        em_dist=em_dist,
    )


# --------------------------------------------------------------------------
#  JSON polling
# --------------------------------------------------------------------------
@timer_bp.route('/api/timer-status')
@login_required
def timer_status():
    """JSON endpoint for polling timer state from the UI."""
    active = (
        TimeLog.query
        .filter_by(user_id=current_user.id, session_end=None)
        .order_by(TimeLog.session_start.desc())
        .first()
    )
    if active:
        now = datetime.now(timezone.utc)
        duration = int((now - active.session_start).total_seconds())
        idle = active.total_idle_seconds or 0
        f2f_active = (
            active.face_to_face_start is not None
            and active.face_to_face_end is None
        )
        f2f_secs = active.face_to_face_seconds or 0
        if f2f_active and active.face_to_face_start:
            f2f_secs += int((now - active.face_to_face_start).total_seconds())
        return jsonify({
            'active_mrn': '****' + active.mrn[-4:] if active.mrn and len(active.mrn) >= 4 else active.mrn,
            'session_start': active.session_start.isoformat(),
            'duration_seconds': duration,
            'is_idle': idle > 0 and (duration - idle) < 10,
            'f2f_active': f2f_active,
            'f2f_seconds': f2f_secs,
            'session_id': active.id,
        })
    return jsonify({
        'active_mrn': None,
        'session_start': None,
        'duration_seconds': 0,
        'is_idle': False,
        'f2f_active': False,
        'f2f_seconds': 0,
        'session_id': None,
    })


# --------------------------------------------------------------------------
#  Manual entry CRUD
# --------------------------------------------------------------------------
@timer_bp.route('/timer/manual', methods=['POST'])
@login_required
def manual_entry():
    """Create a manual TimeLog entry."""
    mrn = request.form.get('mrn', '').strip()
    start_str = request.form.get('session_start', '').strip()
    end_str = request.form.get('session_end', '').strip()
    visit_type = request.form.get('visit_type', '').strip()
    notes = request.form.get('notes', '').strip()

    if not mrn or not start_str or not end_str:
        flash('MRN, start time, and end time are required.', 'error')
        return redirect(url_for('timer.index'))

    try:
        session_start = datetime.fromisoformat(start_str).replace(tzinfo=timezone.utc)
        session_end = datetime.fromisoformat(end_str).replace(tzinfo=timezone.utc)
    except ValueError:
        flash('Invalid date format.', 'error')
        return redirect(url_for('timer.index'))

    duration = int((session_end - session_start).total_seconds())
    if duration <= 0:
        flash('End time must be after start time.', 'error')
        return redirect(url_for('timer.index'))

    entry = TimeLog(
        user_id=current_user.id,
        mrn=mrn,
        session_start=session_start,
        session_end=session_end,
        duration_seconds=duration,
        visit_type=visit_type,
        visit_type_source='manual',
        billing_notes=notes,
        manual_entry=True,
    )
    db.session.add(entry)
    db.session.commit()
    flash('Manual session recorded.', 'success')
    return redirect(url_for('timer.index'))


@timer_bp.route('/timer/<int:entry_id>/edit', methods=['POST'])
@login_required
def edit_entry(entry_id):
    """Edit a manual TimeLog entry (manual entries only)."""
    entry = TimeLog.query.filter_by(id=entry_id, user_id=current_user.id).first()
    if not entry:
        flash('Session not found.', 'error')
        return redirect(url_for('timer.index'))

    if not entry.manual_entry:
        flash('Only manual entries can be fully edited.', 'error')
        return redirect(url_for('timer.index'))

    mrn = request.form.get('mrn', '').strip()
    start_str = request.form.get('session_start', '').strip()
    end_str = request.form.get('session_end', '').strip()
    visit_type = request.form.get('visit_type', '').strip()
    notes = request.form.get('notes', '').strip()

    if mrn:
        entry.mrn = mrn
    if start_str:
        try:
            entry.session_start = datetime.fromisoformat(start_str).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    if end_str:
        try:
            entry.session_end = datetime.fromisoformat(end_str).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    if entry.session_start and entry.session_end:
        entry.duration_seconds = int((entry.session_end - entry.session_start).total_seconds())
    entry.visit_type = visit_type
    entry.visit_type_source = 'manual'
    entry.billing_notes = notes
    db.session.commit()
    flash('Session updated.', 'success')
    return redirect(url_for('timer.index'))


@timer_bp.route('/timer/<int:entry_id>/delete', methods=['POST'])
@login_required
def delete_entry(entry_id):
    """Delete a manual TimeLog entry (manual entries only)."""
    entry = TimeLog.query.filter_by(id=entry_id, user_id=current_user.id).first()
    if not entry:
        flash('Session not found.', 'error')
        return redirect(url_for('timer.index'))

    if not entry.manual_entry:
        flash('Only manual entries can be deleted.', 'error')
        return redirect(url_for('timer.index'))

    db.session.delete(entry)
    db.session.commit()
    flash('Session deleted.', 'success')
    return redirect(url_for('timer.index'))


@timer_bp.route('/timer/<int:entry_id>/note', methods=['POST'])
@login_required
def add_note(entry_id):
    """Add or update billing notes on any TimeLog entry."""
    entry = TimeLog.query.filter_by(id=entry_id, user_id=current_user.id).first()
    if not entry:
        flash('Session not found.', 'error')
        return redirect(url_for('timer.index'))

    notes = request.form.get('notes', '').strip()
    entry.billing_notes = notes
    db.session.commit()
    flash('Notes updated.', 'success')
    return redirect(url_for('timer.index'))


# --------------------------------------------------------------------------
#  F12 — Billing level annotation
# --------------------------------------------------------------------------
@timer_bp.route('/timer/<int:entry_id>/annotate', methods=['POST'])
@login_required
def annotate(entry_id):
    """Set billing level on a session."""
    entry = TimeLog.query.filter_by(id=entry_id, user_id=current_user.id).first()
    if not entry:
        flash('Session not found.', 'error')
        return redirect(url_for('timer.index'))

    level = request.form.get('billed_level', '').strip()
    if level and level not in BILLING_LEVELS:
        flash('Invalid billing level.', 'error')
        return redirect(url_for('timer.index'))

    entry.billed_level = level
    db.session.commit()
    flash('Billing level saved.', 'success')
    return redirect(url_for('timer.index'))


# --------------------------------------------------------------------------
#  F12b — Complex visit flag
# --------------------------------------------------------------------------
@timer_bp.route('/timer/<int:entry_id>/flag-complex', methods=['POST'])
@login_required
def flag_complex(entry_id):
    """Toggle complex visit flag and optional notes."""
    entry = TimeLog.query.filter_by(id=entry_id, user_id=current_user.id).first()
    if not entry:
        flash('Session not found.', 'error')
        return redirect(url_for('timer.index'))

    entry.is_complex = not entry.is_complex
    if entry.is_complex:
        entry.complexity_notes = request.form.get('complexity_notes', '').strip()
    else:
        entry.complexity_notes = ''
    db.session.commit()
    flash('Complex flag updated.', 'success')
    return redirect(url_for('timer.index'))


# --------------------------------------------------------------------------
#  F12 — Face-to-face start / stop
# --------------------------------------------------------------------------
@timer_bp.route('/timer/face/start', methods=['POST'])
@login_required
def face_start():
    """Start face-to-face timer on active session."""
    active = (
        TimeLog.query
        .filter_by(user_id=current_user.id, session_end=None)
        .order_by(TimeLog.session_start.desc())
        .first()
    )
    if not active:
        flash('No active session.', 'error')
        return redirect(url_for('timer.index'))

    if active.face_to_face_start and not active.face_to_face_end:
        flash('Face-to-face already running.', 'warning')
        return redirect(url_for('timer.index'))

    active.face_to_face_start = datetime.now(timezone.utc)
    active.face_to_face_end = None
    db.session.commit()
    flash('Face-to-face timer started.', 'success')
    return redirect(url_for('timer.index'))


@timer_bp.route('/timer/face/stop', methods=['POST'])
@login_required
def face_stop():
    """Stop face-to-face timer on active session."""
    active = (
        TimeLog.query
        .filter_by(user_id=current_user.id, session_end=None)
        .order_by(TimeLog.session_start.desc())
        .first()
    )
    if not active:
        flash('No active session.', 'error')
        return redirect(url_for('timer.index'))

    if not active.face_to_face_start or active.face_to_face_end:
        flash('Face-to-face not currently running.', 'warning')
        return redirect(url_for('timer.index'))

    active.face_to_face_end = datetime.now(timezone.utc)
    elapsed = int((active.face_to_face_end - active.face_to_face_start).total_seconds())
    active.face_to_face_seconds = (active.face_to_face_seconds or 0) + elapsed
    db.session.commit()
    flash('Face-to-face timer stopped.', 'success')
    return redirect(url_for('timer.index'))


# --------------------------------------------------------------------------
#  F12c — Room widget (NO auth)
# --------------------------------------------------------------------------
@timer_bp.route('/timer/room-widget')
def room_widget():
    """Room computer face-to-face widget — no login required."""
    # Read current provider from active_user.json
    active_file = os.path.join('data', 'active_user.json')
    provider_name = ''
    f2f_active = False
    if os.path.exists(active_file):
        try:
            with open(active_file, 'r') as f:
                data = json.load(f)
            user_id = data.get('user_id')
            provider_name = data.get('username', '')
            if user_id:
                active = (
                    TimeLog.query
                    .filter_by(user_id=user_id, session_end=None)
                    .order_by(TimeLog.session_start.desc())
                    .first()
                )
                if active and active.face_to_face_start and not active.face_to_face_end:
                    f2f_active = True
        except (json.JSONDecodeError, OSError):
            pass
    return render_template(
        'timer_room_widget.html',
        provider_name=provider_name,
        f2f_active=f2f_active,
    )


@timer_bp.route('/timer/face/room-toggle', methods=['POST'])
def room_toggle():
    """Room widget toggle — reads active_user.json, no auth."""
    active_file = os.path.join('data', 'active_user.json')
    if not os.path.exists(active_file):
        return jsonify({'error': 'No active provider'}), 404

    try:
        with open(active_file, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return jsonify({'error': 'Cannot read active user'}), 500

    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'No user_id in active_user.json'}), 404

    active = (
        TimeLog.query
        .filter_by(user_id=user_id, session_end=None)
        .order_by(TimeLog.session_start.desc())
        .first()
    )
    if not active:
        return jsonify({'error': 'No active session'}), 404

    now = datetime.now(timezone.utc)
    if active.face_to_face_start and not active.face_to_face_end:
        # Stop F2F
        active.face_to_face_end = now
        elapsed = int((now - active.face_to_face_start).total_seconds())
        active.face_to_face_seconds = (active.face_to_face_seconds or 0) + elapsed
        db.session.commit()
        return jsonify({'f2f_active': False, 'action': 'stopped'})
    else:
        # Start F2F
        active.face_to_face_start = now
        active.face_to_face_end = None
        db.session.commit()
        return jsonify({'f2f_active': True, 'action': 'started'})


# --------------------------------------------------------------------------
#  F12 — CSV export
# --------------------------------------------------------------------------
@timer_bp.route('/timer/export')
@login_required
def export_csv():
    """Export today's sessions as CSV."""
    today = date.today()
    start_of_day = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)

    sessions = (
        TimeLog.query
        .filter_by(user_id=current_user.id)
        .filter(TimeLog.session_start >= start_of_day)
        .order_by(TimeLog.session_start.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'MRN_Last4', 'Start', 'End', 'Duration_Min',
        'Visit_Type', 'F2F_Min', 'Billing_Level',
        'Complex', 'Notes',
    ])
    for s in sessions:
        mrn4 = s.mrn[-4:] if s.mrn and len(s.mrn) >= 4 else s.mrn
        writer.writerow([
            mrn4,
            s.session_start.strftime('%H:%M') if s.session_start else '',
            s.session_end.strftime('%H:%M') if s.session_end else 'Active',
            round((s.duration_seconds or 0) / 60, 1),
            s.visit_type or '',
            round((s.face_to_face_seconds or 0) / 60, 1),
            s.billed_level or '',
            'Yes' if s.is_complex else '',
            s.billing_notes or '',
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=timer_{today.isoformat()}.csv',
        },
    )


# --------------------------------------------------------------------------
#  F12 — Day report (JSON)
# --------------------------------------------------------------------------
@timer_bp.route('/timer/report/<string:report_date>')
@login_required
def day_report(report_date):
    """Day summary JSON for the given date (YYYY-MM-DD)."""
    try:
        rdate = date.fromisoformat(report_date)
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    start = datetime(rdate.year, rdate.month, rdate.day, tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    sessions = (
        TimeLog.query
        .filter_by(user_id=current_user.id)
        .filter(TimeLog.session_start >= start, TimeLog.session_start < end)
        .order_by(TimeLog.session_start.asc())
        .all()
    )

    completed = [s for s in sessions if s.session_end]
    em_dist = {}
    for s in completed:
        lvl = s.billed_level or 'Unbilled'
        em_dist[lvl] = em_dist.get(lvl, 0) + 1

    return jsonify({
        'date': rdate.isoformat(),
        'total_sessions': len(completed),
        'total_duration_min': round(sum(s.duration_seconds or 0 for s in completed) / 60, 1),
        'total_f2f_min': round(sum(s.face_to_face_seconds or 0 for s in completed) / 60, 1),
        'avg_duration_min': round(
            (sum(s.duration_seconds or 0 for s in completed) / len(completed) / 60) if completed else 0, 1
        ),
        'complex_count': sum(1 for s in completed if s.is_complex),
        'em_distribution': em_dist,
    })


# ==========================================================================
#  F14 — Billing Audit Log
# ==========================================================================

# RVU lookup table (2024 Medicare RBRVS, approximate)
RVU_TABLE = {
    '99211': 0.18, '99212': 0.70, '99213': 1.30, '99214': 1.92, '99215': 2.80,
    '99201': 0.48, '99202': 0.93, '99203': 1.60, '99204': 2.60, '99205': 3.50,
    'AWV-Initial': 2.43, 'AWV-Subsequent': 1.50,
}

# F14b — Expected time ranges per E&M level (min chart time)
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


@timer_bp.route('/billing/log')
@login_required
def billing_log():
    """F14 — Billing audit log with filters."""
    # Date filters
    start_str = request.args.get('start', '')
    end_str = request.args.get('end', '')
    level_filter = request.args.get('level', '')
    anomaly_filter = request.args.get('anomaly', '')

    query = (
        TimeLog.query
        .filter_by(user_id=current_user.id)
        .filter(TimeLog.session_end.isnot(None))
    )

    if start_str:
        try:
            start_dt = datetime.fromisoformat(start_str)
            query = query.filter(TimeLog.session_start >= start_dt)
        except ValueError:
            pass
    if end_str:
        try:
            end_dt = datetime.fromisoformat(end_str) + timedelta(days=1)
            query = query.filter(TimeLog.session_start < end_dt)
        except ValueError:
            pass
    if level_filter:
        query = query.filter(TimeLog.billed_level == level_filter)

    sessions = query.order_by(TimeLog.session_start.desc()).all()

    # F14b — Annotate each session with anomaly flags
    entries = []
    for s in sessions:
        anomalies = _detect_anomalies(s)
        if anomaly_filter == 'flagged' and not anomalies:
            continue
        if anomaly_filter == 'clean' and anomalies:
            continue
        entries.append({
            'session': s,
            'anomalies': anomalies,
            'rvu': RVU_TABLE.get(s.billed_level or '', 0),
        })

    # Unique billing levels for filter dropdown
    all_levels = sorted(set(s.billed_level for s in sessions if s.billed_level))

    return render_template(
        'billing_log.html',
        entries=entries,
        all_levels=all_levels,
        start=start_str,
        end=end_str,
        level_filter=level_filter,
        anomaly_filter=anomaly_filter,
        anomaly_guidance=ANOMALY_GUIDANCE,
    )


@timer_bp.route('/billing/log/export')
@login_required
def billing_log_export():
    """F14 — Print-friendly billing log export page."""
    start_str = request.args.get('start', '')
    end_str = request.args.get('end', '')

    query = (
        TimeLog.query
        .filter_by(user_id=current_user.id)
        .filter(TimeLog.session_end.isnot(None))
    )

    if start_str:
        try:
            query = query.filter(TimeLog.session_start >= datetime.fromisoformat(start_str))
        except ValueError:
            pass
    if end_str:
        try:
            query = query.filter(TimeLog.session_start < datetime.fromisoformat(end_str) + timedelta(days=1))
        except ValueError:
            pass

    sessions = query.order_by(TimeLog.session_start.asc()).all()

    entries = []
    for s in sessions:
        entries.append({
            'session': s,
            'anomalies': _detect_anomalies(s),
            'rvu': RVU_TABLE.get(s.billed_level or '', 0),
        })

    return render_template('billing_log_export.html', entries=entries, start=start_str, end=end_str)


@timer_bp.route('/billing/<int:session_id>/add-rationale', methods=['POST'])
@login_required
def add_rationale(session_id):
    """F14 — Add billing rationale to a session."""
    session = TimeLog.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    rationale = request.form.get('rationale', '').strip()
    if rationale:
        existing = session.billing_notes or ''
        separator = '\n---\n' if existing else ''
        session.billing_notes = existing + separator + rationale
        db.session.commit()
    return redirect(url_for('timer.billing_log'))


# --------------------------------------------------------------------------
#  F14a — E&M Calculator Widget
# --------------------------------------------------------------------------

# 2023 AMA MDM complexity levels
MDM_LEVELS = {
    'straightforward': '99211',
    'low':             '99213',
    'moderate':        '99214',
    'high':            '99215',
}

# Time-based E&M (total physician time on encounter date)
TIME_BASED_EM = [
    (75, '99215'),
    (55, '99215'),
    (40, '99214'),
    (30, '99213'),
    (20, '99212'),
    (10, '99211'),
    (0,  '99211'),
]


def _em_from_mdm(complexity):
    """Return (code, rvu) for an MDM complexity level."""
    code = MDM_LEVELS.get(complexity, '99213')
    return code, RVU_TABLE.get(code, 0)


def _em_from_time(minutes):
    """Return (code, rvu) for total physician time."""
    code = '99211'
    for threshold, c in TIME_BASED_EM:
        if minutes >= threshold:
            code = c
            break
    return code, RVU_TABLE.get(code, 0)


@timer_bp.route('/billing/em-calculator')
@login_required
def em_calculator():
    """F14a — E&M calculator page."""
    return render_template('billing_em_calculator.html')


@timer_bp.route('/billing/em-calculator', methods=['POST'])
@login_required
def em_calculate():
    """F14a — Calculate suggested E&M level (higher of MDM vs time)."""
    complexity = request.form.get('mdm_level', 'low')
    minutes = int(request.form.get('total_minutes', 0) or 0)

    mdm_code, mdm_rvu = _em_from_mdm(complexity)
    time_code, time_rvu = _em_from_time(minutes)

    # Pick whichever method supports a higher level
    if time_rvu > mdm_rvu:
        winner = 'Time-Based'
        suggested_code, suggested_rvu = time_code, time_rvu
    else:
        winner = 'MDM'
        suggested_code, suggested_rvu = mdm_code, mdm_rvu

    result = {
        'method': winner,
        'suggested_code': suggested_code,
        'rvu': suggested_rvu,
        'mdm_code': mdm_code,
        'mdm_rvu': mdm_rvu,
        'mdm_input': complexity.title(),
        'time_code': time_code,
        'time_rvu': time_rvu,
        'time_input': f'{minutes} minutes',
    }
    return render_template('billing_em_calculator.html', result=result)


@timer_bp.route('/billing/em-calculate-json', methods=['POST'])
@login_required
def em_calculate_json():
    """F14a — JSON API for inline E&M calculator widget in timer page."""
    data = request.get_json(silent=True) or {}
    complexity = data.get('mdm_level', 'low')
    minutes = int(data.get('total_minutes', 0) or 0)

    mdm_code, mdm_rvu = _em_from_mdm(complexity)
    time_code, time_rvu = _em_from_time(minutes)

    if time_rvu > mdm_rvu:
        winner, suggested_code, suggested_rvu = 'Time-Based', time_code, time_rvu
    else:
        winner, suggested_code, suggested_rvu = 'MDM', mdm_code, mdm_rvu

    return jsonify({
        'method': winner,
        'suggested_code': suggested_code,
        'rvu': suggested_rvu,
        'mdm_code': mdm_code,
        'mdm_rvu': mdm_rvu,
        'time_code': time_code,
        'time_rvu': time_rvu,
    })


# --------------------------------------------------------------------------
#  F14b — Billing Anomaly Detector
# --------------------------------------------------------------------------

# Ordered list of E&M levels from lowest to highest for upcode detection
_EM_LEVEL_ORDER = ['99211', '99212', '99213', '99214', '99215']
_EM_NEW_LEVEL_ORDER = ['99201', '99202', '99203', '99204', '99205']

# Resolution guidance per anomaly type
ANOMALY_GUIDANCE = {
    'time_low': 'Review chart to ensure all time is documented (charting, care coordination, counseling). If time is accurate, consider whether a lower level better matches documentation.',
    'time_high': 'Documented time exceeds typical range. Ensure all time is justified and documented. Consider whether a higher level is supported by documentation.',
    'upcode': 'Your documented time meets or exceeds the minimum for a higher E&M level. Review your MDM documentation to see if the higher level is supportable.',
    'f2f_low': 'Low face-to-face ratio may indicate most time was spent on non-F2F activities. Ensure your documentation reflects the clinical necessity of the E&M level chosen.',
    'no_complexity': 'High-level codes (99215/99205) typically require complexity documentation. Add complexity notes explaining why this visit required high-level MDM.',
    'no_level': 'Assign a billing level to complete the encounter record for audit purposes.',
}


def _detect_anomalies(session):
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
            warnings.append({'msg': f'Chart time ({chart_min:.0f}min) very low for {level} (expected {low}-{high}min)', 'type': 'time_low'})
        elif chart_min > high * 1.5:
            warnings.append({'msg': f'Chart time ({chart_min:.0f}min) very high for {level} (expected {low}-{high}min)', 'type': 'time_high'})

    # F14b upcode suggestion — time supports a higher level
    level_list = _EM_NEW_LEVEL_ORDER if level.startswith('992') and level in _EM_NEW_LEVEL_ORDER else _EM_LEVEL_ORDER
    if level in level_list:
        idx = level_list.index(level)
        if idx < len(level_list) - 1:
            next_level = level_list[idx + 1]
            next_expected = EM_TIME_RANGES.get(next_level)
            if next_expected and chart_min >= next_expected[0]:
                warnings.append({'msg': f'Consider higher level based on time ({chart_min:.0f}min meets {next_level} threshold of {next_expected[0]}min)', 'type': 'upcode'})

    # F2F ratio check — if F2F is less than 30% of chart time on levels >=99213
    if level in ('99213', '99214', '99215', '99203', '99204', '99205'):
        if chart_min > 0 and f2f_min / chart_min < 0.3:
            warnings.append({'msg': f'Low F2F ratio ({f2f_min:.0f}/{chart_min:.0f}min = {f2f_min/chart_min*100:.0f}%)', 'type': 'f2f_low'})

    # High-level code without complexity flag
    if level in ('99215', '99205') and not session.is_complex:
        warnings.append({'msg': f'{level} billed without complexity flag', 'type': 'no_complexity'})

    return warnings


# --------------------------------------------------------------------------
#  F14c — Monthly Billing Report
# --------------------------------------------------------------------------

# New patient vs established patient code sets
_NEW_PATIENT_CODES = {'99201', '99202', '99203', '99204', '99205'}
_ESTABLISHED_CODES = {'99211', '99212', '99213', '99214', '99215'}


def _monthly_stats(sessions):
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

    anomaly_count = sum(1 for s in sessions if _detect_anomalies(s))

    weekly = {}
    for s in sessions:
        _, wk, _ = s.session_start.isocalendar()
        wk_key = f'Week {wk}'
        if wk_key not in weekly:
            weekly[wk_key] = {'patients': 0, 'rvu': 0}
        weekly[wk_key]['patients'] += 1
        weekly[wk_key]['rvu'] = round(weekly[wk_key]['rvu'] + RVU_TABLE.get(s.billed_level or '', 0), 2)

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


@timer_bp.route('/billing/monthly-report')
@login_required
def monthly_report():
    """F14c — Monthly billing summary with RVU totals, new/estab split, prior month comparison."""
    month_str = request.args.get('month', '')
    if month_str:
        try:
            year, month = month_str.split('-')
            year, month = int(year), int(month)
        except (ValueError, AttributeError):
            year, month = date.today().year, date.today().month
    else:
        year, month = date.today().year, date.today().month

    # Current month range
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

    # Prior month range
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    prev_start = datetime(prev_year, prev_month, 1, tzinfo=timezone.utc)
    prev_end = start  # start of current month = end of prior month

    sessions = (
        TimeLog.query
        .filter_by(user_id=current_user.id)
        .filter(TimeLog.session_start >= start, TimeLog.session_start < end,
                TimeLog.session_end.isnot(None))
        .order_by(TimeLog.session_start.asc())
        .all()
    )

    prev_sessions = (
        TimeLog.query
        .filter_by(user_id=current_user.id)
        .filter(TimeLog.session_start >= prev_start, TimeLog.session_start < prev_end,
                TimeLog.session_end.isnot(None))
        .all()
    )

    stats = _monthly_stats(sessions)
    prev_stats = _monthly_stats(prev_sessions) if prev_sessions else None

    return render_template(
        'billing_monthly.html',
        year=year,
        month=month,
        prev_year=prev_year,
        prev_month=prev_month,
        **stats,
        prev=prev_stats,
    )

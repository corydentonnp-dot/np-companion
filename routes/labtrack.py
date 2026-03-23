"""
CareCompanion — Lab Value Tracker Routes

Feature 11:  Lab tracking with custom thresholds and trend charts.
Feature 11a: Chart.js trend visualization.
Feature 11b: Custom alert thresholds per patient.
Feature 11c: Overdue lab notification (scheduled job).
Feature 11d: Lab panel grouping.
"""

import json
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from models import db
from models.labtrack import LabTrack, LabResult, LabPanel, STANDARD_PANELS
from utils.feature_gates import require_feature

labtrack_bp = Blueprint('labtrack', __name__)


# ======================================================================
# GET /api/lab-cache — Return lab reference data for autocomplete
# ======================================================================
@labtrack_bp.route('/api/lab-cache')
@login_required
def lab_cache():
    import os
    cache_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'lab_cache.json')
    try:
        with open(cache_path, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception:
        return jsonify({'labs': [], 'panels': {}, 'refs': {}})


# ======================================================================
# POST /api/lab-cache/update — Update a lab's abbreviation and/or ref
# ======================================================================
@labtrack_bp.route('/api/lab-cache/update', methods=['POST'])
@login_required
def lab_cache_update():
    import os
    cache_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'lab_cache.json')
    try:
        lab_name = request.form.get('lab_name', '').strip()
        if not lab_name:
            return jsonify({'success': False, 'error': 'Lab name required'}), 400

        with open(cache_path, 'r') as f:
            data = json.load(f)

        # Update abbreviation in labs array
        new_abbr = request.form.get('abbr', '').strip()
        if new_abbr:
            for lab in data.get('labs', []):
                if lab['name'] == lab_name:
                    lab['abbr'] = new_abbr
                    break

        # Update reference fields
        refs = data.setdefault('refs', {})
        ref_what = request.form.get('ref_what')
        ref_why = request.form.get('ref_why')
        ref_high = request.form.get('ref_high')
        ref_low = request.form.get('ref_low')

        if any(v is not None for v in [ref_what, ref_why, ref_high, ref_low]):
            ref = refs.setdefault(lab_name, {})
            if ref_what is not None:
                ref['what'] = ref_what.strip()
            if ref_why is not None:
                ref['why'] = ref_why.strip()
            if ref_high is not None:
                ref['high'] = ref_high.strip()
            if ref_low is not None:
                ref['low'] = ref_low.strip()

        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)

        return jsonify({'success': True})
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error updating lab cache: {str(e)}")
        return jsonify({'success': False, 'error': 'Update failed'}), 500


# ======================================================================
# GET /labtrack — Dashboard: all tracked patients with status
# ======================================================================
@labtrack_bp.route('/labtrack')
@login_required
@require_feature('labtrack')
def index():
    """Lab value tracker dashboard showing all tracked labs."""
    tracks = (
        LabTrack.query
        .filter_by(user_id=current_user.id, is_archived=False)
        .order_by(LabTrack.mrn, LabTrack.lab_name)
        .all()
    )

    # Group by MRN for display
    patients = {}
    for t in tracks:
        mrn = t.mrn
        if mrn not in patients:
            patients[mrn] = {'mrn': mrn, 'display_mrn': mrn or '????', 'tracks': []}
        patients[mrn]['tracks'].append(t)

    # Count stats
    overdue_count = sum(1 for t in tracks if t.status == 'overdue')
    critical_count = sum(1 for t in tracks if t.status == 'critical')
    due_soon_count = sum(1 for t in tracks if t.status == 'due_soon')

    # Get panels for the add-panel dropdown
    panels = LabPanel.query.order_by(LabPanel.name).all()

    return render_template(
        'labtrack.html',
        patients=patients,
        all_tracks=tracks,
        overdue_count=overdue_count,
        critical_count=critical_count,
        due_soon_count=due_soon_count,
        panels=panels,
        STANDARD_PANELS=STANDARD_PANELS,
    )


# ======================================================================
# GET /labtrack/<mrn> — Per-patient detail view
# ======================================================================
@labtrack_bp.route('/labtrack/<mrn>')
@login_required
def patient_detail(mrn):
    """All tracked labs for one patient with sparklines and trend data."""
    tracks = (
        LabTrack.query
        .filter_by(user_id=current_user.id, mrn=mrn, is_archived=False)
        .order_by(LabTrack.lab_name)
        .all()
    )
    if not tracks:
        flash('No tracked labs found for that patient.', 'error')
        return redirect(url_for('labtrack.index'))

    display_mrn = mrn or '????'

    # Group by panel
    paneled = {}
    standalone = []
    for t in tracks:
        if t.panel_name:
            paneled.setdefault(t.panel_name, []).append(t)
        else:
            standalone.append(t)

    return render_template(
        'labtrack_patient.html',
        mrn=mrn,
        display_mrn=display_mrn,
        tracks=tracks,
        paneled=paneled,
        standalone=standalone,
        today=datetime.now(timezone.utc).strftime('%Y-%m-%d'),
    )


# ======================================================================
# POST /labtrack/add — Add new tracking criteria
# ======================================================================
@labtrack_bp.route('/labtrack/add', methods=['POST'])
@login_required
def add_tracking():
    """Add new lab tracking criteria for a patient."""
    mrn = request.form.get('mrn', '').strip()
    lab_name = request.form.get('lab_name', '').strip()
    interval_days = request.form.get('interval_days', '90')
    panel_name = request.form.get('panel_name', '').strip()

    if not mrn or not lab_name:
        flash('MRN and lab name are required.', 'error')
        return redirect(url_for('labtrack.index'))

    # Check for duplicate
    existing = LabTrack.query.filter_by(
        user_id=current_user.id, mrn=mrn, lab_name=lab_name
    ).first()
    if existing:
        flash(f'Already tracking {lab_name} for {mrn}.', 'error')
        return redirect(url_for('labtrack.index'))

    track = LabTrack(
        user_id=current_user.id,
        mrn=mrn,
        lab_name=lab_name,
        interval_days=int(interval_days or 90),
        panel_name=panel_name,
        alert_low=_float_or_none(request.form.get('alert_low')),
        alert_high=_float_or_none(request.form.get('alert_high')),
        critical_low=_float_or_none(request.form.get('critical_low')),
        critical_high=_float_or_none(request.form.get('critical_high')),
    )
    db.session.add(track)
    db.session.commit()
    flash(f'Now tracking {lab_name} for {mrn}.', 'success')
    return redirect(url_for('labtrack.index'))


# ======================================================================
# POST /labtrack/add-panel — Add entire panel for a patient (F11d)
# ======================================================================
@labtrack_bp.route('/labtrack/add-panel', methods=['POST'])
@login_required
def add_panel():
    """Add all labs in a standard panel for a patient."""
    mrn = request.form.get('mrn', '').strip()
    panel_name = request.form.get('panel_name', '').strip()
    interval_days = int(request.form.get('interval_days', '90') or 90)

    if not mrn or not panel_name:
        flash('MRN and panel name are required.', 'error')
        return redirect(url_for('labtrack.index'))

    components = STANDARD_PANELS.get(panel_name, [])
    if not components:
        # Try from DB
        panel = LabPanel.query.filter_by(name=panel_name).first()
        if panel:
            components = json.loads(panel.components_json or '[]')

    added = 0
    for lab_name in components:
        existing = LabTrack.query.filter_by(
            user_id=current_user.id, mrn=mrn, lab_name=lab_name
        ).first()
        if not existing:
            track = LabTrack(
                user_id=current_user.id,
                mrn=mrn,
                lab_name=lab_name,
                interval_days=interval_days,
                panel_name=panel_name,
            )
            db.session.add(track)
            added += 1
    db.session.commit()
    flash(f'Added {added} lab(s) from {panel_name} panel for {mrn}.', 'success')
    return redirect(url_for('labtrack.index'))


# ======================================================================
# POST /labtrack/<id>/edit — Edit tracking criteria
# ======================================================================
@labtrack_bp.route('/labtrack/<int:track_id>/edit', methods=['POST'])
@login_required
def edit_tracking(track_id):
    """Edit lab tracking criteria."""
    track = LabTrack.query.get_or_404(track_id)
    if track.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('labtrack.index'))

    track.interval_days = int(request.form.get('interval_days', track.interval_days) or 90)
    track.alert_low = _float_or_none(request.form.get('alert_low'))
    track.alert_high = _float_or_none(request.form.get('alert_high'))
    track.critical_low = _float_or_none(request.form.get('critical_low'))
    track.critical_high = _float_or_none(request.form.get('critical_high'))
    track.notes = request.form.get('notes', track.notes or '')

    db.session.commit()
    flash(f'Updated {track.lab_name} tracking.', 'success')
    return redirect(url_for('labtrack.patient_detail', mrn=track.mrn))


# ======================================================================
# POST /labtrack/<id>/delete — Remove tracking
# ======================================================================
@labtrack_bp.route('/labtrack/<int:track_id>/delete', methods=['POST'])
@login_required
def delete_tracking(track_id):
    """Delete a lab tracking entry and all its results."""
    track = LabTrack.query.get_or_404(track_id)
    if track.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('labtrack.index'))

    mrn = track.mrn
    name = track.lab_name
    # HIPAA: soft-delete clinical records — never hard-delete
    track.is_archived = True
    db.session.commit()
    flash(f'Removed {name} tracking for {mrn}.', 'success')
    return redirect(url_for('labtrack.index'))


# ======================================================================
# POST /labtrack/<id>/result — Manually add a result
# ======================================================================
@labtrack_bp.route('/labtrack/<int:track_id>/result', methods=['POST'])
@login_required
def add_result(track_id):
    """Manually add a lab result value."""
    track = LabTrack.query.get_or_404(track_id)
    if track.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('labtrack.index'))

    result_value = request.form.get('result_value', '').strip()
    result_date_str = request.form.get('result_date', '')

    if not result_value:
        flash('Result value is required.', 'error')
        return redirect(url_for('labtrack.patient_detail', mrn=track.mrn))

    if result_date_str:
        result_date = datetime.strptime(result_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    else:
        result_date = datetime.now(timezone.utc)

    # Determine if critical
    is_critical = False
    try:
        val = float(result_value)
        if track.critical_high is not None and val >= track.critical_high:
            is_critical = True
        if track.critical_low is not None and val <= track.critical_low:
            is_critical = True
    except (ValueError, TypeError):
        pass

    # Determine trend direction
    trend_direction = 'stable'
    if track.results:
        try:
            prev_val = float(track.results[0].result_value)
            curr_val = float(result_value)
            if curr_val > prev_val:
                trend_direction = 'up'
            elif curr_val < prev_val:
                trend_direction = 'down'
        except (ValueError, TypeError):
            pass

    result = LabResult(
        labtrack_id=track.id,
        result_value=result_value,
        result_date=result_date,
        is_critical=is_critical,
        trend_direction=trend_direction,
    )
    db.session.add(result)

    # Update last_checked and overdue status
    track.last_checked = result_date
    track.is_overdue = False

    db.session.commit()

    if is_critical:
        flash(f'CRITICAL VALUE recorded: {result_value}', 'error')
        _send_critical_lab_alert(track, result_value)
    else:
        flash(f'Result recorded: {result_value}', 'success')

    return redirect(url_for('labtrack.patient_detail', mrn=track.mrn))


# ======================================================================
# GET /labtrack/<mrn>/trend/<lab_name> — Trend chart data (JSON)
# ======================================================================
@labtrack_bp.route('/labtrack/<mrn>/trend/<lab_name>')
@login_required
def trend_data(mrn, lab_name):
    """Return JSON data for Chart.js trend graph (F11a)."""
    track = LabTrack.query.filter_by(
        user_id=current_user.id, mrn=mrn, lab_name=lab_name
    ).first_or_404()

    results = (
        LabResult.query
        .filter_by(labtrack_id=track.id)
        .order_by(LabResult.result_date.asc())
        .all()
    )

    labels = []
    values = []
    point_colors = []

    for r in results:
        labels.append(r.result_date.strftime('%m/%d/%y') if r.result_date else '')
        try:
            val = float(r.result_value)
            values.append(val)

            # Color coding: critical=red, alert=orange, normal=green
            color = '#22c55e'  # green
            if track.critical_high is not None and val >= track.critical_high:
                color = '#ef4444'  # red
            elif track.critical_low is not None and val <= track.critical_low:
                color = '#ef4444'
            elif track.alert_high is not None and val >= track.alert_high:
                color = '#f97316'  # orange
            elif track.alert_low is not None and val <= track.alert_low:
                color = '#f97316'
            point_colors.append(color)
        except (ValueError, TypeError):
            values.append(None)
            point_colors.append('#94a3b8')

    # Compute trend label from last 3 numeric values
    numeric_vals = [v for v in values if v is not None]
    if len(numeric_vals) >= 3:
        last3 = numeric_vals[-3:]
        if last3[-1] > last3[-2] > last3[-3]:
            trend_label = 'Trending UP ↑'
        elif last3[-1] < last3[-2] < last3[-3]:
            trend_label = 'Trending DOWN ↓'
        else:
            trend_label = 'Stable →'
    elif len(numeric_vals) >= 2:
        if numeric_vals[-1] > numeric_vals[-2]:
            trend_label = 'Trending UP ↑'
        elif numeric_vals[-1] < numeric_vals[-2]:
            trend_label = 'Trending DOWN ↓'
        else:
            trend_label = 'Stable →'
    else:
        trend_label = 'Insufficient data'

    return jsonify({
        'labels': labels,
        'values': values,
        'point_colors': point_colors,
        'alert_low': track.alert_low,
        'alert_high': track.alert_high,
        'critical_low': track.critical_low,
        'critical_high': track.critical_high,
        'trend_label': trend_label,
        'lab_name': track.lab_name,
    })


# ======================================================================
# GET /labtrack/overdue-count — JSON count for morning briefing
# ======================================================================
@labtrack_bp.route('/labtrack/overdue-count')
@login_required
def overdue_count():
    """Return JSON with overdue lab count for the current user."""
    count = LabTrack.query.filter_by(
        user_id=current_user.id, is_overdue=True, is_archived=False
    ).count()
    return jsonify({'overdue_count': count})


# ======================================================================
# POST /labtrack/seed-panels — Seed standard panel definitions (F11d)
# ======================================================================
@labtrack_bp.route('/labtrack/seed-panels', methods=['POST'])
@login_required
def seed_panels():
    """Seed standard lab panel definitions into the database."""
    added = 0
    for name, components in STANDARD_PANELS.items():
        existing = LabPanel.query.filter_by(name=name).first()
        if not existing:
            panel = LabPanel(name=name, components_json=json.dumps(components))
            db.session.add(panel)
            added += 1
    db.session.commit()
    flash(f'Seeded {added} standard lab panel(s).', 'success')
    return redirect(url_for('labtrack.index'))


# ======================================================================
# Helpers
# ======================================================================

def _float_or_none(val):
    """Convert form value to float or None."""
    if val is None or val == '':
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _send_critical_lab_alert(track, value):
    """Send Pushover notification for critical lab value (F11b). De-identified."""
    import config as cfg
    from agent.notifier import _send_pushover

    user_key = getattr(cfg, 'PUSHOVER_USER_KEY', '')
    api_token = getattr(cfg, 'PUSHOVER_API_TOKEN', '')
    if not user_key or not api_token:
        return

    _send_pushover(
        user_key, api_token,
        title='⚠ CRITICAL LAB VALUE',
        message=f'Critical {track.lab_name} result: {value} — Review immediately',
        priority=1,
        sound='siren',
    )


# ======================================================================
# F11c: Overdue lab detection — called by scheduler
# ======================================================================

def check_overdue_labs(user_id):
    """
    Check all LabTrack entries for overdue labs and flag them.
    Called daily at 6 AM by the scheduler.
    Returns count of newly-flagged overdue entries.
    """
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    count = 0

    tracks = LabTrack.query.filter_by(user_id=user_id, is_archived=False).all()
    for t in tracks:
        was_overdue = t.is_overdue
        if t.last_checked and t.interval_days:
            next_due = t.last_checked + timedelta(days=t.interval_days)
            t.is_overdue = now > next_due
        else:
            # Never checked — consider overdue if tracked for > interval days
            t.is_overdue = False

        if t.is_overdue and not was_overdue:
            count += 1

    db.session.commit()
    return count


def get_overdue_lab_count(user_id):
    """Return count of overdue lab tracks for morning briefing integration."""
    return LabTrack.query.filter_by(user_id=user_id, is_overdue=True, is_archived=False).count()

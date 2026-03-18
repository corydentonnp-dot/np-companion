"""
NP Companion — Metrics & Productivity Routes

File location: np-companion/routes/metrics.py

Provides:
  GET  /metrics                    — Productivity dashboard (F13)
  GET  /metrics/weekly             — Weekly summary page (F13c)
  GET  /metrics/preview-weekly     — Preview this week's summary (F13c)
  GET  /metrics/api/chart-data     — JSON for all Chart.js charts (F13)
  GET  /api/metrics/oncall-stats   — JSON on-call stats (F7e)

Features: F13, F13a, F13b, F13c
"""

from collections import Counter
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user

from models import db
from models.oncall import OnCallNote
from models.timelog import TimeLog
from models.inbox import InboxSnapshot
from models.user import User

metrics_bp = Blueprint('metrics', __name__)


# --------------------------------------------------------------------------
#  F13 — Main Dashboard
# --------------------------------------------------------------------------
@metrics_bp.route('/metrics')
@login_required
def index():
    """Productivity dashboard with charts, stats, and burnout indicators."""
    today = date.today()
    start_of_day = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)

    # Today's stats
    today_sessions = (
        TimeLog.query
        .filter_by(user_id=current_user.id)
        .filter(TimeLog.session_start >= start_of_day, TimeLog.session_end.isnot(None))
        .all()
    )
    today_patients = len(today_sessions)
    today_chart_secs = sum(s.duration_seconds or 0 for s in today_sessions)
    today_f2f_secs = sum(s.face_to_face_seconds or 0 for s in today_sessions)
    today_avg = (today_chart_secs // today_patients) if today_patients else 0

    # On-call stats
    oncall_stats = _oncall_weekly_stats(current_user.id)

    # F13b — Burnout indicators (last 3 weeks)
    burnout = _compute_burnout_indicators(current_user.id)

    # F13a — Benchmark check
    participate = current_user.preferences.get('participate_in_benchmarks', False)

    return render_template(
        'metrics.html',
        oncall_stats=oncall_stats,
        today_patients=today_patients,
        today_chart_secs=today_chart_secs,
        today_f2f_secs=today_f2f_secs,
        today_avg=today_avg,
        burnout=burnout,
        participate_benchmarks=participate,
    )


# --------------------------------------------------------------------------
#  F13 — Chart.js JSON endpoint
# --------------------------------------------------------------------------
@metrics_bp.route('/metrics/api/chart-data')
@login_required
def chart_data():
    """JSON endpoint returning all chart datasets for the metrics page."""
    days = int(request.args.get('days', 30))
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    uid = current_user.id

    # 1. Daily patient count + chart time (weekly trend)
    sessions = (
        TimeLog.query
        .filter(TimeLog.user_id == uid,
                TimeLog.session_start >= start,
                TimeLog.session_end.isnot(None))
        .all()
    )

    daily_counts = {}
    daily_chart_min = {}
    daily_f2f_min = {}
    visit_type_counter = Counter()
    visit_type_time = {}

    for s in sessions:
        d = s.session_start.date().isoformat()
        daily_counts[d] = daily_counts.get(d, 0) + 1
        daily_chart_min[d] = daily_chart_min.get(d, 0) + round((s.duration_seconds or 0) / 60, 1)
        daily_f2f_min[d] = daily_f2f_min.get(d, 0) + round((s.face_to_face_seconds or 0) / 60, 1)

        vt = s.visit_type or 'Unknown'
        visit_type_counter[vt] += 1
        if vt not in visit_type_time:
            visit_type_time[vt] = []
        visit_type_time[vt].append(s.duration_seconds or 0)

    # Build date labels
    labels = []
    counts = []
    chart_mins = []
    f2f_mins = []
    d = start.date()
    while d <= end.date():
        iso = d.isoformat()
        labels.append(iso)
        counts.append(daily_counts.get(iso, 0))
        chart_mins.append(daily_chart_min.get(iso, 0))
        f2f_mins.append(daily_f2f_min.get(iso, 0))
        d += timedelta(days=1)

    # Avg chart time by visit type
    avg_by_type = {}
    for vt, times in visit_type_time.items():
        avg_by_type[vt] = round(sum(times) / len(times) / 60, 1) if times else 0

    # F2F ratio
    total_chart = sum(chart_mins)
    total_f2f = sum(f2f_mins)
    doc_time = total_chart - total_f2f if total_chart > total_f2f else 0

    # 6. Inbox activity (snapshot counts over time)
    snapshots = (
        InboxSnapshot.query
        .filter(InboxSnapshot.user_id == uid, InboxSnapshot.captured_at >= start)
        .order_by(InboxSnapshot.captured_at)
        .all()
    )
    inbox_labels = [s.captured_at.date().isoformat() for s in snapshots]
    inbox_totals = [
        (s.labs_count or 0) + (s.radiology_count or 0) +
        (s.messages_count or 0) + (s.refills_count or 0) + (s.other_count or 0)
        for s in snapshots
    ]

    # 7. On-call volume by week
    oncall_notes = (
        OnCallNote.query
        .filter(OnCallNote.user_id == uid, OnCallNote.call_time >= start)
        .all()
    )
    oncall_weekly = {}
    for n in oncall_notes:
        ct = n.call_time or n.created_at
        iso_year, iso_week, _ = ct.isocalendar()
        wk = f'{iso_year}-W{iso_week:02d}'
        oncall_weekly[wk] = oncall_weekly.get(wk, 0) + 1

    # F13a — Benchmarks (practice averages)
    benchmarks = _compute_benchmarks(uid) if current_user.preferences.get('participate_in_benchmarks', False) else None

    return jsonify({
        'labels': labels,
        'daily_counts': counts,
        'daily_chart_min': chart_mins,
        'daily_f2f_min': f2f_mins,
        'visit_type_breakdown': dict(visit_type_counter),
        'avg_chart_time_by_type': avg_by_type,
        'f2f_ratio': {'face_to_face': round(total_f2f, 1), 'documentation': round(doc_time, 1)},
        'inbox_labels': inbox_labels,
        'inbox_totals': inbox_totals,
        'oncall_weeks': list(oncall_weekly.keys()),
        'oncall_counts': list(oncall_weekly.values()),
        'benchmarks': benchmarks,
    })


# --------------------------------------------------------------------------
#  F13c — Weekly summary
# --------------------------------------------------------------------------
@metrics_bp.route('/metrics/weekly')
@login_required
def weekly_summary():
    """Weekly summary page."""
    summary = _generate_weekly_summary(current_user.id)
    return render_template('metrics_weekly.html', summary=summary)


@metrics_bp.route('/metrics/preview-weekly')
@login_required
def preview_weekly():
    """Preview this week's summary before Friday."""
    summary = _generate_weekly_summary(current_user.id)
    return render_template('metrics_weekly.html', summary=summary, preview=True)


def _generate_weekly_summary(user_id):
    """Build a weekly summary dict for the given user."""
    now = datetime.now(timezone.utc)
    # Start of this week (Monday)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    sessions = (
        TimeLog.query
        .filter(TimeLog.user_id == user_id,
                TimeLog.session_start >= week_start,
                TimeLog.session_end.isnot(None))
        .all()
    )
    patients = len(sessions)
    total_hours = round(sum(s.duration_seconds or 0 for s in sessions) / 3600, 1)
    total_f2f = round(sum(s.face_to_face_seconds or 0 for s in sessions) / 3600, 1)

    # Top 3 visit types
    vt_counter = Counter()
    for s in sessions:
        vt_counter[s.visit_type or 'Unknown'] += 1
    top_types = vt_counter.most_common(3)

    # Inbox activity
    inbox_snaps = (
        InboxSnapshot.query
        .filter(InboxSnapshot.user_id == user_id, InboxSnapshot.captured_at >= week_start)
        .all()
    )
    inbox_items = sum(
        (s.labs_count or 0) + (s.radiology_count or 0) +
        (s.messages_count or 0) + (s.refills_count or 0) + (s.other_count or 0)
        for s in inbox_snaps
    )

    # On-call calls
    oncall = OnCallNote.query.filter(
        OnCallNote.user_id == user_id, OnCallNote.call_time >= week_start
    ).count()

    # Notable metric — compare avg chart time to last week
    last_week_start = week_start - timedelta(weeks=1)
    last_sessions = (
        TimeLog.query
        .filter(TimeLog.user_id == user_id,
                TimeLog.session_start >= last_week_start,
                TimeLog.session_start < week_start,
                TimeLog.session_end.isnot(None))
        .all()
    )
    this_avg = (sum(s.duration_seconds or 0 for s in sessions) / len(sessions) / 60) if sessions else 0
    last_avg = (sum(s.duration_seconds or 0 for s in last_sessions) / len(last_sessions) / 60) if last_sessions else 0
    notable = ''
    if last_avg > 0 and this_avg > 0:
        diff = round(this_avg - last_avg, 1)
        if abs(diff) >= 1:
            direction = 'decreased' if diff < 0 else 'increased'
            notable = f'Your average chart time {direction} by {abs(diff):.1f} minutes compared to last week.'

    return {
        'week_start': week_start.date().isoformat(),
        'patients': patients,
        'total_hours': total_hours,
        'total_f2f': total_f2f,
        'top_types': top_types,
        'inbox_items': inbox_items,
        'oncall_calls': oncall,
        'notable': notable,
    }


# --------------------------------------------------------------------------
#  F13b — Burnout early-warning indicators
# --------------------------------------------------------------------------
def _compute_burnout_indicators(user_id):
    """
    Compute 3 burnout indicators for the last 3 weeks:
      1. After-hours chart time (outside 7AM-6PM)
      2. Inbox backlog trend (growing week-over-week)
      3. F2F ratio trend (documentation growing vs patient time)

    Returns warnings only when an indicator worsens 3 consecutive weeks.
    """
    now = datetime.now(timezone.utc)
    warnings = []
    weekly_data = []

    for i in range(3):
        week_end = now - timedelta(weeks=i)
        week_start = week_end - timedelta(weeks=1)

        sessions = (
            TimeLog.query
            .filter(TimeLog.user_id == user_id,
                    TimeLog.session_start >= week_start,
                    TimeLog.session_start < week_end,
                    TimeLog.session_end.isnot(None))
            .all()
        )

        # After-hours minutes (before 7AM or after 6PM)
        after_hours_secs = 0
        total_chart_secs = 0
        total_f2f_secs = 0
        for s in sessions:
            total_chart_secs += (s.duration_seconds or 0)
            total_f2f_secs += (s.face_to_face_seconds or 0)
            hour = s.session_start.hour if s.session_start else 12
            if hour < 7 or hour >= 18:
                after_hours_secs += (s.duration_seconds or 0)

        # Inbox backlog (sum of snapshot totals)
        snaps = (
            InboxSnapshot.query
            .filter(InboxSnapshot.user_id == user_id,
                    InboxSnapshot.captured_at >= week_start,
                    InboxSnapshot.captured_at < week_end)
            .all()
        )
        inbox_total = sum(
            (s.labs_count or 0) + (s.radiology_count or 0) +
            (s.messages_count or 0) + (s.refills_count or 0) + (s.other_count or 0)
            for s in snaps
        ) if snaps else 0

        # F2F ratio (doc time vs f2f)
        doc_secs = total_chart_secs - total_f2f_secs
        f2f_ratio = round(total_f2f_secs / total_chart_secs * 100, 1) if total_chart_secs > 0 else 0

        weekly_data.append({
            'after_hours_min': round(after_hours_secs / 60, 1),
            'inbox_total': inbox_total,
            'f2f_ratio': f2f_ratio,
            'doc_min': round(doc_secs / 60, 1),
        })

    # Check for 3-consecutive-week worsening (index 0=most recent, 2=oldest)
    if len(weekly_data) == 3:
        # After-hours: increasing 3 weeks
        ah = [w['after_hours_min'] for w in weekly_data]
        if ah[2] < ah[1] < ah[0] and ah[0] > 0:
            pct = round((ah[0] - ah[2]) / max(ah[2], 1) * 100)
            warnings.append(f'After-hours chart time has increased {pct}% over the past 3 weeks.')

        # Inbox backlog: growing
        ib = [w['inbox_total'] for w in weekly_data]
        if ib[2] < ib[1] < ib[0] and ib[0] > 0:
            warnings.append('Inbox backlog has been growing for 3 consecutive weeks.')

        # F2F ratio: decreasing (more doc time, less patient time)
        fr = [w['f2f_ratio'] for w in weekly_data]
        if fr[2] > fr[1] > fr[0] and fr[2] > 0:
            diff = round(fr[2] - fr[0], 1)
            warnings.append(f'Face-to-face ratio has decreased by {diff}% over the past 3 weeks.')

    return {
        'weekly': weekly_data,
        'warnings': warnings,
    }


# --------------------------------------------------------------------------
#  F13a — Benchmark comparison
# --------------------------------------------------------------------------
def _compute_benchmarks(current_user_id):
    """
    Compute anonymized practice averages from all opted-in providers.
    Returns dict with avg chart time by type, avg f2f ratio, avg inbox turnaround.
    """
    opted_in_users = User.query.filter(User.is_active_account.is_(True)).all()
    opted_in_ids = [
        u.id for u in opted_in_users
        if u.preferences.get('participate_in_benchmarks', False)
    ]

    if len(opted_in_ids) < 2:
        return None  # Not enough participants for meaningful comparison

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    sessions = (
        TimeLog.query
        .filter(TimeLog.user_id.in_(opted_in_ids),
                TimeLog.session_start >= cutoff,
                TimeLog.session_end.isnot(None))
        .all()
    )

    if not sessions:
        return None

    # Avg chart time by visit type (practice-wide)
    type_times = {}
    total_chart = 0
    total_f2f = 0
    for s in sessions:
        vt = s.visit_type or 'Unknown'
        if vt not in type_times:
            type_times[vt] = []
        type_times[vt].append(s.duration_seconds or 0)
        total_chart += (s.duration_seconds or 0)
        total_f2f += (s.face_to_face_seconds or 0)

    avg_by_type = {}
    for vt, times in type_times.items():
        avg_by_type[vt] = round(sum(times) / len(times) / 60, 1) if times else 0

    f2f_ratio = round(total_f2f / total_chart * 100, 1) if total_chart > 0 else 0

    return {
        'avg_chart_time_by_type': avg_by_type,
        'avg_f2f_ratio': f2f_ratio,
        'participant_count': len(opted_in_ids),
    }


# --------------------------------------------------------------------------
#  F7e — On-Call stats (existing)
# --------------------------------------------------------------------------
def _oncall_weekly_stats(user_id, weeks=4):
    """Compute weekly on-call stats for the last N weeks."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(weeks=weeks)

    notes = (
        OnCallNote.query
        .filter(OnCallNote.user_id == user_id, OnCallNote.call_time >= cutoff)
        .order_by(OnCallNote.call_time)
        .all()
    )

    if not notes:
        return {
            'weeks': [],
            'total_calls': 0,
            'avg_per_night': 0,
            'top_complaints': [],
        }

    weekly = {}
    complaint_counter = Counter()
    night_counts = Counter()

    for n in notes:
        ct = n.call_time or n.created_at
        iso_year, iso_week, _ = ct.isocalendar()
        week_key = f'{iso_year}-W{iso_week:02d}'
        weekly[week_key] = weekly.get(week_key, 0) + 1
        if n.chief_complaint:
            complaint_counter[n.chief_complaint.strip().lower()] += 1
        night_counts[ct.date()] += 1

    week_data = [{'week': k, 'count': v} for k, v in sorted(weekly.items())]
    total = len(notes)
    unique_nights = len(night_counts)
    avg_per_night = round(total / unique_nights, 1) if unique_nights else 0
    top_complaints = [{'complaint': c.title(), 'count': n} for c, n in complaint_counter.most_common(5)]

    return {
        'weeks': week_data,
        'total_calls': total,
        'avg_per_night': avg_per_night,
        'top_complaints': top_complaints,
    }


@metrics_bp.route('/api/metrics/oncall-stats')
@login_required
def oncall_stats_api():
    """JSON endpoint for on-call stats."""
    stats = _oncall_weekly_stats(current_user.id)
    return jsonify(stats)
    return jsonify(_oncall_weekly_stats(current_user.id))

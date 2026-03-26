"""
CareCompanion — Metrics Service

Weekly summary generation extracted from routes/metrics.py (Band 3 B1.13).
"""

from collections import Counter
from datetime import datetime, timedelta, timezone

from models import db
from models.oncall import OnCallNote
from models.timelog import TimeLog
from models.inbox import InboxSnapshot


def generate_weekly_summary(user_id):
    """Build a weekly summary dict for the given user.

    Covers the current calendar week (Mon 00:00 UTC to now).
    Returns a dict with patients, hours, inbox_items, billing stats, etc.
    """
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
    last_avg = (
        sum(s.duration_seconds or 0 for s in last_sessions) / len(last_sessions) / 60
    ) if last_sessions else 0
    notable = ''
    if last_avg > 0 and this_avg > 0:
        diff = round(this_avg - last_avg, 1)
        if abs(diff) >= 1:
            direction = 'decreased' if diff < 0 else 'increased'
            notable = (
                f'Your average chart time {direction} by {abs(diff):.1f} minutes '
                f'compared to last week.'
            )

    # Billing opportunities captured vs. missed this week
    billing_captured = 0
    billing_missed = 0
    billing_revenue_captured = 0.0
    billing_revenue_missed = 0.0
    try:
        from models.billing import BillingOpportunity
        week_opps = BillingOpportunity.query.filter(
            BillingOpportunity.user_id == user_id,
            BillingOpportunity.visit_date >= week_start.date(),
        ).all()
        for opp in week_opps:
            status = (opp.status or '').lower()
            if status == 'captured':
                billing_captured += 1
                billing_revenue_captured += (opp.estimated_revenue or 0)
            elif status in ('pending', 'dismissed'):
                billing_missed += 1
                billing_revenue_missed += (opp.estimated_revenue or 0)
    except Exception:
        pass

    avg_visit_min = round(this_avg, 1) if sessions else 0

    return {
        'week_start': week_start.date().isoformat(),
        'patients': patients,
        'total_hours': total_hours,
        'total_f2f': total_f2f,
        'top_types': top_types,
        'inbox_items': inbox_items,
        'oncall_calls': oncall,
        'notable': notable,
        'avg_visit_min': avg_visit_min,
        'billing_captured': billing_captured,
        'billing_missed': billing_missed,
        'billing_revenue_captured': round(billing_revenue_captured, 2),
        'billing_revenue_missed': round(billing_revenue_missed, 2),
    }

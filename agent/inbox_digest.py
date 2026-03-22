"""
CareCompanion — Inbox Digest Report Generator

File location: carecompanion/agent/inbox_digest.py

Generates a periodic summary of inbox activity over a configurable
time window (default: 24 hours). Can be sent as a Pushover
notification and/or viewed on the /inbox/digest web page.

Feature: F5e (Inbox Digest Report)

HIPAA note: Digest contains ONLY category counts and trend
indicators — never patient names, MRNs, or clinical details.
"""

import logging
from datetime import datetime, timedelta, timezone

import config

logger = logging.getLogger('agent.inbox_digest')


def generate_digest(user_id, hours=None):
    """
    Build an inbox activity summary for the given time window.

    Parameters
    ----------
    user_id : int
        The provider whose data to summarize.
    hours : int or None
        Lookback window in hours.  Falls back to
        config.INBOX_DIGEST_HOURS (default 24).

    Returns
    -------
    dict
        {
            "period_hours": int,
            "period_start": datetime,
            "period_end": datetime,
            "snapshots_count": int,
            "current_totals": {...},
            "period_new": int,
            "period_resolved": int,
            "still_unresolved": int,
            "critical_seen": int,
            "held_count": int,
            "overdue_count": int,
            "category_breakdown": {...},
            "trend": str,   # "improving", "stable", "growing"
            "message": str, # Plain-text summary for push notification
        }
    """
    from models.inbox import InboxSnapshot, InboxItem

    if hours is None:
        hours = getattr(config, 'INBOX_DIGEST_HOURS', 24)

    now = datetime.now(timezone.utc)
    period_start = now - timedelta(hours=hours)

    # ---- Snapshots in this period ----
    snapshots = (
        InboxSnapshot.query
        .filter(
            InboxSnapshot.user_id == user_id,
            InboxSnapshot.captured_at >= period_start,
        )
        .order_by(InboxSnapshot.captured_at.asc())
        .all()
    )

    # Sum category counts from the most recent snapshot
    latest = snapshots[-1] if snapshots else None
    current_totals = {}
    if latest:
        current_totals = {
            'labs': latest.labs_count,
            'radiology': latest.radiology_count,
            'messages': latest.messages_count,
            'refills': latest.refills_count,
            'other': latest.other_count,
        }

    # ---- Items that appeared in this period ----
    new_items = (
        InboxItem.query
        .filter(
            InboxItem.user_id == user_id,
            InboxItem.first_seen_at >= period_start,
        )
        .all()
    )

    # ---- Items resolved in this period ----
    resolved_items = (
        InboxItem.query
        .filter(
            InboxItem.user_id == user_id,
            InboxItem.is_resolved == True,
            InboxItem.last_seen_at >= period_start,
        )
        .all()
    )

    # ---- Still unresolved ----
    still_unresolved = (
        InboxItem.query
        .filter_by(user_id=user_id, is_resolved=False)
        .count()
    )

    # ---- Critical items seen this period ----
    critical_seen = sum(1 for i in new_items if i.priority == 'critical')

    # ---- Currently held ----
    held_count = (
        InboxItem.query
        .filter_by(user_id=user_id, is_held=True, is_resolved=False)
        .count()
    )

    # ---- Overdue items (past critical threshold) ----
    critical_hours = getattr(config, 'INBOX_CRITICAL_HOURS', 72)
    cutoff = now - timedelta(hours=critical_hours)
    overdue_count = (
        InboxItem.query
        .filter(
            InboxItem.user_id == user_id,
            InboxItem.is_resolved == False,
            InboxItem.first_seen_at <= cutoff,
        )
        .count()
    )

    # ---- Category breakdown of new items ----
    category_breakdown = {}
    for item in new_items:
        cat = item.item_type or 'other'
        category_breakdown[cat] = category_breakdown.get(cat, 0) + 1

    # ---- Trend: compare first-half vs second-half snapshot totals ----
    trend = 'stable'
    if len(snapshots) >= 4:
        mid = len(snapshots) // 2
        first_half = snapshots[:mid]
        second_half = snapshots[mid:]

        def _snap_total(s):
            return (s.labs_count + s.radiology_count + s.messages_count
                    + s.refills_count + s.other_count)

        avg_first = sum(_snap_total(s) for s in first_half) / len(first_half)
        avg_second = sum(_snap_total(s) for s in second_half) / len(second_half)

        if avg_second < avg_first * 0.85:
            trend = 'improving'
        elif avg_second > avg_first * 1.15:
            trend = 'growing'

    # ---- Build plain-text message (counts only — no PHI) ----
    period_new = len(new_items)
    period_resolved = len(resolved_items)

    parts = [f'Past {hours}h:']
    parts.append(f'+{period_new} new, -{period_resolved} resolved')
    parts.append(f'{still_unresolved} unresolved')
    if critical_seen:
        parts.append(f'{critical_seen} CRITICAL')
    if held_count:
        parts.append(f'{held_count} held')
    if overdue_count:
        parts.append(f'{overdue_count} overdue')
    parts.append(f'Trend: {trend}')

    message = ' | '.join(parts)

    return {
        'period_hours': hours,
        'period_start': period_start,
        'period_end': now,
        'snapshots_count': len(snapshots),
        'current_totals': current_totals,
        'period_new': period_new,
        'period_resolved': period_resolved,
        'still_unresolved': still_unresolved,
        'critical_seen': critical_seen,
        'held_count': held_count,
        'overdue_count': overdue_count,
        'category_breakdown': category_breakdown,
        'trend': trend,
        'message': message,
    }


def send_digest_notification(user_id, digest=None):
    """
    Send the inbox digest as a Pushover notification.
    Generates the digest first if not provided.

    HIPAA: Message contains only counts and trend — no PHI.
    """
    if digest is None:
        digest = generate_digest(user_id)

    user_key = getattr(config, 'PUSHOVER_USER_KEY', '')
    api_token = getattr(config, 'PUSHOVER_API_TOKEN', '')

    if not user_key or not api_token:
        logger.warning('Pushover keys not configured — skipping digest notification')
        return

    # Skip if nothing happened
    if digest['period_new'] == 0 and digest['period_resolved'] == 0:
        logger.info('No inbox activity in digest period — skipping notification')
        return

    from agent.notifier import _send_pushover
    _send_pushover(
        user_key, api_token,
        title='Inbox Digest',
        message=digest['message'],
        priority=-1,  # quiet notification, no sound
    )


def run_digest_job(user_id):
    """
    Entry point for the scheduled digest job.
    Generates the digest and sends a push notification.
    """
    logger.info(f'Running inbox digest for user {user_id}')
    digest = generate_digest(user_id)
    send_digest_notification(user_id, digest)
    logger.info(f'Digest complete: {digest["message"]}')
    return digest

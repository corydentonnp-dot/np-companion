"""
CareCompanion — Pushover Notification Service

File location: carecompanion/agent/notifier.py

Sends de-identified push notifications via the Pushover API.
NEVER includes patient names, MRNs, or other PHI in messages.

Feature: F5 (Inbox Monitor notifications)
Feature: F5b (Critical value bypass)
Feature: F7b (Callback reminders)
"""

import logging
from datetime import datetime, timedelta, timezone

import config

logger = logging.getLogger('agent.notifier')


def _is_quiet_hours():
    """Return True if current local time is within quiet hours."""
    now_hour = datetime.now().hour
    start = getattr(config, 'NOTIFY_QUIET_HOURS_START', 22)
    end = getattr(config, 'NOTIFY_QUIET_HOURS_END', 7)

    if start < end:
        return start <= now_hour < end
    else:
        # Wraps midnight (e.g. 22:00 → 07:00)
        return now_hour >= start or now_hour < end


def send_inbox_notification(user_id, summary):
    """
    Send a Pushover notification with inbox counts.

    Parameters
    ----------
    user_id : int
        For logging only — not included in the message.
    summary : dict
        Output from read_inbox(): new_count, critical_flags, counts, etc.
    """
    user_key = getattr(config, 'PUSHOVER_USER_KEY', '')
    api_token = getattr(config, 'PUSHOVER_API_TOKEN', '')

    if not user_key or not api_token:
        logger.warning('Pushover keys not configured — skipping notification')
        return

    new_count = summary.get('new_count', 0)
    critical_flags = summary.get('critical_flags', 0)
    counts = summary.get('counts', {})

    # Nothing new — no notification needed
    if new_count == 0 and critical_flags == 0:
        return

    # Build message — counts only, NEVER PHI
    parts = []
    if counts.get('lab', 0):
        parts.append(f'New labs: {counts["lab"]}')
    if counts.get('chart', 0):
        parts.append(f'New charts: {counts["chart"]}')
    if counts.get('message', 0):
        parts.append(f'New messages: {counts["message"]}')
    if counts.get('radiology', 0):
        parts.append(f'New radiology: {counts["radiology"]}')
    if counts.get('refill', 0):
        parts.append(f'New refills: {counts["refill"]}')

    held = summary.get('total_unresolved', 0)
    if held:
        parts.append(f'Held: {held}')

    message = ', '.join(parts) if parts else f'{new_count} new inbox item(s)'

    # Critical value — immediate high-priority notification
    if critical_flags > 0:
        _send_pushover(
            user_key, api_token,
            title='⚠ CRITICAL VALUE',
            message='CRITICAL VALUE in inbox — Log in immediately to review',
            priority=1,
            sound='siren',
        )
        # F21b: create in-app critical notification for escalation tracking
        try:
            from models.notification import Notification
            from models import db
            crit_notif = Notification(
                user_id=user_id,
                message='CRITICAL VALUE in inbox — Log in immediately to review',
                is_critical=True,
                priority=1,
            )
            db.session.add(crit_notif)
            db.session.commit()
        except Exception as e:
            logger.warning(f'Could not create critical notification record: {e}')
        return

    # Respect quiet hours for non-critical notifications
    if _is_quiet_hours():
        logger.info(f'Quiet hours — suppressing notification for user {user_id}')
        return

    _send_pushover(user_key, api_token, title='CareCompanion Inbox', message=message)


def _send_pushover(user_key, api_token, title, message, priority=0, sound='pushover'):
    """Send a single Pushover notification."""
    try:
        import urllib.request
        import urllib.parse

        data = urllib.parse.urlencode({
            'token': api_token,
            'user': user_key,
            'title': title,
            'message': message,
            'priority': priority,
            'sound': sound,
        }).encode('utf-8')

        req = urllib.request.Request('https://api.pushover.net/1/messages.json', data=data)
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                logger.info(f'Pushover notification sent: {title}')
            else:
                logger.warning(f'Pushover returned status {resp.status}')
    except Exception as e:
        logger.error(f'Pushover notification failed: {e}')


# ======================================================================
# F7b: Callback reminder notifications
# ======================================================================
def get_overdue_callback_count(user_id):
    """Return count of overdue callbacks for a user (for morning briefing)."""
    from models.oncall import OnCallNote

    now = datetime.now(timezone.utc)
    return OnCallNote.query.filter(
        OnCallNote.user_id == user_id,
        OnCallNote.callback_promised.is_(True),
        OnCallNote.callback_completed.is_(False),
        OnCallNote.callback_by <= now,
    ).count()


def check_callback_reminders(user_id):
    """
    Send Pushover notification for callbacks due within 30 minutes.
    Called periodically by the scheduler.
    De-identified: uses patient_identifier shorthand, NOT MRN/name.
    """
    from models.oncall import OnCallNote

    user_key = getattr(config, 'PUSHOVER_USER_KEY', '')
    api_token = getattr(config, 'PUSHOVER_API_TOKEN', '')
    if not user_key or not api_token:
        return

    now = datetime.now(timezone.utc)
    window = now + timedelta(minutes=30)

    upcoming = OnCallNote.query.filter(
        OnCallNote.user_id == user_id,
        OnCallNote.callback_promised.is_(True),
        OnCallNote.callback_completed.is_(False),
        OnCallNote.callback_by > now,
        OnCallNote.callback_by <= window,
    ).all()

    for note in upcoming:
        identifier = note.patient_identifier or 'a patient'
        _send_pushover(
            user_key, api_token,
            title='Callback Due Soon',
            message=f'Callback due in ~30 min for {identifier}',
            priority=0,
            sound='pushover',
        )


# ======================================================================
# F21b: Escalating alerts — re-send unacknowledged critical notifications
# ======================================================================
ESCALATION_INTERVAL_MINUTES = 5
MAX_ESCALATIONS = 3


def check_escalations():
    """
    Re-send Pushover notification for unacknowledged critical alerts.
    Called every 2 minutes by the scheduler. Escalates up to MAX_ESCALATIONS
    times with ESCALATION_INTERVAL_MINUTES between each.
    """
    from models.notification import Notification
    from models import db

    user_key = getattr(config, 'PUSHOVER_USER_KEY', '')
    api_token = getattr(config, 'PUSHOVER_API_TOKEN', '')
    if not user_key or not api_token:
        return

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=ESCALATION_INTERVAL_MINUTES)

    # Find critical notifications that are unacknowledged and due for escalation
    unacked = Notification.query.filter(
        Notification.is_critical.is_(True),
        Notification.acknowledged_at.is_(None),
        Notification.escalation_count < MAX_ESCALATIONS,
    ).all()

    for notif in unacked:
        # Check if enough time has passed since last escalation (or creation)
        last_time = notif.last_escalated_at or notif.created_at
        if last_time and last_time > cutoff:
            continue  # not yet time to re-send

        notif.escalation_count = (notif.escalation_count or 0) + 1
        notif.last_escalated_at = now
        db.session.commit()

        _send_pushover(
            user_key, api_token,
            title=f'⚠ CRITICAL VALUE (escalation {notif.escalation_count}/{MAX_ESCALATIONS})',
            message='UNACKNOWLEDGED critical value — Please review immediately',
            priority=1,
            sound='siren',
        )
        logger.info(f'Escalated critical notification {notif.id} (count={notif.escalation_count})')


# ======================================================================
# Morning briefing Pushover notification (no PHI — counts only)
# ======================================================================
def send_briefing_notification(appointment_count, gap_count, recall_count=0, overlap_count=0):
    """
    Send a morning briefing summary via Pushover.
    Only transmits aggregate counts — no patient identifiers.
    """
    user_key = getattr(config, 'PUSHOVER_USER_KEY', '')
    api_token = getattr(config, 'PUSHOVER_API_TOKEN', '')
    if not user_key or not api_token:
        logger.debug('Pushover not configured — skipping briefing notification')
        return

    lines = [
        f'📅 {appointment_count} appointment{"s" if appointment_count != 1 else ""} today',
    ]
    if gap_count > 0:
        lines.append(f'⚠ {gap_count} open care gap{"s" if gap_count != 1 else ""}')
    if recall_count > 0:
        lines.append(f'🔴 {recall_count} active recall alert{"s" if recall_count != 1 else ""}')
    if overlap_count > 0:
        lines.append(f'⏰ {overlap_count} schedule overlap{"s" if overlap_count != 1 else ""}')

    message = '\n'.join(lines)
    _send_pushover(user_key, api_token, title='☀ Morning Briefing', message=message, priority=0)

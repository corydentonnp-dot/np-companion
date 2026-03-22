"""
CareCompanion — End-of-Day Checker (F20)

File location: carecompanion/agent/eod_checker.py

Queries the local DB for unfinished work items and returns a
summary dict.  Optionally sends a Pushover notification via
agent/notifier.py if anything needs attention.

NO AC automation or OCR — purely database queries.
"""

import logging
from datetime import date, datetime, timezone

logger = logging.getLogger('agent.eod_checker')


# Default EOD checklist categories — provider can customize via Settings
DEFAULT_EOD_CATEGORIES = [
    {'key': 'pending_orders',    'label': 'Open Orders',        'emoji': '📋', 'level': 'danger'},
    {'key': 'pending_messages',  'label': 'Pending Messages',   'emoji': '✉️', 'level': 'danger'},
    {'key': 'inbox_items',       'label': 'Inbox Items',        'emoji': '📥', 'level': 'warning'},
    {'key': 'overdue_ticklers',  'label': 'Overdue Ticklers',   'emoji': '⏰', 'level': 'danger'},
    {'key': 'due_today_ticklers','label': 'Due-Today Ticklers', 'emoji': '📅', 'level': 'warning'},
]


def _get_enabled_categories(user_id):
    """Return the list of enabled EOD category keys for the user."""
    try:
        from models.user import User
        from models import db
        user = db.session.get(User, user_id)
        if user:
            custom = user.get_pref('eod_checklist_items', None)
            if custom is not None and isinstance(custom, list):
                return custom
    except Exception:
        pass
    return [c['key'] for c in DEFAULT_EOD_CATEGORIES]


def run_eod_check(user_id):
    """
    Run all end-of-day checks for the given user.

    Returns
    -------
    dict
        {
            'pending_orders': int,
            'pending_messages': int,
            'inbox_items': int,
            'overdue_ticklers': int,
            'due_today_ticklers': int,
            'all_clear': bool,
            'total_issues': int,
            'enabled_categories': list of category dicts,
        }
    """
    from models.orderset import OrderExecution
    from models.message import DelayedMessage
    from models.inbox import InboxSnapshot
    from models.tickler import Tickler

    today = date.today()
    enabled_keys = _get_enabled_categories(user_id)

    # 1. Open order executions (in_progress)
    pending_orders = 0
    if 'pending_orders' in enabled_keys:
        pending_orders = (
            OrderExecution.query
            .filter_by(user_id=user_id, status='in_progress')
            .count()
        )

    # 2. Pending delayed messages
    pending_messages = 0
    if 'pending_messages' in enabled_keys:
        pending_messages = (
            DelayedMessage.query
            .filter_by(user_id=user_id, status='pending')
            .count()
        )

    # 3. Latest inbox snapshot — sum of category counts
    inbox_items = 0
    if 'inbox_items' in enabled_keys:
        latest_snap = (
            InboxSnapshot.query
            .filter_by(user_id=user_id)
            .order_by(InboxSnapshot.captured_at.desc())
            .first()
        )
        if latest_snap:
            for attr in ('labs_count', 'radiology_count', 'messages_count',
                          'chart_notes_count', 'refills_count', 'other_count'):
                inbox_items += getattr(latest_snap, attr, 0) or 0

    # 4. Overdue ticklers (due before today, not completed)
    overdue_ticklers = 0
    if 'overdue_ticklers' in enabled_keys:
        overdue_ticklers = (
            Tickler.query
            .filter(
                Tickler.user_id == user_id,
                Tickler.due_date < today,
                Tickler.completed_at.is_(None),
            )
            .count()
        )

    # 5. Ticklers due today (not completed)
    due_today_ticklers = 0
    if 'due_today_ticklers' in enabled_keys:
        due_today_ticklers = (
            Tickler.query
            .filter(
                Tickler.user_id == user_id,
                Tickler.due_date == today,
                Tickler.completed_at.is_(None),
            )
            .count()
        )

    total = pending_orders + pending_messages + inbox_items + overdue_ticklers + due_today_ticklers

    # Build the list of enabled category dicts with counts
    all_counts = {
        'pending_orders': pending_orders,
        'pending_messages': pending_messages,
        'inbox_items': inbox_items,
        'overdue_ticklers': overdue_ticklers,
        'due_today_ticklers': due_today_ticklers,
    }
    cat_lookup = {c['key']: c for c in DEFAULT_EOD_CATEGORIES}
    enabled_categories = []
    for key in enabled_keys:
        if key in cat_lookup:
            cat = dict(cat_lookup[key])
            cat['count'] = all_counts.get(key, 0)
            enabled_categories.append(cat)

    return {
        'pending_orders': pending_orders,
        'pending_messages': pending_messages,
        'inbox_items': inbox_items,
        'overdue_ticklers': overdue_ticklers,
        'due_today_ticklers': due_today_ticklers,
        'all_clear': total == 0,
        'total_issues': total,
        'enabled_categories': enabled_categories,
    }


def send_eod_notification(user_id):
    """
    Run the EOD check and, if issues found, send a Pushover notification.

    Only sends if the user has notify_eod_reminder enabled.
    """
    from models.user import User
    from models import db
    from agent.notifier import _send_pushover
    import config

    user = db.session.get(User, user_id)
    if not user or not user.is_active_account:
        return

    prefs = user.preferences or {}
    if not prefs.get('notify_eod_reminder', True):
        return

    result = run_eod_check(user_id)
    if result['all_clear']:
        logger.info(f'EOD check for user {user_id}: all clear')
        return

    # Build notification message — counts only, no PHI
    parts = []
    if result['pending_orders']:
        parts.append(f"Open orders: {result['pending_orders']}")
    if result['pending_messages']:
        parts.append(f"Pending messages: {result['pending_messages']}")
    if result['inbox_items']:
        parts.append(f"Inbox items: {result['inbox_items']}")
    if result['overdue_ticklers']:
        parts.append(f"Overdue ticklers: {result['overdue_ticklers']}")
    if result['due_today_ticklers']:
        parts.append(f"Due-today ticklers: {result['due_today_ticklers']}")

    message = ', '.join(parts)

    user_key = getattr(config, 'PUSHOVER_USER_KEY', '')
    api_token = getattr(config, 'PUSHOVER_API_TOKEN', '')
    if not user_key or not api_token:
        logger.warning('Pushover keys not configured — skipping EOD notification')
        return

    _send_pushover(
        user_key, api_token,
        title='🌙 End-of-Day Check',
        message=f'{result["total_issues"]} item(s) need attention: {message}',
    )
    logger.info(f'EOD notification sent for user {user_id}: {result["total_issues"]} items')

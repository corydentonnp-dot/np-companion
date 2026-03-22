"""
CareCompanion — Inbox Monitor Wrapper

File location: carecompanion/agent/inbox_monitor.py

Thin wrapper that the agent scheduler calls. Coordinates the
inbox reader and notifier.

Feature: F5 (Inbox Monitor)
"""

import logging
from agent.inbox_reader import read_inbox
from agent.notifier import send_inbox_notification

logger = logging.getLogger('agent.inbox_monitor')


def run_inbox_monitor(user_id):
    """
    Called by agent.py's job_inbox_check().

    1. Read the inbox via OCR
    2. If new items exist, send notification
    3. Return summary dict
    """
    summary = read_inbox(user_id)

    if summary.get('new_count', 0) > 0 or summary.get('critical_flags', 0) > 0:
        send_inbox_notification(user_id, summary)

    return summary

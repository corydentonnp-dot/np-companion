"""
CareCompanion — Lab Track Service

Overdue lab check logic extracted from routes/labtrack.py (Band 3 B1.11).
"""

import logging
from datetime import datetime, timedelta, timezone

from models import db
from models.labtrack import LabTrack

logger = logging.getLogger(__name__)


def check_overdue_labs(user_id):
    """
    Check all LabTrack entries for overdue labs and flag them.

    Called daily at 6 AM by the scheduler.
    Returns count of newly-flagged overdue entries.
    """
    now = datetime.now(timezone.utc)
    count = 0

    tracks = LabTrack.query.filter_by(user_id=user_id, is_archived=False).all()
    for t in tracks:
        was_overdue = t.is_overdue
        if t.last_checked and t.interval_days:
            next_due = t.last_checked + timedelta(days=t.interval_days)
            t.is_overdue = now > next_due
        else:
            t.is_overdue = False

        if t.is_overdue and not was_overdue:
            count += 1

    db.session.commit()
    return count

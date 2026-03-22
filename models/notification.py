"""
CareCompanion — Notification Model

Stores in-app notifications sent by admins or the system to users.
"""

from datetime import datetime, timezone
from models import db

# Pre-built notification templates
NOTIFICATION_TEMPLATES = {
    'meeting': 'Reminder: Staff meeting today at {time}.',
    'maintenance': 'System maintenance scheduled for {date}. Please save your work.',
    'policy_update': 'A new office policy has been posted. Please review at your earliest convenience.',
    'schedule_change': 'Your schedule has been updated. Please check your appointments.',
    'training': 'Mandatory training session: {topic}. Date: {date}.',
    'custom': '',
}

# Phase 12: Default priority per notification type
# 1 = P1 (interrupt), 2 = P2 (passive sidebar), 3 = P3 (morning-only)
NOTIFICATION_PRIORITY_DEFAULTS = {
    'critical_value': 1,
    'meeting': 1,
    'lab_result': 2,
    'radiology_result': 2,
    'inbox_message': 2,
    'schedule_change': 2,
    'policy_update': 3,
    'training': 3,
    'maintenance': 3,
    'eod_reminder': 3,
    'morning_briefing': 3,
    'custom': 2,
}


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # Scheduled send — if set, notification is not visible until this time
    scheduled_for = db.Column(db.DateTime, nullable=True)
    # Template name used (for history/audit)
    template_name = db.Column(db.String(80), default='')

    # Phase 12: Three-tier priority (1=interrupt, 2=passive, 3=morning-only)
    priority = db.Column(db.Integer, default=2)

    # F21b: Escalating alerts for critical values
    is_critical = db.Column(db.Boolean, default=False)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    escalation_count = db.Column(db.Integer, default=0)
    last_escalated_at = db.Column(db.DateTime, nullable=True)

    # Phase 12.6: Composite index for fast P1 polling (<50ms)
    __table_args__ = (
        db.Index('ix_notif_p1_poll', 'user_id', 'priority', 'acknowledged_at'),
    )

    user = db.relationship('User', foreign_keys=[user_id], backref='notifications', lazy=True)
    sender = db.relationship('User', foreign_keys=[sender_id], lazy=True)

    def __repr__(self):
        return f'<Notification {self.id} to={self.user_id} p={self.priority}>'

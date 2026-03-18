"""
NP Companion — Notification Model

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

    user = db.relationship('User', foreign_keys=[user_id], backref='notifications', lazy=True)
    sender = db.relationship('User', foreign_keys=[sender_id], lazy=True)

    def __repr__(self):
        return f'<Notification {self.id} to={self.user_id}>'

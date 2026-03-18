"""
NP Companion — Delayed Message Queue Model

File location: np-companion/models/message.py

Messages that the provider writes now but wants sent later via
NetPractice (through the Playwright scraper).  The scheduler picks
up pending messages at their scheduled_send_at time and hands them
to the scraper for delivery.

HIPAA note: message_content may contain clinical details —
it is stored locally and transmitted only through the encrypted
NetPractice session, never through any cloud API.
"""

from datetime import datetime, timezone
from models import db


class DelayedMessage(db.Model):
    """
    One queued message.  Status flow:
      pending → sent       (normal path)
      pending → failed     (scraper error — retry manually)
      pending → cancelled  (user cancelled before send time)
    """
    __tablename__ = 'delayed_messages'

    # ---- Primary key -----------------------------------------------------
    id = db.Column(db.Integer, primary_key=True)

    # ---- Who created this message ----------------------------------------
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )

    # ---- Message content -------------------------------------------------
    recipient_identifier = db.Column(db.String(150), nullable=False)
    message_content = db.Column(db.Text, nullable=False)

    # ---- Scheduling ------------------------------------------------------
    scheduled_send_at = db.Column(db.DateTime, nullable=False, index=True)

    # ---- Status tracking -------------------------------------------------
    # Values: 'pending', 'sent', 'failed', 'cancelled'
    status = db.Column(db.String(20), nullable=False, default='pending')

    sent_at = db.Column(db.DateTime, nullable=True)
    delivery_confirmed = db.Column(db.Boolean, default=False)

    # ---- Timestamps ------------------------------------------------------
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # ---- Relationships ---------------------------------------------------
    user = db.relationship('User', backref='delayed_messages', lazy=True)

    def __repr__(self):
        return f'<DelayedMessage {self.id} status={self.status}>'

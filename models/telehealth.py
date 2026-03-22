"""
CareCompanion — Communication Log Model
File: models/telehealth.py

Phase 25.2 — Patient communication logging for phone E/M,
portal messages, and telehealth encounter tracking.
"""

from datetime import datetime, timezone
from models import db


class CommunicationLog(db.Model):
    """Tracks patient phone calls, portal messages, and telehealth encounters."""
    __tablename__ = 'communication_log'

    id = db.Column(db.Integer, primary_key=True)
    patient_mrn_hash = db.Column(db.String(64), nullable=False, index=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )

    # Communication details
    communication_type = db.Column(
        db.String(30), nullable=False,
        doc='phone_call | portal_message | secure_message | video_visit'
    )
    initiated_by = db.Column(
        db.String(20), default='provider',
        doc='patient | provider | staff'
    )

    # Timing
    start_datetime = db.Column(db.DateTime, nullable=True)
    end_datetime = db.Column(db.DateTime, nullable=True)
    cumulative_minutes = db.Column(db.Integer, default=0)

    # Clinical content
    clinical_decision_made = db.Column(db.Boolean, default=False)
    topic = db.Column(db.String(200), default='')

    # Billing linkage
    resulted_in_visit = db.Column(db.Boolean, default=False)
    visit_date_after = db.Column(db.Date, nullable=True)
    billable_code = db.Column(db.String(10), default='')
    billing_status = db.Column(
        db.String(20), default='pending',
        doc='pending | billable | billed | excluded'
    )

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = db.relationship('User', backref='communication_logs', lazy=True)

    def __repr__(self):
        return (
            f'<CommunicationLog {self.id} '
            f'{self.communication_type} {self.cumulative_minutes}min>'
        )

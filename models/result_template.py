"""
CareCompanion — Result Response Template Model

File location: carecompanion/models/result_template.py

Pre-built message templates for common result responses (F19).
Providers select a template when composing a delayed message,
and placeholders like {patient_name}, {test_name}, {result_value}
are substituted before sending.
"""

from datetime import datetime, timezone
from models import db


class ResultTemplate(db.Model):
    """
    One reusable message template.

    Categories: normal, abnormal, critical, follow_up, referral
    """
    __tablename__ = 'result_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    body_template = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # F19a — Shared Template Library columns
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    is_shared = db.Column(db.Boolean, default=False)
    copied_from_id = db.Column(db.Integer, db.ForeignKey('result_templates.id'), nullable=True)
    legal_reviewed = db.Column(db.Boolean, default=False)
    legal_reviewed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', foreign_keys=[user_id], lazy=True)

    def __repr__(self):
        return f'<ResultTemplate {self.id} {self.category}/{self.name}>'

"""
NP Companion — Audit Log Model

File location: np-companion/models/audit.py

Stores a record of every authenticated page view and API call.
Used by the admin audit-log page for compliance review.

HIPAA note: This table stores the action taken and the module
accessed, but NEVER stores patient identifiers.  MRNs and
patient names must not appear in the 'action' column.
"""

from datetime import datetime, timezone
from models import db


class AuditLog(db.Model):
    """
    One row per HTTP request made by a logged-in user.
    Written automatically by the after_request hook in app.py.
    """
    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)

    # Who performed the action
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # When it happened (UTC)
    timestamp = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    # What they did — e.g. 'GET /dashboard', 'POST /api/verify-pin'
    action = db.Column(db.String(200), nullable=False)

    # Which module the route belongs to — e.g. 'auth', 'timer', 'inbox'
    module = db.Column(db.String(50), default='')

    # Client IP address (for multi-device tracking)
    ip_address = db.Column(db.String(45), default='')

    def __repr__(self):
        return f'<AuditLog {self.id} user={self.user_id} {self.action}>'

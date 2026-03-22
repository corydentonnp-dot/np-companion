"""
CareCompanion — On-Call Note Model

File location: carecompanion/models/oncall.py

Stores after-hours and weekend call notes.  These are entered on
the provider's phone via Tailscale and reviewed the next morning.

HIPAA note: patient_identifier is the provider's own shorthand
(e.g. "Smith knee pain") — never an MRN or date of birth.
The full clinical note stays in Amazing Charts; this is a
reminder/tracking record only.
"""

from datetime import datetime, timezone
from models import db


class OnCallNote(db.Model):
    """
    One row per after-hours call.  Tracks the call, whether a
    callback was promised, and whether the encounter was documented
    back in Amazing Charts.
    """
    __tablename__ = 'oncall_notes'

    # ---- Primary key -----------------------------------------------------
    id = db.Column(db.Integer, primary_key=True)

    # ---- Who took the call -----------------------------------------------
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )

    # ---- Patient shorthand (NOT an MRN or full name) ---------------------
    patient_identifier = db.Column(db.String(120), default='')

    # ---- Call details ----------------------------------------------------
    call_time = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    chief_complaint = db.Column(db.String(200), default='')
    recommendation = db.Column(db.Text, default='')

    # ---- Callback tracking -----------------------------------------------
    callback_promised = db.Column(db.Boolean, default=False)
    callback_by = db.Column(db.DateTime, nullable=True)
    callback_completed = db.Column(db.Boolean, default=False)

    # ---- Documentation status --------------------------------------------
    # Values: 'pending', 'entered', 'not_needed'
    documentation_status = db.Column(
        db.String(20), nullable=False, default='pending'
    )

    # ---- Full note content -----------------------------------------------
    note_content = db.Column(db.Text, default='')

    # ---- Forwarding ------------------------------------------------------
    forwarded_to = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=True
    )
    forwarded_at = db.Column(db.DateTime, nullable=True)

    # ---- Timestamps ------------------------------------------------------
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # ---- Relationships ---------------------------------------------------
    user = db.relationship('User', backref='oncall_notes', lazy=True,
                           foreign_keys=[user_id])
    forwarded_user = db.relationship('User', foreign_keys=[forwarded_to],
                                     lazy=True)

    def __repr__(self):
        return f'<OnCallNote {self.id} status={self.documentation_status}>'


class HandoffLink(db.Model):
    """
    Temporary read-only link for sharing de-identified on-call handoff
    summaries with colleagues.  Expires after 1 hour.
    """
    __tablename__ = 'handoff_links'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False
    )
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    summary_json = db.Column(db.Text, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<HandoffLink {self.id} expires={self.expires_at}>'

"""
CareCompanion — Tickler (Follow-Up Reminder) Model

File location: carecompanion/models/tickler.py

A three-column dashboard item: upcoming | overdue | completed.
Providers create ticklers for patient follow-ups; MAs can be
assigned tasks via assigned_to_user_id.

HIPAA note: patient_display is a non-PHI label the provider
types (e.g. "DM follow-up").  Full MRN is stored separately
for internal lookups but shown only as last 4 digits in the UI.
"""

from datetime import datetime, timezone
from models import db


class Tickler(db.Model):
    """
    One follow-up reminder.  Can be one-time or recurring.
    Recurring ticklers auto-generate a fresh copy when completed.
    """
    __tablename__ = 'ticklers'

    # ---- Primary key -----------------------------------------------------
    id = db.Column(db.Integer, primary_key=True)

    # ---- Owner (provider who created it) ---------------------------------
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )

    # ---- MA delegation (nullable = unassigned) ---------------------------
    assigned_to_user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=True
    )

    # ---- Patient reference -----------------------------------------------
    mrn = db.Column(db.String(20), default='')
    patient_display = db.Column(db.String(120), default='')

    # ---- Reminder details ------------------------------------------------
    due_date = db.Column(db.DateTime, nullable=False, index=True)

    # routine, important, or urgent
    priority = db.Column(db.String(20), default='routine')

    notes = db.Column(db.Text, default='')

    # ---- Status ----------------------------------------------------------
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    # ---- Recurrence ------------------------------------------------------
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_interval_days = db.Column(db.Integer, nullable=True)

    # ---- Timestamps ------------------------------------------------------
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # ---- Relationships ---------------------------------------------------
    # Two FKs to users: owner and assignee
    user = db.relationship(
        'User', foreign_keys=[user_id], backref='ticklers_created', lazy=True
    )
    assignee = db.relationship(
        'User', foreign_keys=[assigned_to_user_id],
        backref='ticklers_assigned', lazy=True
    )

    def __repr__(self):
        return f'<Tickler {self.id} due={self.due_date} priority={self.priority}>'

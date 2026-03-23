"""
CareCompanion — Time Log Model

File location: carecompanion/models/timelog.py

Tracks how long a provider spends in each patient chart.  The MRN
reader agent creates session_start records automatically; the
provider or agent writes session_end when the chart closes.

Face-to-face timing is a separate manual toggle used for billing
calculations (time-based E&M coding).

HIPAA note: Full MRN is stored here for billing accuracy.
Display in the UI should show only the last 4 digits.
"""

from datetime import datetime, timezone
from models import db


class TimeLog(db.Model):
    """
    One row per chart-open session.  The agent creates the row on
    session_start and updates session_end when the chart closes.
    """
    __tablename__ = 'time_logs'

    # ---- Primary key -----------------------------------------------------
    id = db.Column(db.Integer, primary_key=True)

    # ---- Who and which patient -------------------------------------------
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    mrn = db.Column(db.String(20), nullable=False, index=True)

    # ---- Session timing --------------------------------------------------
    session_start = db.Column(db.DateTime, nullable=False)
    session_end = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, default=0)

    # ---- Visit metadata --------------------------------------------------
    visit_type = db.Column(db.String(50), default='')
    visit_type_source = db.Column(db.String(10), default='')   # 'auto' or 'manual' (F12a)
    is_complex = db.Column(db.Boolean, default=False)
    complexity_notes = db.Column(db.Text, default='')           # (F12b)

    # ---- Face-to-face timing (manual toggle) -----------------------------
    face_to_face_start = db.Column(db.DateTime, nullable=True)
    face_to_face_end = db.Column(db.DateTime, nullable=True)
    face_to_face_seconds = db.Column(db.Integer, default=0)

    # ---- Idle / manual flags (Phase 2) ----------------------------------
    total_idle_seconds = db.Column(db.Integer, default=0)
    manual_entry = db.Column(db.Boolean, default=False)

    # ---- Billing ---------------------------------------------------------
    billed_level = db.Column(db.String(10), default='')
    billing_notes = db.Column(db.Text, default='')

    # ---- AWV Interactive Checklist (F16a) --------------------------------
    awv_checklist = db.Column(db.Text, nullable=True)  # JSON: {"hra": true, ...}

    # ---- Timestamps ------------------------------------------------------
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # ---- Relationships ---------------------------------------------------
    user = db.relationship('User', backref='time_logs', lazy=True)

    def __repr__(self):
        return f'<TimeLog {self.id} user={self.user_id} mrn={self.mrn or ""}>'

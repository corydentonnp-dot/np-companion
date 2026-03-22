"""
CareCompanion — TCM Watch Models
File: models/tcm.py
Phase 19.1

Tracks Transitional Care Management (TCM) workflows from hospital
discharge through billing.  TCM = highest per-event revenue
($280 for 99495, $230 for 99496).

Deadlines:
  - 2-business-day contact after discharge
  - 7-day (high complexity) or 14-day (moderate) face-to-face visit
  - Medication reconciliation required before billing
"""

from datetime import datetime, timezone, timedelta
from models import db


class TCMWatchEntry(db.Model):
    """
    A single TCM tracking entry for a discharged patient.
    Created when a discharge is detected (inbox monitor or manual entry).
    """

    __tablename__ = "tcm_watch_entry"

    id = db.Column(db.Integer, primary_key=True)
    patient_mrn_hash = db.Column(db.String(64), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    discharge_date = db.Column(db.Date, nullable=False)
    discharge_facility = db.Column(db.String(200), nullable=True)
    discharge_summary_received = db.Column(db.Boolean, default=False)

    # --- 2-business-day contact deadline ---
    two_day_deadline = db.Column(db.Date, nullable=True)
    two_day_contact_completed = db.Column(db.Boolean, default=False)
    two_day_contact_date = db.Column(db.Date, nullable=True)
    two_day_contact_method = db.Column(
        db.String(30), nullable=True
    )  # phone | portal | in_person

    # --- Face-to-face visit deadlines ---
    fourteen_day_visit_deadline = db.Column(db.Date, nullable=True)
    seven_day_visit_deadline = db.Column(db.Date, nullable=True)
    face_to_face_completed = db.Column(db.Boolean, default=False)
    face_to_face_date = db.Column(db.Date, nullable=True)

    # --- TCM code eligibility ---
    tcm_code_eligible = db.Column(
        db.String(10), nullable=True
    )  # '99495' | '99496' | 'expired'
    tcm_billed = db.Column(db.Boolean, default=False)

    # --- Medication reconciliation ---
    med_reconciliation_completed = db.Column(db.Boolean, default=False)

    # --- Status ---
    status = db.Column(
        db.String(20), default="active"
    )  # active | completed | expired | cancelled
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def compute_deadlines(self):
        """Compute deadline dates from discharge_date."""
        if not self.discharge_date:
            return
        d = self.discharge_date
        # 2-business-day contact: skip weekends
        self.two_day_deadline = _add_business_days(d, 2)
        # Visit deadlines
        self.seven_day_visit_deadline = d + timedelta(days=7)
        self.fourteen_day_visit_deadline = d + timedelta(days=14)

    def determine_tcm_code(self):
        """
        Determine eligible TCM code based on visit timing.
        99495 = high complexity (visit within 7 days)
        99496 = moderate complexity (visit within 14 days)
        """
        if not self.face_to_face_completed or not self.face_to_face_date:
            if self.fourteen_day_visit_deadline and self.discharge_date:
                from datetime import date
                if date.today() > self.fourteen_day_visit_deadline:
                    self.tcm_code_eligible = "expired"
            return
        if self.seven_day_visit_deadline and self.face_to_face_date <= self.seven_day_visit_deadline:
            self.tcm_code_eligible = "99495"
        elif self.fourteen_day_visit_deadline and self.face_to_face_date <= self.fourteen_day_visit_deadline:
            self.tcm_code_eligible = "99496"
        else:
            self.tcm_code_eligible = "expired"

    def is_billable(self):
        """Check if all TCM billing requirements are met."""
        return (
            self.two_day_contact_completed
            and self.face_to_face_completed
            and self.med_reconciliation_completed
            and self.tcm_code_eligible in ("99495", "99496")
            and not self.tcm_billed
        )

    def __repr__(self):
        return f"<TCMWatchEntry {self.id} patient={self.patient_mrn_hash[:8]}... status={self.status}>"


def _add_business_days(start_date, days):
    """Add N business days to a date, skipping weekends."""
    current = start_date
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Mon-Fri
            added += 1
    return current

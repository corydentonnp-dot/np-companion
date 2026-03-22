"""
CareCompanion — CCM Enrollment + Time Tracking Models
File: models/ccm.py
Phase 19.8, 19.9

Chronic Care Management (CCM) — $62/month × panel size.
Highest recurring revenue opportunity.

Requirements:
  - Patient consent (verbal or written) before billing
  - Individualized care plan
  - ≥20 minutes of non-face-to-face clinical staff time per month
  - 2+ chronic conditions expected to last ≥12 months
"""

from datetime import datetime, timezone
from models import db


class CCMEnrollment(db.Model):
    """
    CCM enrollment record for a patient.
    Tracks consent, care plan, and billing status.
    """

    __tablename__ = "ccm_enrollment"

    id = db.Column(db.Integer, primary_key=True)
    patient_mrn_hash = db.Column(db.String(64), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    enrollment_date = db.Column(db.Date, nullable=True)
    consent_date = db.Column(db.Date, nullable=True)
    consent_method = db.Column(
        db.String(30), nullable=True
    )  # verbal | written | portal
    care_plan_date = db.Column(db.Date, nullable=True)

    # JSON list of qualifying conditions: [{"code": "I10", "description": "HTN"}, ...]
    qualifying_conditions = db.Column(db.Text, nullable=True)

    monthly_time_goal = db.Column(db.Integer, default=20)  # minutes

    status = db.Column(
        db.String(20), default="pending"
    )  # pending | active | inactive | disenrolled

    last_billed_month = db.Column(
        db.String(7), nullable=True
    )  # 'YYYY-MM' format
    total_billed_months = db.Column(db.Integer, default=0)

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationship to time entries
    time_entries = db.relationship(
        "CCMTimeEntry", backref="enrollment", lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def get_qualifying_conditions(self):
        """Parse qualifying_conditions JSON."""
        if not self.qualifying_conditions:
            return []
        import json
        try:
            return json.loads(self.qualifying_conditions)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_qualifying_conditions(self, conditions):
        """Set qualifying_conditions from list of dicts."""
        import json
        self.qualifying_conditions = json.dumps(conditions)

    def is_billing_ready(self, month_str=None):
        """
        Check if enrollment meets billing requirements for a given month.
        month_str: 'YYYY-MM' format, defaults to current month.
        """
        if self.status != "active":
            return False
        if not self.consent_date:
            return False
        if not self.care_plan_date:
            return False

        conditions = self.get_qualifying_conditions()
        if len(conditions) < 2:
            return False

        # Check if already billed for this month
        if month_str and self.last_billed_month == month_str:
            return False

        return True

    def monthly_minutes(self, year, month):
        """Total billable minutes for a given month."""
        entries = self.time_entries.filter(
            db.extract("year", CCMTimeEntry.entry_date) == year,
            db.extract("month", CCMTimeEntry.entry_date) == month,
            CCMTimeEntry.is_billable == True,  # noqa: E712
        ).all()
        return sum(e.duration_minutes for e in entries)

    def __repr__(self):
        return f"<CCMEnrollment {self.id} patient={self.patient_mrn_hash[:8]}... status={self.status}>"


class CCMTimeEntry(db.Model):
    """
    Individual CCM time log entry.
    Accumulated monthly to reach 20-minute billing threshold.
    """

    __tablename__ = "ccm_time_entry"

    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(
        db.Integer, db.ForeignKey("ccm_enrollment.id"), nullable=False, index=True
    )
    entry_date = db.Column(db.Date, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)

    activity_type = db.Column(
        db.String(50), nullable=True
    )  # care_coordination | care_plan_review | medication_mgmt | phone_call | portal_message | referral_followup
    staff_name = db.Column(db.String(100), nullable=True)
    staff_role = db.Column(
        db.String(30), nullable=True
    )  # provider | nurse | ma | care_coordinator
    activity_description = db.Column(db.Text, nullable=True)

    is_billable = db.Column(db.Boolean, default=True)

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self):
        return f"<CCMTimeEntry {self.id} enrollment={self.enrollment_id} {self.duration_minutes}min>"

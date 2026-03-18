"""
NP Companion — Care Gap Models

File location: np-companion/models/caregap.py

Two tables:
  - CareGap:       Per-patient preventive care gaps evaluated by the
                   USPSTF rules engine in agent/caregap_engine.py.
  - CareGapRule:   Admin-editable screening rules. Hardcoded defaults
                   are seeded on first run; API-sourced overrides can
                   supersede them.

HIPAA note: Full MRN is stored for clinical accuracy.
Display in the UI should show only the last 4 digits.
"""

from datetime import datetime, timezone
from models import db


class CareGap(db.Model):
    """
    One row per preventive care item per patient.  Updated each
    time the schedule is pulled or the provider manually reviews.
    """
    __tablename__ = 'care_gaps'

    # ---- Primary key -----------------------------------------------------
    id = db.Column(db.Integer, primary_key=True)

    # ---- Who and which patient -------------------------------------------
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    mrn = db.Column(db.String(20), nullable=False, index=True)
    patient_name = db.Column(db.String(200), default='')

    # ---- Gap details -----------------------------------------------------
    gap_type = db.Column(db.String(80), nullable=False)
    gap_name = db.Column(db.String(200), default='')
    description = db.Column(db.Text, default='')

    due_date = db.Column(db.DateTime, nullable=True)
    completed_date = db.Column(db.DateTime, nullable=True)

    # 'open', 'in_progress', 'addressed', 'declined', 'not_applicable'
    status = db.Column(db.String(30), default='open')

    # ---- Provider actions ------------------------------------------------
    is_addressed = db.Column(db.Boolean, default=False)
    addressed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Pre-generated snippet the provider can copy into the note
    documentation_snippet = db.Column(db.Text, default='')

    # Suggested billing code pair (e.g. 'G0438 / G0439')
    billing_code_suggested = db.Column(db.String(40), default='')

    # ---- Timestamps ------------------------------------------------------
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ---- Relationships ---------------------------------------------------
    user = db.relationship('User', backref='care_gaps', lazy=True,
                           foreign_keys=[user_id])
    addressed_user = db.relationship('User', foreign_keys=[addressed_by], lazy=True)

    def __repr__(self):
        return f'<CareGap {self.id} {self.gap_type} status={self.status}>'


class CareGapRule(db.Model):
    """
    Admin-editable screening rule.  Seeded with USPSTF defaults on
    first run.  Admins can edit criteria, intervals, and templates
    from the Admin > Care Gap Rules page.
    """
    __tablename__ = 'care_gap_rules'

    id = db.Column(db.Integer, primary_key=True)

    # Unique key matching CareGap.gap_type (e.g. 'colonoscopy')
    gap_type = db.Column(db.String(80), nullable=False, unique=True)
    gap_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')

    # Criteria stored as JSON for flexible matching:
    # {"min_age": 45, "max_age": 75, "sex": "all", "risk_factors": [...]}
    criteria_json = db.Column(db.Text, default='{}')

    # Days between screenings (0 = one-time)
    interval_days = db.Column(db.Integer, default=365)

    # Billing code pair (e.g. 'G0105 / G0121')
    billing_code_pair = db.Column(db.String(60), default='')

    # Documentation template for closure
    documentation_template = db.Column(db.Text, default='')

    # Source: 'hardcoded' or 'api' — API rules supersede hardcoded
    source = db.Column(db.String(20), default='hardcoded')

    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f'<CareGapRule {self.gap_type} active={self.is_active}>'

"""
CareCompanion — Immunization Series Tracking Model
File: models/immunization.py

Phase 24.1 — Multi-dose vaccine series with dose window tracking,
age eligibility, and seasonal flu/pneumococcal alerts.
"""

from datetime import datetime, timezone
from models import db


class ImmunizationSeries(db.Model):
    """Tracks multi-dose vaccine series status per patient."""
    __tablename__ = 'immunization_series'

    id = db.Column(db.Integer, primary_key=True)
    patient_mrn_hash = db.Column(db.String(64), nullable=False, index=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )

    # Vaccine identification
    vaccine_group = db.Column(db.String(50), nullable=False)   # e.g. 'Shingrix', 'HepB', 'COVID'
    vaccine_cpt = db.Column(db.String(10), default='')         # primary product CPT

    # Dose tracking
    dose_number = db.Column(db.Integer, default=0)             # doses received so far
    total_doses = db.Column(db.Integer, default=1)             # total needed for series
    dose_date = db.Column(db.Date, nullable=True)              # date of most recent dose
    next_dose_due_date = db.Column(db.Date, nullable=True)     # earliest date for next dose
    next_dose_window_end = db.Column(db.Date, nullable=True)   # latest date to still count

    # Status
    series_status = db.Column(
        db.String(20), default='not_started',
        doc='not_started | in_progress | complete | overdue | contraindicated'
    )

    # Age eligibility (denormalized for fast query)
    age_min = db.Column(db.Integer, default=0)
    age_max = db.Column(db.Integer, default=999)

    # Seasonal flag (e.g. flu=Sep-Mar)
    seasonal = db.Column(db.Boolean, default=False)
    season_start_month = db.Column(db.Integer, nullable=True)  # 1-12
    season_end_month = db.Column(db.Integer, nullable=True)    # 1-12

    # Clinical notes
    notes = db.Column(db.Text, default='')

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = db.relationship('User', backref='immunization_series', lazy=True)

    def __repr__(self):
        return (
            f'<ImmunizationSeries {self.id} '
            f'{self.vaccine_group} {self.dose_number}/{self.total_doses} '
            f'{self.series_status}>'
        )

"""
NP Companion — Medication Reference Model

File location: np-companion/models/medication.py

A local formulary / quick-reference for medications organized by
condition.  Entries can be personal (user_id set) or shared with
the whole practice (is_shared = True, user_id = null for
practice-wide entries).

The guideline_review_flag marks entries where the source guideline
may have been updated and a provider should re-verify the
recommendation.
"""

from datetime import datetime, timezone
from models import db


class MedicationEntry(db.Model):
    """
    One medication recommendation for a specific condition.
    Sorted by 'line' (first-line, second-line, third-line).
    """
    __tablename__ = 'medication_entries'

    # ---- Primary key -----------------------------------------------------
    id = db.Column(db.Integer, primary_key=True)

    # ---- Owner (nullable for practice-wide shared entries) ----------------
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=True, index=True
    )

    # ---- Clinical content ------------------------------------------------
    condition = db.Column(db.String(150), nullable=False, index=True)
    drug_name = db.Column(db.String(150), nullable=False)
    drug_class = db.Column(db.String(100), default='')

    # first, second, or third line therapy
    line = db.Column(db.String(20), default='first')

    # ---- Extended notes --------------------------------------------------
    dosing_notes = db.Column(db.Text, default='')
    special_populations = db.Column(db.Text, default='')
    contraindications = db.Column(db.Text, default='')
    monitoring = db.Column(db.Text, default='')
    personal_notes = db.Column(db.Text, default='')

    # ---- Sharing & review ------------------------------------------------
    is_shared = db.Column(db.Boolean, default=False)
    guideline_review_flag = db.Column(db.Boolean, default=False)

    # ---- Timestamps ------------------------------------------------------
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # ---- Relationships ---------------------------------------------------
    user = db.relationship('User', backref='medication_entries', lazy=True)

    def __repr__(self):
        return f'<MedicationEntry {self.id} {self.drug_name} for {self.condition}>'

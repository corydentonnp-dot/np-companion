"""
NP Companion — Tools Models
File: models/tools.py

ORM models for the Tools module features:
- ControlledSubstanceEntry (F25): patient CS registry with fill tracking
- CodeFavorite (F17): provider's saved ICD-10 code favorites
- CodePairing (F17c): ICD-10 code pairing history and suggestions
- PriorAuthorization (F26): PA request history and narrative tracking

Dependencies:
- models/__init__.py (db instance)

HIPAA note: Patient identifiers stored as MRN (internal use only, never
exposed in notifications or logs — use safe_patient_id for logging).
"""

from datetime import datetime, date, timezone, timedelta
from models import db


class ControlledSubstanceEntry(db.Model):
    """
    F25: One row per patient on a controlled substance.
    Tracks fill dates, days supply, PDMP check intervals, and UDS schedules.
    """
    __tablename__ = 'controlled_substance_entry'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    mrn = db.Column(db.String(20), nullable=False, index=True)
    patient_name = db.Column(db.String(200), default='')

    # Medication details
    drug_name = db.Column(db.String(200), nullable=False)
    rxnorm_cui = db.Column(db.String(20), default='')
    dea_schedule = db.Column(db.String(10), default='')  # II, III, IV, V
    dose = db.Column(db.String(100), default='')
    quantity = db.Column(db.Integer, default=0)
    days_supply = db.Column(db.Integer, default=30)

    # Fill tracking
    last_fill_date = db.Column(db.Date, nullable=True)
    next_fill_date = db.Column(db.Date, nullable=True)  # Computed: last_fill_date + days_supply

    # PDMP / UDS monitoring
    pdmp_check_interval_days = db.Column(db.Integer, default=90)  # Default: every 3 months
    last_pdmp_check = db.Column(db.Date, nullable=True)
    uds_interval_days = db.Column(db.Integer, default=180)  # Default: every 6 months
    last_uds_date = db.Column(db.Date, nullable=True)

    # Status
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, default='')

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<CSEntry {self.drug_name} MRN={self.mrn}>'

    @property
    def days_until_refill(self):
        """Days until earliest refill. Negative = past due."""
        if not self.next_fill_date:
            return None
        return (self.next_fill_date - date.today()).days

    @property
    def refill_status(self):
        """Return status string: 'available', 'too_early', 'overdue', 'unknown'."""
        days = self.days_until_refill
        if days is None:
            return 'unknown'
        if days <= 0:
            return 'available'
        if days <= 3:
            return 'available'  # Within 3-day early fill window
        return 'too_early'

    @property
    def pdmp_due(self):
        """True if PDMP check is overdue or due within 7 days."""
        if not self.last_pdmp_check:
            return True
        due_date = self.last_pdmp_check + timedelta(days=self.pdmp_check_interval_days)
        return date.today() >= due_date - timedelta(days=7)

    @property
    def uds_due(self):
        """True if UDS is overdue or due within 14 days."""
        if not self.last_uds_date:
            return True
        due_date = self.last_uds_date + timedelta(days=self.uds_interval_days)
        return date.today() >= due_date - timedelta(days=14)

    def record_fill(self, fill_date=None):
        """Record a new fill and compute next refill date."""
        self.last_fill_date = fill_date or date.today()
        self.next_fill_date = self.last_fill_date + timedelta(days=self.days_supply)
        self.updated_at = datetime.now(timezone.utc)


class CodeFavorite(db.Model):
    """F17: Provider's saved ICD-10 code favorites for quick access."""
    __tablename__ = 'code_favorite'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    icd10_code = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(300), default='')
    use_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'icd10_code', name='uq_user_code_fav'),
    )


class CodePairing(db.Model):
    """F17c: Tracks ICD-10 code pairs used together for pairing suggestions."""
    __tablename__ = 'code_pairing'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    code_a = db.Column(db.String(20), nullable=False)
    code_b = db.Column(db.String(20), nullable=False)
    pair_count = db.Column(db.Integer, default=1)
    last_used = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'code_a', 'code_b', name='uq_user_code_pair'),
    )


class PriorAuthorization(db.Model):
    """F26: Prior authorization request history and narrative tracking."""
    __tablename__ = 'prior_authorization'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    mrn = db.Column(db.String(20), default='')
    patient_name = db.Column(db.String(200), default='')

    # Drug info
    drug_name = db.Column(db.String(200), nullable=False)
    rxnorm_cui = db.Column(db.String(20), default='')
    ndc_code = db.Column(db.String(20), default='')

    # Clinical info
    diagnosis = db.Column(db.String(300), default='')
    icd10_code = db.Column(db.String(20), default='')
    payer_name = db.Column(db.String(200), default='')

    # PA content
    failed_alternatives = db.Column(db.Text, default='')  # JSON list of failed drugs
    clinical_justification = db.Column(db.Text, default='')
    generated_narrative = db.Column(db.Text, default='')

    # Tracking
    status = db.Column(db.String(20), default='draft')  # draft, submitted, approved, denied, appealed
    submitted_date = db.Column(db.Date, nullable=True)
    decision_date = db.Column(db.Date, nullable=True)
    denial_reason = db.Column(db.Text, default='')
    appeal_narrative = db.Column(db.Text, default='')

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<PA {self.drug_name} status={self.status}>'

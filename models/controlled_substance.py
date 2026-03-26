from datetime import date, datetime, timedelta, timezone

from models import db


class ControlledSubstanceEntry(db.Model):
    """F25: One row per patient on a controlled substance."""
    __tablename__ = 'controlled_substance_entry'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    mrn = db.Column(db.String(20), nullable=False, index=True)
    patient_name = db.Column(db.String(200), default='')

    drug_name = db.Column(db.String(200), nullable=False)
    rxnorm_cui = db.Column(db.String(20), default='')
    dea_schedule = db.Column(db.String(10), default='')
    dose = db.Column(db.String(100), default='')
    quantity = db.Column(db.Integer, default=0)
    days_supply = db.Column(db.Integer, default=30)

    last_fill_date = db.Column(db.Date, nullable=True)
    next_fill_date = db.Column(db.Date, nullable=True)

    pdmp_check_interval_days = db.Column(db.Integer, default=90)
    last_pdmp_check = db.Column(db.Date, nullable=True)
    uds_interval_days = db.Column(db.Integer, default=180)
    last_uds_date = db.Column(db.Date, nullable=True)

    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, default='')

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f'<CSEntry {self.drug_name} MRN={self.mrn or "?"}>'

    @property
    def days_until_refill(self):
        if not self.next_fill_date:
            return None
        return (self.next_fill_date - date.today()).days

    @property
    def refill_status(self):
        days = self.days_until_refill
        if days is None:
            return 'unknown'
        if days <= 0:
            return 'available'
        if days <= 3:
            return 'available'
        return 'too_early'

    @property
    def pdmp_due(self):
        if not self.last_pdmp_check:
            return True
        due_date = self.last_pdmp_check + timedelta(days=self.pdmp_check_interval_days)
        return date.today() >= due_date - timedelta(days=7)

    @property
    def uds_due(self):
        if not self.last_uds_date:
            return True
        due_date = self.last_uds_date + timedelta(days=self.uds_interval_days)
        return date.today() >= due_date - timedelta(days=14)

    def record_fill(self, fill_date=None):
        self.last_fill_date = fill_date or date.today()
        self.next_fill_date = self.last_fill_date + timedelta(days=self.days_supply)
        self.updated_at = datetime.now(timezone.utc)

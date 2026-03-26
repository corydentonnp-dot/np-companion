from datetime import date, datetime, timezone

from models import db


class ReferralLetter(db.Model):
    """F27: Referral letter tracking with generated letter text."""
    __tablename__ = 'referral_letter'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    mrn = db.Column(db.String(20), default='')
    patient_display = db.Column(db.String(200), default='')

    specialty = db.Column(db.String(100), nullable=False)
    reason = db.Column(db.Text, default='')
    relevant_history = db.Column(db.Text, default='')
    key_findings = db.Column(db.Text, default='')
    current_medications = db.Column(db.Text, default='')
    urgency = db.Column(db.String(20), default='routine')

    generated_letter = db.Column(db.Text, default='')
    specialty_fields = db.Column(db.Text, nullable=True)

    referral_date = db.Column(db.Date, nullable=True)
    consultation_received = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, default='')

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Referral {self.specialty} {self.patient_display}>'

    @property
    def is_overdue(self):
        if self.consultation_received:
            return False
        if not self.referral_date:
            return False
        return (date.today() - self.referral_date).days > 42

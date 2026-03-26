from datetime import datetime, timezone

from models import db


class PriorAuthorization(db.Model):
    """F26: Prior authorization request history and narrative tracking."""
    __tablename__ = 'prior_authorization'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    mrn = db.Column(db.String(20), default='')
    patient_name = db.Column(db.String(200), default='')

    drug_name = db.Column(db.String(200), nullable=False)
    rxnorm_cui = db.Column(db.String(20), default='')
    ndc_code = db.Column(db.String(20), default='')

    diagnosis = db.Column(db.String(300), default='')
    icd10_code = db.Column(db.String(20), default='')
    payer_name = db.Column(db.String(200), default='')

    failed_alternatives = db.Column(db.Text, default='')
    clinical_justification = db.Column(db.Text, default='')
    generated_narrative = db.Column(db.Text, default='')

    status = db.Column(db.String(20), default='draft')
    submitted_date = db.Column(db.Date, nullable=True)
    decision_date = db.Column(db.Date, nullable=True)
    denial_reason = db.Column(db.Text, default='')
    appeal_narrative = db.Column(db.Text, default='')

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    is_shared = db.Column(db.Boolean, default=False)
    shared_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    forked_from_id = db.Column(db.Integer, nullable=True)
    approval_rate = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f'<PA {self.drug_name} status={self.status}>'

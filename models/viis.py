"""
CareCompanion -- VIIS (Virginia Immunization Information System) Models
File: models/viis.py

Phase VIIS-1 -- Data layer for automated VIIS batch lookups.
Tracks per-patient check history and batch run state for
pre-visit immunization verification.
"""

from datetime import datetime, timezone
from models import db


class VIISCheck(db.Model):
    """Per-patient VIIS lookup result record.

    Created each time a patient is looked up in VIIS (batch or manual).
    Stores status, immunization count, and raw response for audit.
    """
    __tablename__ = 'viis_check'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    mrn = db.Column(db.String(20), nullable=False, index=True)
    status = db.Column(
        db.String(20), nullable=False, default='found',
        doc='found | not_found | error'
    )
    immunization_count = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    checked_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    # Full scraper JSON response for audit trail
    raw_response = db.Column(db.Text, nullable=True)
    # Nullable FK -- null for manual (non-batch) checks
    batch_run_id = db.Column(
        db.Integer, db.ForeignKey('viis_batch_run.id'), nullable=True, index=True
    )

    # Relationships
    user = db.relationship('User', backref='viis_checks', lazy=True)
    batch_run = db.relationship('VIISBatchRun', backref='checks', lazy=True)

    def __repr__(self):
        return f'<VIISCheck {self.id} mrn_hash={self.mrn[:4]}** {self.status}>'


class VIISBatchRun(db.Model):
    """Tracks a batch VIIS lookup execution for resume and reporting.

    Created when the nightly pre-visit batch starts. Updated as each
    patient is processed. If the batch crashes, status stays 'running'
    and the next invocation can resume from last_mrn_processed.
    """
    __tablename__ = 'viis_batch_run'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    started_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    completed_at = db.Column(db.DateTime, nullable=True)

    # Counters
    total_eligible = db.Column(db.Integer, default=0)
    total_checked = db.Column(db.Integer, default=0)
    total_found = db.Column(db.Integer, default=0)
    total_not_found = db.Column(db.Integer, default=0)
    total_errors = db.Column(db.Integer, default=0)
    gaps_closed = db.Column(db.Integer, default=0)

    # Resume support -- last MRN successfully processed
    last_mrn_processed = db.Column(db.String(20), nullable=True)

    # Batch status
    status = db.Column(
        db.String(20), nullable=False, default='running',
        doc='running | completed | failed | partial'
    )

    # Relationships
    user = db.relationship('User', backref='viis_batch_runs', lazy=True)

    def __repr__(self):
        return (
            f'<VIISBatchRun {self.id} {self.status} '
            f'{self.total_checked}/{self.total_eligible}>'
        )

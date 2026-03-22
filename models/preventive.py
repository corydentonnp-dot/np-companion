"""
CareCompanion — Preventive Service Models
File: models/preventive.py

Phase 23 data layer: tracks delivered preventive services per patient —
"what was done and when" — for panel-wide compliance dashboards and
care-gap detection.

Models
------
- PreventiveServiceRecord: one row per preventive service delivered
  per patient (e.g., mammography, AWV, lipid panel, HCV screening).
  Linked to VSAC eCQM measure OIDs for dynamic eligibility.

HIPAA note: Uses patient_mrn_hash (SHA-256) — never stores plain MRN.
"""

from datetime import datetime, timezone
from models import db


class PreventiveServiceRecord(db.Model):
    """
    One row per preventive service delivered to a patient.

    Used for panel-wide compliance dashboards (/care-gaps/preventive)
    and per-patient service history.  VSAC measure OIDs link each
    record to the CMS eCQM that defines the service.
    """
    __tablename__ = 'preventive_service_record'

    id = db.Column(db.Integer, primary_key=True)

    patient_mrn_hash = db.Column(db.String(64), nullable=False, index=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )

    # Service identification
    service_code = db.Column(db.String(20), nullable=False)      # VSAC-derived or CPT
    service_name = db.Column(db.String(200), nullable=False)     # "Lipid Panel", "Mammography"
    cpt_hcpcs_code = db.Column(db.String(20), default='')

    # Dates
    service_date = db.Column(db.Date, nullable=False)
    next_due_date = db.Column(db.Date, nullable=True)            # service_date + interval

    # Result
    result_summary = db.Column(db.String(500), nullable=True)    # "LDL 142, HDL 45"
    performed_by = db.Column(db.String(200), nullable=True)

    # Billing
    billing_status = db.Column(
        db.String(20), default='not_billed'
    )  # not_billed | billed | paid | denied
    payer_at_time = db.Column(db.String(100), default='')

    # VSAC linkage
    vsac_measure_oid = db.Column(db.String(100), nullable=True)

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = db.relationship('User', backref='preventive_services', lazy=True)

    def __repr__(self):
        return (
            f'<PreventiveServiceRecord {self.id} '
            f'{self.service_name} {self.service_date}>'
        )

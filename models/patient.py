"""
CareCompanion — Patient Models

File location: carecompanion/models/patient.py

Two tables for storing parsed clinical summary data:
  - PatientVitals: individual vital signs extracted from CDA XML
  - PatientRecord: per-patient metadata (last XML parse timestamp)

HIPAA note: Full MRN is stored for clinical accuracy.
Full MRN is displayed in the UI for provider workflow needs.
"""

from datetime import datetime, timezone
from models import db


class PatientVitals(db.Model):
    """One row per vital sign measurement extracted from a Clinical Summary."""
    __tablename__ = 'patient_vitals'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    mrn = db.Column(db.String(20), nullable=False, index=True)

    vital_name = db.Column(db.String(100), nullable=False)   # e.g. "Blood Pressure"
    vital_value = db.Column(db.String(100), nullable=False)   # e.g. "120/80"
    vital_unit = db.Column(db.String(50), default='')          # e.g. "mmHg"
    measured_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship('User', backref='patient_vitals', lazy=True)

    def __repr__(self):
        return f'<PatientVitals {self.id} {self.vital_name}={self.vital_value}>'


class PatientRecord(db.Model):
    """
    One row per patient per provider — tracks the last time a
    Clinical Summary was parsed for this patient.
    """
    __tablename__ = 'patient_records'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    mrn = db.Column(db.String(20), nullable=False, index=True)

    patient_name = db.Column(db.String(200), default='')
    patient_dob = db.Column(db.String(20), default='')
    patient_sex = db.Column(db.String(10), default='')
    insurer_type = db.Column(db.String(30), default='unknown')

    last_awv_date = db.Column(db.Date, nullable=True)
    last_discharge_date = db.Column(db.Date, nullable=True)

    last_xml_parsed = db.Column(db.DateTime, nullable=True)

    # Provider who "claimed" this patient for their panel
    claimed_by = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=True
    )
    claimed_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship('User', backref='patient_records', lazy=True,
                           foreign_keys=[user_id])
    provider = db.relationship('User', foreign_keys=[claimed_by], lazy=True)

    def __repr__(self):
        return f'<PatientRecord {self.id} mrn={self.mrn or ""}>'


class PatientMedication(db.Model):
    """Active/inactive medication from parsed Clinical Summary XML."""
    __tablename__ = 'patient_medications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    mrn = db.Column(db.String(20), nullable=False, index=True)
    drug_name = db.Column(db.String(200), nullable=False)
    rxnorm_cui = db.Column(db.String(20), default='')
    dosage = db.Column(db.String(150), default='')
    frequency = db.Column(db.String(100), default='')
    status = db.Column(db.String(20), default='active')  # active / inactive
    start_date = db.Column(db.DateTime, nullable=True)
    user_modified = db.Column(db.Boolean, default=False)  # True when user edited locally
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<PatientMedication {self.id} {self.drug_name}>'


class PatientDiagnosis(db.Model):
    """Active problem list from parsed Clinical Summary XML."""
    __tablename__ = 'patient_diagnoses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    mrn = db.Column(db.String(20), nullable=False, index=True)
    diagnosis_name = db.Column(db.String(300), nullable=False)
    icd10_code = db.Column(db.String(20), default='')
    status = db.Column(db.String(20), default='active')  # active / resolved
    diagnosis_category = db.Column(db.String(20), default='chronic')  # acute / chronic
    onset_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<PatientDiagnosis {self.id} {self.diagnosis_name}>'


class PatientAllergy(db.Model):
    """Allergy record from parsed Clinical Summary XML."""
    __tablename__ = 'patient_allergies'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    mrn = db.Column(db.String(20), nullable=False, index=True)
    allergen = db.Column(db.String(200), nullable=False)
    reaction = db.Column(db.String(200), default='')
    severity = db.Column(db.String(50), default='')
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<PatientAllergy {self.id} {self.allergen}>'


class PatientImmunization(db.Model):
    """Immunization record from parsed Clinical Summary XML or VIIS lookup."""
    __tablename__ = 'patient_immunizations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    mrn = db.Column(db.String(20), nullable=False, index=True)
    vaccine_name = db.Column(db.String(200), nullable=False)
    date_given = db.Column(db.DateTime, nullable=True)
    # Source: 'ac' (Amazing Charts XML) or 'viis' (VIIS scraper)
    source = db.Column(db.String(10), nullable=False, default='ac')
    # Links VIIS-sourced records to their lookup (nullable for AC records)
    viis_check_id = db.Column(
        db.Integer, db.ForeignKey('viis_check.id'), nullable=True, index=True
    )
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Unique constraint: prevent duplicate immunization records
    __table_args__ = (
        db.UniqueConstraint(
            'mrn', 'vaccine_name', 'date_given', 'source',
            name='uq_patient_imm_mrn_vaccine_date_source'
        ),
    )

    def __repr__(self):
        return f'<PatientImmunization {self.id} {self.vaccine_name} ({self.source})>'


class PatientSpecialist(db.Model):
    """Specialist/referral record for a patient."""
    __tablename__ = 'patient_specialists'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    mrn = db.Column(db.String(20), nullable=False, index=True)
    specialty = db.Column(db.String(150), nullable=False)
    provider_name = db.Column(db.String(200), default='')
    phone = db.Column(db.String(30), default='')
    fax = db.Column(db.String(30), default='')
    notes = db.Column(db.Text, default='')
    last_visit = db.Column(db.DateTime, nullable=True)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<PatientSpecialist {self.id} {self.specialty}>'


class PatientNoteDraft(db.Model):
    """Saved prepped-note content for a patient (one draft per patient per user)."""
    __tablename__ = 'patient_note_drafts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    mrn = db.Column(db.String(20), nullable=False, index=True)
    section_data = db.Column(db.Text, default='{}')  # JSON {section_name: content}
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<PatientNoteDraft {self.id} mrn={self.mrn or ""}>'

class PatientLabResult(db.Model):
    """Lab result from parsed Clinical Summary XML."""
    __tablename__ = 'patient_lab_results'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    mrn = db.Column(db.String(20), nullable=False, index=True)
    patient_mrn_hash = db.Column(db.String(64), nullable=True, index=True)
    test_name = db.Column(db.String(200), nullable=False)
    loinc_code = db.Column(db.String(20), default='')
    result_value = db.Column(db.String(100), default='')
    result_units = db.Column(db.String(50), default='')
    result_date = db.Column(db.DateTime, nullable=True)
    result_flag = db.Column(db.String(20), default='normal')  # normal|abnormal|critical
    source = db.Column(db.String(20), default='xml_import')  # xml_import|manual
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<PatientLabResult {self.id} {self.test_name}>'


class PatientSocialHistory(db.Model):
    """Social history from parsed Clinical Summary XML."""
    __tablename__ = 'patient_social_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    mrn = db.Column(db.String(20), nullable=False, index=True)
    patient_mrn_hash = db.Column(db.String(64), nullable=True, index=True)
    tobacco_status = db.Column(db.String(20), default='unknown')  # current|former|never|unknown
    tobacco_pack_years = db.Column(db.Float, nullable=True)
    alcohol_status = db.Column(db.String(20), default='unknown')  # current|former|never|unknown
    alcohol_frequency = db.Column(db.String(100), default='')
    substance_use_status = db.Column(db.String(100), default='')
    sexual_activity = db.Column(db.String(100), default='')
    last_updated = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<PatientSocialHistory {self.id} tobacco={self.tobacco_status}>'


class PatientEncounterNote(db.Model):
    """Prior encounter notes extracted from Clinical Summary XML."""
    __tablename__ = 'patient_encounter_notes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    mrn = db.Column(db.String(20), nullable=False, index=True)
    encounter_date = db.Column(db.DateTime, nullable=True)
    provider_name = db.Column(db.String(200), default='')
    note_type = db.Column(db.String(50), default='Progress Note')
    note_text = db.Column(db.Text, default='')
    location = db.Column(db.String(200), default='')
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<PatientEncounterNote {self.id} {self.note_type}>'
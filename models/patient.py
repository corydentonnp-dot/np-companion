"""
NP Companion — Patient Models

File location: np-companion/models/patient.py

Two tables for storing parsed clinical summary data:
  - PatientVitals: individual vital signs extracted from CDA XML
  - PatientRecord: per-patient metadata (last XML parse timestamp)

HIPAA note: Full MRN is stored for clinical accuracy.
Display in the UI should show only the last 4 digits.
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
        return f'<PatientRecord {self.id} mrn=...{self.mrn[-4:] if self.mrn else ""}>'


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
    """Immunization record from parsed Clinical Summary XML."""
    __tablename__ = 'patient_immunizations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    mrn = db.Column(db.String(20), nullable=False, index=True)
    vaccine_name = db.Column(db.String(200), nullable=False)
    date_given = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<PatientImmunization {self.id} {self.vaccine_name}>'


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
        return f'<PatientNoteDraft {self.id} mrn=...{self.mrn[-4:] if self.mrn else ""}>'


class Icd10Cache(db.Model):
    """
    Global ICD-10 lookup cache — stores diagnosis name → ICD-10 code
    mappings verified via the NIH Clinical Tables API.  Shared across
    all users and patients to avoid redundant API calls.
    """
    __tablename__ = 'icd10_cache'

    id = db.Column(db.Integer, primary_key=True)
    diagnosis_name_lower = db.Column(db.String(300), nullable=False, unique=True, index=True)
    icd10_code = db.Column(db.String(20), nullable=False)
    icd10_description = db.Column(db.String(300), default='')
    source = db.Column(db.String(20), default='nih_api')  # 'nih_api'
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<Icd10Cache {self.diagnosis_name_lower} → {self.icd10_code}>'


class RxNormCache(db.Model):
    """
    Global RxNorm lookup cache — stores RXCUI → structured drug info
    from the NIH RxNorm API.  Shared across all users to avoid
    redundant API calls.  Mirrors the Icd10Cache pattern.
    """
    __tablename__ = 'rxnorm_cache'

    id = db.Column(db.Integer, primary_key=True)
    rxcui = db.Column(db.String(20), nullable=False, unique=True, index=True)
    brand_name = db.Column(db.String(300), default='')
    generic_name = db.Column(db.String(300), default='')
    dose_strength = db.Column(db.String(100), default='')   # e.g. "20 mg"
    dose_form = db.Column(db.String(100), default='')        # e.g. "tablet"
    route = db.Column(db.String(100), default='')             # e.g. "oral"
    tty = db.Column(db.String(20), default='')                # term type: SCD, BN, IN
    source = db.Column(db.String(20), default='rxnorm_api')
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<RxNormCache {self.rxcui} → {self.generic_name or self.brand_name}>'

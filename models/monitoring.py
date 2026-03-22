"""
CareCompanion — Monitoring Models
File: models/monitoring.py

Phase 23 data layer: dynamic API-driven monitoring rules, per-patient
monitoring schedules, and REMS compliance tracking.

Models
------
- MonitoringRule: replaces static MEDICATION_MONITORING_MAP with dynamic,
  API-sourced monitoring rules (DailyMed SPL, Drug@FDA PMR, RxClass,
  VSAC, UpToDate, REMS, manual seed).
- MonitoringSchedule: per-patient monitoring due dates derived from
  MonitoringRule entries cross-referenced against PatientLabResult.
- REMSTrackerEntry: per-patient REMS compliance tracking for drugs
  with mandatory monitoring programs (clozapine, iPLEDGE, opioid REMS,
  THALOMID REMS).

HIPAA note: Uses patient_mrn_hash (SHA-256) — never stores plain MRN.
"""

from datetime import datetime, timezone
from models import db


# ── MonitoringRule ──────────────────────────────────────────────────
class MonitoringRule(db.Model):
    """
    A single monitoring requirement: what lab is needed, for which
    medication/condition/genotype/REMS trigger, and how often.

    Populated dynamically via the MonitoringRuleEngine waterfall:
    DB cache → DailyMed SPL → Drug@FDA PMR → RxClass → UpToDate → seed.
    """
    __tablename__ = 'monitoring_rule'

    id = db.Column(db.Integer, primary_key=True)

    # Trigger identifiers (exactly one should be non-null per row)
    rxcui = db.Column(db.String(20), nullable=True, index=True)
    rxclass_id = db.Column(db.String(50), nullable=True, index=True)
    icd10_trigger = db.Column(db.String(10), nullable=True, index=True)

    # What kind of rule this is
    trigger_type = db.Column(
        db.String(20), nullable=False, default='MEDICATION'
    )  # MEDICATION | CONDITION | GENOTYPE | REMS

    # Where the rule came from
    source = db.Column(
        db.String(20), nullable=False, default='MANUAL'
    )  # DAILYMED | VSAC | REMS | RXCLASS | MANUAL | LLM_EXTRACTED | DRUG_AT_FDA | UPTODATE

    # Lab identification
    lab_loinc_code = db.Column(db.String(20), nullable=False)
    lab_cpt_code = db.Column(db.String(20), nullable=False)
    lab_name = db.Column(db.String(200), nullable=False)

    # Monitoring schedule
    interval_days = db.Column(db.Integer, nullable=False, default=180)

    # Clinical priority
    priority = db.Column(
        db.String(20), nullable=False, default='standard'
    )  # critical | high | standard | low

    # Provenance and confidence
    evidence_source_url = db.Column(db.String(500), default='')
    extraction_confidence = db.Column(db.Float, default=1.0)
    clinical_context = db.Column(db.Text, default='')

    is_active = db.Column(db.Boolean, default=True, index=True)
    last_refreshed = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.UniqueConstraint(
            'rxcui', 'rxclass_id', 'icd10_trigger',
            'lab_loinc_code', 'trigger_type',
            name='uq_monitoring_rule_trigger_lab'
        ),
    )

    def __repr__(self):
        trigger = self.rxcui or self.rxclass_id or self.icd10_trigger or '?'
        return f'<MonitoringRule {self.id} {trigger} → {self.lab_name}>'


# ── MonitoringSchedule ─────────────────────────────────────────────
class MonitoringSchedule(db.Model):
    """
    Per-patient monitoring due date: what lab needs to happen next,
    when it's due, and what triggered it.

    Created by MonitoringRuleEngine.populate_patient_schedule() from
    MonitoringRule entries cross-referenced with PatientLabResult.
    """
    __tablename__ = 'monitoring_schedule'

    id = db.Column(db.Integer, primary_key=True)

    patient_mrn_hash = db.Column(db.String(64), nullable=False, index=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    monitoring_rule_id = db.Column(
        db.Integer, db.ForeignKey('monitoring_rule.id'), nullable=True, index=True
    )

    # Lab identification (denormalized from MonitoringRule for query speed)
    lab_code = db.Column(db.String(20), nullable=False)          # CPT code
    lab_name = db.Column(db.String(200), nullable=False)
    monitoring_rule_code = db.Column(db.String(50), default='')  # e.g. "MON_A1C"

    # Clinical context
    clinical_indication = db.Column(db.String(300), default='')
    triggering_medication = db.Column(db.String(200), nullable=True)
    triggering_condition = db.Column(db.String(200), nullable=True)

    # Schedule
    last_performed_date = db.Column(db.Date, nullable=True)
    next_due_date = db.Column(db.Date, nullable=False, index=True)
    interval_days = db.Column(db.Integer, nullable=False, default=180)

    # Priority and status
    priority = db.Column(db.String(20), default='standard')  # critical|high|standard|low
    status = db.Column(
        db.String(20), default='active', index=True
    )  # active | completed | deferred | cancelled

    # Most recent result
    last_result_value = db.Column(db.String(100), nullable=True)
    last_result_flag = db.Column(db.String(20), default='')  # normal|abnormal|critical

    # Traceability
    source = db.Column(db.String(20), default='')  # DAILYMED|VSAC|MANUAL|etc.
    can_bundle_with = db.Column(db.String(500), nullable=True)  # comma-separated IDs

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = db.relationship('User', backref='monitoring_schedules', lazy=True)
    monitoring_rule = db.relationship('MonitoringRule', backref='schedules', lazy=True)

    __table_args__ = (
        db.Index(
            'ix_monitoring_schedule_patient_status_due',
            'patient_mrn_hash', 'status', 'next_due_date'
        ),
    )

    def __repr__(self):
        return f'<MonitoringSchedule {self.id} {self.lab_name} due={self.next_due_date}>'


# ── REMSTrackerEntry ──────────────────────────────────────────────
class REMSTrackerEntry(db.Model):
    """
    REMS compliance tracking per patient per REMS drug.

    Tracks federally mandated Risk Evaluation and Mitigation Strategy
    requirements: clozapine ANC, iPLEDGE pregnancy tests, opioid REMS
    counseling, THALOMID REMS registry.  Escalation levels drive
    critical-priority alerts in morning briefing and patient chart.
    """
    __tablename__ = 'rems_tracker_entry'

    id = db.Column(db.Integer, primary_key=True)

    patient_mrn_hash = db.Column(db.String(64), nullable=False, index=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )

    # Drug identification
    drug_name = db.Column(db.String(200), nullable=False)
    rxcui = db.Column(db.String(20), default='')

    # REMS program details
    rems_program_name = db.Column(db.String(200), nullable=False)
    requirement_type = db.Column(
        db.String(30), nullable=False
    )  # ANC_CHECK | PREGNANCY_TEST | REGISTRY_ENROLLMENT | LAB_MONITORING | PATIENT_COUNSELING | NALOXONE_COPRESCRIBE
    requirement_description = db.Column(db.Text, default='')

    # Scheduling
    interval_days = db.Column(db.Integer, nullable=False, default=30)
    current_phase = db.Column(db.String(20), default='')  # weekly|biweekly|monthly
    phase_start_date = db.Column(db.Date, nullable=True)
    last_completed_date = db.Column(db.Date, nullable=True)
    next_due_date = db.Column(db.Date, nullable=False, index=True)

    # Compliance
    is_compliant = db.Column(db.Boolean, default=True)
    escalation_level = db.Column(
        db.Integer, default=0
    )  # 0=on track, 1=due within 3 days, 2=overdue, 3=critical hold >7 days

    notes = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.String(20), default='active', index=True
    )  # active | completed | discontinued | hold

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = db.relationship('User', backref='rems_entries', lazy=True)

    def __repr__(self):
        return (
            f'<REMSTrackerEntry {self.id} {self.drug_name} '
            f'{self.rems_program_name} esc={self.escalation_level}>'
        )

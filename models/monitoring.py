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


# ── MedicationCatalogEntry ─────────────────────────────────────────
class MedicationCatalogEntry(db.Model):
    """
    Denormalized medication catalog index — one row per normalized
    medication.  Links to MonitoringRule rows via rxcui.  Provides the
    browsable master list for the admin Medication Control Panel.

    Populated via seeding (common PCP meds), local patient data scan,
    or auto-discovery during XML import.
    """
    __tablename__ = 'medication_catalog_entry'

    id = db.Column(db.Integer, primary_key=True)

    # Medication identity
    display_name = db.Column(db.String(250), nullable=False, index=True)
    normalized_name = db.Column(db.String(250), nullable=False, index=True)
    rxcui = db.Column(db.String(20), nullable=True, index=True)
    ingredient_name = db.Column(db.String(250), default='')
    ingredient_rxcui = db.Column(db.String(20), default='')
    drug_class = db.Column(db.String(200), default='')

    # Origin and confidence
    source_origin = db.Column(
        db.String(30), nullable=False, default='manual'
    )  # local_patient | seeded | api_discovered | manual
    source_confidence = db.Column(db.Float, default=1.0)

    # Status workflow
    status = db.Column(
        db.String(20), nullable=False, default='active', index=True
    )  # active | pending_review | unmapped | inactive | suppressed

    # Usage stats
    local_patient_count = db.Column(db.Integer, default=0)

    # Timestamps
    first_seen_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    last_seen_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    last_refreshed_at = db.Column(db.DateTime, nullable=True)
    last_tested_at = db.Column(db.DateTime, nullable=True)

    notes = db.Column(db.Text, default='')
    is_active = db.Column(db.Boolean, default=True, index=True)

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<MedicationCatalogEntry {self.id} {self.display_name}>'


# ── MonitoringRuleOverride ─────────────────────────────────────────
class MonitoringRuleOverride(db.Model):
    """
    User-level or practice-level override for a MonitoringRule.

    Precedence chain for effective interval:
      user_override → practice_override → MonitoringRule.interval_days
      → class-level rule → null (no rule)

    API refreshes NEVER overwrite overrides — they are preserved and
    the diff is logged in MonitoringRuleDiff.
    """
    __tablename__ = 'monitoring_rule_override'

    id = db.Column(db.Integer, primary_key=True)

    monitoring_rule_id = db.Column(
        db.Integer, db.ForeignKey('monitoring_rule.id'),
        nullable=False, index=True
    )

    # Scope: 'user' → scope_id is user_id; 'practice' → scope_id is NULL
    scope = db.Column(
        db.String(20), nullable=False, default='user'
    )  # user | practice
    scope_id = db.Column(db.Integer, nullable=True, index=True)

    # Override values (null = inherit from rule default)
    override_interval_days = db.Column(db.Integer, nullable=True)
    override_priority = db.Column(db.String(20), nullable=True)
    override_active = db.Column(db.Boolean, default=True)
    override_reminder_text = db.Column(db.String(500), nullable=True)

    reason = db.Column(db.Text, default='')
    created_by = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False
    )

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    monitoring_rule = db.relationship(
        'MonitoringRule', backref='overrides', lazy=True
    )
    creator = db.relationship(
        'User', backref='monitoring_overrides', lazy=True
    )

    __table_args__ = (
        db.UniqueConstraint(
            'monitoring_rule_id', 'scope', 'scope_id',
            name='uq_monitoring_override_rule_scope'
        ),
    )

    def __repr__(self):
        return (
            f'<MonitoringRuleOverride {self.id} rule={self.monitoring_rule_id} '
            f'scope={self.scope} interval={self.override_interval_days}>'
        )


# ── MonitoringEvaluationLog ───────────────────────────────────────
class MonitoringEvaluationLog(db.Model):
    """
    Audit trail of monitoring rule evaluations.  Records whether a
    rule fired (produced a reminder) or was suppressed, and why.

    Used for explainability ("Why is this lab due?"), QA coverage
    analysis, and synthetic-vs-real data separation.

    HIPAA: Uses patient_mrn_hash — never stores plain MRN.
    """
    __tablename__ = 'monitoring_evaluation_log'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    patient_mrn_hash = db.Column(db.String(64), nullable=False, index=True)
    is_synthetic = db.Column(db.Boolean, default=False, index=True)

    # What was evaluated
    medication_key = db.Column(db.String(250), nullable=False)

    # Result
    fired = db.Column(db.Boolean, nullable=False, default=False)
    suppression_reason = db.Column(db.String(300), nullable=True)

    # Rule traceability (JSON list of MonitoringRule.id values)
    matched_rule_ids = db.Column(db.Text, default='[]')

    # Full explanation payload (JSON)
    explanation_json = db.Column(db.Text, default='{}')

    # Computed schedule result
    next_due_date = db.Column(db.Date, nullable=True)
    days_overdue = db.Column(db.Integer, nullable=True)

    evaluation_timestamp = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = db.relationship('User', backref='monitoring_eval_logs', lazy=True)

    __table_args__ = (
        db.Index(
            'ix_eval_log_patient_timestamp',
            'patient_mrn_hash', 'evaluation_timestamp'
        ),
    )

    def __repr__(self):
        status = 'FIRED' if self.fired else 'SUPPRESSED'
        return (
            f'<MonitoringEvaluationLog {self.id} {self.medication_key} '
            f'{status}>'
        )


# ── MonitoringRuleTestResult ─────────────────────────────────────
class MonitoringRuleTestResult(db.Model):
    """
    Result of running a test scenario against a monitoring rule.

    Stores pass/fail and explanation for each scenario type (overdue,
    up-to-date, discontinued, etc.).  Used by the bulk test runner
    and golden case regression harness.
    """
    __tablename__ = 'monitoring_rule_test_result'

    id = db.Column(db.Integer, primary_key=True)

    monitoring_rule_id = db.Column(
        db.Integer, db.ForeignKey('monitoring_rule.id'),
        nullable=True, index=True
    )
    catalog_entry_id = db.Column(
        db.Integer, db.ForeignKey('medication_catalog_entry.id'),
        nullable=True, index=True
    )

    test_scenario = db.Column(
        db.String(50), nullable=False
    )  # no_prior_lab | overdue | up_to_date | discontinued | class_inherited |
       # ingredient_inherited | direct_override | combo_product

    passed = db.Column(db.Boolean, nullable=False)
    explanation = db.Column(db.Text, default='')

    tested_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    tested_by = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=True
    )

    # Relationships
    monitoring_rule = db.relationship(
        'MonitoringRule', backref='test_results', lazy=True
    )
    catalog_entry = db.relationship(
        'MedicationCatalogEntry', backref='test_results', lazy=True
    )

    def __repr__(self):
        result = 'PASS' if self.passed else 'FAIL'
        return (
            f'<MonitoringRuleTestResult {self.id} rule={self.monitoring_rule_id} '
            f'{self.test_scenario} {result}>'
        )


# ── MonitoringRuleDiff ────────────────────────────────────────────
class MonitoringRuleDiff(db.Model):
    """
    Parser drift detection: records before/after snapshots when an
    API refresh (DailyMed, Drug@FDA, etc.) changes a rule's default
    values.

    Manual overrides are NEVER silently overwritten — the attempted
    change is logged here and the override remains active.
    """
    __tablename__ = 'monitoring_rule_diff'

    id = db.Column(db.Integer, primary_key=True)

    rxcui = db.Column(db.String(20), nullable=False, index=True)
    drug_name = db.Column(db.String(250), default='')

    # What changed
    diff_type = db.Column(
        db.String(30), nullable=False
    )  # ADDED | REMOVED | INTERVAL_CHANGED | PRIORITY_CHANGED | LAB_CHANGED

    # Snapshots (JSON)
    before_rules_json = db.Column(db.Text, default='{}')
    after_rules_json = db.Column(db.Text, default='{}')

    # Review status
    reviewed = db.Column(db.Boolean, default=False, index=True)
    reviewed_by = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=True
    )

    diff_timestamp = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return (
            f'<MonitoringRuleDiff {self.id} {self.rxcui} '
            f'{self.diff_type} reviewed={self.reviewed}>'
        )

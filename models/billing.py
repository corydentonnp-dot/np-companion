"""
CareCompanion — Billing Intelligence Models
File: models/billing.py

SQLAlchemy ORM models for the billing opportunity engine:
- BillingOpportunity: per-patient, per-visit billing opportunities detected
  by the billing rules engine. Opportunities are surfaced in the Today View
  and post-visit billing review.
- BillingRuleCache: cached CMS Physician Fee Schedule code data, refreshed
  annually each November when CMS publishes the new fee schedule.

Dependencies:
- models/__init__.py (db instance)

CareCompanion features that rely on this module:
- Billing Opportunity Engine (app/services/billing_rules.py)
- Today View billing card display
- Post-visit billing review (Timer/Billing module)
- Monthly Billing Report (F14c)
- Metrics dashboard (F13) — opportunity gap tracking

HIPAA note: BillingOpportunity stores patient_mrn_hash (SHA-256),
never the plain MRN. The plain MRN is only in PatientRecord.
"""

import json
from datetime import datetime, timezone
from models import db


# Documentation burden levels for scoring
DOC_BURDEN = {
    "LOW": 0.1,       # Passive codes (36415, 90471)
    "MEDIUM": 0.3,    # Screening instruments (PHQ-9, GAD-7)
    "HIGH": 0.6,      # Time documentation / care plan
    "VERY_HIGH": 0.9, # Multi-session tracking (CCM)
}

# Time-to-cash tiers for scoring
TIME_TO_CASH = {
    "IMMEDIATE": 0,    # In-office procedures, vaccines
    "STANDARD": 45,    # Standard claims (30-60 days)
    "COMPLEX": 75,     # Complex / prior auth (60-90 days)
}


class BillingOpportunity(db.Model):
    """
    A billing opportunity detected for a specific patient and visit.

    Created by the billing rules engine (app/services/billing_rules.py)
    during the overnight pre-visit prep job. Displayed to the provider
    before the visit (Today View) and after (post-visit review).

    One record per opportunity per patient per visit date.
    A single patient visit may have multiple opportunities (one per rule category).
    """

    __tablename__ = "billing_opportunity"

    id = db.Column(db.Integer, primary_key=True)

    # Patient identifier — SHA-256 hash of MRN, never the plain MRN
    patient_mrn_hash = db.Column(db.String(64), nullable=False, index=True)

    # The provider who will see this opportunity
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # The scheduled visit date this opportunity was detected for
    visit_date = db.Column(db.Date, nullable=False, index=True)

    # Which billing rule category this opportunity belongs to
    # Values: "CCM", "AWV", "TCM", "G2211", "99417", "BHI", "RPM",
    #         plus care-gap types like "colorectal_colonoscopy", "mammogram", etc.
    opportunity_type = db.Column(db.String(30), nullable=False)

    # Comma-separated list of applicable billing codes
    # Example: "G0439,G2211,G0444" for an AWV stack
    applicable_codes = db.Column(db.Text, nullable=False)

    # Estimated total revenue if all codes are documented and billed
    # Uses national average CMS rates — actual varies by payer
    estimated_revenue = db.Column(db.Float, default=0.0)

    # Why this patient qualifies (human-readable explanation for the provider)
    # Example: "Patient has 3 chronic conditions: HTN, DM2, CKD"
    eligibility_basis = db.Column(db.Text, nullable=True)

    # What documentation is required to bill (injected into note checklist)
    documentation_required = db.Column(db.Text, nullable=True)

    # Confidence level based on how complete the supporting data is
    # "HIGH" — all eligibility data is present and confirmed
    # "MEDIUM" — some eligibility data is inferred or partially present
    # "LOW" — flagged based on partial data, provider should verify
    confidence_level = db.Column(db.String(10), default="MEDIUM")

    # Caveat to show for non-Medicare payers
    # Example: "Verify prior authorization with HEALTHKEEPERS"
    insurer_caveat = db.Column(db.Text, nullable=True)

    # Patient's detected insurer type: "medicare", "medicaid", "commercial", "unknown"
    insurer_type = db.Column(db.String(20), default="unknown")

    # Whether the provider has acted on this opportunity
    # "pending" — not yet reviewed
    # "captured" — documented and billed
    # "dismissed" — provider dismissed with a reason
    # "partial" — some codes captured but not all
    status = db.Column(db.String(20), default="pending", index=True)

    # If dismissed, the provider's reason
    dismissal_reason = db.Column(db.Text, nullable=True)

    # --- Phase 19A expansion columns (backwards compatible) ---
    # Detector category grouping (e.g. "procedures", "chronic_monitoring")
    category = db.Column(db.String(50), nullable=True)
    # Unique rule identifier (e.g. "PROC_EKG", "MON_A1C")
    opportunity_code = db.Column(db.String(20), nullable=True)
    # Suggested modifier (-25, -33, -59, etc.)
    modifier = db.Column(db.String(10), nullable=True)
    # Priority separate from confidence: "critical", "high", "medium", "low"
    priority = db.Column(db.String(10), nullable=True)
    # JSON array of checkbox items for the provider
    documentation_checklist = db.Column(db.Text, nullable=True)
    # When provider captured/dismissed
    actioned_at = db.Column(db.DateTime, nullable=True)
    # Provider display name who actioned
    actioned_by = db.Column(db.String(100), nullable=True)

    # --- Phase 18 expansion: Expected Net Value Scoring ---
    expected_net_dollars = db.Column(db.Float, nullable=True)
    bonus_impact_dollars = db.Column(db.Float, nullable=True)
    bonus_impact_days = db.Column(db.Float, nullable=True)
    opportunity_score = db.Column(db.Float, nullable=True)  # 0.0-1.0
    urgency_score = db.Column(db.Float, nullable=True)      # 0.0-1.0
    implementation_priority = db.Column(db.String(20), nullable=True)

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    reviewed_at = db.Column(db.DateTime, nullable=True)

    # Relationship to closed-loop status entries
    closed_loop_statuses = db.relationship(
        'ClosedLoopStatus', backref='opportunity',
        cascade='all, delete-orphan', lazy='dynamic',
    )

    def __repr__(self):
        return (
            f"<BillingOpportunity {self.opportunity_type} "
            f"visit={self.visit_date} status={self.status}>"
        )

    def get_codes_list(self) -> list:
        """Return applicable_codes as a Python list."""
        if not self.applicable_codes:
            return []
        return [c.strip() for c in self.applicable_codes.split(",") if c.strip()]

    def mark_captured(self):
        """Mark this opportunity as captured (provider documented and billed)."""
        self.status = "captured"
        self.reviewed_at = datetime.now(timezone.utc)

    def dismiss(self, reason: str = ""):
        """Dismiss this opportunity with an optional reason."""
        self.status = "dismissed"
        self.dismissal_reason = reason or "Dismissed by provider"
        self.reviewed_at = datetime.now(timezone.utc)

    def get_checklist(self) -> list:
        """Return documentation_checklist as a Python list."""
        if not self.documentation_checklist:
            return []
        try:
            result = json.loads(self.documentation_checklist)
            return result if isinstance(result, list) else []
        except (json.JSONDecodeError, TypeError):
            return []


class BillingRuleCache(db.Model):
    """
    Cached CMS Physician Fee Schedule data for billing codes.

    Populated by the CMS PFS service (app/services/api/cms_pfs.py) and
    refreshed annually each November when CMS publishes the new rule.
    This serves as a local lookup table for billing code information,
    reducing API calls during the billing rules engine run.

    One record per HCPCS/CPT code per fee schedule year.
    """

    __tablename__ = "billing_rule_cache"

    id = db.Column(db.Integer, primary_key=True)

    # The CPT or HCPCS billing code
    hcpcs_code = db.Column(db.String(10), nullable=False, index=True)

    # Fee schedule year this data applies to (e.g., 2025)
    fee_schedule_year = db.Column(db.Integer, nullable=False, index=True)

    # Official CMS code description
    description = db.Column(db.Text, nullable=True)

    # RVU components
    work_rvu = db.Column(db.Float, default=0.0)
    non_facility_pe_rvu = db.Column(db.Float, default=0.0)
    mp_rvu = db.Column(db.Float, default=0.0)
    total_rvu_non_facility = db.Column(db.Float, default=0.0)

    # Payment amounts (national average, non-facility/office setting)
    non_facility_payment = db.Column(db.Float, default=0.0)
    facility_payment = db.Column(db.Float, default=0.0)

    # Whether this code is currently payable under the PFS
    is_payable = db.Column(db.Boolean, default=True)

    # CMS status code (A=active, R=restricted, etc.)
    status_code = db.Column(db.String(5), nullable=True)

    # When this cache entry was last refreshed from the CMS PFS API
    last_refreshed = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        # Unique constraint: one record per code per year
        db.UniqueConstraint("hcpcs_code", "fee_schedule_year", name="uq_code_year"),
    )

    def __repr__(self):
        return (
            f"<BillingRuleCache {self.hcpcs_code} "
            f"year={self.fee_schedule_year} payment=${self.non_facility_payment}>"
        )

    @classmethod
    def get_payment(cls, hcpcs_code: str, year: int) -> float:
        """
        Look up the non-facility payment amount for a code.
        Returns 0.0 if not found in cache.
        """
        record = cls.query.filter_by(
            hcpcs_code=hcpcs_code.upper(),
            fee_schedule_year=year,
        ).first()
        return record.non_facility_payment if record else 0.0


class BillingRule(db.Model):
    """
    DB-backed configurable billing rule definition.

    Rule logic lives in Python detector classes under billing_engine/detectors/.
    This model provides: admin toggles, revenue estimates, documentation
    checklists for UI display, frequency limits, and modifier defaults.
    """

    __tablename__ = "billing_rule"

    id = db.Column(db.Integer, primary_key=True)

    # Detector group name (e.g. "procedures", "chronic_monitoring", "awv")
    category = db.Column(db.String(50), nullable=False, index=True)

    # Unique rule identifier matching detector output (e.g. "PROC_EKG")
    opportunity_code = db.Column(db.String(20), nullable=False, unique=True)

    # Human-readable rule explanation
    description = db.Column(db.Text, nullable=True)

    # JSON array of CPT/HCPCS codes (e.g. '["93000","93005","93010"]')
    cpt_codes = db.Column(db.Text, nullable=True)

    # JSON array of payer types this rule applies to
    # e.g. '["medicare_b","medicare_advantage","medicaid","commercial"]'
    payer_types = db.Column(db.Text, nullable=True)

    # National average estimated revenue
    estimated_revenue = db.Column(db.Float, default=0.0)

    # Default modifier if any (e.g. "-25", "-33")
    modifier = db.Column(db.String(10), nullable=True)

    # JSON doc for display/documentation (not executed; logic is in Python)
    rule_logic = db.Column(db.Text, nullable=True)

    # JSON array of required documentation items for the provider
    documentation_checklist = db.Column(db.Text, nullable=True)

    # Admin toggle — False means the rule will not fire
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # How often the rule can fire: "annual", "monthly", "once",
    # "per_visit", "per_pregnancy"
    frequency_limit = db.Column(db.String(20), nullable=True)

    last_updated = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return f"<BillingRule {self.opportunity_code} active={self.is_active}>"

    def get_cpt_list(self) -> list:
        """Return cpt_codes as a Python list."""
        import json
        if not self.cpt_codes:
            return []
        try:
            return json.loads(self.cpt_codes)
        except (json.JSONDecodeError, TypeError):
            return []

    def get_payer_list(self) -> list:
        """Return payer_types as a Python list."""
        import json
        if not self.payer_types:
            return []
        try:
            return json.loads(self.payer_types)
        except (json.JSONDecodeError, TypeError):
            return []

    def get_checklist(self) -> list:
        """Return documentation_checklist as a Python list."""
        import json
        if not self.documentation_checklist:
            return []
        try:
            return json.loads(self.documentation_checklist)
        except (json.JSONDecodeError, TypeError):
            return []


class DiagnosisRevenueProfile(db.Model):
    """
    Practice-specific ICD-10 revenue data from the calendar year
    dx code revenue CSV. Used by the Expected Net Value scoring engine
    to weight opportunities by real-world collection and adjustment rates.
    """

    __tablename__ = "diagnosis_revenue_profile"

    id = db.Column(db.Integer, primary_key=True)
    icd10_code = db.Column(db.String(10), nullable=False, unique=True, index=True)
    icd10_description = db.Column(db.String(200), nullable=True)
    encounters_annual = db.Column(db.Integer, default=0)
    billed_annual = db.Column(db.Float, default=0.0)
    received_annual = db.Column(db.Float, default=0.0)
    adjusted_annual = db.Column(db.Float, default=0.0)
    adjustment_rate = db.Column(db.Float, default=0.0)   # 0.0-1.0
    revenue_per_encounter = db.Column(db.Float, default=0.0)
    retention_score = db.Column(db.Float, default=0.0)    # 0.0-1.0
    priority_tier = db.Column(db.String(30), nullable=True)
    frequency_score = db.Column(db.Float, default=0.0)
    payment_score = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f"<DiagnosisRevenueProfile {self.icd10_code} adj={self.adjustment_rate:.1%}>"


class StaffRoutingRule(db.Model):
    """
    Maps billing opportunity codes to responsible staff roles.
    Phase 20.4: Multi-role task routing for billing workflow.
    """

    __tablename__ = "staff_routing_rule"

    id = db.Column(db.Integer, primary_key=True)
    opportunity_code = db.Column(db.String(50), nullable=False, index=True)
    responsible_role = db.Column(db.String(30), nullable=False)  # ma | nurse | front_desk | referral_coordinator | biller | provider | office_manager
    routing_reason = db.Column(db.String(200), nullable=True)
    prep_task_description = db.Column(db.Text, nullable=True)
    timing = db.Column(db.String(30), nullable=True)  # pre_visit | during_visit | post_visit | daily | monthly

    def __repr__(self):
        return f"<StaffRoutingRule {self.opportunity_code} → {self.responsible_role}>"


class DocumentationPhrase(db.Model):
    """
    Phase 21.1: Documentation phrase library.
    Pre-written clinical documentation snippets mapped to billing opportunity codes.
    Providers can customize; customized phrases survive seed updates.
    """

    __tablename__ = "documentation_phrase"

    id = db.Column(db.Integer, primary_key=True)
    opportunity_code = db.Column(db.String(50), nullable=False, index=True)
    cpt_code = db.Column(db.String(20), nullable=True)
    phrase_category = db.Column(db.String(50), nullable=False)  # mdm | time | counseling | screening | care_plan | procedure
    phrase_title = db.Column(db.String(200), nullable=False)
    phrase_text = db.Column(db.Text, nullable=False)
    payer_specific = db.Column(db.String(30), nullable=True)  # NULL = all payers; medicare | medicaid | commercial
    clinical_context = db.Column(db.String(200), nullable=True)
    required_elements = db.Column(db.Text, nullable=True)  # JSON list
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_customized = db.Column(db.Boolean, default=False, nullable=False)

    def get_required_elements(self):
        if not self.required_elements:
            return []
        try:
            result = json.loads(self.required_elements)
            return result if isinstance(result, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    def __repr__(self):
        return f"<DocumentationPhrase {self.opportunity_code}/{self.phrase_category}: {self.phrase_title[:40]}>"


# Valid suppression reasons (Phase 22.1 taxonomy)
SUPPRESSION_REASONS = {
    "chart_unsupported",
    "already_completed",
    "payer_ineligible",
    "poor_expected_value",
    "excessive_denial_risk",
    "external_result_on_file",
    "standalone_too_weak",
    "frequency_limit_reached",
    "documentation_insufficient",
    "provider_disabled_category",
    "age_ineligible",
    "sex_ineligible",
    "concurrent_conflict",
}

# Valid funnel stages (Phase 22.5)
FUNNEL_STAGES = {
    "detected",
    "surfaced",
    "accepted",
    "documented",
    "billed",
    "paid",
    "denied",
    "adjusted",
    "dismissed",
    "deferred",
    "follow_up_needed",
}


class OpportunitySuppression(db.Model):
    """
    Phase 22.1: Tracks every billing opportunity that was evaluated but NOT
    surfaced to the provider, with a structured reason code.
    Powers the 'Why not?' explainability UI.
    """

    __tablename__ = "opportunity_suppression"

    id = db.Column(db.Integer, primary_key=True)
    patient_mrn_hash = db.Column(db.String(64), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    visit_date = db.Column(db.Date, nullable=True)
    opportunity_code = db.Column(db.String(50), nullable=False, index=True)
    suppression_reason = db.Column(db.String(50), nullable=False)
    detail = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return f"<OpportunitySuppression {self.opportunity_code} reason={self.suppression_reason}>"


class ClosedLoopStatus(db.Model):
    """
    Phase 22.5: Tracks the full funnel lifecycle of a billing opportunity.
    Each row is one stage transition. The chain of rows for a single
    opportunity_id forms the complete audit trail from detection to payment.
    """

    __tablename__ = "closed_loop_status"

    id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey("billing_opportunity.id"), nullable=True, index=True)
    patient_mrn_hash = db.Column(db.String(64), nullable=False, index=True)
    funnel_stage = db.Column(db.String(30), nullable=False)
    stage_date = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    stage_actor = db.Column(db.String(100), nullable=True)
    stage_notes = db.Column(db.Text, nullable=True)
    previous_stage = db.Column(db.String(30), nullable=True)

    def __repr__(self):
        return f"<ClosedLoopStatus opp={self.opportunity_id} stage={self.funnel_stage}>"


class BillingCampaign(db.Model):
    """
    Phase 27.1: Revenue campaign with target criteria, patient counts,
    and estimated vs actual revenue tracking.
    """

    __tablename__ = "billing_campaign"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    campaign_name = db.Column(db.String(200), nullable=False)
    campaign_type = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    target_criteria = db.Column(db.Text, nullable=True)  # JSON
    target_patient_count = db.Column(db.Integer, default=0)
    completed_count = db.Column(db.Integer, default=0)
    estimated_revenue = db.Column(db.Float, default=0.0)
    actual_revenue = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default="planned")  # planned | active | completed | paused
    created_by = db.Column(db.String(100), nullable=True)
    priority_score = db.Column(db.Float, default=0.0)
    time_to_cash_days = db.Column(db.Integer, default=30)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = db.relationship("User", backref=db.backref("campaigns", lazy="dynamic"))

    def get_criteria(self):
        """Parse JSON target_criteria."""
        try:
            import json
            return json.loads(self.target_criteria) if self.target_criteria else {}
        except Exception:
            return {}

    def completion_pct(self):
        if not self.target_patient_count:
            return 0
        return min(round(self.completed_count / self.target_patient_count * 100, 1), 100)

    def __repr__(self):
        return f"<BillingCampaign {self.campaign_name} [{self.status}]>"


class PayerCoverageMatrix(db.Model):
    """
    Phase 28.1: Payer coverage matrix for CPT/HCPCS codes.
    
    Each row describes whether a specific code is covered by a payer type,
    whether cost-share is waived, and any modifier/frequency/age/sex
    constraints. Seeded from Medicare coding guide, private payer guide,
    and HealthCare.gov preventive coverage references.
    """

    __tablename__ = "payer_coverage_matrix"

    id = db.Column(db.Integer, primary_key=True)
    cpt_code = db.Column(db.String(10), nullable=False, index=True)
    payer_type = db.Column(db.String(30), nullable=False, index=True)  # medicare_b, medicare_advantage, medicaid, commercial
    is_covered = db.Column(db.Boolean, default=True)
    cost_share_waived = db.Column(db.Boolean, default=False)
    modifier_required = db.Column(db.String(10), nullable=True)  # e.g. "33", "25"
    frequency_limit = db.Column(db.String(50), nullable=True)  # e.g. "1x/year", "1x/lifetime"
    age_range = db.Column(db.String(20), nullable=True)  # e.g. "50-75", "65+", "21+"
    sex_requirement = db.Column(db.String(1), nullable=True)  # "F", "M", or None
    coverage_notes = db.Column(db.Text, nullable=True)
    source_document = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<PayerCoverageMatrix {self.cpt_code} {self.payer_type}>"

    def cost_share_display(self, plan_label=None):
        """Return a patient-facing cost-share message."""
        label = plan_label or self.payer_type.replace("_", " ").title()
        if self.cost_share_waived:
            return f"$0 copay for {label}"
        return ""

    def modifier_display(self):
        """Return payer-specific modifier guidance."""
        if not self.modifier_required:
            return ""
        if self.payer_type in ("commercial", "medicaid"):
            return f"Modifier {self.modifier_required} required for zero cost-share"
        if self.payer_type == "medicare_b":
            return f"G-code (no copay/deductible)"
        return ""

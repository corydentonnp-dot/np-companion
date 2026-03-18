"""
NP Companion — Billing Intelligence Models
File: models/billing.py

SQLAlchemy ORM models for the billing opportunity engine:
- BillingOpportunity: per-patient, per-visit billing opportunities detected
  by the billing rules engine. Opportunities are surfaced in the Today View
  and post-visit billing review.
- BillingRuleCache: cached CMS Physician Fee Schedule code data, refreshed
  annually each November when CMS publishes the new fee schedule.

Dependencies:
- models/__init__.py (db instance)

NP Companion features that rely on this module:
- Billing Opportunity Engine (app/services/billing_rules.py)
- Today View billing card display
- Post-visit billing review (Timer/Billing module)
- Monthly Billing Report (F14c)
- Metrics dashboard (F13) — opportunity gap tracking

HIPAA note: BillingOpportunity stores patient_mrn_hash (SHA-256),
never the plain MRN. The plain MRN is only in PatientRecord.
"""

from datetime import datetime, timezone
from models import db


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
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    # The scheduled visit date this opportunity was detected for
    visit_date = db.Column(db.Date, nullable=False, index=True)

    # Which billing rule category this opportunity belongs to
    # Values: "CCM", "AWV", "TCM", "G2211", "99417", "BHI", "RPM"
    opportunity_type = db.Column(db.String(20), nullable=False)

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

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    reviewed_at = db.Column(db.DateTime, nullable=True)

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

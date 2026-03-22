"""
CareCompanion — Bonus Tracker Model
Phase 17.1

Tracks provider bonus structure, monthly receipts, collection rates,
and projected first bonus quarter.
"""

import json
from datetime import date, datetime, timezone
from models import db


class BonusTracker(db.Model):
    """
    One row per provider — tracks bonus structure.

    Default values from the provider's employment contract and
    the Bonus Calculation Sample workbook ($105K quarterly threshold).
    """
    __tablename__ = 'bonus_tracker'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True
    )

    provider_name = db.Column(db.String(200), default='')
    start_date = db.Column(db.Date, default=lambda: date(2026, 3, 2))

    # Compensation structure
    base_salary = db.Column(db.Float, default=115000.0)
    quarterly_threshold = db.Column(db.Float, default=105000.0)
    bonus_multiplier = db.Column(db.Float, default=0.25)

    # CRITICAL UNKNOWN — provider must confirm with practice administrator
    # whether cumulative deficit resets on Jan 1 or carries indefinitely
    deficit_resets_annually = db.Column(db.Boolean, default=True)

    # JSON: {"2026-03": 2100.00, "2026-04": 3500.00, ...}
    monthly_receipts = db.Column(db.Text, default='{}')

    # JSON: {"medicare": 0.67, "medicaid": 0.60, "commercial": 0.57, "self_pay": 0.35}
    collection_rates = db.Column(
        db.Text,
        default='{"medicare": 0.67, "medicaid": 0.60, "commercial": 0.57, "self_pay": 0.35}'
    )

    # Projections
    projected_first_bonus_quarter = db.Column(db.String(10), nullable=True)  # e.g. "2027-Q2"
    projected_first_bonus_date = db.Column(db.Date, nullable=True)

    # Flag: has the provider confirmed $105K threshold with admin?
    threshold_confirmed = db.Column(db.Boolean, default=False)

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = db.relationship('User', backref='bonus_tracker', lazy=True)

    def __repr__(self):
        return f'<BonusTracker user_id={self.user_id} threshold={self.quarterly_threshold}>'

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    def get_receipts(self) -> dict:
        """Return monthly_receipts as a Python dict."""
        try:
            return json.loads(self.monthly_receipts or '{}')
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_receipts(self, data: dict):
        self.monthly_receipts = json.dumps(data)

    def get_collection_rates(self) -> dict:
        try:
            return json.loads(self.collection_rates or '{}')
        except (json.JSONDecodeError, TypeError):
            return {"medicare": 0.67, "medicaid": 0.60, "commercial": 0.57, "self_pay": 0.35}

    def set_collection_rates(self, data: dict):
        self.collection_rates = json.dumps(data)

    def receipts_for_quarter(self, year: int, quarter: int) -> float:
        """Sum receipts for a specific quarter (Q1=Jan-Mar, Q2=Apr-Jun, etc.)."""
        receipts = self.get_receipts()
        start_month = (quarter - 1) * 3 + 1
        total = 0.0
        for m in range(start_month, start_month + 3):
            key = f"{year}-{m:02d}"
            total += receipts.get(key, 0.0)
        return total

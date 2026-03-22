"""
CareCompanion — Expected Net Value Scoring Engine
File: billing_engine/scoring.py
Phase 18.3

8-factor scoring model that replaces gross-revenue sorting with
risk-adjusted, practice-specific expected-net-value ranking.

Factors:
  1. Collection rate by payer
  2. Adjustment/write-off rate (from DiagnosisRevenueProfile)
  3. Denial risk proxy (>50% adj = high risk)
  4. Documentation burden (LOW → VERY_HIGH)
  5. Completion probability (standalone vs stack)
  6. Time-to-cash (immediate → complex)
  7. Bonus timing urgency (quarter-end weight)
  8. Staff effort (provider-only vs multi-staff)
"""

import logging
import math
from datetime import date

logger = logging.getLogger(__name__)

# ── Factor constants ──────────────────────────────────────────────

# Factor 4: Documentation burden by opportunity code prefix / category
_DOC_BURDEN_MAP = {
    # LOW — passive / MA-handleable
    "PROC_VENIPUNCTURE": 0.1, "PROC_PULSE_OX": 0.1,
    "IMM_FLU": 0.1, "IMM_COVID": 0.1, "IMM_PNEUMO": 0.1,
    "IMM_SHINGRIX": 0.1, "IMM_TDAP": 0.1, "IMM_HEPB": 0.1,
    "PROC_POCT": 0.1,
    # MEDIUM — screening instruments
    "SCREEN_PHQ9": 0.3, "SCREEN_GAD7": 0.3, "SCREEN_AUDIT": 0.3,
    "SCREEN_FALL_RISK": 0.3, "SCREEN_COGNITIVE": 0.3,
    "PROC_EKG": 0.3, "PROC_SPIROMETRY": 0.3,
    # HIGH — time documentation / care plan
    "AWV": 0.6, "AWV_INITIAL": 0.6, "AWV_SUBSEQUENT": 0.6,
    "ACP": 0.6, "G2211": 0.6, "TOBACCO": 0.6,
    "TCM": 0.6, "TCM_HIGH": 0.6, "TCM_MOD": 0.6,
    "PROC_99417": 0.6,
    # VERY_HIGH — multi-session tracking
    "CCM": 0.9, "BHI": 0.9, "COCM": 0.9, "RPM": 0.9, "PCM": 0.9,
}

# Factor 5: Completion probability by classification
_COMPLETION_MAP = {
    "STRONG_STANDALONE": 0.85,
    "STACK_ENHANCER": 0.75,
    "CONDITIONAL": 0.60,
    "STACK_ONLY": 0.50,
}

# Default classification by code prefix
_CLASSIFICATION_MAP = {
    "AWV": "STRONG_STANDALONE", "CCM": "STRONG_STANDALONE",
    "TCM": "STRONG_STANDALONE", "BHI": "STRONG_STANDALONE",
    "G2211": "STACK_ENHANCER", "TOBACCO": "STACK_ENHANCER",
    "SCREEN_": "STACK_ENHANCER", "PROC_": "CONDITIONAL",
    "IMM_": "CONDITIONAL", "ACP": "CONDITIONAL",
    "MON_": "STACK_ONLY",
}

# Factor 6: Time-to-cash days
_TIME_TO_CASH_MAP = {
    "PROC_VENIPUNCTURE": 0, "PROC_POCT": 0, "PROC_PULSE_OX": 0,
    "PROC_EKG": 0, "PROC_SPIROMETRY": 0,
    "IMM_": 0,
    "SCREEN_": 15,
    "AWV": 45, "G2211": 45, "TOBACCO": 45, "ACP": 45,
    "TCM": 60, "CCM": 75, "BHI": 75, "COCM": 75, "RPM": 75, "PCM": 75,
}

# Factor 8: Staff effort (0 = provider-only, 0.5 = MA-handleable, 1.0 = multi-staff)
_STAFF_EFFORT_MAP = {
    "PROC_VENIPUNCTURE": 0.5, "PROC_POCT": 0.5, "PROC_PULSE_OX": 0.5,
    "IMM_FLU": 0.5, "IMM_COVID": 0.5, "IMM_PNEUMO": 0.5,
    "IMM_SHINGRIX": 0.5, "IMM_TDAP": 0.5, "IMM_HEPB": 0.5,
    "SCREEN_PHQ9": 0.5, "SCREEN_GAD7": 0.5, "SCREEN_AUDIT": 0.5,
    "SCREEN_FALL_RISK": 0.5, "SCREEN_COGNITIVE": 0.5,
    "AWV": 0.0, "G2211": 0.0, "ACP": 0.0, "TOBACCO": 0.0,
    "PROC_EKG": 0.3, "PROC_SPIROMETRY": 0.3,
    "CCM": 1.0, "BHI": 1.0, "COCM": 1.0, "RPM": 1.0, "TCM": 0.7,
}


# ── Scoring weights ───────────────────────────────────────────────

WEIGHTS = {
    "collection_rate": 0.25,
    "denial_risk": 0.15,
    "doc_burden": 0.10,
    "completion_prob": 0.15,
    "time_to_cash": 0.10,
    "bonus_urgency": 0.10,
    "staff_effort": 0.05,
    "revenue_magnitude": 0.10,
}


def _lookup_map(code, mapping, default=0.5):
    """Look up code in mapping, with prefix fallback."""
    if code in mapping:
        return mapping[code]
    # Try prefix match
    for prefix, val in mapping.items():
        if prefix.endswith('_') and code.startswith(prefix):
            return val
    return default


class ExpectedNetValueCalculator:
    """
    Scores billing opportunities with 8 weighted factors.

    Usage:
        calc = ExpectedNetValueCalculator(collection_rates, dx_profiles)
        for opp in opportunities:
            calc.score(opp, patient_data)
    """

    def __init__(self, collection_rates=None, dx_profiles=None,
                 bonus_tracker=None):
        """
        Parameters
        ----------
        collection_rates : dict
            {"medicare": 0.67, "commercial": 0.57, ...}
        dx_profiles : dict
            {icd10_code: DiagnosisRevenueProfile} for quick lookup
        bonus_tracker : BonusTracker or None
            If provided, used for bonus timing urgency (Factor 7).
        """
        self.collection_rates = collection_rates or {
            "medicare": 0.67, "medicare_advantage": 0.70,
            "medicaid": 0.60, "commercial": 0.57, "self_pay": 0.35,
            "unknown": 0.55,
        }
        self.dx_profiles = dx_profiles or {}
        self.bonus_tracker = bonus_tracker

    def score(self, opp, patient_data=None):
        """
        Score a single BillingOpportunity, populating:
          - expected_net_dollars
          - opportunity_score (0.0 - 1.0)
          - urgency_score (0.0 - 1.0)
          - implementation_priority
          - bonus_impact_dollars
          - bonus_impact_days

        Returns the opportunity (mutated in place).
        """
        code = getattr(opp, 'opportunity_code', '') or getattr(opp, 'opportunity_type', '') or ''
        insurer = getattr(opp, 'insurer_type', 'unknown') or 'unknown'
        gross_rev = opp.estimated_revenue or 0.0

        # Factor 1: Collection rate by payer
        f1_collection = self.collection_rates.get(
            insurer, self.collection_rates.get('unknown', 0.55))

        # Factor 2: Adjustment rate from diagnosis profile
        f2_adj_rate = self._get_adjustment_rate(patient_data)

        # Factor 3: Denial risk (>50% adj = high risk)
        f3_denial = 1.0 - min(f2_adj_rate * 1.5, 1.0)  # Higher adj → lower score

        # Factor 4: Documentation burden
        f4_doc = 1.0 - _lookup_map(code, _DOC_BURDEN_MAP, 0.5)

        # Factor 5: Completion probability
        classification = self._classify(code)
        f5_completion = _COMPLETION_MAP.get(classification, 0.60)

        # Factor 6: Time-to-cash (shorter = better score)
        ttc_days = _lookup_map(code, _TIME_TO_CASH_MAP, 45)
        f6_ttc = max(0.0, 1.0 - (ttc_days / 90.0))

        # Factor 7: Bonus timing urgency
        f7_urgency = self._bonus_urgency()

        # Factor 8: Staff effort (lower = easier for provider)
        f8_staff = 1.0 - _lookup_map(code, _STAFF_EFFORT_MAP, 0.3)

        # Revenue magnitude factor (normalized: $300 = 1.0, $0 = 0.0)
        f_rev_mag = min(gross_rev / 300.0, 1.0)

        # Weighted composite (0.0 - 1.0)
        opportunity_score = (
            WEIGHTS["collection_rate"] * f1_collection +
            WEIGHTS["denial_risk"] * f3_denial +
            WEIGHTS["doc_burden"] * f4_doc +
            WEIGHTS["completion_prob"] * f5_completion +
            WEIGHTS["time_to_cash"] * f6_ttc +
            WEIGHTS["bonus_urgency"] * f7_urgency +
            WEIGHTS["staff_effort"] * f8_staff +
            WEIGHTS["revenue_magnitude"] * f_rev_mag
        )

        # Expected net dollars
        expected_net = gross_rev * f1_collection * (1.0 - f2_adj_rate) * f5_completion
        bonus_multiplier = 0.25
        bonus_impact = expected_net * bonus_multiplier

        # Bonus impact in days: expected_net / (threshold / 63 biz days)
        daily_rate = 105000.0 / 63.0
        bonus_impact_days = expected_net / daily_rate if daily_rate > 0 else 0

        # Implementation priority
        if opportunity_score >= 0.70:
            impl_priority = "critical"
        elif opportunity_score >= 0.55:
            impl_priority = "high"
        elif opportunity_score >= 0.40:
            impl_priority = "medium"
        else:
            impl_priority = "low"

        # Assign to opportunity
        opp.expected_net_dollars = round(expected_net, 2)
        opp.opportunity_score = round(opportunity_score, 4)
        opp.urgency_score = round(f7_urgency, 4)
        opp.implementation_priority = impl_priority
        opp.bonus_impact_dollars = round(bonus_impact, 2)
        opp.bonus_impact_days = round(bonus_impact_days, 2)

        return opp

    def _get_adjustment_rate(self, patient_data):
        """Get average adjustment rate from patient's diagnoses."""
        if not patient_data or not self.dx_profiles:
            return 0.30  # Default 30%

        diagnoses = patient_data.get('diagnoses') or []
        rates = []
        for dx in diagnoses:
            code = dx.get('code', '') if isinstance(dx, dict) else str(dx)
            if code in self.dx_profiles:
                profile = self.dx_profiles[code]
                adj = getattr(profile, 'adjustment_rate', 0.30)
                rates.append(adj)

        return sum(rates) / len(rates) if rates else 0.30

    def _classify(self, code):
        """Classify opportunity code into standalone/stack categories."""
        if code in _CLASSIFICATION_MAP:
            return _CLASSIFICATION_MAP[code]
        for prefix, cls in _CLASSIFICATION_MAP.items():
            if prefix.endswith('_') and code.startswith(prefix):
                return cls
        return "CONDITIONAL"

    def _bonus_urgency(self):
        """
        Factor 7: Higher urgency near quarter-end with small deficit gap.
        Returns 0.0 (no urgency) to 1.0 (maximum urgency).
        """
        today = date.today()
        quarter = (today.month - 1) // 3 + 1
        q_end_month = quarter * 3
        if q_end_month == 12:
            q_end = date(today.year, 12, 31)
        else:
            q_end = date(today.year, q_end_month + 1, 1)

        days_remaining = (q_end - today).days
        # Time component: more urgent as quarter-end approaches
        time_factor = max(0.0, 1.0 - (days_remaining / 90.0))

        # Gap component: if we have bonus tracker data
        gap_factor = 0.5  # Default medium
        if self.bonus_tracker:
            try:
                from app.services.bonus_calculator import current_quarter_status
                status = current_quarter_status(self.bonus_tracker)
                gap = status.get('gap', 105000)
                if gap <= 0:
                    gap_factor = 0.1  # Already exceeded, low urgency
                elif gap < 25000:
                    gap_factor = 0.9  # Close — high urgency
                elif gap < 50000:
                    gap_factor = 0.6
                else:
                    gap_factor = 0.3
            except Exception:
                pass

        return min(1.0, time_factor * 0.5 + gap_factor * 0.5)

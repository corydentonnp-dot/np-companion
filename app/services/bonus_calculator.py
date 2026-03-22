"""
CareCompanion — Bonus Calculator Service
Phase 17.3

Implements the bonus math from the Bonus Calculation Sample workbook:
  Quarterly Bonus = (Receipts - $105,000) × 0.25
  with cumulative deficit carry-forward.

Supports both deficit_resets_annually=True and =False.
"""

from datetime import date
import math


def calculate_quarterly_bonus(receipts: float, threshold: float,
                              cumulative_deficit: float = 0.0) -> dict:
    """
    Calculate bonus for a single quarter.

    Parameters
    ----------
    receipts : float
        Total receipts for the quarter.
    threshold : float
        Quarterly threshold (default $105,000).
    cumulative_deficit : float
        Carried-forward deficit from prior quarters.

    Returns
    -------
    dict with keys:
        gross_surplus  — receipts - threshold (before deficit)
        net_surplus    — gross_surplus - cumulative_deficit (what's bonus-eligible)
        bonus_amount   — net_surplus × 0.25 (or 0 if net_surplus ≤ 0)
        new_deficit    — updated cumulative deficit going forward
        exceeded       — bool, whether bonus was earned
    """
    gross_surplus = receipts - threshold

    if gross_surplus <= 0:
        # Quarter below threshold — deficit grows
        return {
            "gross_surplus": gross_surplus,
            "net_surplus": 0.0,
            "bonus_amount": 0.0,
            "new_deficit": cumulative_deficit + abs(gross_surplus),
            "exceeded": False,
        }

    # Quarter above threshold — apply against deficit first
    net_surplus = gross_surplus - cumulative_deficit
    if net_surplus <= 0:
        return {
            "gross_surplus": gross_surplus,
            "net_surplus": 0.0,
            "bonus_amount": 0.0,
            "new_deficit": abs(net_surplus),
            "exceeded": False,
        }

    return {
        "gross_surplus": gross_surplus,
        "net_surplus": net_surplus,
        "bonus_amount": net_surplus * 0.25,
        "new_deficit": 0.0,
        "exceeded": True,
    }


def project_first_bonus_quarter(current_receipts: dict, threshold: float,
                                deficit: float = 0.0,
                                growth_rate: float = 0.0,
                                deficit_resets_annually: bool = True,
                                start_year: int = 2026,
                                start_quarter: int = 2) -> dict:
    """
    Project the first quarter where bonus is earned.

    Parameters
    ----------
    current_receipts : dict
        {"2026-03": 2100.00, ...} — actual receipts by month.
    threshold : float
        Quarterly threshold.
    deficit : float
        Starting cumulative deficit.
    growth_rate : float
        Monthly growth rate (0.05 = 5% per month).
    deficit_resets_annually : bool
        Whether deficit resets to 0 on Jan 1 each year.
    start_year : int
        Year to start projecting from.
    start_quarter : int
        Quarter to start projecting (1-4).

    Returns
    -------
    dict with keys:
        first_bonus_quarter — "2027-Q3" or None if not projected within 3 years
        first_bonus_date    — date object for first day of that quarter
        quarters            — list of quarter-by-quarter projections
    """
    quarters = []
    cum_deficit = deficit

    # Calculate average monthly receipts from actuals
    actual_months = sorted(current_receipts.keys())
    if actual_months:
        avg_monthly = sum(current_receipts.values()) / len(actual_months)
    else:
        avg_monthly = 0.0

    monthly_estimate = avg_monthly

    for offset in range(12):  # Project up to 12 quarters (3 years)
        q = start_quarter + offset
        year = start_year + (q - 1) // 4
        quarter = ((q - 1) % 4) + 1

        # Reset deficit on Q1 if configured
        if deficit_resets_annually and quarter == 1 and offset > 0:
            cum_deficit = 0.0

        # Build quarter receipts: use actuals if available, else estimate
        q_receipts = 0.0
        for m_offset in range(3):
            month_num = (quarter - 1) * 3 + 1 + m_offset
            key = f"{year}-{month_num:02d}"
            if key in current_receipts:
                q_receipts += current_receipts[key]
            else:
                q_receipts += monthly_estimate
                monthly_estimate *= (1 + growth_rate)

        result = calculate_quarterly_bonus(q_receipts, threshold, cum_deficit)
        quarter_label = f"{year}-Q{quarter}"
        result["quarter"] = quarter_label
        result["receipts"] = q_receipts
        quarters.append(result)
        cum_deficit = result["new_deficit"]

        if result["exceeded"]:
            first_month = (quarter - 1) * 3 + 1
            return {
                "first_bonus_quarter": quarter_label,
                "first_bonus_date": date(year, first_month, 1),
                "quarters": quarters,
            }

    return {
        "first_bonus_quarter": None,
        "first_bonus_date": None,
        "quarters": quarters,
    }


def calculate_opportunity_impact(estimated_revenue: float,
                                 collection_rate: float,
                                 threshold: float = 105000.0,
                                 bonus_multiplier: float = 0.25) -> dict:
    """
    Calculate how a single billing opportunity impacts the bonus.

    Parameters
    ----------
    estimated_revenue : float
        Gross revenue from the opportunity.
    collection_rate : float
        Expected collection rate (0.0 - 1.0).
    threshold : float
        Quarterly threshold.
    bonus_multiplier : float
        Bonus multiplier (default 0.25).

    Returns
    -------
    dict with keys:
        expected_receipts — revenue × collection rate
        bonus_impact      — expected_receipts × bonus_multiplier (max theoretical)
        daily_rate_impact — how much this reduces the daily rate needed
    """
    expected_receipts = estimated_revenue * collection_rate
    bonus_impact = expected_receipts * bonus_multiplier

    # Daily rate: $105K / ~63 business days per quarter
    business_days_per_quarter = 63
    daily_rate_impact = expected_receipts / business_days_per_quarter

    return {
        "expected_receipts": round(expected_receipts, 2),
        "bonus_impact": round(bonus_impact, 2),
        "daily_rate_impact": round(daily_rate_impact, 2),
    }


def current_quarter_status(tracker) -> dict:
    """
    Build status dict for the current quarter from a BonusTracker instance.

    Returns
    -------
    dict with keys:
        year, quarter, quarter_label,
        receipts_to_date, threshold, gap, pct_of_threshold,
        daily_rate_needed, run_rate, will_exceed,
        days_elapsed, days_remaining, business_days_remaining
    """
    today = date.today()
    year = today.year
    quarter = (today.month - 1) // 3 + 1
    q_start_month = (quarter - 1) * 3 + 1

    receipts = tracker.get_receipts()
    q_total = 0.0
    for m in range(q_start_month, q_start_month + 3):
        key = f"{year}-{m:02d}"
        q_total += receipts.get(key, 0.0)

    threshold = tracker.quarterly_threshold or 105000.0
    gap = max(0, threshold - q_total)
    pct = (q_total / threshold * 100) if threshold > 0 else 0

    # Days in quarter
    q_end_month = q_start_month + 2
    if q_end_month == 12:
        q_end_date = date(year, 12, 31)
    else:
        q_end_date = date(year, q_end_month + 1, 1)
    q_start_date = date(year, q_start_month, 1)

    total_days = (q_end_date - q_start_date).days
    days_elapsed = max(0, (today - q_start_date).days)
    days_remaining = max(0, (q_end_date - today).days)

    # Approximate business days remaining (~5/7 of remaining days)
    business_days_remaining = max(1, math.ceil(days_remaining * 5 / 7))

    # Run rate and daily rate needed
    if days_elapsed > 0:
        run_rate = q_total / days_elapsed * total_days
    else:
        run_rate = 0.0

    daily_rate_needed = gap / business_days_remaining if business_days_remaining > 0 else 0

    return {
        "year": year,
        "quarter": quarter,
        "quarter_label": f"{year}-Q{quarter}",
        "receipts_to_date": round(q_total, 2),
        "threshold": threshold,
        "gap": round(gap, 2),
        "pct_of_threshold": round(pct, 1),
        "daily_rate_needed": round(daily_rate_needed, 2),
        "run_rate": round(run_rate, 2),
        "will_exceed": run_rate >= threshold,
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "business_days_remaining": business_days_remaining,
    }

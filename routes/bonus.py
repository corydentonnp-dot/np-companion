"""
CareCompanion — Bonus Tracker Routes
File: routes/bonus.py
Phase 17.4
"""

import json
import logging
from datetime import date, datetime

from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user

from models import db
from models.bonus import BonusTracker
from app.services.bonus_calculator import (
    calculate_quarterly_bonus,
    project_first_bonus_quarter,
    calculate_opportunity_impact,
    current_quarter_status,
    build_deficit_history as _build_deficit_history,  # B1.20
)

logger = logging.getLogger(__name__)

bonus_bp = Blueprint('bonus', __name__)


@bonus_bp.route('/bonus')
@login_required
def bonus_dashboard():
    """Render the bonus tracker dashboard."""
    tracker = BonusTracker.query.filter_by(user_id=current_user.id).first()
    if not tracker:
        tracker = BonusTracker(
            user_id=current_user.id,
            provider_name=getattr(current_user, 'display_name', '') or getattr(current_user, 'username', ''),
        )
        db.session.add(tracker)
        db.session.commit()

    status = current_quarter_status(tracker)

    # Build deficit history from receipts
    receipts = tracker.get_receipts()
    threshold = tracker.quarterly_threshold or 105000.0
    deficit_history = _build_deficit_history(receipts, threshold,
                                            tracker.deficit_resets_annually)

    # Projection — Scenario A: current pace (0% growth)
    today = date.today()
    year = today.year
    quarter = (today.month - 1) // 3 + 1
    current_deficit = deficit_history[-1]["cumulative_deficit"] if deficit_history else 0.0

    proj_a = project_first_bonus_quarter(
        receipts, threshold, deficit=current_deficit,
        growth_rate=0.0, deficit_resets_annually=tracker.deficit_resets_annually,
        start_year=year, start_quarter=quarter,
    )

    # Projection — Scenario B: with 5% monthly growth (optimization)
    proj_b = project_first_bonus_quarter(
        receipts, threshold, deficit=current_deficit,
        growth_rate=0.05, deficit_resets_annually=tracker.deficit_resets_annually,
        start_year=year, start_quarter=quarter,
    )

    # CCM impact estimate: $62/mo × 3 months = $186/quarter per patient
    ccm_per_quarter = 186.0
    collection_rates = tracker.get_collection_rates()
    ccm_collection = collection_rates.get("ccm", 0.85)

    # Quarter-end surge mode: <30 days remaining AND gap < $25K
    surge_mode = status["days_remaining"] < 30 and 0 < status["gap"] < 25000

    # Threshold mismatch warning (17.9)
    threshold_warning = not tracker.threshold_confirmed

    return render_template(
        'bonus_dashboard.html',
        tracker=tracker,
        status=status,
        deficit_history=deficit_history,
        proj_a=proj_a,
        proj_b=proj_b,
        ccm_per_quarter=ccm_per_quarter,
        ccm_collection=ccm_collection,
        surge_mode=surge_mode,
        threshold_warning=threshold_warning,
        collection_rates=collection_rates,
    )


@bonus_bp.route('/bonus/entry', methods=['POST'])
@login_required
def bonus_entry():
    """Record monthly receipt entry."""
    tracker = BonusTracker.query.filter_by(user_id=current_user.id).first()
    if not tracker:
        return jsonify({"error": "No bonus tracker configured"}), 404

    data = request.form
    month_key = data.get('month_key', '').strip()
    amount_str = data.get('amount', '').strip()

    # Validate month_key format: YYYY-MM
    if not month_key or len(month_key) != 7 or month_key[4] != '-':
        return jsonify({"error": "Invalid month format. Use YYYY-MM"}), 400
    try:
        int(month_key[:4])
        m = int(month_key[5:])
        if m < 1 or m > 12:
            raise ValueError
    except (ValueError, IndexError):
        return jsonify({"error": "Invalid month format. Use YYYY-MM"}), 400

    try:
        amount = float(amount_str)
        if amount < 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid amount"}), 400

    receipts = tracker.get_receipts()
    receipts[month_key] = amount
    tracker.set_receipts(receipts)
    db.session.commit()

    return jsonify({"ok": True, "month": month_key, "amount": amount})


@bonus_bp.route('/bonus/calibrate', methods=['POST'])
@login_required
def bonus_calibrate():
    """Update collection rates."""
    tracker = BonusTracker.query.filter_by(user_id=current_user.id).first()
    if not tracker:
        return jsonify({"error": "No bonus tracker configured"}), 404

    data = request.get_json(silent=True) or {}
    rates = tracker.get_collection_rates()

    for key, val in data.items():
        key = str(key).strip()[:50]
        try:
            rate = float(val)
            if 0 <= rate <= 1.0:
                rates[key] = rate
        except (ValueError, TypeError):
            continue

    tracker.set_collection_rates(rates)
    db.session.commit()

    return jsonify({"ok": True, "rates": rates})


@bonus_bp.route('/api/bonus/projection')
@login_required
def bonus_projection_api():
    """JSON endpoint for AJAX projection updates."""
    tracker = BonusTracker.query.filter_by(user_id=current_user.id).first()
    if not tracker:
        return jsonify({"error": "No bonus tracker configured"}), 404

    growth_rate = request.args.get('growth', 0.0, type=float)
    if growth_rate < -0.5 or growth_rate > 1.0:
        growth_rate = 0.0

    receipts = tracker.get_receipts()
    threshold = tracker.quarterly_threshold or 105000.0

    deficit_history = _build_deficit_history(receipts, threshold,
                                            tracker.deficit_resets_annually)
    current_deficit = deficit_history[-1]["cumulative_deficit"] if deficit_history else 0.0

    today = date.today()
    proj = project_first_bonus_quarter(
        receipts, threshold, deficit=current_deficit,
        growth_rate=growth_rate,
        deficit_resets_annually=tracker.deficit_resets_annually,
        start_year=today.year,
        start_quarter=(today.month - 1) // 3 + 1,
    )

    # Serialize dates
    result = {
        "first_bonus_quarter": proj["first_bonus_quarter"],
        "first_bonus_date": proj["first_bonus_date"].isoformat() if proj["first_bonus_date"] else None,
        "quarters": proj["quarters"],
    }

    return jsonify(result)


@bonus_bp.route('/bonus/confirm-threshold', methods=['POST'])
@login_required
def bonus_confirm_threshold():
    """Confirm the threshold value is correct (dismisses mismatch warning)."""
    tracker = BonusTracker.query.filter_by(user_id=current_user.id).first()
    if not tracker:
        return jsonify({"error": "No bonus tracker configured"}), 404

    tracker.threshold_confirmed = True
    db.session.commit()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Helpers (moved to app/services/bonus_calculator.py — B1.20)
# ---------------------------------------------------------------------------
# _build_deficit_history is imported above from bonus_calculator

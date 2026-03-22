"""
CareCompanion — Revenue Reporting + Reconciliation Routes
File: routes/revenue.py
Phase 26

Full-funnel revenue reporting: detected → captured → billed → paid → denied,
leakage attribution, diagnosis-family rollups, annual opportunity estimates,
and bonus projection.
"""

import json
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user

from models import db
from models.billing import (
    BillingOpportunity, ClosedLoopStatus, DiagnosisRevenueProfile,
)

logger = logging.getLogger(__name__)

revenue_bp = Blueprint('revenue', __name__)

# ============================================================
# 26.1 — Monthly Revenue Report
# ============================================================

@revenue_bp.route('/reports/revenue/<int:year>/<int:month>')
@login_required
def revenue_report(year, month):
    """Revenue dashboard: detected vs captured vs billed vs paid by category."""
    if not (1 <= month <= 12) or not (2020 <= year <= 2099):
        return render_template('errors/404.html'), 404
    uid = current_user.id

    # All opportunities for the month
    opps = (
        BillingOpportunity.query
        .filter(
            BillingOpportunity.user_id == uid,
            db.extract('year', BillingOpportunity.visit_date) == year,
            db.extract('month', BillingOpportunity.visit_date) == month,
        )
        .all()
    )

    # Category breakdown
    categories = defaultdict(lambda: {
        'detected': 0, 'captured': 0, 'dismissed': 0, 'partial': 0,
        'rev_detected': 0.0, 'rev_captured': 0.0, 'rev_missed': 0.0,
        'bonus_impact': 0.0,
    })

    total = {
        'detected': 0, 'captured': 0, 'dismissed': 0, 'partial': 0,
        'rev_detected': 0.0, 'rev_captured': 0.0, 'rev_missed': 0.0,
        'bonus_impact': 0.0,
    }

    for opp in opps:
        cat = opp.opportunity_type or 'unknown'
        rev = opp.estimated_revenue or 0
        net = opp.expected_net_dollars or rev
        bonus = opp.bonus_impact_dollars or 0

        categories[cat]['detected'] += 1
        categories[cat]['rev_detected'] += net
        total['detected'] += 1
        total['rev_detected'] += net

        if opp.status == 'captured':
            categories[cat]['captured'] += 1
            categories[cat]['rev_captured'] += net
            categories[cat]['bonus_impact'] += bonus
            total['captured'] += 1
            total['rev_captured'] += net
            total['bonus_impact'] += bonus
        elif opp.status == 'dismissed':
            categories[cat]['dismissed'] += 1
            categories[cat]['rev_missed'] += net
            total['dismissed'] += 1
            total['rev_missed'] += net
        elif opp.status == 'partial':
            categories[cat]['partial'] += 1
            categories[cat]['rev_captured'] += net * 0.5
            categories[cat]['rev_missed'] += net * 0.5
            total['partial'] += 1
            total['rev_captured'] += net * 0.5
            total['rev_missed'] += net * 0.5
        else:
            categories[cat]['rev_missed'] += net
            total['rev_missed'] += net

    capture_rate = (
        round(total['captured'] / total['detected'] * 100, 1)
        if total['detected'] else 0
    )

    # Sort categories by revenue potential descending
    sorted_cats = sorted(categories.items(), key=lambda x: x[1]['rev_detected'], reverse=True)

    # Top missed opportunities (uncaptured, highest value)
    top_missed = sorted(
        [o for o in opps if o.status not in ('captured',)],
        key=lambda o: (o.expected_net_dollars or o.estimated_revenue or 0),
        reverse=True,
    )[:10]

    # ------ 26.2  Reconciliation funnel from ClosedLoopStatus ------
    opp_ids = [o.id for o in opps]
    funnel_data = _build_funnel(opp_ids)

    # ------ 26.3  Leakage cause attribution ------
    leakage = _build_leakage(opp_ids)

    # ------ 26.5  Annual billing opportunity estimate ------
    annual_estimate = round(total['rev_detected'] * 12, 2)
    annual_captured = round(total['rev_captured'] * 12, 2)
    annual_gap = round(annual_estimate - annual_captured, 2)

    # ------ 26.6  First-bonus projection ------
    bonus_projection = _get_bonus_projection(uid)

    return render_template(
        'revenue_report_full.html',
        year=year,
        month=month,
        total=total,
        capture_rate=capture_rate,
        categories=sorted_cats,
        top_missed=top_missed,
        funnel=funnel_data,
        leakage=leakage,
        annual_estimate=annual_estimate,
        annual_captured=annual_captured,
        annual_gap=annual_gap,
        bonus_projection=bonus_projection,
    )


# ============================================================
# 26.4 — Diagnosis-Family Rollup Report
# ============================================================

DX_FAMILIES = {
    'HTN': {'prefixes': ['I10', 'I11', 'I12', 'I13', 'I15'], 'label': 'Hypertension'},
    'DM': {'prefixes': ['E10', 'E11', 'E13', 'R73'], 'label': 'Diabetes / Pre-Diabetes'},
    'HLD': {'prefixes': ['E78'], 'label': 'Hyperlipidemia'},
    'Thyroid': {'prefixes': ['E03', 'E05', 'E06'], 'label': 'Thyroid'},
    'BH': {'prefixes': ['F41', 'F32', 'F43', 'F90', 'F31'], 'label': 'Behavioral Health'},
    'Tobacco': {'prefixes': ['F17'], 'label': 'Tobacco Use'},
    'Obesity': {'prefixes': ['E66'], 'label': 'Obesity'},
    'Preventive': {'prefixes': ['Z00', 'Z13', 'Z12', 'Z23'], 'label': 'Preventive / Screening'},
}


@revenue_bp.route('/reports/dx-families')
@login_required
def dx_family_report():
    """Diagnosis-family rollup: encounters, received, adj rate, linked opportunities."""
    uid = current_user.id

    # Pull all DiagnosisRevenueProfile rows
    profiles = DiagnosisRevenueProfile.query.filter_by(user_id=uid).all()

    families = []
    for fam_key, fam_spec in DX_FAMILIES.items():
        prefixes = fam_spec['prefixes']
        matching = [
            p for p in profiles
            if any(p.icd10_code and p.icd10_code.startswith(px) for px in prefixes)
        ]

        encounters = sum(p.encounters_annual or 0 for p in matching)
        received = sum(p.received_annual or 0 for p in matching)
        billed = sum(p.billed_annual or 0 for p in matching)
        adj_rate = round(
            sum(p.adjusted_annual or 0 for p in matching)
            / billed * 100, 1
        ) if billed else 0

        # Linked billing opportunities (current year)
        current_year = date.today().year
        linked_opps = (
            BillingOpportunity.query
            .filter(
                BillingOpportunity.user_id == uid,
                db.extract('year', BillingOpportunity.visit_date) == current_year,
            )
            .all()
        )
        family_opps = [
            o for o in linked_opps
            if _opp_matches_family(o, prefixes)
        ]
        opp_captured = sum(
            1 for o in family_opps if o.status == 'captured'
        )
        opp_total = len(family_opps)
        opp_capture_pct = round(opp_captured / opp_total * 100, 1) if opp_total else 0

        families.append({
            'key': fam_key,
            'label': fam_spec['label'],
            'prefixes': prefixes,
            'encounters': encounters,
            'received': received,
            'billed': billed,
            'adj_rate': adj_rate,
            'opp_total': opp_total,
            'opp_captured': opp_captured,
            'opp_capture_pct': opp_capture_pct,
            'codes': [p.icd10_code for p in matching[:10]],
        })

    families.sort(key=lambda f: f['received'], reverse=True)

    return render_template(
        'dx_family_report.html',
        families=families,
    )


# ============================================================
# JSON API for chart data
# ============================================================

@revenue_bp.route('/api/revenue/summary')
@login_required
def revenue_summary_api():
    """JSON summary for dashboard widgets or AJAX calls."""
    uid = current_user.id
    today = date.today()
    year, month = today.year, today.month

    opps = (
        BillingOpportunity.query
        .filter(
            BillingOpportunity.user_id == uid,
            db.extract('year', BillingOpportunity.visit_date) == year,
            db.extract('month', BillingOpportunity.visit_date) == month,
        )
        .all()
    )

    detected = len(opps)
    captured = sum(1 for o in opps if o.status == 'captured')
    rev_detected = sum(o.expected_net_dollars or o.estimated_revenue or 0 for o in opps)
    rev_captured = sum(
        o.expected_net_dollars or o.estimated_revenue or 0
        for o in opps if o.status == 'captured'
    )

    return jsonify({
        'detected': detected,
        'captured': captured,
        'capture_rate': round(captured / detected * 100, 1) if detected else 0,
        'rev_detected': round(rev_detected, 2),
        'rev_captured': round(rev_captured, 2),
        'rev_gap': round(rev_detected - rev_captured, 2),
    })


# ============================================================
# Helper functions
# ============================================================

def _build_funnel(opp_ids):
    """26.2: Aggregate ClosedLoopStatus stages for given opportunity IDs."""
    if not opp_ids:
        return []

    stages_order = [
        'detected', 'surfaced', 'accepted', 'documented',
        'billed', 'paid', 'denied', 'adjusted',
    ]

    stage_counts = defaultdict(int)
    rows = (
        ClosedLoopStatus.query
        .filter(ClosedLoopStatus.opportunity_id.in_(opp_ids))
        .all()
    )
    for r in rows:
        if r.funnel_stage:
            stage_counts[r.funnel_stage] += 1

    total = stage_counts.get('detected', len(opp_ids))
    funnel = []
    for stage in stages_order:
        count = stage_counts.get(stage, 0)
        pct = round(count / total * 100, 1) if total else 0
        funnel.append({'stage': stage, 'count': count, 'pct': pct})

    # Leakage between adjacent stages
    for i in range(1, len(funnel)):
        prev_count = funnel[i - 1]['count']
        curr_count = funnel[i]['count']
        funnel[i]['leakage_pct'] = (
            round((prev_count - curr_count) / prev_count * 100, 1)
            if prev_count else 0
        )

    return funnel


def _build_leakage(opp_ids):
    """26.3: Attribute leakage causes from ClosedLoopStatus notes."""
    if not opp_ids:
        return {}

    cause_map = {
        'detection_gap': 0,
        'workflow_drop': 0,
        'documentation_failure': 0,
        'modifier_failure': 0,
        'payer_denial': 0,
        'staff_bottleneck': 0,
        'patient_refusal': 0,
        'other': 0,
    }

    # Look at dismissed / denied / adjusted stages
    rows = (
        ClosedLoopStatus.query
        .filter(
            ClosedLoopStatus.opportunity_id.in_(opp_ids),
            ClosedLoopStatus.funnel_stage.in_(['dismissed', 'denied', 'adjusted']),
        )
        .all()
    )

    for r in rows:
        notes = (r.stage_notes or '').lower()
        if 'detection' in notes or 'not detected' in notes:
            cause_map['detection_gap'] += 1
        elif 'workflow' in notes or 'missed step' in notes:
            cause_map['workflow_drop'] += 1
        elif 'document' in notes or 'note' in notes:
            cause_map['documentation_failure'] += 1
        elif 'modifier' in notes:
            cause_map['modifier_failure'] += 1
        elif 'payer' in notes or 'denied' in notes or 'denial' in notes:
            cause_map['payer_denial'] += 1
        elif 'staff' in notes or 'bottleneck' in notes:
            cause_map['staff_bottleneck'] += 1
        elif 'patient' in notes or 'refus' in notes:
            cause_map['patient_refusal'] += 1
        else:
            cause_map['other'] += 1

    return cause_map


def _get_bonus_projection(user_id):
    """26.6: Pull bonus tracker data for first-bonus projection."""
    try:
        from models.bonus import BonusTracker
        tracker = BonusTracker.query.filter_by(user_id=user_id).first()
        if not tracker:
            return None

        receipts = tracker.get_monthly_receipts()
        threshold = tracker.quarterly_threshold or 105000
        multiplier = tracker.bonus_multiplier or 0.25

        today = date.today()
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        quarter_months = [
            f"{today.year}-{m:02d}"
            for m in range(quarter_start_month, quarter_start_month + 3)
        ]
        quarter_receipts = sum(receipts.get(m, 0) for m in quarter_months)
        deficit = max(threshold - quarter_receipts, 0)

        return {
            'threshold': threshold,
            'multiplier': multiplier,
            'quarter_receipts': round(quarter_receipts, 2),
            'deficit': round(deficit, 2),
            'projected_first_bonus_quarter': tracker.projected_first_bonus_quarter,
            'projected_first_bonus_date': (
                tracker.projected_first_bonus_date.isoformat()
                if tracker.projected_first_bonus_date else None
            ),
        }
    except Exception:
        return None


def _opp_matches_family(opp, prefixes):
    """Check if an opportunity is related to the given ICD-10 family."""
    # Check primary_code if available; fall back to opportunity_type heuristic
    code = getattr(opp, 'primary_icd10', None) or ''
    if any(code.startswith(px) for px in prefixes):
        return True
    detail = getattr(opp, 'detail_json', None) or '{}'
    try:
        d = json.loads(detail) if isinstance(detail, str) else (detail or {})
        codes = d.get('icd10_codes', [])
        return any(
            c.startswith(px) for c in codes for px in prefixes
        )
    except Exception:
        return False

"""
CareCompanion — Campaign Mode + Admin ROI Routes
File: routes/campaigns.py
Phase 27

Revenue campaigns with patient targeting, ROI tracking,
and admin billing ROI dashboard.
"""

import json
import logging
from collections import defaultdict
from datetime import date, timedelta

from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user

from models import db
from models.billing import (
    BillingCampaign, BillingOpportunity, ClosedLoopStatus,
)
from routes.auth import require_role

logger = logging.getLogger(__name__)

campaigns_bp = Blueprint('campaigns', __name__)

# ============================================================
# 27.3 — Campaign templates
# ============================================================

CAMPAIGN_TEMPLATES = [
    {
        'type': 'awv_push',
        'name': 'Medicare AWV Push',
        'description': 'Medicare patients without AWV in 12 months — scheduling outreach',
        'criteria': {'insurer_type': 'medicare', 'missing': 'AWV', 'lookback_months': 12},
        'time_to_cash_days': 14,
    },
    {
        'type': 'htn_optimization',
        'name': 'HTN Optimization',
        'description': 'I10 + BP >140/90 — E/M + G2211 + labs',
        'criteria': {'dx_prefix': ['I10'], 'bp_threshold': '140/90'},
        'time_to_cash_days': 21,
    },
    {
        'type': 'dm_registry',
        'name': 'DM Registry Cleanup',
        'description': 'E11/E10 + A1C >8 or not checked 6+ months — A1C + UACR + retinal',
        'criteria': {'dx_prefix': ['E11', 'E10'], 'lab_gap': 'A1C', 'gap_months': 6},
        'time_to_cash_days': 30,
    },
    {
        'type': 'immunization_catchup',
        'name': 'Immunization Catch-Up',
        'description': 'Incomplete series or overdue annuals',
        'criteria': {'series_incomplete': True},
        'time_to_cash_days': 7,
    },
    {
        'type': 'tobacco_cessation',
        'name': 'Tobacco Cessation Push',
        'description': 'F17.210 (106 enc) — 99406/99407 every visit',
        'criteria': {'dx_prefix': ['F17']},
        'time_to_cash_days': 7,
    },
    {
        'type': 'bh_screening',
        'name': 'BH Screening Catch-Up',
        'description': 'Seen in 12 months without 96127',
        'criteria': {'dx_prefix': ['F41', 'F32', 'F43', 'F90'], 'missing_cpt': '96127'},
        'time_to_cash_days': 7,
    },
    {
        'type': 'quarter_end_fastcash',
        'name': 'Quarter-End Fast-Cash',
        'description': 'High-certainty quick-revenue in final 30 days',
        'criteria': {'confidence': 'HIGH', 'days_to_quarter_end': 30},
        'time_to_cash_days': 7,
    },
]


@campaigns_bp.route('/campaigns')
@login_required
def campaigns_list():
    """Campaign dashboard with active, planned, and completed campaigns."""
    uid = current_user.id
    campaigns = (
        BillingCampaign.query
        .filter_by(user_id=uid)
        .order_by(BillingCampaign.status.asc(), BillingCampaign.priority_score.desc())
        .all()
    )

    return render_template(
        'campaigns.html',
        campaigns=campaigns,
        templates=CAMPAIGN_TEMPLATES,
    )


@campaigns_bp.route('/api/campaigns', methods=['POST'])
@login_required
def create_campaign():
    """Create a new campaign from a template or custom criteria."""
    data = request.get_json(silent=True) or {}
    name = data.get('campaign_name', '').strip()
    ctype = data.get('campaign_type', '').strip()
    if not name or not ctype:
        return jsonify({"error": "campaign_name and campaign_type are required"}), 400

    today = date.today()
    quarter_end_month = ((today.month - 1) // 3 + 1) * 3
    quarter_end = date(today.year, quarter_end_month, 28)

    criteria = data.get('target_criteria', {})

    campaign = BillingCampaign(
        user_id=current_user.id,
        campaign_name=name,
        campaign_type=ctype,
        start_date=today,
        end_date=data.get('end_date') or quarter_end,
        target_criteria=json.dumps(criteria),
        target_patient_count=min(int(data.get('target_patient_count', 0) or 0), 100000),
        estimated_revenue=min(float(data.get('estimated_revenue', 0) or 0), 10000000),
        status='active',
        created_by=current_user.display_name if hasattr(current_user, 'display_name') else str(current_user.id),
        priority_score=data.get('priority_score', 0),
        time_to_cash_days=data.get('time_to_cash_days', 30),
    )
    db.session.add(campaign)
    db.session.commit()
    return jsonify({"status": "ok", "id": campaign.id}), 201


@campaigns_bp.route('/api/campaigns/<int:campaign_id>/update', methods=['POST'])
@login_required
def update_campaign(campaign_id):
    """Update campaign progress or status."""
    campaign = BillingCampaign.query.filter_by(
        id=campaign_id, user_id=current_user.id,
    ).first_or_404()

    data = request.get_json(silent=True) or {}
    if 'completed_count' in data:
        campaign.completed_count = data['completed_count']
    if 'actual_revenue' in data:
        campaign.actual_revenue = data['actual_revenue']
    if 'status' in data and data['status'] in ('planned', 'active', 'completed', 'paused'):
        campaign.status = data['status']

    db.session.commit()
    return jsonify({"status": "ok"})


# ============================================================
# 27.4 — Ranking by expected net value × time-to-cash
# ============================================================

@campaigns_bp.route('/api/campaigns/ranked')
@login_required
def ranked_campaigns():
    """Return campaigns ranked by (estimated_revenue / time_to_cash_days)."""
    uid = current_user.id
    campaigns = (
        BillingCampaign.query
        .filter_by(user_id=uid, status='active')
        .all()
    )

    ranked = sorted(campaigns, key=lambda c: (
        (c.estimated_revenue or 0) / max(c.time_to_cash_days or 30, 1)
    ), reverse=True)

    return jsonify([
        {
            'id': c.id,
            'name': c.campaign_name,
            'type': c.campaign_type,
            'estimated_revenue': c.estimated_revenue,
            'time_to_cash_days': c.time_to_cash_days,
            'daily_value': round((c.estimated_revenue or 0) / max(c.time_to_cash_days or 30, 1), 2),
            'completion_pct': c.completion_pct(),
            'status': c.status,
        }
        for c in ranked
    ])


# ============================================================
# 27.5 — Admin Billing ROI Dashboard
# ============================================================

@campaigns_bp.route('/admin/billing-roi')
@login_required
@require_role('admin')
def admin_billing_roi():
    """Admin ROI dashboard: revenue projections, leakage, bottlenecks."""
    uid = current_user.id

    # Quarterly revenue by feature family
    today = date.today()
    quarter_start_month = ((today.month - 1) // 3) * 3 + 1
    quarter_start = date(today.year, quarter_start_month, 1)

    opps = (
        BillingOpportunity.query
        .filter(
            BillingOpportunity.user_id == uid,
            BillingOpportunity.visit_date >= quarter_start,
        )
        .all()
    )

    # Feature family rollups
    families = defaultdict(lambda: {'detected': 0, 'captured': 0, 'rev': 0.0})
    for o in opps:
        cat = o.opportunity_type or 'unknown'
        families[cat]['detected'] += 1
        if o.status == 'captured':
            families[cat]['captured'] += 1
            families[cat]['rev'] += o.expected_net_dollars or o.estimated_revenue or 0

    family_list = sorted(families.items(), key=lambda x: x[1]['rev'], reverse=True)

    # Top 5 leakage families (by missed rev)
    leakage_families = []
    for cat, data in family_list:
        detected_rev = sum(
            o.expected_net_dollars or o.estimated_revenue or 0
            for o in opps if (o.opportunity_type or 'unknown') == cat
        )
        captured_rev = data['rev']
        gap = detected_rev - captured_rev
        if gap > 0:
            leakage_families.append({'category': cat, 'gap': round(gap, 2)})
    leakage_families.sort(key=lambda x: x['gap'], reverse=True)
    leakage_families = leakage_families[:5]

    # Top 3 workflow bottlenecks from ClosedLoopStatus
    opp_ids = [o.id for o in opps]
    bottleneck_counts = defaultdict(int)
    if opp_ids:
        dismissed = (
            ClosedLoopStatus.query
            .filter(
                ClosedLoopStatus.opportunity_id.in_(opp_ids),
                ClosedLoopStatus.funnel_stage.in_(['dismissed', 'denied']),
            )
            .all()
        )
        for row in dismissed:
            notes = (row.stage_notes or '').lower()
            if 'workflow' in notes or 'missed' in notes:
                bottleneck_counts['Workflow Drop'] += 1
            elif 'document' in notes or 'note' in notes:
                bottleneck_counts['Documentation Gap'] += 1
            elif 'staff' in notes or 'bottleneck' in notes:
                bottleneck_counts['Staff Bottleneck'] += 1
            elif 'time' in notes or 'busy' in notes:
                bottleneck_counts['Time Constraint'] += 1
            else:
                bottleneck_counts['Other'] += 1

    top_bottlenecks = sorted(bottleneck_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    # Bonus projection
    bonus_proj = None
    try:
        from models.bonus import BonusTracker
        tracker = BonusTracker.query.filter_by(user_id=uid).first()
        if tracker:
            bonus_proj = {
                'threshold': tracker.quarterly_threshold or 105000,
                'projected_first_bonus_quarter': tracker.projected_first_bonus_quarter,
            }
    except Exception:
        pass

    # Active campaigns
    campaigns = BillingCampaign.query.filter_by(user_id=uid).all()

    return render_template(
        'admin_billing_roi.html',
        family_list=family_list,
        leakage_families=leakage_families,
        top_bottlenecks=top_bottlenecks,
        bonus_proj=bonus_proj,
        campaigns=campaigns,
        quarter_label=f"Q{(today.month - 1) // 3 + 1} {today.year}",
    )

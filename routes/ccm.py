"""
CareCompanion — CCM Registry Routes
File: routes/ccm.py
Phase 19.11

Chronic Care Management (CCM) enrollment, time logging, and billing roster.
$62/month per enrolled patient — highest recurring revenue opportunity.
"""

import json
import logging
from datetime import date, datetime

from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user

from models import db
from models.ccm import CCMEnrollment, CCMTimeEntry

logger = logging.getLogger(__name__)

ccm_bp = Blueprint('ccm', __name__)


@ccm_bp.route('/ccm/registry')
@login_required
def ccm_registry():
    """CCM enrollment registry with time tracking and billing readiness."""
    today = date.today()
    current_month = today.strftime('%Y-%m')
    current_year = today.year
    current_month_num = today.month

    enrollments = CCMEnrollment.query.filter_by(
        user_id=current_user.id,
    ).order_by(CCMEnrollment.status.asc(), CCMEnrollment.enrollment_date.desc()).all()

    registry = []
    for e in enrollments:
        minutes = e.monthly_minutes(current_year, current_month_num)
        goal = e.monthly_time_goal or 20
        pct = min(round(minutes / goal * 100), 100) if goal else 0

        # Billing readiness
        if e.status != 'active':
            readiness = 'gray'
            readiness_label = e.status.title()
        elif not e.consent_date:
            readiness = 'red'
            readiness_label = 'Needs Consent'
        elif not e.care_plan_date:
            readiness = 'red'
            readiness_label = 'Needs Care Plan'
        elif len(e.get_qualifying_conditions()) < 2:
            readiness = 'red'
            readiness_label = 'Need 2+ Conditions'
        elif minutes < goal:
            readiness = 'yellow'
            readiness_label = f'{minutes}/{goal} min'
        elif e.last_billed_month == current_month:
            readiness = 'gray'
            readiness_label = 'Billed This Month'
        else:
            readiness = 'green'
            readiness_label = 'Ready to Bill'

        registry.append({
            'enrollment': e,
            'minutes': minutes,
            'goal': goal,
            'pct': pct,
            'readiness': readiness,
            'readiness_label': readiness_label,
            'conditions': e.get_qualifying_conditions(),
        })

    return render_template(
        'ccm_registry.html',
        registry=registry,
        today=today,
        current_month=current_month,
    )


@ccm_bp.route('/ccm/enroll', methods=['POST'])
@login_required
def ccm_enroll():
    """Enroll a patient in CCM."""
    import re as _re
    from utils import safe_patient_id

    mrn = (request.form.get('mrn') or '').strip()
    if not mrn or not _re.match(r'^[A-Za-z0-9\-]{1,20}$', mrn):
        return jsonify({'error': 'Invalid MRN'}), 400

    try:
        mrn_hash = safe_patient_id(mrn)
    except ValueError:
        return jsonify({'error': 'Invalid MRN'}), 400

    consent_method = (request.form.get('consent_method') or '').strip()
    if consent_method and consent_method not in ('verbal', 'written', 'portal'):
        consent_method = 'verbal'

    conditions_raw = request.form.get('conditions', '[]')
    try:
        conditions = json.loads(conditions_raw)
        if not isinstance(conditions, list):
            conditions = []
    except (json.JSONDecodeError, TypeError):
        conditions = []

    # Check for existing active enrollment
    existing = CCMEnrollment.query.filter_by(
        patient_mrn_hash=mrn_hash,
        user_id=current_user.id,
        status='active',
    ).first()
    if existing:
        return jsonify({'error': 'Patient already enrolled in CCM'}), 409

    enrollment = CCMEnrollment(
        patient_mrn_hash=mrn_hash,
        user_id=current_user.id,
        enrollment_date=date.today(),
        consent_date=date.today() if consent_method else None,
        consent_method=consent_method or None,
        status='active' if consent_method else 'pending',
    )
    enrollment.set_qualifying_conditions(conditions)

    db.session.add(enrollment)
    db.session.commit()

    return jsonify({'success': True, 'id': enrollment.id})


@ccm_bp.route('/ccm/<int:enrollment_id>/log-time', methods=['POST'])
@login_required
def ccm_log_time(enrollment_id):
    """Log CCM time for an enrollment."""
    enrollment = CCMEnrollment.query.filter_by(
        id=enrollment_id, user_id=current_user.id
    ).first()
    if not enrollment:
        return jsonify({'error': 'Enrollment not found'}), 404

    try:
        minutes = int(request.form.get('minutes', 0))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid minutes'}), 400

    if minutes <= 0 or minutes > 120:
        return jsonify({'error': 'Minutes must be 1-120'}), 400

    activity_type = (request.form.get('activity_type') or 'care_coordination').strip()
    allowed_types = (
        'care_coordination', 'care_plan_review', 'medication_mgmt',
        'phone_call', 'portal_message', 'referral_followup',
    )
    if activity_type not in allowed_types:
        activity_type = 'care_coordination'

    staff_name = (request.form.get('staff_name') or '').strip()[:100]
    staff_role = (request.form.get('staff_role') or '').strip()
    if staff_role not in ('provider', 'nurse', 'ma', 'care_coordinator', ''):
        staff_role = ''
    description = (request.form.get('description') or '').strip()[:500]

    entry = CCMTimeEntry(
        enrollment_id=enrollment.id,
        entry_date=date.today(),
        duration_minutes=minutes,
        activity_type=activity_type,
        staff_name=staff_name or None,
        staff_role=staff_role or None,
        activity_description=description or None,
        is_billable=True,
    )
    db.session.add(entry)
    db.session.commit()

    # Return updated total
    today = date.today()
    total = enrollment.monthly_minutes(today.year, today.month)

    return jsonify({
        'success': True,
        'id': entry.id,
        'monthly_total': total,
        'goal': enrollment.monthly_time_goal or 20,
    })


@ccm_bp.route('/ccm/<int:enrollment_id>/monthly-summary')
@login_required
def ccm_monthly_summary(enrollment_id):
    """Get monthly summary for a CCM enrollment."""
    enrollment = CCMEnrollment.query.filter_by(
        id=enrollment_id, user_id=current_user.id
    ).first()
    if not enrollment:
        return jsonify({'error': 'Enrollment not found'}), 404

    today = date.today()
    year = int(request.args.get('year', today.year))
    month = int(request.args.get('month', today.month))

    entries = CCMTimeEntry.query.filter(
        CCMTimeEntry.enrollment_id == enrollment.id,
        db.extract('year', CCMTimeEntry.entry_date) == year,
        db.extract('month', CCMTimeEntry.entry_date) == month,
    ).order_by(CCMTimeEntry.entry_date.desc()).all()

    total = sum(e.duration_minutes for e in entries if e.is_billable)
    goal = enrollment.monthly_time_goal or 20

    return jsonify({
        'enrollment_id': enrollment.id,
        'month': f'{year}-{month:02d}',
        'total_minutes': total,
        'goal': goal,
        'threshold_met': total >= goal,
        'entries': [{
            'id': e.id,
            'date': e.entry_date.isoformat() if e.entry_date else None,
            'minutes': e.duration_minutes,
            'activity': e.activity_type,
            'staff': e.staff_name,
            'role': e.staff_role,
            'description': e.activity_description,
            'billable': e.is_billable,
        } for e in entries],
    })


@ccm_bp.route('/ccm/billing-roster')
@login_required
def ccm_billing_roster():
    """Monthly billing roster: enrollments that have met the 20-min threshold."""
    today = date.today()
    current_month = today.strftime('%Y-%m')

    enrollments = CCMEnrollment.query.filter_by(
        user_id=current_user.id,
        status='active',
    ).all()

    roster = []
    for e in enrollments:
        minutes = e.monthly_minutes(today.year, today.month)
        goal = e.monthly_time_goal or 20
        if minutes >= goal and e.last_billed_month != current_month:
            roster.append({
                'enrollment_id': e.id,
                'patient_mrn_hash': e.patient_mrn_hash,
                'minutes': minutes,
                'goal': goal,
                'conditions': e.get_qualifying_conditions(),
                'consent_date': e.consent_date.isoformat() if e.consent_date else None,
                'already_billed': e.last_billed_month == current_month,
            })

    return jsonify({
        'month': current_month,
        'roster': roster,
        'count': len(roster),
        'estimated_revenue': len(roster) * 62,
    })


@ccm_bp.route('/ccm/<int:enrollment_id>/disenroll', methods=['POST'])
@login_required
def ccm_disenroll(enrollment_id):
    """Disenroll a patient from CCM."""
    enrollment = CCMEnrollment.query.filter_by(
        id=enrollment_id, user_id=current_user.id
    ).first()
    if not enrollment:
        return jsonify({'error': 'Enrollment not found'}), 404

    reason = (request.form.get('reason') or '').strip()[:200]
    enrollment.status = 'disenrolled'
    db.session.commit()

    return jsonify({'success': True})


@ccm_bp.route('/api/patient/<patient_mrn_hash>/ccm-status')
@login_required
def ccm_patient_status(patient_mrn_hash):
    """Return CCM enrollment status for a specific patient (sidebar widget)."""
    enrollment = CCMEnrollment.query.filter_by(
        patient_mrn_hash=patient_mrn_hash, user_id=current_user.id
    ).filter(CCMEnrollment.status.in_(['active', 'pending'])).first()

    if not enrollment:
        return jsonify({'enrolled': False})

    today = date.today()
    minutes = enrollment.monthly_minutes(today.year, today.month)
    goal = enrollment.monthly_time_goal or 20
    ready = enrollment.is_billing_ready(today.strftime('%Y-%m'))

    return jsonify({
        'enrolled': True,
        'status': enrollment.status,
        'enrollment_id': enrollment.id,
        'consent': bool(enrollment.consent_date),
        'care_plan': bool(enrollment.care_plan_date),
        'conditions': enrollment.get_qualifying_conditions(),
        'minutes': minutes,
        'goal': goal,
        'pct': min(round(minutes / goal * 100), 100) if goal else 0,
        'billing_ready': ready,
        'monthly_revenue': 62 if ready else 0,
    })

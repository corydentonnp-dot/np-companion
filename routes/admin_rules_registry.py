"""
CareCompanion — Admin Rules Registry
File: routes/admin_rules_registry.py

Unified view of ALL monitoring rules and care gap rules in flat,
searchable/filterable tables.  Includes trigger-test endpoints so
admins can verify a rule fires against a synthetic patient profile.

All routes require @login_required + @require_role('admin').
"""

import json
import logging
from datetime import datetime, timezone, date, timedelta

from flask import (
    Blueprint, current_app, jsonify, render_template, request,
)
from flask_login import current_user, login_required

from models import db
from models.monitoring import MonitoringRule, MonitoringSchedule
from models.caregap import CareGapRule
from routes.auth import require_role

logger = logging.getLogger(__name__)

admin_rules_registry_bp = Blueprint(
    'admin_rules_registry', __name__, url_prefix='/admin/rules-registry'
)


# ══════════════════════════════════════════════════════════════════
# Page route
# ══════════════════════════════════════════════════════════════════

@admin_rules_registry_bp.route('/')
@login_required
@require_role('admin')
def index():
    """Unified rules registry page."""
    return render_template('admin_rules_registry.html')


# ══════════════════════════════════════════════════════════════════
# API — Summary stats
# ══════════════════════════════════════════════════════════════════

@admin_rules_registry_bp.route('/api/stats')
@login_required
@require_role('admin')
def api_stats():
    """Return aggregate counts for both rule systems."""
    try:
        # Monitoring rules
        mon_total = MonitoringRule.query.count()
        mon_active = MonitoringRule.query.filter_by(is_active=True).count()
        mon_inactive = mon_total - mon_active

        # Monitoring by trigger type
        mon_by_type = {}
        for row in (
            db.session.query(
                MonitoringRule.trigger_type,
                db.func.count(MonitoringRule.id)
            )
            .filter(MonitoringRule.is_active == True)
            .group_by(MonitoringRule.trigger_type)
            .all()
        ):
            mon_by_type[row[0]] = row[1]

        # Monitoring by source
        mon_by_source = {}
        for row in (
            db.session.query(
                MonitoringRule.source,
                db.func.count(MonitoringRule.id)
            )
            .filter(MonitoringRule.is_active == True)
            .group_by(MonitoringRule.source)
            .all()
        ):
            mon_by_source[row[0]] = row[1]

        # Monitoring by priority
        mon_by_priority = {}
        for row in (
            db.session.query(
                MonitoringRule.priority,
                db.func.count(MonitoringRule.id)
            )
            .filter(MonitoringRule.is_active == True)
            .group_by(MonitoringRule.priority)
            .all()
        ):
            mon_by_priority[row[0]] = row[1]

        # Care gap rules
        cg_total = CareGapRule.query.count()
        cg_active = CareGapRule.query.filter_by(is_active=True).count()
        cg_inactive = cg_total - cg_active

        # Active schedules count
        sched_active = MonitoringSchedule.query.filter_by(status='active').count()

        return jsonify({
            'success': True,
            'data': {
                'monitoring': {
                    'total': mon_total,
                    'active': mon_active,
                    'inactive': mon_inactive,
                    'by_type': mon_by_type,
                    'by_source': mon_by_source,
                    'by_priority': mon_by_priority,
                },
                'care_gaps': {
                    'total': cg_total,
                    'active': cg_active,
                    'inactive': cg_inactive,
                },
                'active_schedules': sched_active,
            },
            'error': None,
        })
    except Exception as e:
        current_app.logger.error(f"Error in rules_registry.api_stats: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Failed to load stats'}), 500


# ══════════════════════════════════════════════════════════════════
# API — Monitoring rules list
# ══════════════════════════════════════════════════════════════════

@admin_rules_registry_bp.route('/api/monitoring-rules')
@login_required
@require_role('admin')
def api_monitoring_rules():
    """Return all monitoring rules with filtering/sorting."""
    try:
        q = MonitoringRule.query

        # Filters
        search = request.args.get('search', '').strip()
        if search:
            pattern = f'%{search}%'
            q = q.filter(
                db.or_(
                    MonitoringRule.lab_name.ilike(pattern),
                    MonitoringRule.rxcui.ilike(pattern),
                    MonitoringRule.icd10_trigger.ilike(pattern),
                    MonitoringRule.clinical_context.ilike(pattern),
                )
            )

        trigger_type = request.args.get('trigger_type', '')
        if trigger_type:
            q = q.filter(MonitoringRule.trigger_type == trigger_type)

        source = request.args.get('source', '')
        if source:
            q = q.filter(MonitoringRule.source == source)

        priority = request.args.get('priority', '')
        if priority:
            q = q.filter(MonitoringRule.priority == priority)

        active = request.args.get('active', '')
        if active == 'true':
            q = q.filter(MonitoringRule.is_active == True)
        elif active == 'false':
            q = q.filter(MonitoringRule.is_active == False)

        # Sort
        sort = request.args.get('sort', 'lab_name')
        desc = request.args.get('desc', 'false') == 'true'
        sort_map = {
            'lab_name': MonitoringRule.lab_name,
            'trigger_type': MonitoringRule.trigger_type,
            'interval_days': MonitoringRule.interval_days,
            'priority': MonitoringRule.priority,
            'source': MonitoringRule.source,
        }
        col = sort_map.get(sort, MonitoringRule.lab_name)
        q = q.order_by(col.desc() if desc else col.asc())

        rules = q.all()

        data = []
        for r in rules:
            # Build trigger display
            trigger = r.icd10_trigger or r.rxcui or r.rxclass_id or '—'
            data.append({
                'id': r.id,
                'lab_name': r.lab_name,
                'lab_loinc_code': r.lab_loinc_code,
                'lab_cpt_code': r.lab_cpt_code,
                'trigger': trigger,
                'trigger_type': r.trigger_type,
                'source': r.source,
                'interval_days': r.interval_days,
                'priority': r.priority,
                'is_active': r.is_active,
                'clinical_context': r.clinical_context or '',
                'evidence_url': r.evidence_source_url or '',
                'confidence': r.extraction_confidence,
                'schedule_count': len(r.schedules) if r.schedules else 0,
            })

        return jsonify({
            'success': True,
            'data': data,
            'total': len(data),
            'error': None,
        })
    except Exception as e:
        current_app.logger.error(f"Error in rules_registry.api_monitoring_rules: {str(e)}")
        return jsonify({'success': False, 'data': [], 'error': 'Failed to load rules'}), 500


# ══════════════════════════════════════════════════════════════════
# API — Care gap rules list
# ══════════════════════════════════════════════════════════════════

@admin_rules_registry_bp.route('/api/caregap-rules')
@login_required
@require_role('admin')
def api_caregap_rules():
    """Return all care gap rules with filtering."""
    try:
        q = CareGapRule.query

        search = request.args.get('search', '').strip()
        if search:
            pattern = f'%{search}%'
            q = q.filter(
                db.or_(
                    CareGapRule.gap_name.ilike(pattern),
                    CareGapRule.gap_type.ilike(pattern),
                    CareGapRule.description.ilike(pattern),
                )
            )

        active = request.args.get('active', '')
        if active == 'true':
            q = q.filter(CareGapRule.is_active == True)
        elif active == 'false':
            q = q.filter(CareGapRule.is_active == False)

        rules = q.order_by(CareGapRule.gap_name.asc()).all()

        data = []
        for r in rules:
            criteria = {}
            try:
                criteria = json.loads(r.criteria_json or '{}')
            except (json.JSONDecodeError, TypeError):
                pass

            data.append({
                'id': r.id,
                'gap_type': r.gap_type,
                'gap_name': r.gap_name,
                'description': r.description or '',
                'interval_days': r.interval_days,
                'billing_code_pair': r.billing_code_pair or '',
                'source': r.source or 'hardcoded',
                'is_active': r.is_active,
                'min_age': criteria.get('min_age', 0),
                'max_age': criteria.get('max_age', 999),
                'sex': criteria.get('sex', 'all'),
                'risk_factors': criteria.get('risk_factors', []),
            })

        return jsonify({
            'success': True,
            'data': data,
            'total': len(data),
            'error': None,
        })
    except Exception as e:
        current_app.logger.error(f"Error in rules_registry.api_caregap_rules: {str(e)}")
        return jsonify({'success': False, 'data': [], 'error': 'Failed to load care gap rules'}), 500


# ══════════════════════════════════════════════════════════════════
# API — Test monitoring rule trigger
# ══════════════════════════════════════════════════════════════════

@admin_rules_registry_bp.route('/api/test-monitoring-rule/<int:rule_id>', methods=['POST'])
@login_required
@require_role('admin')
def api_test_monitoring_rule(rule_id):
    """
    Test a monitoring rule against a synthetic patient profile.
    Accepts JSON body:
      {
        "medications": [{"drug_name": "metformin", "rxcui": "6809"}],
        "diagnoses": [{"icd10_code": "E11"}],
        "age": 55, "sex": "F",
        "last_lab_date": "2025-06-15"   (optional)
      }
    Returns whether the rule would fire and the resulting schedule.
    """
    try:
        rule = MonitoringRule.query.get(rule_id)
        if not rule:
            return jsonify({'success': False, 'data': None, 'error': 'Rule not found'}), 404

        body = request.get_json(silent=True) or {}
        medications = body.get('medications', [])
        diagnoses = body.get('diagnoses', [])
        age = body.get('age', 55)
        sex = body.get('sex', 'F')
        last_lab_date = body.get('last_lab_date', '')

        # Determine if rule would match
        matched = False
        match_reason = ''

        if rule.trigger_type == 'MEDICATION':
            for med in medications:
                if med.get('rxcui') == rule.rxcui:
                    matched = True
                    match_reason = f"Medication match: rxcui {rule.rxcui}"
                    break
        elif rule.trigger_type == 'CONDITION':
            for dx in diagnoses:
                icd = dx.get('icd10_code', '')
                if icd and rule.icd10_trigger and icd.startswith(rule.icd10_trigger):
                    matched = True
                    match_reason = f"Diagnosis match: {icd} → {rule.icd10_trigger}"
                    break
        elif rule.trigger_type == 'GENOTYPE':
            # Genotype rules fire on matching rxcui (pre-treatment)
            for med in medications:
                if med.get('rxcui') == rule.rxcui:
                    matched = True
                    match_reason = f"Pre-treatment genotype match: rxcui {rule.rxcui}"
                    break
        elif rule.trigger_type == 'REMS':
            for med in medications:
                if med.get('rxcui') == rule.rxcui:
                    matched = True
                    match_reason = f"REMS match: rxcui {rule.rxcui}"
                    break

        # Calculate due date
        due_date = None
        is_overdue = False
        if matched:
            if last_lab_date:
                try:
                    lab_dt = datetime.strptime(last_lab_date, '%Y-%m-%d').date()
                    due_date = lab_dt + timedelta(days=rule.interval_days)
                    is_overdue = due_date <= date.today()
                except ValueError:
                    due_date = date.today()
                    is_overdue = True
            else:
                due_date = date.today()
                is_overdue = True

        return jsonify({
            'success': True,
            'data': {
                'rule_id': rule.id,
                'lab_name': rule.lab_name,
                'matched': matched,
                'match_reason': match_reason,
                'due_date': due_date.isoformat() if due_date else None,
                'is_overdue': is_overdue,
                'interval_days': rule.interval_days,
                'priority': rule.priority,
                'trigger_type': rule.trigger_type,
                'trigger_value': rule.icd10_trigger or rule.rxcui or rule.rxclass_id or '',
            },
            'error': None,
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in rules_registry.api_test_monitoring_rule: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Test failed'}), 500


# ══════════════════════════════════════════════════════════════════
# API — Test care gap rule trigger
# ══════════════════════════════════════════════════════════════════

@admin_rules_registry_bp.route('/api/test-caregap-rule/<int:rule_id>', methods=['POST'])
@login_required
@require_role('admin')
def api_test_caregap_rule(rule_id):
    """
    Test a care gap rule against a synthetic patient profile.
    Accepts JSON body:
      { "age": 55, "sex": "F", "diagnoses": ["E11", "I10"] }
    Returns whether the rule would fire for this patient.
    """
    try:
        rule = CareGapRule.query.get(rule_id)
        if not rule:
            return jsonify({'success': False, 'data': None, 'error': 'Rule not found'}), 404

        body = request.get_json(silent=True) or {}
        age = body.get('age', 55)
        sex = body.get('sex', 'F')
        diagnoses = body.get('diagnoses', [])

        criteria = {}
        try:
            criteria = json.loads(rule.criteria_json or '{}')
        except (json.JSONDecodeError, TypeError):
            pass

        # Evaluate criteria
        reasons = []
        passed = True

        # Age bounds
        min_age = criteria.get('min_age', 0)
        max_age = criteria.get('max_age', 999)
        age_ok = min_age <= age <= max_age
        if age_ok:
            reasons.append(f'Age {age} is within {min_age}–{max_age} ✓')
        else:
            reasons.append(f'Age {age} outside range {min_age}–{max_age} ✗')
            passed = False

        # Sex match
        criteria_sex = criteria.get('sex', 'all')
        sex_norm = sex.upper()[:1] if sex else ''
        if criteria_sex == 'all':
            reasons.append(f'Sex: any sex qualifies ✓')
        elif criteria_sex in ('female', 'F') and sex_norm == 'F':
            reasons.append(f'Sex: female required, patient is female ✓')
        elif criteria_sex in ('male', 'M') and sex_norm == 'M':
            reasons.append(f'Sex: male required, patient is male ✓')
        else:
            reasons.append(f'Sex: requires {criteria_sex}, patient is {sex} ✗')
            passed = False

        # Risk factors
        risk_factors = criteria.get('risk_factors', [])
        if risk_factors:
            matched_risks = [rf for rf in risk_factors if rf in diagnoses]
            if matched_risks:
                reasons.append(f'Risk factors matched: {", ".join(matched_risks)} ✓')
            else:
                reasons.append(f'Risk factors required: {", ".join(risk_factors)}, none matched ✗')
                passed = False
        else:
            reasons.append('No risk factors required ✓')

        return jsonify({
            'success': True,
            'data': {
                'rule_id': rule.id,
                'gap_name': rule.gap_name,
                'matched': passed,
                'reasons': reasons,
                'interval_days': rule.interval_days,
                'billing_code': rule.billing_code_pair or '',
            },
            'error': None,
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in rules_registry.api_test_caregap_rule: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Test failed'}), 500


# ══════════════════════════════════════════════════════════════════
# API — Toggle rule active/inactive
# ══════════════════════════════════════════════════════════════════

@admin_rules_registry_bp.route('/api/toggle-monitoring-rule/<int:rule_id>', methods=['POST'])
@login_required
@require_role('admin')
def api_toggle_monitoring_rule(rule_id):
    """Toggle is_active on a monitoring rule."""
    try:
        rule = MonitoringRule.query.get(rule_id)
        if not rule:
            return jsonify({'success': False, 'data': None, 'error': 'Rule not found'}), 404
        rule.is_active = not rule.is_active
        db.session.commit()
        return jsonify({
            'success': True,
            'data': {'id': rule.id, 'is_active': rule.is_active},
            'error': None,
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in rules_registry.toggle_monitoring: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Toggle failed'}), 500


@admin_rules_registry_bp.route('/api/toggle-caregap-rule/<int:rule_id>', methods=['POST'])
@login_required
@require_role('admin')
def api_toggle_caregap_rule(rule_id):
    """Toggle is_active on a care gap rule."""
    try:
        rule = CareGapRule.query.get(rule_id)
        if not rule:
            return jsonify({'success': False, 'data': None, 'error': 'Rule not found'}), 404
        rule.is_active = not rule.is_active
        db.session.commit()
        return jsonify({
            'success': True,
            'data': {'id': rule.id, 'is_active': rule.is_active},
            'error': None,
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in rules_registry.toggle_caregap: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Toggle failed'}), 500

"""
CareCompanion — Admin Med Catalog Routes
File: routes/admin_med_catalog.py

Phase MM-3: Admin blueprint for the Medication Control Panel,
Med Explorer, Coverage Queue, Testing, and Drift Viewer.

All routes require @login_required + @require_role('admin').
"""

import json
import logging
from datetime import datetime, timezone

from flask import (
    Blueprint, current_app, jsonify, render_template, request,
)
from flask_login import current_user, login_required

from models import db
from models.monitoring import (
    MedicationCatalogEntry, MonitoringRule, MonitoringRuleOverride,
    MonitoringEvaluationLog, MonitoringRuleTestResult, MonitoringRuleDiff,
    MonitoringSchedule,
)
from routes.auth import require_role

logger = logging.getLogger(__name__)

admin_med_catalog_bp = Blueprint(
    'admin_med_catalog', __name__, url_prefix='/admin/med-catalog'
)


# ══════════════════════════════════════════════════════════════════
# Page routes — render templates
# ══════════════════════════════════════════════════════════════════

@admin_med_catalog_bp.route('/')
@login_required
@require_role('admin')
def index():
    """Master medication catalog page."""
    return render_template('admin_med_catalog.html')


@admin_med_catalog_bp.route('/explorer')
@login_required
@require_role('admin')
def explorer():
    """Med lookup explorer page."""
    return render_template('admin_med_explorer.html')


@admin_med_catalog_bp.route('/coverage')
@login_required
@require_role('admin')
def coverage():
    """Coverage queue and dashboard page."""
    return render_template('admin_med_coverage.html')


@admin_med_catalog_bp.route('/testing')
@login_required
@require_role('admin')
def testing():
    """Bulk test runner page."""
    return render_template('admin_med_testing.html')


@admin_med_catalog_bp.route('/diffs')
@login_required
@require_role('admin')
def diffs():
    """Parser drift viewer page."""
    return render_template('admin_med_diffs.html')


# ══════════════════════════════════════════════════════════════════
# API routes — JSON endpoints
# ══════════════════════════════════════════════════════════════════

# ── Catalog list / stats ──────────────────────────────────────────

@admin_med_catalog_bp.route('/api/list')
@login_required
@require_role('admin')
def api_list():
    """Paginated catalog entries for AJAX table."""
    try:
        from app.services.med_catalog_service import MedCatalogService
        svc = MedCatalogService()

        filters = {
            'status': request.args.get('status', ''),
            'source': request.args.get('source', ''),
            'drug_class': request.args.get('drug_class', ''),
            'search': request.args.get('search', ''),
            'low_confidence': request.args.get('low_confidence') == '1',
        }
        sort = request.args.get('sort', 'display_name')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 200)

        result = svc.get_catalog_page(filters, sort, page, per_page)

        # Serialize items
        items = []
        for entry in result['items']:
            # Get matching rule count
            rule_count = 0
            if entry.rxcui:
                rule_count = MonitoringRule.query.filter_by(
                    rxcui=entry.rxcui, is_active=True
                ).count()

            # Get override count
            override_count = 0
            if entry.rxcui:
                rule_ids = [
                    r.id for r in MonitoringRule.query.filter_by(
                        rxcui=entry.rxcui, is_active=True
                    ).all()
                ]
                if rule_ids:
                    override_count = MonitoringRuleOverride.query.filter(
                        MonitoringRuleOverride.monitoring_rule_id.in_(rule_ids),
                        MonitoringRuleOverride.override_active == True,
                    ).count()

            items.append({
                'id': entry.id,
                'display_name': entry.display_name,
                'normalized_name': entry.normalized_name,
                'rxcui': entry.rxcui,
                'ingredient_name': entry.ingredient_name,
                'drug_class': entry.drug_class,
                'source_origin': entry.source_origin,
                'source_confidence': entry.source_confidence,
                'status': entry.status,
                'local_patient_count': entry.local_patient_count,
                'rule_count': rule_count,
                'override_count': override_count,
                'last_refreshed_at': entry.last_refreshed_at.isoformat() if entry.last_refreshed_at else None,
                'last_tested_at': entry.last_tested_at.isoformat() if entry.last_tested_at else None,
                'is_active': entry.is_active,
            })

        return jsonify({
            'success': True,
            'data': {
                'items': items,
                'total': result['total'],
                'page': result['page'],
                'per_page': result['per_page'],
                'pages': result['pages'],
            },
            'error': None,
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_med_catalog.api_list: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Failed to load catalog'}), 500


@admin_med_catalog_bp.route('/api/stats')
@login_required
@require_role('admin')
def api_stats():
    """Catalog statistics for dashboard."""
    try:
        from app.services.med_catalog_service import MedCatalogService
        svc = MedCatalogService()
        stats = svc.get_catalog_stats()
        return jsonify({'success': True, 'data': stats, 'error': None})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_med_catalog.api_stats: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Failed to load stats'}), 500


# ── Override management ───────────────────────────────────────────

@admin_med_catalog_bp.route('/api/override', methods=['POST'])
@login_required
@require_role('admin')
def api_set_override():
    """Set user or practice override."""
    try:
        from app.services.med_override_service import MedOverrideService
        svc = MedOverrideService()

        data = request.get_json(silent=True) or {}
        rule_id = data.get('monitoring_rule_id')
        scope = data.get('scope', 'user')
        interval = data.get('interval_days')
        reason = data.get('reason', '')

        if not rule_id:
            return jsonify({'success': False, 'data': None, 'error': 'Missing monitoring_rule_id'}), 400

        if interval is not None:
            interval = int(interval)

        if scope == 'practice':
            override = svc.set_practice_override(
                monitoring_rule_id=rule_id,
                interval_days=interval,
                reason=reason,
                created_by=current_user.id,
            )
        else:
            override = svc.set_user_override(
                monitoring_rule_id=rule_id,
                user_id=current_user.id,
                interval_days=interval,
                reason=reason,
            )

        return jsonify({
            'success': True,
            'data': {'override_id': override.id},
            'error': None,
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_med_catalog.api_set_override: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Override failed'}), 500


@admin_med_catalog_bp.route('/api/override/<int:override_id>', methods=['DELETE'])
@login_required
@require_role('admin')
def api_reset_override(override_id):
    """Reset (deactivate) an override."""
    try:
        from app.services.med_override_service import MedOverrideService
        svc = MedOverrideService()
        success = svc.reset_override(override_id)
        if not success:
            return jsonify({'success': False, 'data': None, 'error': 'Override not found'}), 404
        return jsonify({'success': True, 'data': None, 'error': None})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_med_catalog.api_reset_override: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Reset failed'}), 500


@admin_med_catalog_bp.route('/api/bulk-override', methods=['POST'])
@login_required
@require_role('admin')
def api_bulk_override():
    """Class-wide override."""
    try:
        from app.services.med_override_service import MedOverrideService
        svc = MedOverrideService()

        data = request.get_json(silent=True) or {}
        rxclass_id = data.get('rxclass_id')
        interval = data.get('interval_days')
        scope = data.get('scope', 'practice')
        reason = data.get('reason', '')

        if not rxclass_id or interval is None:
            return jsonify({'success': False, 'data': None, 'error': 'Missing rxclass_id or interval_days'}), 400

        count = svc.bulk_set_class_override(
            rxclass_id=rxclass_id,
            interval_days=int(interval),
            scope=scope,
            scope_id=current_user.id if scope == 'user' else None,
            reason=reason,
            created_by=current_user.id,
        )

        return jsonify({
            'success': True,
            'data': {'overrides_applied': count},
            'error': None,
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_med_catalog.api_bulk_override: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Bulk override failed'}), 500


# ── Catalog actions ───────────────────────────────────────────────

@admin_med_catalog_bp.route('/api/refresh/<int:entry_id>', methods=['POST'])
@login_required
@require_role('admin')
def api_refresh_entry(entry_id):
    """Trigger API refresh for a single catalog entry."""
    try:
        from app.services.med_catalog_service import MedCatalogService
        svc = MedCatalogService()
        result = svc.refresh_catalog_entry(entry_id)
        return jsonify({'success': result['success'], 'data': result, 'error': result.get('error')})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_med_catalog.api_refresh_entry: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Refresh failed'}), 500


@admin_med_catalog_bp.route('/api/accept/<int:entry_id>', methods=['POST'])
@login_required
@require_role('admin')
def api_accept_entry(entry_id):
    """Accept a pending_review entry as active."""
    try:
        from app.services.med_coverage_service import MedCoverageService
        svc = MedCoverageService()
        result = svc.accept_suggested_rule(entry_id)
        return jsonify({'success': result['success'], 'data': result, 'error': result.get('error')})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_med_catalog.api_accept_entry: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Accept failed'}), 500


@admin_med_catalog_bp.route('/api/suppress/<int:entry_id>', methods=['POST'])
@login_required
@require_role('admin')
def api_suppress_entry(entry_id):
    """Suppress a medication from generating reminders."""
    try:
        data = request.get_json(silent=True) or {}
        reason = data.get('reason', '')

        from app.services.med_coverage_service import MedCoverageService
        svc = MedCoverageService()
        result = svc.suppress_medication(entry_id, reason)
        return jsonify({'success': result['success'], 'data': result, 'error': result.get('error')})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_med_catalog.api_suppress_entry: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Suppress failed'}), 500


# ── Seeding ───────────────────────────────────────────────────────

@admin_med_catalog_bp.route('/api/seed-common', methods=['POST'])
@login_required
@require_role('admin')
def api_seed_common():
    """One-click seed common PCP medications."""
    try:
        from app.services.med_catalog_service import MedCatalogService
        svc = MedCatalogService()
        count = svc.seed_catalog_common_meds()
        return jsonify({
            'success': True,
            'data': {'seeded': count},
            'error': None,
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_med_catalog.api_seed_common: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Seeding failed'}), 500


@admin_med_catalog_bp.route('/api/seed-local', methods=['POST'])
@login_required
@require_role('admin')
def api_seed_local():
    """One-click import medications from local patient data."""
    try:
        from app.services.med_catalog_service import MedCatalogService
        svc = MedCatalogService()
        count = svc.seed_catalog_from_patients(current_user.id)
        return jsonify({
            'success': True,
            'data': {'imported': count},
            'error': None,
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_med_catalog.api_seed_local: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Import failed'}), 500


# ── Med Explorer ──────────────────────────────────────────────────

@admin_med_catalog_bp.route('/api/explore')
@login_required
@require_role('admin')
def api_explore():
    """Full normalization chain for a drug name."""
    try:
        drug_name = request.args.get('drug_name', '').strip()
        if not drug_name:
            return jsonify({'success': False, 'data': None, 'error': 'Missing drug_name'}), 400

        result = {
            'input': drug_name,
            'normalized': drug_name.lower().strip(),
            'rxnorm': None,
            'classes': [],
            'monitoring_rules': [],
            'catalog_entry': None,
        }

        # RxNorm lookup
        try:
            from app.services.api.rxnorm import RxNormService
            rxnorm = RxNormService()
            info = rxnorm.get_drug_info(drug_name)
            if info:
                result['rxnorm'] = info
        except Exception:
            pass

        # RxClass lookup
        rxcui = result.get('rxnorm', {}).get('rxcui', '') if result.get('rxnorm') else ''
        if rxcui:
            try:
                from app.services.api.rxclass import RxClassService
                rxclass = RxClassService()
                classes = rxclass.get_classes_for_drug(rxcui)
                result['classes'] = classes[:10]  # Limit
            except Exception:
                pass

        # Monitoring rules
        try:
            from app.services.monitoring_rule_engine import MonitoringRuleEngine
            engine = MonitoringRuleEngine()
            rules = engine.get_monitoring_rules(rxcui=rxcui, drug_name=drug_name)
            result['monitoring_rules'] = [
                {
                    'id': r.id,
                    'lab_name': r.lab_name,
                    'lab_loinc_code': r.lab_loinc_code,
                    'interval_days': r.interval_days,
                    'priority': r.priority,
                    'source': r.source,
                    'confidence': r.extraction_confidence,
                }
                for r in rules if isinstance(r, MonitoringRule)
            ]
        except Exception:
            pass

        # Catalog entry
        normalized = drug_name.lower().strip()
        entry = MedicationCatalogEntry.query.filter_by(
            normalized_name=normalized
        ).first()
        if entry:
            result['catalog_entry'] = {
                'id': entry.id,
                'display_name': entry.display_name,
                'status': entry.status,
                'source_origin': entry.source_origin,
                'source_confidence': entry.source_confidence,
                'local_patient_count': entry.local_patient_count,
            }

        return jsonify({'success': True, 'data': result, 'error': None})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_med_catalog.api_explore: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Explore failed'}), 500


# ── Coverage ──────────────────────────────────────────────────────

@admin_med_catalog_bp.route('/api/coverage')
@login_required
@require_role('admin')
def api_coverage():
    """Coverage stats and queue."""
    try:
        from app.services.med_coverage_service import MedCoverageService
        svc = MedCoverageService()

        stats = svc.get_coverage_stats()

        filters = {
            'reason': request.args.get('reason', ''),
            'search': request.args.get('search', ''),
        }
        page = int(request.args.get('page', 1))
        queue = svc.get_coverage_queue(filters, page)

        queue_items = [
            {
                'id': e.id,
                'display_name': e.display_name,
                'rxcui': e.rxcui,
                'status': e.status,
                'source_confidence': e.source_confidence,
                'local_patient_count': e.local_patient_count,
                'drug_class': e.drug_class,
            }
            for e in queue['items']
        ]

        return jsonify({
            'success': True,
            'data': {
                'stats': stats,
                'queue': {
                    'items': queue_items,
                    'total': queue['total'],
                    'page': queue['page'],
                    'pages': queue['pages'],
                },
            },
            'error': None,
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_med_catalog.api_coverage: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Coverage load failed'}), 500


# ── Testing ───────────────────────────────────────────────────────

@admin_med_catalog_bp.route('/api/test/<int:entry_id>', methods=['POST'])
@login_required
@require_role('admin')
def api_test_entry(entry_id):
    """Run test scenarios for a single catalog entry."""
    try:
        from app.services.med_test_service import MedTestService
        svc = MedTestService()
        results = svc.run_scenarios_for_entry(entry_id, tested_by=current_user.id)
        return jsonify({
            'success': True,
            'data': {'results': results},
            'error': None,
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_med_catalog.api_test_entry: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Test failed'}), 500


@admin_med_catalog_bp.route('/api/test-bulk', methods=['POST'])
@login_required
@require_role('admin')
def api_test_bulk():
    """Run all/filtered test scenarios."""
    try:
        from app.services.med_test_service import MedTestService
        svc = MedTestService()

        data = request.get_json(silent=True) or {}
        scope = data.get('scope', 'all')

        results = svc.run_bulk_tests(scope=scope, tested_by=current_user.id)
        return jsonify({
            'success': True,
            'data': results,
            'error': None,
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_med_catalog.api_test_bulk: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Bulk test failed'}), 500


@admin_med_catalog_bp.route('/api/test-results')
@login_required
@require_role('admin')
def api_test_results():
    """Get recent test results for display."""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 200)

        q = MonitoringRuleTestResult.query.order_by(
            MonitoringRuleTestResult.tested_at.desc()
        )

        total = q.count()
        items = q.offset((page - 1) * per_page).limit(per_page).all()

        results = [
            {
                'id': r.id,
                'monitoring_rule_id': r.monitoring_rule_id,
                'catalog_entry_id': r.catalog_entry_id,
                'test_scenario': r.test_scenario,
                'passed': r.passed,
                'explanation': r.explanation,
                'tested_at': r.tested_at.isoformat() if r.tested_at else None,
            }
            for r in items
        ]

        return jsonify({
            'success': True,
            'data': {
                'items': results,
                'total': total,
                'page': page,
                'pages': max(1, (total + per_page - 1) // per_page),
            },
            'error': None,
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_med_catalog.api_test_results: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Load failed'}), 500


# ── Diffs ─────────────────────────────────────────────────────────

@admin_med_catalog_bp.route('/api/diffs')
@login_required
@require_role('admin')
def api_diffs_list():
    """List parser drift diffs."""
    try:
        reviewed_filter = request.args.get('reviewed')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 200)

        q = MonitoringRuleDiff.query.order_by(
            MonitoringRuleDiff.diff_timestamp.desc()
        )
        if reviewed_filter == '0':
            q = q.filter_by(reviewed=False)
        elif reviewed_filter == '1':
            q = q.filter_by(reviewed=True)

        total = q.count()
        items = q.offset((page - 1) * per_page).limit(per_page).all()

        diffs = [
            {
                'id': d.id,
                'rxcui': d.rxcui,
                'drug_name': d.drug_name,
                'diff_type': d.diff_type,
                'before_rules_json': d.before_rules_json,
                'after_rules_json': d.after_rules_json,
                'reviewed': d.reviewed,
                'diff_timestamp': d.diff_timestamp.isoformat() if d.diff_timestamp else None,
            }
            for d in items
        ]

        return jsonify({
            'success': True,
            'data': {
                'items': diffs,
                'total': total,
                'page': page,
                'pages': max(1, (total + per_page - 1) // per_page),
            },
            'error': None,
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_med_catalog.api_diffs_list: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Load failed'}), 500


@admin_med_catalog_bp.route('/api/diffs/<int:diff_id>/acknowledge', methods=['POST'])
@login_required
@require_role('admin')
def api_acknowledge_diff(diff_id):
    """Mark a diff as reviewed."""
    try:
        diff = MonitoringRuleDiff.query.get(diff_id)
        if not diff:
            return jsonify({'success': False, 'data': None, 'error': 'Diff not found'}), 404

        diff.reviewed = True
        diff.reviewed_by = current_user.id
        db.session.commit()

        return jsonify({'success': True, 'data': None, 'error': None})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_med_catalog.api_acknowledge_diff: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Acknowledge failed'}), 500


# ── Explainability ────────────────────────────────────────────────

@admin_med_catalog_bp.route('/api/explain/<int:schedule_id>')
@login_required
@require_role('admin')
def api_explain(schedule_id):
    """
    Explanation JSON for a monitoring schedule entry.
    Shows why this lab is due and the full rule chain.
    """
    try:
        entry = MonitoringSchedule.query.get(schedule_id)
        if not entry:
            return jsonify({'success': False, 'data': None, 'error': 'Schedule entry not found'}), 404

        explanation = {
            'schedule_id': entry.id,
            'lab_name': entry.lab_name,
            'lab_code': entry.lab_code,
            'next_due_date': str(entry.next_due_date) if entry.next_due_date else None,
            'interval_days': entry.interval_days,
            'triggering_medication': entry.triggering_medication,
            'triggering_condition': entry.triggering_condition,
            'last_performed': str(entry.last_performed_date) if entry.last_performed_date else None,
            'source': entry.source,
            'priority': entry.priority,
            'rule': None,
            'override': None,
        }

        # Add rule details
        if entry.monitoring_rule_id:
            rule = MonitoringRule.query.get(entry.monitoring_rule_id)
            if rule:
                explanation['rule'] = {
                    'id': rule.id,
                    'source': rule.source,
                    'confidence': rule.extraction_confidence,
                    'clinical_context': rule.clinical_context,
                    'evidence_url': rule.evidence_source_url,
                    'default_interval': rule.interval_days,
                }

                # Check for overrides
                from app.services.med_override_service import MedOverrideService
                override_svc = MedOverrideService()
                diff = override_svc.get_override_diff(rule.id, current_user.id)
                explanation['override'] = diff

        return jsonify({'success': True, 'data': explanation, 'error': None})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_med_catalog.api_explain: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Explain failed'}), 500

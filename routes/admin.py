"""
CareCompanion — Admin Dashboard & Site Map Routes

File location: carecompanion/routes/admin.py

Provides:
  GET  /admin                — admin dashboard hub (links to all admin tools)
  GET  /admin/sitemap        — developer site map (lists all routes)
  POST /admin/server/restart — restart the Flask server process
"""

import os
import sys
from datetime import date
from flask import (
    Blueprint, render_template, request, jsonify,
    redirect, url_for, flash, current_app,
)
from flask_login import login_required, current_user
from models import db
from models.user import User

admin_bp = Blueprint('admin_hub', __name__)


def _require_admin(f):
    """Inline admin check — returns 403 if the user is not admin."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Admin access required.', 'error')
            return redirect('/dashboard')
        return f(*args, **kwargs)
    return wrapper


# ======================================================================
# GET /admin — Admin Dashboard Hub
# ======================================================================
@admin_bp.route('/admin')
@login_required
@_require_admin
def admin_dashboard():
    """Central admin dashboard with links to all admin tools."""
    user_count = User.query.count()
    active_count = User.query.filter_by(is_active_account=True).count()
    pending_count = User.query.filter_by(is_active_account=False).count()

    return render_template(
        'admin_dashboard.html',
        user_count=user_count,
        active_count=active_count,
        pending_count=pending_count,
    )


# ======================================================================
# GET /admin/practice — Practice-wide analytics (F29)
# ======================================================================
@admin_bp.route('/admin/practice')
@login_required
@_require_admin
def practice_overview():
    """Multi-provider practice analytics dashboard."""
    from models.patient import PatientRecord, PatientDiagnosis
    from models.caregap import CareGap
    from models.labtrack import LabTrack
    from models.tools import ControlledSubstanceEntry, ReferralLetter
    from models.billing import BillingOpportunity

    # Aggregate metrics
    all_providers = User.query.filter_by(is_active_account=True, role='provider').all()
    if not all_providers:
        all_providers = User.query.filter_by(is_active_account=True).all()

    total_patients = PatientRecord.query.count()
    active_providers = len(all_providers)

    all_gaps = CareGap.query.all()
    total_open_gaps = sum(1 for g in all_gaps if not g.is_addressed)
    total_addressed = sum(1 for g in all_gaps if g.is_addressed)
    total_gaps = len(all_gaps)
    gap_compliance_pct = round(total_addressed / total_gaps * 100) if total_gaps > 0 else 100

    overdue_labs = sum(
        1 for lt in LabTrack.query.filter_by(is_archived=False).all()
        if lt.status in ('overdue', 'critical')
    )

    overdue_referrals = ReferralLetter.query.filter_by(
        consultation_received=False
    ).count()
    # Only count those >6 weeks old
    from datetime import timedelta as _td
    cutoff = date.today() - _td(days=42)
    overdue_referrals = ReferralLetter.query.filter(
        ReferralLetter.consultation_received == False,
        ReferralLetter.referral_date.isnot(None),
        ReferralLetter.referral_date <= cutoff,
    ).count()

    # Per-provider stats
    provider_stats = []
    for prov in all_providers:
        panel = PatientRecord.query.filter_by(claimed_by=prov.id).count()
        p_gaps = CareGap.query.filter_by(user_id=prov.id).all()
        p_open = sum(1 for g in p_gaps if not g.is_addressed)
        p_total = len(p_gaps)
        p_compliance = round((p_total - p_open) / p_total * 100) if p_total > 0 else 100

        p_overdue_labs = sum(
            1 for lt in LabTrack.query.filter_by(user_id=prov.id, is_archived=False).all()
            if lt.status in ('overdue', 'critical')
        )

        p_overdue_refs = ReferralLetter.query.filter(
            ReferralLetter.user_id == prov.id,
            ReferralLetter.consultation_received == False,
            ReferralLetter.referral_date.isnot(None),
            ReferralLetter.referral_date <= cutoff,
        ).count()

        p_billing = BillingOpportunity.query.filter_by(
            user_id=prov.id, status='pending'
        ).count()

        p_cs = ControlledSubstanceEntry.query.filter_by(
            user_id=prov.id, is_active=True
        ).count()

        provider_stats.append({
            'name': prov.display_name or prov.username,
            'panel_size': panel,
            'open_gaps': p_open,
            'gap_compliance': p_compliance,
            'overdue_labs': p_overdue_labs,
            'overdue_referrals': p_overdue_refs,
            'billing_pending': p_billing,
            'cs_patients': p_cs,
        })

    # Gap compliance by type
    gap_types = {}
    for g in all_gaps:
        gt = g.gap_type or g.gap_name or 'Unknown'
        if gt not in gap_types:
            gap_types[gt] = {'total': 0, 'addressed': 0, 'open': 0}
        gap_types[gt]['total'] += 1
        if g.is_addressed:
            gap_types[gt]['addressed'] += 1
        else:
            gap_types[gt]['open'] += 1

    gap_by_type = []
    for gt, counts in sorted(gap_types.items()):
        pct = round(counts['addressed'] / counts['total'] * 100) if counts['total'] > 0 else 0
        gap_by_type.append({
            'type': gt,
            'total': counts['total'],
            'addressed': counts['addressed'],
            'open': counts['open'],
            'pct': pct,
        })

    return render_template(
        'admin_practice.html',
        total_patients=total_patients,
        active_providers=active_providers,
        total_open_gaps=total_open_gaps,
        gap_compliance_pct=gap_compliance_pct,
        overdue_labs=overdue_labs,
        overdue_referrals=overdue_referrals,
        provider_stats=provider_stats,
        gap_by_type=gap_by_type,
    )


# ======================================================================
# GET /admin/sitemap — Developer Site Map
# ======================================================================
@admin_bp.route('/admin/sitemap')
@login_required
@_require_admin
def admin_sitemap():
    """
    Lists all registered routes in the app, grouped by blueprint.
    Useful for developers to see what pages exist and their URLs.
    """
    routes_by_blueprint = {}

    for rule in current_app.url_map.iter_rules():
        # Skip static file rule
        if rule.endpoint == 'static':
            continue

        bp_name = rule.endpoint.rsplit('.', 1)[0] if '.' in rule.endpoint else 'app'
        methods = sorted(rule.methods - {'HEAD', 'OPTIONS'})

        if bp_name not in routes_by_blueprint:
            routes_by_blueprint[bp_name] = []

        routes_by_blueprint[bp_name].append({
            'rule': rule.rule,
            'endpoint': rule.endpoint,
            'methods': methods,
        })

    # Sort routes within each blueprint
    for bp_name in routes_by_blueprint:
        routes_by_blueprint[bp_name].sort(key=lambda r: r['rule'])

    # Sort blueprints alphabetically
    sorted_blueprints = dict(sorted(routes_by_blueprint.items()))

    return render_template(
        'admin_sitemap.html',
        routes_by_blueprint=sorted_blueprints,
    )


# ======================================================================
# POST /admin/server/restart — Restart the Flask server
# ======================================================================
@admin_bp.route('/admin/server/restart', methods=['POST'])
@login_required
@_require_admin
def restart_server():
    """Restart the Flask server process."""
    try:
        from utils.paths import is_frozen
        import subprocess
        if is_frozen():
            # In exe mode, launch the exe again and let this process exit
            subprocess.Popen(
                [sys.executable, '--mode=server'],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    return jsonify({'success': True})


# ======================================================================
# GET/POST /admin/config — Config Editor
# ======================================================================
# Editable config keys (whitelist — only these can be changed via UI)
_EDITABLE_CONFIG_KEYS = [
    # Section 2
    'SCREEN_RESOLUTION', 'MRN_CAPTURE_REGION',
    'AMAZING_CHARTS_PROCESS_NAME', 'TESSERACT_PATH',
    # Section 4
    'PUSHOVER_USER_KEY', 'PUSHOVER_API_TOKEN',
    'NOTIFY_QUIET_HOURS_START', 'NOTIFY_QUIET_HOURS_END',
    # Section 6
    'INBOX_CHECK_INTERVAL_MINUTES',
    # Section 7
    'IDLE_THRESHOLD_SECONDS', 'MAX_CHART_OPEN_MINUTES',
    'INBOX_FILTER_DROPDOWN_XY', 'INBOX_TABLE_REGION',
    'PATIENT_LIST_ID_SEARCH_XY', 'VISIT_TEMPLATE_RADIO_XY',
    'SELECT_TEMPLATE_DROPDOWN_XY', 'EXPORT_CLIN_SUM_MENU_XY',
    'EXPORT_BUTTON_XY', 'CLINICAL_SUMMARY_EXPORT_FOLDER',
    'CLINICAL_SUMMARY_RETENTION_DAYS',
    'INBOX_WARNING_HOURS', 'INBOX_CRITICAL_HOURS',
    # Section 8 — Test Data
    'TEST_PATIENT_APPOINTMENT_ENABLED',
]


@admin_bp.route('/admin/config', methods=['GET', 'POST'])
@login_required
@_require_admin
def admin_config():
    """View and edit config.py variables through the browser."""
    import config as cfg

    if request.method == 'POST':
        # Save updated values back to config.py
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.py')
        if not os.path.isfile(config_path):
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config.py')

        try:
            with open(config_path, 'r') as f:
                content = f.read()

            changes = []
            for key in _EDITABLE_CONFIG_KEYS:
                new_val = request.form.get(key, '').strip()
                if not new_val:
                    continue

                old_val = getattr(cfg, key, None)
                if old_val is None:
                    continue

                # Convert the form value to the appropriate type
                formatted_val = _format_config_value(old_val, new_val)
                if formatted_val is None:
                    continue

                # Replace in file content using regex
                import re
                pattern = re.compile(
                    r'^(' + re.escape(key) + r'\s*=\s*)(.+)$',
                    re.MULTILINE
                )
                replacement = r'\g<1>' + formatted_val
                new_content, count = pattern.subn(replacement, content)
                if count > 0:
                    content = new_content
                    # Also update the live config module
                    setattr(cfg, key, _parse_config_value(old_val, new_val))
                    changes.append(key)

            if changes:
                with open(config_path, 'w') as f:
                    f.write(content)
                flash(f'Updated {len(changes)} setting(s): {", ".join(changes)}', 'success')
            else:
                flash('No changes detected.', 'info')

        except Exception as e:
            import logging
            logging.getLogger(__name__).error('Config save error: %s', e)
            flash('Could not save configuration. Check server logs for details.', 'error')

        return redirect(url_for('admin_hub.admin_config'))

    # GET — build list of config values
    config_items = []
    for key in _EDITABLE_CONFIG_KEYS:
        val = getattr(cfg, key, None)
        if val is not None:
            config_items.append({
                'key': key,
                'value': repr(val),
                'display_value': str(val),
                'type': type(val).__name__,
            })

    # Pre-live warnings
    warnings = []
    if getattr(cfg, 'AC_MOCK_MODE', False):
        warnings.append('<b>AC_MOCK_MODE</b> is True — agent uses mock screenshots, not the live Amazing Charts window.')
    if getattr(cfg, 'DEBUG', False):
        warnings.append('<b>DEBUG</b> is True — disable before deploying to a shared network.')
    if not getattr(cfg, 'PUSHOVER_USER_KEY', ''):
        warnings.append('<b>PUSHOVER_USER_KEY</b> is empty — push notifications will not work.')
    if not getattr(cfg, 'PUSHOVER_API_TOKEN', ''):
        warnings.append('<b>PUSHOVER_API_TOKEN</b> is empty — push notifications will not work.')
    if getattr(cfg, 'TEST_PATIENT_APPOINTMENT_ENABLED', False):
        warnings.append('<b>TEST_PATIENT_APPOINTMENT_ENABLED</b> is True — a fake 07:00 appointment appears on dashboard.')

    return render_template('admin_config.html', config_items=config_items, warnings=warnings)


def _format_config_value(old_val, new_val):
    """Format a string form value for writing to config.py."""
    if isinstance(old_val, bool):
        return 'True' if new_val.lower() in ('true', '1', 'yes', 'on') else 'False'
    elif isinstance(old_val, int):
        try:
            return str(int(new_val))
        except ValueError:
            return None
    elif isinstance(old_val, float):
        try:
            return str(float(new_val))
        except ValueError:
            return None
    elif isinstance(old_val, tuple):
        # Accept formats like (0, 0) or 0, 0
        cleaned = new_val.strip('() ')
        try:
            parts = [int(x.strip()) for x in cleaned.split(',')]
            return '(' + ', '.join(str(p) for p in parts) + ')'
        except ValueError:
            return None
    elif isinstance(old_val, str):
        # Escape quotes in the value
        escaped = new_val.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    elif isinstance(old_val, list):
        return repr(new_val) if isinstance(new_val, list) else None
    return None


def _parse_config_value(old_val, new_val):
    """Parse a string form value to the correct Python type."""
    if isinstance(old_val, bool):
        return new_val.lower() in ('true', '1', 'yes', 'on')
    elif isinstance(old_val, int):
        return int(new_val)
    elif isinstance(old_val, float):
        return float(new_val)
    elif isinstance(old_val, tuple):
        cleaned = new_val.strip('() ')
        parts = [int(x.strip()) for x in cleaned.split(',')]
        return tuple(parts)
    elif isinstance(old_val, str):
        return new_val
    return new_val


# ======================================================================
# GET /admin/tools — Admin quick-action tools page
# ======================================================================
@admin_bp.route('/admin/tools')
@login_required
@_require_admin
def admin_tools():
    """Quick-action admin tools: seed data, run agent tests, etc."""
    return render_template('admin_tools.html')


# ======================================================================
# POST /admin/tools/seed-test-data — Seed test patient data
# ======================================================================
@admin_bp.route('/admin/tools/seed-test-data', methods=['POST'])
@login_required
@_require_admin
def admin_seed_test_data():
    """Seed the database with test patient data."""
    from scripts.seed_test_data import seed_all_test_data
    try:
        result = seed_all_test_data(current_user.id)
        flash(f'Test data seeded successfully. {result}', 'success')
    except Exception as e:
        import logging
        logging.getLogger(__name__).error('Seed test data error: %s', e)
        flash('Could not seed test data. Check server logs for details.', 'error')
    return redirect(url_for('admin_hub.admin_tools'))


# ======================================================================
# POST /admin/tools/clear-test-data — Remove test patient data
# ======================================================================
@admin_bp.route('/admin/tools/clear-test-data', methods=['POST'])
@login_required
@_require_admin
def admin_clear_test_data():
    """Remove all test patient data from the database."""
    from scripts.seed_test_data import clear_test_data
    try:
        result = clear_test_data(current_user.id)
        flash(f'Test data cleared. {result}', 'success')
    except Exception as e:
        import logging
        logging.getLogger(__name__).error('Clear test data error: %s', e)
        flash('Could not clear test data. Check server logs for details.', 'error')
    return redirect(url_for('admin_hub.admin_tools'))


# ======================================================================
# POST /admin/tools/purge-reimport-xml — Purge all patient data and
# re-import every XML test patient from Documents/xml_test_patients/
# ======================================================================
@admin_bp.route('/admin/tools/purge-reimport-xml', methods=['POST'])
@login_required
@_require_admin
def admin_purge_reimport_xml():
    """Delete all patient clinical data and re-import XML test patients."""
    import glob
    from models import db
    from models.patient import (
        PatientRecord, PatientMedication, PatientDiagnosis,
        PatientAllergy, PatientImmunization, PatientVitals,
        PatientLabResult, PatientSocialHistory, PatientEncounterNote,
    )
    from agent.clinical_summary_parser import parse_clinical_summary, store_parsed_summary

    uid = current_user.id
    xml_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'Documents', 'xml_test_patients',
    )

    try:
        # ---- Phase 1: purge all patient clinical data for this user ----
        purged = 0
        for model in (PatientMedication, PatientDiagnosis, PatientAllergy,
                      PatientImmunization, PatientVitals, PatientLabResult,
                      PatientEncounterNote, PatientSocialHistory):
            purged += model.query.filter_by(user_id=uid).delete()
        # Remove PatientRecord rows so they get re-created from XML
        purged += PatientRecord.query.filter_by(user_id=uid).delete()
        db.session.flush()

        # ---- Phase 2: re-import every XML in the test patients folder ----
        xml_files = sorted(glob.glob(os.path.join(xml_dir, '*.xml')))
        if not xml_files:
            db.session.commit()
            flash('Patient data purged, but no XML files found to reimport.', 'warning')
            return redirect(url_for('admin_hub.admin_tools'))

        imported = 0
        errors = []
        for xml_path in xml_files:
            try:
                parsed = parse_clinical_summary(xml_path)
                mrn = parsed.get('patient_mrn', '').strip()
                if not mrn:
                    errors.append(os.path.basename(xml_path) + ' (no MRN)')
                    continue
                store_parsed_summary(uid, mrn, parsed)
                imported += 1
            except Exception as inner:
                errors.append(os.path.basename(xml_path) + f' ({inner})')

        db.session.commit()

        msg = f'Purged {purged} rows. Re-imported {imported}/{len(xml_files)} patients.'
        if errors:
            msg += f' Errors: {", ".join(errors)}'
        flash(msg, 'success' if not errors else 'warning')
    except Exception as e:
        db.session.rollback()
        import logging
        logging.getLogger(__name__).error('Purge & reimport error: %s', e)
        flash('Purge & reimport failed. Check server logs.', 'error')

    return redirect(url_for('admin_hub.admin_tools'))


# ======================================================================
# GET /admin/caregap-rules — View/edit care gap screening rules (F15)
# ======================================================================
@admin_bp.route('/admin/caregap-rules')
@login_required
@_require_admin
def admin_caregap_rules():
    """List all care gap rules with edit links."""
    from models.caregap import CareGapRule
    rules = CareGapRule.query.order_by(CareGapRule.gap_name).all()
    return render_template('admin_caregap_rules.html', rules=rules)


# ======================================================================
# POST /admin/caregap-rules/<id>/edit — Update a care gap rule
# ======================================================================
@admin_bp.route('/admin/caregap-rules/<int:rule_id>/edit', methods=['POST'])
@login_required
@_require_admin
def admin_caregap_rule_edit(rule_id):
    """Update a single care gap rule from the admin form."""
    import json
    from models.caregap import CareGapRule

    rule = CareGapRule.query.get_or_404(rule_id)

    rule.gap_name = request.form.get('gap_name', rule.gap_name).strip()
    rule.description = request.form.get('description', rule.description).strip()
    rule.interval_days = int(request.form.get('interval_days', rule.interval_days) or 0)
    rule.billing_code_pair = request.form.get('billing_code_pair', rule.billing_code_pair).strip()
    rule.documentation_template = request.form.get('documentation_template', rule.documentation_template).strip()
    rule.is_active = request.form.get('is_active') == 'on'

    # Validate and save criteria JSON
    criteria_str = request.form.get('criteria_json', '').strip()
    if criteria_str:
        try:
            json.loads(criteria_str)
            rule.criteria_json = criteria_str
        except json.JSONDecodeError:
            flash('Invalid criteria JSON — not saved.', 'warning')

    db.session.commit()
    flash(f'Rule "{rule.gap_name}" updated.', 'success')
    return redirect(url_for('admin_hub.admin_caregap_rules'))


# ======================================================================
# POST /admin/caregap-rules/reset — Reset rules to defaults
# ======================================================================
@admin_bp.route('/admin/caregap-rules/reset', methods=['POST'])
@login_required
@_require_admin
def admin_caregap_rules_reset():
    """Delete all rules and re-seed from defaults."""
    from models.caregap import CareGapRule
    from agent.caregap_engine import seed_default_rules

    CareGapRule.query.delete()
    db.session.commit()
    seed_default_rules(current_app._get_current_object())
    flash('Care gap rules reset to USPSTF defaults.', 'success')
    return redirect(url_for('admin_hub.admin_caregap_rules'))


# ======================================================================
# GET /admin/updates — Update management page
# ======================================================================
@admin_bp.route('/admin/updates')
@login_required
@_require_admin
def admin_updates():
    """Show current version and update controls."""
    import config as cfg
    return render_template(
        'admin_updates.html',
        current_version=getattr(cfg, 'APP_VERSION', 'unknown'),
        update_folder=getattr(cfg, 'UPDATE_FOLDER', ''),
    )


# ======================================================================
# POST /admin/updates/scan — Scan a folder for update zips
# ======================================================================
@admin_bp.route('/admin/updates/scan', methods=['POST'])
@login_required
@_require_admin
def admin_updates_scan():
    """Scan the specified folder for CareCompanion_v*.zip files."""
    import config as cfg
    from utils.updater import check_for_update

    folder = request.form.get('folder', '').strip()
    if not folder:
        folder = getattr(cfg, 'UPDATE_FOLDER', '')
    if not folder or not os.path.isdir(folder):
        return jsonify({'found': False, 'error': 'Folder not found or empty path.'})

    result = check_for_update(folder, getattr(cfg, 'APP_VERSION', '0.0.0'))
    if result:
        return jsonify({'found': True, **result})
    return jsonify({'found': False, 'message': 'No newer version found.'})


# ======================================================================
# POST /admin/updates/apply — Apply an update from a zip file
# ======================================================================
@admin_bp.route('/admin/updates/apply', methods=['POST'])
@login_required
@_require_admin
def admin_updates_apply():
    """Apply the update zip and prepare for restart."""
    from utils.updater import apply_update

    zip_path = request.form.get('zip_path', '').strip()
    if not zip_path or not os.path.isfile(zip_path):
        return jsonify({'success': False, 'error': 'Zip file not found.'})

    result = apply_update(zip_path)
    return jsonify(result)


# ======================================================================
# POST /admin/updates/restart — Restart after update
# ======================================================================
@admin_bp.route('/admin/updates/restart', methods=['POST'])
@login_required
@_require_admin
def admin_updates_restart():
    """Restart the application after an update."""
    from utils.updater import restart_after_update
    restart_after_update()
    return jsonify({'success': True})


# ======================================================================
# Phase 13 — Per-Provider Feature Tier Defaults
# ======================================================================
@admin_bp.route('/admin/provider-defaults', methods=['GET', 'POST'])
@login_required
@_require_admin
def admin_provider_defaults():
    """Set org-wide default feature tiers per role (NP, PA, MD)."""
    from utils.feature_gates import FEATURE_TIERS, TIER_DESCRIPTIONS

    if request.method == 'POST':
        for role in ('provider', 'ma'):
            tier = request.form.get(f'default_tier_{role}', 'essential')
            if tier in ('essential', 'standard', 'advanced'):
                # Store as org-level config preference on the admin user
                current_user.set_pref(f'org_default_tier_{role}', tier)
        db.session.commit()
        flash('Provider defaults saved.', 'success')
        return redirect(url_for('admin_hub.admin_provider_defaults'))

    # GET — load current defaults
    defaults = {}
    for role in ('provider', 'ma'):
        defaults[role] = current_user.get_pref(f'org_default_tier_{role}', 'essential')

    users = User.query.filter_by(is_active_account=True).order_by(User.display_name).all()
    user_tiers = []
    for u in users:
        user_tiers.append({
            'id': u.id,
            'name': u.display_name or u.username,
            'role': u.role,
            'tier': u.get_pref('feature_tier', 'essential'),
        })

    return render_template(
        'admin_provider_defaults.html',
        defaults=defaults,
        user_tiers=user_tiers,
        tier_descriptions=TIER_DESCRIPTIONS,
    )


# ======================================================================
# Phase 14 — Dismissal Audit Report
# ======================================================================
@admin_bp.route('/admin/dismissal-audit')
@login_required
@_require_admin
def admin_dismissal_audit():
    """View all dismissed billing opportunities and care gaps with reasons."""
    from models.billing import BillingOpportunity
    from models.caregap import CareGap

    # Filters from query string
    reason_filter = request.args.get('reason', '').strip()
    suggestion_type = request.args.get('type', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    dismissals = []

    # Billing opportunity dismissals
    if suggestion_type in ('', 'billing'):
        q = BillingOpportunity.query.filter_by(status='dismissed')
        if reason_filter:
            q = q.filter(BillingOpportunity.dismissal_reason.ilike(f'%{reason_filter}%'))
        if date_from:
            q = q.filter(BillingOpportunity.reviewed_at >= date_from)
        if date_to:
            q = q.filter(BillingOpportunity.reviewed_at <= date_to + ' 23:59:59')
        for opp in q.order_by(BillingOpportunity.reviewed_at.desc()).limit(200).all():
            dismissals.append({
                'type': 'Billing: ' + (opp.opportunity_type or ''),
                'reason': opp.dismissal_reason or '',
                'user_id': opp.user_id,
                'timestamp': opp.reviewed_at,
                'detail': opp.eligibility_basis or '',
            })

    # Care gap dismissals
    if suggestion_type in ('', 'caregap'):
        q = CareGap.query.filter_by(status='declined')
        if reason_filter:
            q = q.filter(CareGap.dismissal_reason.ilike(f'%{reason_filter}%'))
        if date_from:
            q = q.filter(CareGap.updated_at >= date_from)
        if date_to:
            q = q.filter(CareGap.updated_at <= date_to + ' 23:59:59')
        for gap in q.order_by(CareGap.updated_at.desc()).limit(200).all():
            dismissals.append({
                'type': 'Care Gap: ' + (gap.gap_type or ''),
                'reason': gap.dismissal_reason or '',
                'user_id': gap.user_id,
                'timestamp': gap.updated_at,
                'detail': gap.description or '',
            })

    # Sort combined by timestamp descending
    dismissals.sort(key=lambda d: d['timestamp'] or '', reverse=True)

    # Map user_ids to names
    user_ids = set(d['user_id'] for d in dismissals if d['user_id'])
    user_map = {}
    if user_ids:
        for u in User.query.filter(User.id.in_(user_ids)).all():
            user_map[u.id] = u.display_name or u.username
    for d in dismissals:
        d['user_name'] = user_map.get(d['user_id'], 'Unknown')

    return render_template(
        'admin_dismissal_audit.html',
        dismissals=dismissals,
        reason_filter=reason_filter,
        suggestion_type=suggestion_type,
        date_from=date_from,
        date_to=date_to,
    )

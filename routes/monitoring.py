"""
CareCompanion — Monitoring Calendar Routes
File: routes/monitoring.py
Phase 23.D1 + D2 + D4

Monitoring calendar: panel-wide view of labs due (overdue → due soon → future),
grouped by patient, with REMS highlights and venipuncture bundle annotations.

Preventive gaps dashboard (D2):
  GET /care-gaps/preventive      — Panel-wide preventive service compliance
  GET /care-gaps/preventive/csv  — CSV export for outreach

Patient-level monitoring API (D4):
  GET /api/patient/<mrn>/monitoring-due  — JSON of due labs (+ CDS Hooks format)
  GET /api/monitoring/rules/export       — FHIR R4 PlanDefinition export
"""

import csv
import io
import logging
from datetime import date, timedelta

from flask import Blueprint, render_template, request, jsonify, Response
from flask_login import login_required, current_user

from models import db
from models.monitoring import MonitoringRule, MonitoringSchedule, REMSTrackerEntry

logger = logging.getLogger(__name__)

monitoring_bp = Blueprint('monitoring', __name__)


@monitoring_bp.route('/monitoring/calendar')
@login_required
def calendar():
    """Monitoring calendar — labs due grouped by date range and patient."""
    today = date.today()
    end_of_week = today + timedelta(days=(6 - today.weekday()))
    end_of_month = date(
        today.year + (1 if today.month == 12 else 0),
        (today.month % 12) + 1,
        1,
    ) - timedelta(days=1)
    future_90 = today + timedelta(days=90)

    # Filter controls
    priority_filter = request.args.get('priority', '')
    trigger_filter = request.args.get('trigger', '')
    source_filter = request.args.get('source', '')

    # Base query: active schedules for current user within 90 days
    q = MonitoringSchedule.query.filter_by(
        user_id=current_user.id,
        status='active',
    ).filter(
        MonitoringSchedule.next_due_date <= future_90,
    ).order_by(MonitoringSchedule.next_due_date.asc())

    if priority_filter:
        q = q.filter(MonitoringSchedule.priority == priority_filter)
    if source_filter:
        q = q.filter(MonitoringSchedule.source == source_filter)

    schedules = q.all()

    # Partition into date-range buckets
    overdue = []
    due_this_week = []
    due_this_month = []
    due_future = []

    for s in schedules:
        # Apply trigger filter (trigger is derived, not a column filter)
        if trigger_filter:
            has_med = bool(s.triggering_medication)
            has_cond = bool(s.triggering_condition)
            if trigger_filter == 'medication' and not has_med:
                continue
            if trigger_filter == 'condition' and not has_cond:
                continue
            if trigger_filter == 'rems' and s.priority != 'critical':
                continue

        if not s.next_due_date:
            due_future.append(s)
        elif s.next_due_date < today:
            overdue.append(s)
        elif s.next_due_date <= end_of_week:
            due_this_week.append(s)
        elif s.next_due_date <= end_of_month:
            due_this_month.append(s)
        else:
            due_future.append(s)

    # Group each bucket by patient
    def group_by_patient(entries):
        groups = {}
        for e in entries:
            key = e.patient_mrn_hash
            if key not in groups:
                groups[key] = {
                    'mrn_hash': key,
                    'display_mrn': key[-4:] if key else '????',
                    'entries': [],
                }
            groups[key]['entries'].append(e)
        return list(groups.values())

    # Detect bundles: same patient + same due date = potential single draw
    def annotate_bundles(patient_groups):
        for pg in patient_groups:
            by_date = {}
            for e in pg['entries']:
                by_date.setdefault(str(e.next_due_date), []).append(e)
            pg['bundles'] = {
                d: len(labs) for d, labs in by_date.items() if len(labs) > 1
            }
        return patient_groups

    buckets = [
        {
            'label': 'Overdue',
            'css_class': 'bucket-overdue',
            'color': '#e74c3c',
            'patients': annotate_bundles(group_by_patient(overdue)),
        },
        {
            'label': 'Due This Week',
            'css_class': 'bucket-week',
            'color': '#f39c12',
            'patients': annotate_bundles(group_by_patient(due_this_week)),
        },
        {
            'label': 'Due This Month',
            'css_class': 'bucket-month',
            'color': '#f1c40f',
            'patients': annotate_bundles(group_by_patient(due_this_month)),
        },
        {
            'label': 'Due Next 30–90 Days',
            'css_class': 'bucket-future',
            'color': '#27ae60',
            'patients': annotate_bundles(group_by_patient(due_future)),
        },
    ]

    # REMS entries for current user (for the REMS badge overlay)
    rems_entries = REMSTrackerEntry.query.filter_by(
        user_id=current_user.id,
        status='active',
    ).order_by(REMSTrackerEntry.next_due_date.asc()).all()

    # Summary counts
    total_count = len(schedules)
    overdue_count = len(overdue)
    rems_count = sum(1 for s in schedules if s.priority == 'critical')
    critical_count = sum(1 for s in schedules if s.priority in ('critical', 'high'))

    return render_template(
        'monitoring_calendar.html',
        buckets=buckets,
        rems_entries=rems_entries,
        total_count=total_count,
        overdue_count=overdue_count,
        rems_count=rems_count,
        critical_count=critical_count,
        today=today,
        priority_filter=priority_filter,
        trigger_filter=trigger_filter,
        source_filter=source_filter,
    )


# ======================================================================
# D4 — GET /api/patient/<mrn>/monitoring-due
# ======================================================================

@monitoring_bp.route('/api/patient/<mrn>/monitoring-due')
@login_required
def monitoring_due(mrn):
    """
    During-encounter "Labs Due This Visit" data.

    Returns MonitoringSchedule entries due within 30 days, REMS status,
    KDIGO eGFR alerts, and MELD/Child-Pugh scores for liver patients.

    Query params:
        format=cds-hooks  — returns CDS Hooks card structures
        format=json       — default, returns structured JSON
    """
    from billing_engine.shared import hash_mrn

    mrn_hash = hash_mrn(mrn)
    today = date.today()
    cutoff = today + timedelta(days=30)
    fmt = request.args.get('format', 'json')

    # ── CDS Hooks format ──────────────────────────────────────────
    if fmt == 'cds-hooks':
        try:
            from app.services.monitoring_rule_engine import MonitoringRuleEngine
            engine = MonitoringRuleEngine(db)
            cards = engine.get_cds_hooks_cards(mrn_hash)
            return jsonify({'cards': cards})
        except Exception as exc:
            logger.warning("CDS Hooks generation failed: %s", exc)
            return jsonify({'cards': []})

    # ── Standard JSON format ──────────────────────────────────────

    # Active monitoring schedule entries due within 30 days
    entries = (
        MonitoringSchedule.query
        .filter_by(patient_mrn_hash=mrn_hash, user_id=current_user.id, status='active')
        .filter(MonitoringSchedule.next_due_date <= cutoff)
        .order_by(MonitoringSchedule.next_due_date.asc())
        .all()
    )

    due_labs = []
    for e in entries:
        due_labs.append({
            'id': e.id,
            'lab_name': e.lab_name,
            'lab_code': e.lab_code,
            'clinical_indication': e.clinical_indication or '',
            'next_due_date': str(e.next_due_date) if e.next_due_date else '',
            'overdue': e.next_due_date < today if e.next_due_date else False,
            'priority': e.priority,
            'source': e.source,
            'triggering_medication': e.triggering_medication or '',
            'triggering_condition': e.triggering_condition or '',
            'last_result_value': e.last_result_value or '',
            'last_result_flag': e.last_result_flag or '',
            'can_bundle_with': e.can_bundle_with or '',
        })

    # Detect bundles: same-visit labs that can be drawn together
    bundle_groups = {}
    for lab in due_labs:
        bw = lab['can_bundle_with']
        if bw:
            bundle_groups.setdefault(bw, []).append(lab['lab_name'])
    bundle_count = sum(1 for v in bundle_groups.values() if len(v) >= 2)

    # REMS compliance status
    rems = REMSTrackerEntry.query.filter_by(
        patient_mrn_hash=mrn_hash, status='active'
    ).order_by(REMSTrackerEntry.next_due_date.asc()).all()

    rems_data = []
    for r in rems:
        rems_data.append({
            'id': r.id,
            'rems_program_name': r.rems_program_name,
            'requirement_type': r.requirement_type,
            'current_phase': r.current_phase or '',
            'interval_days': r.interval_days,
            'next_due_date': str(r.next_due_date) if r.next_due_date else '',
            'escalation_level': r.escalation_level,
            'status': r.status,
        })

    # KDIGO eGFR alerts + MELD/Child-Pugh
    egfr_alerts = []
    meld_score = None
    child_pugh_score = None
    try:
        from app.services.monitoring_rule_engine import MonitoringRuleEngine
        engine = MonitoringRuleEngine(db)

        egfr_alerts = engine.compute_egfr_alerts(mrn_hash)

        # Only compute liver scores for patients with liver disease dx
        from models.patient import PatientDiagnosis
        liver_prefixes = ('K70', 'K71', 'K72', 'K73', 'K74', 'K75', 'K76', 'B18')
        has_liver_dx = PatientDiagnosis.query.filter(
            PatientDiagnosis.mrn == mrn,
            PatientDiagnosis.user_id == current_user.id,
            db.or_(
                *[PatientDiagnosis.icd10_code.like(f'{pfx}%') for pfx in liver_prefixes]
            ),
        ).first()

        if has_liver_dx:
            meld_score = engine.compute_meld_score(mrn_hash)
            child_pugh_score = engine.compute_child_pugh_score(mrn_hash)
    except Exception as exc:
        logger.debug("Clinical scoring skipped for %s: %s", mrn, exc)

    return jsonify({
        'due_labs': due_labs,
        'due_count': len(due_labs),
        'overdue_count': sum(1 for lab in due_labs if lab['overdue']),
        'bundle_count': bundle_count,
        'rems': rems_data,
        'egfr_alerts': egfr_alerts,
        'meld_score': meld_score,
        'child_pugh_score': child_pugh_score,
    })


# ======================================================================
# D4 — GET /api/monitoring/rules/export  (FHIR R4 PlanDefinition)
# ======================================================================

@monitoring_bp.route('/api/monitoring/rules/export')
@login_required
def export_rules():
    """
    Export monitoring rules as FHIR R4 PlanDefinition resources.

    Query params:
        rxcui     — filter by RxCUI
        icd10     — filter by ICD-10 trigger code
    """
    rxcui = request.args.get('rxcui', '')
    icd10 = request.args.get('icd10', '')

    try:
        from app.services.monitoring_rule_engine import MonitoringRuleEngine
        engine = MonitoringRuleEngine(db)
        plan_def = engine.export_rules_as_fhir_plan_definition(
            rxcui=rxcui or None,
            icd10_code=icd10 or None,
        )
        return jsonify(plan_def)
    except Exception as exc:
        logger.error("FHIR PlanDefinition export failed: %s", exc)
        return jsonify({'error': 'Export failed'}), 500


# ======================================================================
# D2 — GET /care-gaps/preventive  (Panel-wide preventive compliance)
# ======================================================================

@monitoring_bp.route('/care-gaps/preventive')
@login_required
def preventive_gaps():
    """
    Panel-wide preventive service dashboard.

    Cross-references PatientRecord entries against MonitoringRule VSAC
    rules and PreventiveServiceRecord to show compliance rates, overdue
    counts, and revenue opportunity per service.
    """
    from models.patient import PatientRecord
    from models.preventive import PreventiveServiceRecord
    from models.billing import BillingRuleCache

    today = date.today()

    # All VSAC preventive rules (trigger_type=CONDITION, source=VSAC)
    vsac_rules = MonitoringRule.query.filter_by(
        trigger_type='CONDITION', source='VSAC', is_active=True
    ).all()

    # Patient panel for this provider
    patients = PatientRecord.query.filter_by(
        claimed_by=current_user.id
    ).all()
    total_patients = len(patients)

    # Build patient lookup by mrn_hash
    from billing_engine.shared import hash_mrn
    patient_map = {}
    for p in patients:
        h = hash_mrn(p.mrn)
        patient_map[h] = p

    # All preventive service records for this provider
    all_services = PreventiveServiceRecord.query.filter_by(
        user_id=current_user.id
    ).all()

    # Index completed services by (patient_mrn_hash, service_code)
    completed = {}
    for svc in all_services:
        key = (svc.patient_mrn_hash, svc.service_code)
        existing = completed.get(key)
        if existing is None or (svc.service_date and svc.service_date > existing.service_date):
            completed[key] = svc

    # Current year billing rates for revenue calculation
    current_year = today.year
    rates = {}
    for rule in vsac_rules:
        if rule.lab_cpt_code:
            cached = BillingRuleCache.query.filter_by(
                hcpcs_code=rule.lab_cpt_code,
                fee_schedule_year=current_year,
            ).first()
            if cached:
                rates[rule.lab_cpt_code] = cached.non_facility_payment or 0.0

    # Build per-service summary
    services = []
    total_overdue = 0
    total_revenue = 0.0

    for rule in vsac_rules:
        eligible_count = total_patients  # all claimed patients are eligible by default
        completed_count = 0
        overdue_count = 0
        overdue_patients = []

        for mrn_hash, pat in patient_map.items():
            svc_record = completed.get((mrn_hash, rule.lab_cpt_code))

            if svc_record and svc_record.next_due_date:
                if svc_record.next_due_date > today:
                    completed_count += 1
                    continue

            # One-time screenings (interval_days=0): completed if any record exists
            if rule.interval_days == 0 and svc_record:
                completed_count += 1
                continue

            # Patient is overdue or never screened
            overdue_count += 1
            overdue_patients.append({
                'mrn': pat.mrn,
                'name': pat.patient_name or f'...{pat.mrn[-4:]}',
                'mrn_display': f'...{pat.mrn[-4:]}' if pat.mrn else '????',
                'last_performed': str(svc_record.service_date) if svc_record else 'Never',
            })

        compliance_pct = round(
            (completed_count / eligible_count * 100) if eligible_count > 0 else 0, 1
        )
        cpt_rate = rates.get(rule.lab_cpt_code, 0.0)
        revenue_opportunity = round(overdue_count * cpt_rate, 2)

        total_overdue += overdue_count
        total_revenue += revenue_opportunity

        services.append({
            'rule_id': rule.id,
            'service_name': rule.lab_name,
            'cpt_code': rule.lab_cpt_code,
            'icd10_trigger': rule.icd10_trigger or '',
            'interval_days': rule.interval_days,
            'priority': rule.priority,
            'eligible_count': eligible_count,
            'completed_count': completed_count,
            'overdue_count': overdue_count,
            'compliance_pct': compliance_pct,
            'revenue_opportunity': revenue_opportunity,
            'cpt_rate': cpt_rate,
            'overdue_patients': sorted(
                overdue_patients, key=lambda x: x['name'].lower()
            ),
        })

    # Sort: highest overdue first
    services.sort(key=lambda s: s['overdue_count'], reverse=True)

    # D5: Outreach-needed patients (overdue monitoring + not seen 30+ days)
    outreach_patients = []
    thirty_days_ago = today - timedelta(days=30)
    overdue_schedules = MonitoringSchedule.query.filter(
        MonitoringSchedule.user_id == current_user.id,
        MonitoringSchedule.status == 'active',
        MonitoringSchedule.next_due_date < today,
    ).all()

    outreach_by_patient = {}
    for entry in overdue_schedules:
        outreach_by_patient.setdefault(entry.patient_mrn_hash, []).append(entry)

    for mrn_hash, entries in outreach_by_patient.items():
        pat = patient_map.get(mrn_hash)
        if not pat:
            continue
        # Not seen in 30+ days
        if pat.last_xml_parsed and pat.last_xml_parsed.date() > thirty_days_ago:
            continue
        outreach_patients.append({
            'name': pat.patient_name or f'...{pat.mrn[-4:]}',
            'mrn_display': f'...{pat.mrn[-4:]}' if pat.mrn else '????',
            'overdue_count': len(entries),
            'labs': ', '.join(e.lab_name for e in entries[:3]) + (
                f' +{len(entries) - 3} more' if len(entries) > 3 else ''
            ),
            'has_critical': any(e.priority in ('critical', 'high') for e in entries),
        })

    outreach_patients.sort(key=lambda x: x['has_critical'], reverse=True)

    return render_template(
        'care_gaps_preventive.html',
        services=services,
        total_patients=total_patients,
        total_overdue=total_overdue,
        total_revenue=round(total_revenue, 2),
        service_count=len(vsac_rules),
        today=today,
        outreach_patients=outreach_patients,
    )


# ======================================================================
# D2 — GET /care-gaps/preventive/csv  (CSV export for outreach)
# ======================================================================

@monitoring_bp.route('/care-gaps/preventive/csv')
@login_required
def preventive_gaps_csv():
    """Export overdue preventive services as CSV for outreach."""
    from models.patient import PatientRecord
    from models.preventive import PreventiveServiceRecord
    from billing_engine.shared import hash_mrn

    today = date.today()

    vsac_rules = MonitoringRule.query.filter_by(
        trigger_type='CONDITION', source='VSAC', is_active=True
    ).all()

    patients = PatientRecord.query.filter_by(
        claimed_by=current_user.id
    ).all()

    patient_map = {}
    for p in patients:
        patient_map[hash_mrn(p.mrn)] = p

    all_services = PreventiveServiceRecord.query.filter_by(
        user_id=current_user.id
    ).all()

    completed = {}
    for svc in all_services:
        key = (svc.patient_mrn_hash, svc.service_code)
        existing = completed.get(key)
        if existing is None or (svc.service_date and svc.service_date > existing.service_date):
            completed[key] = svc

    # Optional filter by service
    filter_cpt = request.args.get('cpt', '')

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Patient Name', 'MRN (last 4)', 'Service', 'CPT Code',
                     'Last Performed', 'Status'])

    for rule in vsac_rules:
        if filter_cpt and rule.lab_cpt_code != filter_cpt:
            continue

        for mrn_hash, pat in patient_map.items():
            svc_record = completed.get((mrn_hash, rule.lab_cpt_code))

            is_complete = False
            if svc_record and svc_record.next_due_date and svc_record.next_due_date > today:
                is_complete = True
            if rule.interval_days == 0 and svc_record:
                is_complete = True

            if not is_complete:
                writer.writerow([
                    pat.patient_name or '',
                    f'...{pat.mrn[-4:]}' if pat.mrn else '',
                    rule.lab_name,
                    rule.lab_cpt_code,
                    str(svc_record.service_date) if svc_record else 'Never',
                    'Overdue',
                ])

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=preventive_gaps_outreach.csv'},
    )

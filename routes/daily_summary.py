"""
CareCompanion — Daily Summary & Rooming Sheet Routes
File: routes/daily_summary.py

Printable daily operations sheets for clinical workflow:
  GET /daily-summary              — Provider daily summary (screen view)
  GET /daily-summary/print        — Provider daily summary (print-optimized)
  GET /daily-summary/rooming      — MA/Rooming staff sheet (screen view)
  GET /daily-summary/rooming/print — MA/Rooming staff sheet (print-optimized)
  GET /reference/rems             — REMS medication database viewer
  GET /reference/reportable-diseases — Infectious disease reporting guide
"""

import json
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from models import db
from models.caregap import CareGap
from models.patient import PatientRecord, PatientLabResult
from models.schedule import Schedule

logger = logging.getLogger(__name__)

daily_summary_bp = Blueprint('daily_summary', __name__)

# ── Screening tool mapping ──────────────────────────────────────────
# Maps care gap types to the screening instruments the MA should
# administer during rooming/triage.
SCREENING_TOOLS = {
    'depression_screen': {'tool': 'PHQ-2 → PHQ-9', 'action': 'Administer PHQ-2; if score ≥ 3, administer PHQ-9'},
    'depression_phq2': {'tool': 'PHQ-2 → PHQ-9', 'action': 'Administer PHQ-2; if score ≥ 3, administer PHQ-9'},
    'depression_phq9': {'tool': 'PHQ-9', 'action': 'Administer PHQ-9 questionnaire'},
    'anxiety_screen': {'tool': 'GAD-7', 'action': 'Administer GAD-7 questionnaire'},
    'alcohol_screen': {'tool': 'AUDIT-C', 'action': 'Administer AUDIT-C questionnaire'},
    'alcohol_misuse': {'tool': 'AUDIT-C', 'action': 'Administer AUDIT-C questionnaire'},
    'tobacco_screen': {'tool': '5 A\'s', 'action': 'Ask tobacco/nicotine use status; document in social history'},
    'substance_use_screen': {'tool': 'DAST-10', 'action': 'Administer DAST-10 questionnaire'},
    'fall_risk': {'tool': 'Timed Up & Go', 'action': 'Perform Timed Up & Go test; record time in seconds'},
    'fall_risk_assessment': {'tool': 'Timed Up & Go', 'action': 'Perform Timed Up & Go test; record time in seconds'},
    'cognitive_screen': {'tool': 'Mini-Cog', 'action': 'Prepare Mini-Cog form (3-word recall + clock draw)'},
    'statin_use_discussion': {'tool': 'ASCVD Risk', 'action': 'Ensure fasting lipid panel on file; note statin discussion needed'},
    'intimate_partner_violence': {'tool': 'HITS/WAST', 'action': 'Administer HITS or WAST screening tool in private'},
    'unhealthy_drug_use': {'tool': 'DAST-10', 'action': 'Administer DAST-10 questionnaire'},
}

# Standard rooming tasks by visit type
ROOMING_TASKS_BY_VISIT = {
    '_default': [
        'Vital signs (BP, HR, Temp, RR, SpO2, Weight)',
        'Medication reconciliation',
        'Chief complaint / reason for visit',
    ],
    'PE': [  # Physical Exam
        'Vital signs (BP, HR, Temp, RR, SpO2, Weight, Height, BMI)',
        'Medication reconciliation',
        'Complete social history update',
        'Immunization history review',
        'Advance directive status',
    ],
    'AV': [  # Annual Wellness Visit
        'Vital signs (BP, HR, Temp, RR, SpO2, Weight, Height, BMI)',
        'Medication reconciliation',
        'Health Risk Assessment (HRA) form',
        'Advance directive status',
        'Fall risk screening (if age ≥ 65)',
        'Cognitive screening form (if age ≥ 65)',
        'PHQ-2 depression screen',
        'Complete social history update',
        'Immunization history review',
        'Functional status / ADL assessment',
    ],
    'NP': [  # New Patient
        'Vital signs (BP, HR, Temp, RR, SpO2, Weight, Height, BMI)',
        'Full medication reconciliation with bottles/list',
        'Allergy verification',
        'Complete social history',
        'Surgical history',
        'Family history',
        'Advance directive status',
        'Insurance card copy (front & back)',
        'PHQ-2 depression screen',
    ],
}

# Age-based additions
AGE_SCREENING_ADDITIONS = [
    {'min_age': 12, 'max_age': 999, 'task': 'Screen for depression (PHQ-2)', 'gap_key': 'depression_screen'},
    {'min_age': 18, 'max_age': 999, 'task': 'Ask about alcohol use (AUDIT-C)', 'gap_key': 'alcohol_screen'},
    {'min_age': 65, 'max_age': 999, 'task': 'Fall risk assessment (Timed Up & Go)', 'gap_key': 'fall_risk'},
    {'min_age': 65, 'max_age': 999, 'task': 'Cognitive screen (Mini-Cog) if not done this year', 'gap_key': 'cognitive_screen'},
    {'min_age': 65, 'max_age': 999, 'task': 'Advance directive review', 'gap_key': None},
]


def _estimate_age(dob_str):
    """Estimate patient age from DOB string (MM/DD/YYYY)."""
    if not dob_str:
        return None
    try:
        dob = datetime.strptime(dob_str, '%m/%d/%Y').date()
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except (ValueError, TypeError):
        return None


def _split_name(full_name):
    """Split 'LASTNAME, FIRSTNAME' or 'Firstname Lastname' into (first, last)."""
    if not full_name:
        return ('', '')
    if ',' in full_name:
        parts = full_name.split(',', 1)
        return (parts[1].strip(), parts[0].strip())
    parts = full_name.strip().split()
    if len(parts) >= 2:
        return (parts[0], ' '.join(parts[1:]))
    return (full_name.strip(), '')


def _gather_patient_data(appointments, user_id, include_labs=True, include_monitoring=True):
    """
    For each appointment, gather care gaps, labs, monitoring, and flags.
    Returns list of dicts ready for template rendering.
    """
    today = date.today()
    cutoff_30d = today + timedelta(days=30)
    cutoff_90d = today - timedelta(days=90)

    # Batch-load all open care gaps for this user
    all_gaps = CareGap.query.filter_by(
        user_id=user_id, is_addressed=False
    ).all()
    gaps_by_mrn = {}
    for g in all_gaps:
        gaps_by_mrn.setdefault(g.mrn, []).append(g)

    patients = []
    seen_mrns = set()

    for appt in appointments:
        mrn = appt.patient_mrn
        if not mrn or mrn in seen_mrns:
            continue
        seen_mrns.add(mrn)

        first_name, last_name = _split_name(appt.patient_name)
        age = _estimate_age(appt.patient_dob)

        # Care gaps
        patient_gaps = gaps_by_mrn.get(mrn, [])
        gap_names = [g.gap_name or g.gap_type.replace('_', ' ').title() for g in patient_gaps]
        gap_types = [g.gap_type for g in patient_gaps]

        # Screening tools needed (based on open care gaps)
        screening_tools = []
        for g in patient_gaps:
            tool_info = SCREENING_TOOLS.get(g.gap_type)
            if tool_info:
                screening_tools.append(tool_info)

        # Recent flagged lab results (abnormal/critical in last 90 days)
        flagged_labs = []
        if include_labs:
            flagged_labs = (
                PatientLabResult.query
                .filter(
                    PatientLabResult.user_id == user_id,
                    PatientLabResult.mrn == mrn,
                    PatientLabResult.result_flag.in_(['abnormal', 'critical']),
                    PatientLabResult.result_date >= cutoff_90d,
                )
                .order_by(PatientLabResult.result_date.desc())
                .limit(5)
                .all()
            )

        # Monitoring / Labs due within 30 days
        labs_due = []
        rems_alerts = []
        if include_monitoring:
            try:
                from models.monitoring import MonitoringSchedule, REMSTrackerEntry
                from billing_engine.shared import hash_mrn
                mrn_hash = hash_mrn(mrn)

                labs_due = (
                    MonitoringSchedule.query
                    .filter(
                        MonitoringSchedule.patient_mrn_hash == mrn_hash,
                        MonitoringSchedule.user_id == user_id,
                        MonitoringSchedule.status == 'active',
                        MonitoringSchedule.next_due_date <= cutoff_30d,
                    )
                    .order_by(MonitoringSchedule.next_due_date.asc())
                    .limit(5)
                    .all()
                )

                rems_alerts = (
                    REMSTrackerEntry.query
                    .filter(
                        REMSTrackerEntry.patient_mrn_hash == mrn_hash,
                        REMSTrackerEntry.user_id == user_id,
                        REMSTrackerEntry.status == 'active',
                    )
                    .all()
                )
            except Exception as e:
                logger.debug('Monitoring data fetch failed for %s: %s', mrn[-4:], e)

        patients.append({
            'time': appt.appointment_time or '',
            'first_name': first_name,
            'last_name': last_name,
            'dob': appt.patient_dob or '',
            'mrn': mrn,
            'visit_type': appt.visit_type or '',
            'visit_type_code': appt.visit_type_code or '',
            'is_new_patient': appt.is_new_patient,
            'age': age,
            'gap_count': len(patient_gaps),
            'gap_names': gap_names[:4],
            'gap_overflow': max(0, len(gap_names) - 4),
            'gap_types': gap_types,
            'screening_tools': screening_tools,
            'flagged_labs': [{
                'name': lab.test_name,
                'value': lab.result_value,
                'units': lab.result_units or '',
                'flag': lab.result_flag,
                'date': lab.result_date.strftime('%m/%d') if lab.result_date else '',
            } for lab in flagged_labs],
            'labs_due': [{
                'name': m.lab_name,
                'due': str(m.next_due_date) if m.next_due_date else '',
                'overdue': m.next_due_date < today if m.next_due_date else False,
                'priority': m.priority,
                'trigger': m.triggering_medication or m.triggering_condition or '',
            } for m in labs_due],
            'rems_alerts': [{
                'program': r.rems_program_name,
                'drug': r.drug_name,
                'escalation': r.escalation_level,
                'next_due': str(r.next_due_date) if r.next_due_date else '',
            } for r in rems_alerts],
        })

    return patients


# ======================================================================
# GET /daily-summary — Provider daily summary (screen view)
# ======================================================================
@daily_summary_bp.route('/daily-summary')
@login_required
def daily_summary():
    """Daily provider summary — schedule with care gaps, labs, and flags."""
    view_date_str = request.args.get('date', '')
    if view_date_str:
        try:
            view_date = date.fromisoformat(view_date_str)
        except ValueError:
            view_date = date.today()
    else:
        view_date = date.today()

    appointments = (
        Schedule.query
        .filter_by(user_id=current_user.id, appointment_date=view_date)
        .order_by(Schedule.appointment_time)
        .all()
    )

    provider_name = getattr(current_user, 'full_name', '') or current_user.username
    patients = _gather_patient_data(appointments, current_user.id)

    return render_template(
        'daily_summary_print.html',
        provider_name=provider_name,
        view_date=view_date.strftime('%A, %B %d, %Y'),
        view_date_raw=view_date.isoformat(),
        patients=patients,
        patient_count=len(patients),
        auto_print=False,
    )


# ======================================================================
# GET /daily-summary/print — Provider daily summary (print-optimized)
# ======================================================================
@daily_summary_bp.route('/daily-summary/print')
@login_required
def daily_summary_print():
    """Print-optimized daily summary — opens print dialog on load."""
    view_date_str = request.args.get('date', '')
    if view_date_str:
        try:
            view_date = date.fromisoformat(view_date_str)
        except ValueError:
            view_date = date.today()
    else:
        view_date = date.today()

    appointments = (
        Schedule.query
        .filter_by(user_id=current_user.id, appointment_date=view_date)
        .order_by(Schedule.appointment_time)
        .all()
    )

    provider_name = getattr(current_user, 'full_name', '') or current_user.username
    patients = _gather_patient_data(appointments, current_user.id)

    return render_template(
        'daily_summary_print.html',
        provider_name=provider_name,
        view_date=view_date.strftime('%A, %B %d, %Y'),
        view_date_raw=view_date.isoformat(),
        patients=patients,
        patient_count=len(patients),
        auto_print=True,
    )


# ======================================================================
# GET /daily-summary/rooming — MA/Rooming staff sheet (screen view)
# ======================================================================
@daily_summary_bp.route('/daily-summary/rooming')
@login_required
def rooming_sheet():
    """MA/Rooming staff sheet — screening tools and tasks per patient."""
    view_date_str = request.args.get('date', '')
    if view_date_str:
        try:
            view_date = date.fromisoformat(view_date_str)
        except ValueError:
            view_date = date.today()
    else:
        view_date = date.today()

    appointments = (
        Schedule.query
        .filter_by(user_id=current_user.id, appointment_date=view_date)
        .order_by(Schedule.appointment_time)
        .all()
    )

    provider_name = getattr(current_user, 'full_name', '') or current_user.username
    patients = _gather_patient_data(
        appointments, current_user.id,
        include_labs=False, include_monitoring=False,
    )

    # Build rooming tasks per patient
    for pt in patients:
        code = pt['visit_type_code'].upper() if pt['visit_type_code'] else ''
        base_tasks = list(ROOMING_TASKS_BY_VISIT.get(code, ROOMING_TASKS_BY_VISIT['_default']))

        # Add age-based screening tasks
        age = pt['age']
        if age is not None:
            for rule in AGE_SCREENING_ADDITIONS:
                if rule['min_age'] <= age <= rule['max_age']:
                    # Only add if not already covered by a care gap screening tool
                    if rule['gap_key'] is None or rule['gap_key'] not in [g.get('gap_key', '') for g in pt.get('screening_tools', [])]:
                        if rule['task'] not in base_tasks:
                            base_tasks.append(rule['task'])

        pt['rooming_tasks'] = base_tasks

    return render_template(
        'rooming_sheet_print.html',
        provider_name=provider_name,
        view_date=view_date.strftime('%A, %B %d, %Y'),
        view_date_raw=view_date.isoformat(),
        patients=patients,
        patient_count=len(patients),
        auto_print=False,
    )


# ======================================================================
# GET /daily-summary/rooming/print — MA/Rooming sheet (print-optimized)
# ======================================================================
@daily_summary_bp.route('/daily-summary/rooming/print')
@login_required
def rooming_sheet_print():
    """Print-optimized rooming sheet — opens print dialog on load."""
    view_date_str = request.args.get('date', '')
    if view_date_str:
        try:
            view_date = date.fromisoformat(view_date_str)
        except ValueError:
            view_date = date.today()
    else:
        view_date = date.today()

    appointments = (
        Schedule.query
        .filter_by(user_id=current_user.id, appointment_date=view_date)
        .order_by(Schedule.appointment_time)
        .all()
    )

    provider_name = getattr(current_user, 'full_name', '') or current_user.username
    patients = _gather_patient_data(
        appointments, current_user.id,
        include_labs=False, include_monitoring=False,
    )

    for pt in patients:
        code = pt['visit_type_code'].upper() if pt['visit_type_code'] else ''
        base_tasks = list(ROOMING_TASKS_BY_VISIT.get(code, ROOMING_TASKS_BY_VISIT['_default']))
        age = pt['age']
        if age is not None:
            for rule in AGE_SCREENING_ADDITIONS:
                if rule['min_age'] <= age <= rule['max_age']:
                    if rule['gap_key'] is None or rule['gap_key'] not in [g.get('gap_key', '') for g in pt.get('screening_tools', [])]:
                        if rule['task'] not in base_tasks:
                            base_tasks.append(rule['task'])
        pt['rooming_tasks'] = base_tasks

    return render_template(
        'rooming_sheet_print.html',
        provider_name=provider_name,
        view_date=view_date.strftime('%A, %B %d, %Y'),
        view_date_raw=view_date.isoformat(),
        patients=patients,
        patient_count=len(patients),
        auto_print=True,
    )


# ======================================================================
# GET /reference/rems — REMS medication database viewer
# ======================================================================
@daily_summary_bp.route('/reference/rems')
@login_required
def rems_reference():
    """View the REMS medication database — all active REMS programs."""
    data_path = Path(__file__).resolve().parent.parent / 'data' / 'rems_database.json'
    rems_data = []
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            rems_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error('Failed to load REMS database: %s', e)

    return render_template(
        'rems_reference.html',
        rems_programs=rems_data,
        program_count=len(rems_data),
    )


# ======================================================================
# GET /reference/reportable-diseases — Infectious disease reporting guide
# ======================================================================
@daily_summary_bp.route('/reference/reportable-diseases')
@login_required
def reportable_diseases():
    """View the infectious disease reporting guide."""
    data_path = Path(__file__).resolve().parent.parent / 'data' / 'reportable_diseases.json'
    disease_data = []
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            disease_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error('Failed to load reportable diseases data: %s', e)

    return render_template(
        'reportable_diseases_reference.html',
        diseases=disease_data,
        disease_count=len(disease_data),
    )

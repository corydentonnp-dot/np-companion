"""
CareCompanion — Care Gap Routes

File location: carecompanion/routes/caregap.py

Routes:
  GET  /caregap                         — Overview of upcoming patients' care gaps
  GET  /caregap/<mrn>                   — All gaps for one patient
  POST /caregap/<mrn>/address/<gap_id>  — Mark gap as addressed
  GET  /caregap/panel                   — Panel-wide gap summary
  GET  /caregap/panel/outreach          — Outreach list for a specific gap type
  POST /caregap/<mrn>/status/<gap_id>   — Update gap status (decline, reopen)

Features: F15, F15a (auto-population), F15b (closure docs), F15c (panel report)
"""

from datetime import date, datetime, timedelta, timezone
import json

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, jsonify, Response,
)
from flask_login import login_required, current_user

from models import db
from models.caregap import CareGap, CareGapRule
from models.patient import PatientRecord
from models.schedule import Schedule
from utils.feature_gates import require_feature

caregap_bp = Blueprint('caregap', __name__)


# ======================================================================
# GET /caregap — Overview: upcoming patients' care gaps
# ======================================================================
@caregap_bp.route('/caregap')
@login_required
@require_feature('caregap')
def index():
    """
    Show care gaps for today's (and optionally tomorrow's) scheduled
    patients.  Groups gaps by patient for a quick pre-visit review.
    """
    view_date_str = request.args.get('date', '')
    if view_date_str:
        try:
            view_date = date.fromisoformat(view_date_str)
        except ValueError:
            view_date = date.today()
    else:
        view_date = date.today()

    # Get scheduled patients for the view date
    appointments = (
        Schedule.query
        .filter_by(user_id=current_user.id, appointment_date=view_date)
        .order_by(Schedule.appointment_time)
        .all()
    )

    # Get all open care gaps for this user
    open_gaps = (
        CareGap.query
        .filter_by(user_id=current_user.id, is_addressed=False)
        .all()
    )

    # Group gaps by MRN
    gaps_by_mrn = {}
    for g in open_gaps:
        gaps_by_mrn.setdefault(g.mrn, []).append(g)

    # Build patient list with gap counts
    patients = []
    for appt in appointments:
        if not appt.patient_mrn:
            continue
        mrn = appt.patient_mrn
        patient_gaps = gaps_by_mrn.get(mrn, [])
        patients.append({
            'mrn': mrn,
            'mrn_display': '••' + mrn[-4:] if len(mrn) >= 4 else mrn,
            'name': appt.patient_name,
            'time': appt.appointment_time,
            'visit_type': appt.visit_type,
            'gap_count': len(patient_gaps),
            'gaps': patient_gaps,
        })

    # Also include patients with gaps who aren't on today's schedule
    scheduled_mrns = {p['mrn'] for p in patients}
    unscheduled_with_gaps = []
    for mrn, gaps in gaps_by_mrn.items():
        if mrn not in scheduled_mrns:
            name = gaps[0].patient_name if gaps else ''
            unscheduled_with_gaps.append({
                'mrn': mrn,
                'mrn_display': '••' + mrn[-4:] if len(mrn) >= 4 else mrn,
                'name': name,
                'time': '',
                'visit_type': '',
                'gap_count': len(gaps),
                'gaps': gaps,
            })

    yesterday = view_date - timedelta(days=1)
    tomorrow = view_date + timedelta(days=1)
    is_today = (view_date == date.today())

    total_gaps = sum(p['gap_count'] for p in patients)

    return render_template(
        'caregap.html',
        patients=patients,
        unscheduled_with_gaps=unscheduled_with_gaps,
        view_date=view_date,
        yesterday=yesterday,
        tomorrow=tomorrow,
        is_today=is_today,
        total_gaps=total_gaps,
    )


# ======================================================================
# GET /caregap/<mrn> — All gaps for one patient
# ======================================================================
@caregap_bp.route('/caregap/<mrn>')
@login_required
def patient_gaps(mrn):
    """Show all care gaps for a specific patient — open and addressed."""
    gaps = (
        CareGap.query
        .filter_by(user_id=current_user.id, mrn=mrn)
        .order_by(CareGap.is_addressed, CareGap.gap_name)
        .all()
    )

    # Get patient name from the most recent gap or schedule
    patient_name = ''
    if gaps:
        patient_name = gaps[0].patient_name
    if not patient_name:
        sched = Schedule.query.filter_by(
            user_id=current_user.id, patient_mrn=mrn
        ).order_by(Schedule.appointment_date.desc()).first()
        if sched:
            patient_name = sched.patient_name

    mrn_display = '••' + mrn[-4:] if len(mrn) >= 4 else mrn

    open_gaps = [g for g in gaps if not g.is_addressed]
    addressed_gaps = [g for g in gaps if g.is_addressed]

    return render_template(
        'caregap_patient.html',
        mrn=mrn,
        mrn_display=mrn_display,
        patient_name=patient_name,
        open_gaps=open_gaps,
        addressed_gaps=addressed_gaps,
        _derive_trigger_type=_derive_trigger_type,
    )


def _derive_trigger_type(gap):
    """Return 'risk_factor' or 'demographic' based on the matching rule's criteria."""
    rule = CareGapRule.query.filter_by(gap_type=gap.gap_type).first()
    if rule and rule.criteria_json:
        try:
            criteria = json.loads(rule.criteria_json)
        except (json.JSONDecodeError, TypeError):
            criteria = {}
        if criteria.get('risk_factors') or criteria.get('icd10_codes'):
            return 'risk_factor'
    return 'demographic'


# ======================================================================
# GET /caregap/<mrn>/print — Printer-optimized patient handout
# ======================================================================
@caregap_bp.route('/caregap/<mrn>/print')
@login_required
def print_handout(mrn):
    """Render a clean, printer-friendly care gap handout for the patient."""
    gaps = (
        CareGap.query
        .filter_by(user_id=current_user.id, mrn=mrn)
        .order_by(CareGap.is_addressed, CareGap.gap_name)
        .all()
    )

    patient_name = ''
    if gaps:
        patient_name = gaps[0].patient_name
    if not patient_name:
        sched = Schedule.query.filter_by(
            user_id=current_user.id, patient_mrn=mrn
        ).order_by(Schedule.appointment_date.desc()).first()
        if sched:
            patient_name = sched.patient_name

    # Use first name only on printed handout — no MRN
    first_name = (patient_name or 'Patient').split()[0] if patient_name else 'Patient'

    # Build gap list with plain-English info
    handout_gaps = []
    for g in gaps:
        rule = CareGapRule.query.filter_by(gap_type=g.gap_type).first()
        interval_text = ''
        if rule and rule.interval_days:
            if rule.interval_days >= 3650:
                interval_text = f"Every {rule.interval_days // 365} years"
            elif rule.interval_days >= 365:
                years = rule.interval_days // 365
                interval_text = f"Every {years} year{'s' if years > 1 else ''}"
            elif rule.interval_days > 0:
                interval_text = f"Every {rule.interval_days} days"
            else:
                interval_text = "One-time"

        age_range = ''
        if rule and rule.criteria_json:
            try:
                criteria = json.loads(rule.criteria_json)
                min_a = criteria.get('min_age', '')
                max_a = criteria.get('max_age', '')
                if min_a and max_a and max_a < 999:
                    age_range = f"Ages {min_a}\u2013{max_a}"
                elif min_a:
                    age_range = f"Ages {min_a}+"
            except (json.JSONDecodeError, TypeError):
                pass

        freq_note = ' \u00b7 '.join(filter(None, [interval_text, age_range]))

        if g.is_addressed:
            status = 'Up to Date'
            status_class = 'green'
        elif g.due_date and g.due_date < datetime.now(timezone.utc):
            status = 'Overdue'
            status_class = 'red'
        else:
            status = 'Due'
            status_class = 'yellow'

        handout_gaps.append({
            'name': g.gap_name or g.gap_type.replace('_', ' ').title(),
            'status': status,
            'status_class': status_class,
            'freq_note': freq_note,
            'description': g.description or '',
        })

    return render_template(
        'caregap_print_handout.html',
        first_name=first_name,
        provider_name=getattr(current_user, 'full_name', '') or current_user.username,
        visit_date=date.today().strftime('%B %d, %Y'),
        gaps=handout_gaps,
    )


# ======================================================================
# POST /caregap/<mrn>/address/<gap_id> — Mark gap as addressed (F15b)
# ======================================================================
@caregap_bp.route('/caregap/<mrn>/address/<int:gap_id>', methods=['POST'])
@login_required
def address_gap(mrn, gap_id):
    """
    Mark a care gap as addressed.  Returns the documentation snippet
    for the provider to copy.  Updates the gap record with completion info.
    """
    gap = CareGap.query.filter_by(
        id=gap_id, user_id=current_user.id, mrn=mrn
    ).first()

    if not gap:
        flash('Care gap not found.', 'warning')
        return redirect(url_for('caregap.patient_gaps', mrn=mrn))

    # Get the documentation template from the rule
    rule = CareGapRule.query.filter_by(gap_type=gap.gap_type).first()
    doc_template = rule.documentation_template if rule else ''

    # Allow custom snippet override from form
    custom_snippet = request.form.get('documentation_snippet', '').strip()
    snippet = custom_snippet if custom_snippet else doc_template

    gap.is_addressed = True
    gap.status = 'addressed'
    gap.completed_date = datetime.now(timezone.utc)
    gap.addressed_by = current_user.id
    gap.documentation_snippet = snippet
    db.session.commit()

    # If AJAX request, return JSON with snippet
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'snippet': snippet,
            'gap_id': gap_id,
            'gap_name': gap.gap_name,
        })

    flash(f'{gap.gap_name} marked as addressed.', 'success')
    return redirect(url_for('caregap.patient_gaps', mrn=mrn))


# ======================================================================
# POST /caregap/<mrn>/status/<gap_id> — Update gap status
# ======================================================================
@caregap_bp.route('/caregap/<mrn>/status/<int:gap_id>', methods=['POST'])
@login_required
def update_gap_status(mrn, gap_id):
    """Update status: decline, reopen, mark not applicable."""
    gap = CareGap.query.filter_by(
        id=gap_id, user_id=current_user.id, mrn=mrn
    ).first()

    if not gap:
        flash('Care gap not found.', 'warning')
        return redirect(url_for('caregap.patient_gaps', mrn=mrn))

    new_status = request.form.get('status', 'open')
    if new_status not in ('open', 'declined', 'not_applicable'):
        new_status = 'open'

    gap.status = new_status
    if new_status in ('declined', 'not_applicable'):
        gap.is_addressed = True
        gap.completed_date = datetime.now(timezone.utc)
        gap.addressed_by = current_user.id
    else:
        gap.is_addressed = False
        gap.completed_date = None

    db.session.commit()
    flash(f'{gap.gap_name} status updated to {new_status.replace("_", " ")}.', 'info')
    return redirect(url_for('caregap.patient_gaps', mrn=mrn))


# ======================================================================
# GET /caregap/panel — Panel-wide gap summary (F15c)
# ======================================================================
@caregap_bp.route('/caregap/panel')
@login_required
def panel_report():
    """
    Panel-wide gap summary: which gaps are most prevalent across the
    provider's entire patient panel.  Sorted by worst coverage first.
    """
    # Age/sex filters
    min_age = request.args.get('min_age', type=int)
    max_age = request.args.get('max_age', type=int)
    sex_filter = request.args.get('sex', '').strip().lower()
    claimed_only = request.args.get('claimed', '').strip().lower() == '1'

    # Get all open (unaddressed) gaps for this user
    query = CareGap.query.filter_by(
        user_id=current_user.id,
        is_addressed=False,
    )
    open_gaps = query.all()

    # Get total addressed gaps for coverage calculation
    addressed_gaps = CareGap.query.filter_by(
        user_id=current_user.id,
        is_addressed=True,
    ).all()

    # Apply patient-level filters if needed (uses Schedule/PatientRecord for demographics)
    if min_age is not None or max_age is not None or sex_filter:
        open_gaps = _filter_gaps_by_demographics(
            open_gaps, min_age, max_age, sex_filter
        )

    # Filter to claimed patients only if requested
    if claimed_only:
        claimed_mrns = {
            r.mrn for r in
            PatientRecord.query.filter(
                PatientRecord.user_id == current_user.id,
                PatientRecord.claimed_by.isnot(None),
            ).all()
        }
        open_gaps = [g for g in open_gaps if g.mrn in claimed_mrns]
        addressed_gaps = [g for g in addressed_gaps if g.mrn in claimed_mrns]

    # Group by gap_type and count
    gap_summary = {}
    for g in open_gaps:
        if g.gap_type not in gap_summary:
            gap_summary[g.gap_type] = {
                'gap_type': g.gap_type,
                'gap_name': g.gap_name or g.gap_type,
                'due_count': 0,
                'patients': set(),
            }
        gap_summary[g.gap_type]['due_count'] += 1
        gap_summary[g.gap_type]['patients'].add(g.mrn)

    # Count addressed per type for coverage %
    addressed_by_type = {}
    for g in addressed_gaps:
        addressed_by_type.setdefault(g.gap_type, set()).add(g.mrn)

    # Build final summary with coverage %
    summary_list = []
    for gt, info in gap_summary.items():
        total_patients = len(info['patients']) + len(addressed_by_type.get(gt, set()))
        covered = len(addressed_by_type.get(gt, set()))
        coverage_pct = round(covered / total_patients * 100) if total_patients > 0 else 0
        summary_list.append({
            'gap_type': gt,
            'gap_name': info['gap_name'],
            'due_count': info['due_count'],
            'patient_count': len(info['patients']),
            'total_in_panel': total_patients,
            'covered_count': covered,
            'coverage_pct': coverage_pct,
        })

    # Sort by worst coverage first (lowest %), then by most patients due
    summary_list.sort(key=lambda x: (x['coverage_pct'], -x['due_count']))

    # Unique patient count
    all_mrns = set()
    for g in open_gaps:
        all_mrns.add(g.mrn)

    # ---- Spreadsheet view data ----
    # Gather ALL gaps (open + addressed) to build patient × gap-type matrix
    all_gaps = open_gaps + addressed_gaps
    gap_types_ordered = sorted({g.gap_type for g in all_gaps})
    gap_names_map = {}
    for g in all_gaps:
        gap_names_map[g.gap_type] = g.gap_name or g.gap_type

    # Build per-patient row: {mrn, name, mrn_display, cells: {gap_type: status}}
    patient_map = {}  # mrn -> info dict
    for g in all_gaps:
        if g.mrn not in patient_map:
            patient_map[g.mrn] = {
                'mrn': g.mrn,
                'name': g.patient_name or '',
                'mrn_display': ('••' + g.mrn[-4:]) if len(g.mrn) >= 4 else g.mrn,
                'cells': {},
            }
        # Pick the most significant status per gap_type for this patient
        existing = patient_map[g.mrn]['cells'].get(g.gap_type)
        status = g.status or ('addressed' if g.is_addressed else 'open')
        # Priority: open > declined > not_applicable > addressed
        priority = {'open': 0, 'declined': 1, 'not_applicable': 2, 'addressed': 3}
        if existing is None or priority.get(status, 9) < priority.get(existing, 9):
            patient_map[g.mrn]['cells'][g.gap_type] = status

    spreadsheet_rows = sorted(patient_map.values(), key=lambda r: r['name'].lower())

    # ---- Claimed-only spreadsheet (always computed for dedicated tab) ----
    claimed_mrns = {
        r.mrn for r in
        PatientRecord.query.filter(
            PatientRecord.user_id == current_user.id,
            PatientRecord.claimed_by.isnot(None),
        ).all()
    }
    claimed_spreadsheet_rows = [r for r in spreadsheet_rows if r['mrn'] in claimed_mrns]

    return render_template(
        'caregap_panel.html',
        summary=summary_list,
        total_open_gaps=len(open_gaps),
        unique_patients=len(all_mrns),
        min_age=min_age,
        max_age=max_age,
        sex_filter=sex_filter,
        # Spreadsheet data
        gap_types=gap_types_ordered,
        gap_names_map=gap_names_map,
        spreadsheet_rows=spreadsheet_rows,
        claimed_spreadsheet_rows=claimed_spreadsheet_rows,
        claimed_only=claimed_only,
    )


# ======================================================================
# GET /caregap/panel/csv — CSV export of the spreadsheet view
# ======================================================================
@caregap_bp.route('/caregap/panel/csv')
@login_required
def panel_csv():
    """Export the panel gap spreadsheet as CSV."""
    import csv
    import io

    claimed_only = request.args.get('claimed', '').strip().lower() == '1'

    # Build the same data as the panel report
    all_gaps = CareGap.query.filter_by(user_id=current_user.id).all()

    if claimed_only:
        claimed_mrns = {
            r.mrn for r in
            PatientRecord.query.filter(
                PatientRecord.user_id == current_user.id,
                PatientRecord.claimed_by.isnot(None),
            ).all()
        }
        all_gaps = [g for g in all_gaps if g.mrn in claimed_mrns]

    gap_types_ordered = sorted({g.gap_type for g in all_gaps})
    gap_names_map = {}
    for g in all_gaps:
        gap_names_map[g.gap_type] = g.gap_name or g.gap_type

    patient_map = {}
    for g in all_gaps:
        if g.mrn not in patient_map:
            patient_map[g.mrn] = {
                'name': g.patient_name or g.mrn,
                'mrn': g.mrn,
                'cells': {},
            }
        status = g.status or ('addressed' if g.is_addressed else 'open')
        existing = patient_map[g.mrn]['cells'].get(g.gap_type)
        priority = {'open': 0, 'declined': 1, 'not_applicable': 2, 'addressed': 3}
        if existing is None or priority.get(status, 9) < priority.get(existing, 9):
            patient_map[g.mrn]['cells'][g.gap_type] = status

    rows = sorted(patient_map.values(), key=lambda r: r['name'].lower())

    output = io.StringIO()
    writer = csv.writer(output)
    header = ['Patient', 'MRN'] + [gap_names_map.get(gt, gt) for gt in gap_types_ordered]
    writer.writerow(header)
    for row in rows:
        writer.writerow(
            [row['name'], row['mrn']]
            + [row['cells'].get(gt, '') for gt in gap_types_ordered]
        )

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=care_gap_panel.csv'}
    )


# ======================================================================
# GET /caregap/panel/outreach — Outreach list for a specific gap type
# ======================================================================
@caregap_bp.route('/caregap/panel/outreach')
@login_required
def outreach_list():
    """
    Generate a list of patients due for a specific screening.
    Patient identifiers only in the UI (MRN last 4).
    CSV export includes full names from the gap records.
    """
    gap_type = request.args.get('gap_type', '')
    export = request.args.get('export', '') == 'csv'

    if not gap_type:
        flash('Please select a gap type for the outreach list.', 'warning')
        return redirect(url_for('caregap.panel_report'))

    gaps = (
        CareGap.query
        .filter_by(
            user_id=current_user.id,
            gap_type=gap_type,
            is_addressed=False,
        )
        .order_by(CareGap.patient_name)
        .all()
    )

    gap_name = gaps[0].gap_name if gaps else gap_type

    if export:
        # CSV export with full names for MA use
        lines = ['Patient Name,MRN,Gap,Status,Created']
        for g in gaps:
            lines.append(
                f'"{g.patient_name}",{g.mrn},'
                f'"{g.gap_name}",{g.status},'
                f'{g.created_at.strftime("%Y-%m-%d") if g.created_at else ""}'
            )
        csv_content = '\n'.join(lines)
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=outreach_{gap_type}.csv'
            },
        )

    return render_template(
        'caregap_outreach.html',
        gaps=gaps,
        gap_type=gap_type,
        gap_name=gap_name,
    )


# ======================================================================
# JSON API: GET /caregap/api/patient-gaps/<mrn>
# ======================================================================
@caregap_bp.route('/caregap/api/patient-gaps/<mrn>')
@login_required
def api_patient_gaps(mrn):
    """Return JSON gap data for inline dashboard expansion (F15a)."""
    gaps = (
        CareGap.query
        .filter_by(user_id=current_user.id, mrn=mrn, is_addressed=False)
        .order_by(CareGap.gap_name)
        .all()
    )
    return jsonify([
        {
            'id': g.id,
            'gap_type': g.gap_type,
            'gap_name': g.gap_name or g.gap_type,
            'description': g.description or '',
            'billing_code': g.billing_code_suggested or '',
            'status': g.status,
        }
        for g in gaps
    ])


# ======================================================================
# Helpers
# ======================================================================
def _filter_gaps_by_demographics(gaps, min_age, max_age, sex_filter):
    """Filter a list of CareGap objects by patient demographics."""
    from agent.caregap_engine import _calculate_age
    from models.schedule import Schedule

    if not (min_age is not None or max_age is not None or sex_filter):
        return gaps

    # Build MRN -> demographics lookup from schedule + patient record data
    from models.patient import PatientRecord
    mrns = list({g.mrn for g in gaps})
    demographics = {}
    for mrn in mrns:
        sched = Schedule.query.filter_by(patient_mrn=mrn).order_by(
            Schedule.appointment_date.desc()
        ).first()
        if sched and sched.patient_dob:
            age = _calculate_age(sched.patient_dob)
            demographics[mrn] = {'age': age, 'dob': sched.patient_dob, 'sex': ''}

        # Get sex from PatientRecord (most authoritative source)
        pr = PatientRecord.query.filter_by(mrn=mrn).first()
        if pr and pr.patient_sex:
            if mrn in demographics:
                demographics[mrn]['sex'] = (pr.patient_sex or '').strip().upper()
            elif pr.patient_sex:
                demographics[mrn] = {'age': None, 'dob': '', 'sex': (pr.patient_sex or '').strip().upper()}

    filtered = []
    for g in gaps:
        demo = demographics.get(g.mrn, {})
        age = demo.get('age')
        sex = demo.get('sex', '')

        if min_age is not None and age is not None and age < min_age:
            continue
        if max_age is not None and age is not None and age > max_age:
            continue
        if sex_filter and sex and sex_filter.strip().upper() != sex:
            continue

        filtered.append(g)

    return filtered

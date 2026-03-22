"""
CareCompanion — Clinical Intelligence API Routes
File: routes/intelligence.py

JSON API endpoints that power the Phase 10 intelligence layer widgets.
All endpoints return JSON and are called asynchronously from the patient
chart and dashboard templates.  No PHI is sent to external APIs — only
drug names, ICD-10 codes, and LOINC codes.

Features powered by this module:
- NEW-A: Drug Recall Alert System
- NEW-C: PubMed Guideline Lookup Panel
- NEW-D: Formulary Gap Detection
- NEW-E: Patient Education Auto-Draft
- NEW-F: Drug Safety Panel (interactions + recalls + monitoring)
- F22:   Morning Briefing data
"""

import asyncio
import json
import logging
from datetime import date, datetime, timezone

from flask import Blueprint, jsonify, request, render_template, current_app
from flask_login import login_required, current_user

from models import db
from models.patient import (
    PatientRecord, PatientMedication, PatientDiagnosis,
    PatientAllergy, PatientImmunization, RxNormCache,
)


def _parse_json_safe(text):
    """Parse a JSON string; return empty list on failure."""
    if not text:
        return []
    try:
        result = json.loads(text)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []
from models.schedule import Schedule

logger = logging.getLogger(__name__)

intel_bp = Blueprint('intelligence', __name__)


# ======================================================================
# Billing Opportunity Actions (capture / dismiss)
# ======================================================================
@intel_bp.route('/api/billing/opportunity/<int:opp_id>/capture', methods=['POST'])
@login_required
def capture_opportunity(opp_id):
    """Mark a billing opportunity as captured (provider documented and billed)."""
    from models.billing import BillingOpportunity, ClosedLoopStatus
    opp = BillingOpportunity.query.filter_by(
        id=opp_id, user_id=current_user.id
    ).first()
    if not opp:
        return jsonify({'success': False, 'error': 'Opportunity not found'}), 404
    # Phase 16.5: status validation — only pending/partial can be captured
    if opp.status not in ('pending', 'partial'):
        return jsonify({'success': False, 'error': f'Cannot capture: status is {opp.status}'}), 409
    # Phase 22.6: closed-loop funnel tracking — record 'accepted' stage
    last = ClosedLoopStatus.query.filter_by(opportunity_id=opp.id).order_by(ClosedLoopStatus.stage_date.desc()).first()
    entry = ClosedLoopStatus(
        opportunity_id=opp.id,
        patient_mrn_hash=opp.patient_mrn_hash,
        funnel_stage="accepted",
        stage_actor=current_user.display_name if hasattr(current_user, 'display_name') else str(current_user.id),
        stage_notes="Captured via billing widget",
        previous_stage=last.funnel_stage if last else "surfaced",
    )
    db.session.add(entry)
    opp.mark_captured()
    db.session.commit()
    return jsonify({'success': True, 'status': opp.status})


@intel_bp.route('/api/billing/opportunity/<int:opp_id>/dismiss', methods=['POST'])
@login_required
def dismiss_opportunity(opp_id):
    """Dismiss a billing opportunity with an optional reason."""
    from models.billing import BillingOpportunity, ClosedLoopStatus
    data = request.get_json(silent=True) or {}
    opp = BillingOpportunity.query.filter_by(
        id=opp_id, user_id=current_user.id
    ).first()
    if not opp:
        return jsonify({'success': False, 'error': 'Opportunity not found'}), 404
    # Phase 16.5: status validation — only pending/partial can be dismissed
    if opp.status not in ('pending', 'partial'):
        return jsonify({'success': False, 'error': f'Cannot dismiss: status is {opp.status}'}), 409
    # Phase 16.5: sanitize and cap reason length
    reason = str(data.get('reason', ''))[:500]
    # Phase 22.6: closed-loop funnel tracking — record 'dismissed' stage
    last = ClosedLoopStatus.query.filter_by(opportunity_id=opp.id).order_by(ClosedLoopStatus.stage_date.desc()).first()
    entry = ClosedLoopStatus(
        opportunity_id=opp.id,
        patient_mrn_hash=opp.patient_mrn_hash,
        funnel_stage="dismissed",
        stage_actor=current_user.display_name if hasattr(current_user, 'display_name') else str(current_user.id),
        stage_notes=reason or "Dismissed via billing widget",
        previous_stage=last.funnel_stage if last else "surfaced",
    )
    db.session.add(entry)
    opp.dismiss(reason=reason)
    db.session.commit()
    return jsonify({'success': True, 'status': opp.status})


# ======================================================================
# Care Gap Dismiss (Phase 14)
# ======================================================================
@intel_bp.route('/api/caregap/<int:gap_id>/dismiss', methods=['POST'])
@login_required
def dismiss_caregap(gap_id):
    """Dismiss a care gap with an optional reason."""
    from models.caregap import CareGap
    data = request.get_json(silent=True) or {}
    gap = CareGap.query.filter_by(id=gap_id, user_id=current_user.id).first()
    if not gap:
        return jsonify({'success': False, 'error': 'Care gap not found'}), 404
    gap.status = 'declined'
    gap.dismissal_reason = data.get('reason', '') or 'Dismissed by provider'
    gap.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({'success': True, 'status': gap.status})


@intel_bp.route('/api/patient/<mrn>/billing-opportunities')
@login_required
def patient_billing(mrn):
    """Return billing opportunities for a specific patient (for chart widget)."""
    import re as _re
    from models.billing import BillingOpportunity
    from utils import safe_patient_id
    # Phase 16.5: sanitize MRN input — allow only alphanumeric + hyphen, max 20 chars
    if not mrn or not _re.match(r'^[A-Za-z0-9\-]{1,20}$', mrn):
        return jsonify({'opportunities': []})
    try:
        mrn_hash = safe_patient_id(mrn)
    except ValueError:
        return jsonify({'opportunities': []})

    opps = BillingOpportunity.query.filter(
        BillingOpportunity.user_id == current_user.id,
        BillingOpportunity.patient_mrn_hash == mrn_hash,
        BillingOpportunity.status.in_(['pending', 'partial']),
    ).order_by(BillingOpportunity.expected_net_dollars.desc().nullslast(), BillingOpportunity.estimated_revenue.desc()).all()

    return jsonify({
        'opportunities': [{
            'id': o.id,
            'type': o.opportunity_type,
            'category': o.category or o.opportunity_type,
            'opportunity_code': o.opportunity_code or o.opportunity_type,
            'codes': o.applicable_codes,
            'revenue': o.estimated_revenue or 0,
            'net_value': o.expected_net_dollars,
            'confidence': o.confidence_level,
            'priority': o.priority or 'medium',
            'basis': o.eligibility_basis or '',
            'documentation': o.documentation_required or '',
            'insurer_caveat': o.insurer_caveat or '',
            'checklist': _parse_json_safe(o.documentation_checklist),
            'modifier': o.modifier or '',
        } for o in opps]
    })


@intel_bp.route('/api/patient/<mrn>/billing-stack')
@login_required
def patient_billing_stack(mrn):
    """Return visit stack recommendation for a patient (Phase 20.2)."""
    import re as _re
    from models.billing import BillingOpportunity, StaffRoutingRule
    from utils import safe_patient_id
    from billing_engine.stack_builder import VisitStackBuilder

    if not mrn or not _re.match(r'^[A-Za-z0-9\\-]{1,20}$', mrn):
        return jsonify({'stack': None})
    try:
        mrn_hash = safe_patient_id(mrn)
    except ValueError:
        return jsonify({'stack': None})

    visit_type = request.args.get('visit_type', 'chronic_longitudinal')
    duration = request.args.get('duration', type=int)

    opps = BillingOpportunity.query.filter(
        BillingOpportunity.user_id == current_user.id,
        BillingOpportunity.patient_mrn_hash == mrn_hash,
        BillingOpportunity.status.in_(['pending', 'partial']),
    ).all()

    builder = VisitStackBuilder()
    stack = builder.build_stack({}, {}, visit_type, opps, encounter_duration=duration)

    # Attach staff routing to each item
    routing_lookup = {}
    codes = [i['opportunity_code'] for i in stack['items']]
    if codes:
        rules = StaffRoutingRule.query.filter(
            StaffRoutingRule.opportunity_code.in_(codes)
        ).all()
        for r in rules:
            routing_lookup.setdefault(r.opportunity_code, []).append({
                'role': r.responsible_role,
                'task': r.prep_task_description,
                'timing': r.timing,
            })

    for item in stack['items']:
        item['staff_routing'] = routing_lookup.get(item['opportunity_code'], [])

    return jsonify({'stack': stack, 'templates': builder.get_available_templates()})


# ======================================================================
# Clinical Spell Check / Fuzzy Matcher
# ======================================================================
@intel_bp.route('/api/spell-check', methods=['POST'])
@login_required
def spell_check():
    """
    Analyze free text for medical terminology issues: abbreviations,
    misspellings, drug name fuzzy matches, diagnosis fuzzy matches.
    Returns findings with confidence scores for provider review.
    """
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    use_api = data.get('use_api', True)

    if not text:
        return jsonify({'findings': []})

    try:
        from app.services.clinical_spell_check import analyze_text
        min_conf = 0.6
        if current_user.is_authenticated:
            min_conf = float(current_user.get_pref('spell_check_confidence', 0.6))
        findings = analyze_text(text, use_api=use_api, min_confidence=min_conf)
        return jsonify({
            'findings': findings,
            'total': len(findings),
            'high_confidence': len([f for f in findings if f['confidence'] >= 0.85]),
            'needs_review': len([f for f in findings if min_conf <= f['confidence'] < 0.85]),
        })
    except Exception as e:
        logger.debug('Spell check failed: %s', e)
        return jsonify({'findings': [], 'error': str(e)})


@intel_bp.route('/api/spell-check/expand', methods=['POST'])
@login_required
def spell_check_expand():
    """Expand a single medical abbreviation."""
    data = request.get_json(silent=True) or {}
    abbrev = (data.get('abbreviation') or '').strip()
    if not abbrev:
        return jsonify({'expansion': None})

    from app.services.clinical_spell_check import expand_abbreviation
    expansion = expand_abbreviation(abbrev)
    return jsonify({'abbreviation': abbrev, 'expansion': expansion})


# ======================================================================
# Post-Visit Billing Review
# ======================================================================
@intel_bp.route('/billing/review/<mrn>')
@login_required
def billing_review(mrn):
    """Post-visit billing review for a specific patient."""
    from models.billing import BillingOpportunity

    opportunities = (
        BillingOpportunity.query
        .filter_by(user_id=current_user.id)
        .filter(BillingOpportunity.patient_mrn_hash.like(f'%{mrn[-6:]}%') if len(mrn) > 6 else BillingOpportunity.patient_mrn_hash != '')
        .order_by(BillingOpportunity.visit_date.desc())
        .limit(20)
        .all()
    )

    record = PatientRecord.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).first()

    return render_template(
        'billing_review.html',
        mrn=mrn,
        record=record,
        opportunities=opportunities,
    )


# ======================================================================
# 19E.3 — Monthly Billing Opportunity Report
# ======================================================================
@intel_bp.route('/billing/opportunity-report')
@login_required
def billing_opportunity_report():
    """Monthly report: detected vs captured vs dismissed by category."""
    from models.billing import BillingOpportunity
    from sqlalchemy import func, extract

    month_str = request.args.get('month', '')
    try:
        rpt_year, rpt_month = int(month_str[:4]), int(month_str[5:7])
    except (ValueError, IndexError):
        rpt_year, rpt_month = datetime.now().year, datetime.now().month

    start = datetime(rpt_year, rpt_month, 1, tzinfo=timezone.utc)
    if rpt_month == 12:
        end = datetime(rpt_year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(rpt_year, rpt_month + 1, 1, tzinfo=timezone.utc)

    opps = BillingOpportunity.query.filter(
        BillingOpportunity.user_id == current_user.id,
        BillingOpportunity.visit_date >= start,
        BillingOpportunity.visit_date < end,
    ).all()

    # Aggregate by category / status
    categories = {}
    totals = {'detected': 0, 'captured': 0, 'dismissed': 0,
              'rev_captured': 0, 'rev_missed': 0}
    for o in opps:
        cat = o.category or o.opportunity_type or 'other'
        if cat not in categories:
            categories[cat] = {'detected': 0, 'captured': 0, 'dismissed': 0,
                               'rev_captured': 0, 'rev_missed': 0}
        rev = o.estimated_revenue or 0
        categories[cat]['detected'] += 1
        totals['detected'] += 1
        if o.status == 'captured':
            categories[cat]['captured'] += 1
            categories[cat]['rev_captured'] += rev
            totals['captured'] += 1
            totals['rev_captured'] += rev
        elif o.status == 'dismissed':
            categories[cat]['dismissed'] += 1
            categories[cat]['rev_missed'] += rev
            totals['dismissed'] += 1
            totals['rev_missed'] += rev
        else:
            categories[cat]['rev_missed'] += rev
            totals['rev_missed'] += rev

    # 6-month trend
    trend = []
    for offset in range(5, -1, -1):
        m = rpt_month - offset
        y = rpt_year
        while m <= 0:
            m += 12
            y -= 1
        t_start = datetime(y, m, 1, tzinfo=timezone.utc)
        if m == 12:
            t_end = datetime(y + 1, 1, 1, tzinfo=timezone.utc)
        else:
            t_end = datetime(y, m + 1, 1, tzinfo=timezone.utc)
        month_opps = BillingOpportunity.query.filter(
            BillingOpportunity.user_id == current_user.id,
            BillingOpportunity.visit_date >= t_start,
            BillingOpportunity.visit_date < t_end,
        ).all()
        cap = sum(1 for o in month_opps if o.status == 'captured')
        det = len(month_opps)
        rev_cap = sum((o.estimated_revenue or 0) for o in month_opps if o.status == 'captured')
        trend.append({
            'label': f'{y}-{m:02d}',
            'detected': det,
            'captured': cap,
            'revenue': round(rev_cap),
        })

    # Top 5 by revenue opportunity
    top5 = sorted(categories.items(), key=lambda x: x[1]['rev_captured'] + x[1]['rev_missed'], reverse=True)[:5]

    return render_template(
        'billing_opportunity_report.html',
        year=rpt_year,
        month=rpt_month,
        categories=categories,
        totals=totals,
        trend=trend,
        top5=top5,
    )


# ======================================================================
# F31: Note Template Builder
# ======================================================================
@intel_bp.route('/reformatter/template')
@login_required
def reformatter_template():
    """Note template builder — drag-drop section ordering."""
    return render_template('reformatter_template.html')


@intel_bp.route('/api/save-note-template', methods=['POST'])
@login_required
def save_note_template():
    """Save user's custom note template to preferences."""
    data = request.get_json(silent=True) or {}
    template = data.get('template', {})
    if template:
        import json as _json
        current_user.set_pref('note_template', _json.dumps(template))
        db.session.commit()
    return jsonify({'success': True})


# ======================================================================
# F31: Note Reformatter Wizard (full pipeline)
# ======================================================================
@intel_bp.route('/reformatter')
@login_required
def reformatter():
    """Note Reformatter wizard — paste text, parse, classify, review, output."""
    return render_template('reformatter.html')


@intel_bp.route('/api/reformat-note', methods=['POST'])
@login_required
def api_reformat_note():
    """
    Complete reformatter pipeline: parse → classify → template fill.
    Returns filled note, flagged items, and coverage stats.
    """
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    use_api = data.get('use_api', False)

    if not text:
        return jsonify({'error': 'No text provided'})

    try:
        from agent.note_reformatter import reformat_note
        result = reformat_note(text, use_api=use_api)
        return jsonify(result)
    except Exception as e:
        logger.debug('Reformat failed: %s', e)
        return jsonify({'error': str(e)})


@intel_bp.route('/api/reformat-note/resolve-flag', methods=['POST'])
@login_required
def resolve_flag():
    """
    Resolve a flagged item from the reformatter:
    action = 'add_to_section' | 'keep_as_text' | 'discard'
    """
    data = request.get_json(silent=True) or {}
    # This endpoint exists for the audit trail — the actual text
    # manipulation happens client-side. We log the decision.
    action = data.get('action', '')
    flagged_text = data.get('text', '')
    section = data.get('section', '')

    if action == 'discard':
        # Log discarded items for audit trail
        from models.reformatter import ReformatLog
        logger.info(
            'Reformatter: user %s discarded flagged item from section %s: %s',
            current_user.id, section, flagged_text[:100]
        )

    return jsonify({'success': True, 'action': action})


# ======================================================================
# F31 Step 2: Note Section Parser (standalone, no AC dependency)
# ======================================================================
@intel_bp.route('/api/parse-note', methods=['POST'])
@login_required
def parse_note():
    """
    Parse free text into clinical note sections.
    Used by the Note Reformatter wizard and the spell check feature.
    """
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()

    if not text:
        return jsonify({'sections': {}, 'summary': 'No text provided'})

    try:
        from agent.note_parser import parse_note_sections, get_section_summary
        parsed = parse_note_sections(text)
        summary = get_section_summary(parsed)

        # Extract metadata before returning
        meta = parsed.pop('_metadata', {})
        needs_review = parsed.pop('needs_review', [])
        unclassified = parsed.pop('unclassified_text', '')

        return jsonify({
            'sections': parsed,
            'unclassified_text': unclassified,
            'needs_review': needs_review,
            'metadata': meta,
            'summary': summary,
        })
    except Exception as e:
        logger.debug('Note parse failed: %s', e)
        return jsonify({'sections': {}, 'error': str(e)})


# ======================================================================
# Scheduling Intelligence — AWV/CCM eligibility analysis
# ======================================================================
@intel_bp.route('/api/scheduling-intelligence')
@login_required
def scheduling_intelligence():
    """
    Analyze the provider's patient panel for scheduling opportunities:
    - AWV candidates: Medicare patients with >12 months since last AWV
    - CCM candidates: Patients with 2+ chronic conditions not enrolled in CCM
    Returns lists of patients who should be scheduled.
    """
    from app.api_config import CCM_CHRONIC_CONDITION_PREFIXES

    claimed = PatientRecord.query.filter_by(
        claimed_by=current_user.id
    ).all()

    if not claimed:
        return jsonify({'awv_candidates': [], 'ccm_candidates': [], 'total_panel': 0})

    awv_candidates = []
    ccm_candidates = []

    for record in claimed:
        mrn = record.mrn
        diagnoses = PatientDiagnosis.query.filter_by(
            user_id=current_user.id, mrn=mrn, status='active'
        ).all()

        icd_codes = [d.icd10_code or '' for d in diagnoses]

        # AWV check: any patient with insurer_type containing 'medicare'
        insurer = (getattr(record, 'insurer_type', '') or '').lower()
        if 'medicare' in insurer or not insurer:
            last_awv = getattr(record, 'last_awv_date', None)
            months_since = None
            if last_awv:
                from datetime import date as _d
                delta = _d.today() - last_awv
                months_since = delta.days / 30.44
            if last_awv is None or (months_since and months_since >= 11):
                awv_candidates.append({
                    'mrn': mrn,
                    'name': record.patient_name or 'Unknown',
                    'months_since_awv': round(months_since, 1) if months_since else None,
                    'reason': 'No AWV on record' if not last_awv else f'{round(months_since, 0):.0f} months since last AWV',
                })

        # CCM check: 2+ chronic conditions
        chronic_count = 0
        chronic_names = []
        for code in icd_codes:
            for prefix in CCM_CHRONIC_CONDITION_PREFIXES:
                if code.upper().startswith(prefix):
                    chronic_count += 1
                    dx = next((d for d in diagnoses if d.icd10_code == code), None)
                    if dx:
                        chronic_names.append(dx.diagnosis_name or code)
                    break

        ccm_enrolled = getattr(record, 'ccm_enrolled', False)
        if chronic_count >= 2 and not ccm_enrolled:
            ccm_candidates.append({
                'mrn': mrn,
                'name': record.patient_name or 'Unknown',
                'chronic_count': chronic_count,
                'conditions': chronic_names[:5],
                'reason': f'{chronic_count} chronic conditions — CCM eligible',
            })

    return jsonify({
        'awv_candidates': awv_candidates[:20],
        'ccm_candidates': ccm_candidates[:20],
        'total_panel': len(claimed),
    })


# ======================================================================
# API Setup Guide (accessible to all authenticated users)
# ======================================================================
@intel_bp.route('/api-setup-guide')
@login_required
def api_setup_guide():
    """Display the provider-facing API setup instructions."""
    return render_template('api_setup_guide.html')


# ======================================================================
# F17b: ICD-10 Specificity Reminder
# ======================================================================
@intel_bp.route('/api/icd10/specificity')
@login_required
def icd10_specificity():
    """
    Check if an ICD-10 code has more specific child codes available.
    Returns child codes if the current code is non-terminal.
    """
    code = request.args.get('code', '').strip().upper()
    if not code or len(code) < 3:
        return jsonify({'has_children': False, 'children': []})

    try:
        from app.services.api.icd10 import ICD10Service
        svc = ICD10Service(db)
        children = svc.get_children(code)
        if children:
            return jsonify({
                'has_children': True,
                'code': code,
                'children': children[:10],
                'message': f'More specific code available for {code}',
            })
        return jsonify({'has_children': False, 'code': code, 'children': []})
    except Exception as e:
        logger.debug('ICD-10 specificity check failed: %s', e)
        return jsonify({'has_children': False, 'children': []})


# ======================================================================
# LOINC Lab Reference Range Lookup
# ======================================================================
@intel_bp.route('/api/loinc/lookup')
@login_required
def loinc_lookup():
    """Look up LOINC code properties including reference ranges."""
    code = request.args.get('code', '').strip()
    if not code:
        return jsonify({'error': 'No LOINC code provided'})

    try:
        from app.services.api.loinc import LOINCService
        from app.api_config import LOINC_USERNAME, LOINC_PASSWORD
        svc = LOINCService(db, username=LOINC_USERNAME, password=LOINC_PASSWORD)
        result = svc.lookup_code(code)
        return jsonify(result or {'error': 'Code not found'})
    except Exception as e:
        logger.debug('LOINC lookup failed for %s: %s', code, e)
        return jsonify({'error': 'LOINC service unavailable'})


# ======================================================================
# NEW-B: Abnormal Lab Interpretation Assistant
# ======================================================================
@intel_bp.route('/api/patient/<mrn>/lab-interpretation')
@login_required
def lab_interpretation(mrn):
    """
    Return lab interpretation context: LOINC reference ranges and
    medication cross-reference for abnormal values.
    """
    from models.labtrack import LabTrack

    tracks = LabTrack.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).all()

    if not tracks:
        return jsonify({'interpretations': []})

    medications = PatientMedication.query.filter_by(
        user_id=current_user.id, mrn=mrn, status='active'
    ).all()
    # Build expanded match set: full name, first word, and rxnorm_cui
    med_names = set()
    rxcuis = []
    for m in medications:
        if m.drug_name:
            med_names.add(m.drug_name.lower())
            med_names.add(m.drug_name.split()[0].lower())
        if m.rxnorm_cui:
            med_names.add(m.rxnorm_cui.strip())
            rxcuis.append(m.rxnorm_cui.strip())

    # 14.5: Enrich with therapeutic class names from RxClassCache
    if rxcuis:
        from models.api_cache import RxClassCache
        class_rows = RxClassCache.query.filter(
            RxClassCache.rxcui.in_(rxcuis)
        ).all()
        for row in class_rows:
            if row.class_name:
                med_names.add(row.class_name.lower())

    interpretations = []
    for track in tracks:
        # Get latest result
        latest = None
        if track.results:
            sorted_results = sorted(track.results, key=lambda r: r.result_date or datetime.min, reverse=True)
            latest = sorted_results[0] if sorted_results else None

        if not latest or not latest.result_value:
            continue

        # Try to parse numeric value
        try:
            value = float(latest.result_value.replace(',', '').strip())
        except (ValueError, TypeError):
            continue

        interp = {
            'lab_name': track.lab_name,
            'value': latest.result_value,
            'date': latest.result_date.strftime('%m/%d/%Y') if latest.result_date else '',
            'status': track.status,
            'is_abnormal': False,
            'direction': '',
            'context': '',
            'reference_range': '',
            'drug_context': [],
        }

        # Check against provider-set thresholds
        if track.alert_low and value < track.alert_low:
            interp['is_abnormal'] = True
            interp['direction'] = 'low'
        elif track.alert_high and value > track.alert_high:
            interp['is_abnormal'] = True
            interp['direction'] = 'high'
        elif track.critical_low and value < track.critical_low:
            interp['is_abnormal'] = True
            interp['direction'] = 'critically low'
        elif track.critical_high and value > track.critical_high:
            interp['is_abnormal'] = True
            interp['direction'] = 'critically high'

        if track.alert_low or track.alert_high:
            lo = str(track.alert_low) if track.alert_low else ''
            hi = str(track.alert_high) if track.alert_high else ''
            interp['reference_range'] = f"{lo} – {hi}"

        # Cross-reference with medications for abnormal labs
        if interp['is_abnormal']:
            # Common lab-medication associations
            LAB_DRUG_ASSOCIATIONS = {
                'potassium': ['lisinopril', 'losartan', 'enalapril', 'spironolactone', 'trimethoprim'],
                'creatinine': ['lisinopril', 'losartan', 'ibuprofen', 'naproxen', 'metformin'],
                'glucose': ['metformin', 'glipizide', 'insulin', 'prednisone', 'dexamethasone'],
                'hemoglobin a1c': ['metformin', 'glipizide', 'insulin', 'semaglutide', 'empagliflozin'],
                'a1c': ['metformin', 'glipizide', 'insulin', 'semaglutide', 'empagliflozin'],
                'tsh': ['levothyroxine', 'liothyronine', 'amiodarone', 'lithium'],
                'alt': ['atorvastatin', 'rosuvastatin', 'simvastatin', 'methotrexate', 'acetaminophen'],
                'ast': ['atorvastatin', 'rosuvastatin', 'simvastatin', 'methotrexate'],
                'inr': ['warfarin'],
                'platelets': ['warfarin', 'heparin', 'valproic acid'],
                'wbc': ['methotrexate', 'azathioprine', 'clozapine'],
                'sodium': ['hydrochlorothiazide', 'furosemide', 'carbamazepine', 'desmopressin'],
                'magnesium': ['omeprazole', 'pantoprazole', 'furosemide'],
                'lithium': ['lithium'],
                'digoxin': ['digoxin'],
            }

            lab_lower = track.lab_name.lower()
            for lab_key, drugs in LAB_DRUG_ASSOCIATIONS.items():
                if lab_key in lab_lower:
                    for drug in drugs:
                        if drug in med_names:
                            interp['drug_context'].append({
                                'drug': drug.title(),
                                'note': f"Patient is on {drug.title()} which can affect {track.lab_name} levels",
                            })

            if interp['drug_context']:
                interp['context'] = f"{track.lab_name} is {interp['direction']} — consider medication effect"
            else:
                interp['context'] = f"{track.lab_name} is {interp['direction']} — review clinical significance"

        if interp['is_abnormal'] or track.status in ('critical', 'overdue'):
            interpretations.append(interp)

    return jsonify({'interpretations': interpretations})


# ======================================================================
# NEW-A + NEW-F: Drug Safety Panel  (recalls + interactions + monitoring)
# ======================================================================
@intel_bp.route('/api/patient/<mrn>/drug-safety')
@login_required
def drug_safety(mrn):
    """
    Return combined drug safety data for a patient:
      - Active FDA recalls for their medications
      - Drug interaction flags from FDA labels
      - Monitoring requirements
    """
    medications = PatientMedication.query.filter_by(
        user_id=current_user.id, mrn=mrn, status='active'
    ).all()

    if not medications:
        return jsonify({'recalls': [], 'interactions': [], 'monitoring': []})

    drug_names = [m.drug_name.split()[0] for m in medications if m.drug_name]
    rxcuis = [m.rxnorm_cui for m in medications if getattr(m, 'rxnorm_cui', '')]

    recalls = []
    interactions = []
    monitoring = []

    # --- Recalls via OpenFDA ---
    try:
        from app.services.api.openfda_recalls import OpenFDARecallsService
        svc = OpenFDARecallsService(db)
        recall_results = svc.check_drug_list_for_recalls(drug_names)
        for r in recall_results:
            recalls.append({
                'drug_name': r.get('drug_name', ''),
                'reason': r.get('reason', ''),
                'classification': r.get('classification', ''),
                'priority': r.get('priority', 'low'),
                'status': r.get('status', ''),
                'recall_date': r.get('recall_initiation_date', ''),
            })
    except Exception as e:
        logger.debug('Recall check failed: %s', e)

    # --- Interactions via OpenFDA Labels ---
    try:
        from app.services.api.openfda_labels import OpenFDALabelsService
        label_svc = OpenFDALabelsService(db)
        # Check each medication's label for interaction warnings with other meds
        for med in medications:
            drug = med.drug_name.split()[0] if med.drug_name else ''
            if not drug:
                continue
            cui = getattr(med, 'rxnorm_cui', '') or ''
            try:
                label = label_svc.get_label_by_rxcui(cui) if cui else label_svc.get_label_by_name(drug)
                if not label:
                    continue
                interaction_text = label.get('drug_interactions', '')
                if interaction_text:
                    # Check if any OTHER active medication is mentioned
                    for other in medications:
                        if other.id == med.id:
                            continue
                        other_name = (other.drug_name or '').split()[0].lower()
                        if other_name and len(other_name) > 3 and other_name in interaction_text.lower():
                            interactions.append({
                                'drug_a': drug,
                                'drug_b': other_name.title(),
                                'detail': interaction_text[:300],
                                'severity': 'warning',
                            })

                # Monitoring requirements
                monitoring_text = label.get('warnings_and_cautions', '') or ''
                if any(kw in monitoring_text.lower() for kw in ['monitor', 'check', 'periodic', 'laboratory']):
                    monitoring.append({
                        'drug': drug,
                        'requirement': monitoring_text[:200],
                    })
            except Exception:
                continue
    except Exception as e:
        logger.debug('Label interaction check failed: %s', e)

    # --- REMS program alerts via DailyMed ---
    try:
        from app.services.api.dailymed import DailyMedService
        dm_svc = DailyMedService(db)
        for med in medications:
            drug = med.drug_name.split()[0] if med.drug_name else ''
            if not drug:
                continue
            try:
                rems = dm_svc.check_rems_program(drug)
                if rems.get('has_rems'):
                    monitoring.append({
                        'drug': drug,
                        'requirement': rems.get('rems_detail') or f'REMS program active for {drug} — additional safety monitoring required',
                        'source': 'DailyMed REMS',
                    })
            except Exception:
                continue
    except Exception as e:
        logger.debug('DailyMed REMS check failed: %s', e)

    # --- FAERS serious event stats ---
    faers_stats = []
    try:
        from app.services.api.openfda_adverse_events import OpenFDAAdverseEventsService
        faers_svc = OpenFDAAdverseEventsService(db)
        for med in medications[:5]:
            drug = med.drug_name.split()[0] if med.drug_name else ''
            if not drug:
                continue
            try:
                stats = faers_svc.get_serious_event_stats(drug)
                if stats.get('total_reports', 0) > 0:
                    faers_stats.append({
                        'drug': drug,
                        'serious_percentage': stats.get('serious_percentage', 0),
                        'total_reports': stats.get('total_reports', 0),
                        'top_age_group': stats['age_buckets'][0]['age_group'] if stats.get('age_buckets') else None,
                    })
            except Exception:
                continue
    except Exception as e:
        logger.debug('FAERS serious stats failed: %s', e)

    return jsonify({
        'recalls': recalls,
        'interactions': interactions,
        'monitoring': monitoring,
        'faers_stats': faers_stats,
        'drug_count': len(medications),
    })


# ======================================================================
# NEW-C: PubMed Guideline Lookup Panel
# ======================================================================
@intel_bp.route('/api/patient/<mrn>/guidelines')
@login_required
def guidelines(mrn):
    """
    Return recent PubMed clinical guidelines for the patient's
    top diagnoses. Results are cached per-diagnosis for 30 days.
    """
    diagnoses = PatientDiagnosis.query.filter_by(
        user_id=current_user.id, mrn=mrn, status='active'
    ).order_by(PatientDiagnosis.id.desc()).limit(5).all()

    if not diagnoses:
        return jsonify({'guidelines': [], 'conditions_searched': []})

    results = []
    conditions_searched = []

    try:
        from app.services.api.pubmed import PubMedService
        svc = PubMedService(db)

        for diag in diagnoses[:3]:  # Top 3 diagnoses
            name = diag.diagnosis_name or ''
            if not name or len(name) < 3:
                continue
            conditions_searched.append(name)
            articles = svc.search_guidelines_with_abstracts(name, max_results=3)
            for a in articles:
                results.append({
                    'condition': name,
                    'title': a.get('title', ''),
                    'journal': a.get('journal', ''),
                    'year': a.get('year', ''),
                    'authors': a.get('authors', ''),
                    'pmid': a.get('pmid', ''),
                    'doi': a.get('doi', ''),
                    'abstract': (a.get('abstract') or '')[:500],
                    'is_primary_care': a.get('is_primary_care_journal', False),
                })
    except Exception as e:
        logger.debug('PubMed guideline lookup failed: %s', e)

    return jsonify({
        'guidelines': results,
        'conditions_searched': conditions_searched,
    })


# ======================================================================
# NEW-D: Formulary Gap Detection
# ======================================================================
@intel_bp.route('/api/patient/<mrn>/formulary-gaps')
@login_required
def formulary_gaps(mrn):
    """
    Detect chronic conditions that lack expected medication classes.
    Compares active diagnoses against active medication classes.
    """
    diagnoses = PatientDiagnosis.query.filter_by(
        user_id=current_user.id, mrn=mrn, status='active'
    ).all()
    medications = PatientMedication.query.filter_by(
        user_id=current_user.id, mrn=mrn, status='active'
    ).all()

    if not diagnoses:
        return jsonify({'gaps': []})

    med_names_lower = set()
    rxcuis = []
    for m in medications:
        if m.drug_name:
            med_names_lower.add(m.drug_name.lower())
            # Also add first word (generic name often)
            med_names_lower.add(m.drug_name.split()[0].lower())
        if m.rxnorm_cui:
            med_names_lower.add(m.rxnorm_cui.strip())
            rxcuis.append(m.rxnorm_cui.strip())

    # 14.5: Enrich with therapeutic class names from RxClassCache
    med_class_names = set()
    if rxcuis:
        from models.api_cache import RxClassCache
        class_rows = RxClassCache.query.filter(
            RxClassCache.rxcui.in_(rxcuis)
        ).all()
        for row in class_rows:
            if row.class_name:
                med_names_lower.add(row.class_name.lower())
                med_class_names.add(row.class_name.lower())

    # --- Phase 17.1: RxClass API-driven therapeutic class matching ---
    # Try RxClass API first to get expected classes for each medication;
    # fall back to CONDITION_DRUG_MAP when API unavailable.
    rxclass_available = False
    rxcui_classes = {}  # rxcui → [class_name, ...]
    try:
        from app.services.api.rxnorm import RxNormService
        rxnorm_svc = RxNormService(db)
        for cui in rxcuis[:20]:  # Cap to avoid excessive API calls
            classes = rxnorm_svc.get_therapeutic_classes_for_rxcui(cui)
            if classes:
                rxclass_available = True
                rxcui_classes[cui] = [c.lower() for c in classes]
                for c in classes:
                    med_class_names.add(c.lower())
    except Exception as e:
        logger.debug('RxClass enrichment failed: %s', e)

    # Condition → expected drug class mappings (evidence-based defaults)
    CONDITION_DRUG_MAP = {
        'hypertension': {
            'icd_prefixes': ['I10', 'I11', 'I12', 'I13', 'I15'],
            'expected_classes': ['ACE inhibitor', 'ARB', 'calcium channel blocker', 'thiazide', 'beta blocker'],
            'drug_keywords': ['lisinopril', 'losartan', 'amlodipine', 'hydrochlorothiazide', 'metoprolol',
                              'enalapril', 'valsartan', 'olmesartan', 'nifedipine', 'atenolol',
                              'ramipril', 'irbesartan', 'diltiazem', 'chlorthalidone', 'carvedilol',
                              'benazepril', 'telmisartan', 'felodipine', 'bisoprolol',
                              'hctz', 'lisinopril-hctz', 'losartan-hctz', 'valsartan-hctz'],
        },
        'type 2 diabetes': {
            'icd_prefixes': ['E11'],
            'expected_classes': ['metformin', 'SGLT2 inhibitor', 'GLP-1 agonist', 'DPP-4 inhibitor', 'insulin', 'sulfonylurea'],
            'drug_keywords': ['metformin', 'empagliflozin', 'dapagliflozin', 'canagliflozin',
                              'semaglutide', 'liraglutide', 'dulaglutide', 'tirzepatide',
                              'sitagliptin', 'linagliptin', 'saxagliptin',
                              'glipizide', 'glyburide', 'glimepiride',
                              'insulin', 'jardiance', 'ozempic', 'mounjaro', 'farxiga', 'januvia',
                              'trulicity', 'wegovy', 'victoza',
                              'metformin-sitagliptin', 'metformin-glipizide'],
        },
        'hyperlipidemia': {
            'icd_prefixes': ['E78'],
            'expected_classes': ['statin', 'PCSK9 inhibitor', 'ezetimibe', 'fibrate'],
            'drug_keywords': ['atorvastatin', 'rosuvastatin', 'simvastatin', 'pravastatin',
                              'lovastatin', 'pitavastatin', 'ezetimibe', 'fenofibrate',
                              'lipitor', 'crestor', 'zetia', 'repatha', 'praluent',
                              'evolocumab', 'alirocumab', 'gemfibrozil',
                              'atorvastatin-ezetimibe', 'ezetimibe-simvastatin'],
        },
        'heart failure': {
            'icd_prefixes': ['I50'],
            'expected_classes': ['ACE inhibitor/ARB/ARNI', 'beta blocker', 'mineralocorticoid antagonist', 'SGLT2 inhibitor', 'diuretic'],
            'drug_keywords': ['lisinopril', 'losartan', 'sacubitril', 'entresto',
                              'carvedilol', 'metoprolol', 'bisoprolol',
                              'spironolactone', 'eplerenone',
                              'empagliflozin', 'dapagliflozin',
                              'furosemide', 'bumetanide', 'torsemide'],
        },
        'atrial fibrillation': {
            'icd_prefixes': ['I48'],
            'expected_classes': ['anticoagulant', 'rate control'],
            'drug_keywords': ['apixaban', 'rivaroxaban', 'warfarin', 'dabigatran', 'edoxaban',
                              'eliquis', 'xarelto', 'coumadin',
                              'metoprolol', 'diltiazem', 'digoxin', 'amiodarone'],
        },
        'hypothyroidism': {
            'icd_prefixes': ['E03'],
            'expected_classes': ['thyroid hormone'],
            'drug_keywords': ['levothyroxine', 'synthroid', 'liothyronine', 'armour thyroid',
                              'tirosint', 'cytomel', 'nature-throid'],
        },
        'GERD': {
            'icd_prefixes': ['K21'],
            'expected_classes': ['proton pump inhibitor', 'H2 blocker'],
            'drug_keywords': ['omeprazole', 'pantoprazole', 'lansoprazole', 'esomeprazole',
                              'rabeprazole', 'famotidine', 'ranitidine',
                              'prilosec', 'protonix', 'nexium', 'prevacid', 'pepcid'],
        },
        'asthma': {
            'icd_prefixes': ['J45'],
            'expected_classes': ['inhaled corticosteroid', 'SABA', 'LABA'],
            'drug_keywords': ['albuterol', 'fluticasone', 'budesonide', 'montelukast',
                              'ventolin', 'proair', 'advair', 'symbicort', 'breo',
                              'salmeterol', 'formoterol', 'mometasone', 'beclomethasone',
                              'hfa', 'inhaler'],
        },
        'COPD': {
            'icd_prefixes': ['J44'],
            'expected_classes': ['LAMA', 'LABA', 'inhaled corticosteroid', 'SABA'],
            'drug_keywords': ['tiotropium', 'umeclidinium', 'albuterol',
                              'spiriva', 'incruse', 'trelegy', 'breo', 'anoro',
                              'fluticasone', 'budesonide', 'symbicort'],
        },
        'depression': {
            'icd_prefixes': ['F32', 'F33'],
            'expected_classes': ['SSRI', 'SNRI', 'bupropion', 'TCA', 'atypical antidepressant'],
            'drug_keywords': ['sertraline', 'fluoxetine', 'escitalopram', 'citalopram', 'paroxetine',
                              'venlafaxine', 'duloxetine', 'desvenlafaxine', 'bupropion',
                              'mirtazapine', 'trazodone', 'amitriptyline',
                              'zoloft', 'prozac', 'lexapro', 'cymbalta', 'wellbutrin', 'effexor'],
        },
        'anxiety': {
            'icd_prefixes': ['F41'],
            'expected_classes': ['SSRI', 'SNRI', 'buspirone', 'hydroxyzine'],
            'drug_keywords': ['sertraline', 'escitalopram', 'fluoxetine', 'paroxetine',
                              'venlafaxine', 'duloxetine', 'buspirone', 'hydroxyzine',
                              'zoloft', 'lexapro', 'prozac', 'cymbalta', 'effexor'],
        },
        'osteoporosis': {
            'icd_prefixes': ['M80', 'M81'],
            'expected_classes': ['bisphosphonate', 'denosumab', 'calcium/vitamin D'],
            'drug_keywords': ['alendronate', 'risedronate', 'ibandronate', 'zoledronic',
                              'denosumab', 'prolia', 'fosamax', 'boniva', 'reclast',
                              'calcium', 'vitamin d', 'cholecalciferol', 'mvi'],
        },
    }

    gaps = []
    for diag in diagnoses:
        icd = (diag.icd10_code or '').upper()

        # --- Phase 17.1: Try RxClass API-driven gap detection first ---
        if rxclass_available:
            # Use RxClass: look up what conditions this diagnosis's meds
            # should treat, and see if the patient's med classes cover it
            diag_name_clean = (diag.diagnosis_name or '').lower()
            # Check if any of the patient's medication classes treat a
            # condition matching this diagnosis (via RxClass may_treat)
            treated_conditions = set()
            for cui, classes in rxcui_classes.items():
                for cls in classes:
                    treated_conditions.add(cls)
            # If a med class name appears that relates to this diagnosis
            # name or ICD prefix, consider it treated
            condition_match = False
            for condition, mapping in CONDITION_DRUG_MAP.items():
                if not any(icd.startswith(prefix) for prefix in mapping['icd_prefixes']):
                    continue
                # RxClass-enhanced check: compare med class names against
                # condition keywords + expected classes
                has_api_match = any(
                    ec.lower() in med_class_names
                    for ec in mapping['expected_classes']
                )
                has_keyword_match = any(
                    kw in name for kw in mapping['drug_keywords']
                    for name in med_names_lower
                )
                if not has_api_match and not has_keyword_match:
                    gaps.append({
                        'condition': condition.title(),
                        'diagnosis': diag.diagnosis_name,
                        'icd10': icd,
                        'expected_classes': mapping['expected_classes'],
                        'source': 'rxclass_enhanced',
                        'message': f"No {' / '.join(mapping['expected_classes'][:3])} found for {condition}",
                    })
                condition_match = True
                break
            if condition_match:
                continue

        # --- Fallback: hardcoded CONDITION_DRUG_MAP ---
        for condition, mapping in CONDITION_DRUG_MAP.items():
            if not any(icd.startswith(prefix) for prefix in mapping['icd_prefixes']):
                continue
            has_treatment = any(
                kw in name for kw in mapping['drug_keywords']
                for name in med_names_lower
            )
            if not has_treatment:
                gaps.append({
                    'condition': condition.title(),
                    'diagnosis': diag.diagnosis_name,
                    'icd10': icd,
                    'expected_classes': mapping['expected_classes'],
                    'source': 'hardcoded_fallback',
                    'message': f"No {' / '.join(mapping['expected_classes'][:3])} found for {condition}",
                })
            break  # Only match first condition per diagnosis

    return jsonify({'gaps': gaps})


# ======================================================================
# NEW-E: Patient Education Content
# ======================================================================
@intel_bp.route('/api/patient/<mrn>/education')
@login_required
def patient_education(mrn):
    """
    Return patient education content from MedlinePlus for the patient's
    active diagnoses and medications.
    """
    diagnoses = PatientDiagnosis.query.filter_by(
        user_id=current_user.id, mrn=mrn, status='active'
    ).limit(5).all()
    medications = PatientMedication.query.filter_by(
        user_id=current_user.id, mrn=mrn, status='active'
    ).limit(5).all()

    education = []
    try:
        from app.services.api.medlineplus import MedlinePlusService
        lang = current_user.get_pref('medlineplus_language', 'en')
        svc = MedlinePlusService(db, language=lang)

        # Education for top diagnoses
        for diag in diagnoses[:3]:
            icd = (diag.icd10_code or '').strip()
            if not icd:
                continue
            content = svc.get_for_icd10(icd)
            if content and content.get('title'):
                education.append({
                    'type': 'diagnosis',
                    'source_name': diag.diagnosis_name,
                    'title': content['title'],
                    'summary': content.get('summary', '')[:500],
                    'url': content.get('url', ''),
                    'language': content.get('language', 'en'),
                })

        # Education for medications
        for med in medications[:3]:
            cui = getattr(med, 'rxnorm_cui', '') or ''
            if not cui:
                continue
            content = svc.get_for_rxcui(cui)
            if content and content.get('title'):
                education.append({
                    'type': 'medication',
                    'source_name': med.drug_name,
                    'title': content['title'],
                    'summary': content.get('summary', '')[:500],
                    'url': content.get('url', ''),
                    'language': content.get('language', 'en'),
                })
    except Exception as e:
        logger.debug('Patient education fetch failed: %s', e)

    # --- DailyMed medication guides ---
    try:
        from app.services.api.dailymed import DailyMedService
        dm_svc = DailyMedService(db)
        for med in medications[:3]:
            drug = med.drug_name.split()[0] if med.drug_name else ''
            if not drug:
                continue
            try:
                label = dm_svc.get_drug_label(drug)
                if label.get('has_medication_guide') and label.get('setid'):
                    guide = dm_svc.get_medication_guide(label['setid'])
                    if guide.get('guide_url'):
                        education.append({
                            'type': 'medication_guide',
                            'source_name': med.drug_name,
                            'title': f"Medication Guide: {label.get('title') or drug}",
                            'summary': 'FDA-approved medication guide from the manufacturer.',
                            'url': guide['guide_url'],
                            'language': 'en',
                        })
            except Exception:
                continue
    except Exception as e:
        logger.debug('DailyMed medication guide fetch failed: %s', e)

    return jsonify({'education': education})


# ======================================================================
# Phase 27 — Education pricing paragraph helper
# ======================================================================
def _build_pricing_paragraph(drug_name):
    """
    Build a pricing information paragraph for a drug.
    Returns a string paragraph or empty string if no pricing found.
    Reusable by both send_education_to_patient (27.1) and Trigger 2 new-med
    detection (27.2).
    """
    if not drug_name:
        return ''
    try:
        from app.services.pricing_service import PricingService
        svc = PricingService(db)
        pricing = svc.get_pricing(
            rxcui=None, ndc=None,
            drug_name=drug_name.split()[0],
            strength=None,
        )
        parts = []
        if pricing.get('source') == 'cost_plus' and pricing.get('price_monthly_estimate') is not None:
            parts.append(
                f"Pricing information: This medication may be available at Cost Plus Drugs pharmacy "
                f"for approximately ${pricing['price_monthly_estimate']:.2f}/month. "
                f"Visit: {pricing.get('direct_url', 'https://costplusdrugs.com')}"
            )
        elif pricing.get('source') == 'goodrx' and pricing.get('price_monthly_estimate') is not None:
            parts.append(
                f"Pricing information: You may be able to save on this medication using a GoodRx discount. "
                f"Estimated price: ${pricing['price_monthly_estimate']:.2f}/month. "
                f"Visit: {pricing.get('direct_url', 'https://www.goodrx.com')}"
            )
        programs = pricing.get('assistance_programs') or []
        if programs:
            prog = programs[0]
            parts.append(
                f"Financial assistance may be available for this medication. "
                f"Visit {prog.get('application_url', '')} for eligibility information."
            )
        return '\n'.join(parts)
    except Exception:
        return ''


# ======================================================================
# Phase 10 — Trigger 2: Auto-draft education for new medications
# ======================================================================
def auto_draft_education_message(user_id, mrn, new_meds):
    """
    Create draft DelayedMessage records for each new medication detected.
    Called from clinical_summary_parser._trigger_new_med_education().
    Does NOT auto-send — creates drafts for provider review.

    Parameters
    ----------
    user_id : int
    mrn : str
    new_meds : list[dict]
        Each: {'drug_name': str, 'rxcui': str, 'start_date': str}

    Returns
    -------
    int
        Number of drafts created.
    """
    from models.message import DelayedMessage
    from models.notification import Notification

    if not new_meds:
        return 0

    record = PatientRecord.query.filter_by(user_id=user_id, mrn=mrn).first()
    recipient = record.patient_name if record and record.patient_name else mrn

    # Check for existing pending drafts to avoid duplicates
    existing_pending = DelayedMessage.query.filter_by(
        user_id=user_id, status='pending',
    ).all()
    existing_drug_names = set()
    for msg in existing_pending:
        content_lower = (msg.message_content or '').lower()
        if 'new medication education' in content_lower:
            # Extract drug name from "Regarding: <drug_name>" line
            for line in (msg.message_content or '').split('\n'):
                if line.startswith('Regarding: '):
                    existing_drug_names.add(line[len('Regarding: '):].strip().lower())

    drafts_created = 0
    for med in new_meds:
        drug_name = med.get('drug_name', '').strip()
        if not drug_name:
            continue
        # Skip if a draft already exists for this drug
        if drug_name.lower() in existing_drug_names:
            continue

        body_parts = [f"New Medication Education: {drug_name}"]
        body_parts.append(f"Regarding: {drug_name}")
        if med.get('start_date'):
            body_parts.append(f"Started: {med['start_date']}")

        # Append pricing paragraph
        pricing_para = _build_pricing_paragraph(drug_name)
        if pricing_para:
            body_parts.append(f"\n{pricing_para}")

        body_parts.append("\n— Auto-drafted by CareCompanion (review before sending)")

        draft = DelayedMessage(
            user_id=user_id,
            recipient_identifier=recipient,
            message_content="\n".join(body_parts),
            scheduled_send_at=datetime.now(timezone.utc),
            status='pending',
        )
        db.session.add(draft)
        drafts_created += 1

    if drafts_created > 0:
        # Create a notification for the provider (HIPAA-safe: MRN last 4 only)
        mrn_tail = mrn[-4:] if len(mrn) >= 4 else mrn
        notif = Notification(
            user_id=user_id,
            message=f"📋 {drafts_created} new medication education draft{'s' if drafts_created != 1 else ''} created for ••{mrn_tail}",
            priority=2,
        )
        db.session.add(notif)
        db.session.commit()

    return drafts_created


# ======================================================================
# NEW-E: Patient Education → Delayed Message Draft (Phase 13D)
# ======================================================================
@intel_bp.route('/api/patient/<mrn>/education/send', methods=['POST'])
@login_required
def send_education_to_patient(mrn):
    """
    Create a DelayedMessage draft with MedlinePlus education content.
    Expects JSON body: {title, summary, url, source_name}
    """
    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    summary = (data.get('summary') or '').strip()
    url = (data.get('url') or '').strip()
    source_name = (data.get('source_name') or '').strip()

    if not title:
        return jsonify({'error': 'Education title is required'}), 400

    # Build message body
    body_parts = [f"Patient Education: {title}"]
    if source_name:
        body_parts.append(f"Regarding: {source_name}")
    if summary:
        body_parts.append(f"\n{summary}")
    if url:
        body_parts.append(f"\nMore information: {url}")

    # --- Pricing information paragraph (Phase 27.1) ---
    pricing_para = _build_pricing_paragraph(source_name)
    if pricing_para:
        body_parts.append(f"\n{pricing_para}")

    body_parts.append("\n\n— Sent via CareCompanion")

    message_content = "\n".join(body_parts)

    # Look up patient name for recipient
    record = PatientRecord.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).first()
    recipient = record.patient_name if record and record.patient_name else mrn

    from models.message import DelayedMessage
    draft = DelayedMessage(
        user_id=current_user.id,
        recipient_identifier=recipient,
        message_content=message_content,
        scheduled_send_at=datetime.now(timezone.utc),
        status='pending',
    )
    db.session.add(draft)
    db.session.commit()

    return jsonify({'ok': True, 'message_id': draft.id, 'redirect': '/messages'})


# ======================================================================
# NEW-G: Clinical Trials Widget
# ======================================================================
@intel_bp.route('/api/patient/<mrn>/clinical-trials')
@login_required
def clinical_trials(mrn):
    """
    Return recruiting clinical trials near the practice that match the
    patient's active diagnoses, age, and sex.
    """
    diagnoses = PatientDiagnosis.query.filter_by(
        user_id=current_user.id, mrn=mrn, status='active'
    ).limit(5).all()

    if not diagnoses:
        return jsonify({'trials': [], 'conditions_searched': []})

    conditions = [d.icd10_code for d in diagnoses if d.icd10_code]
    if not conditions:
        return jsonify({'trials': [], 'conditions_searched': []})

    # Get patient demographics for eligibility filtering
    record = PatientRecord.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).first()
    age = None
    sex = None
    if record:
        if hasattr(record, 'date_of_birth') and record.date_of_birth:
            from datetime import date
            try:
                dob = record.date_of_birth
                if isinstance(dob, str):
                    dob = date.fromisoformat(dob)
                age = (date.today() - dob).days // 365
            except Exception:
                pass
        if hasattr(record, 'sex'):
            sex = record.sex

    trials = []
    try:
        from app.services.api.clinical_trials import ClinicalTrialsService
        svc = ClinicalTrialsService(db)
        trials = svc.search_for_patient(conditions, age=age, sex=sex)
    except Exception as e:
        logger.debug('Clinical trials fetch failed: %s', e)

    return jsonify({
        'trials': trials,
        'conditions_searched': conditions[:5],
    })


# ======================================================================
# F22: Morning Briefing
# ======================================================================
@intel_bp.route('/briefing')
@login_required
def morning_briefing():
    """
    Morning Briefing page — aggregates weather, schedule overview,
    recall alerts, care gap summary, and guideline pre-loads.
    """
    today = date.today()

    # Schedule overview
    appointments = Schedule.query.filter_by(
        user_id=current_user.id, appointment_date=today
    ).order_by(Schedule.appointment_time).all()

    # Weather
    weather = {}
    forecast = {}
    air_quality = {}
    try:
        from app.services.api.open_meteo import OpenMeteoService
        weather_svc = OpenMeteoService(db)
        weather = weather_svc.get_current_conditions() or {}
        forecast = weather_svc.get_7day_forecast() or {}
        air_quality = weather_svc.get_air_quality() or {}
    except Exception as e:
        logger.debug('Weather fetch failed: %s', e)

    # Recall alerts across all active medications for this provider's patients
    recall_alerts = []
    try:
        from app.services.api.openfda_recalls import OpenFDARecallsService
        recall_svc = OpenFDARecallsService(db)
        # Get unique drug names across all claimed patients
        med_names = [
            row[0] for row in
            db.session.query(PatientMedication.drug_name)
            .filter(
                PatientMedication.user_id == current_user.id,
                PatientMedication.status == 'active',
            )
            .distinct().limit(50).all()
            if row[0]
        ]
        if med_names:
            drug_first_words = list(set(n.split()[0] for n in med_names if n))
            results = recall_svc.check_drug_list_for_recalls(drug_first_words)
            recall_alerts = [r for r in results if r.get('priority') in ('critical', 'high')]
    except Exception as e:
        logger.debug('Briefing recall check failed: %s', e)

    # Care gap summary
    from models.caregap import CareGap
    open_gaps = CareGap.query.filter_by(
        user_id=current_user.id, is_addressed=False
    ).all()
    gap_count = len(open_gaps)

    # Claimed patient count
    claimed_count = PatientRecord.query.filter_by(
        claimed_by=current_user.id
    ).count()

    # Phase 12: P3 morning-only notifications
    p3_notifications = []
    try:
        from models.notification import Notification
        p3_notifications = (
            Notification.query
            .filter_by(user_id=current_user.id, priority=3, is_read=False)
            .order_by(Notification.created_at.desc())
            .limit(20)
            .all()
        )
    except Exception as e:
        logger.debug('P3 notification query failed: %s', e)

    # F4c: Schedule anomaly analysis — overlap count for briefing
    from routes.dashboard import analyze_schedule_anomalies
    anomalies = analyze_schedule_anomalies(appointments)
    overlap_count = sum(1 for a in anomalies if a.get('type') == 'schedule_overlap')

    # F25a: PDMP overdue count for briefing
    pdmp_overdue_count = 0
    try:
        from routes.tools import get_overdue_pdmp_patients
        pdmp_overdue_count = len(get_overdue_pdmp_patients(current_user.id))
    except Exception:
        pass

    # Phase 17.8: Bonus projection for morning briefing
    bonus_status = None
    bonus_proj = None
    try:
        from models.bonus import BonusTracker
        from app.services.bonus_calculator import current_quarter_status, project_first_bonus_quarter
        tracker = BonusTracker.query.filter_by(user_id=current_user.id).first()
        if tracker:
            bonus_status = current_quarter_status(tracker)
            receipts = tracker.get_receipts()
            if receipts:
                from routes.bonus import _build_deficit_history
                deficit_history = _build_deficit_history(
                    receipts, tracker.quarterly_threshold or 105000.0,
                    tracker.deficit_resets_annually)
                current_deficit = deficit_history[-1]["cumulative_deficit"] if deficit_history else 0.0
                bonus_proj = project_first_bonus_quarter(
                    receipts, tracker.quarterly_threshold or 105000.0,
                    deficit=current_deficit, growth_rate=0.0,
                    deficit_resets_annually=tracker.deficit_resets_annually,
                    start_year=today.year, start_quarter=(today.month - 1) // 3 + 1)
    except Exception as e:
        logger.debug('Bonus briefing data failed: %s', e)

    # Phase 23.D3: Monitoring due — labs due within 30 days for tomorrow's patients
    monitoring_due = []
    monitoring_rems = []
    monitoring_due_count = 0
    try:
        from models.monitoring import MonitoringSchedule, REMSTrackerEntry
        from billing_engine.shared import hash_mrn
        from datetime import timedelta

        tomorrow = today + timedelta(days=1)
        cutoff = today + timedelta(days=30)

        # Get MRNs for tomorrow's scheduled patients
        tomorrow_appts = Schedule.query.filter_by(
            user_id=current_user.id, appointment_date=tomorrow
        ).all()
        tomorrow_mrns = [a.patient_mrn for a in tomorrow_appts if a.patient_mrn]

        for mrn in tomorrow_mrns:
            mrn_hash = hash_mrn(mrn)
            entries = (
                MonitoringSchedule.query
                .filter_by(patient_mrn_hash=mrn_hash, status='active')
                .filter(MonitoringSchedule.next_due_date <= cutoff)
                .order_by(MonitoringSchedule.next_due_date.asc())
                .all()
            )
            for e in entries:
                monitoring_due.append({
                    'mrn_display': f'...{mrn[-4:]}' if mrn else '????',
                    'lab_name': e.lab_name,
                    'next_due_date': str(e.next_due_date) if e.next_due_date else '',
                    'clinical_indication': e.clinical_indication or '',
                    'priority': e.priority,
                    'overdue': e.next_due_date < today if e.next_due_date else False,
                    'triggering_medication': e.triggering_medication or '',
                    'triggering_condition': e.triggering_condition or '',
                })

            # REMS entries
            rems = REMSTrackerEntry.query.filter_by(
                patient_mrn_hash=mrn_hash, status='active'
            ).all()
            for r in rems:
                monitoring_rems.append({
                    'mrn_display': f'...{mrn[-4:]}' if mrn else '????',
                    'rems_program_name': r.rems_program_name,
                    'next_due_date': str(r.next_due_date) if r.next_due_date else '',
                    'escalation_level': r.escalation_level,
                })

        monitoring_due_count = len(monitoring_due)
    except Exception as e:
        logger.debug('Monitoring briefing data failed: %s', e)

    # ── Phase 24.4 — Immunization series gaps for tomorrow's patients ──
    imm_gaps = []
    imm_seasonal = []
    try:
        from app.services.immunization_engine import get_series_gaps, get_seasonal_alerts
        from billing_engine.shared import hash_mrn as _hash_mrn_imm
        from datetime import timedelta as _td_imm

        tomorrow_imm = today + _td_imm(days=1)
        tomorrow_appts_imm = Schedule.query.filter_by(
            user_id=current_user.id, appointment_date=tomorrow_imm
        ).all()
        for appt in tomorrow_appts_imm:
            mrn = appt.patient_mrn
            if not mrn:
                continue
            mrn_hash = _hash_mrn_imm(mrn)
            pr = PatientRecord.query.filter_by(mrn=mrn, claimed_by=current_user.id).first()
            age = pr.age if pr and pr.age else 0
            gaps = get_series_gaps(mrn_hash, current_user.id, age, today)
            for g in gaps:
                g['mrn_display'] = f'...{mrn[-4:]}' if mrn else '????'
                imm_gaps.append(g)
            seasonal = get_seasonal_alerts(age, today)
            for s in seasonal:
                s['mrn_display'] = f'...{mrn[-4:]}' if mrn else '????'
                imm_seasonal.append(s)
    except Exception as e:
        logger.debug('Immunization briefing data failed: %s', e)

    # Phase 32.5 — Risk score alerts for tomorrow's scheduled patients (counts only, no PHI)
    risk_score_alerts = {'bmi_obese3': 0, 'prevent_high': 0, 'ldl_190_plus': 0}
    try:
        from models.calculator import CalculatorResult
        from datetime import timedelta as _td_rs
        tomorrow_rs = today + _td_rs(days=1)
        tomorrow_appts_rs = Schedule.query.filter_by(
            user_id=current_user.id, appointment_date=tomorrow_rs,
        ).all()
        for appt_rs in tomorrow_appts_rs:
            mrn_rs = appt_rs.patient_mrn
            if not mrn_rs:
                continue
            scores = CalculatorResult.query.filter_by(
                user_id=current_user.id, mrn=mrn_rs, is_current=True,
            ).all()
            for s in scores:
                if s.calculator_key == 'bmi' and s.score_label == 'obesity_class_3':
                    risk_score_alerts['bmi_obese3'] += 1
                elif s.calculator_key == 'prevent' and s.score_value is not None and s.score_value >= 10:
                    risk_score_alerts['prevent_high'] += 1
                elif s.calculator_key == 'ldl' and s.score_value is not None and s.score_value >= 190:
                    risk_score_alerts['ldl_190_plus'] += 1
    except Exception as e:
        logger.debug('Risk score briefing data failed: %s', e)

    # Phase 35.5 — Score changes since last visit for tomorrow's patients (no PHI)
    score_changes = []
    try:
        from app.services.calculator_engine import CalculatorEngine as _CE
        _engine35 = _CE()
        _seen_mrns = set()
        for _appt in (tomorrow_appts_rs if 'tomorrow_appts_rs' in dir() else []):
            _mrn35 = getattr(_appt, 'patient_mrn', None)
            if not _mrn35 or _mrn35 in _seen_mrns:
                continue
            _seen_mrns.add(_mrn35)
            _changes = _engine35.detect_score_changes(_mrn35, current_user.id)
            for _ch in _changes:
                score_changes.append({
                    **_ch,
                    'mrn_display': f'...{_mrn35[-4:]}' if len(_mrn35) >= 4 else _mrn35,
                })
    except Exception as e:
        logger.debug('Score change detection failed: %s', e)

    return render_template(
        'morning_briefing.html',
        today=today,
        appointments=appointments,
        weather=weather,
        forecast=forecast,
        air_quality=air_quality,
        recall_alerts=recall_alerts,
        gap_count=gap_count,
        open_gaps=open_gaps[:10],
        claimed_count=claimed_count,
        appointment_count=len(appointments),
        p3_notifications=p3_notifications,
        overlap_count=overlap_count,
        pdmp_overdue_count=pdmp_overdue_count,
        bonus_status=bonus_status,
        bonus_proj=bonus_proj,
        monitoring_due=monitoring_due,
        monitoring_rems=monitoring_rems,
        monitoring_due_count=monitoring_due_count,
        imm_gaps=imm_gaps,
        imm_seasonal=imm_seasonal,
        risk_score_alerts=risk_score_alerts,
        score_changes=score_changes,
    )


# ======================================================================
# F22a: Commute Mode
# ======================================================================
@intel_bp.route('/briefing/commute')
@login_required
def commute_briefing():
    """
    Commute Mode — large-text, auto-read briefing for hands-free use.
    Gathers same data as morning briefing with emphasis on commute weather.
    Uses Web Speech API for text-to-speech.
    """
    today = date.today()

    # Schedule overview
    appointments = Schedule.query.filter_by(
        user_id=current_user.id, appointment_date=today
    ).order_by(Schedule.appointment_time).all()

    # Weather with commute-specific data
    weather = {}
    forecast = {}
    air_quality = {}
    try:
        from app.services.api.open_meteo import OpenMeteoService
        weather_svc = OpenMeteoService(db)
        weather = weather_svc.get_current_conditions() or {}
        forecast = weather_svc.get_7day_forecast() or {}
        air_quality = weather_svc.get_air_quality() or {}
    except Exception as e:
        logger.debug('Commute weather fetch failed: %s', e)

    # Care gap summary
    from models.caregap import CareGap
    gap_count = CareGap.query.filter_by(
        user_id=current_user.id, is_addressed=False
    ).count()

    # Unread inbox count
    from models.inbox import InboxItem
    inbox_unread = InboxItem.query.filter_by(
        user_id=current_user.id, is_resolved=False
    ).count()

    # Phase 12: P3 morning-only notifications
    p3_notifications = []
    try:
        from models.notification import Notification
        p3_notifications = (
            Notification.query
            .filter_by(user_id=current_user.id, priority=3, is_read=False)
            .order_by(Notification.created_at.desc())
            .limit(20)
            .all()
        )
    except Exception as e:
        logger.debug('Commute P3 query failed: %s', e)

    return render_template(
        'commute_briefing.html',
        today=today,
        appointments=appointments,
        weather=weather,
        forecast=forecast,
        air_quality=air_quality,
        gap_count=gap_count,
        inbox_unread=inbox_unread,
        appointment_count=len(appointments),
        p3_notifications=p3_notifications,
    )


# ======================================================================
# Admin API Configuration
# ======================================================================
@intel_bp.route('/admin/api', methods=['GET', 'POST'])
@login_required
def admin_api_settings():
    """Admin page for managing API keys and cache."""
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin only'}), 403

    if request.method == 'POST':
        action = request.form.get('action', '')
        if action == 'flush_cache':
            api_name = request.form.get('api_name', '')
            if api_name:
                try:
                    from app.services.api.cache_manager import CacheManager
                    cache = CacheManager(db)
                    cache.flush_api(api_name)
                    from flask import flash
                    flash(f'Cache flushed for {api_name}.', 'success')
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error('Cache flush error: %s', e)
                    from flask import flash
                    flash('Cache flush failed. Check server logs for details.', 'danger')

    # Get cache stats
    cache_stats = {}
    try:
        from app.services.api.cache_manager import CacheManager
        cache = CacheManager(db)
        cache_stats = cache.get_all_api_stats()
    except Exception:
        pass

    return render_template(
        'admin_api.html',
        cache_stats=cache_stats,
    )


# ======================================================================
# Phase 7.1: VIIS Immunization Scraper Endpoint
# ======================================================================
@intel_bp.route('/api/patient/<mrn>/immunizations/viis')
@login_required
def viis_immunizations(mrn):
    """
    Query Virginia Immunization Information System for patient immunization records.
    Requires patient name and DOB from PatientRecord.
    """
    record = PatientRecord.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).first()
    if not record or not record.patient_name:
        return jsonify({'success': False, 'error': 'Patient record not found or missing name'}), 404

    # Parse patient name and DOB
    name = record.patient_name.strip()
    parts = name.split(',') if ',' in name else name.rsplit(' ', 1)
    if len(parts) >= 2:
        last_name = parts[0].strip()
        first_name = parts[1].strip().split()[0] if parts[1].strip() else ''
    else:
        last_name = name
        first_name = ''

    dob = (record.patient_dob or '').strip()
    if not first_name or not last_name or not dob:
        return jsonify({'success': False, 'error': 'Patient name or DOB incomplete'}), 400

    # Format DOB to MM/DD/YYYY if stored as YYYYMMDD
    if len(dob) == 8 and dob.isdigit():
        dob = f"{dob[4:6]}/{dob[6:8]}/{dob[:4]}"

    try:
        from scrapers.viis import VIISScraper
        scraper = VIISScraper(current_app._get_current_object())
        result = asyncio.run(scraper.lookup_patient(first_name, last_name, dob))
        return jsonify(result)
    except Exception as e:
        logger.debug('VIIS lookup failed for MRN %s: %s', mrn, e)
        return jsonify({'success': False, 'error': f'VIIS lookup failed: {e}'}), 503


# ======================================================================
# Phase 7.2: PDMP Controlled Substance Scraper Endpoint
# ======================================================================
@intel_bp.route('/api/patient/<mrn>/pdmp')
@login_required
def pdmp_lookup(mrn):
    """
    Query Virginia PDMP (Prescription Drug Monitoring Program) for patient's
    controlled substance prescriptions.
    """
    record = PatientRecord.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).first()
    if not record or not record.patient_name:
        return jsonify({'success': False, 'error': 'Patient record not found or missing name'}), 404

    # Parse patient name and DOB
    name = record.patient_name.strip()
    parts = name.split(',') if ',' in name else name.rsplit(' ', 1)
    if len(parts) >= 2:
        last_name = parts[0].strip()
        first_name = parts[1].strip().split()[0] if parts[1].strip() else ''
    else:
        last_name = name
        first_name = ''

    dob = (record.patient_dob or '').strip()
    if not first_name or not last_name or not dob:
        return jsonify({'success': False, 'error': 'Patient name or DOB incomplete'}), 400

    if len(dob) == 8 and dob.isdigit():
        dob = f"{dob[4:6]}/{dob[6:8]}/{dob[:4]}"

    try:
        from scrapers.pdmp import PDMPScraper
        scraper = PDMPScraper(current_app._get_current_object())
        result = asyncio.run(scraper.lookup_patient(first_name, last_name, dob))

        # Flag potential issues: other prescribers, high quantity
        prescriptions = result.get('prescriptions', [])
        flags = []
        seen_drugs = {}
        for rx in prescriptions:
            drug = (rx.get('drug_name') or '').lower()
            prescriber = rx.get('prescriber', '')
            if drug in seen_drugs and seen_drugs[drug] != prescriber:
                flags.append({
                    'type': 'multiple_prescribers',
                    'message': f"'{rx.get('drug_name')}' prescribed by multiple providers",
                    'severity': 'warning',
                })
            seen_drugs[drug] = prescriber

            days = int(rx.get('days_supply') or 0)
            if days > 90:
                flags.append({
                    'type': 'long_supply',
                    'message': f"'{rx.get('drug_name')}' has {days}-day supply",
                    'severity': 'info',
                })

        result['flags'] = flags
        return jsonify(result)
    except Exception as e:
        logger.debug('PDMP lookup failed for MRN %s: %s', mrn, e)
        return jsonify({'success': False, 'error': f'PDMP lookup failed: {e}'}), 503


# ======================================================================
# Phase 7.4: CMS Data Benchmark Endpoint
# ======================================================================
@intel_bp.route('/api/billing/benchmark')
@login_required
def billing_benchmark():
    """
    Return CMS utilization benchmarks for specified HCPCS codes.
    Query params: codes (comma-separated), state (default VA), specialty
    """
    codes_str = request.args.get('codes', '')
    state = request.args.get('state', 'VA')
    specialty = request.args.get('specialty', 'Nurse Practitioner')

    codes = [c.strip().upper() for c in codes_str.split(',') if c.strip()]
    if not codes:
        return jsonify({'benchmarks': [], 'error': 'No codes specified'})

    benchmarks = []
    try:
        from app.services.api.cms_data import CmsDataService
        svc = CmsDataService(db)
        for code in codes[:10]:  # Limit to 10 codes per request
            result = svc.get_benchmark(code, state=state, specialty=specialty)
            benchmarks.append(result)
    except Exception as e:
        logger.debug('CMS benchmark fetch failed: %s', e)

    return jsonify({'benchmarks': benchmarks, 'state': state, 'specialty': specialty})


# ======================================================================
# Phase 21.4: Documentation Phrase Library
# ======================================================================


@intel_bp.route('/settings/phrases')
@login_required
def phrase_settings():
    """Documentation phrase library — browse, search, copy, edit."""
    from models.billing import DocumentationPhrase

    phrases = DocumentationPhrase.query.filter_by(is_active=True).order_by(
        DocumentationPhrase.opportunity_code, DocumentationPhrase.phrase_category
    ).all()

    # Group by opportunity_code
    grouped = {}
    categories = set()
    category_counts = {}
    for p in phrases:
        grouped.setdefault(p.opportunity_code, []).append(p)
        categories.add(p.phrase_category)
        category_counts[p.phrase_category] = category_counts.get(p.phrase_category, 0) + 1

    return render_template(
        'phrase_settings.html',
        phrases=phrases,
        grouped=grouped,
        categories=sorted(categories),
        category_counts=category_counts,
    )


@intel_bp.route('/api/billing/phrase/<int:phrase_id>')
@login_required
def get_phrase(phrase_id):
    """Get single phrase for edit modal."""
    from models.billing import DocumentationPhrase
    p = DocumentationPhrase.query.get_or_404(phrase_id)
    return jsonify({
        "id": p.id,
        "opportunity_code": p.opportunity_code,
        "cpt_code": p.cpt_code,
        "phrase_category": p.phrase_category,
        "phrase_title": p.phrase_title,
        "phrase_text": p.phrase_text,
        "payer_specific": p.payer_specific,
        "clinical_context": p.clinical_context,
        "is_customized": p.is_customized,
    })


@intel_bp.route('/settings/phrases/<int:phrase_id>/edit', methods=['POST'])
@login_required
def edit_phrase(phrase_id):
    """Edit a documentation phrase. Marks as customized to survive re-seeds."""
    from models.billing import DocumentationPhrase
    from flask import redirect, url_for, flash

    p = DocumentationPhrase.query.get_or_404(phrase_id)
    title = request.form.get('phrase_title', '').strip()
    text = request.form.get('phrase_text', '').strip()

    if title and text:
        p.phrase_title = title
        p.phrase_text = text
        p.is_customized = True
        db.session.commit()
        flash('Phrase updated.', 'success')
    else:
        flash('Title and text are required.', 'error')

    return redirect(url_for('intelligence.phrase_settings'))


@intel_bp.route('/api/billing/phrases-for-code/<opportunity_code>')
@login_required
def phrases_for_code(opportunity_code):
    """Get all active phrases for a specific opportunity code (used by clipboard integration)."""
    from models.billing import DocumentationPhrase
    phrases = DocumentationPhrase.query.filter_by(
        opportunity_code=opportunity_code, is_active=True
    ).all()
    return jsonify({
        "phrases": [{
            "id": p.id,
            "title": p.phrase_title,
            "text": p.phrase_text,
            "category": p.phrase_category,
            "cpt_code": p.cpt_code,
        } for p in phrases]
    })


# ======================================================================
# Phase 22: Why-Not Explainability + Closed-Loop Tracking
# ======================================================================


@intel_bp.route('/billing/why-not/<mrn>')
@login_required
def billing_why_not(mrn):
    """Display suppressed opportunities with reasons — filterable page."""
    import re as _re
    from models.billing import OpportunitySuppression
    from utils import safe_patient_id

    if not mrn or not _re.match(r'^[A-Za-z0-9\-]{1,20}$', mrn):
        return render_template('billing_why_not.html', suppressions=[], grouped={}, reasons=set(), mrn=mrn)
    try:
        mrn_hash = safe_patient_id(mrn)
    except ValueError:
        return render_template('billing_why_not.html', suppressions=[], grouped={}, reasons=set(), mrn=mrn)

    supps = OpportunitySuppression.query.filter(
        OpportunitySuppression.user_id == current_user.id,
        OpportunitySuppression.patient_mrn_hash == mrn_hash,
    ).order_by(OpportunitySuppression.created_at.desc()).all()

    grouped = {}
    reasons = set()
    for s in supps:
        grouped.setdefault(s.suppression_reason, []).append(s)
        reasons.add(s.suppression_reason)

    return render_template('billing_why_not.html', suppressions=supps, grouped=grouped, reasons=reasons, mrn=mrn)


@intel_bp.route('/api/billing/why-not/<mrn>')
@login_required
def api_billing_why_not(mrn):
    """JSON endpoint: suppressed opportunities for a patient."""
    import re as _re
    from models.billing import OpportunitySuppression
    from utils import safe_patient_id

    if not mrn or not _re.match(r'^[A-Za-z0-9\-]{1,20}$', mrn):
        return jsonify({'suppressions': [], 'count': 0})
    try:
        mrn_hash = safe_patient_id(mrn)
    except ValueError:
        return jsonify({'suppressions': [], 'count': 0})

    supps = OpportunitySuppression.query.filter(
        OpportunitySuppression.user_id == current_user.id,
        OpportunitySuppression.patient_mrn_hash == mrn_hash,
    ).order_by(OpportunitySuppression.created_at.desc()).all()

    return jsonify({
        'suppressions': [{
            'id': s.id,
            'opportunity_code': s.opportunity_code,
            'reason': s.suppression_reason,
            'detail': s.detail,
            'visit_date': s.visit_date.isoformat() if s.visit_date else None,
            'created_at': s.created_at.isoformat() if s.created_at else None,
        } for s in supps],
        'count': len(supps),
    })


@intel_bp.route('/api/billing/opportunity/<int:opp_id>/funnel')
@login_required
def api_opportunity_funnel(opp_id):
    """JSON endpoint: closed-loop funnel history for an opportunity."""
    from models.billing import ClosedLoopStatus

    entries = ClosedLoopStatus.query.filter_by(
        opportunity_id=opp_id
    ).order_by(ClosedLoopStatus.stage_date.asc()).all()

    return jsonify({
        'stages': [{
            'id': e.id,
            'stage': e.funnel_stage,
            'date': e.stage_date.isoformat() if e.stage_date else None,
            'actor': e.stage_actor,
            'notes': e.stage_notes,
            'previous': e.previous_stage,
        } for e in entries],
        'count': len(entries),
    })


@intel_bp.route('/api/billing/opportunity/<int:opp_id>/transition', methods=['POST'])
@login_required
def api_opportunity_transition(opp_id):
    """Record a funnel stage transition for an opportunity."""
    from models.billing import ClosedLoopStatus, BillingOpportunity, FUNNEL_STAGES

    data = request.get_json(silent=True) or {}
    stage = data.get('stage', '').strip()
    if not stage or stage not in FUNNEL_STAGES:
        return jsonify({'success': False, 'error': 'Invalid funnel stage'}), 400

    opp = BillingOpportunity.query.get(opp_id)
    if not opp or opp.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Opportunity not found'}), 404

    # Find the last stage
    last = ClosedLoopStatus.query.filter_by(
        opportunity_id=opp_id
    ).order_by(ClosedLoopStatus.stage_date.desc()).first()

    entry = ClosedLoopStatus(
        opportunity_id=opp_id,
        patient_mrn_hash=opp.patient_mrn_hash,
        funnel_stage=stage,
        stage_actor=data.get('actor') or current_user.display_name if hasattr(current_user, 'display_name') else str(current_user.id),
        stage_notes=data.get('notes'),
        previous_stage=last.funnel_stage if last else None,
    )
    db.session.add(entry)
    db.session.commit()

    return jsonify({'success': True, 'stage_id': entry.id})


@intel_bp.route('/api/billing/leakage-summary')
@login_required
def api_leakage_summary():
    """Leakage attribution summary: classify stalls by category."""
    from models.billing import OpportunitySuppression

    supps = OpportunitySuppression.query.filter_by(
        user_id=current_user.id
    ).all()

    # Map suppression reasons to leakage categories
    leakage_map = {
        "chart_unsupported": "documentation_failure",
        "documentation_insufficient": "documentation_failure",
        "already_completed": "detection_gap",
        "external_result_on_file": "detection_gap",
        "payer_ineligible": "payer_behavior",
        "poor_expected_value": "payer_behavior",
        "excessive_denial_risk": "payer_behavior",
        "standalone_too_weak": "workflow_drop",
        "frequency_limit_reached": "workflow_drop",
        "provider_disabled_category": "provider_deferral",
        "age_ineligible": "detection_gap",
        "sex_ineligible": "detection_gap",
        "concurrent_conflict": "modifier_failure",
    }

    attribution = {}
    for s in supps:
        cat = leakage_map.get(s.suppression_reason, "workflow_drop")
        attribution[cat] = attribution.get(cat, 0) + 1

    return jsonify({
        'attribution': attribution,
        'total_suppressions': len(supps),
        'categories': list(attribution.keys()),
    })


# ======================================================================
# Phase 20.6: Staff Billing Tasks Route
# ======================================================================


@intel_bp.route('/staff/billing-tasks')
@login_required
def staff_billing_tasks():
    """Role-filtered daily billing task view."""
    from models.billing import StaffRoutingRule

    rules = StaffRoutingRule.query.order_by(
        StaffRoutingRule.timing, StaffRoutingRule.responsible_role
    ).all()

    # Group by timing
    grouped = {}
    role_counts = {}
    roles = set()
    for r in rules:
        grouped.setdefault(r.timing or 'daily', []).append(r)
        role_counts[r.responsible_role] = role_counts.get(r.responsible_role, 0) + 1
        roles.add(r.responsible_role)

    return render_template(
        'staff_billing_tasks.html',
        grouped=grouped,
        roles=sorted(roles),
        role_counts=role_counts,
    )


# ======================================================================
# Phase 19: TCM Discharge Watch Routes
# ======================================================================


@intel_bp.route('/tcm/watch-list')
@login_required
def tcm_watch_list():
    """TCM watch list: all active discharge entries with deadline tracking."""
    from models.tcm import TCMWatchEntry
    from datetime import timedelta

    entries = TCMWatchEntry.query.filter_by(
        user_id=current_user.id,
    ).order_by(TCMWatchEntry.discharge_date.desc()).all()

    today = date.today()
    watch_data = []
    for e in entries:
        # Deadline status color
        if e.status in ('completed', 'cancelled'):
            color = 'gray'
        elif e.two_day_deadline and not e.two_day_contact_completed and today >= e.two_day_deadline:
            color = 'red'
        elif e.fourteen_day_visit_deadline and not e.face_to_face_completed and today >= e.fourteen_day_visit_deadline:
            color = 'red'
        elif e.two_day_deadline and not e.two_day_contact_completed and (e.two_day_deadline - today).days <= 1:
            color = 'yellow'
        elif e.seven_day_visit_deadline and not e.face_to_face_completed and today >= e.seven_day_visit_deadline:
            color = 'yellow'
        else:
            color = 'green'

        # Days until next deadline
        next_deadline = None
        next_deadline_label = None
        if not e.two_day_contact_completed and e.two_day_deadline:
            next_deadline = e.two_day_deadline
            next_deadline_label = '2-day contact'
        elif not e.face_to_face_completed and e.seven_day_visit_deadline:
            next_deadline = e.seven_day_visit_deadline
            next_deadline_label = '7-day visit'
        elif not e.face_to_face_completed and e.fourteen_day_visit_deadline:
            next_deadline = e.fourteen_day_visit_deadline
            next_deadline_label = '14-day visit'

        days_remaining = (next_deadline - today).days if next_deadline else None

        watch_data.append({
            'entry': e,
            'color': color,
            'next_deadline': next_deadline,
            'next_deadline_label': next_deadline_label,
            'days_remaining': days_remaining,
            'is_billable': e.is_billable(),
        })

    return render_template(
        'tcm_watch.html',
        watch_data=watch_data,
        today=today,
    )


@intel_bp.route('/tcm/add-discharge', methods=['POST'])
@login_required
def tcm_add_discharge():
    """Add a new discharge to the TCM watch list."""
    import re as _re
    from models.tcm import TCMWatchEntry
    from utils import safe_patient_id

    mrn = (request.form.get('mrn') or '').strip()
    discharge_date_str = (request.form.get('discharge_date') or '').strip()
    facility = (request.form.get('facility') or '').strip()

    if not mrn or not _re.match(r'^[A-Za-z0-9\-]{1,20}$', mrn):
        return jsonify({'error': 'Invalid MRN'}), 400

    try:
        mrn_hash = safe_patient_id(mrn)
    except ValueError:
        return jsonify({'error': 'Invalid MRN'}), 400

    if not discharge_date_str:
        return jsonify({'error': 'Discharge date required'}), 400

    try:
        d_date = datetime.strptime(discharge_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format (use YYYY-MM-DD)'}), 400

    entry = TCMWatchEntry(
        patient_mrn_hash=mrn_hash,
        user_id=current_user.id,
        discharge_date=d_date,
        discharge_facility=facility[:200] if facility else None,
    )
    entry.compute_deadlines()

    db.session.add(entry)
    db.session.commit()

    return jsonify({'success': True, 'id': entry.id})


@intel_bp.route('/tcm/<int:entry_id>/log-contact', methods=['POST'])
@login_required
def tcm_log_contact(entry_id):
    """Log the 2-business-day contact for a TCM entry."""
    from models.tcm import TCMWatchEntry

    entry = TCMWatchEntry.query.filter_by(
        id=entry_id, user_id=current_user.id
    ).first()
    if not entry:
        return jsonify({'error': 'Entry not found'}), 404

    method = (request.form.get('method') or 'phone').strip()
    if method not in ('phone', 'portal', 'in_person'):
        method = 'phone'

    contact_date_str = request.form.get('contact_date')
    if contact_date_str:
        try:
            contact_date = datetime.strptime(contact_date_str, '%Y-%m-%d').date()
        except ValueError:
            contact_date = date.today()
    else:
        contact_date = date.today()

    entry.two_day_contact_completed = True
    entry.two_day_contact_date = contact_date
    entry.two_day_contact_method = method

    db.session.commit()
    return jsonify({'success': True})


@intel_bp.route('/tcm/<int:entry_id>/log-visit', methods=['POST'])
@login_required
def tcm_log_visit(entry_id):
    """Log the face-to-face visit for a TCM entry."""
    from models.tcm import TCMWatchEntry

    entry = TCMWatchEntry.query.filter_by(
        id=entry_id, user_id=current_user.id
    ).first()
    if not entry:
        return jsonify({'error': 'Entry not found'}), 404

    visit_date_str = request.form.get('visit_date')
    if visit_date_str:
        try:
            visit_date = datetime.strptime(visit_date_str, '%Y-%m-%d').date()
        except ValueError:
            visit_date = date.today()
    else:
        visit_date = date.today()

    entry.face_to_face_completed = True
    entry.face_to_face_date = visit_date
    entry.determine_tcm_code()

    db.session.commit()
    return jsonify({'success': True, 'tcm_code': entry.tcm_code_eligible})


@intel_bp.route('/tcm/<int:entry_id>/log-med-rec', methods=['POST'])
@login_required
def tcm_log_med_rec(entry_id):
    """Log medication reconciliation completion for a TCM entry."""
    from models.tcm import TCMWatchEntry

    entry = TCMWatchEntry.query.filter_by(
        id=entry_id, user_id=current_user.id
    ).first()
    if not entry:
        return jsonify({'error': 'Entry not found'}), 404

    entry.med_reconciliation_completed = True

    # Check if now billable
    if entry.is_billable():
        entry.status = 'completed'

    db.session.commit()
    return jsonify({'success': True, 'is_billable': entry.is_billable()})

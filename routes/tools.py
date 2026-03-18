"""
NP Companion — Tools Routes
File: routes/tools.py

Routes for the Tools module:
- F25: Controlled Substance Tracker (/cs-tracker)
- F17: ICD-10 Coding Helper (/coding)
- F26: Prior Authorization Generator (/pa)

Dependencies:
- models/tools.py (ControlledSubstanceEntry, CodeFavorite, CodePairing, PriorAuthorization)
- app/services/api/rxnorm.py (RxNormService)
- app/services/api/icd10.py (ICD10Service)
- app/services/api/rxclass.py (RxClassService)
"""

import json
import logging
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from models import db
from models.tools import (
    ControlledSubstanceEntry, CodeFavorite, CodePairing, PriorAuthorization,
    ReferralLetter,
)
from models.tickler import Tickler
from models.user import User

logger = logging.getLogger(__name__)

tools_bp = Blueprint('tools', __name__)


# ======================================================================
# Tools Hub
# ======================================================================
@tools_bp.route('/tools')
@login_required
def index():
    """Tools hub: links to all tool modules."""
    return render_template('tools.html')


# ======================================================================
# F25: Controlled Substance Tracker
# ======================================================================

@tools_bp.route('/cs-tracker')
@login_required
def cs_tracker():
    """Controlled substance registry with fill tracking."""
    entries = (
        ControlledSubstanceEntry.query
        .filter_by(user_id=current_user.id, is_active=True)
        .order_by(ControlledSubstanceEntry.next_fill_date)
        .all()
    )
    return render_template('cs_tracker.html', entries=entries)


@tools_bp.route('/cs-tracker/add', methods=['POST'])
@login_required
def cs_add():
    """Add a new controlled substance entry."""
    data = request.get_json(silent=True) or request.form

    drug_name = (data.get('drug_name') or '').strip()
    if not drug_name:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Drug name required'}), 400
        flash('Drug name is required.', 'error')
        return redirect(url_for('tools.cs_tracker'))

    entry = ControlledSubstanceEntry(
        user_id=current_user.id,
        mrn=(data.get('mrn') or '').strip(),
        patient_name=(data.get('patient_name') or '').strip(),
        drug_name=drug_name,
        dea_schedule=(data.get('dea_schedule') or '').strip(),
        dose=(data.get('dose') or '').strip(),
        quantity=int(data.get('quantity') or 0),
        days_supply=int(data.get('days_supply') or 30),
        pdmp_check_interval_days=int(data.get('pdmp_interval') or 90),
        uds_interval_days=int(data.get('uds_interval') or 180),
        notes=(data.get('notes') or '').strip(),
    )

    # Auto-lookup DEA schedule via RxNorm if not provided
    if not entry.dea_schedule:
        entry.dea_schedule = _lookup_dea_schedule(drug_name)

    # Set initial fill date if provided
    fill_str = (data.get('last_fill_date') or '').strip()
    if fill_str:
        try:
            entry.last_fill_date = date.fromisoformat(fill_str)
            entry.next_fill_date = entry.last_fill_date + timedelta(days=entry.days_supply)
        except ValueError:
            pass

    db.session.add(entry)
    db.session.commit()

    if request.is_json:
        return jsonify({'success': True, 'id': entry.id})
    flash(f'{drug_name} added to CS tracker.', 'success')
    return redirect(url_for('tools.cs_tracker'))


@tools_bp.route('/cs-tracker/<int:entry_id>/fill', methods=['POST'])
@login_required
def cs_fill(entry_id):
    """Record a new fill for a controlled substance entry."""
    entry = ControlledSubstanceEntry.query.filter_by(
        id=entry_id, user_id=current_user.id
    ).first()
    if not entry:
        return jsonify({'success': False, 'error': 'Entry not found'}), 404

    data = request.get_json(silent=True) or request.form
    fill_str = (data.get('fill_date') or '').strip()
    fill_date = date.fromisoformat(fill_str) if fill_str else date.today()
    days = int(data.get('days_supply') or entry.days_supply)
    entry.days_supply = days
    entry.record_fill(fill_date)
    db.session.commit()

    return jsonify({
        'success': True,
        'next_fill': entry.next_fill_date.isoformat() if entry.next_fill_date else '',
        'days_until': entry.days_until_refill,
    })


@tools_bp.route('/cs-tracker/<int:entry_id>/pdmp', methods=['POST'])
@login_required
def cs_pdmp_check(entry_id):
    """Record a PDMP check for a controlled substance entry."""
    entry = ControlledSubstanceEntry.query.filter_by(
        id=entry_id, user_id=current_user.id
    ).first()
    if not entry:
        return jsonify({'success': False, 'error': 'Entry not found'}), 404

    entry.last_pdmp_check = date.today()
    db.session.commit()
    return jsonify({'success': True})


@tools_bp.route('/cs-tracker/<int:entry_id>/uds', methods=['POST'])
@login_required
def cs_uds_check(entry_id):
    """Record a UDS for a controlled substance entry."""
    entry = ControlledSubstanceEntry.query.filter_by(
        id=entry_id, user_id=current_user.id
    ).first()
    if not entry:
        return jsonify({'success': False, 'error': 'Entry not found'}), 404

    entry.last_uds_date = date.today()
    db.session.commit()
    return jsonify({'success': True})


@tools_bp.route('/cs-tracker/<int:entry_id>/deactivate', methods=['POST'])
@login_required
def cs_deactivate(entry_id):
    """Deactivate a controlled substance entry (soft delete)."""
    entry = ControlledSubstanceEntry.query.filter_by(
        id=entry_id, user_id=current_user.id
    ).first()
    if not entry:
        return jsonify({'success': False, 'error': 'Entry not found'}), 404

    entry.is_active = False
    db.session.commit()
    return jsonify({'success': True})


@tools_bp.route('/cs-tracker/calculator')
@login_required
def cs_calculator():
    """Standalone refill date calculator."""
    return render_template('cs_calculator.html')


def _lookup_dea_schedule(drug_name):
    """Try to determine DEA schedule from RxNorm properties."""
    try:
        from app.services.api.rxnorm import RxNormService
        svc = RxNormService(db)
        result = svc.get_rxcui(drug_name)
        if result and result.get('rxcui'):
            props = svc.get_properties(result['rxcui'])
            if props:
                # RxNorm concept name may include schedule info
                name = (props.get('name') or '').upper()
                for schedule in ['SCHEDULE II', 'SCHEDULE III', 'SCHEDULE IV', 'SCHEDULE V',
                                 'C-II', 'C-III', 'C-IV', 'C-V', 'CII', 'CIII', 'CIV', 'CV']:
                    if schedule in name:
                        return schedule.replace('SCHEDULE ', '').replace('C-', '')
    except Exception:
        pass

    # Common controlled substances by name
    KNOWN_SCHEDULES = {
        'oxycodone': 'II', 'hydrocodone': 'II', 'morphine': 'II', 'fentanyl': 'II',
        'methadone': 'II', 'amphetamine': 'II', 'methylphenidate': 'II', 'adderall': 'II',
        'concerta': 'II', 'ritalin': 'II', 'oxycontin': 'II', 'percocet': 'II',
        'vicodin': 'II', 'norco': 'II', 'dilaudid': 'II', 'suboxone': 'III',
        'buprenorphine': 'III', 'testosterone': 'III', 'ketamine': 'III',
        'tylenol #3': 'III', 'codeine': 'III',
        'benzodiazepine': 'IV', 'alprazolam': 'IV', 'diazepam': 'IV',
        'lorazepam': 'IV', 'clonazepam': 'IV', 'zolpidem': 'IV',
        'xanax': 'IV', 'valium': 'IV', 'ativan': 'IV', 'klonopin': 'IV',
        'ambien': 'IV', 'tramadol': 'IV', 'carisoprodol': 'IV', 'soma': 'IV',
        'gabapentin': 'V', 'pregabalin': 'V', 'lyrica': 'V',
    }
    name_lower = drug_name.lower().split()[0]
    return KNOWN_SCHEDULES.get(name_lower, '')


# ======================================================================
# F17: ICD-10 Coding Helper
# ======================================================================

@tools_bp.route('/coding')
@login_required
def coding():
    """ICD-10 coding suggester with favorites and pairings."""
    favorites = (
        CodeFavorite.query
        .filter_by(user_id=current_user.id)
        .order_by(CodeFavorite.use_count.desc())
        .limit(50)
        .all()
    )
    return render_template('coding.html', favorites=favorites)


@tools_bp.route('/coding/search')
@login_required
def coding_search():
    """Search ICD-10 codes with specificity hints and pairing suggestions."""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'results': [], 'pairings': []})

    # Search via ICD10 service
    results = []
    try:
        from app.services.api.icd10 import ICD10Service
        svc = ICD10Service(db)
        raw = svc.search(query, max_results=15)
        for r in raw:
            code = r.get('code', '')
            desc = r.get('description', '')
            # Check specificity
            has_children = False
            if code and not code[-1].isdigit():
                has_children = False  # Already specific
            elif code and '.' not in code:
                has_children = True  # Unspecified — likely has children

            # Check if favorited
            is_fav = CodeFavorite.query.filter_by(
                user_id=current_user.id, icd10_code=code
            ).first() is not None

            results.append({
                'code': code,
                'description': desc,
                'is_billable': '.' in code,
                'needs_specificity': has_children or code.endswith('.9'),
                'is_favorite': is_fav,
            })
    except Exception as e:
        logger.debug('Coding search failed: %s', e)

    # Get pairing suggestions for the first result
    pairings = []
    if results:
        first_code = results[0]['code']
        pairings = _get_pairing_suggestions(first_code)

    return jsonify({'results': results, 'pairings': pairings})


@tools_bp.route('/coding/favorite', methods=['POST'])
@login_required
def coding_add_favorite():
    """Add or remove an ICD-10 code from favorites."""
    data = request.get_json(silent=True) or {}
    code = (data.get('code') or '').strip()
    desc = (data.get('description') or '').strip()

    if not code:
        return jsonify({'success': False, 'error': 'Code required'}), 400

    existing = CodeFavorite.query.filter_by(
        user_id=current_user.id, icd10_code=code
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'success': True, 'action': 'removed'})

    fav = CodeFavorite(
        user_id=current_user.id,
        icd10_code=code,
        description=desc,
    )
    db.session.add(fav)
    db.session.commit()
    return jsonify({'success': True, 'action': 'added'})


@tools_bp.route('/coding/pair', methods=['POST'])
@login_required
def coding_record_pair():
    """Record that two codes were used together."""
    data = request.get_json(silent=True) or {}
    code_a = (data.get('code_a') or '').strip()
    code_b = (data.get('code_b') or '').strip()

    if not code_a or not code_b or code_a == code_b:
        return jsonify({'success': False}), 400

    # Normalize order so (A,B) == (B,A)
    if code_a > code_b:
        code_a, code_b = code_b, code_a

    existing = CodePairing.query.filter_by(
        user_id=current_user.id, code_a=code_a, code_b=code_b
    ).first()

    if existing:
        existing.pair_count += 1
        existing.last_used = datetime.now(timezone.utc)
    else:
        pair = CodePairing(
            user_id=current_user.id,
            code_a=code_a,
            code_b=code_b,
        )
        db.session.add(pair)

    db.session.commit()
    return jsonify({'success': True})


@tools_bp.route('/coding/specificity')
@login_required
def coding_specificity():
    """Get more specific child codes for a given ICD-10 code."""
    code = request.args.get('code', '').strip()
    if not code:
        return jsonify({'children': []})

    try:
        from app.services.api.icd10 import ICD10Service
        svc = ICD10Service(db)
        children = svc.get_children(code)
        return jsonify({'children': children or []})
    except Exception:
        return jsonify({'children': []})


def _get_pairing_suggestions(code):
    """Get commonly paired codes from user history and hardcoded clinical pairings."""
    suggestions = []

    # User's own pairing history
    pairs = CodePairing.query.filter(
        CodePairing.user_id == current_user.id,
        db.or_(CodePairing.code_a == code, CodePairing.code_b == code)
    ).order_by(CodePairing.pair_count.desc()).limit(5).all()

    for p in pairs:
        paired_code = p.code_b if p.code_a == code else p.code_a
        suggestions.append({
            'code': paired_code,
            'source': 'history',
            'count': p.pair_count,
        })

    # Common clinical pairings (evidence-based)
    CLINICAL_PAIRINGS = {
        'I10': ['I12.9', 'N18.3', 'E78.5', 'E11.9'],     # HTN → CKD, hyperlipidemia, DM2
        'E11': ['E11.65', 'E11.40', 'E11.22', 'G63'],     # DM2 → neuropathy, retinopathy, CKD
        'E78.5': ['I10', 'E11.9', 'I25.10'],               # Hyperlipidemia → HTN, DM2, CAD
        'I50': ['I10', 'I48.91', 'N18.3'],                 # HF → HTN, AFib, CKD
        'J44': ['J96.10', 'R06.00', 'F17.210'],            # COPD → resp failure, dyspnea, nicotine
        'F32': ['F41.1', 'G47.00'],                        # Depression → anxiety, insomnia
        'F41': ['F32.1', 'G47.00'],                        # Anxiety → depression, insomnia
        'M54.5': ['M54.2', 'G89.29', 'M47.816'],           # Low back pain → cervicalgia, chronic pain
        'E03.9': ['E78.5', 'R63.5'],                       # Hypothyroidism → hyperlipidemia, weight gain
    }

    code_prefix = code.split('.')[0] if '.' in code else code
    for prefix, paired_codes in CLINICAL_PAIRINGS.items():
        if code.startswith(prefix) or code_prefix == prefix:
            for pc in paired_codes:
                if pc not in [s['code'] for s in suggestions]:
                    suggestions.append({
                        'code': pc,
                        'source': 'clinical',
                        'count': 0,
                    })

    return suggestions[:8]


# ======================================================================
# F26: Prior Authorization Generator
# ======================================================================

@tools_bp.route('/pa')
@login_required
def pa_index():
    """Prior authorization generator and history."""
    history = (
        PriorAuthorization.query
        .filter_by(user_id=current_user.id)
        .order_by(PriorAuthorization.created_at.desc())
        .limit(50)
        .all()
    )
    return render_template('pa.html', history=history)


@tools_bp.route('/pa/generate', methods=['POST'])
@login_required
def pa_generate():
    """Generate a PA narrative from drug + diagnosis + failed alternatives."""
    data = request.get_json(silent=True) or {}

    drug_name = (data.get('drug_name') or '').strip()
    diagnosis = (data.get('diagnosis') or '').strip()
    icd10 = (data.get('icd10_code') or '').strip()
    payer = (data.get('payer_name') or '').strip()
    failed_alts = data.get('failed_alternatives', [])
    justification = (data.get('justification') or '').strip()
    mrn = (data.get('mrn') or '').strip()
    patient_name = (data.get('patient_name') or '').strip()

    if not drug_name:
        return jsonify({'success': False, 'error': 'Drug name required'}), 400

    # Build narrative
    narrative_parts = []
    condition_text = diagnosis or "the patient's condition"
    icd10_text = f" (ICD-10: {icd10})" if icd10 else ""
    narrative_parts.append(
        f"I am requesting prior authorization for {drug_name} for the treatment "
        f"of {condition_text}{icd10_text}."
    )

    if failed_alts:
        alt_names = [a.get('name', a) if isinstance(a, dict) else str(a) for a in failed_alts]
        narrative_parts.append(
            f"The patient has previously trialed and failed the following alternative therapies: "
            f"{', '.join(alt_names)}."
        )
        for alt in failed_alts:
            if isinstance(alt, dict) and alt.get('reason'):
                narrative_parts.append(
                    f"  - {alt['name']}: discontinued due to {alt['reason']}."
                )

    narrative_parts.append(
        f"{drug_name} is medically necessary for this patient because "
        f"{justification or 'standard first-line therapies have been inadequate or contraindicated'}."
    )

    # Enrich with RxNorm data
    ndc = ''
    generic_available = False
    drug_class = ''
    try:
        from app.services.api.rxnorm import RxNormService
        svc = RxNormService(db)
        cui_result = svc.get_rxcui(drug_name)
        if cui_result and cui_result.get('rxcui'):
            rxcui = cui_result['rxcui']
            ndcs = svc.get_ndcs(rxcui)
            if ndcs and ndcs.get('ndcs'):
                ndc = ndcs['ndcs'][0]
                narrative_parts.append(f"NDC: {ndc}.")

            # Check for generic
            ing = svc.get_ingredient(rxcui)
            if ing and ing.get('rxcui') and ing['rxcui'] != rxcui:
                generic_available = True

        # Drug class
        from app.services.api.rxclass import RxClassService
        class_svc = RxClassService(db)
        classes = class_svc.get_classes_for_drug_name(drug_name)
        if classes:
            drug_class = classes[0].get('class_name', '')
    except Exception:
        pass

    if generic_available:
        narrative_parts.append(
            "A generic formulation may be available; however, the brand-name product is "
            "requested due to specific clinical requirements or prior generic failure."
        )

    narrative = '\n\n'.join(narrative_parts)

    # Save to database
    pa = PriorAuthorization(
        user_id=current_user.id,
        mrn=mrn,
        patient_name=patient_name,
        drug_name=drug_name,
        rxnorm_cui=cui_result['rxcui'] if 'cui_result' in dir() and cui_result else '',
        ndc_code=ndc,
        diagnosis=diagnosis,
        icd10_code=icd10,
        payer_name=payer,
        failed_alternatives=json.dumps(failed_alts) if failed_alts else '',
        clinical_justification=justification,
        generated_narrative=narrative,
        status='draft',
    )
    db.session.add(pa)
    db.session.commit()

    return jsonify({
        'success': True,
        'id': pa.id,
        'narrative': narrative,
        'ndc': ndc,
        'generic_available': generic_available,
        'drug_class': drug_class,
    })


@tools_bp.route('/pa/<int:pa_id>/status', methods=['POST'])
@login_required
def pa_update_status(pa_id):
    """Update PA status (submitted, approved, denied, appealed)."""
    pa = PriorAuthorization.query.filter_by(
        id=pa_id, user_id=current_user.id
    ).first()
    if not pa:
        return jsonify({'success': False, 'error': 'PA not found'}), 404

    data = request.get_json(silent=True) or {}
    new_status = (data.get('status') or '').strip()
    if new_status not in ('submitted', 'approved', 'denied', 'appealed'):
        return jsonify({'success': False, 'error': 'Invalid status'}), 400

    pa.status = new_status
    if new_status == 'submitted':
        pa.submitted_date = date.today()
    elif new_status in ('approved', 'denied'):
        pa.decision_date = date.today()
    if new_status == 'denied':
        pa.denial_reason = (data.get('reason') or '').strip()
    db.session.commit()

    return jsonify({'success': True, 'status': pa.status})


@tools_bp.route('/pa/<int:pa_id>/appeal', methods=['POST'])
@login_required
def pa_generate_appeal(pa_id):
    """Generate an appeal narrative for a denied PA."""
    pa = PriorAuthorization.query.filter_by(
        id=pa_id, user_id=current_user.id
    ).first()
    if not pa:
        return jsonify({'success': False, 'error': 'PA not found'}), 404

    appeal = (
        f"APPEAL — Prior Authorization for {pa.drug_name}\n\n"
        f"This is an appeal of the denial decision dated {pa.decision_date or 'N/A'} "
        f"for {pa.drug_name} for the treatment of {pa.diagnosis or 'the patient condition'}.\n\n"
    )
    if pa.denial_reason:
        appeal += f"The stated denial reason was: {pa.denial_reason}\n\n"

    appeal += (
        f"I respectfully disagree with this determination. {pa.drug_name} remains "
        f"medically necessary for this patient.\n\n"
        f"{pa.clinical_justification or ''}\n\n"
        f"The original prior authorization narrative is included below for reference:\n\n"
        f"---\n{pa.generated_narrative or ''}\n---\n\n"
        f"I request that this denial be overturned and authorization be granted "
        f"for {pa.drug_name}."
    )

    pa.appeal_narrative = appeal
    pa.status = 'appealed'
    db.session.commit()

    return jsonify({'success': True, 'appeal': appeal})


# ======================================================================
# F24: Follow-Up Tickler System
# ======================================================================

@tools_bp.route('/tickler')
@login_required
def tickler():
    """Three-column tickler board: overdue, due today, upcoming."""
    from datetime import date as _date
    today_start = datetime.combine(_date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(_date.today(), datetime.max.time()).replace(tzinfo=timezone.utc)

    all_open = (
        Tickler.query
        .filter_by(user_id=current_user.id, is_completed=False)
        .order_by(Tickler.due_date, Tickler.priority.desc())
        .all()
    )
    # Also show items assigned to this user by others
    assigned = (
        Tickler.query
        .filter(
            Tickler.assigned_to_user_id == current_user.id,
            Tickler.is_completed == False,
            Tickler.user_id != current_user.id,
        )
        .order_by(Tickler.due_date)
        .all()
    )
    all_items = list({t.id: t for t in all_open + assigned}.values())

    overdue = [t for t in all_items if t.due_date and t.due_date < today_start]
    today_items = [t for t in all_items if t.due_date and today_start <= t.due_date <= today_end]
    upcoming = [t for t in all_items if t.due_date and t.due_date > today_end]

    all_users = User.query.filter_by(is_active_account=True).order_by(User.display_name).all()

    return render_template(
        'tickler.html',
        overdue=overdue,
        today_items=today_items,
        upcoming=upcoming,
        all_users=all_users,
    )


@tools_bp.route('/tickler/add', methods=['POST'])
@login_required
def tickler_add():
    """Add a new tickler item."""
    data = request.get_json(silent=True) or {}

    due_str = (data.get('due_date') or '').strip()
    if not due_str:
        return jsonify({'success': False, 'error': 'Due date required'}), 400

    try:
        due_dt = datetime.strptime(due_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid date format'}), 400

    assigned_to = data.get('assigned_to', '')
    assigned_id = int(assigned_to) if assigned_to and assigned_to.isdigit() else None

    t = Tickler(
        user_id=current_user.id,
        assigned_to_user_id=assigned_id,
        mrn=(data.get('mrn') or '').strip(),
        patient_display=(data.get('patient_display') or '').strip(),
        due_date=due_dt,
        priority=(data.get('priority') or 'routine').strip(),
        notes=(data.get('notes') or '').strip(),
        is_recurring=bool(data.get('is_recurring')),
        recurrence_interval_days=int(data.get('recurrence_days') or 0) or None,
    )
    db.session.add(t)
    db.session.commit()
    return jsonify({'success': True, 'id': t.id})


@tools_bp.route('/tickler/<int:tid>/complete', methods=['POST'])
@login_required
def tickler_complete(tid):
    """Mark a tickler as completed. If recurring, create the next one."""
    t = Tickler.query.filter(
        Tickler.id == tid,
        db.or_(Tickler.user_id == current_user.id, Tickler.assigned_to_user_id == current_user.id)
    ).first()
    if not t:
        return jsonify({'success': False, 'error': 'Not found'}), 404

    t.is_completed = True
    t.completed_at = datetime.now(timezone.utc)

    # Auto-create next occurrence if recurring
    if t.is_recurring and t.recurrence_interval_days:
        next_due = t.due_date + timedelta(days=t.recurrence_interval_days)
        next_t = Tickler(
            user_id=t.user_id,
            assigned_to_user_id=t.assigned_to_user_id,
            mrn=t.mrn,
            patient_display=t.patient_display,
            due_date=next_due,
            priority=t.priority,
            notes=t.notes,
            is_recurring=True,
            recurrence_interval_days=t.recurrence_interval_days,
        )
        db.session.add(next_t)

    db.session.commit()
    return jsonify({'success': True})


@tools_bp.route('/tickler/<int:tid>/snooze', methods=['POST'])
@login_required
def tickler_snooze(tid):
    """Snooze a tickler to a new date."""
    t = Tickler.query.filter(
        Tickler.id == tid,
        db.or_(Tickler.user_id == current_user.id, Tickler.assigned_to_user_id == current_user.id)
    ).first()
    if not t:
        return jsonify({'success': False, 'error': 'Not found'}), 404

    data = request.get_json(silent=True) or {}
    days = int(data.get('days') or 7)
    t.due_date = datetime.now(timezone.utc) + timedelta(days=days)
    db.session.commit()
    return jsonify({'success': True})


# ======================================================================
# F27: Referral Letter Generator
# ======================================================================

SPECIALTIES = [
    'Cardiology', 'Orthopedics', 'Gastroenterology', 'Dermatology',
    'Endocrinology', 'Neurology', 'Urology', 'Pulmonology',
    'Nephrology', 'Rheumatology', 'Psychiatry', 'General Surgery',
    'Ophthalmology', 'ENT/Otolaryngology', 'Allergy/Immunology',
    'Hematology/Oncology', 'Infectious Disease', 'Pain Management',
    'Physical Medicine', 'Podiatry', 'Other',
]


@tools_bp.route('/referral')
@login_required
def referral():
    """Referral letter generator and tracking log."""
    log = (
        ReferralLetter.query
        .filter_by(user_id=current_user.id)
        .order_by(ReferralLetter.created_at.desc())
        .limit(50)
        .all()
    )
    return render_template('referral.html', log=log, specialties=SPECIALTIES)


@tools_bp.route('/referral/generate', methods=['POST'])
@login_required
def referral_generate():
    """Generate a referral letter and save to log."""
    data = request.get_json(silent=True) or {}

    specialty = (data.get('specialty') or '').strip()
    reason = (data.get('reason') or '').strip()
    history = (data.get('relevant_history') or '').strip()
    findings = (data.get('key_findings') or '').strip()
    meds = (data.get('current_medications') or '').strip()
    urgency = (data.get('urgency') or 'routine').strip()
    patient = (data.get('patient_display') or 'this patient').strip()

    if not specialty or not reason:
        return jsonify({'success': False, 'error': 'Specialty and reason required'}), 400

    # Get provider name from user profile
    provider_name = current_user.display_name or current_user.username

    # Generate letter
    today_str = date.today().strftime('%B %d, %Y')
    urgency_line = ''
    if urgency == 'urgent':
        urgency_line = '\n**URGENT REFERRAL — Please expedite scheduling.**\n'
    elif urgency == 'emergent':
        urgency_line = '\n**EMERGENT REFERRAL — Same-day evaluation requested.**\n'

    letter = f"""{today_str}

Dear {specialty} Colleague,
{urgency_line}
I am referring {patient} for evaluation of {reason}.

"""
    if history:
        letter += f"RELEVANT HISTORY:\n{history}\n\n"
    if findings:
        letter += f"KEY CLINICAL FINDINGS:\n{findings}\n\n"
    if meds:
        letter += f"CURRENT MEDICATIONS:\n{meds}\n\n"

    letter += f"""I would appreciate your evaluation and recommendations regarding the management of this patient. Please send a consultation note to our office at your earliest convenience.

Thank you for your expertise and timely attention.

Sincerely,
{provider_name}
Family Practice Associates of Chesterfield"""

    ref = ReferralLetter(
        user_id=current_user.id,
        mrn=(data.get('mrn') or '').strip(),
        patient_display=patient,
        specialty=specialty,
        reason=reason,
        relevant_history=history,
        key_findings=findings,
        current_medications=meds,
        urgency=urgency,
        generated_letter=letter,
        referral_date=date.today(),
    )
    db.session.add(ref)
    db.session.commit()

    return jsonify({'success': True, 'id': ref.id, 'letter': letter})


@tools_bp.route('/referral/<int:ref_id>/received', methods=['POST'])
@login_required
def referral_received(ref_id):
    """Mark a referral consultation as received."""
    ref = ReferralLetter.query.filter_by(id=ref_id, user_id=current_user.id).first()
    if not ref:
        return jsonify({'success': False}), 404
    ref.consultation_received = True
    ref.follow_up_date = date.today()
    db.session.commit()
    return jsonify({'success': True})

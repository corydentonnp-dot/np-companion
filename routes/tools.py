"""
CareCompanion — Tools Routes
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
from models.notification import Notification, NOTIFICATION_TEMPLATES
from models.macro import AhkMacro, DotPhrase, MacroStep, MacroVariable
from models.result_template import ResultTemplate

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

def get_overdue_pdmp_patients(user_id):
    """Return list of active CS patients overdue for PDMP check.

    Each dict: {mrn, drug_name, last_checked, days_overdue}.
    A patient is overdue when last_pdmp_check is null or older than
    the entry's pdmp_check_interval_days.
    """
    from datetime import date, timedelta
    entries = (
        ControlledSubstanceEntry.query
        .filter_by(user_id=user_id, is_active=True)
        .all()
    )
    overdue = []
    for e in entries:
        if e.last_pdmp_check is None:
            days_overdue = e.pdmp_check_interval_days
        else:
            due_date = e.last_pdmp_check + timedelta(days=e.pdmp_check_interval_days)
            if date.today() < due_date:
                continue
            days_overdue = (date.today() - due_date).days
        overdue.append({
            'mrn': e.mrn,
            'drug_name': e.drug_name,
            'last_checked': e.last_pdmp_check.isoformat() if e.last_pdmp_check else None,
            'days_overdue': days_overdue,
        })
    return overdue


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
    if len(drug_name) > 200:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Drug name too long'}), 400
        flash('Drug name is too long.', 'error')
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


@tools_bp.route('/cs-tracker/<int:entry_id>/pdmp-lookup', methods=['POST'])
@login_required
def cs_pdmp_lookup(entry_id):
    """Run an automated PDMP lookup for a CS tracker patient."""
    entry = ControlledSubstanceEntry.query.filter_by(
        id=entry_id, user_id=current_user.id
    ).first()
    if not entry:
        return jsonify({'success': False, 'error': 'Entry not found'}), 404

    # Get patient record for name/DOB
    from models.patient import PatientRecord
    patient = PatientRecord.query.filter_by(
        user_id=current_user.id, mrn=entry.mrn
    ).first() if entry.mrn else None

    if not patient or not patient.patient_name:
        return jsonify({
            'success': False,
            'error': 'Patient name and DOB required for PDMP lookup. Update patient demographics first.',
        })

    # Parse name into first/last
    name_parts = (patient.patient_name or '').split(',')
    if len(name_parts) >= 2:
        last_name = name_parts[0].strip()
        first_name = name_parts[1].strip().split()[0] if name_parts[1].strip() else ''
    else:
        parts = patient.patient_name.split()
        first_name = parts[0] if parts else ''
        last_name = parts[-1] if len(parts) > 1 else ''

    # Parse DOB
    dob_raw = patient.patient_dob or ''
    dob_clean = dob_raw.replace('-', '').replace('/', '')
    if len(dob_clean) >= 8:
        dob = f'{dob_clean[:4]}-{dob_clean[4:6]}-{dob_clean[6:8]}'
    else:
        dob = dob_raw

    if not first_name or not last_name:
        return jsonify({'success': False, 'error': 'Could not parse patient name'})

    try:
        import asyncio
        from flask import current_app
        from scrapers.pdmp import PDMPScraper
        scraper = PDMPScraper(current_app._get_current_object())
        result = asyncio.run(scraper.lookup_patient(first_name, last_name, dob))

        # Record the PDMP check regardless of success
        entry.last_pdmp_check = date.today()
        db.session.commit()

        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'PDMP lookup failed: {str(e)}',
            'prescriptions': [],
        })


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
    cui_result = None
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
        rxnorm_cui=cui_result['rxcui'] if cui_result else '',
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
# F26a: Shared PA Library (Phase 22.8)
# ======================================================================

@tools_bp.route('/pa/library')
@login_required
def pa_library():
    """Practice-wide shared PA template library with approval rates."""
    shared_pas = (
        PriorAuthorization.query
        .filter_by(is_shared=True)
        .order_by(PriorAuthorization.drug_name)
        .all()
    )
    return render_template('pa_library.html', shared_pas=shared_pas)


@tools_bp.route('/pa/<int:pa_id>/share', methods=['POST'])
@login_required
def pa_share(pa_id):
    """Share a PA template with the practice library."""
    pa = PriorAuthorization.query.filter_by(
        id=pa_id, user_id=current_user.id
    ).first_or_404()
    pa.is_shared = True
    pa.shared_by_user_id = current_user.id
    db.session.commit()
    flash('PA template shared with practice library.', 'success')
    return redirect(url_for('tools.pa_index'))


@tools_bp.route('/pa/<int:pa_id>/unshare', methods=['POST'])
@login_required
def pa_unshare(pa_id):
    """Remove a PA template from the shared library."""
    pa = PriorAuthorization.query.filter_by(
        id=pa_id, user_id=current_user.id
    ).first_or_404()
    pa.is_shared = False
    db.session.commit()
    flash('PA template removed from shared library.', 'success')
    return redirect(url_for('tools.pa_index'))


@tools_bp.route('/pa/<int:pa_id>/import', methods=['POST'])
@login_required
def pa_import(pa_id):
    """Fork a shared PA template into the current user's PA list."""
    source = PriorAuthorization.query.filter_by(
        id=pa_id, is_shared=True
    ).first_or_404()

    forked = PriorAuthorization(
        user_id=current_user.id,
        drug_name=source.drug_name,
        rxnorm_cui=source.rxnorm_cui,
        ndc_code=source.ndc_code,
        diagnosis=source.diagnosis,
        icd10_code=source.icd10_code,
        payer_name=source.payer_name,
        failed_alternatives=source.failed_alternatives,
        clinical_justification=source.clinical_justification,
        generated_narrative=source.generated_narrative,
        status='draft',
        forked_from_id=source.id,
    )
    db.session.add(forked)
    db.session.commit()
    flash(f'Imported PA template for {source.drug_name}.', 'success')
    return redirect(url_for('tools.pa_index'))


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

SPECIALTY_FIELDS = {
    'Cardiology': [
        {'name': 'ekg_findings', 'label': 'EKG Findings', 'type': 'text', 'placeholder': 'e.g., NSR, LBBB, ST changes'},
        {'name': 'echo_results', 'label': 'Echocardiogram Results', 'type': 'textarea', 'placeholder': 'EF, wall motion, valve findings...'},
        {'name': 'chest_pain_characteristics', 'label': 'Chest Pain Characteristics', 'type': 'text', 'placeholder': 'e.g., exertional, substernal, duration'},
    ],
    'Orthopedics': [
        {'name': 'imaging_results', 'label': 'Imaging Results', 'type': 'textarea', 'placeholder': 'X-ray, MRI, CT findings...'},
        {'name': 'affected_area', 'label': 'Affected Joint/Extremity', 'type': 'text', 'placeholder': 'e.g., right knee, lumbar spine'},
        {'name': 'injury_mechanism', 'label': 'Injury Mechanism', 'type': 'text', 'placeholder': 'e.g., fall, overuse, trauma'},
    ],
    'Gastroenterology': [
        {'name': 'lab_results', 'label': 'Recent Labs (LFTs, CBC)', 'type': 'textarea', 'placeholder': 'AST, ALT, bilirubin, CBC values...'},
        {'name': 'prior_endoscopy', 'label': 'Prior Endoscopy Results', 'type': 'textarea', 'placeholder': 'EGD/colonoscopy findings...'},
        {'name': 'gi_symptoms', 'label': 'GI Symptom Details', 'type': 'text', 'placeholder': 'e.g., duration, frequency, triggers'},
    ],
    'Dermatology': [
        {'name': 'lesion_location', 'label': 'Lesion Location', 'type': 'text', 'placeholder': 'e.g., left forearm, scalp'},
        {'name': 'lesion_duration', 'label': 'Duration', 'type': 'text', 'placeholder': 'e.g., 3 months, worsening'},
        {'name': 'prior_treatments', 'label': 'Prior Treatments', 'type': 'text', 'placeholder': 'e.g., topical steroids, antifungals'},
    ],
    'Endocrinology': [
        {'name': 'recent_labs', 'label': 'Recent Labs (A1c, TSH, etc.)', 'type': 'textarea', 'placeholder': 'A1c, TSH, free T4, glucose values...'},
        {'name': 'current_regimen', 'label': 'Current Endocrine Regimen', 'type': 'text', 'placeholder': 'e.g., metformin 1000mg BID, levothyroxine 75mcg'},
        {'name': 'target_concerns', 'label': 'Target Concerns', 'type': 'text', 'placeholder': 'e.g., uncontrolled DM, thyroid nodule'},
    ],
    'Neurology': [
        {'name': 'neuro_exam', 'label': 'Neurological Exam Findings', 'type': 'textarea', 'placeholder': 'Cranial nerves, reflexes, strength, sensation...'},
        {'name': 'imaging_results', 'label': 'Brain/Spine Imaging', 'type': 'textarea', 'placeholder': 'MRI/CT findings...'},
        {'name': 'symptom_timeline', 'label': 'Symptom Timeline', 'type': 'text', 'placeholder': 'e.g., onset 2 weeks ago, progressive'},
    ],
    'Urology': [
        {'name': 'psa_results', 'label': 'PSA / Labs', 'type': 'text', 'placeholder': 'e.g., PSA 5.2, UA with micro hematuria'},
        {'name': 'imaging_results', 'label': 'Imaging Results', 'type': 'textarea', 'placeholder': 'Renal US, CT findings...'},
        {'name': 'urinary_symptoms', 'label': 'Urinary Symptoms', 'type': 'text', 'placeholder': 'e.g., frequency, hesitancy, nocturia'},
    ],
    'Pulmonology': [
        {'name': 'pft_results', 'label': 'PFT / Spirometry Results', 'type': 'textarea', 'placeholder': 'FEV1, FVC, DLCO values...'},
        {'name': 'chest_imaging', 'label': 'Chest Imaging', 'type': 'textarea', 'placeholder': 'CXR or CT chest findings...'},
        {'name': 'respiratory_symptoms', 'label': 'Respiratory Symptoms', 'type': 'text', 'placeholder': 'e.g., dyspnea on exertion, chronic cough'},
    ],
    'Nephrology': [
        {'name': 'renal_labs', 'label': 'Renal Labs (BMP, UA)', 'type': 'textarea', 'placeholder': 'Cr, BUN, GFR, UA with protein...'},
        {'name': 'renal_imaging', 'label': 'Renal Imaging', 'type': 'textarea', 'placeholder': 'Renal US findings...'},
        {'name': 'ckd_stage', 'label': 'CKD Stage / Concerns', 'type': 'text', 'placeholder': 'e.g., Stage 3b, declining GFR'},
    ],
    'Rheumatology': [
        {'name': 'inflammatory_labs', 'label': 'Inflammatory Labs', 'type': 'textarea', 'placeholder': 'ESR, CRP, RF, ANA, anti-CCP...'},
        {'name': 'joint_involvement', 'label': 'Joint Involvement', 'type': 'text', 'placeholder': 'e.g., bilateral MCP, PIPs, symmetric'},
        {'name': 'symptom_pattern', 'label': 'Symptom Pattern', 'type': 'text', 'placeholder': 'e.g., morning stiffness >1hr, flares'},
    ],
    'Psychiatry': [
        {'name': 'psych_meds', 'label': 'Current Psychiatric Medications', 'type': 'textarea', 'placeholder': 'Drug, dose, duration...'},
        {'name': 'screening_scores', 'label': 'PHQ-9 / GAD-7 Scores', 'type': 'text', 'placeholder': 'e.g., PHQ-9: 18, GAD-7: 14'},
        {'name': 'safety_concerns', 'label': 'Safety Concerns', 'type': 'text', 'placeholder': 'e.g., SI/HI assessment, substance use'},
    ],
    'General Surgery': [
        {'name': 'imaging_results', 'label': 'Imaging Results', 'type': 'textarea', 'placeholder': 'CT, US, MRI findings...'},
        {'name': 'surgical_history', 'label': 'Prior Surgical History', 'type': 'text', 'placeholder': 'e.g., appendectomy 2010, cholecystectomy 2015'},
        {'name': 'anticoagulation', 'label': 'Anticoagulation Status', 'type': 'text', 'placeholder': 'e.g., on warfarin, last INR 2.3'},
    ],
    'Ophthalmology': [
        {'name': 'visual_acuity', 'label': 'Visual Acuity', 'type': 'text', 'placeholder': 'e.g., OD 20/40, OS 20/25'},
        {'name': 'ocular_symptoms', 'label': 'Ocular Symptoms', 'type': 'text', 'placeholder': 'e.g., blurred vision, floaters, eye pain'},
        {'name': 'dm_htn_status', 'label': 'DM/HTN Status', 'type': 'text', 'placeholder': 'e.g., DM2 x10yr, A1c 7.8, HTN controlled'},
    ],
    'ENT/Otolaryngology': [
        {'name': 'symptom_duration', 'label': 'Symptom Duration', 'type': 'text', 'placeholder': 'e.g., chronic sinusitis x6 months'},
        {'name': 'prior_treatments', 'label': 'Prior Treatments', 'type': 'text', 'placeholder': 'e.g., nasal steroids, antibiotics x3 courses'},
        {'name': 'imaging_results', 'label': 'Imaging Results', 'type': 'text', 'placeholder': 'e.g., sinus CT findings'},
    ],
    'Allergy/Immunology': [
        {'name': 'allergen_history', 'label': 'Known Allergies / Triggers', 'type': 'textarea', 'placeholder': 'Environmental, food, drug allergies...'},
        {'name': 'prior_testing', 'label': 'Prior Allergy Testing', 'type': 'text', 'placeholder': 'e.g., skin prick, IgE levels'},
        {'name': 'current_antihistamines', 'label': 'Current Allergy Medications', 'type': 'text', 'placeholder': 'e.g., cetirizine, montelukast, fluticasone'},
    ],
    'Hematology/Oncology': [
        {'name': 'cbc_results', 'label': 'CBC / Blood Smear', 'type': 'textarea', 'placeholder': 'WBC, Hgb, Plt, differential...'},
        {'name': 'concerning_findings', 'label': 'Concerning Findings', 'type': 'textarea', 'placeholder': 'e.g., unexplained lymphadenopathy, mass on imaging'},
        {'name': 'family_cancer_hx', 'label': 'Family Cancer History', 'type': 'text', 'placeholder': 'e.g., mother breast ca age 45, father colon ca age 60'},
    ],
    'Infectious Disease': [
        {'name': 'culture_results', 'label': 'Culture / Sensitivity Results', 'type': 'textarea', 'placeholder': 'Blood Cx, wound Cx, susceptibilities...'},
        {'name': 'antibiotic_history', 'label': 'Antibiotic History', 'type': 'textarea', 'placeholder': 'Prior antibiotics tried, duration, response...'},
        {'name': 'travel_exposure', 'label': 'Travel / Exposure History', 'type': 'text', 'placeholder': 'e.g., recent travel, animal exposure, IV drug use'},
    ],
    'Pain Management': [
        {'name': 'pain_location', 'label': 'Pain Location / Characteristics', 'type': 'text', 'placeholder': 'e.g., chronic low back, radicular, neuropathic'},
        {'name': 'prior_interventions', 'label': 'Prior Interventions', 'type': 'textarea', 'placeholder': 'PT, injections, nerve blocks, medications tried...'},
        {'name': 'current_pain_meds', 'label': 'Current Pain Medications', 'type': 'text', 'placeholder': 'e.g., gabapentin 300mg TID, meloxicam 15mg'},
    ],
    'Physical Medicine': [
        {'name': 'functional_status', 'label': 'Functional Limitations', 'type': 'textarea', 'placeholder': 'ADL limitations, mobility status, work restrictions...'},
        {'name': 'prior_therapy', 'label': 'Prior PT/OT', 'type': 'text', 'placeholder': 'e.g., 6 weeks PT, completed home program'},
        {'name': 'rehab_goals', 'label': 'Rehabilitation Goals', 'type': 'text', 'placeholder': 'e.g., return to work, independent ambulation'},
    ],
    'Podiatry': [
        {'name': 'foot_exam', 'label': 'Foot Exam Findings', 'type': 'textarea', 'placeholder': 'Pulses, sensation, deformity, wound...'},
        {'name': 'dm_status', 'label': 'Diabetes Status', 'type': 'text', 'placeholder': 'e.g., DM2 x15yr, A1c 8.1, neuropathy'},
        {'name': 'footwear_orthotics', 'label': 'Footwear / Orthotics', 'type': 'text', 'placeholder': 'e.g., diabetic shoes, custom orthotics'},
    ],
    'Other': [],
}


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
    return render_template('referral.html', log=log, specialties=SPECIALTIES,
                               specialty_fields_json=json.dumps(SPECIALTY_FIELDS))


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

    # Specialty-specific clinical details
    spec_fields = SPECIALTY_FIELDS.get(specialty, [])
    specialty_details = {}
    clinical_lines = []
    for fld in spec_fields:
        val = (data.get(fld['name']) or '').strip()
        if val:
            specialty_details[fld['name']] = val
            clinical_lines.append(f"{fld['label']}: {val}")
    if clinical_lines:
        letter += "SPECIALTY-SPECIFIC CLINICAL DETAILS:\n"
        letter += '\n'.join(clinical_lines) + '\n\n'

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
        specialty_fields=json.dumps(specialty_details) if specialty_details else None,
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


# ======================================================================
# F20: End-of-Day Checker
# ======================================================================

@tools_bp.route('/tools/eod')
@login_required
def eod():
    """End-of-Day dashboard — live status check."""
    from agent.eod_checker import run_eod_check
    result = run_eod_check(current_user.id)
    return render_template('eod.html', result=result)


# ======================================================================
# F5: Notification History
# ======================================================================

@tools_bp.route('/notifications')
@login_required
def notifications():
    """Full notification history page with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = 30
    type_filter = request.args.get('type', '')

    query = Notification.query.filter_by(user_id=current_user.id)
    if type_filter:
        query = query.filter_by(template_name=type_filter)

    pagination = (
        query
        .order_by(Notification.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    template_types = list(NOTIFICATION_TEMPLATES.keys())
    return render_template(
        'notifications.html',
        notifications=pagination.items,
        pagination=pagination,
        type_filter=type_filter,
        template_types=template_types,
    )


# ======================================================================
# F23: Dot Phrase Engine
# ======================================================================

@tools_bp.route('/tools/dot-phrases')
@login_required
def dot_phrases():
    """Dot phrase management page — browse, add, edit, delete."""
    category = request.args.get('category', '')
    query = DotPhrase.query.filter_by(user_id=current_user.id, is_active=True)
    if category:
        query = query.filter_by(category=category)
    phrases = query.order_by(DotPhrase.abbreviation).all()
    categories = ['hpi', 'exam', 'plan', 'instructions', 'letters', 'custom']
    return render_template('dot_phrases.html', phrases=phrases, categories=categories,
                           active_category=category)


@tools_bp.route('/tools/dot-phrases', methods=['POST'])
@login_required
def dot_phrase_create():
    """Create a new dot phrase."""
    data = request.get_json(silent=True) or {}
    abbreviation = (data.get('abbreviation') or '').strip().lower()
    expansion = (data.get('expansion') or '').strip()
    category = (data.get('category') or 'custom').strip()

    if not abbreviation:
        return jsonify({'success': False, 'error': 'Abbreviation is required'}), 400
    if not abbreviation.startswith('.'):
        abbreviation = '.' + abbreviation
    if not expansion:
        return jsonify({'success': False, 'error': 'Expansion text is required'}), 400

    existing = DotPhrase.query.filter_by(user_id=current_user.id, abbreviation=abbreviation).first()
    if existing:
        return jsonify({'success': False, 'error': f'"{abbreviation}" already exists'}), 409

    import re as _re
    placeholders = json.dumps(sorted(set(_re.findall(r'\{(\w+)\}', expansion))))

    phrase = DotPhrase(
        user_id=current_user.id,
        abbreviation=abbreviation,
        expansion=expansion,
        category=category,
        placeholders=placeholders,
    )
    db.session.add(phrase)
    db.session.commit()
    _sync_ahk_to_disk(current_user.id)
    return jsonify({'success': True, 'id': phrase.id, 'abbreviation': phrase.abbreviation})


@tools_bp.route('/tools/dot-phrases/<int:phrase_id>', methods=['PUT'])
@login_required
def dot_phrase_update(phrase_id):
    """Edit an existing dot phrase."""
    phrase = DotPhrase.query.filter_by(id=phrase_id, user_id=current_user.id).first_or_404()
    data = request.get_json(silent=True) or {}

    if 'abbreviation' in data:
        abbrev = data['abbreviation'].strip().lower()
        if not abbrev.startswith('.'):
            abbrev = '.' + abbrev
        dup = DotPhrase.query.filter_by(user_id=current_user.id, abbreviation=abbrev).first()
        if dup and dup.id != phrase.id:
            return jsonify({'success': False, 'error': f'"{abbrev}" already exists'}), 409
        phrase.abbreviation = abbrev

    if 'expansion' in data:
        phrase.expansion = data['expansion'].strip()
        import re as _re
        phrase.placeholders = json.dumps(sorted(set(_re.findall(r'\{(\w+)\}', phrase.expansion))))

    if 'category' in data:
        phrase.category = data['category'].strip()

    db.session.commit()
    _sync_ahk_to_disk(current_user.id)
    return jsonify({'success': True})


@tools_bp.route('/tools/dot-phrases/<int:phrase_id>', methods=['DELETE'])
@login_required
def dot_phrase_delete(phrase_id):
    """Delete a dot phrase."""
    phrase = DotPhrase.query.filter_by(id=phrase_id, user_id=current_user.id).first_or_404()
    db.session.delete(phrase)
    db.session.commit()
    _sync_ahk_to_disk(current_user.id)
    return jsonify({'success': True})


@tools_bp.route('/api/dot-phrases')
@login_required
def dot_phrases_api():
    """JSON list of active dot phrases for autocomplete / live expansion."""
    phrases = (DotPhrase.query
               .filter_by(user_id=current_user.id, is_active=True)
               .order_by(DotPhrase.abbreviation)
               .all())
    return jsonify([{
        'id': p.id,
        'abbreviation': p.abbreviation,
        'expansion': p.expansion,
        'category': p.category,
        'use_count': p.use_count,
    } for p in phrases])


@tools_bp.route('/api/dot-phrases/<int:phrase_id>/increment', methods=['POST'])
@login_required
def dot_phrase_increment(phrase_id):
    """Bump the use_count for a dot phrase."""
    phrase = DotPhrase.query.filter_by(id=phrase_id, user_id=current_user.id).first_or_404()
    phrase.use_count = (phrase.use_count or 0) + 1
    db.session.commit()
    return jsonify({'success': True, 'use_count': phrase.use_count})


@tools_bp.route('/tools/dot-phrases/export')
@login_required
def dot_phrases_export():
    """Export all active dot phrases as an AHK hotstring file."""
    from utils.ahk_generator import generate_dot_phrase_script

    phrases = (DotPhrase.query
               .filter_by(user_id=current_user.id, is_active=True)
               .order_by(DotPhrase.category, DotPhrase.abbreviation)
               .all())
    script = generate_dot_phrase_script(phrases)
    from flask import Response
    return Response(
        script,
        mimetype='text/plain',
        headers={'Content-Disposition': 'attachment; filename=dot_phrases.ahk'},
    )


# ======================================================================
# F23: Macro Recorder
# ======================================================================

@tools_bp.route('/tools/macros/recorder')
@login_required
def macro_recorder():
    """Macro recorder page — step builder UI."""
    return render_template('macro_recorder.html')


@tools_bp.route('/api/macros/record/save', methods=['POST'])
@login_required
def macro_record_save():
    """Save recorded steps as a new macro."""
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Macro name is required'}), 400

    macro = AhkMacro(
        user_id=current_user.id,
        name=name,
        description=(data.get('description') or '').strip(),
        hotkey=(data.get('hotkey') or '').strip(),
        category=(data.get('category') or 'custom').strip(),
    )
    db.session.add(macro)
    db.session.flush()  # get macro.id

    steps_data = data.get('steps') or []
    for i, s in enumerate(steps_data):
        step = MacroStep(
            macro_id=macro.id,
            step_order=i + 1,
            action_type=s.get('action_type', 'sleep'),
            target_x=s.get('target_x'),
            target_y=s.get('target_y'),
            key_sequence=s.get('key_sequence'),
            delay_ms=s.get('delay_ms', 100),
            window_title=s.get('window_title'),
            comment=s.get('comment'),
        )
        db.session.add(step)

    variables_data = data.get('variables') or []
    for v in variables_data:
        var = MacroVariable(
            macro_id=macro.id,
            var_name=v.get('var_name', ''),
            var_label=v.get('var_label', ''),
            default_value=v.get('default_value', ''),
            var_type=v.get('var_type', 'text'),
            choices=v.get('choices'),
        )
        db.session.add(var)

    db.session.commit()
    return jsonify({'success': True, 'id': macro.id, 'name': macro.name})


@tools_bp.route('/api/macros/<int:macro_id>/steps')
@login_required
def macro_get_steps(macro_id):
    """Get steps for a macro (for preview / editing)."""
    macro = AhkMacro.query.filter_by(id=macro_id, user_id=current_user.id).first_or_404()
    steps = MacroStep.query.filter_by(macro_id=macro.id).order_by(MacroStep.step_order).all()
    return jsonify([s.to_dict() for s in steps])


@tools_bp.route('/api/macros/<int:macro_id>/steps', methods=['PUT'])
@login_required
def macro_update_steps(macro_id):
    """Replace all steps for a macro (bulk update after reorder/edit)."""
    macro = AhkMacro.query.filter_by(id=macro_id, user_id=current_user.id).first_or_404()

    # Delete existing steps
    MacroStep.query.filter_by(macro_id=macro.id).delete()

    steps_data = (request.get_json(silent=True) or {}).get('steps', [])
    for i, s in enumerate(steps_data):
        step = MacroStep(
            macro_id=macro.id,
            step_order=i + 1,
            action_type=s.get('action_type', 'sleep'),
            target_x=s.get('target_x'),
            target_y=s.get('target_y'),
            key_sequence=s.get('key_sequence'),
            delay_ms=s.get('delay_ms', 100),
            window_title=s.get('window_title'),
            comment=s.get('comment'),
        )
        db.session.add(step)

    db.session.commit()
    return jsonify({'success': True})


# ======================================================================
# F23: Macro Library (Main Management Page)
# ======================================================================

@tools_bp.route('/tools/macros')
@login_required
def macro_library():
    """Macro library — card grid with all macros grouped by category."""
    category = request.args.get('category', '')
    query = AhkMacro.query.filter_by(user_id=current_user.id, is_active=True)
    if category:
        query = query.filter_by(category=category)
    macros = query.order_by(AhkMacro.display_order, AhkMacro.name).all()

    # Detect hotkey conflicts
    hotkey_counts = {}
    for m in macros:
        if m.hotkey:
            hotkey_counts.setdefault(m.hotkey, []).append(m.id)
    conflicts = {hk: ids for hk, ids in hotkey_counts.items() if len(ids) > 1}

    import config as _cfg
    sync_enabled = bool(getattr(_cfg, 'AHK_AUTO_SYNC_PATH', None))
    categories = ['navigation', 'template', 'order_entry', 'dot_phrase', 'data_entry', 'custom']
    return render_template('macros.html', macros=macros, categories=categories,
                           active_category=category, conflicts=conflicts,
                           sync_enabled=sync_enabled,
                           last_sync=_last_sync_result)


@tools_bp.route('/tools/macros', methods=['POST'])
@login_required
def macro_create():
    """Create a new macro from form or code editor."""
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Name is required'}), 400

    macro = AhkMacro(
        user_id=current_user.id,
        name=name,
        description=(data.get('description') or '').strip(),
        hotkey=(data.get('hotkey') or '').strip(),
        script_content=(data.get('script_content') or '').strip(),
        category=(data.get('category') or 'custom').strip(),
    )
    db.session.add(macro)
    db.session.commit()
    _sync_ahk_to_disk(current_user.id)
    return jsonify({'success': True, 'id': macro.id})


@tools_bp.route('/tools/macros/<int:macro_id>', methods=['PUT'])
@login_required
def macro_update(macro_id):
    """Edit macro metadata and/or script content."""
    macro = AhkMacro.query.filter_by(id=macro_id, user_id=current_user.id).first_or_404()
    data = request.get_json(silent=True) or {}

    for field in ('name', 'description', 'hotkey', 'script_content', 'category'):
        if field in data:
            setattr(macro, field, (data[field] or '').strip())

    db.session.commit()
    _sync_ahk_to_disk(current_user.id)
    return jsonify({'success': True})


@tools_bp.route('/tools/macros/<int:macro_id>', methods=['DELETE'])
@login_required
def macro_delete(macro_id):
    """Soft-delete a macro (set is_active=False)."""
    macro = AhkMacro.query.filter_by(id=macro_id, user_id=current_user.id).first_or_404()
    macro.is_active = False
    db.session.commit()
    _sync_ahk_to_disk(current_user.id)
    return jsonify({'success': True, 'undo': True})


@tools_bp.route('/tools/macros/<int:macro_id>/restore', methods=['POST'])
@login_required
def macro_restore(macro_id):
    """Undo a soft-delete — restore macro."""
    macro = AhkMacro.query.filter_by(id=macro_id, user_id=current_user.id).first_or_404()
    macro.is_active = True
    db.session.commit()
    return jsonify({'success': True})


@tools_bp.route('/tools/macros/<int:macro_id>/duplicate', methods=['POST'])
@login_required
def macro_duplicate(macro_id):
    """Clone a macro with ' (Copy)' suffix."""
    original = AhkMacro.query.filter_by(id=macro_id, user_id=current_user.id).first_or_404()

    clone = AhkMacro(
        user_id=current_user.id,
        name=original.name + ' (Copy)',
        description=original.description,
        hotkey='',  # clear hotkey to avoid conflicts
        script_content=original.script_content,
        category=original.category,
    )
    db.session.add(clone)
    db.session.flush()

    # Clone steps
    for step in original.steps:
        new_step = MacroStep(
            macro_id=clone.id,
            step_order=step.step_order,
            action_type=step.action_type,
            target_x=step.target_x,
            target_y=step.target_y,
            key_sequence=step.key_sequence,
            delay_ms=step.delay_ms,
            window_title=step.window_title,
            comment=step.comment,
        )
        db.session.add(new_step)

    # Clone variables
    for var in original.variables:
        new_var = MacroVariable(
            macro_id=clone.id,
            var_name=var.var_name,
            var_label=var.var_label,
            default_value=var.default_value,
            var_type=var.var_type,
            choices=var.choices,
        )
        db.session.add(new_var)

    db.session.commit()
    return jsonify({'success': True, 'id': clone.id, 'name': clone.name})


@tools_bp.route('/tools/macros/reorder', methods=['PUT'])
@login_required
def macro_reorder():
    """Update display_order for multiple macros."""
    data = request.get_json(silent=True) or {}
    order_map = data.get('order', {})  # {macro_id: new_order}
    for mid_str, new_order in order_map.items():
        macro = AhkMacro.query.filter_by(id=int(mid_str), user_id=current_user.id).first()
        if macro:
            macro.display_order = int(new_order)
    db.session.commit()
    return jsonify({'success': True})


@tools_bp.route('/tools/macros/<int:macro_id>/preview')
@login_required
def macro_preview(macro_id):
    """Preview generated AHK code for a single macro."""
    from utils.ahk_generator import generate_macro_script
    macro = AhkMacro.query.filter_by(id=macro_id, user_id=current_user.id).first_or_404()
    steps = MacroStep.query.filter_by(macro_id=macro.id).order_by(MacroStep.step_order).all()
    variables = MacroVariable.query.filter_by(macro_id=macro.id).all()
    script = generate_macro_script(macro, steps, variables)
    return jsonify({'success': True, 'script': script, 'name': macro.name})


# ======================================================================
# F23: AHK Auto-Sync Helper
# ======================================================================

_last_sync_result = {'synced_at': None, 'error': None, 'macro_count': 0}


def _sync_ahk_to_disk(user_id):
    """Write the full AHK library to disk if AHK_AUTO_SYNC_PATH is configured.

    Never raises — sync failure is logged but never blocks the save operation.
    Returns dict with sync result.
    """
    import config
    sync_path = getattr(config, 'AHK_AUTO_SYNC_PATH', None)
    if not sync_path:
        return {'synced': False, 'reason': 'not_configured'}

    try:
        from utils.ahk_generator import generate_full_library

        macros_raw = (
            AhkMacro.query
            .filter_by(user_id=user_id, is_active=True)
            .order_by(AhkMacro.display_order, AhkMacro.name)
            .all()
        )
        macros = []
        for m in macros_raw:
            steps = MacroStep.query.filter_by(macro_id=m.id).order_by(MacroStep.step_order).all()
            variables = MacroVariable.query.filter_by(macro_id=m.id).all()
            macros.append((m, steps, variables))

        phrases = (
            DotPhrase.query
            .filter_by(user_id=user_id, is_active=True)
            .order_by(DotPhrase.category, DotPhrase.abbreviation)
            .all()
        )

        script = generate_full_library(macros, phrases)

        import os
        sync_dir = os.path.dirname(sync_path)
        if sync_dir:
            os.makedirs(sync_dir, exist_ok=True)
        with open(sync_path, 'w', encoding='utf-8') as f:
            f.write(script)

        now_str = datetime.now(timezone.utc).isoformat()
        _last_sync_result['synced_at'] = now_str
        _last_sync_result['error'] = None
        _last_sync_result['macro_count'] = len(macros) + len(phrases)
        logger.info('AHK auto-sync: wrote %d items to %s', len(macros) + len(phrases), sync_path)
        return {'synced': True, 'synced_at': now_str, 'macro_count': len(macros) + len(phrases)}
    except Exception as exc:
        _last_sync_result['error'] = str(exc)
        logger.warning('AHK auto-sync failed: %s', exc)
        return {'synced': False, 'error': str(exc)}


# ======================================================================
# F23: Import / Export
# ======================================================================

@tools_bp.route('/tools/macros/export')
@login_required
def macro_export_all():
    """Export all active macros + dot phrases as a single .ahk file."""
    from utils.ahk_generator import generate_full_library
    from flask import Response

    macros_raw = (AhkMacro.query
                  .filter_by(user_id=current_user.id, is_active=True)
                  .order_by(AhkMacro.display_order, AhkMacro.name)
                  .all())
    macros = []
    for m in macros_raw:
        steps = MacroStep.query.filter_by(macro_id=m.id).order_by(MacroStep.step_order).all()
        variables = MacroVariable.query.filter_by(macro_id=m.id).all()
        macros.append((m, steps, variables))

    phrases = (DotPhrase.query
               .filter_by(user_id=current_user.id, is_active=True)
               .order_by(DotPhrase.category, DotPhrase.abbreviation)
               .all())

    script = generate_full_library(macros, phrases)
    return Response(
        script,
        mimetype='text/plain',
        headers={'Content-Disposition': 'attachment; filename=carecompanion_macros.ahk'},
    )


@tools_bp.route('/tools/macros/export/<int:macro_id>')
@login_required
def macro_export_single(macro_id):
    """Export a single macro as an .ahk file."""
    from utils.ahk_generator import generate_macro_script
    from flask import Response

    macro = AhkMacro.query.filter_by(id=macro_id, user_id=current_user.id).first_or_404()
    steps = MacroStep.query.filter_by(macro_id=macro.id).order_by(MacroStep.step_order).all()
    variables = MacroVariable.query.filter_by(macro_id=macro.id).all()
    script = generate_macro_script(macro, steps, variables)

    safe_name = macro.name.replace(' ', '_').lower()[:40]
    return Response(
        script,
        mimetype='text/plain',
        headers={'Content-Disposition': f'attachment; filename={safe_name}.ahk'},
    )


@tools_bp.route('/tools/macros/import', methods=['POST'])
@login_required
def macro_import_ahk():
    """Import .ahk file — parse hotkeys and hotstrings into macros/dot phrases."""
    from utils.ahk_generator import parse_ahk_hotstring

    content = None
    if request.is_json:
        content = (request.get_json(silent=True) or {}).get('content', '')
    elif request.files.get('file'):
        content = request.files['file'].read().decode('utf-8', errors='replace')

    if not content:
        return jsonify({'success': False, 'error': 'No content provided'}), 400

    imported_phrases = 0
    imported_macros = 0

    for line in content.split('\n'):
        line = line.strip()
        parsed = parse_ahk_hotstring(line)
        if parsed:
            abbrev, expansion = parsed
            existing = DotPhrase.query.filter_by(
                user_id=current_user.id, abbreviation=abbrev
            ).first()
            if not existing:
                import re as _re
                placeholders = json.dumps(sorted(set(_re.findall(r'\{(\w+)\}', expansion))))
                dp = DotPhrase(
                    user_id=current_user.id,
                    abbreviation=abbrev,
                    expansion=expansion,
                    category='custom',
                    placeholders=placeholders,
                )
                db.session.add(dp)
                imported_phrases += 1

    db.session.commit()
    _sync_ahk_to_disk(current_user.id)
    return jsonify({
        'success': True,
        'imported_phrases': imported_phrases,
        'imported_macros': imported_macros,
    })


@tools_bp.route('/tools/macros/export-json')
@login_required
def macro_export_json():
    """Export full library as JSON backup."""
    macros_raw = (AhkMacro.query
                  .filter_by(user_id=current_user.id)
                  .order_by(AhkMacro.display_order)
                  .all())
    macros_list = []
    for m in macros_raw:
        steps = MacroStep.query.filter_by(macro_id=m.id).order_by(MacroStep.step_order).all()
        variables = MacroVariable.query.filter_by(macro_id=m.id).all()
        macros_list.append({
            'name': m.name,
            'description': m.description,
            'hotkey': m.hotkey,
            'script_content': m.script_content,
            'category': m.category,
            'is_active': m.is_active,
            'display_order': m.display_order,
            'steps': [s.to_dict() for s in steps],
            'variables': [v.to_dict() for v in variables],
        })

    phrases = DotPhrase.query.filter_by(user_id=current_user.id).order_by(DotPhrase.abbreviation).all()
    phrases_list = [{
        'abbreviation': p.abbreviation,
        'expansion': p.expansion,
        'category': p.category,
        'placeholders': p.placeholders,
        'use_count': p.use_count,
        'is_active': p.is_active,
    } for p in phrases]

    from flask import Response
    backup = json.dumps({
        'version': 1,
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'macros': macros_list,
        'dot_phrases': phrases_list,
    }, indent=2)
    return Response(
        backup,
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename=carecompanion_macros_backup.json'},
    )


@tools_bp.route('/tools/macros/import-json', methods=['POST'])
@login_required
def macro_import_json():
    """Import JSON backup to restore library."""
    content = None
    if request.is_json:
        content = request.get_json(silent=True)
    elif request.files.get('file'):
        raw = request.files['file'].read().decode('utf-8', errors='replace')
        try:
            content = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return jsonify({'success': False, 'error': 'Invalid JSON file'}), 400

    if not content or not isinstance(content, dict):
        return jsonify({'success': False, 'error': 'No valid JSON data provided'}), 400

    imported_macros = 0
    imported_phrases = 0

    for m_data in content.get('macros', []):
        name = (m_data.get('name') or '').strip()
        if not name:
            continue
        macro = AhkMacro(
            user_id=current_user.id,
            name=name,
            description=m_data.get('description', ''),
            hotkey=m_data.get('hotkey', ''),
            script_content=m_data.get('script_content', ''),
            category=m_data.get('category', 'custom'),
            is_active=m_data.get('is_active', True),
            display_order=m_data.get('display_order', 0),
        )
        db.session.add(macro)
        db.session.flush()

        for s_data in m_data.get('steps', []):
            step = MacroStep(
                macro_id=macro.id,
                step_order=s_data.get('step_order', 0),
                action_type=s_data.get('action_type', 'sleep'),
                target_x=s_data.get('target_x'),
                target_y=s_data.get('target_y'),
                key_sequence=s_data.get('key_sequence'),
                delay_ms=s_data.get('delay_ms', 100),
                window_title=s_data.get('window_title'),
                comment=s_data.get('comment'),
            )
            db.session.add(step)

        for v_data in m_data.get('variables', []):
            var = MacroVariable(
                macro_id=macro.id,
                var_name=v_data.get('var_name', ''),
                var_label=v_data.get('var_label', ''),
                default_value=v_data.get('default_value', ''),
                var_type=v_data.get('var_type', 'text'),
                choices=v_data.get('choices'),
            )
            db.session.add(var)
        imported_macros += 1

    for p_data in content.get('dot_phrases', []):
        abbrev = (p_data.get('abbreviation') or '').strip()
        if not abbrev:
            continue
        existing = DotPhrase.query.filter_by(user_id=current_user.id, abbreviation=abbrev).first()
        if existing:
            continue
        dp = DotPhrase(
            user_id=current_user.id,
            abbreviation=abbrev,
            expansion=p_data.get('expansion', ''),
            category=p_data.get('category', 'custom'),
            placeholders=p_data.get('placeholders', '[]'),
            use_count=p_data.get('use_count', 0),
            is_active=p_data.get('is_active', True),
        )
        db.session.add(dp)
        imported_phrases += 1

    db.session.commit()
    _sync_ahk_to_disk(current_user.id)
    return jsonify({
        'success': True,
        'imported_macros': imported_macros,
        'imported_phrases': imported_phrases,
    })


@tools_bp.route('/tools/macros/sync', methods=['POST'])
@login_required
def macro_sync():
    """Manual sync — write AHK library to disk on demand."""
    result = _sync_ahk_to_disk(current_user.id)
    if result.get('synced'):
        return jsonify({
            'success': True,
            'synced_at': result['synced_at'],
            'macro_count': result['macro_count'],
        })
    return jsonify({
        'success': False,
        'error': result.get('error') or result.get('reason', 'unknown'),
    })


# ======================================================================
# F19a: Result Template Library
# ======================================================================

TEMPLATE_CATEGORIES = ['normal', 'abnormal', 'critical', 'follow_up', 'referral']


@tools_bp.route('/tools/templates')
@login_required
def template_library():
    """Result template library — My / Shared / System tabs."""
    uid = current_user.id

    my_templates = (
        ResultTemplate.query
        .filter_by(user_id=uid, is_active=True)
        .order_by(ResultTemplate.category, ResultTemplate.display_order)
        .all()
    )
    shared_templates = (
        ResultTemplate.query
        .filter(ResultTemplate.user_id != uid, ResultTemplate.user_id != None,
                ResultTemplate.is_shared == True, ResultTemplate.is_active == True)
        .order_by(ResultTemplate.category, ResultTemplate.display_order)
        .all()
    )
    system_templates = (
        ResultTemplate.query
        .filter_by(user_id=None, is_active=True)
        .order_by(ResultTemplate.category, ResultTemplate.display_order)
        .all()
    )

    return render_template(
        'result_template_library.html',
        my_templates=my_templates,
        shared_templates=shared_templates,
        system_templates=system_templates,
        categories=TEMPLATE_CATEGORIES,
    )


@tools_bp.route('/tools/templates/create', methods=['POST'])
@login_required
def template_create():
    """Create a new result template owned by the current user."""
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    category = (data.get('category') or '').strip()
    body = (data.get('body_template') or '').strip()

    if not name or not category or not body:
        return jsonify({'success': False, 'error': 'Name, category, and body are required'}), 400
    if category not in TEMPLATE_CATEGORIES:
        return jsonify({'success': False, 'error': 'Invalid category'}), 400

    t = ResultTemplate(
        name=name,
        category=category,
        body_template=body,
        user_id=current_user.id,
    )
    db.session.add(t)
    db.session.commit()
    return jsonify({'success': True, 'id': t.id})


@tools_bp.route('/tools/templates/<int:tid>/update', methods=['POST'])
@login_required
def template_update(tid):
    """Update a result template (owner or admin only)."""
    t = ResultTemplate.query.get(tid)
    if not t:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    if t.user_id != current_user.id and current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Permission denied'}), 403

    data = request.get_json(silent=True) or {}
    if 'name' in data:
        t.name = (data['name'] or '').strip()
    if 'category' in data:
        cat = (data['category'] or '').strip()
        if cat and cat in TEMPLATE_CATEGORIES:
            t.category = cat
    if 'body_template' in data:
        t.body_template = (data['body_template'] or '').strip()

    db.session.commit()
    return jsonify({'success': True})


@tools_bp.route('/tools/templates/<int:tid>/delete', methods=['POST'])
@login_required
def template_delete(tid):
    """Soft-delete a template (set is_active=False). Owner or admin."""
    t = ResultTemplate.query.get(tid)
    if not t:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    if t.user_id != current_user.id and current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Permission denied'}), 403

    t.is_active = False
    db.session.commit()
    return jsonify({'success': True})


@tools_bp.route('/tools/templates/<int:tid>/share', methods=['POST'])
@login_required
def template_share(tid):
    """Toggle is_shared on a user-owned template."""
    t = ResultTemplate.query.get(tid)
    if not t:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    if t.user_id != current_user.id and current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Permission denied'}), 403

    t.is_shared = not t.is_shared
    db.session.commit()
    return jsonify({'success': True, 'is_shared': t.is_shared})


@tools_bp.route('/tools/templates/<int:tid>/fork', methods=['POST'])
@login_required
def template_fork(tid):
    """Fork a shared or system template into user's collection."""
    t = ResultTemplate.query.get(tid)
    if not t:
        return jsonify({'success': False, 'error': 'Not found'}), 404

    copy = ResultTemplate(
        name=t.name + ' (My Copy)',
        category=t.category,
        body_template=t.body_template,
        user_id=current_user.id,
        copied_from_id=t.id,
    )
    db.session.add(copy)
    db.session.commit()
    return jsonify({'success': True, 'id': copy.id})


@tools_bp.route('/tools/templates/<int:tid>/flag-reviewed', methods=['POST'])
@login_required
def template_flag_reviewed(tid):
    """Mark a template as legally reviewed (provider/admin)."""
    if current_user.role not in ('admin', 'provider'):
        return jsonify({'success': False, 'error': 'Permission denied'}), 403

    t = ResultTemplate.query.get(tid)
    if not t:
        return jsonify({'success': False, 'error': 'Not found'}), 404

    t.legal_reviewed = True
    t.legal_reviewed_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({'success': True})

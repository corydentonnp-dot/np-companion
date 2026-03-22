"""
CareCompanion — Medication Reference Routes
File: routes/medref.py

Feature F10: Searchable clinical drug reference powered by:
- RxNorm (NIH/NLM) — drug name normalization, properties, classes
- OpenFDA Drug Label — FDA-approved prescribing information
- OpenFDA FAERS — real-world adverse event reports
- OpenFDA Recalls — active drug recalls

No patient data is sent to any external API. Only drug names and RXCUI
codes are transmitted.
"""

import logging
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user

from models import db

logger = logging.getLogger(__name__)

medref_bp = Blueprint('medref', __name__)


@medref_bp.route('/medref')
@login_required
def index():
    """Medication Reference: API-powered drug lookup."""
    return render_template('medref.html')


@medref_bp.route('/api/medref/lookup')
@login_required
def lookup():
    """
    Look up a drug by name. Returns combined data from RxNorm + OpenFDA.
    Query param: q (drug name string)
    """
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'error': 'Enter at least 2 characters'})
    if len(query) > 200:
        return jsonify({'error': 'Query too long'}), 400

    result = {
        'query': query,
        'rxcui': '',
        'brand_name': '',
        'generic_name': '',
        'dose_strength': '',
        'dose_form': '',
        'route': '',
        'drug_class': '',
        'label': {},
        'faers': [],
        'recalls': [],
    }

    # 1. RxNorm: resolve name → RXCUI → properties
    rxcui = ''
    try:
        from app.services.api.rxnorm import RxNormService
        rxnorm_svc = RxNormService(db)
        cui_result = rxnorm_svc.get_rxcui(query)
        if cui_result and cui_result.get('rxcui'):
            rxcui = cui_result['rxcui']
            result['rxcui'] = rxcui

            props = rxnorm_svc.get_properties(rxcui)
            if props:
                result['generic_name'] = props.get('name', '')
                result['dose_form'] = props.get('dose_form', '')

            # Get brand name
            try:
                from app.services.api.rxnorm import RxNormService as _Rx
                import urllib.request
                import json as _json
                brand_data = _fetch_rxnorm('/rxcui/' + rxcui + '/related.json?tty=BN')
                if brand_data:
                    groups = (brand_data.get('relatedGroup') or {}).get('conceptGroup', [])
                    for g in groups:
                        pl = g.get('conceptProperties', [])
                        if pl:
                            result['brand_name'] = pl[0].get('name', '')
                            break
            except Exception:
                pass

            # Get ingredient for generic name if not already set
            if not result['generic_name']:
                ing = rxnorm_svc.get_ingredient(rxcui)
                if ing and ing.get('name'):
                    result['generic_name'] = ing['name']

        else:
            # Try approximate match
            approx = _fetch_rxnorm('/approximateTerm.json?term=' + _url_quote(query))
            if approx:
                candidates = (approx.get('approximateGroup') or {}).get('candidate', [])
                if candidates:
                    rxcui = candidates[0].get('rxcui', '')
                    result['rxcui'] = rxcui
                    result['generic_name'] = candidates[0].get('name', query)
    except Exception as e:
        logger.debug('RxNorm lookup failed: %s', e)

    # Parse dose from concept name
    if result['generic_name']:
        import re
        m = re.search(r'(\d+(?:\.\d+)?\s*(?:MG|MCG|ML|UNITS?|%|MEQ)(?:/[\d.]+\s*(?:MG|MCG|ML|HR))?)', result['generic_name'], re.IGNORECASE)
        if m:
            result['dose_strength'] = m.group(1).strip()
        fm = re.search(r'(?:MG|MCG|ML|UNITS?|%|MEQ|HR)\s+(Oral|Injectable|Topical)?\s*(Tablet|Capsule|Solution|Suspension|Injection|Cream|Ointment|Gel|Patch|Spray|Inhaler)?', result['generic_name'], re.IGNORECASE)
        if fm:
            result['route'] = (fm.group(1) or '').strip()
            result['dose_form'] = result['dose_form'] or (fm.group(2) or '').strip()

    # 2. RxClass: therapeutic class
    try:
        from app.services.api.rxclass import RxClassService
        rxclass_svc = RxClassService(db)
        if rxcui:
            classes = rxclass_svc.get_classes_for_drug(rxcui)
            if classes:
                # Pick first pharmacologic class
                for c in classes:
                    if c.get('class_name'):
                        result['drug_class'] = c['class_name']
                        break
        elif query:
            classes = rxclass_svc.get_classes_for_drug_name(query)
            if classes:
                for c in classes:
                    if c.get('class_name'):
                        result['drug_class'] = c['class_name']
                        break
    except Exception as e:
        logger.debug('RxClass lookup failed: %s', e)

    # 3. OpenFDA Label: prescribing information
    try:
        from app.services.api.openfda_labels import OpenFDALabelsService
        label_svc = OpenFDALabelsService(db)
        label = None
        if rxcui:
            label = label_svc.get_label_by_rxcui(rxcui)
        if not label:
            label = label_svc.get_label_by_name(query)
        if label:
            result['label'] = {
                'indications': label.get('indications_and_usage', ''),
                'dosage_admin': label.get('dosage_and_administration', ''),
                'boxed_warning': label.get('boxed_warning', ''),
                'warnings': label.get('warnings_and_cautions', '') or label.get('warnings', ''),
                'contraindications': label.get('contraindications', ''),
                'adverse_reactions': label.get('adverse_reactions', ''),
                'drug_interactions': label.get('drug_interactions', ''),
                'pregnancy': label.get('pregnancy', '') or label.get('nursing_mothers', ''),
                'renal_hepatic': label.get('use_in_specific_populations', ''),
            }
    except Exception as e:
        logger.debug('OpenFDA label lookup failed: %s', e)

    # 4. OpenFDA FAERS: real-world adverse events
    try:
        from app.services.api.openfda_adverse_events import OpenFDAAdverseEventsService
        faers_svc = OpenFDAAdverseEventsService(db)
        drug_name = result['generic_name'] or query
        events = faers_svc.get_top_adverse_events(drug_name, top_n=5)
        if events:
            result['faers'] = [
                {'reaction': e.get('reaction', ''), 'count': e.get('count', 0)}
                for e in events
            ]
    except Exception as e:
        logger.debug('FAERS lookup failed: %s', e)

    # 5. OpenFDA Recalls
    try:
        from app.services.api.openfda_recalls import OpenFDARecallsService
        recall_svc = OpenFDARecallsService(db)
        drug_name = result['generic_name'] or query
        recalls = recall_svc.check_drug_for_recalls(drug_name.split()[0] if drug_name else query)
        if recalls:
            result['recalls'] = [
                {
                    'classification': r.get('classification', ''),
                    'reason': r.get('reason', ''),
                    'status': r.get('status', ''),
                }
                for r in recalls[:3]
            ]
    except Exception as e:
        logger.debug('Recall lookup failed: %s', e)

    # 6. F10d: RxNorm history status — check for obsoleted/remapped drugs
    result['guideline_flag'] = None
    if rxcui:
        try:
            history = _fetch_rxnorm('/rxcui/' + rxcui + '/historystatus.json')
            if history:
                status_info = (history.get('rxcuiStatusHistory') or {}).get('metaData') or {}
                status = (status_info.get('status') or '').lower()
                if status in ('remapped', 'obsolete', 'retired'):
                    remapped_to = ''
                    remapped_data = (history.get('rxcuiStatusHistory') or {}).get('derivedConcepts') or {}
                    remapped_list = remapped_data.get('remappedConcept', [])
                    if remapped_list and isinstance(remapped_list, list):
                        remapped_to = remapped_list[0].get('remappedRxCui', '')
                    result['guideline_flag'] = {
                        'status': status,
                        'message': f'This drug entry has been {status} in the RxNorm database. Prescribing information may be outdated.',
                        'remapped_to': remapped_to,
                    }
        except Exception:
            pass

    # If we got no data at all, return error
    if not result['rxcui'] and not result['label'] and not result['generic_name']:
        return jsonify({'error': f'No results found for "{query}". Try a different spelling or generic name.'})

    # Fill in brand/generic from query if still empty
    if not result['brand_name'] and not result['generic_name']:
        result['generic_name'] = query.title()

    return jsonify(result)


# ======================================================================
# F10d: Guideline Review Admin Page
# ======================================================================

@medref_bp.route('/medref/review-needed')
@login_required
def review_needed():
    """
    Guideline review page — shows MedicationEntry records that have been
    flagged (guideline_review_flag=True) or whose RxNorm RXCUI has a
    non-active history status (obsolete / remapped / retired).
    """
    from routes.auth import require_role
    from models.medication import MedicationEntry

    # Accessible to providers and admins
    if current_user.role not in ('provider', 'admin'):
        flash('You do not have permission to access that page.', 'error')
        return redirect(url_for('medref.index'))

    filter_status = request.args.get('filter', 'all')

    # Get all active medication entries visible to this user
    entries = MedicationEntry.query.filter(
        db.or_(
            MedicationEntry.user_id == current_user.id,
            MedicationEntry.is_shared == True,           # noqa: E712
            MedicationEntry.user_id == None,             # noqa: E711
        )
    ).order_by(MedicationEntry.drug_name).all()

    # Check RxNorm history status for each entry and build flagged list
    flagged = []
    for entry in entries:
        status_info = None

        # If already manually flagged
        if entry.guideline_review_flag:
            status_info = {'status': 'flagged', 'message': 'Manually flagged for review'}

        # Try RxNorm history check by drug name
        if not status_info:
            try:
                from app.services.api.rxnorm import RxNormService
                rxnorm_svc = RxNormService(db)
                cui_result = rxnorm_svc.get_rxcui(entry.drug_name)
                if cui_result and cui_result.get('rxcui'):
                    rxcui = cui_result['rxcui']
                    history = _fetch_rxnorm('/rxcui/' + rxcui + '/historystatus.json')
                    if history:
                        meta = (history.get('rxcuiStatusHistory') or {}).get('metaData') or {}
                        status = (meta.get('status') or '').lower()
                        if status in ('remapped', 'obsolete', 'retired'):
                            remapped_to = ''
                            derived = (history.get('rxcuiStatusHistory') or {}).get('derivedConcepts') or {}
                            remapped_list = derived.get('remappedConcept', [])
                            if remapped_list and isinstance(remapped_list, list):
                                remapped_to = remapped_list[0].get('remappedRxCui', '')
                            status_info = {
                                'status': status,
                                'rxcui': rxcui,
                                'remapped_to': remapped_to,
                                'message': f'RxNorm status: {status}',
                            }
            except Exception as e:
                logger.debug('RxNorm history check failed for %s: %s', entry.drug_name, e)

        if status_info:
            # Apply filter
            if filter_status != 'all':
                if filter_status == 'dismissed' and entry.reviewed_at is None:
                    continue
                if filter_status != 'dismissed' and filter_status != status_info['status']:
                    continue
                if filter_status == 'dismissed' and entry.reviewed_at is None:
                    continue
            # Skip dismissed entries unless filtering for them
            if filter_status != 'dismissed' and entry.reviewed_at is not None:
                continue

            flagged.append({
                'entry': entry,
                'status': status_info['status'],
                'message': status_info['message'],
                'rxcui': status_info.get('rxcui', ''),
                'remapped_to': status_info.get('remapped_to', ''),
            })

    return render_template(
        'medref_review.html',
        flagged=flagged,
        flagged_count=len(flagged),
        filter_status=filter_status,
    )


@medref_bp.route('/medref/review-needed/<int:entry_id>/dismiss', methods=['POST'])
@login_required
def dismiss_review(entry_id):
    """Mark a MedicationEntry as reviewed / dismissed."""
    from models.medication import MedicationEntry

    if current_user.role not in ('provider', 'admin'):
        return jsonify({'error': 'Permission denied'}), 403

    entry = MedicationEntry.query.get_or_404(entry_id)
    entry.reviewed_at = datetime.now(timezone.utc)
    entry.reviewed_by = current_user.id
    db.session.commit()
    flash(f'"{entry.drug_name}" marked as reviewed.', 'success')
    return redirect(url_for('medref.review_needed'))


@medref_bp.route('/medref/review-needed/<int:entry_id>/update-rxcui', methods=['POST'])
@login_required
def update_rxcui(entry_id):
    """Update a MedicationEntry's drug info when RxNorm has remapped the RXCUI."""
    from models.medication import MedicationEntry

    if current_user.role not in ('provider', 'admin'):
        return jsonify({'error': 'Permission denied'}), 403

    entry = MedicationEntry.query.get_or_404(entry_id)
    new_rxcui = request.form.get('new_rxcui', '').strip()

    if new_rxcui:
        # Look up the new drug name from RxNorm
        try:
            from app.services.api.rxnorm import RxNormService
            rxnorm_svc = RxNormService(db)
            props = rxnorm_svc.get_properties(new_rxcui)
            if props and props.get('name'):
                old_name = entry.drug_name
                entry.drug_name = props['name']
                entry.guideline_review_flag = False
                entry.reviewed_at = datetime.now(timezone.utc)
                entry.reviewed_by = current_user.id
                db.session.commit()
                flash(f'Updated "{old_name}" → "{entry.drug_name}".', 'success')
            else:
                flash('Could not resolve the new RXCUI. No changes made.', 'error')
        except Exception as e:
            logger.warning('RXCUI update failed: %s', e)
            flash('Update failed. Please try again.', 'error')
    else:
        flash('No new RXCUI provided.', 'error')

    return redirect(url_for('medref.review_needed'))


def _fetch_rxnorm(path):
    """Quick RxNorm REST fetch for endpoints not covered by RxNormService."""
    import urllib.request
    import json as _json
    url = 'https://rxnav.nlm.nih.gov/REST' + path
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return _json.loads(resp.read().decode())
    except Exception:
        return None


@medref_bp.route('/api/medref/pricing')
@login_required
def pricing():
    """
    Look up pricing for a drug via the Three-Tier Waterfall.
    Query params: rxcui, ndc, drug_name, strength
    Returns JSON PricingResult.
    """
    rxcui = request.args.get('rxcui', '').strip() or None
    ndc = request.args.get('ndc', '').strip() or None
    drug_name = request.args.get('drug_name', '').strip() or None
    strength = request.args.get('strength', '').strip() or None

    if not drug_name and not rxcui and not ndc:
        return jsonify({'error': 'Provide at least drug_name, rxcui, or ndc'})

    try:
        from app.services.pricing_service import PricingService
        svc = PricingService(db)
        result = svc.get_pricing(
            rxcui=rxcui, ndc=ndc, drug_name=drug_name, strength=strength,
        )
        return jsonify(result)
    except Exception as e:
        logger.debug('Pricing lookup failed: %s', e)
        return jsonify({
            'source': 'none',
            'price_monthly_estimate': None,
            'badge_color': None,
            'assistance_programs': [],
        })


def _url_quote(s):
    """URL-encode a string."""
    import urllib.parse
    return urllib.parse.quote(s)

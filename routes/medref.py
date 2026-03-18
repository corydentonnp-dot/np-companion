"""
NP Companion — Medication Reference Routes
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
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required

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

    # If we got no data at all, return error
    if not result['rxcui'] and not result['label'] and not result['generic_name']:
        return jsonify({'error': f'No results found for "{query}". Try a different spelling or generic name.'})

    # Fill in brand/generic from query if still empty
    if not result['brand_name'] and not result['generic_name']:
        result['generic_name'] = query.title()

    return jsonify(result)


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


def _url_quote(s):
    """URL-encode a string."""
    import urllib.parse
    return urllib.parse.quote(s)

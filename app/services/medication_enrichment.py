"""
CareCompanion — Medication Enrichment Service

RxNorm API enrichment and medication frequency normalization.
Extracted from routes/patient.py (Band 3 B1.7).
"""

import json
import logging
import re as _re

from models import db
from models.api_cache import RxNormCache

logger = logging.getLogger(__name__)


# ======================================================================
# RxNorm API helpers
# ======================================================================

def fetch_rxnorm_api(path):
    """Fetch a single RxNorm REST API endpoint, return parsed JSON or None."""
    import urllib.request
    url = 'https://rxnav.nlm.nih.gov/REST' + path
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def enrich_rxnorm_single(rxcui):
    """
    Look up one RXCUI via the NIH RxNorm API.

    Returns dict with: brand_name, generic_name, dose_strength, dose_form,
    route, tty, ndc. Returns None on failure.
    """
    # 1. Get concept properties
    props_data = fetch_rxnorm_api(f'/rxcui/{rxcui}/properties.json')
    if not props_data:
        return None
    concept = (props_data.get('properties') or {})
    name = concept.get('name', '')
    tty = concept.get('tty', '')

    # 2. Get related ingredient (generic name)
    generic_name = ''
    related_in = fetch_rxnorm_api(f'/rxcui/{rxcui}/related.json?tty=IN')
    if related_in:
        groups = (related_in.get('relatedGroup') or {}).get('conceptGroup', [])
        for group in groups:
            props_list = group.get('conceptProperties', [])
            if props_list:
                generic_name = props_list[0].get('name', '')
                break

    # 3. Get related brand name
    brand_name = ''
    related_bn = fetch_rxnorm_api(f'/rxcui/{rxcui}/related.json?tty=BN')
    if related_bn:
        groups = (related_bn.get('relatedGroup') or {}).get('conceptGroup', [])
        for group in groups:
            props_list = group.get('conceptProperties', [])
            if props_list:
                brand_name = props_list[0].get('name', '')
                break

    # 4. Parse dose strength and form from the concept name
    dose_strength = ''
    dose_form = ''
    route = ''
    m = _re.search(
        r'(\d+(?:\.\d+)?\s*(?:MG|MCG|ML|UNITS?|%|MEQ)(?:/[\d.]+\s*(?:MG|MCG|ML|HR))?)',
        name, _re.IGNORECASE
    )
    if m:
        dose_strength = m.group(1).strip()
    form_m = _re.search(
        r'(?:MG|MCG|ML|UNITS?|%|MEQ|HR)\s+(Oral|Injectable|Topical|Inhalant|Nasal|Ophthalmic|Otic|Rectal|Vaginal|Transdermal)?\s*'
        r'(Tablet|Capsule|Solution|Suspension|Injection|Cream|Ointment|Gel|Patch|Spray|Inhaler|Drops|Powder|Suppository|Film|Lozenge|Pack|Kit)?',
        name, _re.IGNORECASE
    )
    if form_m:
        route = (form_m.group(1) or '').strip()
        dose_form = (form_m.group(2) or '').strip()

    if tty == 'BN':
        brand_name = brand_name or name
    elif tty == 'IN':
        generic_name = generic_name or name

    # 5. Get first NDC code
    ndc = ''
    ndc_data = fetch_rxnorm_api(f'/rxcui/{rxcui}/ndcs.json')
    if ndc_data:
        ndc_list = (ndc_data.get('ndcGroup') or {}).get('ndcList', {}).get('ndc', [])
        if ndc_list:
            ndc = ndc_list[0]

    return {
        'brand_name': brand_name,
        'generic_name': generic_name or name,
        'dose_strength': dose_strength,
        'dose_form': dose_form,
        'route': route,
        'tty': tty,
        'ndc': ndc,
    }


def enrich_rxnorm(rxcui, drug_name_fallback='', cache_only=False):
    """
    Return an RxNormCache row for the given RXCUI.

    Resolution order:
      1. Check local RxNormCache (no network).
      2. If cache_only=False, try RxNormService; then raw RxNorm API.
    If rxcui is empty, tries approximate match by drug name first.
    """
    import urllib.parse

    rxcui = (rxcui or '').strip()

    # Fallback: look up by name if no CUI provided
    if not rxcui and drug_name_fallback:
        if not cache_only:
            try:
                from app.services.api.rxnorm import RxNormService
                svc = RxNormService(db)
                result = svc.get_rxcui(drug_name_fallback)
                if result and result.get('rxcui'):
                    rxcui = result['rxcui']
            except Exception:
                pass

            if not rxcui:
                data = fetch_rxnorm_api(
                    '/rxcui.json?name=' + urllib.parse.quote(drug_name_fallback) + '&search=2'
                )
                if data:
                    group = data.get('idGroup', {})
                    rxn_list = group.get('rxnormId', [])
                    if rxn_list:
                        rxcui = rxn_list[0]

    if not rxcui:
        return None

    # 1. Check local cache
    cached = RxNormCache.query.filter_by(rxcui=rxcui).first()
    if cached:
        return cached

    if cache_only:
        return None

    # 2. Query API
    info = enrich_rxnorm_single(rxcui)
    if not info:
        return None

    entry = RxNormCache(
        rxcui=rxcui,
        brand_name=info['brand_name'],
        generic_name=info['generic_name'],
        dose_strength=info['dose_strength'],
        dose_form=info['dose_form'],
        route=info['route'],
        tty=info['tty'],
        ndc=info.get('ndc', ''),
    )
    try:
        db.session.add(entry)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return RxNormCache.query.filter_by(rxcui=rxcui).first()

    return entry


def standardize_frequency(raw):
    """
    Normalize free-text medication instructions to a standard abbreviation.

    Examples:
      "take 1 tablet by mouth once daily" -> "Daily"
      "twice daily" -> "BID"
      "every 8 hours" -> "Q8H"
      "as needed" -> "PRN"
    """
    if not raw:
        return ''
    t = raw.strip()
    low = t.lower()

    _freq_map = [
        (r'\b(?:four times\s+(?:a\s+)?daily|4\s*(?:times\s*)?(?:a\s+)?day|QID)\b', 'QID'),
        (r'\b(?:three times\s+(?:a\s+)?daily|3\s*(?:times\s*)?(?:a\s+)?day|TID)\b', 'TID'),
        (r'\b(?:twice\s+(?:a\s+)?daily|2\s*(?:times?\s*)?(?:a\s+)?day|BID|b\.i\.d)\b', 'BID'),
        (r'\b(?:once\s+(?:a\s+)?daily|(?:1\s*(?:time\s*)?(?:a\s+)?day)|daily|QD|q\.?d)\b', 'Daily'),
        (r'\bevery\s*(\d+)\s*h(?:ou)?rs?\b', r'Q\1H'),
        (r'\b(?:every\s*(?:other\s+)?day|QOD|q\.?o\.?d)\b', 'QOD'),
        (r'\b(?:once\s+(?:a\s+)?week|weekly|1\s*(?:time\s*)?(?:a\s+)?week|QW|q\.?w)\b', 'Weekly'),
        (r'\b(?:twice\s+(?:a\s+)?week|2\s*(?:times?\s*)?(?:a\s+)?week|BIW)\b', 'BIW'),
        (r'\b(?:once\s+(?:a\s+)?month|monthly|1\s*(?:time\s*)?(?:a\s+)?month)\b', 'Monthly'),
        (r'\b(?:every\s*(\d+)\s*weeks?)\b', r'Q\1W'),
        (r'\b(?:every\s*(\d+)\s*months?)\b', r'Q\1M'),
        (r'\b(?:every\s*(\d+)\s*days?)\b', r'Q\1D'),
        (r'\b(?:at\s+(?:bed\s*time|HS|h\.?s\.?)|(?:bed\s*time))\b', 'QHS'),
        (r'\b(?:(?:as\s+)?(?:needed|necessary)|PRN|p\.?r\.?n)\b', 'PRN'),
        (r'\b(?:in\s+the\s+morning|(?:every\s+)?(?:AM|a\.m\.))\b', 'QAM'),
        (r'\b(?:in\s+the\s+evening|(?:every\s+)?(?:PM|p\.m\.))\b', 'QPM'),
    ]
    for pattern, replacement in _freq_map:
        match = _re.search(pattern, low, _re.IGNORECASE)
        if match:
            if '\\1' in replacement:
                return _re.sub(pattern, replacement, low, count=1, flags=_re.IGNORECASE).upper()
            return replacement
    return t


def parse_dose_fallback(drug_name, frequency):
    """
    Last-resort dose extraction when RxNorm lookup fails.

    Parses dose from the drug name string or the Instructions/frequency field.
    Returns (dose_str, form_str) or ('', '').
    """
    for text in [drug_name, frequency]:
        if not text:
            continue
        m = _re.search(
            r'(\d+(?:\.\d+)?\s*(?:mg|mcg|ml|units?|%|meq|g|iu)(?:/[\d.]+\s*(?:mg|mcg|ml|hr))?)',
            text, _re.IGNORECASE
        )
        if m:
            dose = m.group(1).strip()
            fm = _re.search(
                r'(?:mg|mcg|ml|units?|%|meq|g|iu|hr)\s+'
                r'(oral|injectable|topical|inhalant|nasal|ophthalmic)?\s*'
                r'(tablet|capsule|solution|suspension|injection|cream|ointment|gel|patch|spray|inhaler|drops|powder|suppository)?',
                text, _re.IGNORECASE
            )
            form = ''
            if fm:
                parts = [x for x in [fm.group(1), fm.group(2)] if x]
                form = ' '.join(parts).strip()
            return dose, form
    return '', ''


def enrich_medications(medications, cache_only=False):
    """
    Annotate a list of PatientMedication objects with RxNorm data.

    Adds .rx_info attribute (RxNormCache row or None) and .std_frequency.
    Falls back to regex-based dose parsing when RxNorm lookup fails.
    When cache_only=True, skip all network calls.
    """
    for med in medications:
        med.rx_info = enrich_rxnorm(
            getattr(med, 'rxnorm_cui', ''),
            drug_name_fallback=med.drug_name,
            cache_only=cache_only,
        )
        med.std_frequency = standardize_frequency(med.frequency)
        if not med.rx_info or not getattr(med.rx_info, 'dose_strength', ''):
            dose, form = parse_dose_fallback(med.drug_name, med.frequency)
            if dose:
                if not med.rx_info:
                    class _FallbackRx:
                        pass
                    med.rx_info = _FallbackRx()
                    med.rx_info.brand_name = ''
                    med.rx_info.generic_name = ''
                    med.rx_info.route = ''
                    med.rx_info.tty = ''
                med.rx_info.dose_strength = dose
                med.rx_info.dose_form = form if form else getattr(med.rx_info, 'dose_form', '')
    return medications

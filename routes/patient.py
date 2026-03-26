"""
CareCompanion — Patient Chart View (F10e) — Widget-Based Layout

File location: carecompanion/routes/patient.py

Draggable/resizable widget-based patient chart with:
  - XML upload (manual CDA import)
  - Medications (active/inactive)
  - Diagnoses (acute vs chronic)
  - Labs (Epic-style spreadsheet with graphing)
  - USPSTF recommendations
  - Specialists
  - Note Generator
  - Vitals, Allergies, Immunizations, Care Gaps
"""

import json
import os
from collections import defaultdict
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user

import config

from models import db
from sqlalchemy.orm import joinedload
from models.patient import (
    PatientRecord, PatientVitals, PatientMedication,
    PatientDiagnosis, PatientAllergy, PatientImmunization,
    PatientNoteDraft, PatientSpecialist,
    PatientEncounterNote,
)
from models.api_cache import Icd10Cache, RxNormCache
from models.labtrack import LabTrack
from models.caregap import CareGap, CareGapRule
from models.schedule import Schedule

# Service layer imports (extracted from this file, Band 3 B1)
from utils.patient_helpers import (
    mrn_display as _mrn_display,
    calc_age as _calc_age,
    calc_age_years as _calc_age_years,
    normalize_name as _normalize_name,
    normalize_dob as _normalize_dob,
)
from app.services.patient_service import (
    schedule_context_for_patient as _schedule_context_for_patient,
    ensure_patient_record_for_view as _ensure_patient_record_for_view,
    prepopulate_sections as _prepopulate_sections,
)
from app.services.diagnosis_service import (
    classify_diagnosis as _classify_diagnosis,
    backfill_icd10_codes as _backfill_icd10_codes,
    load_icd10_csv as _load_icd10_csv,
    ACUTE_ICD10_PREFIXES,
    ACUTE_KEYWORDS,
)
from app.services.medication_enrichment import (
    fetch_rxnorm_api as _fetch_rxnorm_api,
    enrich_rxnorm_single as _enrich_rxnorm_single,
    enrich_rxnorm as _enrich_rxnorm,
    standardize_frequency as _standardize_frequency,
    parse_dose_fallback as _parse_dose_fallback,
    enrich_medications as _enrich_medications,
)
from app.services.caregap_service import (
    get_uspstf_recommendations as _get_uspstf_recommendations,
    auto_evaluate_care_gaps as _auto_evaluate_care_gaps,
)

patient_bp = Blueprint('patient', __name__)

AC_NOTE_SECTIONS = [
    "Chief Complaint",
    "History of Present Illness",
    "Review of Systems",
    "Past Medical History",
    "Social History",
    "Family History",
    "Allergies",
    "Medications",
    "Physical Exam",
    "Functional Status/Mental Status",
    "Confidential Information",
    "Assessment",
    "Plan",
    "Instructions",
    "Goals",
    "Health Concerns",
]

# ICD-10 codes that are typically acute conditions
ACUTE_ICD10_PREFIXES = (
    'J00', 'J01', 'J02', 'J03', 'J04', 'J05', 'J06',  # Acute upper resp
    'J09', 'J10', 'J11',  # Influenza
    'J20', 'J21', 'J22',  # Acute lower resp
    'A00', 'A01', 'A02', 'A03', 'A04', 'A05', 'A06', 'A07', 'A08', 'A09',  # GI infections
    'B00', 'B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B09',  # Viral
    'H10',  # Conjunctivitis
    'H60', 'H65', 'H66',  # Otitis
    'L00', 'L01', 'L02', 'L03', 'L04', 'L05',  # Skin infections
    'M54',  # Back pain (often acute)
    'M79',  # Soft tissue disorders
    'N30',  # Cystitis
    'N39',  # UTI
    'R05', 'R06', 'R07', 'R10', 'R11', 'R50', 'R51',  # Symptoms
    'S', 'T',  # Injuries, poisoning
    'W', 'X', 'Y',  # External causes
)

ACUTE_KEYWORDS = (
    'acute', 'sprain', 'strain', 'fracture', 'laceration', 'contusion',
    'uti', 'urinary tract infection', 'bronchitis', 'sinusitis', 'pharyngitis',
    'otitis', 'cellulitis', 'abscess', 'bite', 'burn', 'concussion',
    'dislocation', 'foreign body', 'pain', 'injury', 'wound',
)


def _mrn_display_unused_placeholder():
    pass  # replaced by import above — kept as marker, will be removed


def _calc_age_years_unused_placeholder_remove():
    pass  # replaced by import above


def _calc_age_years_REMOVE_dob_str():
    """Calculate numeric age from DOB string."""
    if not True:
        return None
    try:
        if '/' in '':
            dob = datetime.strptime('', '%m/%d/%Y')
        elif len('') == 8:
            dob = datetime.strptime(dob_str, '%Y%m%d')
        else:
            return None
        today = datetime.now()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except ValueError:
        return None


def _normalize_name(name):
    """Normalize patient names from schedule/query data for display."""
    name = (name or '').strip()
    if not name:
        return ''
    if ',' in name:
        parts = [part.strip() for part in name.split(',', 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            return f'{parts[1]} {parts[0]}'
    return ' '.join(name.split())


def _normalize_dob(dob_str):
    """Normalize DOB strings to YYYYMMDD for PatientRecord storage."""
    dob_str = (dob_str or '').strip()
    if not dob_str:
        return ''
    for fmt in ('%Y%m%d', '%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y'):
        try:
            return datetime.strptime(dob_str, fmt).strftime('%Y%m%d')
        except ValueError:
            continue
    digits = ''.join(ch for ch in dob_str if ch.isdigit())
    if len(digits) == 8:
        if digits.startswith(('19', '20')):
            return digits
        try:
            return datetime.strptime(digits, '%m%d%Y').strftime('%Y%m%d')
        except ValueError:
            return ''
    return ''


def _schedule_context_for_patient(user_id, mrn):
    """Return the most relevant schedule metadata for this user/MRN."""
    latest = (
        Schedule.query
        .filter_by(user_id=user_id, patient_mrn=mrn)
        .order_by(Schedule.appointment_date.desc(), Schedule.appointment_time.desc())
        .first()
    )

    context = {
        'patient_name': _normalize_name(request.args.get('name', '')),
        'patient_dob': _normalize_dob(request.args.get('dob', '')),
        'appointment_time': (request.args.get('appt', '') or '').strip(),
        'visit_type': (request.args.get('visit', '') or '').strip(),
        'reason': (request.args.get('reason', '') or '').strip(),
        'appointment_date': None,
        'status': '',
    }

    if latest:
        context['patient_name'] = context['patient_name'] or _normalize_name(latest.patient_name)
        context['patient_dob'] = context['patient_dob'] or _normalize_dob(latest.patient_dob)
        context['appointment_time'] = context['appointment_time'] or (latest.appointment_time or '')
        context['visit_type'] = context['visit_type'] or (latest.visit_type or '')
        context['reason'] = context['reason'] or (latest.reason or '')
        context['appointment_date'] = latest.appointment_date
        context['status'] = latest.status or ''

    return context


def _ensure_patient_record_for_view(user_id, mrn, schedule_context):
    """Create or backfill a per-user patient record from schedule context."""
    record = PatientRecord.query.filter_by(user_id=user_id, mrn=mrn).first()
    changed = False

    if not record:
        record = PatientRecord(user_id=user_id, mrn=mrn)
        db.session.add(record)
        changed = True

    if schedule_context['patient_name'] and not (record.patient_name or '').strip():
        record.patient_name = schedule_context['patient_name']
        changed = True

    if schedule_context['patient_dob'] and not (record.patient_dob or '').strip():
        record.patient_dob = schedule_context['patient_dob']
        changed = True

    if changed:
        db.session.commit()

    return record


def _classify_diagnosis(name, icd10):
    """Classify diagnosis as acute or chronic based on ICD-10 and name."""
    icd = (icd10 or '').upper().replace('.', '')
    name_lower = (name or '').lower()

    for prefix in ACUTE_ICD10_PREFIXES:
        if icd.startswith(prefix):
            return 'acute'

    for kw in ACUTE_KEYWORDS:
        if kw in name_lower:
            return 'acute'

    return 'chronic'


def _backfill_icd10_codes(user_id, mrn, cache_only=False):
    """
    Ensure every PatientDiagnosis for this patient has an NIH-verified
    ICD-10 code.  Resolution order:
      1. Check the local Icd10Cache table (fast, no network).
      2. If not cached and cache_only=False, query the NIH Clinical Tables API
         via ICD10Service and store the result in icd10_cache for future lookups.
      3. NIH API codes always supersede codes that came from XML files.
    """
    import logging
    logger = logging.getLogger(__name__)

    all_diags = PatientDiagnosis.query.filter(
        PatientDiagnosis.user_id == user_id,
        PatientDiagnosis.mrn == mrn,
    ).all()

    if not all_diags:
        return

    # Lazy-init the ICD10 service (uses BaseAPIClient with caching + retry)
    try:
        from app.services.api.icd10 import ICD10Service
        icd10_svc = ICD10Service(db)
    except Exception:
        icd10_svc = None

    changed = False
    for diag in all_diags:
        name = (diag.diagnosis_name or '').strip()
        if not name or len(name) < 3:
            continue

        name_lower = name.lower()

        # 1. Check local cache
        cached = Icd10Cache.query.filter_by(diagnosis_name_lower=name_lower).first()
        if cached:
            if diag.icd10_code != cached.icd10_code:
                diag.icd10_code = cached.icd10_code
                changed = True
            continue

        # In cache-only mode, skip API calls
        if cache_only:
            continue

        # 2. Query NIH API via service (preferred) or raw urllib (fallback)
        try:
            code = ''
            desc = ''
            if icd10_svc:
                results = icd10_svc.search(name, max_results=1)
                if results:
                    code = results[0].get('code', '')
                    desc = results[0].get('description', '')
            else:
                # Fallback to raw urllib if service import fails
                import urllib.request
                import urllib.parse
                url = (
                    'https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search'
                    '?sf=code,name&maxList=1&terms='
                    + urllib.parse.quote(name)
                )
                req = urllib.request.Request(url, headers={'Accept': 'application/json'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode())
                    if len(data) >= 4 and data[3] and len(data[3]) > 0:
                        best = data[3][0]
                        if len(best) >= 2:
                            code = best[0]
                            desc = best[1]

            if code:
                # Store in global cache
                entry = Icd10Cache(
                    diagnosis_name_lower=name_lower,
                    icd10_code=code,
                    icd10_description=desc,
                    source='nih_api',
                )
                db.session.add(entry)
                # Always apply NIH code (supersedes XML)
                diag.icd10_code = code
                changed = True
        except Exception as e:
            logger.debug('NIH ICD-10 lookup failed for %s: %s', name, e)
            continue

    if changed:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()


# ======================================================================
# RxNorm API enrichment — cached drug info from NIH
# ======================================================================
def _fetch_rxnorm_api(path):
    """Fetch a single RxNorm REST API endpoint, return parsed JSON or None."""
    import urllib.request
    url = 'https://rxnav.nlm.nih.gov/REST' + path
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def _enrich_rxnorm_single(rxcui):
    """
    Look up one RXCUI via the NIH RxNorm API and return a dict with
    brand_name, generic_name, dose_strength, dose_form, route, tty.
    Returns None on failure.
    """
    import re as _re
    import logging
    logger = logging.getLogger(__name__)

    # 1. Get concept properties
    props_data = _fetch_rxnorm_api(f'/rxcui/{rxcui}/properties.json')
    if not props_data:
        return None
    concept = (props_data.get('properties') or {})
    name = concept.get('name', '')
    tty = concept.get('tty', '')

    # 2. Get related ingredient (generic name)
    generic_name = ''
    related_in = _fetch_rxnorm_api(f'/rxcui/{rxcui}/related.json?tty=IN')
    if related_in:
        groups = (related_in.get('relatedGroup') or {}).get('conceptGroup', [])
        for group in groups:
            props_list = group.get('conceptProperties', [])
            if props_list:
                generic_name = props_list[0].get('name', '')
                break

    # 3. Get related brand name
    brand_name = ''
    related_bn = _fetch_rxnorm_api(f'/rxcui/{rxcui}/related.json?tty=BN')
    if related_bn:
        groups = (related_bn.get('relatedGroup') or {}).get('conceptGroup', [])
        for group in groups:
            props_list = group.get('conceptProperties', [])
            if props_list:
                brand_name = props_list[0].get('name', '')
                break

    # 4. Parse dose strength and form from the concept name
    #    Typical SCD name: "atorvastatin 20 MG Oral Tablet"
    dose_strength = ''
    dose_form = ''
    route = ''
    m = _re.search(r'(\d+(?:\.\d+)?\s*(?:MG|MCG|ML|UNITS?|%|MEQ)(?:/[\d.]+\s*(?:MG|MCG|ML|HR))?)', name, _re.IGNORECASE)
    if m:
        dose_strength = m.group(1).strip()
    # Dose form comes after the dose strength
    form_m = _re.search(
        r'(?:MG|MCG|ML|UNITS?|%|MEQ|HR)\s+(Oral|Injectable|Topical|Inhalant|Nasal|Ophthalmic|Otic|Rectal|Vaginal|Transdermal)?\s*'
        r'(Tablet|Capsule|Solution|Suspension|Injection|Cream|Ointment|Gel|Patch|Spray|Inhaler|Drops|Powder|Suppository|Film|Lozenge|Pack|Kit)?',
        name, _re.IGNORECASE
    )
    if form_m:
        route = (form_m.group(1) or '').strip()
        dose_form = (form_m.group(2) or '').strip()

    # If brand name IS the concept name for BN type, set accordingly
    if tty == 'BN':
        brand_name = brand_name or name
    elif tty == 'IN':
        generic_name = generic_name or name

    # 5. Get first NDC code for pricing lookups
    ndc = ''
    ndc_data = _fetch_rxnorm_api(f'/rxcui/{rxcui}/ndcs.json')
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


def _enrich_rxnorm(rxcui, drug_name_fallback='', cache_only=False):
    """
    Return an RxNormCache row for the given RXCUI.
    Checks local cache first; on miss, queries the NIH API.
    If rxcui is empty, tries approximate match by drug name.
    Uses RxNormService when available (with caching + retry),
    falls back to raw urllib.
    When cache_only=True, skip all network calls (fast path for page load).
    """
    import urllib.parse
    import logging
    logger = logging.getLogger(__name__)

    # Normalize
    rxcui = (rxcui or '').strip()

    # Fallback: look up by name if no CUI
    if not rxcui and drug_name_fallback:
        if not cache_only:
            # Try RxNormService first (has better caching and retry)
            try:
                from app.services.api.rxnorm import RxNormService
                svc = RxNormService(db)
                result = svc.get_rxcui(drug_name_fallback)
                if result and result.get('rxcui'):
                    rxcui = result['rxcui']
            except Exception:
                pass

            # Fallback to raw API if service didn't resolve
            if not rxcui:
                data = _fetch_rxnorm_api(
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

    # In cache-only mode, stop here — no API call
    if cache_only:
        return None

    # 2. Query API
    info = _enrich_rxnorm_single(rxcui)
    if not info:
        return None

    # 3. Cache the result
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
        # May have been inserted concurrently
        return RxNormCache.query.filter_by(rxcui=rxcui).first()

    return entry


def _standardize_frequency(raw):
    """
    Normalize free-text medication instructions to a standard abbreviation.
    Examples:
      "take 1 tablet by mouth once daily" → "Daily"
      "take 1 tablet by mouth twice daily" → "BID"
      "1 PO BID" → "BID"
      "every 8 hours" → "Q8H"
      "once a week" → "Weekly"
      "as needed" → "PRN"
    Returns the abbreviated frequency string or the original if unmatched.
    """
    import re as _re
    if not raw:
        return ''
    t = raw.strip()
    low = t.lower()

    # Map of regex → standard abbreviation (checked in order)
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
            # Handle dynamic group substitution (e.g. Q\1H)
            if '\\1' in replacement:
                return _re.sub(pattern, replacement, low, count=1, flags=_re.IGNORECASE).upper()
            return replacement
    return t


def _parse_dose_fallback(drug_name, frequency):
    """
    Last-resort dose extraction when RxNorm lookup fails.
    Parses dose from the drug name string or the Instructions/frequency field.
    Examples:
      "Lisinopril 10 MG Tablet" → "10 MG"
      "take 0.25 mg SQ once a week" → "0.25 mg"
    Returns (dose_str, form_str) or ('', '').
    """
    import re as _re
    # Try drug_name first (e.g. "Lisinopril 10 MG Oral Tablet")
    for text in [drug_name, frequency]:
        if not text:
            continue
        m = _re.search(
            r'(\d+(?:\.\d+)?\s*(?:mg|mcg|ml|units?|%|meq|g|iu)(?:/[\d.]+\s*(?:mg|mcg|ml|hr))?)',
            text, _re.IGNORECASE
        )
        if m:
            dose = m.group(1).strip()
            # Try to find form after the dose
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


def _enrich_medications(medications, cache_only=False):
    """
    Annotate a list of PatientMedication objects with RxNorm data.
    Adds .rx_info attribute to each medication (RxNormCache row or None).
    Adds .std_frequency with standardized frequency abbreviation.
    When RxNorm lookup fails, falls back to regex-based dose parsing
    from drug_name or frequency (Instructions) to avoid showing
    raw quantity in the dose column.
    When cache_only=True, skip network calls for faster page load.
    """
    for med in medications:
        med.rx_info = _enrich_rxnorm(
            getattr(med, 'rxnorm_cui', ''),
            drug_name_fallback=med.drug_name,
            cache_only=cache_only,
        )
        # Standardize frequency display
        med.std_frequency = _standardize_frequency(med.frequency)
        # Fallback: if no RxNorm dose_strength, try parsing from drug name / frequency
        if not med.rx_info or not getattr(med.rx_info, 'dose_strength', ''):
            dose, form = _parse_dose_fallback(med.drug_name, med.frequency)
            if dose:
                if not med.rx_info:
                    # Create a lightweight stand-in object
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


def _prepopulate_sections(mrn, user_id, allergies=None, medications=None,
                          diagnoses=None, immunizations=None):
    """Build dict mapping AC note section names to pre-populated text.

    Accepts pre-fetched query results to avoid redundant DB queries.
    Falls back to querying if not provided.
    """
    prepop = {}
    if allergies is None:
        allergies = PatientAllergy.query.filter_by(user_id=user_id, mrn=mrn).all()
    if allergies:
        prepop['Allergies'] = '\n'.join(
            f'{a.allergen} — {a.reaction}' if a.reaction else a.allergen
            for a in allergies
        )
    if medications is None:
        medications = PatientMedication.query.filter_by(
            user_id=user_id, mrn=mrn, status='active'
        ).order_by(PatientMedication.drug_name).all()
    active_meds = [m for m in medications if getattr(m, 'status', '') == 'active']
    if active_meds:
        prepop['Medications'] = '\n'.join(
            f'{m.drug_name} {m.dosage} {m.frequency}'.strip() for m in active_meds
        )
    if diagnoses is None:
        diagnoses = PatientDiagnosis.query.filter_by(
            user_id=user_id, mrn=mrn, status='active'
        ).all()
    active_dx = [d for d in diagnoses if getattr(d, 'status', '') == 'active']
    if active_dx:
        lines = []
        for d in active_dx:
            line = d.diagnosis_name
            if d.icd10_code:
                line += f' ({d.icd10_code})'
            lines.append(line)
        prepop['Past Medical History'] = '\n'.join(lines)

    if immunizations is None:
        immunizations = PatientImmunization.query.filter_by(
            user_id=user_id, mrn=mrn
        ).order_by(PatientImmunization.date_given.desc()).all()
    if immunizations:
        seen = set()
        imm_lines = []
        for imm in immunizations:
            date_str = imm.date_given.strftime('%m/%Y') if imm.date_given else 'Unknown'
            key = (imm.vaccine_name, date_str)
            if key not in seen:
                seen.add(key)
                label = imm.vaccine_name
                if imm.source == 'viis':
                    label += ' [VIIS]'
                imm_lines.append(f'{label} ({date_str})')
        prepop['Immunizations'] = ', '.join(imm_lines)

    return prepop


def _get_uspstf_recommendations(age, sex):
    """Return applicable USPSTF screening recommendations."""
    recs = []
    rules = CareGapRule.query.all()
    for rule in rules:
        try:
            criteria = json.loads(rule.criteria_json) if rule.criteria_json else {}
        except (json.JSONDecodeError, TypeError):
            criteria = {}
        min_age = criteria.get('min_age', 0)
        max_age = criteria.get('max_age', 999)
        req_sex = criteria.get('sex', 'all')
        if age is not None and min_age <= age <= max_age:
            if req_sex == 'all' or req_sex == sex:
                # Split billing_code_pair "G0105 / G0121" → commercial, medicare
                pair = (rule.billing_code_pair or '').strip()
                if ' / ' in pair:
                    commercial, medicare = [p.strip() for p in pair.split(' / ', 1)]
                elif pair:
                    commercial = medicare = pair
                else:
                    commercial = medicare = ''
                recs.append({
                    'name': rule.gap_type,
                    'description': getattr(rule, 'description', '') or rule.gap_type,
                    'interval_days': rule.interval_days,
                    'billing_code': commercial,
                    'medicare_code': medicare,
                    'explanation': getattr(rule, 'description', '') or '',
                    'documentation_template': getattr(rule, 'documentation_template', '') or '',
                })
    return recs


def _auto_evaluate_care_gaps(user_id, mrn):
    """
    Trigger the USPSTF care gap engine for one patient.
    Called after XML upload and on chart load when gaps are empty.
    Fails silently — care gaps are not critical path.
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        from flask import current_app
        from agent.caregap_engine import evaluate_and_persist_gaps

        record = PatientRecord.query.filter_by(user_id=user_id, mrn=mrn).first()
        if not record:
            return

        diagnoses = PatientDiagnosis.query.filter_by(
            user_id=user_id, mrn=mrn, status='active'
        ).all()
        immunizations = PatientImmunization.query.filter_by(
            user_id=user_id, mrn=mrn
        ).all()

        patient_data = {
            'patient_name': record.patient_name or '',
            'patient_dob': record.patient_dob or '',
            'patient_sex': record.patient_sex or '',
            'diagnoses': [
                {'name': d.diagnosis_name, 'icd10': d.icd10_code or ''}
                for d in diagnoses
            ],
            'immunizations': [
                {'name': i.vaccine_name or '', 'date_given': str(i.date_given) if i.date_given else ''}
                for i in immunizations
            ],
        }
        evaluate_and_persist_gaps(user_id, mrn, patient_data, current_app._get_current_object())
    except Exception as e:
        logger.debug('Care gap auto-evaluation failed for ••%s: %s', mrn[-4:], e)


# ======================================================================
# GET /patient/<mrn> — Patient Chart (widget layout)
# ======================================================================
@patient_bp.route('/patient/<mrn>')
@login_required
def chart(mrn):
    """Patient chart view — widget-based drag/resize layout."""
    schedule_context = _schedule_context_for_patient(current_user.id, mrn)
    record = _ensure_patient_record_for_view(current_user.id, mrn, schedule_context)

    medications = PatientMedication.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).order_by(PatientMedication.status, PatientMedication.drug_name).all()

    # Cache-only enrichment on page load (no API calls — fast path)
    _enrich_medications(medications, cache_only=True)

    # Cache-only ICD-10 backfill (no API calls — fast path)
    _backfill_icd10_codes(current_user.id, mrn, cache_only=True)

    diagnoses = PatientDiagnosis.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).order_by(PatientDiagnosis.status, PatientDiagnosis.diagnosis_name).all()

    allergies = PatientAllergy.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).all()

    immunizations = PatientImmunization.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).order_by(PatientImmunization.date_given.desc()).all()

    vitals = PatientVitals.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).order_by(PatientVitals.measured_at.desc()).all()

    lab_tracks = LabTrack.query.filter_by(
        user_id=current_user.id, mrn=mrn, is_archived=False
    ).options(joinedload(LabTrack.results)).all()

    care_gaps = CareGap.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).all()

    # Auto-evaluate care gaps on first chart load (when none exist yet)
    if not care_gaps and record and record.last_xml_parsed:
        _auto_evaluate_care_gaps(current_user.id, mrn)
        care_gaps = CareGap.query.filter_by(
            user_id=current_user.id, mrn=mrn
        ).all()

    specialists = PatientSpecialist.query.filter_by(
        user_id=current_user.id, mrn=mrn, is_archived=False
    ).order_by(PatientSpecialist.specialty).all()

    # Encounter notes (prior notes)
    encounter_notes = PatientEncounterNote.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).order_by(PatientEncounterNote.encounter_date.desc()).all()

    # Note draft
    draft = PatientNoteDraft.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).first()
    draft_data = json.loads(draft.section_data) if draft else {}

    prepopulated = _prepopulate_sections(
        mrn, current_user.id,
        allergies=allergies,
        medications=medications,
        diagnoses=diagnoses,
        immunizations=immunizations,
    )

    # USPSTF recommendations
    age = _calc_age_years(record.patient_dob if record else '')
    sex = getattr(record, 'patient_sex', 'unknown') if record else 'unknown'
    uspstf_recs = _get_uspstf_recommendations(age, sex)

    # Build lab spreadsheet data: {lab_name: [{date, value}, ...]}
    lab_spreadsheet = defaultdict(list)
    all_lab_dates = set()
    for lt in lab_tracks:
        for r in lt.results:
            if r.result_date:
                date_str = r.result_date.strftime('%m/%d/%Y')
                lab_spreadsheet[lt.lab_name].append({
                    'date': date_str,
                    'value': r.result_value,
                    'is_critical': r.is_critical,
                })
                all_lab_dates.add(date_str)

    # Sort dates chronologically
    sorted_dates = sorted(all_lab_dates, key=lambda d: datetime.strptime(d, '%m/%d/%Y'))

    # Overdue labs
    overdue_labs = [lt for lt in lab_tracks if lt.status in ('overdue', 'due_soon', 'critical')]

    # Widget layout preferences (default ordering)
    widget_layout = current_user.get_pref('chart_widget_layout', None)
    chart_layout_mode = current_user.get_pref('chart_layout_mode', 'grid')
    chart_free_positions = current_user.get_pref('chart_free_widget_positions', None)
    chart_view_mode = current_user.get_pref('chart_view_mode', 'tabs')

    # Phase 24.4 — Immunization series gaps deferred to AJAX for faster page load
    imm_series_gaps = []

    # Phase 32.1 — Auto-compute risk scores deferred to AJAX for faster page load
    auto_scores = {}

    return render_template(
        'patient_chart.html',
        record=record,
        mrn=mrn,
        mrn_display=_mrn_display(mrn),
        age_str=_calc_age(record.patient_dob if record else ''),
        medications=medications,
        diagnoses=diagnoses,
        allergies=allergies,
        immunizations=immunizations,
        vitals=vitals,
        lab_tracks=lab_tracks,
        care_gaps=care_gaps,
        specialists=specialists,
        draft_data=draft_data,
        prepopulated=prepopulated,
        note_sections=AC_NOTE_SECTIONS,
        uspstf_recs=uspstf_recs,
        lab_spreadsheet=dict(lab_spreadsheet),
        lab_dates=sorted_dates,
        overdue_labs=overdue_labs,
        schedule_context=schedule_context,
        widget_layout=json.dumps(widget_layout) if widget_layout else 'null',
        chart_layout_mode=chart_layout_mode,
        chart_free_positions=json.dumps(chart_free_positions) if chart_free_positions else 'null',
        chart_view_mode=chart_view_mode,
        has_data=record is not None and record.last_xml_parsed is not None,
        imm_series_gaps=imm_series_gaps,
        auto_scores=auto_scores,
        encounter_notes=encounter_notes,
    )


# ======================================================================
# POST /api/patient/<mrn>/enrich — Deferred API enrichment (RxNorm + ICD-10)
# Called via AJAX after page load to avoid blocking chart render.
# ======================================================================
@patient_bp.route('/api/patient/<mrn>/enrich', methods=['POST'])
@login_required
def enrich_patient_data(mrn):
    """Run full API enrichment (RxNorm + ICD-10) for a patient."""
    try:
        medications = PatientMedication.query.filter_by(
            user_id=current_user.id, mrn=mrn
        ).all()
        _enrich_medications(medications, cache_only=False)
        _backfill_icd10_codes(current_user.id, mrn, cache_only=False)
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error('enrich_patient_data error for %s: %s', mrn[-4:] if len(mrn) > 4 else '??', str(e))
        return jsonify({'success': False, 'error': 'Enrichment skipped'}), 200


# ======================================================================
# GET /api/patient/<mrn>/auto-scores — Deferred risk score computation
# Called via AJAX after page load to avoid blocking chart render.
# ======================================================================
@patient_bp.route('/api/patient/<mrn>/auto-scores')
@login_required
def get_auto_scores(mrn):
    """Compute auto risk scores for patient chart (deferred from page load)."""
    try:
        from app.services.calculator_engine import CalculatorEngine
        engine = CalculatorEngine()
        score_list = engine.run_auto_scores(mrn, current_user.id)
        scores = {s['calculator_key']: s for s in score_list if s.get('score_value') is not None}
        return jsonify({'success': True, 'data': scores})
    except Exception as e:
        current_app.logger.debug('Auto-scores failed for ••%s: %s', mrn[-4:], e)
        return jsonify({'success': True, 'data': {}})


# ======================================================================
# GET /api/patient/<mrn>/imm-gaps — Deferred immunization series gaps
# Called via AJAX after page load to avoid blocking chart render.
# ======================================================================
@patient_bp.route('/api/patient/<mrn>/imm-gaps')
@login_required
def get_imm_gaps(mrn):
    """Compute immunization series gaps for patient chart (deferred from page load)."""
    try:
        from app.services.immunization_engine import get_series_gaps, populate_patient_series
        from billing_engine.shared import hash_mrn

        record = PatientRecord.query.filter_by(
            user_id=current_user.id, mrn=mrn
        ).first()
        age = _calc_age_years(record.patient_dob if record else '')

        mrn_hash = hash_mrn(mrn)
        populate_patient_series(mrn_hash, current_user.id)
        gaps = get_series_gaps(mrn_hash, current_user.id, age)
        # Serialize for JSON (gaps may contain non-serializable objects)
        gap_list = []
        for g in gaps:
            gap_list.append({
                'series_name': g.get('series_name', ''),
                'status': g.get('status', ''),
                'message': g.get('message', ''),
                'next_due': str(g.get('next_due', '')) if g.get('next_due') else None,
            })
        return jsonify({'success': True, 'data': gap_list})
    except Exception as e:
        current_app.logger.debug('Imm gaps failed for ••%s: %s', mrn[-4:], e)
        return jsonify({'success': True, 'data': []})


# ======================================================================
# GET /api/patient/<mrn>/pricing — Bulk medication pricing
# ======================================================================
@patient_bp.route('/api/patient/<mrn>/pricing')
@login_required
def medication_pricing(mrn):
    """Return pricing data for all active medications of a patient (max 20)."""
    import logging
    logger = logging.getLogger(__name__)
    try:
        from app.services.pricing_service import PricingService
        medications = PatientMedication.query.filter_by(
            user_id=current_user.id, mrn=mrn, status='active'
        ).order_by(PatientMedication.drug_name).limit(20).all()

        record = PatientRecord.query.filter_by(
            user_id=current_user.id, mrn=mrn
        ).first()

        svc = PricingService(db)
        results = []
        for med in medications:
            try:
                pricing = svc.get_pricing_for_medication(med, record)
            except Exception as e:
                logger.debug('Pricing failed for %s: %s', med.drug_name, e)
                pricing = {'source': 'none', 'price_monthly_estimate': None,
                           'badge_color': None, 'assistance_programs': []}
            results.append({
                'drug_name': med.drug_name,
                'rxcui': med.rxnorm_cui,
                'med_id': med.id,
                'pricing': pricing,
            })
        return jsonify({'medications': results})
    except Exception as e:
        logger.error('Bulk pricing error for MRN ••%s: %s', mrn[-4:], e)
        return jsonify({'medications': []}), 200


# ======================================================================
# GET /api/patient/<mrn>/summary — Quick patient summary for PA lookup
# ======================================================================
@patient_bp.route('/api/patient/<mrn>/summary')
@login_required
def patient_summary(mrn):
    """Return basic patient info for auto-populating forms."""
    record = PatientRecord.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).first()
    if not record:
        return jsonify({'success': False, 'error': 'Patient not found'}), 404
    return jsonify({
        'success': True,
        'data': {
            'name': record.patient_name or '',
            'dob': record.patient_dob or '',
            'sex': record.patient_sex or '',
            'insurance': record.insurer_type or '',
        }
    })


# ======================================================================
# POST /patient/<mrn>/upload-xml — Manual XML upload
# ======================================================================
@patient_bp.route('/patient/<mrn>/upload-xml', methods=['POST'])
@login_required
def upload_xml(mrn):
    """Upload a CDA Clinical Summary XML file and parse it."""
    if 'xml_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400

    f = request.files['xml_file']
    if not f.filename:
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if not f.filename.lower().endswith('.xml'):
        return jsonify({'success': False, 'message': 'File must be .xml'}), 400

    # Save to temp file, parse, then delete
    export_folder = getattr(config, 'CLINICAL_SUMMARY_EXPORT_FOLDER', 'data/clinical_summaries/')
    if not os.path.isabs(export_folder):
        export_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), export_folder)
    export_folder = os.path.normpath(export_folder)
    os.makedirs(export_folder, exist_ok=True)

    # Use secure filename
    safe_name = f'upload_{current_user.id}_{mrn}_{int(datetime.now().timestamp())}.xml'
    xml_path = os.path.join(export_folder, safe_name)

    try:
        f.save(xml_path)
        from agent.clinical_summary_parser import parse_clinical_summary, store_parsed_summary

        parsed = parse_clinical_summary(xml_path)

        # Use the MRN from the URL (trusted) not from XML
        if parsed.get('patient_mrn') and parsed['patient_mrn'] != mrn:
            # Warn but still use the URL MRN
            pass

        # Clear existing data for this patient before re-import
        PatientMedication.query.filter_by(user_id=current_user.id, mrn=mrn).delete()
        PatientDiagnosis.query.filter_by(user_id=current_user.id, mrn=mrn).delete()
        PatientAllergy.query.filter_by(user_id=current_user.id, mrn=mrn).delete()
        PatientImmunization.query.filter_by(user_id=current_user.id, mrn=mrn).delete()
        PatientVitals.query.filter_by(user_id=current_user.id, mrn=mrn).delete()
        db.session.flush()

        store_parsed_summary(current_user.id, mrn, parsed)

        # Backfill missing ICD-10 codes via NIH API
        _backfill_icd10_codes(current_user.id, mrn)

        # Auto-classify diagnoses
        for diag in PatientDiagnosis.query.filter_by(user_id=current_user.id, mrn=mrn).all():
            diag.diagnosis_category = _classify_diagnosis(diag.diagnosis_name, diag.icd10_code)
        db.session.commit()

        # Evaluate care gaps now that we have fresh clinical data
        _auto_evaluate_care_gaps(current_user.id, mrn)

        sections = [k for k, v in parsed.items() if v and k not in ('patient_name', 'patient_mrn', 'patient_dob')]
        return jsonify({
            'success': True,
            'message': f'Parsed {len(sections)} sections successfully.',
            'sections': sections,
            'patient_name': parsed.get('patient_name', ''),
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Parse error: {str(e)}'}), 500
    finally:
        # Clean up temp file
        try:
            if os.path.exists(xml_path):
                os.remove(xml_path)
        except OSError:
            pass


# ======================================================================
# GET /api/patient/<mrn>/labs — Lab data for spreadsheet & graphing
# ======================================================================
@patient_bp.route('/api/patient/<mrn>/labs')
@login_required
def api_labs(mrn):
    """Return lab data for the Epic-style spreadsheet and graphing."""
    lab_tracks = LabTrack.query.filter_by(
        user_id=current_user.id, mrn=mrn, is_archived=False
    ).all()

    data = {}
    all_dates = set()

    for lt in lab_tracks:
        results = []
        for r in lt.results:
            if r.result_date:
                date_str = r.result_date.strftime('%Y-%m-%d')
                results.append({
                    'date': date_str,
                    'display_date': r.result_date.strftime('%m/%d/%y'),
                    'value': r.result_value,
                    'is_critical': r.is_critical,
                    'trend': r.trend_direction,
                })
                all_dates.add(date_str)
        data[lt.lab_name] = {
            'results': results,
            'alert_low': lt.alert_low,
            'alert_high': lt.alert_high,
            'interval_days': lt.interval_days,
            'status': lt.status,
        }

    sorted_dates = sorted(all_dates)
    return jsonify({'labs': data, 'dates': sorted_dates})


# ======================================================================
# POST /patient/<mrn>/specialist — Add specialist
# ======================================================================
@patient_bp.route('/patient/<mrn>/specialist', methods=['POST'])
@login_required
def add_specialist(mrn):
    """Add a specialist record for a patient."""
    data = request.get_json(silent=True) or {}
    spec = PatientSpecialist(
        user_id=current_user.id,
        mrn=mrn,
        specialty=data.get('specialty', ''),
        provider_name=data.get('provider_name', ''),
        phone=data.get('phone', ''),
        fax=data.get('fax', ''),
        notes=data.get('notes', ''),
    )
    db.session.add(spec)
    db.session.commit()
    return jsonify({'success': True, 'id': spec.id})


# ======================================================================
# DELETE /patient/<mrn>/specialist/<id> — Remove specialist
# ======================================================================
@patient_bp.route('/patient/<mrn>/specialist/<int:spec_id>', methods=['DELETE'])
@login_required
def delete_specialist(mrn, spec_id):
    """Remove a specialist record."""
    spec = PatientSpecialist.query.filter_by(
        id=spec_id, user_id=current_user.id, mrn=mrn
    ).first()
    if spec:
        # HIPAA: soft-delete clinical records — never hard-delete
        spec.is_archived = True
        db.session.commit()
    return jsonify({'success': True})


# ======================================================================
# POST /patient/<mrn>/widget-layout — Save widget positions
# ======================================================================
@patient_bp.route('/patient/<mrn>/widget-layout', methods=['POST'])
@login_required
def save_widget_layout(mrn):
    """Save widget positions/sizes to user preferences."""
    data = request.get_json(silent=True) or {}
    layout = data.get('layout', {})
    current_user.set_pref('chart_widget_layout', layout)
    db.session.commit()
    return jsonify({'success': True})


# ======================================================================
# POST /patient/<mrn>/note/save — Save Prepped Note draft
# ======================================================================
@patient_bp.route('/patient/<mrn>/note/save', methods=['POST'])
@login_required
def save_note(mrn):
    """Save prepped note draft to database."""
    data = request.get_json(silent=True) or {}
    sections = data.get('sections', {})

    draft = PatientNoteDraft.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).first()

    if draft:
        draft.section_data = json.dumps(sections)
        draft.updated_at = datetime.now(timezone.utc)
    else:
        draft = PatientNoteDraft(
            user_id=current_user.id,
            mrn=mrn,
            section_data=json.dumps(sections),
        )
        db.session.add(draft)

    db.session.commit()
    return jsonify({'success': True})


# ======================================================================
# POST /patient/<mrn>/note/send-to-ac — PyAutoGUI paste to AC
# ======================================================================
@patient_bp.route('/patient/<mrn>/note/send-to-ac', methods=['POST'])
@login_required
def send_to_ac(mrn):
    """Trigger PyAutoGUI paste to Amazing Charts."""
    from agent.ac_window import get_ac_state

    if getattr(config, 'AC_MOCK_MODE', False):
        ac_state = 'home_screen'
    else:
        ac_state = get_ac_state()

    if ac_state == 'not_running':
        return jsonify({
            'success': False,
            'message': 'Amazing Charts is not running. Start AC and try again.',
        })

    if ac_state == 'login_screen':
        return jsonify({
            'success': False,
            'message': 'Amazing Charts is at the login screen. Log in first.',
        })

    return jsonify({
        'success': False,
        'message': (
            'Automatic note injection is not yet implemented. '
            'Use "Copy All" and paste into the Enlarge Textbox manually. '
            'The 16 sections can be navigated with "Update & Go to Next Field".'
        ),
    })


# ======================================================================
# POST /patient/<mrn>/refresh — Re-export Clinical Summary
# ======================================================================
@patient_bp.route('/patient/<mrn>/refresh', methods=['POST'])
@login_required
def refresh_patient(mrn):
    """Trigger a clinical summary re-export for this patient."""
    imported_items_path = getattr(config, 'AC_IMPORTED_ITEMS_PATH', '')
    if imported_items_path:
        patient_folder = os.path.join(imported_items_path, str(mrn))
        if os.path.isdir(patient_folder):
            files = os.listdir(patient_folder)
            if files:
                return jsonify({
                    'success': True,
                    'message': f'Found {len(files)} imported item(s). Processing will begin shortly.',
                    'source': 'imported_items',
                    'file_count': len(files),
                })

    return jsonify({
        'success': True,
        'message': (
            'Refresh requested. Export a Clinical Summary XML from AC '
            '(Alt+P > Export Clinical Summary), then upload it here.'
        ),
        'source': 'pending',
    })


@patient_bp.route('/patient/<mrn>/auto-scores', methods=['POST'])
@login_required
def refresh_auto_scores(mrn):
    """Phase 32.3 — Re-run all auto_ehr calculators and return updated results as JSON."""
    try:
        from app.services.calculator_engine import CalculatorEngine
        calc_engine = CalculatorEngine()
        results = calc_engine.run_auto_scores(mrn, current_user.id)
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ======================================================================
# POST /patient/<mrn>/claim — Claim patient for your panel
# ======================================================================
@patient_bp.route('/patient/<mrn>/claim', methods=['POST'])
@login_required
def claim_patient(mrn):
    """Claim a patient for the current provider's panel."""
    from models.schedule import Schedule
    data = request.get_json(silent=True) or {}

    record = PatientRecord.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).first()

    if not record:
        record = PatientRecord(
            user_id=current_user.id,
            mrn=mrn,
        )
        db.session.add(record)

    # Populate patient_name if missing
    _reject_names = {'unknown patient', 'unknown', ''}
    if not record.patient_name or record.patient_name.lower() in _reject_names:
        # 1) Accept from POST body (chart header knows the name)
        name_from_body = (data.get('patient_name') or '').strip()
        if name_from_body and name_from_body.lower() not in _reject_names:
            record.patient_name = name_from_body
        else:
            # 2) Look up from schedule data
            sched = Schedule.query.filter_by(patient_mrn=mrn).order_by(
                Schedule.appointment_date.desc()
            ).first()
            if sched and sched.patient_name:
                record.patient_name = sched.patient_name

    record.claimed_by = current_user.id
    record.claimed_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({'success': True, 'claimed_by': current_user.display_name})


# ======================================================================
# POST /patient/<mrn>/generate-note — AI-assisted note generation
# ======================================================================
@patient_bp.route('/patient/<mrn>/generate-note', methods=['POST'])
@login_required
def generate_note(mrn):
    """Generate note sections from patient data (rule-based, not LLM)."""
    data = request.get_json(silent=True) or {}
    selected_sections = data.get('sections', [])

    record = PatientRecord.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).first()

    generated = {}

    for section in selected_sections:
        if section == 'Allergies':
            allergies = PatientAllergy.query.filter_by(
                user_id=current_user.id, mrn=mrn
            ).all()
            if allergies:
                lines = []
                for a in allergies:
                    line = a.allergen
                    if a.reaction:
                        line += f' → {a.reaction}'
                    if a.severity:
                        line += f' ({a.severity})'
                    lines.append(line)
                generated[section] = '\n'.join(lines)
            else:
                generated[section] = 'NKDA'

        elif section == 'Medications':
            meds = PatientMedication.query.filter_by(
                user_id=current_user.id, mrn=mrn, status='active'
            ).order_by(PatientMedication.drug_name).all()
            if meds:
                lines = []
                for m in meds:
                    line = m.drug_name
                    if m.dosage:
                        line += f' {m.dosage}'
                    if m.frequency:
                        line += f' {m.frequency}'
                    lines.append(line)
                generated[section] = '\n'.join(lines)
            else:
                generated[section] = 'No active medications'

        elif section == 'Past Medical History':
            diags = PatientDiagnosis.query.filter_by(
                user_id=current_user.id, mrn=mrn, status='active'
            ).all()
            chronic = [d for d in diags if d.diagnosis_category == 'chronic']
            acute = [d for d in diags if d.diagnosis_category == 'acute']
            lines = []
            if chronic:
                lines.append('Chronic conditions:')
                for d in chronic:
                    line = f'  - {d.diagnosis_name}'
                    if d.icd10_code:
                        line += f' ({d.icd10_code})'
                    lines.append(line)
            if acute:
                lines.append('Recent/Acute:')
                for d in acute:
                    line = f'  - {d.diagnosis_name}'
                    if d.icd10_code:
                        line += f' ({d.icd10_code})'
                    lines.append(line)
            generated[section] = '\n'.join(lines) if lines else 'No active diagnoses'

        elif section == 'Social History':
            # Pull from parsed XML social_history if available
            generated[section] = ''

        elif section == 'Assessment':
            diags = PatientDiagnosis.query.filter_by(
                user_id=current_user.id, mrn=mrn, status='active'
            ).all()
            if diags:
                lines = []
                for i, d in enumerate(diags, 1):
                    line = f'{i}. {d.diagnosis_name}'
                    if d.icd10_code:
                        line += f' ({d.icd10_code})'
                    lines.append(line)
                generated[section] = '\n'.join(lines)
            else:
                generated[section] = ''

        elif section == 'Plan':
            # Generate basic plan from care gaps + overdue labs
            lines = []
            gaps = CareGap.query.filter_by(
                user_id=current_user.id, mrn=mrn
            ).filter(CareGap.status.in_(['open', 'in_progress'])).all()
            if gaps:
                lines.append('Preventive care:')
                for g in gaps:
                    lines.append(f'  - {g.gap_type}: {g.gap_name or "due"}')

            overdue = LabTrack.query.filter_by(
                user_id=current_user.id, mrn=mrn, is_overdue=True, is_archived=False
            ).all()
            if overdue:
                lines.append('Lab orders:')
                for lt in overdue:
                    lines.append(f'  - {lt.lab_name} (overdue)')

            generated[section] = '\n'.join(lines) if lines else ''

        elif section == 'Physical Exam':
            vitals = PatientVitals.query.filter_by(
                user_id=current_user.id, mrn=mrn
            ).order_by(PatientVitals.measured_at.desc()).all()
            seen = set()
            lines = ['Vitals:']
            for v in vitals:
                if v.vital_name not in seen:
                    seen.add(v.vital_name)
                    lines.append(f'  {v.vital_name}: {v.vital_value} {v.vital_unit}')
                if len(seen) >= 8:
                    break
            generated[section] = '\n'.join(lines) if len(lines) > 1 else ''

        elif section == 'Health Concerns':
            gaps = CareGap.query.filter_by(
                user_id=current_user.id, mrn=mrn
            ).filter(CareGap.status.in_(['open', 'in_progress'])).all()
            if gaps:
                generated[section] = '\n'.join(f'- {g.gap_type}' for g in gaps)
            else:
                generated[section] = ''
        else:
            generated[section] = ''

    return jsonify({'success': True, 'sections': generated})


# ======================================================================
# POST /patient/upload-xml — Dashboard drag-and-drop XML upload (auto-detect MRN)
# ======================================================================
@patient_bp.route('/patient/upload-xml', methods=['POST'])
@login_required
def upload_xml_auto():
    """Upload one or more CDA Clinical Summary XML files, auto-detecting MRN."""
    files = request.files.getlist('xml_files')
    if not files:
        return jsonify({'success': False, 'message': 'No files uploaded'}), 400

    results = []
    for f in files:
        if not f.filename or not f.filename.lower().endswith('.xml'):
            results.append({'file': f.filename or '?', 'success': False, 'message': 'Not an XML file'})
            continue

        export_folder = getattr(config, 'CLINICAL_SUMMARY_EXPORT_FOLDER', 'data/clinical_summaries/')
        if not os.path.isabs(export_folder):
            export_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), export_folder)
        os.makedirs(export_folder, exist_ok=True)

        safe_name = f'upload_{current_user.id}_{int(datetime.now().timestamp())}_{f.filename}'
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '._-')
        xml_path = os.path.join(export_folder, safe_name)

        try:
            f.save(xml_path)
            from agent.clinical_summary_parser import parse_clinical_summary, store_parsed_summary

            parsed = parse_clinical_summary(xml_path)
            mrn = parsed.get('patient_mrn', '')
            if not mrn:
                results.append({'file': f.filename, 'success': False, 'message': 'No MRN found in XML'})
                continue

            store_parsed_summary(current_user.id, mrn, parsed)

            # Backfill missing ICD-10 codes via NIH API
            _backfill_icd10_codes(current_user.id, mrn)

            # Auto-classify diagnoses
            for diag in PatientDiagnosis.query.filter_by(user_id=current_user.id, mrn=mrn).all():
                diag.diagnosis_category = _classify_diagnosis(diag.diagnosis_name, diag.icd10_code)
            db.session.commit()

            sections = [k for k, v in parsed.items() if v and k not in ('patient_name', 'patient_mrn', 'patient_dob')]
            results.append({
                'file': f.filename,
                'success': True,
                'mrn': mrn,
                'patient_name': parsed.get('patient_name', ''),
                'sections': sections,
            })
        except Exception as e:
            db.session.rollback()
            results.append({'file': f.filename, 'success': False, 'message': str(e)})
        finally:
            try:
                if os.path.exists(xml_path):
                    os.remove(xml_path)
            except OSError:
                pass

    ok_count = sum(1 for r in results if r.get('success'))
    return jsonify({
        'success': ok_count > 0,
        'message': f'Imported {ok_count} of {len(results)} file(s)',
        'results': results,
    })


# ======================================================================
# GET /patients — Patient Roster (My Patients panel)
# ======================================================================
@patient_bp.route('/patients')
@login_required
def roster():
    """Show patients — 'all' (imported by user) or 'mine' (claimed by user)."""
    view = request.args.get('view', 'all')
    if view == 'mine':
        patients = (
            PatientRecord.query
            .filter_by(claimed_by=current_user.id)
            .order_by(PatientRecord.patient_name)
            .all()
        )
    else:
        view = 'all'
        patients = (
            PatientRecord.query
            .filter_by(user_id=current_user.id)
            .order_by(PatientRecord.patient_name)
            .all()
        )

    return render_template(
        'patient_roster.html',
        patients=patients,
        current_view=view,
    )


# ======================================================================
# POST /patient/<mrn>/diagnosis/<id>/toggle-category
# ======================================================================
@patient_bp.route('/patient/<mrn>/diagnosis/<int:dx_id>/toggle-category', methods=['POST'])
@login_required
def toggle_dx_category(mrn, dx_id):
    """Toggle a diagnosis between acute and chronic."""
    dx = db.session.get(PatientDiagnosis, dx_id)
    if not dx:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    new_cat = 'acute' if (dx.diagnosis_category or 'chronic') == 'chronic' else 'chronic'
    dx.diagnosis_category = new_cat
    db.session.commit()
    return jsonify({'success': True, 'new_category': new_cat})


# ======================================================================
# POST /patient/<mrn>/<item_type>/<id>/toggle-status
# ======================================================================
@patient_bp.route('/patient/<mrn>/<item_type>/<int:item_id>/toggle-status', methods=['POST'])
@login_required
def toggle_item_status(mrn, item_type, item_id):
    """Toggle active/inactive status for a medication or diagnosis."""
    if item_type == 'medication':
        item = db.session.get(PatientMedication, item_id)
    elif item_type == 'diagnosis':
        item = db.session.get(PatientDiagnosis, item_id)
    else:
        return jsonify({'success': False, 'error': 'Invalid type'}), 400

    if not item:
        return jsonify({'success': False, 'error': 'Not found'}), 404

    new_status = 'inactive' if item.status == 'active' else 'active'
    item.status = new_status
    db.session.commit()
    return jsonify({'success': True, 'new_status': new_status})


# ======================================================================
# POST /patient/<mrn>/medication/<id>/update — Edit medication fields
# ======================================================================
@patient_bp.route('/patient/<mrn>/medication/<int:med_id>/update', methods=['POST'])
@login_required
def update_medication(mrn, med_id):
    """Update a medication's dosage or frequency. Marks user_modified flag."""
    med = PatientMedication.query.filter_by(
        id=med_id, user_id=current_user.id, mrn=mrn
    ).first()
    if not med:
        return jsonify({'success': False, 'error': 'Not found'}), 404

    data = request.get_json(silent=True) or {}
    field = data.get('field', '')
    value = (data.get('value') or '').strip()

    if field == 'dosage':
        med.dosage = value
    elif field == 'frequency':
        med.frequency = value
    else:
        return jsonify({'success': False, 'error': 'Invalid field'}), 400

    med.user_modified = True
    try:
        db.session.commit()
        return jsonify({'success': True, 'field': field, 'value': value, 'user_modified': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating medication: {str(e)}")
        return jsonify({'success': False, 'error': 'Update failed'}), 500


# ======================================================================
# POST /patient/<mrn>/diagnosis/add — Add a new diagnosis (UX-20)
# ======================================================================
@patient_bp.route('/patient/<mrn>/diagnosis/add', methods=['POST'])
@login_required
def add_diagnosis(mrn):
    """Add a new ICD-10 diagnosis to the patient's problem list."""
    data = request.get_json(silent=True) or {}
    name = (data.get('diagnosis_name') or '').strip()
    code = (data.get('icd10_code') or '').strip()
    category = (data.get('category') or 'chronic').strip()

    if not name:
        return jsonify({'success': False, 'error': 'Diagnosis name required'}), 400

    try:
        dx = PatientDiagnosis(
            user_id=current_user.id,
            mrn=mrn,
            diagnosis_name=name,
            icd10_code=code,
            diagnosis_category=category,
            status='active',
        )
        db.session.add(dx)
        db.session.commit()
        return jsonify({
            'success': True,
            'data': {'id': dx.id, 'diagnosis_name': dx.diagnosis_name, 'icd10_code': dx.icd10_code}
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding diagnosis: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to add diagnosis'}), 500


# ======================================================================
# POST /patient/<mrn>/diagnosis/<id>/remove — Soft-delete a diagnosis (UX-20)
# ======================================================================
@patient_bp.route('/patient/<mrn>/diagnosis/<int:dx_id>/remove', methods=['POST'])
@login_required
def remove_diagnosis(mrn, dx_id):
    """Soft-delete a diagnosis by setting status to 'resolved'."""
    dx = PatientDiagnosis.query.filter_by(
        id=dx_id, user_id=current_user.id, mrn=mrn
    ).first()
    if not dx:
        return jsonify({'success': False, 'error': 'Not found'}), 404

    dx.status = 'resolved'
    db.session.commit()
    return jsonify({'success': True})


# ======================================================================
# POST /patient/<mrn>/update-demographics — Edit patient demographics
# ======================================================================
@patient_bp.route('/patient/<mrn>/update-demographics', methods=['POST'])
@login_required
def update_demographics(mrn):
    """Update patient demographics (name, DOB, sex). Re-evaluates care gaps on sex change."""
    data = request.get_json(silent=True) or {}
    record = PatientRecord.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).first()
    if not record:
        record = PatientRecord(user_id=current_user.id, mrn=mrn)
        db.session.add(record)

    old_sex = record.patient_sex or ''

    if 'patient_name' in data and data['patient_name'].strip():
        record.patient_name = data['patient_name'].strip()
    if 'patient_dob' in data:
        record.patient_dob = data['patient_dob'].strip()
    if 'patient_sex' in data:
        record.patient_sex = data['patient_sex'].strip()

    db.session.commit()

    # Re-evaluate care gaps when sex changes
    new_sex = record.patient_sex or ''
    if new_sex and new_sex != old_sex:
        try:
            from agent.caregap_engine import evaluate_and_persist_gaps
            patient_data = {
                'mrn': mrn,
                'sex': new_sex,
                'dob': record.patient_dob or '',
                'age': None,
            }
            evaluate_and_persist_gaps(current_user.id, mrn, patient_data, current_app._get_current_object())
        except Exception as e:
            current_app.logger.error(f"Care gap re-eval on sex change failed for MRN {mrn[-4:]}: {e}")

    return jsonify({'success': True})


# ======================================================================
# GET /patient/<mrn>/print — Print patient paperwork (stub)
# ======================================================================
@patient_bp.route('/patient/<mrn>/print')
@login_required
def print_paperwork(mrn):
    """Stub — future patient paperwork printing (visit summary, after-visit instructions, etc.)."""
    record = PatientRecord.query.filter_by(mrn=mrn, claimed_by=current_user.id).first()
    if not record:
        record = PatientRecord.query.filter_by(mrn=mrn).first()
    mrn_display = mrn
    return render_template('patient_print_stub.html', record=record, mrn_display=mrn_display)


# ======================================================================
# GET /api/icd10/search — Proxy to NIH ICD-10 API + local CSV fallback
# ======================================================================
_icd10_local_cache = None

def _load_icd10_csv():
    """Load local ICD-10 codes from billing CSV (cached in memory)."""
    global _icd10_local_cache
    if _icd10_local_cache is not None:
        return _icd10_local_cache
    import csv
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'Documents', 'billing_resources',
        'calendar_year_dx_revenue_priority_icd10.csv'
    )
    codes = []
    try:
        with open(csv_path, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                desc = (row.get('ICD & Description') or '').strip()
                if not desc:
                    continue
                parts = desc.split(' ', 1)
                if len(parts) == 2:
                    codes.append({'code': parts[0], 'name': parts[1]})
    except FileNotFoundError:
        pass
    _icd10_local_cache = codes
    return codes


@patient_bp.route('/api/icd10/search')
@login_required
def icd10_search():
    """Search ICD-10-CM codes — local CSV first, then NIH API."""
    import urllib.request
    import urllib.parse
    import urllib.error

    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'results': []})

    q_lower = query.lower()

    # Local CSV matches first (instant, no network)
    local_codes = _load_icd10_csv()
    local_matches = [
        c for c in local_codes
        if q_lower in c['code'].lower() or q_lower in c['name'].lower()
    ]

    # NIH API for broader results
    api_results = []
    url = (
        'https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search'
        '?sf=code,name&terms=' + urllib.parse.quote(query)
    )
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if len(data) >= 4 and data[3]:
                for item in data[3]:
                    if len(item) >= 2:
                        api_results.append({'code': item[0], 'name': item[1]})
    except Exception:
        pass  # local results still available

    # Merge: local first, then API (deduplicated)
    seen = set()
    results = []
    for r in local_matches + api_results:
        if r['code'] not in seen:
            seen.add(r['code'])
            results.append(r)
        if len(results) >= 25:
            break

    return jsonify({'results': results})
"""
CareCompanion — Diagnosis Service

ICD-10 classification and backfill helpers.
Extracted from routes/patient.py (Band 3 B1.6).
"""

import json
import logging

from models import db
from models.patient import PatientDiagnosis
from models.api_cache import Icd10Cache

logger = logging.getLogger(__name__)

# ICD-10 prefixes that indicate acute conditions
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

# Module-level cache for the local ICD-10 CSV (loaded once per process)
_icd10_local_cache = None


def classify_diagnosis(name, icd10):
    """Classify a diagnosis as 'acute' or 'chronic' based on ICD-10 code and name."""
    icd = (icd10 or '').upper().replace('.', '')
    name_lower = (name or '').lower()

    for prefix in ACUTE_ICD10_PREFIXES:
        if icd.startswith(prefix):
            return 'acute'

    for kw in ACUTE_KEYWORDS:
        if kw in name_lower:
            return 'acute'

    return 'chronic'


def backfill_icd10_codes(user_id, mrn, cache_only=False):
    """
    Ensure every PatientDiagnosis for this patient has an NIH-verified ICD-10 code.

    Resolution order:
      1. Check the local Icd10Cache table (fast, no network).
      2. If not cached and cache_only=False, query the NIH Clinical Tables API
         via ICD10Service and store the result in icd10_cache.
      3. NIH API codes always supersede codes that came from XML files.
    """
    all_diags = PatientDiagnosis.query.filter(
        PatientDiagnosis.user_id == user_id,
        PatientDiagnosis.mrn == mrn,
    ).all()

    if not all_diags:
        return

    # Lazy-init the ICD10 service
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
                entry = Icd10Cache(
                    diagnosis_name_lower=name_lower,
                    icd10_code=code,
                    icd10_description=desc,
                    source='nih_api',
                )
                db.session.add(entry)
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


def load_icd10_csv():
    """Load local ICD-10 codes from billing CSV (cached in memory)."""
    global _icd10_local_cache
    if _icd10_local_cache is not None:
        return _icd10_local_cache
    import csv
    import os
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
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

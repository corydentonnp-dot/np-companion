"""
CareCompanion — Billing Engine Shared Utilities

Common helper functions used across all detector modules.
"""

from datetime import date, datetime


def age_from_dob(dob) -> int:
    """Calculate age in whole years from a date-of-birth."""
    if dob is None:
        return 0
    if isinstance(dob, str):
        for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
            try:
                dob = datetime.strptime(dob, fmt).date()
                break
            except ValueError:
                continue
        else:
            return 0
    if isinstance(dob, datetime):
        dob = dob.date()
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def has_dx(diagnoses: list, prefixes) -> bool:
    """
    Check whether any diagnosis code starts with one of the given prefixes.

    Parameters
    ----------
    diagnoses : list[str] or list[dict]
        Either plain ICD-10 code strings or dicts with an ``icd10`` key.
    prefixes : str | tuple | list
        One or more ICD-10 prefix strings (e.g. ``"E11"`` or ``["E10", "E11"]``).
    """
    if isinstance(prefixes, str):
        prefixes = (prefixes,)
    prefixes = tuple(p.upper() for p in prefixes)
    for dx in _normalise_dx_list(diagnoses):
        if dx.upper().startswith(prefixes):
            return True
    return False


def get_dx(diagnoses: list, prefixes) -> list:
    """Return all diagnosis codes matching the given prefixes."""
    if isinstance(prefixes, str):
        prefixes = (prefixes,)
    prefixes = tuple(p.upper() for p in prefixes)
    return [dx for dx in _normalise_dx_list(diagnoses) if dx.upper().startswith(prefixes)]


def months_since(ref_date) -> int:
    """Return the number of whole months elapsed since *ref_date*."""
    if ref_date is None:
        return 9999  # treat missing date as "overdue"
    if isinstance(ref_date, str):
        for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
            try:
                ref_date = datetime.strptime(ref_date, fmt).date()
                break
            except ValueError:
                continue
        else:
            return 9999
    if isinstance(ref_date, datetime):
        ref_date = ref_date.date()
    today = date.today()
    return (today.year - ref_date.year) * 12 + (today.month - ref_date.month)


def has_medication(medications: list, drug_names) -> bool:
    """
    Check whether any active medication matches the given drug names.

    Parameters
    ----------
    medications : list[str] or list[dict]
        Either plain drug name strings or dicts with a ``name`` key.
    drug_names : str | list
        One or more drug name substrings to match (case-insensitive).
    """
    if isinstance(drug_names, str):
        drug_names = [drug_names]
    drug_names = [n.lower() for n in drug_names]
    for med in _normalise_med_list(medications):
        med_lower = med.lower()
        for name in drug_names:
            if name in med_lower:
                return True
    return False


def get_medications(medications: list, drug_names) -> list:
    """Return all medication entries matching the given drug names."""
    if isinstance(drug_names, str):
        drug_names = [drug_names]
    drug_names = [n.lower() for n in drug_names]
    results = []
    for med in _normalise_med_list(medications):
        med_lower = med.lower()
        if any(name in med_lower for name in drug_names):
            results.append(med)
    return results


def is_overdue(last_date, interval_months: int) -> bool:
    """Return True if more than *interval_months* have elapsed since *last_date*."""
    return months_since(last_date) >= interval_months


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _normalise_dx_list(diagnoses: list) -> list:
    """Extract plain code strings from a heterogeneous diagnosis list."""
    codes = []
    for item in (diagnoses or []):
        if isinstance(item, str):
            codes.append(item.strip())
        elif isinstance(item, dict):
            code = item.get("icd10") or item.get("code") or item.get("icd10_code") or ""
            if code:
                codes.append(code.strip())
    return codes


def _normalise_med_list(medications: list) -> list:
    """Extract plain drug name strings from a heterogeneous medication list."""
    names = []
    for item in (medications or []):
        if isinstance(item, str):
            names.append(item.strip())
        elif isinstance(item, dict):
            name = item.get("name") or item.get("drug_name") or item.get("medication") or ""
            if name:
                names.append(name.strip())
    return names


# ------------------------------------------------------------------
# ICD-10 Revenue Reference Data
# ------------------------------------------------------------------

import csv
import os
import re as _re

# Singleton loaded on first access
_ICD10_REVENUE_DATA = None  # dict[str, dict]
_ICD10_FAMILY_INDEX = None  # dict[str(3-char prefix), list[str]]


def _load_icd10_revenue():
    """Parse the practice revenue CSV into a lookup dict keyed by ICD-10 code."""
    global _ICD10_REVENUE_DATA, _ICD10_FAMILY_INDEX
    if _ICD10_REVENUE_DATA is not None:
        return

    _ICD10_REVENUE_DATA = {}
    _ICD10_FAMILY_INDEX = {}
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'Documents', 'billing_resources',
        'calendar_year_dx_revenue_priority_icd10.csv',
    )
    if not os.path.isfile(csv_path):
        return

    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = (row.get('ICD & Description') or '').strip()
            if not raw:
                continue
            # Extract ICD-10 code (first token before space)
            parts = raw.split(' ', 1)
            code = parts[0].strip().upper()
            description = parts[1].strip() if len(parts) > 1 else ''
            if not _re.match(r'^[A-Z]\d', code):
                continue  # skip malformed rows

            # Parse dollar amounts (remove $, commas)
            def _parse_dollar(val):
                if not val:
                    return 0.0
                return float(val.replace('$', '').replace(',', '').strip() or '0')

            def _parse_pct(val):
                if not val:
                    return 0.0
                return float(val.replace('%', '').strip() or '0') / 100.0

            per_encounter = _parse_dollar(row.get('$/ Encounter', ''))
            tier = (row.get('Teir') or row.get('Tier') or '').strip()
            retention = _parse_pct(row.get('Retention Score', ''))

            entry = {
                'code': code,
                'description': description,
                'encounters': int(row.get('Encounters', '0').strip() or '0'),
                'billed': _parse_dollar(row.get('$ Billed ', '')),
                'received': _parse_dollar(row.get('$ Recieved', '')),
                'per_encounter': per_encounter,
                'retention': retention,
                'priority_score': float(row.get('Priority Score (V2)', '0').strip() or '0'),
                'tier': tier,
            }
            _ICD10_REVENUE_DATA[code] = entry

            # Index by 3-character family (e.g. "E11", "I10", "F41")
            family = code[:3]
            _ICD10_FAMILY_INDEX.setdefault(family, []).append(code)


def get_icd10_revenue(code):
    """
    Look up revenue data for a single ICD-10 code.
    Returns dict with per_encounter, tier, etc. or None.
    """
    _load_icd10_revenue()
    return _ICD10_REVENUE_DATA.get((code or '').strip().upper())


def find_revenue_alternatives(code):
    """
    Find same-family ICD-10 codes with higher per-encounter revenue.
    Only returns codes within the same 3-character category (e.g. E11.xx)
    to ensure clinical relevance — never suggests a code from a
    different diagnostic family.

    Returns list of dicts sorted by per_encounter descending,
    each with: code, description, per_encounter, delta, tier.
    Excludes the input code itself and Z-codes (screening/admin).
    """
    _load_icd10_revenue()
    if not code:
        return []
    code = code.strip().upper()
    family = code[:3]

    # Skip Z-codes entirely — they are screening/admin, not billable diagnoses
    if family.startswith('Z'):
        return []

    current = _ICD10_REVENUE_DATA.get(code)
    current_rev = current['per_encounter'] if current else 0.0

    siblings = _ICD10_FAMILY_INDEX.get(family, [])
    alternatives = []
    for sib_code in siblings:
        if sib_code == code:
            continue
        sib = _ICD10_REVENUE_DATA[sib_code]
        # Skip Z-codes and codes with no revenue
        if sib_code.startswith('Z') or sib['per_encounter'] <= 0:
            continue
        # Only suggest codes that pay more
        if sib['per_encounter'] > current_rev:
            alternatives.append({
                'code': sib_code,
                'description': sib['description'],
                'per_encounter': sib['per_encounter'],
                'delta': round(sib['per_encounter'] - current_rev, 2),
                'tier': sib['tier'],
                'retention': sib['retention'],
            })

    alternatives.sort(key=lambda x: x['per_encounter'], reverse=True)
    return alternatives

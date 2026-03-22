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

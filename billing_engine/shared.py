"""
CareCompanion — Billing Engine Shared Clinical Helpers
File: billing_engine/shared.py

Module-level clinical helper functions used by multiple detectors.
Migrated from app/services/billing_rules.py module-level functions
so they can be imported by any detector without circular dependencies.

Functions here handle VSAC code lookups, qualifying-diagnosis matching,
chronic condition counting, date math, and MRN hashing.
"""

import hashlib
import logging
import threading
from datetime import datetime, date, timedelta

from app.api_config import CCM_CHRONIC_CONDITION_PREFIXES

logger = logging.getLogger(__name__)

# VSAC condition code cache — populated lazily, avoids repeated DB queries
_vsac_code_cache = {}
_vsac_code_cache_lock = threading.Lock()


def get_vsac_codes(category: str) -> set:
    """
    Return cached set of ICD-10 codes from VSAC for a billing category.
    Returns empty set if VSAC data is unavailable (hardcoded fallback used).
    """
    with _vsac_code_cache_lock:
        if category in _vsac_code_cache:
            return _vsac_code_cache[category]
    try:
        from billing_engine.valueset_map import get_vsac_icd10_codes  # B6.7
        codes = set(get_vsac_icd10_codes(category))
    except Exception:
        codes = set()
    with _vsac_code_cache_lock:
        _vsac_code_cache[category] = codes
    return codes


def has_qualifying_dx(diagnoses, vsac_category, fallback_prefixes,
                      *, exclude_resolved=True):
    """
    Return diagnoses matching a billing category's condition set.
    Tries VSAC exact code match first; falls back to hardcoded prefix match.
    """
    vsac_codes = get_vsac_codes(vsac_category)
    matches = []
    for d in diagnoses:
        code = (d.get("icd10_code") or "").upper().strip()
        if not code:
            continue
        if exclude_resolved and (d.get("status") or "").lower() == "resolved":
            continue
        if vsac_codes and code in vsac_codes:
            matches.append(d)
            continue
        if any(code.startswith(prefix) for prefix in fallback_prefixes):
            matches.append(d)
    return matches


def hash_mrn(mrn):
    """SHA-256 hash of MRN for safe storage. Never store plain MRN in billing tables."""
    return hashlib.sha256(str(mrn).encode()).hexdigest()


def count_chronic_conditions(diagnoses):
    """
    Count active chronic conditions from the CCM eligibility list.
    Uses VSAC codes when cached, falls back to hardcoded prefixes.
    Deduplicates by 3-char ICD-10 prefix to avoid double-counting.
    """
    vsac_codes = get_vsac_codes("ccm")
    count = 0
    seen_prefixes = set()
    for dx in diagnoses:
        code = (dx.get("icd10_code") or "").upper()
        status = (dx.get("status") or "").lower()
        if status == "resolved":
            continue
        if vsac_codes and code in vsac_codes:
            dedup = code[:3]
            if dedup not in seen_prefixes:
                count += 1
                seen_prefixes.add(dedup)
            continue
        for prefix in CCM_CHRONIC_CONDITION_PREFIXES:
            if code.startswith(prefix) and prefix not in seen_prefixes:
                count += 1
                seen_prefixes.add(prefix)
                break
    return count


def get_chronic_condition_names(diagnoses):
    """Return names of chronic conditions for the eligibility description."""
    vsac_codes = get_vsac_codes("ccm")
    names = []
    seen_prefixes = set()
    for dx in diagnoses:
        code = (dx.get("icd10_code") or "").upper()
        status = (dx.get("status") or "").lower()
        if status == "resolved":
            continue
        if vsac_codes and code in vsac_codes:
            dedup = code[:3]
            if dedup not in seen_prefixes:
                name = dx.get("diagnosis_name") or code
                names.append(name)
                seen_prefixes.add(dedup)
            continue
        for prefix in CCM_CHRONIC_CONDITION_PREFIXES:
            if code.startswith(prefix) and prefix not in seen_prefixes:
                name = dx.get("diagnosis_name") or code
                names.append(name)
                seen_prefixes.add(prefix)
                break
    return names


# months_since is canonical in billing_engine.utils — re-export for compatibility
from billing_engine.utils import months_since  # noqa: F401, E402


def add_business_days(start_date, days):
    """
    Add N business days to a date (skipping weekends only — no holidays).
    Used for TCM 2-business-day contact window calculation.
    """
    current = start_date
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current

"""
CareCompanion — Patient Helper Utilities

Pure-function helpers for patient name/DOB/age normalization.
No Flask context or DB required — safe to call anywhere.

Extracted from routes/patient.py (Band 3 B1.4).
"""

from datetime import datetime


def mrn_display(mrn):
    """Return full MRN for display."""
    return mrn or ''


def calc_age(dob_str):
    """Calculate age string from DOB string (MM/DD/YYYY or YYYYMMDD)."""
    if not dob_str:
        return ''
    try:
        if '/' in dob_str:
            dob = datetime.strptime(dob_str, '%m/%d/%Y')
        elif len(dob_str) == 8:
            dob = datetime.strptime(dob_str, '%Y%m%d')
        else:
            return ''
        today = datetime.now()
        age = today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )
        return f'{age}y'
    except ValueError:
        return ''


def calc_age_years(dob_str):
    """Calculate numeric age from DOB string. Returns None if unparseable."""
    if not dob_str:
        return None
    try:
        if '/' in dob_str:
            dob = datetime.strptime(dob_str, '%m/%d/%Y')
        elif len(dob_str) == 8:
            dob = datetime.strptime(dob_str, '%Y%m%d')
        else:
            return None
        today = datetime.now()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except ValueError:
        return None


def normalize_name(name):
    """Normalize patient names from schedule/query data for display.

    Converts "LAST, FIRST" format to "FIRST LAST". Collapses extra whitespace.
    """
    name = (name or '').strip()
    if not name:
        return ''
    if ',' in name:
        parts = [part.strip() for part in name.split(',', 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            return f'{parts[1]} {parts[0]}'
    return ' '.join(name.split())


def normalize_dob(dob_str):
    """Normalize DOB strings to YYYYMMDD for PatientRecord storage.

    Accepts: YYYYMMDD, YYYY-MM-DD, MM/DD/YYYY, MM/DD/YY, and bare 8-digit strings.
    """
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

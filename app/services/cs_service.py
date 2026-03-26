"""
CareCompanion — Controlled Substance Service

PDMP overdue patient lookup extracted from routes/tools.py (Band 3 B1.20).
"""

from models.controlled_substance import ControlledSubstanceEntry


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

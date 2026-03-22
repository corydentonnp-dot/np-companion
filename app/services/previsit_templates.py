"""
Pre-visit template selector.

Given an appointment dict (with fields like insurer, dob, reason, etc.),
selects the most appropriate pre-visit template for billing prep.
"""


def select_previsit_template(appt: dict) -> str:
    """Return the template name best matching the appointment context.

    Parameters
    ----------
    appt : dict
        Appointment data with keys such as 'insurer', 'dob', 'reason',
        'patient_name', etc.

    Returns
    -------
    str
        Template identifier (e.g. 'medicare_awv', 'commercial_followup').
    """
    insurer = (appt.get('insurer') or '').upper()
    reason = (appt.get('reason') or '').upper()

    # Medicare Annual Wellness Visit
    if any(kw in insurer for kw in ('MEDICARE', 'MCARE', 'RAILROAD')) and \
       any(kw in reason for kw in ('AWV', 'ANNUAL WELL', 'WELLNESS', 'IPPE')):
        return 'medicare_awv'

    # Medicare follow-up
    if any(kw in insurer for kw in ('MEDICARE', 'MCARE', 'RAILROAD')):
        return 'medicare_followup'

    # Commercial / managed-care AWV
    if any(kw in reason for kw in ('PHYSICAL', 'ANNUAL', 'WELL VISIT', 'AWV')):
        return 'commercial_awv'

    # Default
    return 'commercial_followup'

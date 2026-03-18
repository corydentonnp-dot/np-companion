"""
NP Companion — Utilities Package

Re-exports log_access so existing `from utils import log_access` still works.
Also provides path resolution helpers via utils.paths.

safe_patient_id(mrn) — SHA-256 hash of a plain MRN for HIPAA-safe logging.
  Use this everywhere a patient identifier is needed outside of PatientRecord.
  Never store or log the plain MRN.
"""

import hashlib
from datetime import datetime, timezone

from models import db
from models.audit import AuditLog


def safe_patient_id(mrn: str) -> str:
    """
    Return a SHA-256 hex digest of the plain MRN for HIPAA-safe storage
    and logging. The plain MRN must never appear in logs, notifications,
    or any table outside of PatientRecord.

    Parameters
    ----------
    mrn : str
        The plain patient MRN as read from Amazing Charts or the schedule.

    Returns
    -------
    str
        64-character lowercase hex SHA-256 digest of the MRN.

    Example
    -------
    >>> safe_patient_id("123456")
    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92'
    """
    if not mrn:
        raise ValueError("safe_patient_id: mrn must be a non-empty string")
    return hashlib.sha256(str(mrn).encode("utf-8")).hexdigest()


def log_access(user_id, action, module='', ip_address=''):
    """
    Write one row to the audit_log table.

    Parameters
    ----------
    user_id : int
        The ID of the logged-in user performing the action.
    action : str
        A short description e.g. 'GET /dashboard' or 'view_lab_tracker'.
    module : str
        The blueprint / feature name e.g. 'auth', 'timer', 'inbox'.
    ip_address : str
        The client's IP address (request.remote_addr).
    """
    entry = AuditLog(
        user_id=user_id,
        timestamp=datetime.now(timezone.utc),
        action=action,
        module=module,
        ip_address=ip_address,
    )
    db.session.add(entry)
    # Commit is handled by the caller or by the after_request hook

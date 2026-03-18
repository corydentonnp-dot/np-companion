"""
NP Companion — Utilities Package

Re-exports log_access so existing `from utils import log_access` still works.
Also provides path resolution helpers via utils.paths.
"""

from datetime import datetime, timezone

from models import db
from models.audit import AuditLog


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

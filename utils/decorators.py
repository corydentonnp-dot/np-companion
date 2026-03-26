"""
CareCompanion — Shared Route Decorators

Provides the require_role() decorator used across multiple blueprint modules.
Moving this here eliminates cross-route imports of routes.auth.

Extracted from routes/auth.py (Band 3 B1.22 remediation).
"""

from functools import wraps

from flask import redirect, url_for, flash
from flask_login import current_user


def require_role(role):
    """
    Decorator that restricts a route to a single role (or admin).

    Usage::

        @some_bp.route('/protected')
        @login_required
        @require_role('admin')
        def protected_page(): ...

    Admins always pass. Otherwise the user's role must match exactly.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            # Admins bypass all role restrictions
            if current_user.role == 'admin':
                return func(*args, **kwargs)
            if current_user.role != role:
                flash('You do not have permission to access that page.', 'error')
                return redirect(url_for('auth.login'))
            return func(*args, **kwargs)
        return wrapper
    return decorator

"""
Phase 13 — Progressive Feature Enablement

Three complexity tiers gate features so new users aren't overwhelmed:
  Essential  — visible by default for all new users
  Standard   — enabled after 1 week or manual opt-in
  Advanced   — manual opt-in only
"""

from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

# ── Tier definitions ────────────────────────────────────────────────
TIER_ORDER = {'essential': 0, 'standard': 1, 'advanced': 2}

FEATURE_TIERS = {
    # Essential — always visible
    'dashboard':        'essential',
    'patient_overview':  'essential',
    'patient_meds':      'essential',
    'inbox':             'essential',
    'timer':             'essential',
    'notifications':     'essential',
    'oncall':            'essential',

    # Standard — enabled after 1 week or opt-in
    'billing':           'standard',
    'labtrack':          'standard',
    'caregap':           'standard',
    'drug_safety':       'standard',
    'lab_interpretation': 'standard',
    'metrics':           'standard',
    'briefing':          'standard',

    # Advanced — manual opt-in only
    'orders':            'advanced',
    'dot_phrases':       'advanced',
    'clinical_guidelines': 'advanced',
    'formulary_gaps':    'advanced',
    'pubmed':            'advanced',
    'schedule_scraper':  'advanced',
    'reformatter':       'advanced',
    'medref':            'advanced',
    'patient_gen':       'advanced',
}

TIER_DESCRIPTIONS = {
    'essential': 'Core tools for daily patient care',
    'standard':  'Clinical intelligence and population health',
    'advanced':  'Power tools for complex workflows',
}

# ── Feature check ───────────────────────────────────────────────────

def is_feature_enabled(user, feature_name):
    """Check if *feature_name* is enabled for *user* given their tier."""
    if user is None or not user.is_authenticated:
        return False

    # Admin always has full access
    if getattr(user, 'role', '') == 'admin':
        return True

    # Per-feature overrides (user toggled individually in Settings)
    overrides = user.get_pref('feature_overrides', {})
    if feature_name in overrides:
        return overrides[feature_name]

    # Tier-based check
    user_tier = user.get_pref('feature_tier', 'essential')
    feature_tier = FEATURE_TIERS.get(feature_name, 'essential')
    return TIER_ORDER.get(user_tier, 0) >= TIER_ORDER.get(feature_tier, 0)


# ── Route decorator ─────────────────────────────────────────────────

def require_feature(feature_name):
    """Decorator that blocks access if the user's tier doesn't include *feature_name*."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if not is_feature_enabled(current_user, feature_name):
                flash('This feature is not enabled in your current plan. '
                      'Upgrade in Settings → Features.', 'warning')
                return redirect(url_for('dashboard.dashboard_home'))
            return func(*args, **kwargs)
        return wrapper
    return decorator

"""
NP Companion — NetPractice Admin Routes

File location: np-companion/routes/netpractice_admin.py

Provides:
  GET  /admin/netpractice            — settings page (URL, client number)
  POST /admin/netpractice/save       — save global NP settings
  GET  /admin/netpractice/wizard     — setup wizard for recording nav steps
  POST /api/netpractice/save-steps   — save recorded navigation steps
  POST /api/netpractice/test-login   — test NP credentials
  GET  /api/netpractice/user-steps   — get current user's nav steps
"""

import json
import os
from datetime import datetime, timezone

from flask import (
    Blueprint, render_template, request, jsonify,
    redirect, url_for, flash, current_app,
)
from flask_login import login_required, current_user
from models import db
from models.user import User

np_admin_bp = Blueprint('np_admin', __name__)


# ======================================================================
# Helpers
# ======================================================================
def _require_admin(f):
    """Inline admin check — returns 403 if the user is not admin."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Admin access required.', 'error')
            return redirect('/dashboard')
        return f(*args, **kwargs)
    return wrapper


def _read_np_settings():
    """Read global NetPractice settings from data/np_settings.json."""
    path = os.path.join(current_app.root_path, 'data', 'np_settings.json')
    if not os.path.exists(path):
        return {
            'netpractice_url': current_app.config.get('NETPRACTICE_URL', ''),
            'client_number': '',
            'scrape_time': '18:00',
            'max_appointment_hour': '19:00',
        }
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {
            'netpractice_url': '',
            'client_number': '',
            'scrape_time': '18:00',
            'max_appointment_hour': '19:00',
        }


def _save_np_settings(data):
    """Write global NetPractice settings to data/np_settings.json."""
    path = os.path.join(current_app.root_path, 'data', 'np_settings.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


# ======================================================================
# GET /admin/netpractice — settings page
# ======================================================================
@np_admin_bp.route('/admin/netpractice')
@login_required
@_require_admin
def admin_netpractice():
    """Global NetPractice configuration page."""
    settings = _read_np_settings()
    users = User.query.filter(User.is_active_account == True).order_by(User.display_name).all()
    return render_template(
        'admin_netpractice.html',
        settings=settings,
        users=users,
    )


# ======================================================================
# POST /admin/netpractice/save — save global settings
# ======================================================================
@np_admin_bp.route('/admin/netpractice/save', methods=['POST'])
@login_required
@_require_admin
def admin_save_np_settings():
    """Save the global NetPractice URL and related settings."""
    settings = _read_np_settings()

    settings['netpractice_url'] = request.form.get('netpractice_url', '').strip()
    settings['client_number'] = request.form.get('client_number', '').strip()
    settings['scrape_time'] = request.form.get('scrape_time', '18:00').strip()
    settings['max_appointment_hour'] = request.form.get('max_appointment_hour', '19:00').strip()
    settings['updated_at'] = datetime.now(timezone.utc).isoformat()

    _save_np_settings(settings)

    # Also update the Flask config so the scraper picks it up immediately
    current_app.config['NETPRACTICE_URL'] = settings['netpractice_url']

    flash('NetPractice settings saved.', 'success')
    return redirect(url_for('np_admin.admin_netpractice'))


# ======================================================================
# GET /admin/netpractice/wizard — setup wizard page
# ======================================================================
@np_admin_bp.route('/admin/netpractice/wizard')
@login_required
def np_setup_wizard():
    """
    Setup wizard page where users record their navigation steps
    to reach their daily schedule in webPRACTICE.

    This page guides the user through:
    1. Log in to webPRACTICE
    2. Navigate to the schedule page
    3. Record each click/step along the way
    4. Save the steps so the scraper can replay them
    """
    settings = _read_np_settings()
    return render_template(
        'np_setup_wizard.html',
        settings=settings,
        existing_steps=current_user.nav_steps,
    )


# ======================================================================
# POST /api/netpractice/save-steps — save recorded navigation steps
# ======================================================================
@np_admin_bp.route('/api/netpractice/save-steps', methods=['POST'])
@login_required
def api_save_nav_steps():
    """
    Save the user's recorded navigation steps.
    Expects JSON body: { "steps": [...] }

    Each step is a dict like:
    {
        "order": 1,
        "action": "click",
        "target": "Schedule",
        "selector": "a:has-text('Schedule')",
        "description": "Click Schedule in left nav",
        "wait_for": "text=Schedule Menu"
    }
    """
    data = request.get_json(silent=True) or {}
    steps = data.get('steps', [])

    if not isinstance(steps, list):
        return jsonify({'success': False, 'error': 'Steps must be a list'}), 400

    # Validate each step has required fields
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            return jsonify({'success': False, 'error': f'Step {i} is not a dict'}), 400
        if 'action' not in step:
            return jsonify({'success': False, 'error': f'Step {i} missing action'}), 400

    current_user.nav_steps = steps
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Saved {len(steps)} navigation steps',
        'step_count': len(steps),
    })


# ======================================================================
# GET /api/netpractice/user-steps — get current user's nav steps
# ======================================================================
@np_admin_bp.route('/api/netpractice/user-steps')
@login_required
def api_get_nav_steps():
    """Return the current user's recorded navigation steps."""
    return jsonify({
        'success': True,
        'steps': current_user.nav_steps,
        'provider_name': current_user.np_provider_name or '',
        'has_credentials': current_user.has_np_credentials(),
    })


# ======================================================================
# POST /api/netpractice/test-login — test NP credentials
# ======================================================================
@np_admin_bp.route('/api/netpractice/test-login', methods=['POST'])
@login_required
def api_test_np_login():
    """
    Quick test: try to log into webPRACTICE with the user's saved creds.
    Returns success/fail — does NOT scrape anything.

    This is an async operation done synchronously for simplicity.
    It launches a headless browser, tries to log in, and reports back.
    """
    if not current_user.has_np_credentials():
        return jsonify({
            'success': False,
            'error': 'No NetPractice credentials saved. Go to Settings > Account first.',
        })

    settings = _read_np_settings()
    np_url = settings.get('netpractice_url', '')
    client_number = settings.get('client_number', '')

    if not np_url:
        return jsonify({
            'success': False,
            'error': 'NetPractice URL not configured. Ask your admin to set it.',
        })

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'Playwright not installed. Run: pip install playwright && playwright install chromium',
        })

    np_user = current_user.get_np_username()
    np_pass = current_user.get_np_password()

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(np_url, timeout=20000)

            # Fill in the CGM webPRACTICE login form
            # Client Number field
            if client_number:
                client_field = page.locator('input[name*="client" i], input[name*="Client" i]').first
                if client_field.count():
                    client_field.fill(client_number)

            # Username field
            user_field = page.locator('input[name*="user" i], input[name*="User" i]').first
            if user_field.count():
                user_field.fill(np_user)

            # Password field
            pass_field = page.locator('input[type="password"]').first
            if pass_field.count():
                pass_field.fill(np_pass)

            # Click Log In button
            login_btn = page.locator('input[type="submit"], button[type="submit"]').first
            if login_btn.count():
                login_btn.click()

            # Wait for navigation
            page.wait_for_load_state('networkidle', timeout=10000)

            # Check if we're past the login page
            # If we see "Schedule" or "Patient" in the nav, login worked
            page_text = page.content()
            login_success = (
                'Schedule' in page_text
                or 'Patient' in page_text
                or 'Schedule Menu' in page_text
            )

            browser.close()

            if login_success:
                return jsonify({
                    'success': True,
                    'message': 'Login successful! WebPRACTICE authenticated.',
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Login may have failed — could not find expected page content after login.',
                })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Login test failed: {str(e)}',
        })

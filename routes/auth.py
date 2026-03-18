"""
NP Companion — Authentication & Account Routes

File location: np-companion/routes/auth.py

Handles login, logout, registration, account settings, notification
preferences, user admin, and the PIN-verify API endpoint.

Key rules (from copilot-instructions.md):
 - First registered user becomes admin automatically.
 - Subsequent registrations require an admin to be logged in.
 - Passwords must be at least 8 characters.
 - Every route except /login requires @login_required.
 - On login/logout, write data/active_user.json for the background agent.
"""

import json
import os
import subprocess
import webbrowser
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, jsonify, current_app,
)
from flask_login import (
    login_user, logout_user, login_required, current_user,
)
from models import db
from models.user import User


auth_bp = Blueprint('auth', __name__)


# ======================================================================
# ROLE DECORATOR — @require_role('admin'), @require_role('provider')
# ======================================================================
def require_role(role):
    """
    Decorator that restricts a route to a single role (or admin).
    Usage:
        @auth_bp.route('/admin/something')
        @login_required
        @require_role('admin')
        def admin_page(): ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            # Admins always pass
            if current_user.role == 'admin':
                return func(*args, **kwargs)
            # Otherwise, the user's role must match exactly
            if current_user.role != role:
                flash('You do not have permission to access that page.', 'error')
                return redirect(url_for('auth.login'))
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ======================================================================
# Helper — write data/active_user.json so the background agent knows
# who is logged in.
# ======================================================================
def _write_active_user(user=None):
    """Write current provider info (or null) to data/active_user.json."""
    path = os.path.join(current_app.root_path, 'data', 'active_user.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if user:
        payload = {
            'user_id': user.id,
            'username': user.username,
            'logged_in_at': datetime.now(timezone.utc).isoformat(),
        }
    else:
        payload = {'user_id': None}
    with open(path, 'w') as f:
        json.dump(payload, f)


# ======================================================================
# LOGIN
# ======================================================================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Show login form and authenticate the user."""
    # Already logged in → go to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard_redirect'))

    # First run — no users yet, send straight to registration
    if User.query.first() is None:
        return redirect(url_for('auth.register'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if not user.is_active_account:
                flash(
                    'Your account is pending admin approval or has been '
                    'deactivated. Contact your administrator.',
                    'warning'
                )
                return render_template('login.html')

            login_user(user, remember=True)
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            _write_active_user(user)

            next_page = request.args.get('next')
            return redirect(next_page or url_for('auth.dashboard_redirect'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


# Tiny redirect helper — avoids hard-coding '/dashboard' everywhere
@auth_bp.route('/')
def dashboard_redirect():
    if current_user.is_authenticated:
        return redirect('/dashboard')
    return redirect(url_for('auth.login'))


# ======================================================================
# LOGOUT
# ======================================================================
@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user and clear the active-user file."""
    _write_active_user(None)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ======================================================================
# REGISTER
# ======================================================================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Create a new account.
    - The very first user is automatically an admin.
    - After that, only an admin can register new users.
    """
    first_user = User.query.first() is None

    # True when an admin is currently logged in and creating an account
    # for someone else.  Self-registrations (no admin session) are allowed
    # but the new account starts inactive (pending approval).
    admin_creating = (
        not first_user
        and current_user.is_authenticated
        and current_user.role == 'admin'
    )

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        display_name = request.form.get('display_name', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        # Only admins can pick a role; self-registrations are always 'provider'
        role = request.form.get('role', 'provider') if admin_creating else 'provider'
        pin = request.form.get('pin', '').strip()

        # ---- Validation -------------------------------------------------
        errors = []
        if not username:
            errors.append('Username is required.')
        if User.query.filter_by(username=username).first():
            errors.append('That username is already taken.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if role not in ('provider', 'ma', 'admin'):
            errors.append('Invalid role selected.')
        if pin and (len(pin) != 4 or not pin.isdigit()):
            errors.append('PIN must be exactly 4 digits.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('register.html',
                                   first_user=first_user,
                                   form=request.form)

        # ---- Create user -------------------------------------------------
        # Admins creating accounts → active immediately.
        # Self-registrations → inactive until admin approves.
        user = User(
            username=username,
            display_name=display_name or username,
            role='admin' if first_user else role,
            is_active_account=True if (first_user or admin_creating) else False,
            email=request.form.get('email', '').strip(),
        )
        user.set_password(password)
        if pin:
            user.set_pin(pin)

        # Default notification preferences
        user.preferences = {
            'theme': 'light',
            'pushover_enabled': False,
            'inbox_check_interval': 120,
            'quiet_hours_start': 22,
            'quiet_hours_end': 7,
            'weekend_alerts': False,
            'notify_new_labs': True,
            'notify_new_radiology': True,
            'notify_new_messages': True,
            'notify_eod_reminder': True,
            'notify_morning_briefing': True,
        }

        db.session.add(user)
        db.session.commit()

        if first_user:
            flash(f'Admin account created. Welcome, {user.display_name}!', 'success')
            login_user(user, remember=True)
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            _write_active_user(user)
            return redirect('/dashboard')
        elif admin_creating:
            flash(f'Account created for {user.display_name}.', 'success')
            return redirect(url_for('auth.admin_users'))
        else:
            flash(
                'Account request submitted! An admin will review and approve '
                'it. You will be able to log in once approved.',
                'success'
            )
            return redirect(url_for('auth.login'))

    return render_template('register.html',
                           first_user=first_user,
                           admin_creating=admin_creating,
                           form=request.form if request.method == 'POST' else {})


# ======================================================================
# ACCOUNT SETTINGS — password, display name, PIN
# ======================================================================
@auth_bp.route('/settings/account', methods=['GET', 'POST'])
@login_required
def settings_account():
    """Change display name, password, or PIN."""
    if request.method == 'POST':
        action = request.form.get('action', '')

        # ---- Update display name -----------------------------------------
        if action == 'update_profile':
            new_name = request.form.get('display_name', '').strip()
            new_email = request.form.get('email', '').strip()
            if new_name:
                current_user.display_name = new_name
                current_user.email = new_email
                db.session.commit()
                flash('Profile updated.', 'success')
            else:
                flash('Display name cannot be empty.', 'error')

        # ---- Change password ---------------------------------------------
        elif action == 'change_password':
            current_pw = request.form.get('current_password', '')
            new_pw = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_password', '')

            if not current_user.check_password(current_pw):
                flash('Current password is incorrect.', 'error')
            elif len(new_pw) < 8:
                flash('New password must be at least 8 characters.', 'error')
            elif new_pw != confirm_pw:
                flash('New passwords do not match.', 'error')
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                flash('Password changed successfully.', 'success')

        # ---- Set or change PIN -------------------------------------------
        elif action == 'set_pin':
            pin = request.form.get('pin', '').strip()
            if len(pin) != 4 or not pin.isdigit():
                flash('PIN must be exactly 4 digits.', 'error')
            else:
                current_user.set_pin(pin)
                db.session.commit()
                flash('PIN updated.', 'success')

        # ---- Set NetPractice credentials ---------------------------------
        elif action == 'set_np_credentials':
            np_user = request.form.get('np_username', '').strip()
            np_pass = request.form.get('np_password', '')
            np_prov = request.form.get('np_provider_name', '').strip()

            # Only update password if a new one was typed
            if np_pass:
                current_user.set_np_credentials(np_user, np_pass)
            elif np_user:
                # Update username only, keep existing password
                current_user.set_np_credentials(
                    np_user, current_user.get_np_password()
                )

            current_user.np_provider_name = np_prov
            db.session.commit()
            flash('NetPractice credentials saved.', 'success')

        # ---- Set Amazing Charts credentials ------------------------------
        elif action == 'set_ac_credentials':
            ac_user = request.form.get('ac_username', '').strip()
            ac_pass = request.form.get('ac_password', '')

            if ac_pass:
                current_user.set_ac_credentials(ac_user, ac_pass)
            elif ac_user:
                current_user.set_ac_credentials(ac_user, current_user.get_ac_password())

            db.session.commit()
            flash('Amazing Charts credentials saved.', 'success')

        # ---- Set work PC password ----------------------------------------
        elif action == 'set_pc_password':
            pc_pass = request.form.get('pc_password', '')
            if pc_pass:
                current_user.set_pc_password(pc_pass)
                db.session.commit()
                flash('Work PC password saved.', 'success')

        # ---- Set XML export folder path ----------------------------------
        elif action == 'set_export_folder':
            folder = request.form.get('xml_export_folder', '').strip()
            current_user.set_pref('xml_export_folder', folder)
            db.session.commit()
            flash('Export folder updated.', 'success')

        # ---- Set AI assistant config -------------------------------------
        elif action == 'set_ai_config':
            if not getattr(current_user, 'ai_enabled', False):
                flash('AI access is not enabled for your account.', 'error')
            else:
                provider = request.form.get('ai_provider', '').strip()
                api_key = request.form.get('ai_api_key', '').strip()

                if provider not in ('openai', 'anthropic', 'xai', ''):
                    flash('Invalid AI provider.', 'error')
                else:
                    current_user.ai_provider = provider
                    if api_key:
                        current_user.set_ai_api_key(api_key)
                    db.session.commit()
                    flash('AI assistant settings saved.', 'success')

        # ---- Set clinical intelligence preferences ----------------------
        elif action == 'set_intelligence_prefs':
            current_user.set_pref('intel_drug_safety', 'intel_drug_safety' in request.form)
            current_user.set_pref('intel_guidelines', 'intel_guidelines' in request.form)
            current_user.set_pref('intel_formulary_gaps', 'intel_formulary_gaps' in request.form)
            current_user.set_pref('intel_education', 'intel_education' in request.form)
            try:
                current_user.set_pref('guideline_publication_years', int(request.form.get('guideline_years', 3)))
            except (ValueError, TypeError):
                pass
            current_user.set_pref('medlineplus_language', request.form.get('medlineplus_language', 'en'))
            current_user.set_pref('care_gap_grade_threshold', request.form.get('care_gap_grade', 'A+B'))
            db.session.commit()
            flash('Intelligence preferences saved.', 'success')

        # ---- Set billing preferences ------------------------------------
        elif action == 'set_billing_prefs':
            current_user.set_pref('revenue_display_mode', request.form.get('revenue_display', 'dollars'))
            current_user.set_pref('opportunity_min_confidence', request.form.get('min_confidence', 'MEDIUM'))
            current_user.set_pref('billing_insurer_default', request.form.get('insurer_default', 'unknown'))
            current_user.set_pref('show_billing_widget', 'show_billing_widget' in request.form)
            current_user.set_pref('show_scheduling_opps', 'show_scheduling_opps' in request.form)
            db.session.commit()
            flash('Billing preferences saved.', 'success')

        # ---- Set preferred browser --------------------------------------
        elif action == 'set_preferred_browser':
            browser = request.form.get('preferred_browser', 'chrome').strip()
            if browser not in ('chrome', 'edge', 'firefox'):
                browser = 'chrome'
            current_user.set_pref('preferred_browser', browser)
            db.session.commit()
            flash('Browser preference saved.', 'success')

        # ---- Set email address ------------------------------------------
        elif action == 'set_email':
            email = request.form.get('email', '').strip()
            current_user.email = email
            db.session.commit()
            flash('Email address saved.', 'success')

        return redirect(url_for('auth.settings_account'))

    return render_template('settings.html')


# ======================================================================
# NOTIFICATION PREFERENCES
# ======================================================================
@auth_bp.route('/settings/notifications', methods=['GET', 'POST'])
@login_required
def settings_notifications():
    """Per-user notification preferences stored in the JSON column."""
    if request.method == 'POST':
        prefs = current_user.preferences

        prefs['pushover_enabled'] = 'pushover_enabled' in request.form
        prefs['inbox_check_interval'] = int(
            request.form.get('inbox_check_interval', 120)
        )
        # Quiet hours come from a time input ("HH:MM").
        # Support plain integers too, in case of legacy stored values.
        qs = request.form.get('quiet_hours_start', '22:00')
        prefs['quiet_hours_start'] = int(qs.split(':')[0]) if ':' in qs else int(qs or 22)
        qe = request.form.get('quiet_hours_end', '07:00')
        prefs['quiet_hours_end'] = int(qe.split(':')[0]) if ':' in qe else int(qe or 7)
        prefs['weekend_alerts'] = 'weekend_alerts' in request.form

        # Notification type checkboxes
        prefs['notify_new_labs'] = 'notify_new_labs' in request.form
        prefs['notify_new_radiology'] = 'notify_new_radiology' in request.form
        prefs['notify_new_messages'] = 'notify_new_messages' in request.form
        prefs['notify_eod_reminder'] = 'notify_eod_reminder' in request.form
        prefs['notify_morning_briefing'] = 'notify_morning_briefing' in request.form

        # Critical value alerts — always on, cannot be disabled
        prefs['notify_critical_values'] = True

        current_user.preferences = prefs
        db.session.commit()
        flash('Notification preferences saved.', 'success')
        return redirect(url_for('auth.settings_account'))

    # GET requests redirect to the unified settings page
    return redirect(url_for('auth.settings_account'))


# ======================================================================
# PREFERENCE API (JSON) — used by metrics benchmark toggle, etc.
# ======================================================================
@auth_bp.route('/settings/account/preference', methods=['POST'])
@login_required
def save_preference():
    """Save a single preference key/value via JSON POST."""
    data = request.get_json(silent=True) or {}
    key = data.get('key', '')
    value = data.get('value')
    if not key or not isinstance(key, str) or len(key) > 64:
        return jsonify({'error': 'Invalid key'}), 400
    current_user.set_pref(key, value)
    db.session.commit()
    return jsonify({'ok': True})


# ======================================================================
# ADMIN — User management
# ======================================================================
@auth_bp.route('/admin/users')
@login_required
@require_role('admin')
def admin_users():
    """List all users. Admin only."""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)


@auth_bp.route('/admin/users/<int:user_id>/role', methods=['POST'])
@login_required
@require_role('admin')
def admin_change_role(user_id):
    """Change a user's role."""
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.admin_users'))

    new_role = request.form.get('role', '')
    if new_role not in ('provider', 'ma', 'admin'):
        flash('Invalid role.', 'error')
        return redirect(url_for('auth.admin_users'))

    # Prevent removing the last admin
    if user.role == 'admin' and new_role != 'admin':
        admin_count = User.query.filter_by(role='admin').count()
        if admin_count <= 1:
            flash('Cannot remove the only admin account.', 'error')
            return redirect(url_for('auth.admin_users'))

    user.role = new_role
    db.session.commit()
    flash(f'{user.display_name} is now {new_role}.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@require_role('admin')
def admin_reset_password(user_id):
    """Reset a user's password to a temporary value."""
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.admin_users'))

    temp_pw = request.form.get('new_password', '')
    if len(temp_pw) < 8:
        flash('Temporary password must be at least 8 characters.', 'error')
        return redirect(url_for('auth.admin_users'))

    user.set_password(temp_pw)
    db.session.commit()
    flash(f'Password reset for {user.display_name}.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/admin/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@require_role('admin')
def admin_toggle_active(user_id):
    """Activate or deactivate a user account (immediate or scheduled)."""
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.admin_users'))

    # Don't let admins lock themselves out
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('auth.admin_users'))

    deactivate_mode = request.form.get('deactivate_mode', 'now')
    schedule_date = request.form.get('schedule_date', '').strip()

    if user.is_active_account:
        if deactivate_mode == 'scheduled' and schedule_date:
            try:
                dt = datetime.strptime(schedule_date, '%Y-%m-%d')
                user.deactivate_at = dt.replace(tzinfo=timezone.utc)
                db.session.commit()
                flash(f'{user.display_name} scheduled for deactivation on {schedule_date}.', 'success')
            except ValueError:
                flash('Invalid date format.', 'error')
        else:
            user.is_active_account = False
            user.deactivate_at = None
            db.session.commit()
            flash(f'{user.display_name} has been deactivated.', 'success')
    else:
        user.is_active_account = True
        user.deactivate_at = None
        db.session.commit()
        flash(f'{user.display_name} has been activated.', 'success')

    return redirect(url_for('auth.admin_users'))


# ======================================================================
# ADMIN — Approve pending user account
# ======================================================================
@auth_bp.route('/admin/users/<int:user_id>/approve', methods=['POST'])
@login_required
@require_role('admin')
def admin_approve_user(user_id):
    """Activate a pending (or deactivated) account."""
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.admin_users'))
    user.is_active_account = True
    db.session.commit()
    flash(f'{user.display_name}\'s account has been approved and is now active.', 'success')
    return redirect(url_for('auth.admin_users'))


# ======================================================================
# ADMIN — Change a user's username
# ======================================================================
@auth_bp.route('/admin/users/<int:user_id>/change-username', methods=['POST'])
@login_required
@require_role('admin')
def admin_change_username(user_id):
    """Admin can update a user's login username."""
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.admin_users'))
    new_username = request.form.get('new_username', '').strip()
    if not new_username:
        flash('Username cannot be empty.', 'error')
        return redirect(url_for('auth.admin_users'))
    if User.query.filter_by(username=new_username).first():
        flash('That username is already taken.', 'error')
        return redirect(url_for('auth.admin_users'))
    old = user.username
    user.username = new_username
    db.session.commit()
    flash(f'Username changed from \'{old}\' to \'{new_username}\'.', 'success')
    return redirect(url_for('auth.admin_users'))


# ======================================================================
# ADMIN — Set a user's 4-digit PIN
# ======================================================================
@auth_bp.route('/admin/users/<int:user_id>/set-pin', methods=['POST'])
@login_required
@require_role('admin')
def admin_set_pin(user_id):
    """Admin can set or reset any user's auto-lock PIN."""
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.admin_users'))
    new_pin = request.form.get('new_pin', '').strip()
    if len(new_pin) != 4 or not new_pin.isdigit():
        flash('PIN must be exactly 4 digits (numbers only).', 'error')
        return redirect(url_for('auth.admin_users'))
    user.set_pin(new_pin)
    db.session.commit()
    flash(f'PIN updated for {user.display_name}.', 'success')
    return redirect(url_for('auth.admin_users'))


# ======================================================================
# ADMIN — Toggle AI access for a user
# ======================================================================
@auth_bp.route('/admin/users/<int:user_id>/toggle-ai', methods=['POST'])
@login_required
@require_role('admin')
def admin_toggle_ai(user_id):
    """Admin can enable or disable AI assistant access for any user."""
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.admin_users'))
    user.ai_enabled = not user.ai_enabled
    db.session.commit()
    status = 'enabled' if user.ai_enabled else 'disabled'
    flash(f'AI access {status} for {user.display_name}.', 'success')
    return redirect(url_for('auth.admin_users'))


# ======================================================================
# API — PIN verification (for auto-lock overlay in main.js)
# ======================================================================
@auth_bp.route('/api/verify-pin', methods=['POST'])
@login_required
def api_verify_pin():
    """Check the 4-digit PIN without exposing the hash."""
    data = request.get_json(silent=True) or {}
    pin = data.get('pin', '')
    if current_user.check_pin(pin):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Incorrect PIN'}), 401


# ======================================================================
# API — Theme preference (theme/font/accent from settings + dark toggle)
# ======================================================================
VALID_THEMES = {'light', 'dark', 'modern', 'fancy', 'retro', 'minimalist',
                'nature', 'ocean', 'sunset', 'nord'}
VALID_FONTS  = {'system', 'inter', 'roboto', 'poppins', 'source-code',
                'merriweather', 'comic'}
VALID_ACCENTS = {'', 'blue', 'teal', 'purple', 'rose', 'amber', 'emerald'}

@auth_bp.route('/api/settings/theme', methods=['POST'])
@login_required
def api_set_theme():
    """Save theme, font, and accent colour preferences."""
    data = request.get_json(silent=True) or {}

    theme = data.get('theme', 'light')
    if theme not in VALID_THEMES:
        theme = 'light'
    current_user.set_pref('theme', theme)

    font = data.get('font')
    if font is not None:
        if font not in VALID_FONTS:
            font = 'system'
        current_user.set_pref('theme_font', font)

    accent = data.get('accent')
    if accent is not None:
        if accent not in VALID_ACCENTS:
            accent = ''
        current_user.set_pref('theme_accent', accent)

    db.session.commit()
    return jsonify({'success': True, 'theme': theme,
                    'font': current_user.get_pref('theme_font', 'system'),
                    'accent': current_user.get_pref('theme_accent', '')})


# ======================================================================
# API — Notifications (polled by the bell in base.html)
# ======================================================================
@auth_bp.route('/api/notifications')
@login_required
def api_notifications():
    """Returns unread notification count and list from in-app notifications + system sources."""
    from models.notification import Notification

    # In-app notifications
    notifs = (
        Notification.query
        .filter_by(user_id=current_user.id, is_read=False)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )

    unread_count = len(notifs)
    items = []
    for n in notifs:
        sender_name = ''
        if n.sender:
            sender_name = n.sender.display_name or n.sender.username
        items.append({
            'id': n.id,
            'message': n.message,
            'time': n.created_at.strftime('%m/%d %I:%M %p') if n.created_at else '',
            'sender': sender_name,
        })

    return jsonify({
        'unread_count': unread_count,
        'notifications': items,
    })


# ======================================================================
# API — Mark notification as read
# ======================================================================
@auth_bp.route('/api/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def api_mark_notification_read(notif_id):
    from models.notification import Notification
    n = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first()
    if n:
        n.is_read = True
        db.session.commit()
    return jsonify({'ok': True})


# ======================================================================
# API — Mark all notifications as read
# ======================================================================
@auth_bp.route('/api/notifications/read-all', methods=['POST'])
@login_required
def api_mark_all_read():
    from models.notification import Notification
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'ok': True})


# ======================================================================
# ADMIN — Send notification to a user
# ======================================================================
@auth_bp.route('/admin/send-notification', methods=['POST'])
@login_required
@require_role('admin')
def admin_send_notification():
    """Admin sends an in-app notification to specific user(s) or all."""
    from models.notification import Notification, NOTIFICATION_TEMPLATES
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    message = (data.get('message') or '').strip()
    send_to_all = data.get('send_to_all', False)
    template_name = (data.get('template_name') or '').strip()
    scheduled_for_str = (data.get('scheduled_for') or '').strip()

    if not message:
        return jsonify({'success': False, 'error': 'Message is required.'}), 400
    if not send_to_all and not user_id:
        return jsonify({'success': False, 'error': 'Select a user or Send to All.'}), 400

    # Parse scheduled datetime
    scheduled_dt = None
    if scheduled_for_str:
        try:
            scheduled_dt = datetime.strptime(scheduled_for_str, '%Y-%m-%dT%H:%M')
            scheduled_dt = scheduled_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format.'}), 400

    # Build recipient list
    if send_to_all:
        recipients = User.query.filter(User.is_active_account.is_(True)).all()
    else:
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Invalid user ID.'}), 400
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found.'}), 404
        recipients = [user]

    count = 0
    for recipient in recipients:
        notif = Notification(
            user_id=recipient.id,
            sender_id=current_user.id,
            message=message,
            template_name=template_name,
            scheduled_for=scheduled_dt,
        )
        db.session.add(notif)
        count += 1
    db.session.commit()
    label = f'{count} user(s)' if send_to_all else recipients[0].display_name
    return jsonify({'success': True, 'message': f'Notification sent to {label}.'})


# ======================================================================
# API — Notification history (for admin modal)
# ======================================================================
@auth_bp.route('/api/admin/notification-history')
@login_required
@require_role('admin')
def notification_history():
    """Return recent notification history for the admin panel."""
    from models.notification import Notification
    recent = (
        Notification.query
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify([{
        'id': n.id,
        'to': n.user.display_name if n.user else 'Unknown',
        'from': n.sender.display_name if n.sender else 'System',
        'message': n.message[:120],
        'template': n.template_name or '',
        'is_read': n.is_read,
        'scheduled_for': n.scheduled_for.strftime('%m/%d/%Y %I:%M %p') if n.scheduled_for else '',
        'created_at': n.created_at.strftime('%m/%d/%Y %I:%M %p') if n.created_at else '',
    } for n in recent])


# ======================================================================
# API — Open URL in preferred browser (called from JS)
# ======================================================================
@auth_bp.route('/api/open-url', methods=['POST'])
@login_required
def api_open_url():
    """Open a URL in the user's preferred browser."""
    data = request.get_json(silent=True) or {}
    url = (data.get('url') or '').strip()
    if not url or not (url.startswith('http://') or url.startswith('https://')):
        return jsonify({'error': 'Invalid URL'}), 400

    browser = current_user.get_pref('preferred_browser', 'chrome')
    browser_paths = {
        'chrome': [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        ],
        'edge': [
            r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
            r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
        ],
        'firefox': [
            r'C:\Program Files\Mozilla Firefox\firefox.exe',
            r'C:\Program Files (x86)\Mozilla Firefox\firefox.exe',
        ],
    }

    paths = browser_paths.get(browser, browser_paths['chrome'])
    opened = False
    for p in paths:
        if os.path.exists(p):
            try:
                subprocess.Popen([p, url])
                opened = True
                break
            except OSError:
                continue

    if not opened:
        # Fallback to system default
        webbrowser.open(url)

    return jsonify({'ok': True})


# ======================================================================
# SETUP — onboarding wizard for new users
# ======================================================================
@auth_bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup_page():
    """
    Shows role-based setup tasks and handles form submissions for
    NP credentials, AC credentials, and PC password from this page.
    """
    if request.method == 'POST':
        action = request.form.get('action', '')

        if action == 'set_np_credentials':
            np_user = request.form.get('np_username', '').strip()
            np_pass = request.form.get('np_password', '')
            np_prov = request.form.get('np_provider_name', '').strip()

            if np_pass:
                current_user.set_np_credentials(np_user, np_pass)
            elif np_user:
                current_user.set_np_credentials(np_user, current_user.get_np_password())

            current_user.np_provider_name = np_prov
            db.session.commit()
            flash('NetPractice credentials saved.', 'success')

        elif action == 'set_ac_credentials':
            ac_user = request.form.get('ac_username', '').strip()
            ac_pass = request.form.get('ac_password', '')

            if ac_pass:
                current_user.set_ac_credentials(ac_user, ac_pass)
            elif ac_user:
                current_user.set_ac_credentials(ac_user, current_user.get_ac_password())

            db.session.commit()
            flash('Amazing Charts credentials saved.', 'success')

        elif action == 'set_pc_password':
            pc_pass = request.form.get('pc_password', '')
            if pc_pass:
                current_user.set_pc_password(pc_pass)
                db.session.commit()
                flash('Work PC password saved.', 'success')

        # Check if setup is now complete
        if current_user.is_setup_complete() and not current_user.setup_completed_at:
            current_user.setup_completed_at = datetime.now(timezone.utc)
            db.session.commit()

        return redirect(url_for('auth.setup_page'))

    # Build template context
    tasks = current_user.get_setup_tasks()
    incomplete_count = sum(1 for t in tasks if not t['complete'])
    all_complete = incomplete_count == 0

    # Determine which forms to show (only show forms for incomplete tasks)
    task_ids = {t['id']: t['complete'] for t in tasks}

    return render_template(
        'setup.html',
        tasks=tasks,
        incomplete_count=incomplete_count,
        all_complete=all_complete,
        show_np_form=not task_ids.get('np_credentials', True),
        show_nav_steps_link=not task_ids.get('np_nav_steps', True),
        show_ac_form=not task_ids.get('ac_credentials', True),
        show_pc_form=current_user.role in ('provider', 'admin'),
    )


# ======================================================================
# API — Setup status (polled by the setup button in header)
# ======================================================================
@auth_bp.route('/api/setup-status')
@login_required
def api_setup_status():
    """Return how many setup tasks remain for the current user."""
    count = current_user.setup_incomplete_count()
    return jsonify({
        'incomplete_count': count,
        'is_complete': count == 0,
    })


# ======================================================================
# ADMIN — Audit Log viewer
# ======================================================================
@auth_bp.route('/admin/audit-log')
@login_required
@require_role('admin')
def admin_audit_log():
    """
    Show the last 500 audit log entries with optional filters
    for user, date range, and module.
    """
    from models.audit import AuditLog

    query = AuditLog.query

    # ---- Filter by user --------------------------------------------------
    filter_user = request.args.get('user_id', '', type=str)
    if filter_user.isdigit():
        query = query.filter_by(user_id=int(filter_user))

    # ---- Filter by module ------------------------------------------------
    filter_module = request.args.get('module', '').strip()
    if filter_module:
        query = query.filter_by(module=filter_module)

    # ---- Filter by date range --------------------------------------------
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    if date_from:
        try:
            from datetime import datetime
            start = datetime.fromisoformat(date_from)
            query = query.filter(AuditLog.timestamp >= start)
        except ValueError:
            pass
    if date_to:
        try:
            from datetime import datetime, timedelta
            end = datetime.fromisoformat(date_to) + timedelta(days=1)
            query = query.filter(AuditLog.timestamp < end)
        except ValueError:
            pass

    # Order by most recent, cap at 500
    entries = query.order_by(AuditLog.timestamp.desc()).limit(500).all()

    # Provide the list of users and known modules for the filter dropdowns
    users = User.query.order_by(User.display_name).all()
    modules = (
        db.session.query(AuditLog.module)
        .filter(AuditLog.module != '')
        .distinct()
        .order_by(AuditLog.module)
        .all()
    )
    module_list = [m[0] for m in modules]

    return render_template(
        'admin_audit_log.html',
        entries=entries,
        users=users,
        module_list=module_list,
        filter_user=filter_user,
        filter_module=filter_module,
        date_from=date_from,
        date_to=date_to,
    )

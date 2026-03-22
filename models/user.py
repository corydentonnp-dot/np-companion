"""
CareCompanion — User Model

File location: carecompanion/models/user.py

Defines the User table: accounts, roles, PIN hashes, and a JSON
column for per-user preferences (dark mode, notification settings, etc.).

Password and PIN hashes are generated with Flask-Bcrypt — plain text
is never stored.
"""

import base64
import json
from datetime import datetime, timezone

from cryptography.fernet import Fernet, InvalidToken
from flask_login import UserMixin
from models import db


def _get_fernet():
    """
    Build a Fernet cipher from the app's SECRET_KEY.
    Fernet needs a 32-byte URL-safe base64-encoded key.
    We hash the SECRET_KEY with SHA-256 then base64 it.
    """
    import hashlib
    from flask import current_app
    secret = current_app.config.get('SECRET_KEY', 'fallback-key')
    key_bytes = hashlib.sha256(secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))


class User(UserMixin, db.Model):
    """
    One row per provider / MA / admin who uses CareCompanion.
    Flask-Login's UserMixin supplies is_authenticated, is_active, etc.
    """
    __tablename__ = 'users'

    # ---- Primary key -----------------------------------------------------
    id = db.Column(db.Integer, primary_key=True)

    # ---- Credentials -----------------------------------------------------
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # ---- Profile ---------------------------------------------------------
    display_name = db.Column(db.String(120), default='')
    role = db.Column(db.String(20), nullable=False, default='provider')
    # Valid roles: 'provider', 'ma', 'admin'

    # ---- Auto-lock PIN (4 digits, bcrypt-hashed) -------------------------
    pin_hash = db.Column(db.String(128), default='')

    # ---- Preferences (stored as JSON text) --------------------------------
    # Example contents:
    # {
    #     "theme": "dark",
    #     "pushover_enabled": true,
    #     "inbox_check_interval": 120,
    #     "quiet_hours_start": 22,
    #     "quiet_hours_end": 7,
    #     "weekend_alerts": false,
    #     "notify_new_labs": true,
    #     "notify_new_radiology": true,
    #     "notify_new_messages": true,
    #     "notify_eod_reminder": true,
    #     "notify_morning_briefing": true
    # }
    _preferences = db.Column('preferences', db.Text, default='{}')

    # ---- NetPractice credentials (encrypted at rest) --------------------
    # These are encrypted with Fernet using the app's SECRET_KEY.
    # Only decrypted when the scraper needs to log in.
    np_username_enc = db.Column(db.Text, default='')      # Fernet-encrypted
    np_password_enc = db.Column(db.Text, default='')      # Fernet-encrypted
    np_totp_secret_enc = db.Column(db.Text, default='')   # Fernet-encrypted TOTP secret for MFA
    np_provider_name = db.Column(db.String(200), default='')  # e.g. "ASHLEY MORSBERGER FNP (45)"

    # ---- Navigation steps (JSON) — recorded path to schedule page --------
    # Stores a list of step dicts recorded by the setup wizard.
    _nav_steps = db.Column('nav_steps', db.Text, default='[]')

    # ---- Amazing Charts credentials (encrypted at rest) ------------------
    ac_username_enc = db.Column(db.Text, default='')      # Fernet-encrypted
    ac_password_enc = db.Column(db.Text, default='')      # Fernet-encrypted

    # ---- Work PC password (encrypted, optional) --------------------------
    pc_password_enc = db.Column(db.Text, default='')      # Fernet-encrypted

    # ---- AI Assistant ----------------------------------------------------
    ai_api_key_enc = db.Column(db.Text, default='')       # Fernet-encrypted
    ai_provider = db.Column(db.String(30), default='')    # 'openai', 'anthropic', 'xai'
    ai_enabled = db.Column(db.Boolean, default=False)
    ai_hipaa_acknowledged = db.Column(db.Boolean, default=False)

    # ---- Email (for self-service password/PIN reset) ---------------------
    email = db.Column(db.String(200), default='')

    # ---- Scheduled deactivation ------------------------------------------
    deactivate_at = db.Column(db.DateTime, nullable=True)

    # ---- Setup tracking --------------------------------------------------
    setup_completed_at = db.Column(db.DateTime, nullable=True)

    # ---- Timestamps ------------------------------------------------------
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    last_login = db.Column(db.DateTime, nullable=True)

    # ---- Account status --------------------------------------------------
    is_active_account = db.Column(db.Boolean, default=True)

    # ------------------------------------------------------------------
    # Password helpers (use bcrypt imported from the app module)
    # ------------------------------------------------------------------
    def set_password(self, plain_password):
        """Hash and store a new password."""
        from app import bcrypt
        self.password_hash = bcrypt.generate_password_hash(
            plain_password
        ).decode('utf-8')

    def check_password(self, plain_password):
        """Return True if the plain-text password matches the hash."""
        from app import bcrypt
        return bcrypt.check_password_hash(self.password_hash, plain_password)

    # ------------------------------------------------------------------
    # PIN helpers
    # ------------------------------------------------------------------
    def set_pin(self, plain_pin):
        """Hash and store a 4-digit PIN for the auto-lock screen."""
        from app import bcrypt
        self.pin_hash = bcrypt.generate_password_hash(
            plain_pin
        ).decode('utf-8')

    def check_pin(self, plain_pin):
        """Return True if the plain-text PIN matches the hash."""
        from app import bcrypt
        if not self.pin_hash:
            return False
        return bcrypt.check_password_hash(self.pin_hash, plain_pin)

    # ------------------------------------------------------------------
    # Preferences (JSON) helpers
    # ------------------------------------------------------------------
    @property
    def preferences(self):
        """Return preferences as a Python dict."""
        try:
            return json.loads(self._preferences or '{}')
        except (json.JSONDecodeError, TypeError):
            return {}

    @preferences.setter
    def preferences(self, value):
        """Accept a dict and store it as JSON text."""
        self._preferences = json.dumps(value)

    def get_pref(self, key, default=None):
        """Read a single preference value with a fallback default."""
        return self.preferences.get(key, default)

    def set_pref(self, key, value):
        """Update one preference key without touching the others."""
        prefs = self.preferences
        prefs[key] = value
        self.preferences = prefs

    # ------------------------------------------------------------------
    # Flask-Login override: respect deactivated accounts
    # ------------------------------------------------------------------
    @property
    def is_active(self):
        return self.is_active_account

    # ------------------------------------------------------------------
    # NetPractice credential helpers (encrypt / decrypt)
    # ------------------------------------------------------------------
    def set_np_credentials(self, username, password):
        """Encrypt and store NetPractice login credentials."""
        f = _get_fernet()
        self.np_username_enc = f.encrypt(username.encode()).decode() if username else ''
        self.np_password_enc = f.encrypt(password.encode()).decode() if password else ''

    def get_np_username(self):
        """Decrypt and return the stored NetPractice username."""
        if not self.np_username_enc:
            return ''
        try:
            f = _get_fernet()
            return f.decrypt(self.np_username_enc.encode()).decode()
        except (InvalidToken, Exception):
            return ''

    def get_np_password(self):
        """Decrypt and return the stored NetPractice password."""
        if not self.np_password_enc:
            return ''
        try:
            f = _get_fernet()
            return f.decrypt(self.np_password_enc.encode()).decode()
        except (InvalidToken, Exception):
            return ''

    def has_np_credentials(self):
        """Return True if both NP username and password are stored."""
        return bool(self.np_username_enc and self.np_password_enc)

    # ------------------------------------------------------------------
    # NetPractice TOTP secret helpers (encrypt / decrypt)
    # ------------------------------------------------------------------
    def set_np_totp_secret(self, secret):
        """Encrypt and store the TOTP secret for NetPractice MFA."""
        f = _get_fernet()
        self.np_totp_secret_enc = f.encrypt(secret.encode()).decode() if secret else ''

    def get_np_totp_secret(self):
        """Decrypt and return the stored TOTP secret."""
        if not self.np_totp_secret_enc:
            return ''
        try:
            f = _get_fernet()
            return f.decrypt(self.np_totp_secret_enc.encode()).decode()
        except (InvalidToken, Exception):
            return ''

    def has_np_totp_secret(self):
        """Return True if a TOTP secret is stored."""
        return bool(self.np_totp_secret_enc)

    # ------------------------------------------------------------------
    # Navigation steps helpers (JSON)
    # ------------------------------------------------------------------
    @property
    def nav_steps(self):
        """Return navigation steps as a Python list."""
        try:
            return json.loads(self._nav_steps or '[]')
        except (json.JSONDecodeError, TypeError):
            return []

    @nav_steps.setter
    def nav_steps(self, value):
        """Accept a list and store it as JSON text."""
        self._nav_steps = json.dumps(value)

    # ------------------------------------------------------------------
    # Amazing Charts credential helpers (encrypt / decrypt)
    # ------------------------------------------------------------------
    def set_ac_credentials(self, username, password):
        """Encrypt and store Amazing Charts login credentials."""
        f = _get_fernet()
        self.ac_username_enc = f.encrypt(username.encode()).decode() if username else ''
        self.ac_password_enc = f.encrypt(password.encode()).decode() if password else ''

    def get_ac_username(self):
        """Decrypt and return the stored Amazing Charts username."""
        if not self.ac_username_enc:
            return ''
        try:
            f = _get_fernet()
            return f.decrypt(self.ac_username_enc.encode()).decode()
        except (InvalidToken, Exception):
            return ''

    def get_ac_password(self):
        """Decrypt and return the stored Amazing Charts password."""
        if not self.ac_password_enc:
            return ''
        try:
            f = _get_fernet()
            return f.decrypt(self.ac_password_enc.encode()).decode()
        except (InvalidToken, Exception):
            return ''

    def has_ac_credentials(self):
        """Return True if both AC username and password are stored."""
        return bool(self.ac_username_enc and self.ac_password_enc)

    # ------------------------------------------------------------------
    # Work PC password helpers (encrypt / decrypt)
    # ------------------------------------------------------------------
    def set_pc_password(self, password):
        """Encrypt and store the work PC password."""
        f = _get_fernet()
        self.pc_password_enc = f.encrypt(password.encode()).decode() if password else ''

    def get_pc_password(self):
        """Decrypt and return the stored work PC password."""
        if not self.pc_password_enc:
            return ''
        try:
            f = _get_fernet()
            return f.decrypt(self.pc_password_enc.encode()).decode()
        except (InvalidToken, Exception):
            return ''

    def has_pc_password(self):
        """Return True if a work PC password is stored."""
        return bool(self.pc_password_enc)

    # ------------------------------------------------------------------
    # AI Assistant helpers (encrypt / decrypt API key)
    # ------------------------------------------------------------------
    def set_ai_api_key(self, key):
        """Encrypt and store the AI API key."""
        f = _get_fernet()
        self.ai_api_key_enc = f.encrypt(key.encode()).decode() if key else ''

    def get_ai_api_key(self):
        """Decrypt and return the stored AI API key."""
        if not self.ai_api_key_enc:
            return ''
        try:
            f = _get_fernet()
            return f.decrypt(self.ai_api_key_enc.encode()).decode()
        except (InvalidToken, Exception):
            return ''

    def has_ai_api_key(self):
        """Return True if an AI API key is stored."""
        return bool(self.ai_api_key_enc)

    def can_use_ai(self):
        """Return True if this user is allowed to use the AI assistant."""
        return bool(self.ai_enabled and self.ai_api_key_enc and self.ai_provider)

    # ------------------------------------------------------------------
    # Setup wizard: return list of incomplete tasks for this user's role
    # ------------------------------------------------------------------
    def get_setup_tasks(self):
        """
        Returns a list of setup task dicts based on the user's role.
        Each dict has: id, title, description, complete (bool), url
        """
        tasks = []

        if self.role in ('provider', 'admin'):
            # Task 1: Display name (must not be empty or same as username)
            tasks.append({
                'id': 'display_name',
                'title': 'Set Your Display Name',
                'description': 'Enter your full name as it appears in your systems.',
                'complete': bool(self.display_name and self.display_name != self.username),
                'url': '/settings/account',
            })
            # Task 2: NetPractice credentials + provider name
            tasks.append({
                'id': 'np_credentials',
                'title': 'NetPractice Login & Provider Name',
                'description': 'Enter your webPRACTICE credentials and the exact provider name shown on your schedule.',
                'complete': bool(self.has_np_credentials() and self.np_provider_name),
                'url': '/setup',
            })
            # Task 3: NetPractice navigation steps
            tasks.append({
                'id': 'np_nav_steps',
                'title': 'NetPractice Navigation Setup',
                'description': 'Record the clicks needed to reach your daily schedule in webPRACTICE.',
                'complete': bool(self.nav_steps and len(self.nav_steps) > 0),
                'url': '/admin/netpractice/wizard',
            })
            # Task 4: Amazing Charts credentials
            tasks.append({
                'id': 'ac_credentials',
                'title': 'Amazing Charts Login',
                'description': 'Enter your Amazing Charts username and password for automation.',
                'complete': self.has_ac_credentials(),
                'url': '/setup',
            })

        elif self.role == 'ma':
            # MAs just need their display name for now
            tasks.append({
                'id': 'display_name',
                'title': 'Set Your Display Name',
                'description': 'Enter your full name.',
                'complete': bool(self.display_name and self.display_name != self.username),
                'url': '/settings/account',
            })

        return tasks

    def setup_incomplete_count(self):
        """Return number of incomplete setup tasks."""
        return sum(1 for t in self.get_setup_tasks() if not t['complete'])

    def is_setup_complete(self):
        """Return True if all setup tasks are done."""
        return self.setup_incomplete_count() == 0

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

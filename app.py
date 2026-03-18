"""
NP Companion — Main Flask Application

File location: np-companion/app.py (project root)

This is the entry point for the NP Companion web server.  It creates
the Flask app, connects the database, sets up login handling, and
registers all the route blueprints (one per module).

Run with:  python app.py
"""

import os
import logging
import traceback
from flask import Flask, render_template, request
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from models import db
from utils.paths import is_frozen, get_resource_dir, get_data_dir, get_db_path


# ---------------------------------------------------------------------------
# Extensions — created here at module level, then bound to the app
# inside create_app().  Other files can import these directly:
#   from app import login_manager, bcrypt
# ---------------------------------------------------------------------------
login_manager = LoginManager()
bcrypt = Bcrypt()


# ---------------------------------------------------------------------------
# Role-based access — controls which sidebar items each role can see.
# '*' means "everything, including admin pages".
# ---------------------------------------------------------------------------
ROLE_PERMISSIONS = {
    'ma':       ['dashboard', 'orders', 'caregap', 'medref'],
    'provider': ['dashboard', 'orders', 'caregap', 'medref', 'timer',
                 'billing', 'inbox', 'oncall', 'labtrack', 'metrics',
                 'tools', 'reformatter', 'briefing'],
    'admin':    ['*'],
}


def create_app():
    """
    App factory — builds and returns a fully configured Flask app.
    Called once when the server starts.
    """
    # ---- Build Flask with correct paths for frozen or dev mode -----
    if is_frozen():
        res = get_resource_dir()
        app = Flask(
            __name__,
            template_folder=os.path.join(res, 'templates'),
            static_folder=os.path.join(res, 'static'),
        )
    else:
        app = Flask(__name__)

    # ---- Load settings from config.py ------------------------------------
    app.config.from_object('config')

    # ---- Database setup --------------------------------------------------
    db_path = get_db_path()

    # SQLite URI needs forward slashes, even on Windows
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path.replace('\\', '/')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Create the data/ and data/backups/ directories if needed
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    backup_path = os.path.join(get_data_dir(), 'backups')
    os.makedirs(backup_path, exist_ok=True)

    # ---- Initialize extensions -------------------------------------------
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Redirect unauthenticated visitors to the login page
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access NP Companion.'
    login_manager.login_message_category = 'info'

    # ---- User loader for Flask-Login ------------------------------------
    @login_manager.user_loader
    def load_user(user_id):
        """Flask-Login calls this on every request to reload the user."""
        try:
            from models.user import User
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    # ---- Register route blueprints ---------------------------------------
    _register_blueprints(app)

    # ---- Template helpers ------------------------------------------------
    @app.context_processor
    def inject_helpers():
        """Make utility functions available in every Jinja template."""
        def user_can_access(module):
            """Return True if the current user's role allows this module."""
            try:
                if not current_user.is_authenticated:
                    return False
                role = getattr(current_user, 'role', 'provider')
                if role == 'admin':
                    return True
                allowed = ROLE_PERMISSIONS.get(role, [])
                return module in allowed
            except Exception:
                return False
        def oncall_pending_count():
            try:
                if not current_user.is_authenticated:
                    return 0
                from models.oncall import OnCallNote
                return OnCallNote.query.filter_by(
                    user_id=current_user.id,
                    documentation_status='pending'
                ).count()
            except Exception:
                return 0
        return {'user_can_access': user_can_access, 'oncall_pending_count': oncall_pending_count, 'app_version': app.config.get('APP_VERSION', ''),
                'user_can_use_ai': lambda: current_user.is_authenticated and current_user.can_use_ai(),
                'user_ai_enabled': lambda: current_user.is_authenticated and getattr(current_user, 'ai_enabled', False)}

    # ---- Audit log — automatic after_request hook ------------------------
    @app.after_request
    def log_request(response):
        """Write every authenticated request to the audit_log table."""
        try:
            if current_user.is_authenticated:
                # Skip noisy polling endpoints to keep the log useful
                skip_paths = ('/api/notifications', '/api/agent-status', '/api/auth-status', '/api/setup-status', '/api/netpractice/', '/static/')
                if not any(request.path.startswith(p) for p in skip_paths):
                    # Determine which blueprint handled the request
                    module = ''
                    if request.blueprints:
                        module = request.blueprints[0]
                    from utils import log_access
                    log_access(
                        user_id=current_user.id,
                        action=f'{request.method} {request.path}',
                        module=module,
                        ip_address=request.remote_addr or '',
                    )
                    db.session.commit()
        except Exception:
            # Never let audit logging break the actual response
            db.session.rollback()
        return response

    # ---- File logging for errors -----------------------------------------
    if not app.debug:
        log_dir = os.path.join(app.root_path, 'data')
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(
            os.path.join(log_dir, 'error.log')
        )
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        app.logger.addHandler(file_handler)

    # ---- Error handlers --------------------------------------------------
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        tb = traceback.format_exc()
        app.logger.error('500 error:\n%s', tb)
        return render_template('errors/500.html', error=error, traceback=tb), 500

    # ---- Create database tables on first run -----------------------------
    with app.app_context():
        import models  # noqa: F401 — triggers model registration
        db.create_all()

        # Seed USPSTF care gap rules on first run (F15)
        try:
            from agent.caregap_engine import seed_default_rules
            seed_default_rules(app)
        except Exception:
            pass  # non-critical — rules can be seeded later

    return app


# ---------------------------------------------------------------------------
# Blueprint registration
# ---------------------------------------------------------------------------
def _register_blueprints(app):
    """
    Import and register each route blueprint.
    Wrapped in try/except so the app still starts even when a
    blueprint file has not been created yet.
    """
    blueprint_map = [
        ('routes.auth',      'auth_bp'),
        ('routes.admin',     'admin_bp'),
        ('routes.agent_api', 'agent_api_bp'),
        ('routes.dashboard', 'dashboard_bp'),
        ('routes.timer',     'timer_bp'),
        ('routes.inbox',     'inbox_bp'),
        ('routes.oncall',    'oncall_bp'),
        ('routes.orders',    'orders_bp'),
        ('routes.medref',    'medref_bp'),
        ('routes.labtrack',  'labtrack_bp'),
        ('routes.caregap',   'caregap_bp'),
        ('routes.metrics',   'metrics_bp'),
        ('routes.tools',     'tools_bp'),
        ('routes.netpractice_admin', 'np_admin_bp'),
        ('routes.patient',   'patient_bp'),
        ('routes.ai_api',    'ai_api_bp'),
        ('routes.intelligence', 'intel_bp'),
    ]
    for module_path, bp_name in blueprint_map:
        try:
            module = __import__(module_path, fromlist=[bp_name])
            blueprint = getattr(module, bp_name)
            app.register_blueprint(blueprint)
        except (ImportError, AttributeError):
            app.logger.warning(
                f'Blueprint {module_path}.{bp_name} not found — skipping.'
            )


# ---------------------------------------------------------------------------
# Direct execution:  python app.py
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app = create_app()
    app.run(
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 5000),
        debug=app.config.get('DEBUG', False),
    )

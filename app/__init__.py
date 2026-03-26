"""
CareCompanion — Flask App Package

This package is the canonical home for the Flask app factory so imports
like `from app import create_app` work in both source mode and frozen
PyInstaller mode.
"""

import logging
import os
import traceback

from flask import Flask, render_template, request, session
from flask_bcrypt import Bcrypt
from flask_compress import Compress
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import HTTPException

from models import db
from utils.error_logger import log_http_error, log_exception, log_startup_error
from utils.paths import get_data_dir, get_db_path, get_resource_dir, is_frozen


# Extensions are module-level singletons used across models/routes.
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()
compress = Compress()


# Role-based access control for sidebar/module visibility.
ROLE_PERMISSIONS = {
	'ma': ['dashboard', 'orders', 'caregap', 'medref', 'patient_gen'],
	'provider': [
		'dashboard', 'orders', 'caregap', 'medref', 'timer',
		'billing', 'inbox', 'oncall', 'labtrack', 'metrics',
		'tools', 'reformatter', 'briefing', 'patient_gen',
	],
	'admin': ['*'],
}


def create_app(testing=False):
	"""Build and return a fully configured Flask app instance."""
	if is_frozen():
		res = get_resource_dir()
		app = Flask(
			__name__,
			template_folder=os.path.join(res, 'templates'),
			static_folder=os.path.join(res, 'static'),
		)
	else:
		root = os.path.dirname(os.path.abspath(__file__))
		app = Flask(
			__name__,
			template_folder=os.path.join(root, '..', 'templates'),
			static_folder=os.path.join(root, '..', 'static'),
		)

	app.config.from_object('config')

	db_path = get_db_path()
	app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path.replace('\\', '/')
	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

	os.makedirs(os.path.dirname(db_path), exist_ok=True)
	backup_path = os.path.join(get_data_dir(), 'backups')
	os.makedirs(backup_path, exist_ok=True)

	db.init_app(app)
	login_manager.init_app(app)
	bcrypt.init_app(app)
	csrf.init_app(app)

	# Enable response compression (gzip/brotli) in non-test environments.
	if not testing:
		compress.init_app(app)

	login_manager.login_view = 'auth.login'
	login_manager.login_message = 'Please log in to access CareCompanion.'
	login_manager.login_message_category = 'info'

	@login_manager.user_loader
	def load_user(user_id):
		try:
			from models.user import User
			return db.session.get(User, int(user_id))
		except (ValueError, TypeError):
			return None
		except Exception:
			app.logger.warning('Unexpected error in load_user for id=%s', user_id, exc_info=True)
			return None

	_register_blueprints(app)

	# ---- Jinja template filters ----
	_GAP_DISPLAY_NAMES = {
		'colorectal_colonoscopy': 'Colonoscopy',
		'colorectal_fobt': 'FOBT/FIT',
		'mammogram': 'Mammogram',
		'cervical_pap': 'Pap Smear',
		'cervical_pap_hpv': 'Pap + HPV Co-test',
		'lung_ldct': 'Lung Cancer Screening (LDCT)',
		'dexa_scan': 'DEXA Scan',
		'hypertension_screen': 'Blood Pressure Screening',
		'diabetes_screen': 'Diabetes Screening',
		'lipid_screen': 'Lipid Panel',
		'depression_screen': 'Depression Screening (PHQ-9)',
		'aaa_screen': 'AAA Screening',
		'fall_risk': 'Fall Risk Assessment',
		'hiv_screen': 'HIV Screening',
		'hep_b_screen': 'Hepatitis B Screening',
		'hep_c_screen': 'Hepatitis C Screening',
		'flu_vaccine': 'Flu Vaccine',
		'covid_vaccine': 'COVID-19 Vaccine',
		'shingrix': 'Shingles Vaccine (Shingrix)',
		'tdap': 'Tdap Vaccine',
		'pneumococcal': 'Pneumococcal Vaccine',
	}

	@app.template_filter('gap_display')
	def gap_display_filter(gap_name_or_type):
		"""Convert gap_type keys like 'colorectal_colonoscopy' to clean names."""
		if not gap_name_or_type:
			return 'Unknown Screening'
		# If it's already a clean name (has spaces or parens), return as-is
		if ' ' in gap_name_or_type:
			return gap_name_or_type
		# Look up in mapping, fall back to title-casing the key
		return _GAP_DISPLAY_NAMES.get(
			gap_name_or_type,
			gap_name_or_type.replace('_', ' ').title()
		)

	@app.context_processor
	def inject_helpers():
		def user_can_access(module):
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
			"""Cached for 60s to avoid a COUNT(*) on every page render."""
			try:
				if not current_user.is_authenticated:
					return 0
				import time
				cache_key = '_oncall_count'
				cache_ts_key = '_oncall_count_ts'
				cached = session.get(cache_key)
				cached_ts = session.get(cache_ts_key, 0)
				if cached is not None and (time.time() - cached_ts) < 60:
					return cached
				from models.oncall import OnCallNote
				count = OnCallNote.query.filter_by(
					user_id=current_user.id,
					documentation_status='pending',
				).count()
				session[cache_key] = count
				session[cache_ts_key] = time.time()
				return count
			except Exception:
				return 0

		from datetime import datetime, timezone
		from utils.feature_gates import is_feature_enabled
		return {
			'user_can_access': user_can_access,
			'feature_enabled': lambda feat: is_feature_enabled(current_user, feat),
			'oncall_pending_count': oncall_pending_count,
			'app_version': app.config.get('APP_VERSION', ''),
			'user_can_use_ai': lambda: current_user.is_authenticated and current_user.can_use_ai(),
			'user_ai_enabled': lambda: current_user.is_authenticated and getattr(current_user, 'ai_enabled', False),
			'chart_flag_enabled': lambda: app.config.get('CHART_FLAG_ENABLED', False),
			'utcnow': datetime.now(timezone.utc),
		}

	@app.after_request
	def log_request(response):
		try:
			if current_user.is_authenticated:
				skip_paths = (
					'/api/notifications', '/api/agent-status', '/api/auth-status',
					'/api/setup-status', '/api/netpractice/', '/static/',
					# Skip high-frequency AJAX widget endpoints (patient chart
					# fires ~15 parallel calls on load — audit logging each one
					# adds 15 synchronous DB writes per chart open).
					'/api/patient/',
					'/api/active-chart',
				)
				if not any(request.path.startswith(p) for p in skip_paths):
					module = request.blueprints[0] if request.blueprints else ''
					from utils import log_access

					log_access(
						user_id=current_user.id,
						action=f'{request.method} {request.path}',
						module=module,
						ip_address=request.remote_addr or '',
					)
					db.session.commit()
		except Exception:
			db.session.rollback()
		if response.status_code >= 400:
			log_http_error(response, request)

		# Cache-Control for static assets — avoid re-fetching CSS/JS.
		if request.path.startswith('/static/'):
			response.cache_control.public = True
			response.cache_control.max_age = 604800  # 7 days

		return response

	log_dir = os.path.join(get_data_dir(), 'logs')
	os.makedirs(log_dir, exist_ok=True)

	import logging.config
	logging.config.dictConfig({
		'version': 1,
		'disable_existing_loggers': False,
		'formatters': {
			'json': {
				'format': '{"timestamp":"%(asctime)s","level":"%(levelname)s",'
				          '"module":"%(module)s","message":"%(message)s"}',
				'datefmt': '%Y-%m-%dT%H:%M:%S',
			},
		},
		'handlers': {
			'rotating_file': {
				'class': 'logging.handlers.TimedRotatingFileHandler',
				'filename': os.path.join(log_dir, 'carecompanion.log'),
				'when': 'midnight',
				'backupCount': 7,
				'formatter': 'json',
				'level': 'INFO',
				'encoding': 'utf-8',
			},
		},
		'root': {
			'level': 'INFO' if not app.debug else 'DEBUG',
			'handlers': ['rotating_file'],
		},
	})
	app.logger.info('Structured logging initialised — %s', log_dir)

	@app.route('/favicon.ico')
	def favicon():
		# Serve the inline SVG favicon as an actual .ico-compatible response
		from flask import Response
		svg = (
			"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
			"<rect width='32' height='32' rx='6' fill='#177a6b'/>"
			"<text x='16' y='22' font-family='Arial,sans-serif' font-size='14' font-weight='700' "
			"fill='white' text-anchor='middle'>CC</text></svg>"
		)
		return Response(svg, mimetype='image/svg+xml')

	@app.errorhandler(404)
	def page_not_found(error):
		return render_template('errors/404.html'), 404

	@app.errorhandler(500)
	def internal_server_error(error):
		db.session.rollback()
		tb = traceback.format_exc()
		app.logger.error('500 error:\n%s', tb)
		log_exception(error, request)
		return render_template('errors/500.html', error=error, traceback=tb if app.debug else None), 500

	@app.errorhandler(Exception)
	def unhandled_exception(error):
		# Let HTTP exceptions (400, 403, 404, etc.) return their proper status
		# codes instead of being re-wrapped as 500.
		if isinstance(error, HTTPException):
			return error
		db.session.rollback()
		tb = traceback.format_exc()
		app.logger.error('Unhandled exception:\n%s', tb)
		log_exception(error, request)
		return render_template('errors/500.html', error=error, traceback=tb if app.debug else None), 500

	with app.app_context():
		try:
			import models  # noqa: F401

			# In dev mode the Werkzeug reloader spawns a parent process that
			# never serves requests.  Skip heavy DB init in that parent --
			# the child (WERKZEUG_RUN_MAIN=true) will do the real work.
			_is_reloader_parent = (
				app.debug
				and not os.environ.get('WERKZEUG_RUN_MAIN')
			)
			if not _is_reloader_parent:
				db.create_all()
				_run_pending_migrations(app)

				try:
					from agent.caregap_engine import seed_default_rules

					seed_default_rules(app)
				except Exception:
					pass
		except Exception as e:
			log_startup_error('Failed during app startup', e)
			raise

	return app


def _run_pending_migrations(app):
	"""
	Auto-run any migrate_*.py scripts that haven't been applied yet.
	Tracks applied migrations in the _applied_migrations table.
	"""
	# Recursion guard — prevent re-entry when a migration calls create_app()
	if getattr(_run_pending_migrations, '_running', False):
		return
	_run_pending_migrations._running = True

	import glob
	import importlib
	import sqlite3
	from datetime import datetime, timezone

	try:
		db_path = get_db_path()
		conn = sqlite3.connect(db_path)
		cur = conn.cursor()

		# Create tracking table if missing
		cur.execute(
			'CREATE TABLE IF NOT EXISTS _applied_migrations '
			'(name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)'
		)
		conn.commit()

		# Already-applied set
		cur.execute('SELECT name FROM _applied_migrations')
		applied = {row[0] for row in cur.fetchall()}

		# Find all migrate_*.py in project root and migrations/ subfolder
		root = os.path.dirname(os.path.abspath(__file__))
		project_root = os.path.dirname(root)
		scripts = sorted(glob.glob(os.path.join(project_root, 'migrate_*.py')))
		scripts += sorted(glob.glob(os.path.join(project_root, 'migrations', 'migrate_*.py')))

		# Fast-path: if every migration file is already applied, skip the
		# expensive per-file loop entirely (avoids reading 69+ files).
		script_names = {os.path.basename(s) for s in scripts}
		if script_names.issubset(applied):
			conn.close()
			app.logger.debug('All %d migrations already applied -- skipping scan', len(applied))
			return

		for script_path in scripts:
			name = os.path.basename(script_path)
			if name in applied:
				continue

			app.logger.info('Running migration: %s', name)
			try:
				module_name = name[:-3]  # strip .py
				spec = importlib.util.spec_from_file_location(module_name, script_path)
				mod = importlib.util.module_from_spec(spec)
				# Prevent raw-SQL scripts from executing on import
				# by checking for run_migration first via source inspection
				with open(script_path, 'r') as _mig_f:
					source = _mig_f.read()
				has_run_fn = 'def run_migration' in source

				if has_run_fn:
					spec.loader.exec_module(mod)
					from models import db as _db
					mod.run_migration(app, _db)
				else:
					# Raw SQL scripts — run as subprocess for isolation
					import subprocess
					import sys
					result = subprocess.run(
						[sys.executable, script_path],
						cwd=project_root,
						capture_output=True,
						text=True,
						timeout=60,
					)
					if result.returncode != 0:
						app.logger.error(
							'Migration %s failed (exit %d): %s',
							name, result.returncode, result.stderr[:500],
						)
						continue

				# Record success
				now_str = datetime.now(timezone.utc).isoformat()
				cur.execute(
					'INSERT OR IGNORE INTO _applied_migrations (name, applied_at) VALUES (?, ?)',
					(name, now_str),
				)
				conn.commit()
				app.logger.info('Migration applied: %s', name)
			except Exception as exc:
				app.logger.error('Migration %s error: %s', name, exc)

		conn.close()
	finally:
		_run_pending_migrations._running = False


def _register_blueprints(app):
	"""Import and register route blueprints."""
	blueprint_map = [
		('routes.auth', 'auth_bp'),
		('routes.admin', 'admin_bp'),
		('routes.agent_api', 'agent_api_bp'),
		('routes.dashboard', 'dashboard_bp'),
		('routes.timer', 'timer_bp'),
		('routes.inbox', 'inbox_bp'),
		('routes.oncall', 'oncall_bp'),
		('routes.orders', 'orders_bp'),
		('routes.medref', 'medref_bp'),
		('routes.labtrack', 'labtrack_bp'),
		('routes.caregap', 'caregap_bp'),
		('routes.metrics', 'metrics_bp'),
		('routes.tools', 'tools_bp'),
		('routes.netpractice_admin', 'np_admin_bp'),
		('routes.patient', 'patient_bp'),
		('routes.ai_api', 'ai_api_bp'),
		('routes.intelligence', 'intel_bp'),
		('routes.patient_gen', 'patient_gen_bp'),
		('routes.message', 'message_bp'),
		('routes.bonus', 'bonus_bp'),
		('routes.ccm', 'ccm_bp'),
		('routes.monitoring', 'monitoring_bp'),
		('routes.telehealth', 'telehealth_bp'),
		('routes.revenue', 'revenue_bp'),
		('routes.campaigns', 'campaigns_bp'),
		('routes.calculator', 'calculator_bp'),
		('routes.daily_summary', 'daily_summary_bp'),
		('routes.help', 'help_bp'),
		('routes.admin_med_catalog', 'admin_med_catalog_bp'),
		('routes.admin_rules_registry', 'admin_rules_registry_bp'),
		('routes.admin_benchmarks', 'admin_benchmarks_bp'),
	]

	for module_path, bp_name in blueprint_map:
		try:
			module = __import__(module_path, fromlist=[bp_name])
			bp = getattr(module, bp_name)
			app.register_blueprint(bp)
		except Exception as e:
			app.logger.warning('Could not register blueprint %s (%s): %s', module_path, bp_name, e)

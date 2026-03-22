"""
CareCompanion — Agent API & Admin Routes

File location: carecompanion/routes/agent_api.py

Provides:
  GET  /api/health            — public health-check (no auth)
  GET  /api/agent-status     — JSON status for the header health dot
  GET  /admin/agent          — detailed agent dashboard (admin only)
  POST /admin/agent/restart  — restart the agent process (admin only)
"""

import os
import json
import subprocess
import sys
from datetime import datetime, timezone

from flask import (
    Blueprint, render_template, request, jsonify, current_app,
)
from flask_login import login_required, current_user
from models import db
from models.agent import AgentLog, AgentError

agent_api_bp = Blueprint('agent_api', __name__)

_server_started_at = datetime.now(timezone.utc)


# ======================================================================
# GET /api/health — public health-check (no auth required)
# ======================================================================
@agent_api_bp.route('/api/health')
def api_health():
    """Lightweight health-check for load-balancers and monitoring tools."""
    now = datetime.now(timezone.utc)
    uptime = (now - _server_started_at).total_seconds()

    # Quick DB connectivity test
    db_status = 'connected'
    try:
        db.session.execute(db.text('SELECT 1'))
    except Exception:
        db_status = 'error'

    version = current_app.config.get('APP_VERSION', 'unknown')

    status_code = 200 if db_status == 'connected' else 503
    return jsonify({
        'status': 'ok' if db_status == 'connected' else 'degraded',
        'version': version,
        'db': db_status,
        'uptime_seconds': int(uptime),
    }), status_code


# ======================================================================
# Helpers
# ======================================================================
def _read_active_user_file():
    """Read data/active_user.json and return the dict (or empty dict)."""
    path = os.path.join(current_app.root_path, 'data', 'active_user.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _require_admin(f):
    """Inline admin check — returns 403 JSON if the user is not admin."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Admin only'}), 403
        return f(*args, **kwargs)
    return wrapper


# ======================================================================
# GET /api/agent-status — polled every 15 seconds by the header JS
# ======================================================================
@agent_api_bp.route('/api/agent-status')
@login_required
def api_agent_status():
    """
    Returns the agent's current health based on database heartbeats.
    The header JS uses this to colour the status dot green/yellow/red.
    """
    now = datetime.now(timezone.utc)

    # Find the most recent heartbeat (or startup) event
    last_beat = (
        AgentLog.query
        .filter(AgentLog.event.in_(['heartbeat', 'startup']))
        .order_by(AgentLog.timestamp.desc())
        .first()
    )

    if not last_beat:
        return jsonify({
            'status': 'offline',
            'last_heartbeat': None,
            'active_user': _read_active_user_file(),
            'jobs_running': 0,
        })

    # SQLite stores naive datetimes — treat them as UTC
    beat_time = last_beat.timestamp.replace(tzinfo=timezone.utc)
    age_seconds = (now - beat_time).total_seconds()

    if age_seconds <= 60:
        status = 'green'
    elif age_seconds <= 300:
        status = 'yellow'
    else:
        status = 'red'

    return jsonify({
        'status': status,
        'last_heartbeat': last_beat.timestamp.isoformat(),
        'age_seconds': int(age_seconds),
        'active_user': _read_active_user_file(),
        'jobs_running': 0,
    })


# ======================================================================
# GET /admin/agent — detailed agent health dashboard
# ======================================================================
@agent_api_bp.route('/admin/agent')
@login_required
@_require_admin
def admin_agent_dashboard():
    """
    Full-page admin view showing uptime, last heartbeat, recent job
    runs, and any errors from the agent_errors table.
    """
    now = datetime.now(timezone.utc)

    # Last startup event (to calculate uptime)
    last_startup = (
        AgentLog.query
        .filter_by(event='startup')
        .order_by(AgentLog.timestamp.desc())
        .first()
    )

    # Last heartbeat
    last_heartbeat = (
        AgentLog.query
        .filter(AgentLog.event.in_(['heartbeat', 'startup']))
        .order_by(AgentLog.timestamp.desc())
        .first()
    )

    # Calculate uptime string
    uptime_str = 'Agent has not started'
    if last_startup:
        # SQLite stores naive datetimes — treat them as UTC
        startup_time = last_startup.timestamp.replace(tzinfo=timezone.utc)
        delta = now - startup_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes = remainder // 60
        uptime_str = f'{hours}h {minutes}m'

    # Recent lifecycle events (last 50)
    recent_events = (
        AgentLog.query
        .order_by(AgentLog.timestamp.desc())
        .limit(50)
        .all()
    )

    # Recent errors (last 30)
    recent_errors = (
        AgentError.query
        .order_by(AgentError.timestamp.desc())
        .limit(30)
        .all()
    )

    # Active user file
    active_user = _read_active_user_file()

    # Heartbeat age for template
    heartbeat_age = None
    if last_heartbeat:
        hb_time = last_heartbeat.timestamp.replace(tzinfo=timezone.utc)
        heartbeat_age = int((now - hb_time).total_seconds())

    return render_template(
        'admin_agent.html',
        uptime_str=uptime_str,
        last_startup=last_startup,
        last_heartbeat=last_heartbeat,
        heartbeat_age=heartbeat_age,
        recent_events=recent_events,
        recent_errors=recent_errors,
        active_user=active_user,
        now=now,
    )


# ======================================================================
# POST /admin/agent/restart — restart agent.py subprocess
# ======================================================================
@agent_api_bp.route('/admin/agent/restart', methods=['POST'])
@login_required
@_require_admin
def admin_restart_agent():
    """
    Launches agent.py as a new detached subprocess.  The old agent
    (if running) should detect the new PID file and shut down.
    """
    try:
        from utils.paths import is_frozen
        python_exe = sys.executable

        if is_frozen():
            # In exe mode, the exe itself handles --mode=agent
            cmd = [python_exe, '--mode=agent']
        else:
            agent_path = os.path.join(current_app.root_path, 'agent.py')
            if not os.path.exists(agent_path):
                return jsonify({
                    'success': False,
                    'error': 'agent.py not found in project root',
                }), 404
            cmd = [python_exe, agent_path]

        # Start as a detached process (Windows-friendly)
        # CREATE_NEW_PROCESS_GROUP lets it survive if Flask restarts
        subprocess.Popen(
            cmd,
            cwd=os.path.dirname(python_exe) if is_frozen() else current_app.root_path,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return jsonify({
            'success': True,
            'message': 'Agent restart initiated',
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


# ======================================================================
# GET /api/auth-status — NetPractice auth indicator (polled by header JS)
# ======================================================================
@agent_api_bp.route('/api/auth-status')
@login_required
def api_auth_status():
    """
    Returns the NetPractice session health for the header auth dot.
    Reads data/np_reauth.json written by the scraper.
    """
    reauth_file = os.path.join(
        current_app.root_path, 'data', 'np_reauth.json',
    )

    # If the file doesn't exist, we've never run — status unknown
    if not os.path.exists(reauth_file):
        return jsonify({
            'status': 'unknown',
            'needs_reauth': False,
            'last_checked': None,
            'netpractice_configured': bool(current_app.config.get('NETPRACTICE_URL')),
        })

    try:
        with open(reauth_file, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        data = {}

    needs_reauth = data.get('needs_reauth', False)
    last_checked = data.get('last_checked')

    if needs_reauth:
        status = 'red'
    elif last_checked:
        status = 'green'
    else:
        status = 'unknown'

    return jsonify({
        'status': status,
        'needs_reauth': needs_reauth,
        'last_checked': last_checked,
        'netpractice_configured': bool(current_app.config.get('NETPRACTICE_URL')),
    })


# ======================================================================
# POST /admin/auth/clear-session — clear NetPractice cookies ("Reauth Now")
# ======================================================================
@agent_api_bp.route('/admin/auth/clear-session', methods=['POST'])
@login_required
@_require_admin
def admin_clear_np_session():
    """
    Deletes the saved NetPractice cookie file.
    The user will need to manually re-authenticate via the browser.
    """
    cookie_file = os.path.join(
        current_app.root_path,
        current_app.config.get('SESSION_COOKIE_FILE', 'data/np_session.pkl'),
    )

    # Delete cookie file
    if os.path.exists(cookie_file):
        os.remove(cookie_file)

    # Set re-auth flag
    reauth_file = os.path.join(current_app.root_path, 'data', 'np_reauth.json')
    reauth_data = {
        'needs_reauth': True,
        'last_checked': datetime.now(timezone.utc).isoformat(),
        'status': 'needs_reauth',
    }
    os.makedirs(os.path.dirname(reauth_file), exist_ok=True)
    with open(reauth_file, 'w') as f:
        json.dump(reauth_data, f)

    return jsonify({
        'success': True,
        'message': 'NetPractice session cleared — manual re-auth required',
    })

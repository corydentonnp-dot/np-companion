"""
Runtime Error Logger — writes structured error entries to data/logs/error_log.jsonl

Captures:
  - HTTP 4xx/5xx responses (404, 500, etc.)
  - Unhandled exceptions
  - Startup/launch errors
  - Agent and background job failures

Each entry is a single JSON line with: timestamp, level, category, path,
method, status_code, user_id, ip, message, traceback (if any).

Log file rotates daily, keeps 30 days of history for pre-beta debugging.
"""

import json
import logging
import logging.handlers
import os
import traceback as tb_module
from datetime import datetime, timezone

from utils.paths import get_data_dir

_logger = None


def _get_logger():
    """Lazy-init a dedicated file logger for error_log.jsonl."""
    global _logger
    if _logger is not None:
        return _logger

    log_dir = os.path.join(get_data_dir(), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    _logger = logging.getLogger('np_error_log')
    _logger.setLevel(logging.DEBUG)
    _logger.propagate = False  # Don't duplicate into root logger

    handler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join(log_dir, 'error_log.jsonl'),
        when='midnight',
        backupCount=30,
        encoding='utf-8',
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('%(message)s'))
    _logger.addHandler(handler)
    return _logger


def log_error(category, message, *, status_code=None, path=None, method=None,
              user_id=None, ip=None, traceback_str=None, extra=None):
    """Write a structured error entry to error_log.jsonl.

    Args:
        category: e.g. 'http_404', 'http_500', 'unhandled_exception',
                  'startup', 'agent_error', 'background_job'
        message: Human-readable description
        status_code: HTTP status code (if applicable)
        path: Request path (if applicable)
        method: HTTP method (if applicable)
        user_id: Authenticated user ID (if applicable)
        ip: Client IP address (if applicable)
        traceback_str: Full traceback string (if applicable)
        extra: Dict of additional context
    """
    entry = {
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'level': 'ERROR' if (status_code or 0) >= 500 or category in ('unhandled_exception', 'startup') else 'WARNING',
        'category': category,
        'message': str(message),
    }
    if status_code is not None:
        entry['status_code'] = status_code
    if path is not None:
        entry['path'] = path
    if method is not None:
        entry['method'] = method
    if user_id is not None:
        entry['user_id'] = user_id
    if ip is not None:
        entry['ip'] = ip
    if traceback_str:
        entry['traceback'] = traceback_str
    if extra:
        entry['extra'] = extra

    _get_logger().error(json.dumps(entry, ensure_ascii=False))


def log_http_error(response, request_obj):
    """Log an HTTP 4xx/5xx error from a Flask after_request hook."""
    if response.status_code < 400:
        return

    from flask_login import current_user
    user_id = current_user.id if (current_user and current_user.is_authenticated) else None

    category = f'http_{response.status_code}'
    message = f'{request_obj.method} {request_obj.path} -> {response.status_code}'

    log_error(
        category=category,
        message=message,
        status_code=response.status_code,
        path=request_obj.path,
        method=request_obj.method,
        user_id=user_id,
        ip=request_obj.remote_addr,
        extra={'referrer': request_obj.referrer} if request_obj.referrer else None,
    )


def log_exception(error, request_obj=None):
    """Log an unhandled exception with full traceback."""
    from flask_login import current_user

    user_id = None
    path = None
    method = None
    ip = None

    if request_obj:
        path = request_obj.path
        method = request_obj.method
        ip = request_obj.remote_addr
        try:
            if current_user and current_user.is_authenticated:
                user_id = current_user.id
        except Exception:
            pass

    log_error(
        category='unhandled_exception',
        message=str(error),
        status_code=500,
        path=path,
        method=method,
        user_id=user_id,
        ip=ip,
        traceback_str=tb_module.format_exc(),
    )


def log_startup_error(message, error=None):
    """Log a startup/launch error."""
    log_error(
        category='startup',
        message=message,
        traceback_str=tb_module.format_exc() if error else None,
    )

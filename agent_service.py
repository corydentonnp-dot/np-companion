"""
NP Companion — Background Agent

File location: np-companion/agent.py (project root)

Implements Dev Guide F3 requirements:
- System tray icon (pystray) with menu actions
- HTTP status endpoint on port 5001
- APScheduler integration for recurring jobs
- Crash recovery popup for incomplete time sessions
"""

import json
import logging
import os
import threading
import time
import traceback
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from agent.scheduler import build_scheduler
from agent.mrn_reader import read_mrn, calibrate_mrn_reader
from agent.inbox_monitor import run_inbox_monitor
from agent.inbox_digest import run_digest_job
from agent.clinical_summary_parser import ClinicalSummaryHandler, poll_export_folder, start_xml_watcher
from agent.notifier import check_callback_reminders
from routes.labtrack import check_overdue_labs

# Optional desktop dependencies for tray/popup features.
try:
    import pystray
    from pystray import MenuItem as TrayItem
except Exception:  # pragma: no cover
    pystray = None
    TrayItem = None

try:
    from PIL import Image, ImageDraw
except Exception:  # pragma: no cover
    Image = None
    ImageDraw = None


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger('agent')

ACTIVE_USER_PATH = os.path.join(os.path.dirname(__file__), 'data', 'active_user.json')


class AgentService:
    """Coordinates scheduler, tray controls, and local HTTP status server."""

    def __init__(self):
        self.pid = os.getpid()
        self.started_at = datetime.now(timezone.utc)
        self.shutdown_event = threading.Event()
        self.scheduler = None
        self.http_server = None
        self.http_thread = None
        self.tray_icon = None
        self.paused = False
        self.last_heartbeat_at = None
        self.xml_observer = None
        self._processed_xml_files = set()

        self.app = self._create_app_context()

    # ------------------------------------------------------------------
    # Flask app context + DB helpers
    # ------------------------------------------------------------------
    def _create_app_context(self):
        from app import create_app

        app = create_app()
        ctx = app.app_context()
        ctx.push()
        return app

    def read_active_user(self):
        if not os.path.exists(ACTIVE_USER_PATH):
            return {'user_id': None}
        try:
            with open(ACTIVE_USER_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {'user_id': None}

    def write_heartbeat(self):
        from models import db
        from models.agent import AgentLog

        try:
            entry = AgentLog(
                event='heartbeat',
                pid=self.pid,
                details='',
                timestamp=datetime.now(timezone.utc),
            )
            db.session.add(entry)
            db.session.commit()
            self.last_heartbeat_at = entry.timestamp
        except Exception as e:
            db.session.rollback()
            logger.error(f'Failed to write heartbeat: {e}')

    def write_startup_log(self, crash_recovered=False, recovery_details=''):
        from models import db
        from models.agent import AgentLog

        details = f'PID={self.pid}'
        if crash_recovered:
            details += f' | Crash recovery: {recovery_details}'

        try:
            entry = AgentLog(
                event='startup',
                pid=self.pid,
                details=details,
                timestamp=datetime.now(timezone.utc),
            )
            db.session.add(entry)
            db.session.commit()
            logger.info(f'Startup logged: {details}')
        except Exception as e:
            db.session.rollback()
            logger.error(f'Failed to write startup log: {e}')

    def write_shutdown_log(self):
        from models import db
        from models.agent import AgentLog

        try:
            entry = AgentLog(
                event='shutdown',
                pid=self.pid,
                details=f'PID={self.pid} clean shutdown',
                timestamp=datetime.now(timezone.utc),
            )
            db.session.add(entry)
            db.session.commit()
            logger.info('Shutdown logged')
        except Exception as e:
            db.session.rollback()
            logger.error(f'Failed to write shutdown log: {e}')

    def log_agent_error(self, job_name, error_msg, tb_text='', user_id=None):
        from models import db
        from models.agent import AgentError

        try:
            entry = AgentError(
                job_name=job_name,
                error_message=error_msg,
                traceback=tb_text,
                user_id=user_id,
                timestamp=datetime.now(timezone.utc),
            )
            db.session.add(entry)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f'Failed to log agent error: {e}')

    # ------------------------------------------------------------------
    # Crash recovery with provider confirmation popup
    # ------------------------------------------------------------------
    def _show_recovery_popup(self, pending_count):
        """
        Ask provider whether to close incomplete sessions with estimated end times.
        Returns True to close, False to keep pending.
        """
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            msg = (
                f'NP Companion found {pending_count} incomplete time session(s) from a prior crash.\n\n'
                'Do you want to close them now using an estimated end time?\n'
                'Choose No to leave them open for manual review.'
            )
            result = messagebox.askyesno('NP Companion Crash Recovery', msg)
            root.destroy()
            return bool(result)
        except Exception as e:
            logger.warning(f'Could not show crash-recovery popup: {e}')
            return False

    def perform_crash_recovery(self):
        from models import db
        from models.timelog import TimeLog
        from models.agent import AgentLog

        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        try:
            incomplete = (
                TimeLog.query
                .filter(TimeLog.session_start >= cutoff, TimeLog.session_end.is_(None))
                .all()
            )

            if not incomplete:
                return ''

            should_close = self._show_recovery_popup(len(incomplete))
            if not should_close:
                summary = f'Provider deferred closure for {len(incomplete)} incomplete session(s)'
                db.session.add(
                    AgentLog(
                        event='crash_recovery_pending',
                        pid=self.pid,
                        details=summary,
                        timestamp=datetime.now(timezone.utc),
                    )
                )
                db.session.commit()
                logger.info(summary)
                return summary

            last_hb = (
                AgentLog.query
                .filter(AgentLog.event.in_(['heartbeat', 'startup']))
                .order_by(AgentLog.timestamp.desc())
                .first()
            )
            estimated_end = last_hb.timestamp if last_hb else datetime.now(timezone.utc)

            recovered = []
            for tl in incomplete:
                tl.session_end = estimated_end
                tl.duration_seconds = int((estimated_end - tl.session_start).total_seconds())
                note = tl.billing_notes or ''
                tl.billing_notes = (
                    note + (' | ' if note else '') +
                    'ESTIMATED: session closed by crash recovery (provider confirmed)'
                )
                recovered.append(f'TimeLog#{tl.id}')

            summary = f'Recovered {len(recovered)} incomplete session(s): {", ".join(recovered)}'
            db.session.add(
                AgentLog(
                    event='crash_recovery',
                    pid=self.pid,
                    details=summary,
                    timestamp=datetime.now(timezone.utc),
                )
            )
            db.session.commit()
            logger.info(summary)
            return summary

        except Exception as e:
            db.session.rollback()
            logger.error(f'Crash recovery failed: {e}')
            return f'Crash recovery error: {e}'

    # ------------------------------------------------------------------
    # Safe job wrappers + placeholder jobs
    # ------------------------------------------------------------------
    def safe_job(self, job_name, func, *args, **kwargs):
        active = self.read_active_user()
        user_id = active.get('user_id')
        try:
            func(*args, **kwargs)
        except Exception as e:
            tb_text = traceback.format_exc()
            logger.error(f'Job {job_name} failed: {e}\n{tb_text}')
            self.log_agent_error(job_name, str(e), tb_text=tb_text, user_id=user_id)

    def job_heartbeat(self):
        self.write_heartbeat()

    def job_mrn_reader(self):
        active = self.read_active_user()
        if not active.get('user_id'):
            return
        read_mrn(active['user_id'])

    def job_inbox_check(self):
        active = self.read_active_user()
        if not active.get('user_id'):
            return
        run_inbox_monitor(active['user_id'])

    def job_inbox_digest(self):
        active = self.read_active_user()
        if not active.get('user_id'):
            return
        run_digest_job(active['user_id'])

    def job_callback_check(self):
        active = self.read_active_user()
        if not active.get('user_id'):
            return
        check_callback_reminders(active['user_id'])

    def job_overdue_lab_check(self):
        """F11c: daily check for overdue lab tracking entries."""
        active = self.read_active_user()
        if not active.get('user_id'):
            return
        with self.app.app_context():
            count = check_overdue_labs(active['user_id'])
            if count:
                logger.info(f'Flagged {count} newly overdue lab(s)')

    def job_xml_archive_cleanup(self):
        """F11e: daily cleanup of old clinical summary XML files."""
        import hashlib
        import config as cfg
        from models import db
        from models.audit import AuditLog

        retention_days = getattr(cfg, 'CLINICAL_SUMMARY_RETENTION_DAYS', 183)
        export_folder = getattr(cfg, 'CLINICAL_SUMMARY_EXPORT_FOLDER', 'data/clinical_summaries/')
        if not os.path.isabs(export_folder):
            export_folder = os.path.join(os.path.dirname(__file__), export_folder)

        if not os.path.isdir(export_folder):
            return

        cutoff = time.time() - (retention_days * 86400)
        deleted = 0

        for fname in os.listdir(export_folder):
            if not fname.lower().endswith('.xml'):
                continue
            fpath = os.path.join(export_folder, fname)
            if os.path.getmtime(fpath) < cutoff:
                name_hash = hashlib.sha256(fname.encode()).hexdigest()[:12]
                os.remove(fpath)
                deleted += 1
                with self.app.app_context():
                    log = AuditLog(
                        user_id=0,
                        action='xml_archive_delete',
                        details=name_hash,
                    )
                    db.session.add(log)
                    db.session.commit()
                logger.info(f'Archived old XML: {name_hash}')

        if deleted:
            logger.info(f'XML archive cleanup: removed {deleted} file(s) older than {retention_days} days')

    def job_xml_poll(self):
        """F6d fallback: poll the export folder for new clinical summary XMLs."""
        active = self.read_active_user()
        uid = active.get('user_id') or 0
        if not uid:
            return
        with self.app.app_context():
            self._xml_processed = poll_export_folder(
                uid,
                processed_files=getattr(self, '_xml_processed', None),
            )

    def job_weekly_summary(self):
        """F13c: generate and email weekly productivity summary every Friday at 5 PM."""
        from models.user import User

        with self.app.app_context():
            users = User.query.filter_by(is_active_account=True).all()
            for user in users:
                if not user.preferences.get('weekly_summary_email', False):
                    continue
                try:
                    from routes.metrics import _generate_weekly_summary
                    summary = _generate_weekly_summary(user.id)
                    self._send_weekly_email(user, summary)
                    logger.info(f'Weekly summary sent to {user.display_name or user.username}')
                except Exception as e:
                    logger.error(f'Weekly summary failed for user {user.id}: {e}')

    def job_deactivation_check(self):
        """Deactivate users whose deactivate_at date has passed."""
        from models import db
        from models.user import User

        with self.app.app_context():
            now = datetime.now(timezone.utc)
            due = User.query.filter(
                User.is_active_account == True,
                User.deactivate_at.isnot(None),
                User.deactivate_at <= now,
            ).all()
            for user in due:
                user.is_active_account = False
                user.deactivate_at = None
                logger.info(f'Scheduled deactivation: {user.display_name or user.username} (id={user.id})')
            if due:
                db.session.commit()

    def job_monthly_billing(self):
        """F14c: generate and email monthly billing report on the 1st of each month."""
        from models.user import User

        with self.app.app_context():
            users = User.query.filter_by(is_active_account=True).all()
            for user in users:
                if not user.preferences.get('monthly_billing_email', True):
                    continue
                try:
                    from routes.timer import _monthly_stats, RVU_TABLE
                    from models.timelog import TimeLog
                    from datetime import date as dt_date

                    today = dt_date.today()
                    # Report for previous month
                    if today.month == 1:
                        rpt_year, rpt_month = today.year - 1, 12
                    else:
                        rpt_year, rpt_month = today.year, today.month - 1

                    start = datetime(rpt_year, rpt_month, 1, tzinfo=timezone.utc)
                    if rpt_month == 12:
                        end = datetime(rpt_year + 1, 1, 1, tzinfo=timezone.utc)
                    else:
                        end = datetime(rpt_year, rpt_month + 1, 1, tzinfo=timezone.utc)

                    sessions = (
                        TimeLog.query
                        .filter_by(user_id=user.id)
                        .filter(TimeLog.session_start >= start, TimeLog.session_start < end,
                                TimeLog.session_end.isnot(None))
                        .all()
                    )
                    stats = _monthly_stats(sessions)
                    self._send_monthly_billing_email(user, rpt_year, rpt_month, stats)
                    logger.info(f'Monthly billing report sent to {user.display_name or user.username}')
                except Exception as e:
                    logger.error(f'Monthly billing report failed for user {user.id}: {e}')

    def _send_monthly_billing_email(self, user, year, month, stats):
        """Send a monthly billing summary email via configured SMTP."""
        import smtplib
        from email.mime.text import MIMEText
        import config as cfg

        smtp_server = getattr(cfg, 'SMTP_SERVER', '')
        smtp_port = int(getattr(cfg, 'SMTP_PORT', 587))
        smtp_user = getattr(cfg, 'SMTP_USER', '')
        smtp_pass = getattr(cfg, 'SMTP_PASS', '')
        from_addr = getattr(cfg, 'SMTP_FROM', smtp_user)

        to_addr = user.preferences.get('email', '')
        if not to_addr or not smtp_server:
            return

        month_label = f'{year}-{month:02d}'
        em_lines = ''
        for lvl in sorted(stats['em_dist'].keys()):
            d = stats['em_dist'][lvl]
            em_lines += f'  {lvl}: {d["count"]} visits, {d["rvu"]} wRVU\n'

        body = (
            f"NP Companion — Monthly Billing Report ({month_label})\n\n"
            f"Total Patients: {stats['total_patients']}\n"
            f"Total wRVU: {stats['total_rvu']}\n"
            f"Chart Hours: {stats['total_chart_hrs']}\n"
            f"F2F Hours: {stats['total_f2f_hrs']}\n"
            f"New Patients: {stats['new_count']}\n"
            f"Established Patients: {stats['estab_count']}\n"
            f"Anomaly Flags: {stats['anomaly_count']}\n\n"
            f"E&M Distribution:\n{em_lines}\n"
            f"View full report: /billing/monthly-report?month={month_label}\n"
        )

        msg = MIMEText(body)
        msg['Subject'] = f"NP Companion Monthly Billing Report — {month_label}"
        msg['From'] = from_addr
        msg['To'] = to_addr

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_addr, [to_addr], msg.as_string())

    def _send_weekly_email(self, user, summary):
        """Send a weekly summary email via configured SMTP."""
        import smtplib
        from email.mime.text import MIMEText
        import config as cfg

        smtp_server = getattr(cfg, 'SMTP_SERVER', '')
        smtp_port = int(getattr(cfg, 'SMTP_PORT', 587))
        smtp_user = getattr(cfg, 'SMTP_USER', '')
        smtp_pass = getattr(cfg, 'SMTP_PASS', '')
        from_addr = getattr(cfg, 'SMTP_FROM', smtp_user)

        to_addr = user.preferences.get('email', '')
        if not to_addr or not smtp_server:
            return

        body = (
            f"NP Companion — Weekly Summary ({summary['week_start']})\n\n"
            f"Patients Seen: {summary['patients']}\n"
            f"Total Chart Hours: {summary['total_hours']}\n"
            f"F2F Hours: {summary['total_f2f']}\n"
            f"On-Call Calls: {summary['oncall_calls']}\n"
        )
        if summary.get('notable'):
            body += f"\n{summary['notable']}\n"

        msg = MIMEText(body)
        msg['Subject'] = f"NP Companion Weekly Summary — {summary['week_start']}"
        msg['From'] = from_addr
        msg['To'] = to_addr

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_addr, [to_addr], msg.as_string())

    # ------------------------------------------------------------------
    # Scheduler controls (APScheduler)
    # ------------------------------------------------------------------
    def start_scheduler(self):
        interval_min = int(self.app.config.get('INBOX_CHECK_INTERVAL_MINUTES', 120) or 120)

        # Inbox digest (F5e) — daily cron job
        import config as cfg
        digest_enabled = getattr(cfg, 'INBOX_DIGEST_ENABLED', True)
        digest_hour = getattr(cfg, 'INBOX_DIGEST_SEND_HOUR', 17)
        digest_minute = getattr(cfg, 'INBOX_DIGEST_SEND_MINUTE', 0)

        self.scheduler = build_scheduler(
            timezone=timezone.utc,
            heartbeat_fn=lambda: self.safe_job('heartbeat', self.job_heartbeat),
            mrn_fn=lambda: self.safe_job('mrn_reader', self.job_mrn_reader),
            inbox_fn=lambda: self.safe_job('inbox_check', self.job_inbox_check),
            inbox_minutes=interval_min,
            digest_fn=(lambda: self.safe_job('inbox_digest', self.job_inbox_digest))
                      if digest_enabled else None,
            digest_hour=digest_hour,
            digest_minute=digest_minute,
            callback_fn=lambda: self.safe_job('callback_check', self.job_callback_check),
            overdue_lab_fn=lambda: self.safe_job('overdue_lab_check', self.job_overdue_lab_check),
            xml_archive_fn=lambda: self.safe_job('xml_archive_cleanup', self.job_xml_archive_cleanup),
            xml_poll_fn=lambda: self.safe_job('xml_poll', self.job_xml_poll),
            weekly_summary_fn=lambda: self.safe_job('weekly_summary', self.job_weekly_summary),
            monthly_billing_fn=lambda: self.safe_job('monthly_billing', self.job_monthly_billing),
            deactivation_fn=lambda: self.safe_job('deactivation_check', self.job_deactivation_check),
        )
        self.scheduler.start()
        logger.info('APScheduler started')

    def _start_xml_observer(self):
        """Start the watchdog file observer for clinical summary XMLs."""
        active = self.read_active_user()
        user_id = active.get('user_id') or 0
        started = start_xml_watcher(user_id)
        if not started:
            logger.info('Watchdog not available — XML polling fallback active via scheduler')

    def pause(self):
        if self.scheduler and not self.paused:
            self.scheduler.pause()
            self.paused = True
            logger.info('Agent paused from tray/HTTP control')

    def resume(self):
        if self.scheduler and self.paused:
            self.scheduler.resume()
            self.paused = False
            logger.info('Agent resumed from tray/HTTP control')

    def trigger_inbox_check(self):
        self.safe_job('manual_inbox_check', self.job_inbox_check)

    # ------------------------------------------------------------------
    # HTTP status server (port 5001)
    # ------------------------------------------------------------------
    def _status_payload(self):
        jobs = []
        if self.scheduler:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                })

        return {
            'ok': True,
            'pid': self.pid,
            'started_at': self.started_at.isoformat(),
            'paused': self.paused,
            'scheduler_running': bool(self.scheduler and self.scheduler.running),
            'last_heartbeat': self.last_heartbeat_at.isoformat() if self.last_heartbeat_at else None,
            'active_user': self.read_active_user(),
            'jobs': jobs,
        }

    def start_http_server(self):
        service = self

        class StatusHandler(BaseHTTPRequestHandler):
            def _send_json(self, payload, status=200):
                body = json.dumps(payload).encode('utf-8')
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path in ('/', '/status'):
                    self._send_json(service._status_payload(), 200)
                    return
                self._send_json({'ok': False, 'error': 'Not found'}, 404)

            def do_POST(self):
                if self.path == '/pause':
                    service.pause()
                    self._send_json({'ok': True, 'message': 'paused'})
                    return
                if self.path == '/resume':
                    service.resume()
                    self._send_json({'ok': True, 'message': 'resumed'})
                    return
                if self.path == '/check-inbox':
                    service.trigger_inbox_check()
                    self._send_json({'ok': True, 'message': 'inbox check triggered'})
                    return
                if self.path == '/quit':
                    self._send_json({'ok': True, 'message': 'shutdown requested'})
                    threading.Thread(target=service.stop, daemon=True).start()
                    return
                self._send_json({'ok': False, 'error': 'Not found'}, 404)

            def log_message(self, fmt, *args):
                logger.info('HTTP 5001 - ' + fmt % args)

        self.http_server = ThreadingHTTPServer(('127.0.0.1', 5001), StatusHandler)
        self.http_thread = threading.Thread(target=self.http_server.serve_forever, daemon=True)
        self.http_thread.start()
        logger.info('Agent HTTP status server started on http://127.0.0.1:5001/status')

    # ------------------------------------------------------------------
    # Tray icon (pystray)
    # ------------------------------------------------------------------
    def _create_tray_image(self):
        if not Image or not ImageDraw:
            return None
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((4, 4, 60, 60), fill=(27, 58, 107, 255))
        draw.text((18, 22), 'NP', fill=(255, 255, 255, 255))
        return img

    def _open_app(self, icon=None, item=None):
        webbrowser.open('http://127.0.0.1:5000')

    def _pause_action(self, icon=None, item=None):
        self.pause()

    def _resume_action(self, icon=None, item=None):
        self.resume()

    def _check_inbox_action(self, icon=None, item=None):
        self.trigger_inbox_check()

    def _view_status_action(self, icon=None, item=None):
        webbrowser.open('http://127.0.0.1:5001/status')

    def _calibrate_mrn_action(self, icon=None, item=None):
        calibrate_mrn_reader()

    def _quit_action(self, icon=None, item=None):
        self.stop()
        if icon is not None:
            icon.stop()

    def run_tray(self):
        if not pystray or not TrayItem:
            logger.warning('pystray not available, running without tray icon')
            while not self.shutdown_event.is_set():
                time.sleep(0.5)
            return

        menu = pystray.Menu(
            TrayItem('Open', self._open_app),
            TrayItem('Pause', self._pause_action),
            TrayItem('Resume', self._resume_action),
            TrayItem('Check Inbox', self._check_inbox_action),
            TrayItem('Calibrate MRN Reader', self._calibrate_mrn_action),
            TrayItem('View Status', self._view_status_action),
            TrayItem('Quit', self._quit_action),
        )

        self.tray_icon = pystray.Icon('NP Companion Agent', self._create_tray_image(), 'NP Companion Agent', menu)
        self.tray_icon.run()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self):
        logger.info('Agent starting...')

        recovery_summary = self.perform_crash_recovery()
        self.write_startup_log(
            crash_recovered=bool(recovery_summary),
            recovery_details=recovery_summary,
        )

        self.start_scheduler()
        self.start_http_server()
        self._start_xml_observer()
        logger.info(f'Agent running (PID {self.pid})')

    def start_headless(self):
        """
        Start the agent without blocking on pystray.
        Used by launcher.py — the tray icon is managed by the launcher's
        main thread instead.
        """
        logger.info('Agent starting (headless)...')

        recovery_summary = self.perform_crash_recovery()
        self.write_startup_log(
            crash_recovered=bool(recovery_summary),
            recovery_details=recovery_summary,
        )

        self.start_scheduler()
        self.start_http_server()
        self._start_xml_observer()
        logger.info(f'Agent running headless (PID {self.pid})')

    def stop(self):
        if self.shutdown_event.is_set():
            return

        self.shutdown_event.set()

        try:
            if self.xml_observer:
                self.xml_observer.stop()
                self.xml_observer.join(timeout=3)
        except Exception as e:
            logger.warning(f'XML observer shutdown warning: {e}')

        try:
            if self.scheduler:
                self.scheduler.shutdown(wait=False)
        except Exception as e:
            logger.warning(f'Scheduler shutdown warning: {e}')

        try:
            if self.http_server:
                self.http_server.shutdown()
                self.http_server.server_close()
        except Exception as e:
            logger.warning(f'HTTP server shutdown warning: {e}')

        self.write_shutdown_log()
        logger.info('Agent stopped.')


def main():
    service = AgentService()

    try:
        service.start()
        service.run_tray()
    except KeyboardInterrupt:
        logger.info('Agent received shutdown signal (Ctrl+C)')
    except Exception as e:
        tb_text = traceback.format_exc()
        logger.critical(f'Agent crashed: {e}\n{tb_text}')
        service.log_agent_error('main', str(e), tb_text=tb_text)
    finally:
        service.stop()


if __name__ == '__main__':
    main()

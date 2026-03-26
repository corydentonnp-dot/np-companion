"""
CareCompanion — Background Agent

File location: carecompanion/agent.py (project root)

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
from datetime import date, datetime, timedelta, timezone
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
                f'CareCompanion found {pending_count} incomplete time session(s) from a prior crash.\n\n'
                'Do you want to close them now using an estimated end time?\n'
                'Choose No to leave them open for manual review.'
            )
            result = messagebox.askyesno('CareCompanion Crash Recovery', msg)
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
            now = datetime.now()  # naive local time — matches how deactivate_at is stored
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

    def job_delayed_message_sender(self):
        """F18: check for pending delayed messages ready to send."""
        from models import db
        from models.message import DelayedMessage

        with self.app.app_context():
            now = datetime.now(timezone.utc)
            due = (
                DelayedMessage.query
                .filter(
                    DelayedMessage.status == 'pending',
                    DelayedMessage.scheduled_send_at <= now,
                )
                .all()
            )
            for msg in due:
                try:
                    # Deliver via Pushover push notification (de-identified)
                    from agent.notifier import _send_pushover
                    import config
                    user_key = getattr(config, 'PUSHOVER_USER_KEY', '')
                    api_token = getattr(config, 'PUSHOVER_API_TOKEN', '')
                    if user_key and api_token:
                        _send_pushover(
                            user_key, api_token,
                            title='CareCompanion — Scheduled Message',
                            message=f'Delayed message ready for {msg.recipient_identifier}. Open CareCompanion to review.',
                        )
                    else:
                        logger.warning('Pushover not configured — delayed message %d notification skipped', msg.id)
                    # NOTE: Actual NetPractice in-app delivery requires AC automation
                    # on the work PC. For now, Pushover alerts the provider to send manually.
                    msg.status = 'sent'
                    msg.sent_at = datetime.now(timezone.utc)
                    logger.info(f'Delayed message {msg.id} marked sent (recipient={msg.recipient_identifier})')
                except Exception:
                    msg.status = 'failed'
                    logger.exception(f'Delayed message {msg.id} send failed')
            if due:
                db.session.commit()

    def job_eod_check(self):
        """F20: run end-of-day checks and send notifications for all active users."""
        from models.user import User

        with self.app.app_context():
            users = User.query.filter_by(is_active_account=True).all()
            for user in users:
                try:
                    from agent.eod_checker import send_eod_notification
                    send_eod_notification(user.id)
                except Exception:
                    logger.exception(f'EOD check failed for user {user.id}')

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

    def job_drug_recall_scan(self):
        """NEW-A: daily scan of active patient medications against FDA recalls."""
        from models import db
        from models.patient import PatientMedication
        from models.notification import Notification
        from models.user import User

        with self.app.app_context():
            users = User.query.filter_by(is_active_account=True).all()
            for user in users:
                try:
                    # Get unique active drug names for this provider
                    rows = (
                        db.session.query(
                            PatientMedication.drug_name,
                            PatientMedication.rxnorm_cui,
                        )
                        .filter(
                            PatientMedication.user_id == user.id,
                            PatientMedication.status == 'active',
                        )
                        .distinct()
                        .limit(100)
                        .all()
                    )
                    if not rows:
                        continue

                    drug_list = [
                        {'drug_name': r.drug_name, 'rxcui': r.rxnorm_cui or ''}
                        for r in rows if r.drug_name
                    ]

                    from app.services.api.openfda_recalls import OpenFDARecallsService
                    svc = OpenFDARecallsService(db)
                    results = svc.check_drug_list_for_recalls(drug_list)

                    # Only alert on critical/high priority recalls
                    alerts = [r for r in results if r.get('alert_priority') in ('critical', 'high')]
                    if not alerts:
                        continue

                    # Build a concise notification message
                    drug_names = list({a.get('product_description', 'Unknown')[:60] for a in alerts})
                    msg = (
                        f"FDA Drug Recall Alert: {len(alerts)} active recall(s) found — "
                        f"{', '.join(drug_names[:5])}"
                    )
                    if len(drug_names) > 5:
                        msg += f" and {len(drug_names) - 5} more"

                    notif = Notification(
                        user_id=user.id,
                        sender_id=None,
                        message=msg,
                        template_name='drug_recall',
                    )
                    db.session.add(notif)
                    db.session.commit()
                    logger.info(f'Drug recall alert created for user {user.id}: {len(alerts)} recall(s)')

                except Exception as e:
                    logger.error(f'Drug recall scan failed for user {user.id}: {e}')

    def job_auto_scrape(self):
        """Nightly auto-scrape: pull tomorrow's schedule from webPRACTICE.

        Runs at the configured scrape_time (default 18:00) for all active
        users with NetPractice credentials.  Uses TOTP for automatic MFA
        if the secret is configured.
        """
        import asyncio
        from models import db
        from models.user import User
        from scrapers.netpractice import NetPracticeScraper

        with self.app.app_context():
            users = User.query.filter_by(is_active_account=True).all()
            scraper = NetPracticeScraper(self.app)
            tomorrow = (date.today() + timedelta(days=1))

            for user in users:
                if not user.has_np_credentials():
                    continue
                if not user.nav_steps:
                    continue

                try:
                    logger.info(
                        f'Auto-scrape: pulling tomorrow ({tomorrow}) for {user.username}'
                    )
                    loop = asyncio.new_event_loop()
                    try:
                        loop.run_until_complete(
                            scraper._scrape_date(user.id, tomorrow)
                        )
                    finally:
                        loop.close()

                    # Send success notification
                    try:
                        from agent.notifier import send_inbox_notification
                        import json as _json
                        status_path = os.path.join(
                            self.app.root_path, 'data', 'np_scrape_status.json'
                        )
                        if os.path.exists(status_path):
                            with open(status_path, 'r') as f:
                                status = _json.load(f)
                            count = status.get('appointment_count', 0)
                            send_inbox_notification(
                                user.id,
                                f"Tomorrow's schedule scraped: {count} appointments",
                            )
                    except Exception:
                        pass

                except Exception as e:
                    logger.error(f'Auto-scrape failed for {user.username}: {e}')
                    try:
                        from agent.notifier import send_inbox_notification
                        send_inbox_notification(
                            user.id,
                            f'Schedule scrape failed: {e}',
                        )
                    except Exception:
                        pass

    def job_previsit_billing(self):
        """Phase 15.7: nightly pre-compute billing opportunities for tomorrow's schedule.
        Fixed: now populates patient_data from actual DB records instead of empty defaults."""
        from models import db
        from models.user import User
        from models.schedule import Schedule
        from models.patient import (
            PatientRecord, PatientMedication, PatientDiagnosis,
            PatientAllergy, PatientImmunization, PatientVitals,
            PatientLabResult, PatientSocialHistory,
        )
        from models.billing import BillingOpportunity
        from billing_engine.shared import hash_mrn

        with self.app.app_context():
            tomorrow = (date.today() + timedelta(days=1))
            users = User.query.filter_by(is_active_account=True).all()

            for user in users:
                try:
                    appts = (
                        Schedule.query
                        .filter_by(user_id=user.id, appointment_date=tomorrow)
                        .all()
                    )
                    if not appts:
                        continue

                    from app.services.billing_rules import BillingRulesEngine
                    engine = BillingRulesEngine(db)

                    for appt in appts:
                        mrn = appt.patient_mrn or ""
                        if not mrn:
                            continue

                        patient = PatientRecord.query.filter_by(
                            user_id=user.id, mrn=mrn
                        ).first()

                        # Build patient_data from actual DB records
                        diagnoses = []
                        medications = []
                        vitals = {}
                        immunizations = []
                        lab_results = []
                        social_history = {}
                        insurer_type = "unknown"
                        awv_history = {}
                        discharge_date = None
                        is_pregnant = False

                        if patient:
                            insurer_type = patient.insurer_type or "unknown"
                            awv_history = {"last_awv_date": patient.last_awv_date}
                            discharge_date = patient.last_discharge_date

                            # Diagnoses from PatientDiagnosis
                            dx_rows = PatientDiagnosis.query.filter_by(
                                user_id=user.id, mrn=mrn
                            ).all()
                            for dx in dx_rows:
                                diagnoses.append({
                                    "icd10_code": dx.icd10_code or "",
                                    "diagnosis_name": dx.diagnosis_name or "",
                                    "status": dx.status or "active",
                                })
                                # Pregnancy O-code detection (15.6)
                                code = (dx.icd10_code or "").upper().strip()
                                if code and code[0] == 'O' and len(code) >= 3 and dx.status == 'active':
                                    is_pregnant = True

                            # Medications from PatientMedication
                            med_rows = PatientMedication.query.filter_by(
                                user_id=user.id, mrn=mrn
                            ).all()
                            for med in med_rows:
                                medications.append({
                                    "drug_name": med.drug_name or "",
                                    "rxnorm_cui": med.rxnorm_cui or "",
                                    "dosage": med.dosage or "",
                                    "status": med.status or "active",
                                })

                            # Latest vitals from PatientVitals
                            latest_vitals = PatientVitals.query.filter_by(
                                user_id=user.id, mrn=mrn
                            ).order_by(PatientVitals.measured_at.desc()).limit(20).all()
                            for v in latest_vitals:
                                key = (v.vital_name or "").lower().replace(" ", "_")
                                if key and key not in vitals:
                                    vitals[key] = v.vital_value

                            # Immunizations from PatientImmunization
                            imm_rows = PatientImmunization.query.filter_by(
                                user_id=user.id, mrn=mrn
                            ).all()
                            for imm in imm_rows:
                                immunizations.append({
                                    "vaccine_name": imm.vaccine_name or "",
                                    "date_given": str(imm.date_given) if imm.date_given else "",
                                })

                            # Lab results from PatientLabResult
                            lab_rows = PatientLabResult.query.filter_by(
                                user_id=user.id, mrn=mrn
                            ).order_by(PatientLabResult.result_date.desc()).all()
                            for lab in lab_rows:
                                lab_results.append({
                                    "test_name": lab.test_name or "",
                                    "loinc_code": lab.loinc_code or "",
                                    "result_value": lab.result_value or "",
                                    "result_date": str(lab.result_date) if lab.result_date else "",
                                    "result_flag": lab.result_flag or "normal",
                                })

                            # Social history from PatientSocialHistory
                            social = PatientSocialHistory.query.filter_by(
                                user_id=user.id, mrn=mrn
                            ).first()
                            if social:
                                social_history = {
                                    "tobacco_status": social.tobacco_status or "unknown",
                                    "tobacco_pack_years": social.tobacco_pack_years,
                                    "alcohol_status": social.alcohol_status or "unknown",
                                    "alcohol_frequency": social.alcohol_frequency or "",
                                }

                            # Populate last_awv_date if missing
                            if not patient.last_awv_date:
                                from agent.clinical_summary_parser import populate_last_awv_date
                                populate_last_awv_date(patient)

                        patient_data = {
                            "mrn": mrn,
                            "user_id": user.id,
                            "visit_date": tomorrow,
                            "visit_type": appt.visit_type or "office_visit",
                            "diagnoses": diagnoses,
                            "medications": medications,
                            "insurer_type": insurer_type,
                            "awv_history": awv_history,
                            "vitals": vitals,
                            "immunizations": immunizations,
                            "lab_results": lab_results,
                            "social_history": social_history,
                            "is_pregnant": is_pregnant,
                            "discharge_date": discharge_date,
                            "ccm_minutes_this_month": 0,
                            "face_to_face_minutes": 0,
                            "prior_encounters_count": 0,
                            "behavioral_dx_minutes": 0,
                            "rpm_enrolled": False,
                            "patient_dob": getattr(patient, "patient_dob", "") if patient else "",
                            "patient_sex": getattr(patient, "patient_sex", "") if patient else "",
                        }

                        # Phase 25.4: populate telehealth + BHI fields from CommunicationLog
                        try:
                            from app.services.telehealth_engine import get_telehealth_fields
                            from billing_engine.shared import hash_mrn as _hash_mrn_tele
                            tele_fields = get_telehealth_fields(
                                _hash_mrn_tele(mrn), user.id, tomorrow,
                            )
                            patient_data.update(tele_fields)
                        except Exception:
                            pass

                        # Phase 23.C2: populate monitoring schedule before billing
                        try:
                            from app.services.monitoring_rule_engine import MonitoringRuleEngine
                            from billing_engine.shared import hash_mrn as _hash_mrn
                            mon_engine = MonitoringRuleEngine(db)
                            mrn_hash = _hash_mrn(mrn)
                            mon_engine.populate_patient_schedule(
                                mrn_hash, user.id, medications, diagnoses, lab_results,
                            )
                            overdue = mon_engine.get_overdue_monitoring(mrn_hash)
                            patient_data["monitoring_schedule"] = [
                                {
                                    "lab_name": e.lab_name,
                                    "lab_code": e.lab_code,
                                    "next_due_date": str(e.next_due_date) if e.next_due_date else "",
                                    "priority": e.priority,
                                    "source": e.source,
                                }
                                for e in overdue
                            ]
                        except Exception as mon_exc:
                            logger.debug("Monitoring schedule population skipped: %s", mon_exc)
                            patient_data["monitoring_schedule"] = []

                        # Phase 32.4 — Pre-compute risk scores for tomorrow's patients
                        try:
                            from app.services.calculator_engine import CalculatorEngine
                            calc_engine = CalculatorEngine()
                            calc_engine.run_auto_scores(mrn, user.id)
                        except Exception as calc_exc:
                            logger.debug("Auto risk scores precompute skipped: %s", calc_exc)

                        # Phase 35.4 — Create care gaps from calculator threshold alerts
                        try:
                            from agent.caregap_engine import evaluate_calculator_care_gaps
                            from models.patient import PatientRecord as _PR
                            _pt = _PR.query.filter_by(mrn=mrn).first()
                            _pt_age = calc_engine._age_from_dob(_pt.date_of_birth) if _pt else None
                            evaluate_calculator_care_gaps(mrn, user.id, _pt_age, self.app)
                        except Exception as cg_exc:
                            logger.debug("Calculator care gaps creation skipped: %s", cg_exc)

                        opps = engine.evaluate_patient(patient_data)
                        for opp in opps:
                            # Avoid duplicates: skip if same type already exists for this patient/date
                            existing = BillingOpportunity.query.filter_by(
                                user_id=user.id,
                                patient_mrn_hash=opp.patient_mrn_hash,
                                visit_date=tomorrow,
                                opportunity_type=opp.opportunity_type,
                            ).first()
                            if not existing:
                                db.session.add(opp)

                    db.session.commit()
                    logger.info(f'Pre-visit billing computed for user {user.id}, date {tomorrow}')

                except Exception as e:
                    db.session.rollback()
                    logger.error(f'Pre-visit billing failed for user {user.id}: {e}')

    def job_viis_previsit(self):
        """VIIS: Nightly batch lookup for tomorrow's scheduled patients with open vaccine care gaps."""
        from app.services.viis_batch import run_viis_batch
        from models.user import User

        with self.app.app_context():
            users = User.query.filter_by(is_active_account=True).all()
            for user in users:
                try:
                    run_viis_batch(user.id, self.app)
                except Exception as e:
                    logger.error(f'VIIS pre-visit batch failed for user {user.id}: {e}')

    def job_daily_backup(self):
        """Phase 18: Nightly database backup with PRAGMA integrity_check."""
        import shutil
        import sqlite3
        import config as cfg

        with self.app.app_context():
            db_path = os.path.join(os.path.dirname(__file__), 'data', 'carecompanion.db')
            backup_dir = os.path.join(os.path.dirname(__file__), 'data', 'backups')
            os.makedirs(backup_dir, exist_ok=True)

            stamp = date.today().strftime('%Y%m%d')
            backup_path = os.path.join(backup_dir, f'carecompanion_{stamp}.db')

            try:
                shutil.copy2(db_path, backup_path)
                logger.info('Database backup created: %s', backup_path)
            except Exception as e:
                logger.error('Database backup copy failed: %s', e)
                self._backup_alert(f'Backup copy failed: {e}')
                return

            # Integrity check on the backup copy
            try:
                conn = sqlite3.connect(backup_path)
                result = conn.execute('PRAGMA integrity_check').fetchone()
                conn.close()

                if result and result[0] == 'ok':
                    logger.info('Backup integrity check passed: %s', backup_path)
                else:
                    msg = f'Backup integrity check FAILED: {result}'
                    logger.error(msg)
                    self._backup_alert(msg)
            except Exception as e:
                logger.error('Backup integrity check error: %s', e)
                self._backup_alert(f'Backup integrity check error: {e}')

            # Prune backups older than 30 days
            cutoff = date.today() - timedelta(days=30)
            for fname in os.listdir(backup_dir):
                if fname.startswith('carecompanion_') and fname.endswith('.db'):
                    try:
                        fdate = datetime.strptime(fname[12:20], '%Y%m%d').date()
                        if fdate < cutoff:
                            os.remove(os.path.join(backup_dir, fname))
                            logger.info('Pruned old backup: %s', fname)
                    except (ValueError, OSError):
                        pass

    def _backup_alert(self, message):
        """Send a Pushover alert on backup failure."""
        try:
            import config as cfg
            user_key = getattr(cfg, 'PUSHOVER_USER_KEY', '')
            api_token = getattr(cfg, 'PUSHOVER_API_TOKEN', '')
            if user_key and api_token:
                from agent.notifier import _send_pushover
                _send_pushover(
                    user_key, api_token,
                    title='CareCompanion Backup Alert',
                    message=message,
                    priority=1,
                )
        except Exception as e:
            logger.error('Backup Pushover alert failed: %s', e)

    def job_escalation_check(self):
        """F21b: Re-send Pushover for unacknowledged critical notifications."""
        with self.app.app_context():
            from agent.notifier import check_escalations
            check_escalations()

    def job_tcm_deadline_checker(self):
        """Phase 19.14: Expire overdue TCM entries and alert on approaching deadlines."""
        with self.app.app_context():
            from models import db
            from models.tcm import TCMWatchEntry
            from datetime import date, timedelta

            today = date.today()
            active = TCMWatchEntry.query.filter_by(status='active').all()
            expired_count = 0
            alert_count = 0

            for entry in active:
                # Expire entries past 14-day visit deadline
                if entry.fourteen_day_visit_deadline and today > entry.fourteen_day_visit_deadline:
                    if not entry.face_to_face_completed:
                        entry.status = 'expired'
                        entry.tcm_code_eligible = 'expired'
                        expired_count += 1
                        continue

                # Alert on 2-day contact deadline approaching (within 1 day)
                if (entry.two_day_deadline and not entry.two_day_contact_completed
                        and today >= entry.two_day_deadline - timedelta(days=1)):
                    alert_count += 1
                    try:
                        from agent.notifier import send_push
                        send_push(
                            entry.user_id,
                            f'TCM Alert: 2-day contact deadline approaching for patient '
                            f'{entry.patient_mrn_hash[:8]}… at {entry.discharge_facility}',
                            priority='high',
                        )
                    except Exception:
                        pass

            if expired_count or alert_count:
                db.session.commit()
                logger.info(f'TCM deadline check: {expired_count} expired, {alert_count} alerts sent')

    def job_ccm_month_end(self):
        """Phase 19.14: Mark CCM billing readiness at month end, log summary."""
        with self.app.app_context():
            from models import db
            from models.ccm import CCMEnrollment
            from datetime import date

            today = date.today()
            # Process previous month
            if today.month == 1:
                year, month = today.year - 1, 12
            else:
                year, month = today.year, today.month - 1
            month_str = f'{year}-{month:02d}'

            active = CCMEnrollment.query.filter_by(status='active').all()
            billed_count = 0
            not_ready_count = 0

            for enrollment in active:
                if enrollment.is_billing_ready(month_str):
                    enrollment.last_billed_month = month_str
                    enrollment.total_billed_months = (enrollment.total_billed_months or 0) + 1
                    billed_count += 1
                else:
                    not_ready_count += 1

            db.session.commit()
            logger.info(f'CCM month-end ({month_str}): {billed_count} billed, '
                        f'{not_ready_count} not ready, ${billed_count * 62} estimated revenue')

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
            f"CareCompanion — Monthly Billing Report ({month_label})\n\n"
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
        msg['Subject'] = f"CareCompanion Monthly Billing Report — {month_label}"
        msg['From'] = from_addr
        msg['To'] = to_addr

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_addr, [to_addr], msg.as_string())

    def _send_weekly_email(self, user, summary):
        """Send a weekly summary email via configured SMTP (HTML format)."""
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

        week = summary['week_start']
        patients = summary['patients']
        total_h = summary['total_hours']
        f2f_h = summary['total_f2f']
        avg_min = summary.get('avg_visit_min', 0)
        oncall = summary['oncall_calls']
        inbox = summary['inbox_items']
        captured = summary.get('billing_captured', 0)
        missed = summary.get('billing_missed', 0)
        rev_captured = summary.get('billing_revenue_captured', 0)
        rev_missed = summary.get('billing_revenue_missed', 0)
        notable = summary.get('notable', '')

        html = f"""<html><body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:0 auto;">
<h2 style="color:#0D7377;border-bottom:2px solid #0D7377;padding-bottom:8px;">
CareCompanion &mdash; Weekly Summary</h2>
<p style="color:#666;font-size:14px;">Week of {week}</p>

<table style="width:100%;border-collapse:collapse;margin:16px 0;">
<tr>
  <td style="padding:12px;background:#f8fafc;border-radius:6px;text-align:center;width:25%;">
    <div style="font-size:28px;font-weight:700;color:#0D7377;">{patients}</div>
    <div style="font-size:12px;color:#666;">Patients Seen</div></td>
  <td style="padding:12px;background:#f8fafc;border-radius:6px;text-align:center;width:25%;">
    <div style="font-size:28px;font-weight:700;color:#0D7377;">{avg_min}</div>
    <div style="font-size:12px;color:#666;">Avg Min/Visit</div></td>
  <td style="padding:12px;background:#f8fafc;border-radius:6px;text-align:center;width:25%;">
    <div style="font-size:28px;font-weight:700;color:#0D7377;">{total_h}</div>
    <div style="font-size:12px;color:#666;">Chart Hours</div></td>
  <td style="padding:12px;background:#f8fafc;border-radius:6px;text-align:center;width:25%;">
    <div style="font-size:28px;font-weight:700;color:#0D7377;">{f2f_h}</div>
    <div style="font-size:12px;color:#666;">F2F Hours</div></td>
</tr>
</table>

<table style="width:100%;border-collapse:collapse;margin:16px 0;">
<tr>
  <td style="padding:8px 12px;border-bottom:1px solid #eee;font-size:14px;">&#128229; Inbox Items Processed</td>
  <td style="padding:8px 12px;border-bottom:1px solid #eee;font-size:14px;text-align:right;font-weight:600;">{inbox}</td>
</tr>
<tr>
  <td style="padding:8px 12px;border-bottom:1px solid #eee;font-size:14px;">&#128222; On-Call Notes</td>
  <td style="padding:8px 12px;border-bottom:1px solid #eee;font-size:14px;text-align:right;font-weight:600;">{oncall}</td>
</tr>
<tr>
  <td style="padding:8px 12px;border-bottom:1px solid #eee;font-size:14px;">&#9989; Billing Captured</td>
  <td style="padding:8px 12px;border-bottom:1px solid #eee;font-size:14px;text-align:right;font-weight:600;color:#16a34a;">{captured} (~${rev_captured:,.0f})</td>
</tr>
<tr>
  <td style="padding:8px 12px;border-bottom:1px solid #eee;font-size:14px;">&#10060; Billing Missed</td>
  <td style="padding:8px 12px;border-bottom:1px solid #eee;font-size:14px;text-align:right;font-weight:600;color:#dc2626;">{missed} (~${rev_missed:,.0f})</td>
</tr>
</table>

{"<p style='margin:16px 0;padding:12px;background:#eff6ff;border-radius:6px;font-size:14px;'>" + notable + "</p>" if notable else ""}

<p style="font-size:12px;color:#999;margin-top:24px;border-top:1px solid #eee;padding-top:12px;">
This is an automated summary from CareCompanion. Log in to view full metrics.</p>
</body></html>"""

        msg = MIMEText(html, 'html')
        msg['Subject'] = f"CareCompanion Weekly Summary — {week}"
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

        # Auto-scrape time from NP settings (defaults to 18:00)
        try:
            np_settings_path = os.path.join(
                self.app.root_path, 'data', 'np_settings.json'
            )
            if os.path.exists(np_settings_path):
                with open(np_settings_path, 'r') as f:
                    np_cfg = json.load(f)
                scrape_time = np_cfg.get('scrape_time', '18:00')
            else:
                scrape_time = '18:00'
            scrape_hour, scrape_minute = (int(x) for x in scrape_time.split(':'))
        except Exception:
            scrape_hour, scrape_minute = 18, 0

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
            delayed_message_fn=lambda: self.safe_job('delayed_message_sender', self.job_delayed_message_sender),
            eod_check_fn=lambda: self.safe_job('eod_check', self.job_eod_check),
            drug_recall_fn=lambda: self.safe_job('drug_recall_scan', self.job_drug_recall_scan),
            auto_scrape_fn=lambda: self.safe_job('auto_scrape', self.job_auto_scrape),
            auto_scrape_hour=scrape_hour,
            auto_scrape_minute=scrape_minute,
            previsit_billing_fn=lambda: self.safe_job('previsit_billing', self.job_previsit_billing),
            daily_backup_fn=lambda: self.safe_job('daily_backup', self.job_daily_backup),
            escalation_fn=lambda: self.safe_job('escalation_check', self.job_escalation_check),
            viis_previsit_fn=lambda: self.safe_job('viis_previsit', self.job_viis_previsit),
            viis_previsit_hour=getattr(config, 'VIIS_BATCH_HOUR', 18),
            viis_previsit_minute=getattr(config, 'VIIS_BATCH_MINUTE', 30),
            tcm_deadline_fn=lambda: self.safe_job('tcm_deadline_check', self.job_tcm_deadline_checker),
            ccm_month_end_fn=lambda: self.safe_job('ccm_month_end', self.job_ccm_month_end),
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

        self.tray_icon = pystray.Icon('CareCompanion Agent', self._create_tray_image(), 'CareCompanion Agent', menu)
        self.tray_icon.run()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def _write_pid_file(self):
        """Write own PID to data/agent.pid so other code can detect a running agent."""
        try:
            pid_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
            os.makedirs(pid_dir, exist_ok=True)
            pid_path = os.path.join(pid_dir, 'agent.pid')
            with open(pid_path, 'w') as f:
                f.write(str(self.pid))
        except Exception as e:
            logger.warning(f'Failed to write PID file: {e}')

    def _delete_pid_file(self):
        """Remove data/agent.pid on clean shutdown."""
        try:
            pid_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'agent.pid')
            if os.path.exists(pid_path):
                os.remove(pid_path)
        except Exception as e:
            logger.warning(f'Failed to delete PID file: {e}')

    def start(self):
        logger.info('Agent starting...')
        self._write_pid_file()

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
        Used by launcher.py -- the tray icon is managed by the launcher's
        main thread instead.
        """
        logger.info('Agent starting (headless)...')
        self._write_pid_file()

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

        self._delete_pid_file()
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

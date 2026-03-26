"""
CareCompanion — Agent Scheduler

Centralized APScheduler setup for the background agent.
"""

from apscheduler.schedulers.background import BackgroundScheduler


def build_scheduler(*, timezone, heartbeat_fn, mrn_fn, inbox_fn, inbox_minutes=120,
                    digest_fn=None, digest_hour=17, digest_minute=0,
                    callback_fn=None,
                    overdue_lab_fn=None,
                    xml_archive_fn=None,
                    xml_poll_fn=None,
                    weekly_summary_fn=None,
                    monthly_billing_fn=None,
                    deactivation_fn=None,
                    delayed_message_fn=None,
                    eod_check_fn=None,
                    drug_recall_fn=None,
                    previsit_billing_fn=None,
                    daily_backup_fn=None,
                    escalation_fn=None,
                    auto_scrape_fn=None,
                    auto_scrape_hour=18,
                    auto_scrape_minute=0,
                    viis_previsit_fn=None,
                    viis_previsit_hour=18,
                    viis_previsit_minute=30,
                    **kwargs):
    """
    Build and configure a BackgroundScheduler with standard NP jobs.

    Parameters
    ----------
    timezone : tzinfo or str
        Timezone for trigger calculations.
    heartbeat_fn : callable
        Function called every 30 seconds.
    mrn_fn : callable
        Function called every 3 seconds.
    inbox_fn : callable
        Function called every N minutes.
    inbox_minutes : int
        Inbox polling interval in minutes.
    digest_fn : callable or None
        Function called once daily for inbox digest (F5e).
    digest_hour : int
        Hour (0-23) to run digest.
    digest_minute : int
        Minute (0-59) to run digest.
    callback_fn : callable or None
        Function called every 10 minutes to check for upcoming callbacks (F7b).
    overdue_lab_fn : callable or None
        Function called daily at 6 AM to flag overdue lab tracking (F11c).
    xml_archive_fn : callable or None
        Function called daily at 2 AM to clean up old clinical summary XMLs (F11e).
    xml_poll_fn : callable or None
        Function called every 30 seconds to poll the export folder for new XML files (F6d fallback).
    weekly_summary_fn : callable or None
        Function called every Friday at 5 PM to generate and email weekly summary (F13c).
    monthly_billing_fn : callable or None
        Function called on the 1st of each month at 7 AM to generate and email monthly billing report (F14c).
    delayed_message_fn : callable or None
        Function called every 60 seconds to check for pending delayed messages ready to send (F18).
    eod_check_fn : callable or None
        Function called daily at 5:00 PM to run end-of-day checks and send notifications (F20).
    drug_recall_fn : callable or None
        Function called daily at 3:00 AM to scan active patient medications for FDA recalls (NEW-A).
    previsit_billing_fn : callable or None
        Function called daily at 8:00 PM to pre-compute billing opportunities for tomorrow's schedule.
    daily_backup_fn : callable or None
        Function called daily at 1:00 AM to back up the database with integrity verification.
    """
    scheduler = BackgroundScheduler(timezone=timezone)

    scheduler.add_job(
        heartbeat_fn,
        trigger='interval',
        seconds=30,
        id='heartbeat',
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.add_job(
        mrn_fn,
        trigger='interval',
        seconds=3,
        id='mrn_reader',
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.add_job(
        inbox_fn,
        trigger='interval',
        minutes=max(1, int(inbox_minutes or 120)),
        id='inbox_check',
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    if digest_fn is not None:
        scheduler.add_job(
            digest_fn,
            trigger='cron',
            hour=int(digest_hour),
            minute=int(digest_minute),
            id='inbox_digest',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    if callback_fn is not None:
        scheduler.add_job(
            callback_fn,
            trigger='interval',
            minutes=10,
            id='callback_check',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # F11c: daily overdue lab detection at 6:00 AM
    if overdue_lab_fn is not None:
        scheduler.add_job(
            overdue_lab_fn,
            trigger='cron',
            hour=6,
            minute=0,
            id='overdue_lab_check',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # F11e: daily XML clinical summary archive cleanup at 2:00 AM
    if xml_archive_fn is not None:
        scheduler.add_job(
            xml_archive_fn,
            trigger='cron',
            hour=2,
            minute=0,
            id='xml_archive_cleanup',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # F6d: XML export folder polling fallback — every 30 seconds
    if xml_poll_fn is not None:
        scheduler.add_job(
            xml_poll_fn,
            trigger='interval',
            seconds=30,
            id='xml_poll',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # F13c: weekly productivity summary email — Friday at 5:00 PM
    if weekly_summary_fn is not None:
        scheduler.add_job(
            weekly_summary_fn,
            trigger='cron',
            day_of_week='fri',
            hour=17,
            minute=0,
            id='weekly_summary',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # F14c: monthly billing report email — 1st of month at 7:00 AM
    if monthly_billing_fn is not None:
        scheduler.add_job(
            monthly_billing_fn,
            trigger='cron',
            day=1,
            hour=7,
            minute=0,
            id='monthly_billing',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # Scheduled user deactivation check — every 5 minutes
    if deactivation_fn is not None:
        scheduler.add_job(
            deactivation_fn,
            trigger='interval',
            minutes=5,
            id='deactivation_check',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # F18: delayed message sender — every 60 seconds
    if delayed_message_fn is not None:
        scheduler.add_job(
            delayed_message_fn,
            trigger='interval',
            seconds=60,
            id='delayed_message_sender',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # F20: end-of-day checker — daily at 5:00 PM
    if eod_check_fn is not None:
        scheduler.add_job(
            eod_check_fn,
            trigger='cron',
            hour=17,
            minute=0,
            id='eod_check',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # NEW-A: drug recall background scan — daily at 3:00 AM
    if drug_recall_fn is not None:
        scheduler.add_job(
            drug_recall_fn,
            trigger='cron',
            hour=3,
            minute=0,
            id='drug_recall_scan',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # Scraper overhaul: nightly auto-scrape tomorrow's schedule
    if auto_scrape_fn is not None:
        scheduler.add_job(
            auto_scrape_fn,
            trigger='cron',
            hour=int(auto_scrape_hour),
            minute=int(auto_scrape_minute),
            id='auto_scrape',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # Phase 13C: pre-visit billing opportunity computation — daily at 8:00 PM
    if previsit_billing_fn is not None:
        scheduler.add_job(
            previsit_billing_fn,
            trigger='cron',
            hour=20,
            minute=0,
            id='previsit_billing',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # VIIS: pre-visit VIIS batch lookup — daily (default 6:30 PM)
    if viis_previsit_fn is not None:
        scheduler.add_job(
            viis_previsit_fn,
            trigger='cron',
            hour=viis_previsit_hour,
            minute=viis_previsit_minute,
            id='viis_previsit',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # Phase 18: daily database backup with integrity check — 1:00 AM
    if daily_backup_fn is not None:
        scheduler.add_job(
            daily_backup_fn,
            trigger='cron',
            hour=1,
            minute=0,
            id='daily_backup',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # F21b: escalating alerts — check every 2 minutes for unacknowledged critical values
    if escalation_fn is not None:
        scheduler.add_job(
            escalation_fn,
            trigger='interval',
            minutes=2,
            id='escalation_check',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # Phase 19.14: TCM deadline checker — run nightly at 6 AM
    if kwargs.get('tcm_deadline_fn') is not None:
        scheduler.add_job(
            kwargs['tcm_deadline_fn'],
            trigger='cron',
            hour=6,
            minute=0,
            id='tcm_deadline_check',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # Phase 19.14: CCM month-end processing — run on 1st of each month at 2 AM
    if kwargs.get('ccm_month_end_fn') is not None:
        scheduler.add_job(
            kwargs['ccm_month_end_fn'],
            trigger='cron',
            day=1,
            hour=2,
            minute=0,
            id='ccm_month_end',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # XML cleanup — delete expired clinical summary files daily at 2 AM
    try:
        from agent.clinical_summary_parser import run_scheduled_deletions
        scheduler.add_job(
            run_scheduled_deletions,
            trigger='cron',
            hour=2,
            minute=0,
            id='xml_cleanup',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
    except ImportError:
        pass

    return scheduler

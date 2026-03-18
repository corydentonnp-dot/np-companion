"""
NP Companion — API Intelligence Layer Scheduler
File: app/services/api_scheduler.py

Registers background jobs for the API intelligence layer into an
existing APScheduler BackgroundScheduler. Called by agent/scheduler.py
(or directly by app.py) after the base scheduler is built.

Jobs registered here:
  - morning_briefing_prep  — 6:00 AM daily: weather + recalls + PubMed pre-load
  - overnight_visit_prep   — 8:00 PM daily: billing rules engine for next day
  - daily_recall_check     — 5:45 AM daily: OpenFDA recall sweep for active meds
  - weekly_cache_refresh   — Sunday 2:00 AM: flush and rebuild stale API caches

All schedule constants are sourced from app/api_config.py. No magic
numbers here.

Dependencies:
- app/api_config.py (schedule constants)
- app/services/api/open_meteo.py
- app/services/api/openfda_recalls.py
- app/services/api/pubmed.py
- app/services/api/cms_pfs.py
- app/services/api/cache_manager.py
- app/services/billing_rules.py
- models/billing.py (BillingOpportunity)
- models (db)

NP Companion features that rely on this module:
- Morning Briefing (F22) — weather, recalls, PubMed loaded before provider arrives
- Billing Opportunity Engine — overnight pre-visit prep
- Drug Safety Monitor — daily recall sweep
"""

import logging
from datetime import date, timedelta

from app.api_config import (
    MORNING_BRIEFING_HOUR,
    OVERNIGHT_PREP_HOUR,
    DAILY_RECALL_CHECK_HOUR,
    DAILY_RECALL_CHECK_MINUTE,
    WEEKLY_CACHE_REFRESH_DAY,
    WEEKLY_CACHE_REFRESH_HOUR,
    CY2025_CONVERSION_FACTOR,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Job implementations
# ---------------------------------------------------------------------------

def run_morning_briefing_prep(app, db):
    """
    6:00 AM — Fetch weather conditions and check for drug recalls.
    Pre-loads PubMed guidelines for today's scheduled patients.

    Runs inside the Flask app context so models are available.
    """
    with app.app_context():
        logger.info("[api_scheduler] Morning briefing prep starting")
        _run_weather_fetch(db)
        _run_recall_check(db)
        _run_pubmed_preload(db)
        logger.info("[api_scheduler] Morning briefing prep complete")


def run_overnight_visit_prep(app, db):
    """
    8:00 PM — Run the billing rules engine for tomorrow's scheduled patients.
    Creates BillingOpportunity records for the Today View.

    Runs inside the Flask app context so ORM writes succeed.
    """
    with app.app_context():
        tomorrow = date.today() + timedelta(days=1)
        logger.info(
            "[api_scheduler] Overnight visit prep for %s starting", tomorrow
        )
        _run_billing_rules(db, target_date=tomorrow)
        logger.info("[api_scheduler] Overnight visit prep complete")


def run_daily_recall_check(app, db):
    """
    5:45 AM — OpenFDA recall sweep for all active patient medications.
    Fires before morning briefing so alerts are ready at 6:00 AM.
    """
    with app.app_context():
        logger.info("[api_scheduler] Daily recall check starting")
        _run_recall_check(db)
        logger.info("[api_scheduler] Daily recall check complete")


def run_weekly_cache_refresh(app, db):
    """
    Sunday 2:00 AM — Flush stale cache entries and warm up caches for
    APIs that have long TTLs (ICD-10, RxClass, LOINC).
    """
    with app.app_context():
        logger.info("[api_scheduler] Weekly cache refresh starting")
        _flush_stale_caches(db)
        logger.info("[api_scheduler] Weekly cache refresh complete")


# ---------------------------------------------------------------------------
# Scheduler registration
# ---------------------------------------------------------------------------

def register_api_jobs(scheduler, app, db):
    """
    Register all API intelligence layer jobs into an existing APScheduler
    BackgroundScheduler instance.

    Parameters
    ----------
    scheduler : BackgroundScheduler
        The already-configured scheduler from agent/scheduler.py.
    app : Flask
        The Flask application instance (needed for app_context()).
    db : SQLAlchemy
        The shared database instance.

    Usage
    -----
    In agent_service.py or app.py, after build_scheduler():
        from app.services.api_scheduler import register_api_jobs
        register_api_jobs(scheduler, app, db)
    """
    # 6:00 AM — Morning briefing prep (weather + recalls + PubMed)
    scheduler.add_job(
        func=run_morning_briefing_prep,
        kwargs={"app": app, "db": db},
        trigger="cron",
        hour=MORNING_BRIEFING_HOUR,
        minute=0,
        id="api_morning_briefing",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # 8:00 PM — Overnight billing rules engine for next-day visits
    scheduler.add_job(
        func=run_overnight_visit_prep,
        kwargs={"app": app, "db": db},
        trigger="cron",
        hour=OVERNIGHT_PREP_HOUR,
        minute=0,
        id="api_overnight_prep",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # 5:45 AM — Recall check (before morning briefing so alerts are ready)
    scheduler.add_job(
        func=run_daily_recall_check,
        kwargs={"app": app, "db": db},
        trigger="cron",
        hour=DAILY_RECALL_CHECK_HOUR,
        minute=DAILY_RECALL_CHECK_MINUTE,
        id="api_daily_recall",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # Sunday 2:00 AM — Weekly cache flush and warm-up
    scheduler.add_job(
        func=run_weekly_cache_refresh,
        kwargs={"app": app, "db": db},
        trigger="cron",
        day_of_week=WEEKLY_CACHE_REFRESH_DAY,
        hour=WEEKLY_CACHE_REFRESH_HOUR,
        minute=0,
        id="api_weekly_cache",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    logger.info(
        "[api_scheduler] Registered 4 API intelligence jobs: "
        "morning_briefing=%d:00, overnight_prep=%d:00, "
        "recall_check=%d:%02d, cache_refresh=%s %d:00",
        MORNING_BRIEFING_HOUR,
        OVERNIGHT_PREP_HOUR,
        DAILY_RECALL_CHECK_HOUR,
        DAILY_RECALL_CHECK_MINUTE,
        WEEKLY_CACHE_REFRESH_DAY.upper(),
        WEEKLY_CACHE_REFRESH_HOUR,
    )


# ---------------------------------------------------------------------------
# Private job helpers
# ---------------------------------------------------------------------------

def _run_weather_fetch(db):
    """Fetch and cache current weather conditions for the clinic location."""
    try:
        from app.services.api.open_meteo import OpenMeteoService
        svc = OpenMeteoService(db)
        result = svc.get_current_conditions()
        if result:
            temp = result.get("temperature_f")
            desc = result.get("description", "unknown")
            logger.info(
                "[api_scheduler] Weather cached: %s°F, %s", temp, desc
            )
        else:
            logger.warning("[api_scheduler] Weather fetch returned empty result")
    except Exception as exc:
        logger.error("[api_scheduler] Weather fetch failed: %s", exc)


def _run_recall_check(db):
    """
    Check all active patient medications against OpenFDA drug recalls.
    Logs a warning for any Class I or Class II recalls found.
    """
    try:
        from models.patient import PatientMedication
        from app.services.api.openfda_recalls import OpenFDARecallsService

        svc = OpenFDARecallsService(db)

        # Gather distinct active medication names across all patients
        med_names = [
            row[0] for row in
            db.session.query(PatientMedication.drug_name)
            .filter(PatientMedication.is_active.is_(True))
            .distinct()
            .all()
            if row[0]
        ]

        if not med_names:
            logger.info("[api_scheduler] No active medications to check for recalls")
            return

        results = svc.check_drug_list_for_recalls(med_names)
        flagged = [r for r in results if r.get("priority") in ("critical", "high")]

        if flagged:
            logger.warning(
                "[api_scheduler] RECALL ALERT — %d high-priority recall(s) "
                "for active medications: %s",
                len(flagged),
                ", ".join(r.get("drug_name", "?") for r in flagged),
            )
        else:
            logger.info(
                "[api_scheduler] Recall check complete — %d medication(s) checked, "
                "no critical/high-priority recalls",
                len(med_names),
            )
    except Exception as exc:
        logger.error("[api_scheduler] Recall check failed: %s", exc)


def _run_pubmed_preload(db):
    """
    Pre-load PubMed guideline cache for today's scheduled patients'
    top diagnoses. Runs at morning briefing so literature is ready
    when the provider opens the chart.
    """
    try:
        from models.schedule import Schedule
        from models.patient import PatientDiagnosis
        from app.services.api.pubmed import PubMedService

        svc = PubMedService(db)
        today = date.today()

        # Get patient MRN hashes for today's appointments
        scheduled_hashes = [
            row[0] for row in
            db.session.query(Schedule.patient_mrn_hash)
            .filter(Schedule.visit_date == today)
            .distinct()
            .all()
            if row[0]
        ]

        if not scheduled_hashes:
            logger.info("[api_scheduler] No scheduled patients — PubMed pre-load skipped")
            return

        # For each scheduled patient, pre-load guidelines for top 2 diagnoses
        conditions_checked = set()
        for mrn_hash in scheduled_hashes:
            top_dx = (
                db.session.query(PatientDiagnosis.icd10_description)
                .filter(PatientDiagnosis.patient_mrn_hash == mrn_hash)
                .order_by(PatientDiagnosis.id.desc())
                .limit(2)
                .all()
            )
            for (desc,) in top_dx:
                if desc and desc not in conditions_checked:
                    conditions_checked.add(desc)
                    svc.search_guidelines(desc)

        logger.info(
            "[api_scheduler] PubMed pre-load complete — %d condition(s) cached "
            "for %d scheduled patient(s)",
            len(conditions_checked),
            len(scheduled_hashes),
        )
    except Exception as exc:
        logger.error("[api_scheduler] PubMed pre-load failed: %s", exc)


def _run_billing_rules(db, target_date):
    """
    Run the billing rules engine for all patients scheduled on target_date.
    Creates or updates BillingOpportunity records.
    """
    try:
        from models.schedule import Schedule
        from models.patient import PatientRecord
        from models.billing import BillingOpportunity
        from app.services.api.cms_pfs import CMSPhysicianFeeScheduleService
        from app.services.billing_rules import BillingRulesEngine

        cms_svc = CMSPhysicianFeeScheduleService(db)
        engine = BillingRulesEngine(db, cms_pfs_service=cms_svc)

        scheduled = (
            db.session.query(Schedule)
            .filter(Schedule.visit_date == target_date)
            .all()
        )

        if not scheduled:
            logger.info(
                "[api_scheduler] No patients scheduled for %s — billing rules skipped",
                target_date,
            )
            return

        created_count = 0
        for appt in scheduled:
            mrn_hash = appt.patient_mrn_hash
            user_id = appt.user_id

            # Look up full patient record for rule evaluation
            patient_record = (
                db.session.query(PatientRecord)
                .filter(PatientRecord.patient_mrn_hash == mrn_hash)
                .first()
            )
            if not patient_record:
                continue

            # Build patient_data dict expected by BillingRulesEngine
            patient_data = _build_patient_data(db, patient_record, user_id, target_date)

            # Delete stale pending opportunities for this patient+date
            db.session.query(BillingOpportunity).filter(
                BillingOpportunity.patient_mrn_hash == mrn_hash,
                BillingOpportunity.visit_date == target_date,
                BillingOpportunity.status == "pending",
            ).delete(synchronize_session=False)

            opportunities = engine.evaluate_patient(patient_data)
            for opp in opportunities:
                db.session.add(opp)
                created_count += 1

        db.session.commit()
        logger.info(
            "[api_scheduler] Billing rules engine: %d opportunity record(s) "
            "created for %d patient(s) on %s",
            created_count,
            len(scheduled),
            target_date,
        )
    except Exception as exc:
        logger.error("[api_scheduler] Billing rules engine failed: %s", exc)
        try:
            db.session.rollback()
        except Exception:
            pass


def _build_patient_data(db, patient_record, user_id, visit_date):
    """
    Assemble a patient_data dict from ORM objects for BillingRulesEngine.
    Mirrors the dict structure documented in billing_rules.py.
    """
    from models.patient import (
        PatientDiagnosis, PatientMedication, PatientImmunization, PatientVitals,
    )
    mrn_hash = patient_record.patient_mrn_hash

    diagnoses = [
        d.icd10_code for d in
        db.session.query(PatientDiagnosis)
        .filter(PatientDiagnosis.patient_mrn_hash == mrn_hash)
        .all()
        if d.icd10_code
    ]

    medications = [
        m.drug_name for m in
        db.session.query(PatientMedication)
        .filter(
            PatientMedication.patient_mrn_hash == mrn_hash,
            PatientMedication.is_active.is_(True),
        )
        .all()
        if m.drug_name
    ]

    immunizations = [
        {"cvx_code": i.cvx_code, "date_given": i.date_given}
        for i in
        db.session.query(PatientImmunization)
        .filter(PatientImmunization.patient_mrn_hash == mrn_hash)
        .all()
    ]

    vitals = (
        db.session.query(PatientVitals)
        .filter(PatientVitals.patient_mrn_hash == mrn_hash)
        .order_by(PatientVitals.recorded_at.desc())
        .first()
    )

    return {
        "mrn": getattr(patient_record, "mrn", ""),
        "patient_mrn_hash": mrn_hash,
        "user_id": user_id,
        "visit_date": visit_date,
        "age": getattr(patient_record, "age", None),
        "sex": getattr(patient_record, "sex", ""),
        "insurer_type": getattr(patient_record, "insurer_type", "unknown"),
        "insurer_name": getattr(patient_record, "insurer_name", ""),
        "medicare_start_date": getattr(patient_record, "medicare_start_date", None),
        "diagnoses": diagnoses,
        "medications": medications,
        "immunizations": immunizations,
        "last_awv_date": getattr(patient_record, "last_awv_date", None),
        "last_discharge_date": getattr(patient_record, "last_discharge_date", None),
        "ccm_enrolled": getattr(patient_record, "ccm_enrolled", False),
        "ccm_minutes_this_month": getattr(patient_record, "ccm_minutes_this_month", 0),
        "rpm_enrolled": getattr(patient_record, "rpm_enrolled", False),
        "bhi_minutes_this_month": getattr(patient_record, "bhi_minutes_this_month", 0),
        "face_to_face_minutes": None,  # Set at time of visit, not overnight
        "is_new_patient": getattr(patient_record, "is_new_patient", False),
        "has_complex_condition": getattr(patient_record, "has_complex_condition", False),
        "vitals": {
            "bmi": getattr(vitals, "bmi", None),
            "blood_pressure": getattr(vitals, "blood_pressure", None),
        } if vitals else {},
    }


def _flush_stale_caches(db):
    """
    Weekly maintenance: remove cache entries older than 2x their TTL.
    Lets the caches rebuild on next demand with fresh data.
    """
    try:
        from app.services.api.cache_manager import CacheManager

        cache = CacheManager(db)
        stats_before = cache.get_all_api_stats()
        total_before = sum(s.get("count", 0) for s in stats_before.values())

        # Flush APIs with short TTLs that may have accumulated stale entries
        stale_apis = ["openfda_recalls", "openfda_events", "open_meteo"]
        for api_name in stale_apis:
            cache.flush_api(api_name)

        stats_after = cache.get_all_api_stats()
        total_after = sum(s.get("count", 0) for s in stats_after.values())

        logger.info(
            "[api_scheduler] Weekly cache refresh: %d entries removed "
            "(%d → %d total)",
            total_before - total_after,
            total_before,
            total_after,
        )
    except Exception as exc:
        logger.error("[api_scheduler] Cache flush failed: %s", exc)

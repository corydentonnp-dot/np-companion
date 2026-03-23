"""
CareCompanion — API Intelligence Layer Scheduler
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

CareCompanion features that rely on this module:
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
    PRICING_CACHE_REFRESH_HOUR,
    PRICING_CACHE_REFRESH_MINUTE,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Job implementations
# ---------------------------------------------------------------------------

def run_morning_briefing_prep(app, db):
    """
    6:00 AM — Fetch weather conditions and check for drug recalls.
    Pre-loads PubMed guidelines for today's scheduled patients.
    Phase 24.6: medication safety + staff prep tasks.

    Runs inside the Flask app context so models are available.
    """
    with app.app_context():
        logger.info("[api_scheduler] Morning briefing prep starting")
        _run_weather_fetch(db)
        _run_recall_check(db)
        _run_pubmed_preload(db)
        _run_medication_safety_prep(db)
        logger.info("[api_scheduler] Morning briefing prep complete")


def run_overnight_visit_prep(app, db):
    """
    8:00 PM — Run the billing rules engine for tomorrow's scheduled patients.
    Creates BillingOpportunity records for the Today View.
    Phase 23: Also populates monitoring schedules and advances REMS phases.

    Runs inside the Flask app context so ORM writes succeed.
    """
    with app.app_context():
        tomorrow = date.today() + timedelta(days=1)
        logger.info(
            "[api_scheduler] Overnight visit prep for %s starting", tomorrow
        )
        _run_billing_rules(db, target_date=tomorrow)
        _run_nightly_monitoring_update(db, target_date=tomorrow)
        _run_nightly_outreach_check(db)
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


def run_weekly_rxclass_vsac_refresh(app, db):
    """
    Sunday 3:00 AM — Refresh RxClass and VSAC caches, log new entries
    discovered via API that weren't in the hardcoded fallbacks.
    Phase 17.3 auto-update verification.
    Phase 23: Also refreshes monitoring rules for newly added medications.
    """
    with app.app_context():
        logger.info("[api_scheduler] RxClass/VSAC refresh starting")
        _run_rxclass_vsac_refresh(db)
        _run_weekly_monitoring_refresh(db)
        logger.info("[api_scheduler] RxClass/VSAC refresh complete")


def run_pricing_cache_refresh(app, db):
    """
    5:30 AM — Refresh pricing cache for medications on today's scheduled patients.
    Cost Plus runs first (free), GoodRx only for Cost Plus misses.
    Runs before recall check (5:45) and morning briefing (6:00).
    """
    with app.app_context():
        logger.info("[api_scheduler] Pricing cache refresh starting")
        _run_pricing_cache_refresh(db)
        logger.info("[api_scheduler] Pricing cache refresh complete")


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

    # Sunday 3:00 AM — RxClass/VSAC auto-update verification (Phase 17.3)
    scheduler.add_job(
        func=run_weekly_rxclass_vsac_refresh,
        kwargs={"app": app, "db": db},
        trigger="cron",
        day_of_week=WEEKLY_CACHE_REFRESH_DAY,
        hour=WEEKLY_CACHE_REFRESH_HOUR + 1,
        minute=0,
        id="api_rxclass_vsac_refresh",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # 5:30 AM — Pricing cache refresh for today's scheduled patients (Phase 28)
    scheduler.add_job(
        func=run_pricing_cache_refresh,
        kwargs={"app": app, "db": db},
        trigger="cron",
        hour=PRICING_CACHE_REFRESH_HOUR,
        minute=PRICING_CACHE_REFRESH_MINUTE,
        id="api_pricing_cache_refresh",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    logger.info(
        "[api_scheduler] Registered 6 API intelligence jobs: "
        "morning_briefing=%d:00, overnight_prep=%d:00, "
        "recall_check=%d:%02d, cache_refresh=%s %d:00, "
        "rxclass_vsac_refresh=%s %d:00, pricing_cache=%d:%02d",
        MORNING_BRIEFING_HOUR,
        OVERNIGHT_PREP_HOUR,
        DAILY_RECALL_CHECK_HOUR,
        DAILY_RECALL_CHECK_MINUTE,
        WEEKLY_CACHE_REFRESH_DAY.upper(),
        WEEKLY_CACHE_REFRESH_HOUR,
        WEEKLY_CACHE_REFRESH_DAY.upper(),
        WEEKLY_CACHE_REFRESH_HOUR + 1,
        PRICING_CACHE_REFRESH_HOUR,
        PRICING_CACHE_REFRESH_MINUTE,
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


def _run_medication_safety_prep(db):
    """
    Phase 24.6 — Medication safety expansion.
    For today's scheduled patients:
      1. Cross-ref active meds against cached FDA recall results
      2. Gather monitoring bundles (labs due) for MA lab-draw prep
      3. Create staff prep Notification records for MA workflow
    """
    try:
        from models.schedule import Schedule
        from models.patient import PatientMedication
        from models.monitoring import MonitoringSchedule
        from models.notification import Notification
        from billing_engine.shared import hash_mrn

        today = date.today()

        # Get today's scheduled patients
        appointments = Schedule.query.filter_by(appointment_date=today).all()
        if not appointments:
            return

        unique_users = {}
        for appt in appointments:
            if not appt.patient_mrn:
                continue
            key = (appt.user_id, appt.patient_mrn)
            unique_users[key] = appt

        prep_count = 0
        for (user_id, mrn), appt in unique_users.items():
            mrn_hash = hash_mrn(mrn)

            # ── 1. Monitoring labs due → MA lab-draw prep ──
            due_labs = (
                MonitoringSchedule.query
                .filter_by(patient_mrn_hash=mrn_hash, status='active')
                .filter(MonitoringSchedule.next_due_date <= today)
                .all()
            )
            if due_labs:
                lab_names = [e.lab_name for e in due_labs if e.lab_name]
                if lab_names:
                    msg = f'MA PREP {mrn}: Draw labs — {", ".join(lab_names[:5])}'
                    if len(lab_names) > 5:
                        msg += f' (+{len(lab_names) - 5} more)'

                    existing = Notification.query.filter_by(
                        user_id=user_id,
                        template_name='staff_lab_prep',
                        is_read=False,
                    ).filter(Notification.message.startswith(f'MA PREP ...{mrn[-4:]}')).first()

                    if not existing:
                        notif = Notification(
                            user_id=user_id,
                            message=msg,
                            template_name='staff_lab_prep',
                            priority=2,
                        )
                        db.session.add(notif)
                        prep_count += 1

            # ── 2. Active meds with recall flags ──
            active_meds = (
                PatientMedication.query
                .filter_by(user_id=user_id, mrn=mrn, is_active=True)
                .all()
            )
            for med in active_meds:
                if getattr(med, 'recall_flag', None):
                    recall_msg = (
                        f'RECALL ALERT ...{mrn[-4:]}: {med.drug_name} — '
                        f'FDA recall flagged. Review before visit.'
                    )
                    existing = Notification.query.filter_by(
                        user_id=user_id,
                        template_name='med_recall_prep',
                        is_read=False,
                    ).filter(Notification.message.startswith(f'RECALL ALERT ...{mrn[-4:]}')).first()

                    if not existing:
                        notif = Notification(
                            user_id=user_id,
                            message=recall_msg,
                            template_name='med_recall_prep',
                            priority=1,
                        )
                        db.session.add(notif)
                        prep_count += 1

        if prep_count > 0:
            db.session.commit()
            logger.info(
                "[api_scheduler] Medication safety prep: %d staff tasks created",
                prep_count,
            )
        else:
            logger.info("[api_scheduler] Medication safety prep: no tasks needed")

    except Exception as exc:
        db.session.rollback()
        logger.error("[api_scheduler] Medication safety prep failed: %s", exc)


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

            # Phase 23.C2: populate monitoring schedule before billing
            try:
                from app.services.monitoring_rule_engine import MonitoringRuleEngine
                mon_engine = MonitoringRuleEngine(db)
                mon_engine.populate_patient_schedule(
                    mrn_hash, user_id,
                    patient_data.get("medications", []),
                    patient_data.get("diagnoses", []),
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

    result = {
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
        "monitoring_schedule": [],  # populated in C2 block after _build_patient_data
    }

    # Phase 25.4: populate telehealth + BHI fields from CommunicationLog
    try:
        from app.services.telehealth_engine import get_telehealth_fields
        tele_fields = get_telehealth_fields(mrn_hash, user_id, visit_date)
        result.update(tele_fields)
    except Exception:
        pass

    return result


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


def _run_rxclass_vsac_refresh(db):
    """
    Phase 17.3 — Weekly auto-update verification.
    Refreshes RxClass therapeutic class cache for known medications and
    VSAC immunization value sets. Logs when new entries are discovered
    that aren't in the hardcoded fallbacks.
    """
    new_classes = 0
    new_vaccines = 0

    # --- RxClass refresh: re-query classes for all cached RxCUIs ---
    try:
        from models.api_cache import RxClassCache
        from app.services.api.rxnorm import RxNormService

        rxnorm_svc = RxNormService(db)
        existing_rxcuis = [
            row.rxcui for row in
            db.session.query(RxClassCache.rxcui).distinct().limit(100).all()
        ]

        for rxcui in existing_rxcuis:
            try:
                classes = rxnorm_svc.get_therapeutic_classes_for_rxcui(rxcui)
                for cls_name in classes:
                    existing = RxClassCache.query.filter_by(
                        rxcui=rxcui, class_name=cls_name
                    ).first()
                    if not existing:
                        db.session.add(RxClassCache(
                            rxcui=rxcui,
                            class_id=cls_name.lower().replace(" ", "_"),
                            class_name=cls_name,
                            class_type="MEDRT",
                            source="rxclass_api_refresh",
                        ))
                        new_classes += 1
            except Exception:
                continue
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("[api_scheduler] RxClass refresh failed: %s", e)

    # --- VSAC immunization refresh ---
    try:
        from app.services.api.umls import UMLSService
        from app.api_config import UMLS_API_KEY
        from models.api_cache import CdcImmunizationCache

        if UMLS_API_KEY:
            umls_svc = UMLSService(db, api_key=UMLS_API_KEY)
            vsac_vaccines = umls_svc.get_immunization_value_set()
            for vac in vsac_vaccines:
                cvx = vac.get("cvx_code", "")
                if not cvx:
                    continue
                existing = CdcImmunizationCache.query.filter_by(vaccine_code=cvx).first()
                if not existing:
                    db.session.add(CdcImmunizationCache(
                        vaccine_code=cvx,
                        vaccine_name=vac.get("vaccine_name", ""),
                        schedule_description="VSAC-sourced — verify applicability",
                        min_age="19",
                        max_age="999",
                    ))
                    new_vaccines += 1
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("[api_scheduler] VSAC immunization refresh failed: %s", e)

    if new_classes or new_vaccines:
        logger.info(
            "[api_scheduler] RxClass/VSAC refresh: %d new therapeutic classes, "
            "%d new vaccines discovered via API",
            new_classes, new_vaccines,
        )
        # Create admin notification for new entries
        try:
            from models.notification import Notification
            from models.user import User
            admin = User.query.filter_by(role='admin', is_active_account=True).first()
            if admin:
                msg_parts = []
                if new_classes:
                    msg_parts.append(f"{new_classes} new therapeutic class(es)")
                if new_vaccines:
                    msg_parts.append(f"{new_vaccines} new vaccine(s)")
                db.session.add(Notification(
                    user_id=admin.id,
                    title="API Auto-Update: New entries discovered",
                    message=f"Weekly refresh found {' and '.join(msg_parts)} via RxClass/VSAC — review in admin.",
                    priority=2,
                    category="system",
                ))
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.debug("Notification creation failed: %s", e)
    else:
        logger.info("[api_scheduler] RxClass/VSAC refresh: no new entries found")


def _run_pricing_cache_refresh(db):
    """
    Phase 28 — Refresh pricing cache for today's scheduled patients' medications.
    Cost Plus queried first (free, fast), GoodRx only for Cost Plus misses.
    Deduplicates medications across patients.
    """
    from models.schedule import Schedule
    from models.patient import PatientMedication, PatientRecord

    today = date.today()
    cost_plus_hits = 0
    goodrx_hits = 0

    try:
        # Get today's scheduled patient MRNs
        scheduled_mrns = [
            row[0] for row in
            db.session.query(Schedule.patient_mrn_hash)
            .filter(Schedule.visit_date == today)
            .distinct()
            .all()
            if row[0]
        ]

        if not scheduled_mrns:
            logger.info("[api_scheduler] No scheduled patients — pricing cache refresh skipped")
            return

        # Gather distinct active medications across scheduled patients
        seen_drugs = set()
        med_list = []
        for mrn in scheduled_mrns:
            meds = PatientMedication.query.filter_by(
                mrn=mrn, status='active'
            ).all()
            for m in meds:
                drug_key = (m.drug_name or '').lower().split()[0] if m.drug_name else ''
                if drug_key and drug_key not in seen_drugs:
                    seen_drugs.add(drug_key)
                    med_list.append(m)

        if not med_list:
            logger.info("[api_scheduler] No active medications for scheduled patients")
            return

        # Tier 1: Cost Plus (free, no auth)
        try:
            from app.services.api.cost_plus_service import CostPlusService
            cp_svc = CostPlusService(db)
            cost_plus_misses = []
            for m in med_list:
                try:
                    result = cp_svc.get_price(
                        drug_name=m.drug_name.split()[0] if m.drug_name else '',
                        ndc=getattr(m, 'ndc', None),
                    )
                    if result and result.get('price') is not None:
                        cost_plus_hits += 1
                    else:
                        cost_plus_misses.append(m)
                except Exception:
                    cost_plus_misses.append(m)
        except Exception as e:
            logger.error("[api_scheduler] Cost Plus pricing refresh failed: %s", e)
            cost_plus_misses = med_list  # All meds fall through to GoodRx

        # Tier 2: GoodRx (only for Cost Plus misses)
        try:
            from app.services.api.goodrx_service import GoodRxService
            grx_svc = GoodRxService(db)
            for m in cost_plus_misses:
                try:
                    result = grx_svc.get_price(
                        drug_name=m.drug_name.split()[0] if m.drug_name else '',
                    )
                    if result and result.get('price') is not None:
                        goodrx_hits += 1
                except Exception:
                    continue
        except Exception as e:
            logger.error("[api_scheduler] GoodRx pricing refresh failed: %s", e)

        # Tier 1b: NADAC reference pricing (informational — failures non-blocking)
        nadac_hits = 0
        try:
            from app.services.api.nadac_service import NADACService
            nadac_svc = NADACService(db)
            for m in med_list:
                try:
                    result = nadac_svc.get_price(
                        ndc=getattr(m, 'ndc', None),
                        drug_name=m.drug_name.split()[0] if m.drug_name else '',
                    )
                    if result and result.get('found'):
                        nadac_hits += 1
                except Exception:
                    continue
        except Exception as e:
            logger.error("[api_scheduler] NADAC pricing refresh failed: %s", e)

        logger.info(
            "[api_scheduler] Pricing cache: refreshed %d medications "
            "(%d from Cost Plus, %d from GoodRx, %d NADAC refs)",
            len(med_list), cost_plus_hits, goodrx_hits, nadac_hits,
        )

    except Exception as exc:
        logger.error("[api_scheduler] Pricing cache refresh failed: %s", exc)


# ---------------------------------------------------------------------------
# Phase 23 — Monitoring + REMS background jobs
# ---------------------------------------------------------------------------

def _run_nightly_monitoring_update(db, target_date):
    """
    Phase 23 (E1): Nightly monitoring schedule update.

    For each patient on tomorrow's schedule:
    - Populate monitoring schedules with latest lab results
    - Advance REMS phases (clozapine weekly→biweekly→monthly)
    - Update REMS escalation levels
    """
    try:
        from app.services.monitoring_rule_engine import MonitoringRuleEngine
        from app.services.api.dailymed import DailyMedService
        from models.patient import PatientMedication, PatientDiagnosis, PatientLabResult, PatientRecord

        engine = MonitoringRuleEngine(db)
        dm = DailyMedService(db)

        # Get patients on tomorrow's schedule
        try:
            from models.schedule import Schedule
            scheduled = (
                db.session.query(Schedule.patient_mrn_hash, Schedule.user_id)
                .filter(Schedule.visit_date == target_date)
                .distinct()
                .all()
            )
        except Exception:
            scheduled = []

        updated = 0
        for mrn_hash, user_id in scheduled:
            if not mrn_hash:
                continue
            try:
                # Get patient's medications, diagnoses, labs
                record = PatientRecord.query.filter_by(
                    user_id=user_id
                ).filter(
                    PatientRecord.mrn.isnot(None)
                ).first()
                if not record:
                    continue

                meds = PatientMedication.query.filter_by(
                    user_id=user_id, mrn=record.mrn, status='active'
                ).all()
                diagnoses = PatientDiagnosis.query.filter_by(
                    user_id=user_id, mrn=record.mrn, status='active'
                ).all()
                labs = PatientLabResult.query.filter_by(
                    user_id=user_id, mrn=record.mrn
                ).order_by(PatientLabResult.result_date.desc()).limit(100).all()

                engine.populate_patient_schedule(
                    mrn_hash, user_id,
                    [{'drug_name': m.drug_name, 'rxnorm_cui': m.rxnorm_cui} for m in meds],
                    [{'icd10_code': d.icd10_code, 'diagnosis_name': d.diagnosis_name} for d in diagnoses],
                    labs,
                )
                updated += 1
            except Exception as exc:
                logger.debug(
                    "[api_scheduler] Monitoring update failed for %s: %s",
                    mrn_hash[:8], exc,
                )

        # Advance REMS phases and update escalation levels
        try:
            advanced = dm.advance_rems_phases()
            escalation = dm.bulk_update_rems_escalation()
            logger.info(
                "[api_scheduler] REMS: %d phases advanced, escalation: %s",
                advanced, escalation,
            )
        except Exception as exc:
            logger.debug("[api_scheduler] REMS update failed: %s", exc)

        logger.info(
            "[api_scheduler] Nightly monitoring: updated %d patients", updated
        )
    except Exception as exc:
        logger.error("[api_scheduler] Nightly monitoring update failed: %s", exc)


def _run_nightly_outreach_check(db):
    """
    Phase 23 (D5): Proactive outreach flag.

    Identifies patients with overdue monitoring who haven't been seen in 30+ days.
    Creates Notification records for the dashboard. Sends Pushover for critical items.
    """
    try:
        from models.monitoring import MonitoringSchedule
        from models.patient import PatientRecord
        from models.notification import Notification
        from models.user import User

        today = date.today()
        thirty_days_ago = today - timedelta(days=30)

        # Get all active, overdue monitoring entries
        overdue = (
            MonitoringSchedule.query
            .filter(
                MonitoringSchedule.status == 'active',
                MonitoringSchedule.next_due_date < today,
            )
            .all()
        )

        if not overdue:
            return

        # Group by (patient_mrn_hash, user_id)
        by_patient = {}
        for entry in overdue:
            key = (entry.patient_mrn_hash, entry.user_id)
            by_patient.setdefault(key, []).append(entry)

        flagged = 0
        critical_alerts = []

        for (mrn_hash, user_id), entries in by_patient.items():
            # Check if patient was seen recently (last_xml_parsed as proxy)
            record = PatientRecord.query.filter_by(
                user_id=user_id,
            ).filter(
                PatientRecord.mrn.isnot(None),
            ).first()

            if not record:
                continue

            # Use last_xml_parsed as proxy for last visit
            last_seen = record.last_xml_parsed
            if last_seen and last_seen.date() > thirty_days_ago:
                continue  # Seen recently — not flagged for outreach

            # Check if patient is on any future schedule
            try:
                from models.schedule import Schedule
                future_appt = Schedule.query.filter(
                    Schedule.user_id == user_id,
                    Schedule.appointment_date >= today,
                ).first()
                if future_appt:
                    continue  # Has an upcoming visit — skip
            except Exception:
                pass

            # Flag for outreach
            flagged += 1
            has_critical = any(e.priority in ('critical', 'high') for e in entries)

            # Create notification (idempotent — check for existing by template_name + message prefix)
            msg_prefix = f'Patient ...{mrn_hash[-4:]}'
            existing = Notification.query.filter(
                Notification.user_id == user_id,
                Notification.template_name == 'monitoring_outreach',
                Notification.message.like(f'{msg_prefix}%'),
                Notification.is_read == False,
            ).first()

            if not existing:
                lab_names = ', '.join(e.lab_name for e in entries[:3])
                if len(entries) > 3:
                    lab_names += f' +{len(entries) - 3} more'

                notif = Notification(
                    user_id=user_id,
                    template_name='monitoring_outreach',
                    message=f'{msg_prefix} has {len(entries)} overdue lab(s): {lab_names}',
                    priority=1 if has_critical else 2,
                )
                db.session.add(notif)

            # Collect critical alerts for Pushover
            if has_critical:
                critical_entries = [e for e in entries if e.priority in ('critical', 'high')]
                critical_alerts.append({
                    'mrn_display': f'...{mrn_hash[-4:]}',
                    'user_id': user_id,
                    'labs': [e.lab_name for e in critical_entries],
                })

        db.session.commit()

        # Send Pushover for critical overdue monitoring
        if critical_alerts:
            try:
                import config
                user_key = getattr(config, 'PUSHOVER_USER_KEY', '')
                api_token = getattr(config, 'PUSHOVER_API_TOKEN', '')
                if user_key and api_token:
                    from agent.notifier import _send_pushover
                    msg_parts = []
                    for alert in critical_alerts[:5]:
                        labs = ', '.join(alert['labs'][:3])
                        msg_parts.append(f"{alert['mrn_display']}: {labs}")
                    msg = '\n'.join(msg_parts)
                    if len(critical_alerts) > 5:
                        msg += f'\n+{len(critical_alerts) - 5} more patients'
                    _send_pushover(
                        user_key, api_token,
                        'Critical Lab Monitoring Overdue',
                        msg,
                        priority=1,
                        sound='siren',
                    )
            except Exception as exc:
                logger.debug("[api_scheduler] Pushover outreach alert failed: %s", exc)

        logger.info(
            "[api_scheduler] Outreach check: %d patients flagged, %d critical alerts",
            flagged, len(critical_alerts),
        )
    except Exception as exc:
        logger.error("[api_scheduler] Outreach check failed: %s", exc)


def _run_weekly_monitoring_refresh(db):
    """
    Phase 23 (E1 + B4): Weekly monitoring rule refresh.

    Queries medications added in the past 7 days that don't yet have
    MonitoringRule entries and populates rules via the waterfall.
    Also refreshes VSAC preventive service OIDs (B4).
    """
    try:
        from app.services.monitoring_rule_engine import MonitoringRuleEngine
        engine = MonitoringRuleEngine(db)
        count = engine.bulk_refresh_new_medications(lookback_days=7)
        logger.info(
            "[api_scheduler] Weekly monitoring refresh: %d new rules created",
            count,
        )

        # B4: Refresh VSAC preventive service OIDs
        vsac_count = engine.refresh_preventive_vsac_oids()
        logger.info(
            "[api_scheduler] VSAC preventive OID refresh: %d OIDs updated",
            vsac_count,
        )
    except Exception as exc:
        logger.error(
            "[api_scheduler] Weekly monitoring refresh failed: %s", exc
        )

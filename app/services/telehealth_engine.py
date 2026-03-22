"""
CareCompanion — Telehealth Aggregation Engine
File: app/services/telehealth_engine.py
Phase 25.4

Aggregates CommunicationLog entries into the fields that
billing_engine/detectors/telehealth.py and bhi.py expect in patient_data.
"""

import logging
from datetime import date, timedelta

from models import db
from models.telehealth import CommunicationLog

logger = logging.getLogger(__name__)


def get_telehealth_fields(mrn_hash, user_id, visit_date=None):
    """
    Return a dict with all telehealth-related fields needed by the
    billing engine detectors (telehealth.py + bhi.py).

    Fields returned:
        phone_encounter_minutes        — total phone minutes today (or visit_date)
        phone_resulted_in_visit_24hr   — True if any phone call led to face-to-face
        portal_message_minutes_7day    — portal message time in last 7 days
        interprofessional_consult_minutes — interprofessional consult time this month
        behavioral_dx_minutes          — BHI-qualifying care minutes this calendar month
    """
    ref = visit_date or date.today()

    # --- Phone E/M (same-day) ---
    phone_entries = (
        db.session.query(CommunicationLog)
        .filter(
            CommunicationLog.patient_mrn_hash == mrn_hash,
            CommunicationLog.user_id == user_id,
            CommunicationLog.communication_type == 'phone_call',
            db.func.date(CommunicationLog.start_datetime) == ref,
        )
        .all()
    )
    phone_minutes = sum(e.cumulative_minutes or 0 for e in phone_entries)
    phone_resulted_in_visit = any(e.resulted_in_visit for e in phone_entries)

    # --- Portal / digital E/M (7-day window) ---
    portal_start = ref - timedelta(days=7)
    portal_minutes = (
        db.session.query(db.func.coalesce(db.func.sum(CommunicationLog.cumulative_minutes), 0))
        .filter(
            CommunicationLog.patient_mrn_hash == mrn_hash,
            CommunicationLog.user_id == user_id,
            CommunicationLog.communication_type == 'portal_message',
            db.func.date(CommunicationLog.start_datetime) >= portal_start,
            db.func.date(CommunicationLog.start_datetime) <= ref,
        )
        .scalar()
    ) or 0

    # --- Interprofessional consult (current month) ---
    month_start = ref.replace(day=1)
    interprof_minutes = (
        db.session.query(db.func.coalesce(db.func.sum(CommunicationLog.cumulative_minutes), 0))
        .filter(
            CommunicationLog.patient_mrn_hash == mrn_hash,
            CommunicationLog.user_id == user_id,
            CommunicationLog.communication_type == 'secure_message',
            CommunicationLog.topic.ilike('%consult%'),
            db.func.date(CommunicationLog.start_datetime) >= month_start,
            db.func.date(CommunicationLog.start_datetime) <= ref,
        )
        .scalar()
    ) or 0

    # --- BHI / behavioral health minutes (current month) ---
    bhi_minutes = (
        db.session.query(db.func.coalesce(db.func.sum(CommunicationLog.cumulative_minutes), 0))
        .filter(
            CommunicationLog.patient_mrn_hash == mrn_hash,
            CommunicationLog.user_id == user_id,
            CommunicationLog.clinical_decision_made.is_(True),
            db.func.date(CommunicationLog.start_datetime) >= month_start,
            db.func.date(CommunicationLog.start_datetime) <= ref,
        )
        .scalar()
    ) or 0

    return {
        "phone_encounter_minutes": int(phone_minutes),
        "phone_resulted_in_visit_24hr": phone_resulted_in_visit,
        "portal_message_minutes_7day": int(portal_minutes),
        "interprofessional_consult_minutes": int(interprof_minutes),
        "behavioral_dx_minutes": int(bhi_minutes),
    }

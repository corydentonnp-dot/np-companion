"""
CareCompanion — Telehealth / Communication Log Routes
File: routes/telehealth.py
Phase 25.4

Endpoints for logging phone calls, portal messages, and other
non-face-to-face encounters.  Data feeds telehealth billing
detectors (99441-99443, 99421-99423, 99452) and BHI (99484).
"""

import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from models import db
from models.telehealth import CommunicationLog
from billing_engine.shared import hash_mrn

logger = logging.getLogger(__name__)

telehealth_bp = Blueprint('telehealth', __name__)


@telehealth_bp.route('/api/patient/<mrn>/communication-log', methods=['POST'])
@login_required
def log_communication(mrn):
    """Log a phone call, portal message, or other telehealth encounter."""
    data = request.get_json(silent=True) or {}
    mrn_hash = hash_mrn(mrn)

    comm_type = data.get('communication_type', 'phone_call')
    allowed_types = ('phone_call', 'portal_message', 'secure_message', 'video_visit')
    if comm_type not in allowed_types:
        return jsonify({"error": f"Invalid communication_type. Must be one of {allowed_types}"}), 400

    minutes = data.get('cumulative_minutes')
    if minutes is None or not isinstance(minutes, (int, float)) or minutes < 0:
        return jsonify({"error": "cumulative_minutes is required and must be >= 0"}), 400

    start_dt = data.get('start_datetime')
    if start_dt:
        try:
            start_dt = datetime.fromisoformat(start_dt)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid start_datetime format (ISO 8601 expected)"}), 400
    else:
        start_dt = datetime.utcnow()

    end_dt = data.get('end_datetime')
    if end_dt:
        try:
            end_dt = datetime.fromisoformat(end_dt)
        except (ValueError, TypeError):
            end_dt = None

    entry = CommunicationLog(
        patient_mrn_hash=mrn_hash,
        user_id=current_user.id,
        communication_type=comm_type,
        initiated_by=data.get('initiated_by', 'provider'),
        start_datetime=start_dt,
        end_datetime=end_dt,
        cumulative_minutes=round(float(minutes), 1),
        clinical_decision_made=bool(data.get('clinical_decision_made', False)),
        topic=data.get('topic', ''),
        resulted_in_visit=bool(data.get('resulted_in_visit', False)),
        visit_date_after=data.get('visit_date_after'),
        billable_code=data.get('billable_code'),
        billing_status='pending',
    )
    db.session.add(entry)
    db.session.commit()

    return jsonify({"status": "ok", "id": entry.id}), 201


@telehealth_bp.route('/api/patient/<mrn>/communications', methods=['GET'])
@login_required
def get_communications(mrn):
    """Return communication log entries for a patient (newest first)."""
    mrn_hash = hash_mrn(mrn)
    limit = min(int(request.args.get('limit', 50)), 200)

    entries = (
        CommunicationLog.query
        .filter_by(patient_mrn_hash=mrn_hash, user_id=current_user.id)
        .order_by(CommunicationLog.start_datetime.desc())
        .limit(limit)
        .all()
    )

    return jsonify([
        {
            "id": e.id,
            "communication_type": e.communication_type,
            "initiated_by": e.initiated_by,
            "start_datetime": e.start_datetime.isoformat() if e.start_datetime else None,
            "end_datetime": e.end_datetime.isoformat() if e.end_datetime else None,
            "cumulative_minutes": e.cumulative_minutes,
            "clinical_decision_made": e.clinical_decision_made,
            "topic": e.topic,
            "resulted_in_visit": e.resulted_in_visit,
            "billable_code": e.billable_code,
            "billing_status": e.billing_status,
        }
        for e in entries
    ])

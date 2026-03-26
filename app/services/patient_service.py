"""
CareCompanion — Patient Service

Shared patient-record helpers with DB access.
Extracted from routes/patient.py (Band 3 B1.5).
"""

from flask import request

from models import db
from models.patient import (
    PatientRecord,
    PatientMedication,
    PatientDiagnosis,
    PatientAllergy,
    PatientImmunization,
)
from models.schedule import Schedule
from utils.patient_helpers import normalize_name, normalize_dob


def schedule_context_for_patient(user_id, mrn):
    """Return the most relevant schedule metadata for this user/MRN.

    Merges query-string overrides (name, dob, appt, visit, reason) with
    the most recent matching Schedule row. Query-string values take priority.
    """
    latest = (
        Schedule.query
        .filter_by(user_id=user_id, patient_mrn=mrn)
        .order_by(Schedule.appointment_date.desc(), Schedule.appointment_time.desc())
        .first()
    )

    context = {
        'patient_name': normalize_name(request.args.get('name', '')),
        'patient_dob': normalize_dob(request.args.get('dob', '')),
        'appointment_time': (request.args.get('appt', '') or '').strip(),
        'visit_type': (request.args.get('visit', '') or '').strip(),
        'reason': (request.args.get('reason', '') or '').strip(),
        'appointment_date': None,
        'status': '',
    }

    if latest:
        context['patient_name'] = context['patient_name'] or normalize_name(latest.patient_name)
        context['patient_dob'] = context['patient_dob'] or normalize_dob(latest.patient_dob)
        context['appointment_time'] = context['appointment_time'] or (latest.appointment_time or '')
        context['visit_type'] = context['visit_type'] or (latest.visit_type or '')
        context['reason'] = context['reason'] or (latest.reason or '')
        context['appointment_date'] = latest.appointment_date
        context['status'] = latest.status or ''

    return context


def ensure_patient_record_for_view(user_id, mrn, schedule_context):
    """Create or backfill a per-user patient record from schedule context.

    If the record doesn't exist yet, creates it. Fills blank name/dob from
    schedule context. Commits only when changes were made.
    """
    record = PatientRecord.query.filter_by(user_id=user_id, mrn=mrn).first()
    changed = False

    if not record:
        record = PatientRecord(user_id=user_id, mrn=mrn)
        db.session.add(record)
        changed = True

    if schedule_context['patient_name'] and not (record.patient_name or '').strip():
        record.patient_name = schedule_context['patient_name']
        changed = True

    if schedule_context['patient_dob'] and not (record.patient_dob or '').strip():
        record.patient_dob = schedule_context['patient_dob']
        changed = True

    if changed:
        db.session.commit()

    return record


def prepopulate_sections(mrn, user_id, allergies=None, medications=None,
                         diagnoses=None, immunizations=None):
    """Build dict mapping AC note section names to pre-populated text.

    Accepts pre-fetched query results to avoid redundant DB queries.
    Falls back to querying if not provided.
    """
    prepop = {}

    if allergies is None:
        allergies = PatientAllergy.query.filter_by(user_id=user_id, mrn=mrn).all()
    if allergies:
        prepop['Allergies'] = '\n'.join(
            f'{a.allergen} — {a.reaction}' if a.reaction else a.allergen
            for a in allergies
        )

    if medications is None:
        medications = PatientMedication.query.filter_by(
            user_id=user_id, mrn=mrn, status='active'
        ).order_by(PatientMedication.drug_name).all()
    active_meds = [m for m in medications if getattr(m, 'status', '') == 'active']
    if active_meds:
        prepop['Medications'] = '\n'.join(
            f'{m.drug_name} {m.dosage} {m.frequency}'.strip() for m in active_meds
        )

    if diagnoses is None:
        diagnoses = PatientDiagnosis.query.filter_by(
            user_id=user_id, mrn=mrn, status='active'
        ).all()
    active_dx = [d for d in diagnoses if getattr(d, 'status', '') == 'active']
    if active_dx:
        lines = []
        for d in active_dx:
            line = d.diagnosis_name
            if d.icd10_code:
                line += f' ({d.icd10_code})'
            lines.append(line)
        prepop['Past Medical History'] = '\n'.join(lines)

    if immunizations is None:
        immunizations = PatientImmunization.query.filter_by(
            user_id=user_id, mrn=mrn
        ).order_by(PatientImmunization.date_given.desc()).all()
    if immunizations:
        seen = set()
        imm_lines = []
        for imm in immunizations:
            date_str = imm.date_given.strftime('%m/%Y') if imm.date_given else 'Unknown'
            key = (imm.vaccine_name, date_str)
            if key not in seen:
                seen.add(key)
                label = imm.vaccine_name
                if imm.source == 'viis':
                    label += ' [VIIS]'
                imm_lines.append(f'{label} ({date_str})')
        prepop['Immunizations'] = ', '.join(imm_lines)

    return prepop

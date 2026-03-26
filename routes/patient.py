"""
CareCompanion — Patient Chart View (F10e) — Widget-Based Layout

File location: carecompanion/routes/patient.py

Draggable/resizable widget-based patient chart with:
  - XML upload (manual CDA import)
  - Medications (active/inactive)
  - Diagnoses (acute vs chronic)
  - Labs (Epic-style spreadsheet with graphing)
  - USPSTF recommendations
  - Specialists
  - Note Generator
  - Vitals, Allergies, Immunizations, Care Gaps
"""

import json
import os
from collections import defaultdict
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user

import config

from models import db
from sqlalchemy.orm import joinedload
from models.patient import (
    PatientRecord, PatientVitals, PatientMedication,
    PatientDiagnosis, PatientAllergy, PatientImmunization,
    PatientNoteDraft, PatientSpecialist,
    PatientEncounterNote,
)
from models.api_cache import Icd10Cache, RxNormCache
from models.labtrack import LabTrack
from models.caregap import CareGap, CareGapRule
from models.schedule import Schedule

# Service layer imports (extracted from this file, Band 3 B1)
from utils.patient_helpers import (
    mrn_display as _mrn_display,
    calc_age as _calc_age,
    calc_age_years as _calc_age_years,
    normalize_name as _normalize_name,
    normalize_dob as _normalize_dob,
)
from app.services.patient_service import (
    schedule_context_for_patient as _schedule_context_for_patient,
    ensure_patient_record_for_view as _ensure_patient_record_for_view,
    prepopulate_sections as _prepopulate_sections,
)
from app.services.diagnosis_service import (
    classify_diagnosis as _classify_diagnosis,
    backfill_icd10_codes as _backfill_icd10_codes,
    load_icd10_csv as _load_icd10_csv,
    ACUTE_ICD10_PREFIXES,
    ACUTE_KEYWORDS,
)
from app.services.medication_enrichment import (
    fetch_rxnorm_api as _fetch_rxnorm_api,
    enrich_rxnorm_single as _enrich_rxnorm_single,
    enrich_rxnorm as _enrich_rxnorm,
    standardize_frequency as _standardize_frequency,
    parse_dose_fallback as _parse_dose_fallback,
    enrich_medications as _enrich_medications,
)
from app.services.caregap_service import (
    get_uspstf_recommendations as _get_uspstf_recommendations,
    auto_evaluate_care_gaps as _auto_evaluate_care_gaps,
)

patient_bp = Blueprint('patient', __name__)

AC_NOTE_SECTIONS = [
    "Chief Complaint",
    "History of Present Illness",
    "Review of Systems",
    "Past Medical History",
    "Social History",
    "Family History",
    "Allergies",
    "Medications",
    "Physical Exam",
    "Functional Status/Mental Status",
    "Confidential Information",
    "Assessment",
    "Plan",
    "Instructions",
    "Goals",
    "Health Concerns",
]

# ACUTE_ICD10_PREFIXES and ACUTE_KEYWORDS are imported from app.services.diagnosis_service above.


# ======================================================================
# GET /patient/<mrn> — Patient Chart (widget layout)
# ======================================================================
@patient_bp.route('/patient/<mrn>')
@login_required
def chart(mrn):
    """Patient chart view — widget-based drag/resize layout."""
    schedule_context = _schedule_context_for_patient(current_user.id, mrn)
    record = _ensure_patient_record_for_view(current_user.id, mrn, schedule_context)

    medications = PatientMedication.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).order_by(PatientMedication.status, PatientMedication.drug_name).all()

    # Cache-only enrichment on page load (no API calls — fast path)
    _enrich_medications(medications, cache_only=True)

    # Cache-only ICD-10 backfill (no API calls — fast path)
    _backfill_icd10_codes(current_user.id, mrn, cache_only=True)

    diagnoses = PatientDiagnosis.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).order_by(PatientDiagnosis.status, PatientDiagnosis.diagnosis_name).all()

    allergies = PatientAllergy.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).all()

    immunizations = PatientImmunization.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).order_by(PatientImmunization.date_given.desc()).all()

    vitals = PatientVitals.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).order_by(PatientVitals.measured_at.desc()).all()

    lab_tracks = LabTrack.query.filter_by(
        user_id=current_user.id, mrn=mrn, is_archived=False
    ).options(joinedload(LabTrack.results)).all()

    care_gaps = CareGap.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).all()

    # Auto-evaluate care gaps on first chart load (when none exist yet)
    if not care_gaps and record and record.last_xml_parsed:
        _auto_evaluate_care_gaps(current_user.id, mrn)
        care_gaps = CareGap.query.filter_by(
            user_id=current_user.id, mrn=mrn
        ).all()

    specialists = PatientSpecialist.query.filter_by(
        user_id=current_user.id, mrn=mrn, is_archived=False
    ).order_by(PatientSpecialist.specialty).all()

    # Encounter notes (prior notes)
    encounter_notes = PatientEncounterNote.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).order_by(PatientEncounterNote.encounter_date.desc()).all()

    # Note draft
    draft = PatientNoteDraft.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).first()
    draft_data = json.loads(draft.section_data) if draft else {}

    prepopulated = _prepopulate_sections(
        mrn, current_user.id,
        allergies=allergies,
        medications=medications,
        diagnoses=diagnoses,
        immunizations=immunizations,
    )

    # USPSTF recommendations
    age = _calc_age_years(record.patient_dob if record else '')
    sex = getattr(record, 'patient_sex', 'unknown') if record else 'unknown'
    uspstf_recs = _get_uspstf_recommendations(age, sex)

    # Build lab spreadsheet data: {lab_name: [{date, value}, ...]}
    lab_spreadsheet = defaultdict(list)
    all_lab_dates = set()
    for lt in lab_tracks:
        for r in lt.results:
            if r.result_date:
                date_str = r.result_date.strftime('%m/%d/%Y')
                lab_spreadsheet[lt.lab_name].append({
                    'date': date_str,
                    'value': r.result_value,
                    'is_critical': r.is_critical,
                })
                all_lab_dates.add(date_str)

    # Sort dates chronologically
    sorted_dates = sorted(all_lab_dates, key=lambda d: datetime.strptime(d, '%m/%d/%Y'))

    # Overdue labs
    overdue_labs = [lt for lt in lab_tracks if lt.status in ('overdue', 'due_soon', 'critical')]

    # Widget layout preferences (default ordering)
    widget_layout = current_user.get_pref('chart_widget_layout', None)
    chart_layout_mode = current_user.get_pref('chart_layout_mode', 'grid')
    chart_free_positions = current_user.get_pref('chart_free_widget_positions', None)
    chart_view_mode = current_user.get_pref('chart_view_mode', 'tabs')

    # Phase 24.4 — Immunization series gaps deferred to AJAX for faster page load
    imm_series_gaps = []

    # Phase 32.1 — Auto-compute risk scores deferred to AJAX for faster page load
    auto_scores = {}

    return render_template(
        'patient_chart.html',
        record=record,
        mrn=mrn,
        mrn_display=_mrn_display(mrn),
        age_str=_calc_age(record.patient_dob if record else ''),
        medications=medications,
        diagnoses=diagnoses,
        allergies=allergies,
        immunizations=immunizations,
        vitals=vitals,
        lab_tracks=lab_tracks,
        care_gaps=care_gaps,
        specialists=specialists,
        draft_data=draft_data,
        prepopulated=prepopulated,
        note_sections=AC_NOTE_SECTIONS,
        uspstf_recs=uspstf_recs,
        lab_spreadsheet=dict(lab_spreadsheet),
        lab_dates=sorted_dates,
        overdue_labs=overdue_labs,
        schedule_context=schedule_context,
        widget_layout=json.dumps(widget_layout) if widget_layout else 'null',
        chart_layout_mode=chart_layout_mode,
        chart_free_positions=json.dumps(chart_free_positions) if chart_free_positions else 'null',
        chart_view_mode=chart_view_mode,
        has_data=record is not None and record.last_xml_parsed is not None,
        imm_series_gaps=imm_series_gaps,
        auto_scores=auto_scores,
        encounter_notes=encounter_notes,
    )


# ======================================================================
# POST /api/patient/<mrn>/enrich — Deferred API enrichment (RxNorm + ICD-10)
# Called via AJAX after page load to avoid blocking chart render.
# ======================================================================
@patient_bp.route('/api/patient/<mrn>/enrich', methods=['POST'])
@login_required
def enrich_patient_data(mrn):
    """Run full API enrichment (RxNorm + ICD-10) for a patient."""
    try:
        medications = PatientMedication.query.filter_by(
            user_id=current_user.id, mrn=mrn
        ).all()
        _enrich_medications(medications, cache_only=False)
        _backfill_icd10_codes(current_user.id, mrn, cache_only=False)
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error('enrich_patient_data error for %s: %s', mrn[-4:] if len(mrn) > 4 else '??', str(e))
        return jsonify({'success': False, 'error': 'Enrichment skipped'}), 200


# ======================================================================
# GET /api/patient/<mrn>/auto-scores — Deferred risk score computation
# Called via AJAX after page load to avoid blocking chart render.
# ======================================================================
@patient_bp.route('/api/patient/<mrn>/auto-scores')
@login_required
def get_auto_scores(mrn):
    """Compute auto risk scores for patient chart (deferred from page load)."""
    try:
        from app.services.calculator_engine import CalculatorEngine
        engine = CalculatorEngine()
        score_list = engine.run_auto_scores(mrn, current_user.id)
        scores = {s['calculator_key']: s for s in score_list if s.get('score_value') is not None}
        return jsonify({'success': True, 'data': scores})
    except Exception as e:
        current_app.logger.debug('Auto-scores failed for ••%s: %s', mrn[-4:], e)
        return jsonify({'success': True, 'data': {}})


# ======================================================================
# GET /api/patient/<mrn>/imm-gaps — Deferred immunization series gaps
# Called via AJAX after page load to avoid blocking chart render.
# ======================================================================
@patient_bp.route('/api/patient/<mrn>/imm-gaps')
@login_required
def get_imm_gaps(mrn):
    """Compute immunization series gaps for patient chart (deferred from page load)."""
    try:
        from app.services.immunization_engine import get_series_gaps, populate_patient_series
        from billing_engine.shared import hash_mrn

        record = PatientRecord.query.filter_by(
            user_id=current_user.id, mrn=mrn
        ).first()
        age = _calc_age_years(record.patient_dob if record else '')

        mrn_hash = hash_mrn(mrn)
        populate_patient_series(mrn_hash, current_user.id)
        gaps = get_series_gaps(mrn_hash, current_user.id, age)
        # Serialize for JSON (gaps may contain non-serializable objects)
        gap_list = []
        for g in gaps:
            gap_list.append({
                'series_name': g.get('series_name', ''),
                'status': g.get('status', ''),
                'message': g.get('message', ''),
                'next_due': str(g.get('next_due', '')) if g.get('next_due') else None,
            })
        return jsonify({'success': True, 'data': gap_list})
    except Exception as e:
        current_app.logger.debug('Imm gaps failed for ••%s: %s', mrn[-4:], e)
        return jsonify({'success': True, 'data': []})


# ======================================================================
# GET /api/patient/<mrn>/pricing — Bulk medication pricing
# ======================================================================
@patient_bp.route('/api/patient/<mrn>/pricing')
@login_required
def medication_pricing(mrn):
    """Return pricing data for all active medications of a patient (max 20)."""
    import logging
    logger = logging.getLogger(__name__)
    try:
        from app.services.pricing_service import PricingService
        medications = PatientMedication.query.filter_by(
            user_id=current_user.id, mrn=mrn, status='active'
        ).order_by(PatientMedication.drug_name).limit(20).all()

        record = PatientRecord.query.filter_by(
            user_id=current_user.id, mrn=mrn
        ).first()

        svc = PricingService(db)
        results = []
        for med in medications:
            try:
                pricing = svc.get_pricing_for_medication(med, record)
            except Exception as e:
                logger.debug('Pricing failed for %s: %s', med.drug_name, e)
                pricing = {'source': 'none', 'price_monthly_estimate': None,
                           'badge_color': None, 'assistance_programs': []}
            results.append({
                'drug_name': med.drug_name,
                'rxcui': med.rxnorm_cui,
                'med_id': med.id,
                'pricing': pricing,
            })
        return jsonify({'medications': results})
    except Exception as e:
        logger.error('Bulk pricing error for MRN ••%s: %s', mrn[-4:], e)
        return jsonify({'medications': []}), 200


# ======================================================================
# GET /api/patient/<mrn>/summary — Quick patient summary for PA lookup
# ======================================================================
@patient_bp.route('/api/patient/<mrn>/summary')
@login_required
def patient_summary(mrn):
    """Return basic patient info for auto-populating forms."""
    record = PatientRecord.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).first()
    if not record:
        return jsonify({'success': False, 'error': 'Patient not found'}), 404
    return jsonify({
        'success': True,
        'data': {
            'name': record.patient_name or '',
            'dob': record.patient_dob or '',
            'sex': record.patient_sex or '',
            'insurance': record.insurer_type or '',
        }
    })


# ======================================================================
# POST /patient/<mrn>/upload-xml — Manual XML upload
# ======================================================================
@patient_bp.route('/patient/<mrn>/upload-xml', methods=['POST'])
@login_required
def upload_xml(mrn):
    """Upload a CDA Clinical Summary XML file and parse it."""
    if 'xml_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400

    f = request.files['xml_file']
    if not f.filename:
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if not f.filename.lower().endswith('.xml'):
        return jsonify({'success': False, 'message': 'File must be .xml'}), 400

    # Save to temp file, parse, then delete
    export_folder = getattr(config, 'CLINICAL_SUMMARY_EXPORT_FOLDER', 'data/clinical_summaries/')
    if not os.path.isabs(export_folder):
        export_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), export_folder)
    export_folder = os.path.normpath(export_folder)
    os.makedirs(export_folder, exist_ok=True)

    # Use secure filename
    safe_name = f'upload_{current_user.id}_{mrn}_{int(datetime.now().timestamp())}.xml'
    xml_path = os.path.join(export_folder, safe_name)

    try:
        f.save(xml_path)
        from agent.clinical_summary_parser import parse_clinical_summary, store_parsed_summary

        parsed = parse_clinical_summary(xml_path)

        # Use the MRN from the URL (trusted) not from XML
        if parsed.get('patient_mrn') and parsed['patient_mrn'] != mrn:
            # Warn but still use the URL MRN
            pass

        # Clear existing data for this patient before re-import
        PatientMedication.query.filter_by(user_id=current_user.id, mrn=mrn).delete()
        PatientDiagnosis.query.filter_by(user_id=current_user.id, mrn=mrn).delete()
        PatientAllergy.query.filter_by(user_id=current_user.id, mrn=mrn).delete()
        PatientImmunization.query.filter_by(user_id=current_user.id, mrn=mrn).delete()
        PatientVitals.query.filter_by(user_id=current_user.id, mrn=mrn).delete()
        db.session.flush()

        store_parsed_summary(current_user.id, mrn, parsed)

        # Backfill missing ICD-10 codes via NIH API
        _backfill_icd10_codes(current_user.id, mrn)

        # Auto-classify diagnoses
        for diag in PatientDiagnosis.query.filter_by(user_id=current_user.id, mrn=mrn).all():
            diag.diagnosis_category = _classify_diagnosis(diag.diagnosis_name, diag.icd10_code)
        db.session.commit()

        # Evaluate care gaps now that we have fresh clinical data
        _auto_evaluate_care_gaps(current_user.id, mrn)

        sections = [k for k, v in parsed.items() if v and k not in ('patient_name', 'patient_mrn', 'patient_dob')]
        return jsonify({
            'success': True,
            'message': f'Parsed {len(sections)} sections successfully.',
            'sections': sections,
            'patient_name': parsed.get('patient_name', ''),
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Parse error: {str(e)}'}), 500
    finally:
        # Clean up temp file
        try:
            if os.path.exists(xml_path):
                os.remove(xml_path)
        except OSError:
            pass


# ======================================================================
# GET /api/patient/<mrn>/labs — Lab data for spreadsheet & graphing
# ======================================================================
@patient_bp.route('/api/patient/<mrn>/labs')
@login_required
def api_labs(mrn):
    """Return lab data for the Epic-style spreadsheet and graphing."""
    lab_tracks = LabTrack.query.filter_by(
        user_id=current_user.id, mrn=mrn, is_archived=False
    ).all()

    data = {}
    all_dates = set()

    for lt in lab_tracks:
        results = []
        for r in lt.results:
            if r.result_date:
                date_str = r.result_date.strftime('%Y-%m-%d')
                results.append({
                    'date': date_str,
                    'display_date': r.result_date.strftime('%m/%d/%y'),
                    'value': r.result_value,
                    'is_critical': r.is_critical,
                    'trend': r.trend_direction,
                })
                all_dates.add(date_str)
        data[lt.lab_name] = {
            'results': results,
            'alert_low': lt.alert_low,
            'alert_high': lt.alert_high,
            'interval_days': lt.interval_days,
            'status': lt.status,
        }

    sorted_dates = sorted(all_dates)
    return jsonify({'labs': data, 'dates': sorted_dates})


# ======================================================================
# POST /patient/<mrn>/specialist — Add specialist
# ======================================================================
@patient_bp.route('/patient/<mrn>/specialist', methods=['POST'])
@login_required
def add_specialist(mrn):
    """Add a specialist record for a patient."""
    data = request.get_json(silent=True) or {}
    spec = PatientSpecialist(
        user_id=current_user.id,
        mrn=mrn,
        specialty=data.get('specialty', ''),
        provider_name=data.get('provider_name', ''),
        phone=data.get('phone', ''),
        fax=data.get('fax', ''),
        notes=data.get('notes', ''),
    )
    db.session.add(spec)
    db.session.commit()
    return jsonify({'success': True, 'id': spec.id})


# ======================================================================
# DELETE /patient/<mrn>/specialist/<id> — Remove specialist
# ======================================================================
@patient_bp.route('/patient/<mrn>/specialist/<int:spec_id>', methods=['DELETE'])
@login_required
def delete_specialist(mrn, spec_id):
    """Remove a specialist record."""
    spec = PatientSpecialist.query.filter_by(
        id=spec_id, user_id=current_user.id, mrn=mrn
    ).first()
    if spec:
        # HIPAA: soft-delete clinical records — never hard-delete
        spec.is_archived = True
        db.session.commit()
    return jsonify({'success': True})


# ======================================================================
# POST /patient/<mrn>/widget-layout — Save widget positions
# ======================================================================
@patient_bp.route('/patient/<mrn>/widget-layout', methods=['POST'])
@login_required
def save_widget_layout(mrn):
    """Save widget positions/sizes to user preferences."""
    data = request.get_json(silent=True) or {}
    layout = data.get('layout', {})
    current_user.set_pref('chart_widget_layout', layout)
    db.session.commit()
    return jsonify({'success': True})


# ======================================================================
# POST /patient/<mrn>/note/save — Save Prepped Note draft
# ======================================================================
@patient_bp.route('/patient/<mrn>/note/save', methods=['POST'])
@login_required
def save_note(mrn):
    """Save prepped note draft to database."""
    data = request.get_json(silent=True) or {}
    sections = data.get('sections', {})

    draft = PatientNoteDraft.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).first()

    if draft:
        draft.section_data = json.dumps(sections)
        draft.updated_at = datetime.now(timezone.utc)
    else:
        draft = PatientNoteDraft(
            user_id=current_user.id,
            mrn=mrn,
            section_data=json.dumps(sections),
        )
        db.session.add(draft)

    db.session.commit()
    return jsonify({'success': True})


# ======================================================================
# POST /patient/<mrn>/note/send-to-ac — PyAutoGUI paste to AC
# ======================================================================
@patient_bp.route('/patient/<mrn>/note/send-to-ac', methods=['POST'])
@login_required
def send_to_ac(mrn):
    """Trigger PyAutoGUI paste to Amazing Charts."""
    from agent.ac_window import get_ac_state

    if getattr(config, 'AC_MOCK_MODE', False):
        ac_state = 'home_screen'
    else:
        ac_state = get_ac_state()

    if ac_state == 'not_running':
        return jsonify({
            'success': False,
            'message': 'Amazing Charts is not running. Start AC and try again.',
        })

    if ac_state == 'login_screen':
        return jsonify({
            'success': False,
            'message': 'Amazing Charts is at the login screen. Log in first.',
        })

    return jsonify({
        'success': False,
        'message': (
            'Automatic note injection is not yet implemented. '
            'Use "Copy All" and paste into the Enlarge Textbox manually. '
            'The 16 sections can be navigated with "Update & Go to Next Field".'
        ),
    })


# ======================================================================
# POST /patient/<mrn>/refresh — Re-export Clinical Summary
# ======================================================================
@patient_bp.route('/patient/<mrn>/refresh', methods=['POST'])
@login_required
def refresh_patient(mrn):
    """Trigger a clinical summary re-export for this patient."""
    imported_items_path = getattr(config, 'AC_IMPORTED_ITEMS_PATH', '')
    if imported_items_path:
        patient_folder = os.path.join(imported_items_path, str(mrn))
        if os.path.isdir(patient_folder):
            files = os.listdir(patient_folder)
            if files:
                return jsonify({
                    'success': True,
                    'message': f'Found {len(files)} imported item(s). Processing will begin shortly.',
                    'source': 'imported_items',
                    'file_count': len(files),
                })

    return jsonify({
        'success': True,
        'message': (
            'Refresh requested. Export a Clinical Summary XML from AC '
            '(Alt+P > Export Clinical Summary), then upload it here.'
        ),
        'source': 'pending',
    })


@patient_bp.route('/patient/<mrn>/auto-scores', methods=['POST'])
@login_required
def refresh_auto_scores(mrn):
    """Phase 32.3 — Re-run all auto_ehr calculators and return updated results as JSON."""
    try:
        from app.services.calculator_engine import CalculatorEngine
        calc_engine = CalculatorEngine()
        results = calc_engine.run_auto_scores(mrn, current_user.id)
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ======================================================================
# POST /patient/<mrn>/claim — Claim patient for your panel
# ======================================================================
@patient_bp.route('/patient/<mrn>/claim', methods=['POST'])
@login_required
def claim_patient(mrn):
    """Claim a patient for the current provider's panel."""
    from models.schedule import Schedule
    data = request.get_json(silent=True) or {}

    record = PatientRecord.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).first()

    if not record:
        record = PatientRecord(
            user_id=current_user.id,
            mrn=mrn,
        )
        db.session.add(record)

    # Populate patient_name if missing
    _reject_names = {'unknown patient', 'unknown', ''}
    if not record.patient_name or record.patient_name.lower() in _reject_names:
        # 1) Accept from POST body (chart header knows the name)
        name_from_body = (data.get('patient_name') or '').strip()
        if name_from_body and name_from_body.lower() not in _reject_names:
            record.patient_name = name_from_body
        else:
            # 2) Look up from schedule data
            sched = Schedule.query.filter_by(patient_mrn=mrn).order_by(
                Schedule.appointment_date.desc()
            ).first()
            if sched and sched.patient_name:
                record.patient_name = sched.patient_name

    record.claimed_by = current_user.id
    record.claimed_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({'success': True, 'claimed_by': current_user.display_name})


# ======================================================================
# POST /patient/<mrn>/generate-note — AI-assisted note generation
# ======================================================================
@patient_bp.route('/patient/<mrn>/generate-note', methods=['POST'])
@login_required
def generate_note(mrn):
    """Generate note sections from patient data (rule-based, not LLM)."""
    data = request.get_json(silent=True) or {}
    selected_sections = data.get('sections', [])

    record = PatientRecord.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).first()

    generated = {}

    for section in selected_sections:
        if section == 'Allergies':
            allergies = PatientAllergy.query.filter_by(
                user_id=current_user.id, mrn=mrn
            ).all()
            if allergies:
                lines = []
                for a in allergies:
                    line = a.allergen
                    if a.reaction:
                        line += f' → {a.reaction}'
                    if a.severity:
                        line += f' ({a.severity})'
                    lines.append(line)
                generated[section] = '\n'.join(lines)
            else:
                generated[section] = 'NKDA'

        elif section == 'Medications':
            meds = PatientMedication.query.filter_by(
                user_id=current_user.id, mrn=mrn, status='active'
            ).order_by(PatientMedication.drug_name).all()
            if meds:
                lines = []
                for m in meds:
                    line = m.drug_name
                    if m.dosage:
                        line += f' {m.dosage}'
                    if m.frequency:
                        line += f' {m.frequency}'
                    lines.append(line)
                generated[section] = '\n'.join(lines)
            else:
                generated[section] = 'No active medications'

        elif section == 'Past Medical History':
            diags = PatientDiagnosis.query.filter_by(
                user_id=current_user.id, mrn=mrn, status='active'
            ).all()
            chronic = [d for d in diags if d.diagnosis_category == 'chronic']
            acute = [d for d in diags if d.diagnosis_category == 'acute']
            lines = []
            if chronic:
                lines.append('Chronic conditions:')
                for d in chronic:
                    line = f'  - {d.diagnosis_name}'
                    if d.icd10_code:
                        line += f' ({d.icd10_code})'
                    lines.append(line)
            if acute:
                lines.append('Recent/Acute:')
                for d in acute:
                    line = f'  - {d.diagnosis_name}'
                    if d.icd10_code:
                        line += f' ({d.icd10_code})'
                    lines.append(line)
            generated[section] = '\n'.join(lines) if lines else 'No active diagnoses'

        elif section == 'Social History':
            # Pull from parsed XML social_history if available
            generated[section] = ''

        elif section == 'Assessment':
            diags = PatientDiagnosis.query.filter_by(
                user_id=current_user.id, mrn=mrn, status='active'
            ).all()
            if diags:
                lines = []
                for i, d in enumerate(diags, 1):
                    line = f'{i}. {d.diagnosis_name}'
                    if d.icd10_code:
                        line += f' ({d.icd10_code})'
                    lines.append(line)
                generated[section] = '\n'.join(lines)
            else:
                generated[section] = ''

        elif section == 'Plan':
            # Generate basic plan from care gaps + overdue labs
            lines = []
            gaps = CareGap.query.filter_by(
                user_id=current_user.id, mrn=mrn
            ).filter(CareGap.status.in_(['open', 'in_progress'])).all()
            if gaps:
                lines.append('Preventive care:')
                for g in gaps:
                    lines.append(f'  - {g.gap_type}: {g.gap_name or "due"}')

            overdue = LabTrack.query.filter_by(
                user_id=current_user.id, mrn=mrn, is_overdue=True, is_archived=False
            ).all()
            if overdue:
                lines.append('Lab orders:')
                for lt in overdue:
                    lines.append(f'  - {lt.lab_name} (overdue)')

            generated[section] = '\n'.join(lines) if lines else ''

        elif section == 'Physical Exam':
            vitals = PatientVitals.query.filter_by(
                user_id=current_user.id, mrn=mrn
            ).order_by(PatientVitals.measured_at.desc()).all()
            seen = set()
            lines = ['Vitals:']
            for v in vitals:
                if v.vital_name not in seen:
                    seen.add(v.vital_name)
                    lines.append(f'  {v.vital_name}: {v.vital_value} {v.vital_unit}')
                if len(seen) >= 8:
                    break
            generated[section] = '\n'.join(lines) if len(lines) > 1 else ''

        elif section == 'Health Concerns':
            gaps = CareGap.query.filter_by(
                user_id=current_user.id, mrn=mrn
            ).filter(CareGap.status.in_(['open', 'in_progress'])).all()
            if gaps:
                generated[section] = '\n'.join(f'- {g.gap_type}' for g in gaps)
            else:
                generated[section] = ''
        else:
            generated[section] = ''

    return jsonify({'success': True, 'sections': generated})


# ======================================================================
# POST /patient/upload-xml — Dashboard drag-and-drop XML upload (auto-detect MRN)
# ======================================================================
@patient_bp.route('/patient/upload-xml', methods=['POST'])
@login_required
def upload_xml_auto():
    """Upload one or more CDA Clinical Summary XML files, auto-detecting MRN."""
    files = request.files.getlist('xml_files')
    if not files:
        return jsonify({'success': False, 'message': 'No files uploaded'}), 400

    results = []
    for f in files:
        if not f.filename or not f.filename.lower().endswith('.xml'):
            results.append({'file': f.filename or '?', 'success': False, 'message': 'Not an XML file'})
            continue

        export_folder = getattr(config, 'CLINICAL_SUMMARY_EXPORT_FOLDER', 'data/clinical_summaries/')
        if not os.path.isabs(export_folder):
            export_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), export_folder)
        os.makedirs(export_folder, exist_ok=True)

        safe_name = f'upload_{current_user.id}_{int(datetime.now().timestamp())}_{f.filename}'
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '._-')
        xml_path = os.path.join(export_folder, safe_name)

        try:
            f.save(xml_path)
            from agent.clinical_summary_parser import parse_clinical_summary, store_parsed_summary

            parsed = parse_clinical_summary(xml_path)
            mrn = parsed.get('patient_mrn', '')
            if not mrn:
                results.append({'file': f.filename, 'success': False, 'message': 'No MRN found in XML'})
                continue

            store_parsed_summary(current_user.id, mrn, parsed)

            # Backfill missing ICD-10 codes via NIH API
            _backfill_icd10_codes(current_user.id, mrn)

            # Auto-classify diagnoses
            for diag in PatientDiagnosis.query.filter_by(user_id=current_user.id, mrn=mrn).all():
                diag.diagnosis_category = _classify_diagnosis(diag.diagnosis_name, diag.icd10_code)
            db.session.commit()

            sections = [k for k, v in parsed.items() if v and k not in ('patient_name', 'patient_mrn', 'patient_dob')]
            results.append({
                'file': f.filename,
                'success': True,
                'mrn': mrn,
                'patient_name': parsed.get('patient_name', ''),
                'sections': sections,
            })
        except Exception as e:
            db.session.rollback()
            results.append({'file': f.filename, 'success': False, 'message': str(e)})
        finally:
            try:
                if os.path.exists(xml_path):
                    os.remove(xml_path)
            except OSError:
                pass

    ok_count = sum(1 for r in results if r.get('success'))
    return jsonify({
        'success': ok_count > 0,
        'message': f'Imported {ok_count} of {len(results)} file(s)',
        'results': results,
    })


# ======================================================================
# GET /patients — Patient Roster (My Patients panel)
# ======================================================================
@patient_bp.route('/patients')
@login_required
def roster():
    """Show patients — 'all' (imported by user) or 'mine' (claimed by user)."""
    view = request.args.get('view', 'all')
    if view == 'mine':
        patients = (
            PatientRecord.query
            .filter_by(claimed_by=current_user.id)
            .order_by(PatientRecord.patient_name)
            .all()
        )
    else:
        view = 'all'
        patients = (
            PatientRecord.query
            .filter_by(user_id=current_user.id)
            .order_by(PatientRecord.patient_name)
            .all()
        )

    return render_template(
        'patient_roster.html',
        patients=patients,
        current_view=view,
    )


# ======================================================================
# POST /patient/<mrn>/diagnosis/<id>/toggle-category
# ======================================================================
@patient_bp.route('/patient/<mrn>/diagnosis/<int:dx_id>/toggle-category', methods=['POST'])
@login_required
def toggle_dx_category(mrn, dx_id):
    """Toggle a diagnosis between acute and chronic."""
    dx = db.session.get(PatientDiagnosis, dx_id)
    if not dx:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    new_cat = 'acute' if (dx.diagnosis_category or 'chronic') == 'chronic' else 'chronic'
    dx.diagnosis_category = new_cat
    db.session.commit()
    return jsonify({'success': True, 'new_category': new_cat})


# ======================================================================
# POST /patient/<mrn>/<item_type>/<id>/toggle-status
# ======================================================================
@patient_bp.route('/patient/<mrn>/<item_type>/<int:item_id>/toggle-status', methods=['POST'])
@login_required
def toggle_item_status(mrn, item_type, item_id):
    """Toggle active/inactive status for a medication or diagnosis."""
    if item_type == 'medication':
        item = db.session.get(PatientMedication, item_id)
    elif item_type == 'diagnosis':
        item = db.session.get(PatientDiagnosis, item_id)
    else:
        return jsonify({'success': False, 'error': 'Invalid type'}), 400

    if not item:
        return jsonify({'success': False, 'error': 'Not found'}), 404

    new_status = 'inactive' if item.status == 'active' else 'active'
    item.status = new_status
    db.session.commit()
    return jsonify({'success': True, 'new_status': new_status})


# ======================================================================
# POST /patient/<mrn>/medication/<id>/update — Edit medication fields
# ======================================================================
@patient_bp.route('/patient/<mrn>/medication/<int:med_id>/update', methods=['POST'])
@login_required
def update_medication(mrn, med_id):
    """Update a medication's dosage or frequency. Marks user_modified flag."""
    med = PatientMedication.query.filter_by(
        id=med_id, user_id=current_user.id, mrn=mrn
    ).first()
    if not med:
        return jsonify({'success': False, 'error': 'Not found'}), 404

    data = request.get_json(silent=True) or {}
    field = data.get('field', '')
    value = (data.get('value') or '').strip()

    if field == 'dosage':
        med.dosage = value
    elif field == 'frequency':
        med.frequency = value
    else:
        return jsonify({'success': False, 'error': 'Invalid field'}), 400

    med.user_modified = True
    try:
        db.session.commit()
        return jsonify({'success': True, 'field': field, 'value': value, 'user_modified': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating medication: {str(e)}")
        return jsonify({'success': False, 'error': 'Update failed'}), 500


# ======================================================================
# POST /patient/<mrn>/diagnosis/add — Add a new diagnosis (UX-20)
# ======================================================================
@patient_bp.route('/patient/<mrn>/diagnosis/add', methods=['POST'])
@login_required
def add_diagnosis(mrn):
    """Add a new ICD-10 diagnosis to the patient's problem list."""
    data = request.get_json(silent=True) or {}
    name = (data.get('diagnosis_name') or '').strip()
    code = (data.get('icd10_code') or '').strip()
    category = (data.get('category') or 'chronic').strip()

    if not name:
        return jsonify({'success': False, 'error': 'Diagnosis name required'}), 400

    try:
        dx = PatientDiagnosis(
            user_id=current_user.id,
            mrn=mrn,
            diagnosis_name=name,
            icd10_code=code,
            diagnosis_category=category,
            status='active',
        )
        db.session.add(dx)
        db.session.commit()
        return jsonify({
            'success': True,
            'data': {'id': dx.id, 'diagnosis_name': dx.diagnosis_name, 'icd10_code': dx.icd10_code}
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding diagnosis: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to add diagnosis'}), 500


# ======================================================================
# POST /patient/<mrn>/diagnosis/<id>/remove — Soft-delete a diagnosis (UX-20)
# ======================================================================
@patient_bp.route('/patient/<mrn>/diagnosis/<int:dx_id>/remove', methods=['POST'])
@login_required
def remove_diagnosis(mrn, dx_id):
    """Soft-delete a diagnosis by setting status to 'resolved'."""
    dx = PatientDiagnosis.query.filter_by(
        id=dx_id, user_id=current_user.id, mrn=mrn
    ).first()
    if not dx:
        return jsonify({'success': False, 'error': 'Not found'}), 404

    dx.status = 'resolved'
    db.session.commit()
    return jsonify({'success': True})


# ======================================================================
# POST /patient/<mrn>/update-demographics — Edit patient demographics
# ======================================================================
@patient_bp.route('/patient/<mrn>/update-demographics', methods=['POST'])
@login_required
def update_demographics(mrn):
    """Update patient demographics (name, DOB, sex). Re-evaluates care gaps on sex change."""
    data = request.get_json(silent=True) or {}
    record = PatientRecord.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).first()
    if not record:
        record = PatientRecord(user_id=current_user.id, mrn=mrn)
        db.session.add(record)

    old_sex = record.patient_sex or ''

    if 'patient_name' in data and data['patient_name'].strip():
        record.patient_name = data['patient_name'].strip()
    if 'patient_dob' in data:
        record.patient_dob = data['patient_dob'].strip()
    if 'patient_sex' in data:
        record.patient_sex = data['patient_sex'].strip()

    db.session.commit()

    # Re-evaluate care gaps when sex changes
    new_sex = record.patient_sex or ''
    if new_sex and new_sex != old_sex:
        try:
            from agent.caregap_engine import evaluate_and_persist_gaps
            patient_data = {
                'mrn': mrn,
                'sex': new_sex,
                'dob': record.patient_dob or '',
                'age': None,
            }
            evaluate_and_persist_gaps(current_user.id, mrn, patient_data, current_app._get_current_object())
        except Exception as e:
            current_app.logger.error(f"Care gap re-eval on sex change failed for MRN {mrn[-4:]}: {e}")

    return jsonify({'success': True})


# ======================================================================
# GET /patient/<mrn>/print — Print patient paperwork (stub)
# ======================================================================
@patient_bp.route('/patient/<mrn>/print')
@login_required
def print_paperwork(mrn):
    """Stub — future patient paperwork printing (visit summary, after-visit instructions, etc.)."""
    record = PatientRecord.query.filter_by(mrn=mrn, claimed_by=current_user.id).first()
    if not record:
        record = PatientRecord.query.filter_by(mrn=mrn).first()
    mrn_display = mrn
    return render_template('patient_print_stub.html', record=record, mrn_display=mrn_display)


# ======================================================================
# GET /api/icd10/search — Proxy to NIH ICD-10 API + local CSV fallback
# ======================================================================
# _load_icd10_csv() imported from app.services.diagnosis_service above.

@patient_bp.route('/api/icd10/search')
@login_required
def icd10_search():
    """Search ICD-10-CM codes — local CSV first, then NIH API."""
    import urllib.request
    import urllib.parse
    import urllib.error

    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'results': []})

    q_lower = query.lower()

    # Local CSV matches first (instant, no network)
    local_codes = _load_icd10_csv()
    local_matches = [
        c for c in local_codes
        if q_lower in c['code'].lower() or q_lower in c['name'].lower()
    ]

    # NIH API for broader results
    api_results = []
    url = (
        'https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search'
        '?sf=code,name&terms=' + urllib.parse.quote(query)
    )
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if len(data) >= 4 and data[3]:
                for item in data[3]:
                    if len(item) >= 2:
                        api_results.append({'code': item[0], 'name': item[1]})
    except Exception:
        pass  # local results still available

    # Merge: local first, then API (deduplicated)
    seen = set()
    results = []
    for r in local_matches + api_results:
        if r['code'] not in seen:
            seen.add(r['code'])
            results.append(r)
        if len(results) >= 25:
            break

    return jsonify({'results': results})
"""
CareCompanion — Care Gap Service

USPSTF recommendation lookup and automated care gap evaluation.
Extracted from routes/patient.py (Band 3 B1.8).
"""

import json
import logging

from models import db
from models.patient import PatientRecord, PatientDiagnosis, PatientImmunization
from models.caregap import CareGapRule

logger = logging.getLogger(__name__)


def get_uspstf_recommendations(age, sex):
    """Return applicable USPSTF screening recommendations for this patient.

    Looks up all CareGapRule rows and filters by age and sex criteria.
    """
    recs = []
    rules = CareGapRule.query.all()
    for rule in rules:
        try:
            criteria = json.loads(rule.criteria_json) if rule.criteria_json else {}
        except (json.JSONDecodeError, TypeError):
            criteria = {}
        min_age = criteria.get('min_age', 0)
        max_age = criteria.get('max_age', 999)
        req_sex = criteria.get('sex', 'all')
        if age is not None and min_age <= age <= max_age:
            if req_sex == 'all' or req_sex == sex:
                pair = (rule.billing_code_pair or '').strip()
                if ' / ' in pair:
                    commercial, medicare = [p.strip() for p in pair.split(' / ', 1)]
                elif pair:
                    commercial = medicare = pair
                else:
                    commercial = medicare = ''
                recs.append({
                    'name': rule.gap_type,
                    'description': getattr(rule, 'description', '') or rule.gap_type,
                    'interval_days': rule.interval_days,
                    'billing_code': commercial,
                    'medicare_code': medicare,
                    'explanation': getattr(rule, 'description', '') or '',
                    'documentation_template': getattr(rule, 'documentation_template', '') or '',
                })
    return recs


def auto_evaluate_care_gaps(user_id, mrn, app=None):
    """
    Trigger the USPSTF care gap engine for one patient.

    Called after XML upload and on chart load when gaps are empty.
    Fails silently — care gaps are not critical path.

    Parameters
    ----------
    user_id : int
    mrn : str
    app : Flask app object, optional. Pass current_app._get_current_object() from route context.
    """
    try:
        from flask import current_app
        from agent.caregap_engine import evaluate_and_persist_gaps

        record = PatientRecord.query.filter_by(user_id=user_id, mrn=mrn).first()
        if not record:
            return

        diagnoses = PatientDiagnosis.query.filter_by(
            user_id=user_id, mrn=mrn, status='active'
        ).all()
        immunizations = PatientImmunization.query.filter_by(
            user_id=user_id, mrn=mrn
        ).all()

        patient_data = {
            'patient_name': record.patient_name or '',
            'patient_dob': record.patient_dob or '',
            'patient_sex': record.patient_sex or '',
            'diagnoses': [
                {'name': d.diagnosis_name, 'icd10': d.icd10_code or ''}
                for d in diagnoses
            ],
            'immunizations': [
                {
                    'name': i.vaccine_name or '',
                    'date_given': str(i.date_given) if i.date_given else '',
                }
                for i in immunizations
            ],
        }
        flask_app = app or current_app._get_current_object()
        evaluate_and_persist_gaps(user_id, mrn, patient_data, flask_app)
    except Exception as e:
        logger.debug('Care gap auto-evaluation failed for ••%s: %s', mrn[-4:], e)

"""
CareCompanion — Care Gap Rules Engine

File location: carecompanion/agent/caregap_engine.py

Evaluates which USPSTF preventive care screenings are due for a given
patient based on age, sex, diagnoses, immunization history, and the
last time each screening was completed.

Two rule sources:
  1. Hardcoded defaults (USPSTF 2024 guidelines) — always present
  2. Admin-editable CareGapRule rows in the database — override defaults

Usage:
    from agent.caregap_engine import evaluate_care_gaps, seed_default_rules
    gaps = evaluate_care_gaps(patient_data, app)
"""

import json
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger('carecompanion.caregap_engine')

# ======================================================================
# Hardcoded USPSTF default rules
# ======================================================================

DEFAULT_RULES = [
    {
        'gap_type': 'colorectal_colonoscopy',
        'gap_name': 'Colorectal Cancer Screening (Colonoscopy)',
        'description': 'USPSTF recommends screening for colorectal cancer in adults age 45-75.',
        'criteria': {'min_age': 45, 'max_age': 75, 'sex': 'all'},
        'interval_days': 3650,  # 10 years
        'billing_code_pair': 'G0105 / G0121',
        'documentation_template': (
            'Colorectal cancer screening discussed. Patient agrees to '
            'colonoscopy referral. Order placed today.'
        ),
    },
    {
        'gap_type': 'colorectal_fobt',
        'gap_name': 'Colorectal Cancer Screening (FOBT/FIT)',
        'description': 'Annual fecal occult blood or fecal immunochemical test, age 45-75.',
        'criteria': {'min_age': 45, 'max_age': 75, 'sex': 'all'},
        'interval_days': 365,
        'billing_code_pair': '82270',
        'documentation_template': (
            'Colorectal cancer screening discussed. FIT/FOBT kit provided. '
            'Patient instructed on collection and return.'
        ),
    },
    {
        'gap_type': 'mammogram',
        'gap_name': 'Breast Cancer Screening (Mammogram)',
        'description': 'Biennial screening mammography for women aged 40 and older.',
        'criteria': {'min_age': 40, 'max_age': 999, 'sex': 'female'},
        'interval_days': 730,  # 2 years
        'billing_code_pair': '77067',
        'documentation_template': (
            'Breast cancer screening discussed. Mammogram ordered. '
            'Patient counseled on importance of routine screening.'
        ),
    },
    {
        'gap_type': 'cervical_pap',
        'gap_name': 'Cervical Cancer Screening (Pap)',
        'description': 'Pap smear every 3 years for women aged 21-65.',
        'criteria': {'min_age': 21, 'max_age': 65, 'sex': 'female'},
        'interval_days': 1095,  # 3 years
        'billing_code_pair': '88141 / Q0091',
        'documentation_template': (
            'Cervical cancer screening performed. Pap smear collected. '
            'Results pending.'
        ),
    },
    {
        'gap_type': 'cervical_pap_hpv',
        'gap_name': 'Cervical Cancer Screening (Pap + HPV co-test)',
        'description': 'Pap + HPV co-testing every 5 years for women aged 30-65.',
        'criteria': {'min_age': 30, 'max_age': 65, 'sex': 'female'},
        'interval_days': 1825,  # 5 years
        'billing_code_pair': '88141 / 87624',
        'documentation_template': (
            'Cervical cancer screening performed. Pap smear with HPV '
            'co-testing collected. Results pending.'
        ),
    },
    {
        'gap_type': 'lung_ldct',
        'gap_name': 'Lung Cancer Screening (LDCT)',
        'description': (
            'Annual low-dose CT for adults aged 50-80 with 20+ pack-year '
            'smoking history who currently smoke or quit within past 15 years.'
        ),
        'criteria': {
            'min_age': 50, 'max_age': 80, 'sex': 'all',
            'risk_factors': ['heavy_smoker'],
        },
        'interval_days': 365,
        'billing_code_pair': 'G0297 / 71271',
        'documentation_template': (
            'Lung cancer screening discussed. Patient meets criteria '
            '(age/smoking history). LDCT ordered. Shared decision-making '
            'discussion documented.'
        ),
    },
    {
        'gap_type': 'dexa_scan',
        'gap_name': 'Osteoporosis Screening (DEXA)',
        'description': 'DEXA scan for women 65+ or younger women with risk factors.',
        'criteria': {'min_age': 65, 'max_age': 999, 'sex': 'female'},
        'interval_days': 730,  # 2 years
        'billing_code_pair': '77080',
        'documentation_template': (
            'Osteoporosis screening discussed. DEXA scan ordered. '
            'Patient counseled on calcium/vitamin D supplementation.'
        ),
    },
    {
        'gap_type': 'hypertension_screen',
        'gap_name': 'Hypertension Screening',
        'description': 'Blood pressure screening for all adults at every visit.',
        'criteria': {'min_age': 18, 'max_age': 999, 'sex': 'all'},
        'interval_days': 365,
        'billing_code_pair': '99473',
        'documentation_template': (
            'Blood pressure screening performed. Result: [BP]. '
            'Patient counseled on lifestyle modifications.'
        ),
    },
    {
        'gap_type': 'diabetes_screen',
        'gap_name': 'Diabetes Screening',
        'description': 'Screen adults aged 35-70 who are overweight or obese.',
        'criteria': {
            'min_age': 35, 'max_age': 70, 'sex': 'all',
            'risk_factors': ['overweight'],
        },
        'interval_days': 1095,  # 3 years
        'billing_code_pair': '82947 / 83036',
        'documentation_template': (
            'Diabetes screening performed. Fasting glucose / HbA1c ordered. '
            'Patient counseled on diet and exercise.'
        ),
    },
    {
        'gap_type': 'lipid_screen',
        'gap_name': 'Lipid Screening',
        'description': 'Lipid panel for men 35+ and women 45+ (or younger with risk factors).',
        'criteria': {'min_age': 35, 'max_age': 999, 'sex': 'all'},
        'interval_days': 1825,  # 5 years
        'billing_code_pair': '80061',
        'documentation_template': (
            'Lipid screening ordered. Patient counseled on cardiovascular '
            'risk factors and healthy lifestyle.'
        ),
    },
    {
        'gap_type': 'depression_screen',
        'gap_name': 'Depression Screening (PHQ-9)',
        'description': 'Annual depression screening for all adults using PHQ-9.',
        'criteria': {'min_age': 18, 'max_age': 999, 'sex': 'all'},
        'interval_days': 365,
        'billing_code_pair': 'G0444 / 96127',
        'documentation_template': (
            'Annual depression screening performed using PHQ-9. '
            'Score: [X]. [Positive/Negative screening]. '
            'Follow-up plan discussed.'
        ),
    },
    {
        'gap_type': 'aaa_screen',
        'gap_name': 'AAA Screening (Abdominal Aortic Aneurysm)',
        'description': 'One-time ultrasound for men aged 65-75 who have ever smoked.',
        'criteria': {
            'min_age': 65, 'max_age': 75, 'sex': 'male',
            'risk_factors': ['ever_smoked'],
        },
        'interval_days': 0,  # one-time
        'billing_code_pair': 'G0389',
        'documentation_template': (
            'AAA screening discussed. Patient meets criteria (male, 65-75, '
            'smoking history). Abdominal ultrasound ordered.'
        ),
    },
    {
        'gap_type': 'fall_risk',
        'gap_name': 'Fall Risk Assessment',
        'description': 'Annual fall risk screening for adults 65 and older.',
        'criteria': {'min_age': 65, 'max_age': 999, 'sex': 'all'},
        'interval_days': 365,
        'billing_code_pair': '99420',
        'documentation_template': (
            'Fall risk assessment performed. Patient screened for gait, '
            'balance, and environmental hazards. '
            '[Interventions discussed/ordered as appropriate.]'
        ),
    },
    {
        'gap_type': 'hiv_screen',
        'gap_name': 'HIV Screening',
        'description': 'One-time HIV screening for adults aged 15-65.',
        'criteria': {'min_age': 15, 'max_age': 65, 'sex': 'all'},
        'interval_days': 0,  # one-time
        'billing_code_pair': '86701 / 87389',
        'documentation_template': (
            'HIV screening discussed per USPSTF recommendation. '
            'Patient consented. HIV test ordered.'
        ),
    },
    {
        'gap_type': 'flu_vaccine',
        'gap_name': 'Influenza Vaccine (Annual)',
        'description': 'Annual influenza vaccination for all adults.',
        'criteria': {'min_age': 18, 'max_age': 999, 'sex': 'all'},
        'interval_days': 365,
        'billing_code_pair': '90688 / 90471',
        'documentation_template': (
            'Influenza vaccine administered today. Lot #[XX], '
            'expiration [date], [site]. VIS provided. '
            'Patient tolerated well, no immediate adverse reaction.'
        ),
    },
    {
        'gap_type': 'covid_vaccine',
        'gap_name': 'COVID-19 Vaccine (Per Current Guidelines)',
        'description': 'COVID-19 vaccination per current CDC/ACIP guidelines.',
        'criteria': {'min_age': 18, 'max_age': 999, 'sex': 'all'},
        'interval_days': 365,
        'billing_code_pair': '91309 / 0074A',
        'documentation_template': (
            'COVID-19 vaccination discussed. Patient [received/declined]. '
            'Current guidelines reviewed.'
        ),
    },
    {
        'gap_type': 'shingrix',
        'gap_name': 'Shingrix (Herpes Zoster Vaccine)',
        'description': 'Two-dose Shingrix series for adults aged 50 and older.',
        'criteria': {'min_age': 50, 'max_age': 999, 'sex': 'all'},
        'interval_days': 0,  # series completion — one-time
        'billing_code_pair': '90750 / 90471',
        'documentation_template': (
            'Shingrix vaccine dose [1/2] administered. Lot #[XX]. '
            'Patient counseled on expected side effects. '
            'Second dose due in 2-6 months.'
        ),
    },
    {
        'gap_type': 'tdap',
        'gap_name': 'Tdap Vaccine',
        'description': 'Tdap booster every 10 years for all adults.',
        'criteria': {'min_age': 18, 'max_age': 999, 'sex': 'all'},
        'interval_days': 3650,  # 10 years
        'billing_code_pair': '90715 / 90471',
        'documentation_template': (
            'Tdap vaccine administered today. Lot #[XX], '
            'expiration [date], [site]. VIS provided.'
        ),
    },
    {
        'gap_type': 'pneumococcal',
        'gap_name': 'Pneumococcal Vaccine',
        'description': 'Pneumococcal vaccination for adults 65+ or with risk factors.',
        'criteria': {'min_age': 65, 'max_age': 999, 'sex': 'all'},
        'interval_days': 0,  # series-based
        'billing_code_pair': '90677 / 90471',
        'documentation_template': (
            'Pneumococcal vaccine [PCV20/PPSV23] administered. '
            'Lot #[XX]. Patient counseled on series completion.'
        ),
    },
]


# ======================================================================
# Engine functions
# ======================================================================

def seed_default_rules(app):
    """
    Insert (or update) DEFAULT_RULES into the care_gap_rules table.
    Called once at startup via app context.  Existing admin edits
    with source='hardcoded' are NOT overwritten — only missing rows
    are inserted.
    """
    from models import db
    from models.caregap import CareGapRule

    with app.app_context():
        # Fast check: if we already have enough hardcoded rules, skip
        # the per-rule query loop entirely.
        existing_count = CareGapRule.query.filter_by(source='hardcoded').count()
        if existing_count >= len(DEFAULT_RULES):
            return

        for rule_def in DEFAULT_RULES:
            existing = CareGapRule.query.filter_by(
                gap_type=rule_def['gap_type']
            ).first()
            if existing:
                continue  # never overwrite admin edits
            rule = CareGapRule(
                gap_type=rule_def['gap_type'],
                gap_name=rule_def['gap_name'],
                description=rule_def['description'],
                criteria_json=json.dumps(rule_def['criteria']),
                interval_days=rule_def['interval_days'],
                billing_code_pair=rule_def['billing_code_pair'],
                documentation_template=rule_def['documentation_template'],
                source='hardcoded',
                is_active=True,
            )
            db.session.add(rule)
        db.session.commit()
        logger.info('Care gap default rules seeded')


def _calculate_age(dob_str):
    """
    Calculate age from a DOB string.  Accepts MM/DD/YYYY, YYYY-MM-DD, or YYYYMMDD.
    Returns None if unparseable.
    """
    if not dob_str:
        return None
    for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%Y%m%d'):
        try:
            dob = datetime.strptime(dob_str.strip(), fmt)
            today = datetime.now(timezone.utc).date()
            age = today.year - dob.year - (
                (today.month, today.day) < (dob.month, dob.day)
            )
            return age
        except ValueError:
            continue
    return None


def _patient_sex_matches(criteria_sex, patient_sex):
    """Check if the patient's sex matches the rule criteria."""
    if criteria_sex == 'all':
        return True
    patient_lower = (patient_sex or '').lower().strip()
    if criteria_sex == 'female':
        return patient_lower in ('f', 'female')
    if criteria_sex == 'male':
        return patient_lower in ('m', 'male')
    return True


def _has_risk_factors(required_factors, patient_diagnoses):
    """
    Check if the patient has the required risk factors based on
    their diagnosis list.  Maps risk factor keys to diagnosis keywords.
    Also checks SNOMED parent concepts for broader condition matching
    (e.g., "Diabetic nephropathy" → both Diabetes and CKD).
    """
    if not required_factors:
        return True

    diag_text = ' '.join(d.lower() for d in (patient_diagnoses or []))

    factor_keywords = {
        'heavy_smoker': ['tobacco', 'smoker', 'smoking', 'nicotine', 'pack-year'],
        'ever_smoked': ['tobacco', 'smoker', 'smoking', 'nicotine', 'former smoker',
                        'history of tobacco'],
        'overweight': ['overweight', 'obese', 'obesity', 'bmi >25', 'bmi>25',
                       'bmi > 30', 'bmi>30'],
    }

    # SNOMED parent→child condition groups: if a patient has a specific
    # subtype diagnosis, also match the parent condition risk factor
    SNOMED_CONDITION_GROUPS = {
        'diabetes': ['diabetic', 'diabetes', 'dm ', 'dm1', 'dm2', 'type 1',
                     'type 2', 'niddm', 'iddm', 'diabetic nephropathy',
                     'diabetic retinopathy', 'diabetic neuropathy'],
        'ckd': ['chronic kidney', 'ckd', 'renal failure', 'nephropathy',
                'glomerulonephritis', 'nephrotic', 'dialysis', 'esrd',
                'diabetic nephropathy'],
        'cardiovascular': ['coronary', 'cad', 'chf', 'heart failure',
                           'atrial fibrillation', 'afib', 'cardiomyopathy',
                           'myocardial', 'angina', 'pvd', 'peripheral vascular'],
        'hypertension': ['hypertension', 'htn', 'high blood pressure',
                         'hypertensive'],
    }

    for factor in required_factors:
        # First try standard keyword matching
        keywords = factor_keywords.get(factor, [factor])
        if any(kw in diag_text for kw in keywords):
            continue

        # Then try SNOMED condition group matching
        group_keywords = SNOMED_CONDITION_GROUPS.get(factor, [])
        if group_keywords and any(kw in diag_text for kw in group_keywords):
            continue

        # Factor not matched
        return False
    return True


def evaluate_care_gaps(patient_data, app):
    """
    Evaluate which care gaps apply to a patient.

    Parameters
    ----------
    patient_data : dict
        Required keys:
            mrn : str
            age : int or None (calculated from dob if missing)
            sex : str ('M'/'F'/'male'/'female')
            dob : str (MM/DD/YYYY or YYYY-MM-DD)
        Optional keys:
            known_diagnoses : list[str]
            last_visit_date : str
            immunizations : list[str]  (vaccine names)
            existing_gaps : list[dict]  (current CareGap records)
    app : Flask app
        For database access.

    Returns
    -------
    list[dict]  — each dict has:
        gap_type, gap_name, description, interval_days,
        billing_code_pair, documentation_template, is_new (bool)
    """
    from models.caregap import CareGapRule

    age = patient_data.get('age')
    if age is None:
        age = _calculate_age(patient_data.get('dob', ''))
    if age is None:
        return []  # can't evaluate without age

    sex = patient_data.get('sex', '')
    diagnoses = patient_data.get('known_diagnoses', [])
    existing_gaps = patient_data.get('existing_gaps', [])

    # Build a set of gap_types already tracked (open or addressed)
    existing_types = set()
    for g in existing_gaps:
        if isinstance(g, dict):
            existing_types.add(g.get('gap_type', ''))
        else:
            existing_types.add(getattr(g, 'gap_type', ''))

    with app.app_context():
        rules = CareGapRule.query.filter_by(is_active=True).all()

    applicable = []

    for rule in rules:
        criteria = {}
        try:
            criteria = json.loads(rule.criteria_json or '{}')
        except (json.JSONDecodeError, TypeError):
            pass

        # Age check
        min_age = criteria.get('min_age', 0)
        max_age = criteria.get('max_age', 999)
        if not (min_age <= age <= max_age):
            continue

        # Sex check
        criteria_sex = criteria.get('sex', 'all')
        if not _patient_sex_matches(criteria_sex, sex):
            continue

        # Risk factor check
        risk_factors = criteria.get('risk_factors', [])
        if risk_factors and not _has_risk_factors(risk_factors, diagnoses):
            continue

        # Check if already tracked and not yet due for re-evaluation
        is_new = rule.gap_type not in existing_types

        # For one-time screenings (interval=0), skip if already addressed
        if rule.interval_days == 0 and not is_new:
            # Check if already addressed
            for g in existing_gaps:
                gt = g.get('gap_type', '') if isinstance(g, dict) else getattr(g, 'gap_type', '')
                addressed = g.get('is_addressed', False) if isinstance(g, dict) else getattr(g, 'is_addressed', False)
                if gt == rule.gap_type and addressed:
                    is_new = False
                    break
            else:
                is_new = True
            if not is_new:
                # Check if it was already addressed — skip
                for g in existing_gaps:
                    gt = g.get('gap_type', '') if isinstance(g, dict) else getattr(g, 'gap_type', '')
                    addressed = g.get('is_addressed', False) if isinstance(g, dict) else getattr(g, 'is_addressed', False)
                    if gt == rule.gap_type and addressed:
                        break
                else:
                    # Exists but not addressed — still applicable
                    applicable.append({
                        'gap_type': rule.gap_type,
                        'gap_name': rule.gap_name,
                        'description': rule.description,
                        'interval_days': rule.interval_days,
                        'billing_code_pair': rule.billing_code_pair,
                        'documentation_template': rule.documentation_template,
                        'is_new': False,
                    })
                continue

        applicable.append({
            'gap_type': rule.gap_type,
            'gap_name': rule.gap_name,
            'description': rule.description,
            'interval_days': rule.interval_days,
            'billing_code_pair': rule.billing_code_pair,
            'documentation_template': rule.documentation_template,
            'is_new': is_new,
        })

    return applicable


def evaluate_and_persist_gaps(user_id, mrn, patient_data, app):
    """
    Evaluate gaps for a patient and create/update CareGap records.

    This is the main entry point called by the schedule scraper (F15a).
    It compares the engine output against existing records and only
    creates new gaps for items not already tracked.

    Returns the count of new gaps created.
    """
    from models import db
    from models.caregap import CareGap

    with app.app_context():
        # Load existing gaps for this patient/user
        existing = CareGap.query.filter_by(
            user_id=user_id,
            mrn=mrn,
        ).all()

        patient_data['existing_gaps'] = existing

        applicable = evaluate_care_gaps(patient_data, app)

        # Build lookup of existing gap_types
        existing_types = {g.gap_type: g for g in existing}

        new_count = 0
        for gap_info in applicable:
            gt = gap_info['gap_type']
            if gt in existing_types:
                # Already tracked — check if it needs re-opening
                record = existing_types[gt]
                if record.is_addressed and gap_info['interval_days'] > 0:
                    # Check if enough time has passed to re-open
                    if record.completed_date:
                        days_since = (datetime.now(timezone.utc) - record.completed_date).days
                        if days_since >= gap_info['interval_days']:
                            record.is_addressed = False
                            record.status = 'open'
                            record.completed_date = None
                            record.documentation_snippet = ''
                            new_count += 1
                continue

            # New gap — create record
            new_gap = CareGap(
                user_id=user_id,
                mrn=mrn,
                patient_name=patient_data.get('patient_name', ''),
                gap_type=gt,
                gap_name=gap_info['gap_name'],
                description=gap_info['description'],
                billing_code_suggested=gap_info['billing_code_pair'],
                status='open',
                is_addressed=False,
            )
            db.session.add(new_gap)
            new_count += 1

        db.session.commit()
        return new_count


# ======================================================================
# Phase 35.4 — Calculator-Driven Care Gap Evaluation
# ======================================================================

# Rules triggered by CalculatorResult values (thresholds, not demographics)
_CALC_GAP_RULES = [
    {
        'gap_type': 'obesity_counseling',
        'gap_name': 'Obesity Counseling (BMI ≥ 30)',
        'description': (
            'BMI ≥ 30 — obesity counseling indicated. Eligible for '
            'G0447 (intensive behavioral therapy) or 99401-99404.'
        ),
        'billing_code_suggested': 'G0447',
        'calc_keys': ['bmi'],
        'threshold': 30.0,
        'age_min': None,
        'age_max': None,
    },
    {
        'gap_type': 'statin_therapy_discussion',
        'gap_name': 'Statin Therapy Discussion (PREVENT ≥ 7.5%)',
        'description': (
            'PREVENT 10yr CVD risk ≥ 7.5% — ACC/AHA statin therapy '
            'discussion recommended (shared decision-making).'
        ),
        'billing_code_suggested': '99401-99215',
        'calc_keys': ['prevent'],
        'threshold': 7.5,
        'age_min': None,
        'age_max': None,
    },
    {
        'gap_type': 'fh_evaluation',
        'gap_name': 'Familial Hypercholesterolemia Evaluation (LDL ≥ 190)',
        'description': (
            'LDL ≥ 190 mg/dL — evaluate for familial hypercholesterolemia '
            'per Dutch FH criteria. Consider genetic testing (81401).'
        ),
        'billing_code_suggested': '81401',
        'calc_keys': ['ldl', 'ldl_calculated'],
        'threshold': 190.0,
        'age_min': None,
        'age_max': None,
    },
    {
        'gap_type': 'lung_cancer_screening',
        'gap_name': 'Lung Cancer Screening — LDCT (pack-years ≥ 20)',
        'description': (
            'Pack-year history ≥ 20 — eligible for annual LDCT lung cancer '
            'screening per USPSTF Grade B recommendation (age 50-80, '
            'current smoker or quit within 15 years). '
            'Order 71271 + G0296 counseling visit.'
        ),
        'billing_code_suggested': '71271 / G0296',
        'calc_keys': ['pack_years'],
        'threshold': 20.0,
        'age_min': 50,
        'age_max': 80,
    },
]


def evaluate_calculator_care_gaps(mrn: str, user_id: int, patient_age, app) -> int:
    """
    Phase 35.4 — Create CareGap records triggered by CalculatorResult thresholds.

    Parameters
    ----------
    mrn : str
    user_id : int
    patient_age : float | None  — used for age-gated rules (LDCT)
    app : Flask app instance

    Returns
    -------
    int — number of new gaps created or reopened
    """
    from models import db
    from models.calculator import CalculatorResult
    from models.caregap import CareGap
    from datetime import datetime, timezone

    new_count = 0

    with app.app_context():
        for rule in _CALC_GAP_RULES:
            try:
                # Age gate (if applicable)
                if rule['age_min'] is not None:
                    if patient_age is None:
                        continue
                    if not (rule['age_min'] <= patient_age <= rule['age_max']):
                        continue

                # Find best matching CalculatorResult for any of the calc_keys
                row = None
                for ck in rule['calc_keys']:
                    row = (CalculatorResult.query
                           .filter_by(mrn=mrn, calculator_key=ck, is_current=True)
                           .order_by(CalculatorResult.computed_at.desc())
                           .first())
                    if row and row.score_value is not None:
                        break

                if row is None or row.score_value is None:
                    continue
                if row.score_value < rule['threshold']:
                    continue

                # Check existing gap record
                existing = (CareGap.query
                            .filter_by(user_id=user_id, mrn=mrn, gap_type=rule['gap_type'])
                            .first())

                if existing:
                    if not existing.is_addressed:
                        continue  # already open — do not duplicate
                    # Threshold still met but was addressed — re-open
                    existing.is_addressed = False
                    existing.status = 'open'
                    existing.completed_date = None
                    existing.updated_at = datetime.now(timezone.utc)
                    new_count += 1
                else:
                    new_gap = CareGap(
                        user_id=user_id,
                        mrn=mrn,
                        patient_name='',
                        gap_type=rule['gap_type'],
                        gap_name=rule['gap_name'],
                        description=rule['description'],
                        billing_code_suggested=rule['billing_code_suggested'],
                        status='open',
                        is_addressed=False,
                    )
                    db.session.add(new_gap)
                    new_count += 1

            except Exception as e:
                logger.debug(
                    'evaluate_calculator_care_gaps(%s, %s): %s',
                    mrn, rule['gap_type'], e
                )

        try:
            db.session.commit()
        except Exception as e:
            logger.error('evaluate_calculator_care_gaps commit error: %s', e)
            db.session.rollback()

    return new_count

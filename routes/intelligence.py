"""
NP Companion — Clinical Intelligence API Routes
File: routes/intelligence.py

JSON API endpoints that power the Phase 10 intelligence layer widgets.
All endpoints return JSON and are called asynchronously from the patient
chart and dashboard templates.  No PHI is sent to external APIs — only
drug names, ICD-10 codes, and LOINC codes.

Features powered by this module:
- NEW-A: Drug Recall Alert System
- NEW-C: PubMed Guideline Lookup Panel
- NEW-D: Formulary Gap Detection
- NEW-E: Patient Education Auto-Draft
- NEW-F: Drug Safety Panel (interactions + recalls + monitoring)
- F22:   Morning Briefing data
"""

import json
import logging
from datetime import date, datetime, timezone

from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user

from models import db
from models.patient import (
    PatientRecord, PatientMedication, PatientDiagnosis,
    PatientAllergy, PatientImmunization, RxNormCache,
)
from models.schedule import Schedule

logger = logging.getLogger(__name__)

intel_bp = Blueprint('intelligence', __name__)


# ======================================================================
# Billing Opportunity Actions (capture / dismiss)
# ======================================================================
@intel_bp.route('/api/billing/opportunity/<int:opp_id>/capture', methods=['POST'])
@login_required
def capture_opportunity(opp_id):
    """Mark a billing opportunity as captured (provider documented and billed)."""
    from models.billing import BillingOpportunity
    opp = BillingOpportunity.query.filter_by(
        id=opp_id, user_id=current_user.id
    ).first()
    if not opp:
        return jsonify({'success': False, 'error': 'Opportunity not found'}), 404
    opp.mark_captured()
    db.session.commit()
    return jsonify({'success': True, 'status': opp.status})


@intel_bp.route('/api/billing/opportunity/<int:opp_id>/dismiss', methods=['POST'])
@login_required
def dismiss_opportunity(opp_id):
    """Dismiss a billing opportunity with an optional reason."""
    from models.billing import BillingOpportunity
    data = request.get_json(silent=True) or {}
    opp = BillingOpportunity.query.filter_by(
        id=opp_id, user_id=current_user.id
    ).first()
    if not opp:
        return jsonify({'success': False, 'error': 'Opportunity not found'}), 404
    opp.dismiss(reason=data.get('reason', ''))
    db.session.commit()
    return jsonify({'success': True, 'status': opp.status})


@intel_bp.route('/api/patient/<mrn>/billing-opportunities')
@login_required
def patient_billing(mrn):
    """Return billing opportunities for a specific patient (for chart widget)."""
    from models.billing import BillingOpportunity
    from utils import safe_patient_id
    try:
        mrn_hash = safe_patient_id(mrn)
    except ValueError:
        return jsonify({'opportunities': []})

    opps = BillingOpportunity.query.filter(
        BillingOpportunity.user_id == current_user.id,
        BillingOpportunity.patient_mrn_hash == mrn_hash,
        BillingOpportunity.status.in_(['pending', 'partial']),
    ).order_by(BillingOpportunity.estimated_revenue.desc()).all()

    return jsonify({
        'opportunities': [{
            'id': o.id,
            'type': o.opportunity_type,
            'codes': o.applicable_codes,
            'revenue': o.estimated_revenue or 0,
            'confidence': o.confidence_level,
            'basis': o.eligibility_basis or '',
            'documentation': o.documentation_required or '',
            'insurer_caveat': o.insurer_caveat or '',
        } for o in opps]
    })


# ======================================================================
# Clinical Spell Check / Fuzzy Matcher
# ======================================================================
@intel_bp.route('/api/spell-check', methods=['POST'])
@login_required
def spell_check():
    """
    Analyze free text for medical terminology issues: abbreviations,
    misspellings, drug name fuzzy matches, diagnosis fuzzy matches.
    Returns findings with confidence scores for provider review.
    """
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    use_api = data.get('use_api', True)

    if not text:
        return jsonify({'findings': []})

    try:
        from app.services.clinical_spell_check import analyze_text
        findings = analyze_text(text, use_api=use_api)
        return jsonify({
            'findings': findings,
            'total': len(findings),
            'high_confidence': len([f for f in findings if f['confidence'] >= 0.85]),
            'needs_review': len([f for f in findings if 0.6 <= f['confidence'] < 0.85]),
        })
    except Exception as e:
        logger.debug('Spell check failed: %s', e)
        return jsonify({'findings': [], 'error': str(e)})


@intel_bp.route('/api/spell-check/expand', methods=['POST'])
@login_required
def spell_check_expand():
    """Expand a single medical abbreviation."""
    data = request.get_json(silent=True) or {}
    abbrev = (data.get('abbreviation') or '').strip()
    if not abbrev:
        return jsonify({'expansion': None})

    from app.services.clinical_spell_check import expand_abbreviation
    expansion = expand_abbreviation(abbrev)
    return jsonify({'abbreviation': abbrev, 'expansion': expansion})


# ======================================================================
# Post-Visit Billing Review
# ======================================================================
@intel_bp.route('/billing/review/<mrn>')
@login_required
def billing_review(mrn):
    """Post-visit billing review for a specific patient."""
    from models.billing import BillingOpportunity

    opportunities = (
        BillingOpportunity.query
        .filter_by(user_id=current_user.id)
        .filter(BillingOpportunity.patient_mrn_hash.like(f'%{mrn[-6:]}%') if len(mrn) > 6 else BillingOpportunity.patient_mrn_hash != '')
        .order_by(BillingOpportunity.visit_date.desc())
        .limit(20)
        .all()
    )

    record = PatientRecord.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).first()

    return render_template(
        'billing_review.html',
        mrn=mrn,
        record=record,
        opportunities=opportunities,
    )


# ======================================================================
# API Setup Guide (accessible to all authenticated users)
# ======================================================================
@intel_bp.route('/api-setup-guide')
@login_required
def api_setup_guide():
    """Display the provider-facing API setup instructions."""
    return render_template('api_setup_guide.html')


# ======================================================================
# F17b: ICD-10 Specificity Reminder
# ======================================================================
@intel_bp.route('/api/icd10/specificity')
@login_required
def icd10_specificity():
    """
    Check if an ICD-10 code has more specific child codes available.
    Returns child codes if the current code is non-terminal.
    """
    code = request.args.get('code', '').strip().upper()
    if not code or len(code) < 3:
        return jsonify({'has_children': False, 'children': []})

    try:
        from app.services.api.icd10 import ICD10Service
        svc = ICD10Service(db)
        children = svc.get_children(code)
        if children:
            return jsonify({
                'has_children': True,
                'code': code,
                'children': children[:10],
                'message': f'More specific code available for {code}',
            })
        return jsonify({'has_children': False, 'code': code, 'children': []})
    except Exception as e:
        logger.debug('ICD-10 specificity check failed: %s', e)
        return jsonify({'has_children': False, 'children': []})


# ======================================================================
# LOINC Lab Reference Range Lookup
# ======================================================================
@intel_bp.route('/api/loinc/lookup')
@login_required
def loinc_lookup():
    """Look up LOINC code properties including reference ranges."""
    code = request.args.get('code', '').strip()
    if not code:
        return jsonify({'error': 'No LOINC code provided'})

    try:
        from app.services.api.loinc import LOINCService
        from app.api_config import LOINC_USERNAME, LOINC_PASSWORD
        svc = LOINCService(db, username=LOINC_USERNAME, password=LOINC_PASSWORD)
        result = svc.lookup_code(code)
        return jsonify(result or {'error': 'Code not found'})
    except Exception as e:
        logger.debug('LOINC lookup failed for %s: %s', code, e)
        return jsonify({'error': 'LOINC service unavailable'})


# ======================================================================
# NEW-B: Abnormal Lab Interpretation Assistant
# ======================================================================
@intel_bp.route('/api/patient/<mrn>/lab-interpretation')
@login_required
def lab_interpretation(mrn):
    """
    Return lab interpretation context: LOINC reference ranges and
    medication cross-reference for abnormal values.
    """
    from models.labtrack import LabTrack

    tracks = LabTrack.query.filter_by(
        user_id=current_user.id, mrn=mrn
    ).all()

    if not tracks:
        return jsonify({'interpretations': []})

    medications = PatientMedication.query.filter_by(
        user_id=current_user.id, mrn=mrn, status='active'
    ).all()
    med_names = [m.drug_name.split()[0].lower() for m in medications if m.drug_name]

    interpretations = []
    for track in tracks:
        # Get latest result
        latest = None
        if track.results:
            sorted_results = sorted(track.results, key=lambda r: r.result_date or datetime.min, reverse=True)
            latest = sorted_results[0] if sorted_results else None

        if not latest or not latest.result_value:
            continue

        # Try to parse numeric value
        try:
            value = float(latest.result_value.replace(',', '').strip())
        except (ValueError, TypeError):
            continue

        interp = {
            'lab_name': track.lab_name,
            'value': latest.result_value,
            'date': latest.result_date.strftime('%m/%d/%Y') if latest.result_date else '',
            'status': track.status,
            'is_abnormal': False,
            'direction': '',
            'context': '',
            'reference_range': '',
            'drug_context': [],
        }

        # Check against provider-set thresholds
        if track.alert_low and value < track.alert_low:
            interp['is_abnormal'] = True
            interp['direction'] = 'low'
        elif track.alert_high and value > track.alert_high:
            interp['is_abnormal'] = True
            interp['direction'] = 'high'
        elif track.critical_low and value < track.critical_low:
            interp['is_abnormal'] = True
            interp['direction'] = 'critically low'
        elif track.critical_high and value > track.critical_high:
            interp['is_abnormal'] = True
            interp['direction'] = 'critically high'

        if track.alert_low or track.alert_high:
            lo = str(track.alert_low) if track.alert_low else ''
            hi = str(track.alert_high) if track.alert_high else ''
            interp['reference_range'] = f"{lo} – {hi}"

        # Cross-reference with medications for abnormal labs
        if interp['is_abnormal']:
            # Common lab-medication associations
            LAB_DRUG_ASSOCIATIONS = {
                'potassium': ['lisinopril', 'losartan', 'enalapril', 'spironolactone', 'trimethoprim'],
                'creatinine': ['lisinopril', 'losartan', 'ibuprofen', 'naproxen', 'metformin'],
                'glucose': ['metformin', 'glipizide', 'insulin', 'prednisone', 'dexamethasone'],
                'hemoglobin a1c': ['metformin', 'glipizide', 'insulin', 'semaglutide', 'empagliflozin'],
                'a1c': ['metformin', 'glipizide', 'insulin', 'semaglutide', 'empagliflozin'],
                'tsh': ['levothyroxine', 'liothyronine', 'amiodarone', 'lithium'],
                'alt': ['atorvastatin', 'rosuvastatin', 'simvastatin', 'methotrexate', 'acetaminophen'],
                'ast': ['atorvastatin', 'rosuvastatin', 'simvastatin', 'methotrexate'],
                'inr': ['warfarin'],
                'platelets': ['warfarin', 'heparin', 'valproic acid'],
                'wbc': ['methotrexate', 'azathioprine', 'clozapine'],
                'sodium': ['hydrochlorothiazide', 'furosemide', 'carbamazepine', 'desmopressin'],
                'magnesium': ['omeprazole', 'pantoprazole', 'furosemide'],
                'lithium': ['lithium'],
                'digoxin': ['digoxin'],
            }

            lab_lower = track.lab_name.lower()
            for lab_key, drugs in LAB_DRUG_ASSOCIATIONS.items():
                if lab_key in lab_lower:
                    for drug in drugs:
                        if drug in med_names:
                            interp['drug_context'].append({
                                'drug': drug.title(),
                                'note': f"Patient is on {drug.title()} which can affect {track.lab_name} levels",
                            })

            if interp['drug_context']:
                interp['context'] = f"{track.lab_name} is {interp['direction']} — consider medication effect"
            else:
                interp['context'] = f"{track.lab_name} is {interp['direction']} — review clinical significance"

        if interp['is_abnormal'] or track.status in ('critical', 'overdue'):
            interpretations.append(interp)

    return jsonify({'interpretations': interpretations})


# ======================================================================
# NEW-A + NEW-F: Drug Safety Panel  (recalls + interactions + monitoring)
# ======================================================================
@intel_bp.route('/api/patient/<mrn>/drug-safety')
@login_required
def drug_safety(mrn):
    """
    Return combined drug safety data for a patient:
      - Active FDA recalls for their medications
      - Drug interaction flags from FDA labels
      - Monitoring requirements
    """
    medications = PatientMedication.query.filter_by(
        user_id=current_user.id, mrn=mrn, status='active'
    ).all()

    if not medications:
        return jsonify({'recalls': [], 'interactions': [], 'monitoring': []})

    drug_names = [m.drug_name.split()[0] for m in medications if m.drug_name]
    rxcuis = [m.rxnorm_cui for m in medications if getattr(m, 'rxnorm_cui', '')]

    recalls = []
    interactions = []
    monitoring = []

    # --- Recalls via OpenFDA ---
    try:
        from app.services.api.openfda_recalls import OpenFDARecallsService
        svc = OpenFDARecallsService(db)
        recall_results = svc.check_drug_list_for_recalls(drug_names)
        for r in recall_results:
            recalls.append({
                'drug_name': r.get('drug_name', ''),
                'reason': r.get('reason', ''),
                'classification': r.get('classification', ''),
                'priority': r.get('priority', 'low'),
                'status': r.get('status', ''),
                'recall_date': r.get('recall_initiation_date', ''),
            })
    except Exception as e:
        logger.debug('Recall check failed: %s', e)

    # --- Interactions via OpenFDA Labels ---
    try:
        from app.services.api.openfda_labels import OpenFDALabelsService
        label_svc = OpenFDALabelsService(db)
        # Check each medication's label for interaction warnings with other meds
        for med in medications:
            drug = med.drug_name.split()[0] if med.drug_name else ''
            if not drug:
                continue
            cui = getattr(med, 'rxnorm_cui', '') or ''
            try:
                label = label_svc.get_label_by_rxcui(cui) if cui else label_svc.get_label_by_name(drug)
                if not label:
                    continue
                interaction_text = label.get('drug_interactions', '')
                if interaction_text:
                    # Check if any OTHER active medication is mentioned
                    for other in medications:
                        if other.id == med.id:
                            continue
                        other_name = (other.drug_name or '').split()[0].lower()
                        if other_name and len(other_name) > 3 and other_name in interaction_text.lower():
                            interactions.append({
                                'drug_a': drug,
                                'drug_b': other_name.title(),
                                'detail': interaction_text[:300],
                                'severity': 'warning',
                            })

                # Monitoring requirements
                monitoring_text = label.get('warnings_and_cautions', '') or ''
                if any(kw in monitoring_text.lower() for kw in ['monitor', 'check', 'periodic', 'laboratory']):
                    monitoring.append({
                        'drug': drug,
                        'requirement': monitoring_text[:200],
                    })
            except Exception:
                continue
    except Exception as e:
        logger.debug('Label interaction check failed: %s', e)

    return jsonify({
        'recalls': recalls,
        'interactions': interactions,
        'monitoring': monitoring,
        'drug_count': len(medications),
    })


# ======================================================================
# NEW-C: PubMed Guideline Lookup Panel
# ======================================================================
@intel_bp.route('/api/patient/<mrn>/guidelines')
@login_required
def guidelines(mrn):
    """
    Return recent PubMed clinical guidelines for the patient's
    top diagnoses. Results are cached per-diagnosis for 30 days.
    """
    diagnoses = PatientDiagnosis.query.filter_by(
        user_id=current_user.id, mrn=mrn, status='active'
    ).order_by(PatientDiagnosis.id.desc()).limit(5).all()

    if not diagnoses:
        return jsonify({'guidelines': [], 'conditions_searched': []})

    results = []
    conditions_searched = []

    try:
        from app.services.api.pubmed import PubMedService
        svc = PubMedService(db)

        for diag in diagnoses[:3]:  # Top 3 diagnoses
            name = diag.diagnosis_name or ''
            if not name or len(name) < 3:
                continue
            conditions_searched.append(name)
            articles = svc.search_guidelines(name, max_results=3)
            for a in articles:
                results.append({
                    'condition': name,
                    'title': a.get('title', ''),
                    'journal': a.get('journal', ''),
                    'year': a.get('year', ''),
                    'authors': a.get('authors', ''),
                    'pmid': a.get('pmid', ''),
                    'doi': a.get('doi', ''),
                    'is_primary_care': a.get('is_primary_care_journal', False),
                })
    except Exception as e:
        logger.debug('PubMed guideline lookup failed: %s', e)

    return jsonify({
        'guidelines': results,
        'conditions_searched': conditions_searched,
    })


# ======================================================================
# NEW-D: Formulary Gap Detection
# ======================================================================
@intel_bp.route('/api/patient/<mrn>/formulary-gaps')
@login_required
def formulary_gaps(mrn):
    """
    Detect chronic conditions that lack expected medication classes.
    Compares active diagnoses against active medication classes.
    """
    diagnoses = PatientDiagnosis.query.filter_by(
        user_id=current_user.id, mrn=mrn, status='active'
    ).all()
    medications = PatientMedication.query.filter_by(
        user_id=current_user.id, mrn=mrn, status='active'
    ).all()

    if not diagnoses:
        return jsonify({'gaps': []})

    med_names_lower = set()
    for m in medications:
        if m.drug_name:
            med_names_lower.add(m.drug_name.lower())
            # Also add first word (generic name often)
            med_names_lower.add(m.drug_name.split()[0].lower())

    # Condition → expected drug class mappings (evidence-based defaults)
    CONDITION_DRUG_MAP = {
        'hypertension': {
            'icd_prefixes': ['I10', 'I11', 'I12', 'I13', 'I15'],
            'expected_classes': ['ACE inhibitor', 'ARB', 'calcium channel blocker', 'thiazide', 'beta blocker'],
            'drug_keywords': ['lisinopril', 'losartan', 'amlodipine', 'hydrochlorothiazide', 'metoprolol',
                              'enalapril', 'valsartan', 'olmesartan', 'nifedipine', 'atenolol',
                              'ramipril', 'irbesartan', 'diltiazem', 'chlorthalidone', 'carvedilol',
                              'benazepril', 'telmisartan', 'felodipine', 'bisoprolol', 'hctz'],
        },
        'type 2 diabetes': {
            'icd_prefixes': ['E11'],
            'expected_classes': ['metformin', 'SGLT2 inhibitor', 'GLP-1 agonist', 'DPP-4 inhibitor', 'insulin', 'sulfonylurea'],
            'drug_keywords': ['metformin', 'empagliflozin', 'dapagliflozin', 'canagliflozin',
                              'semaglutide', 'liraglutide', 'dulaglutide', 'tirzepatide',
                              'sitagliptin', 'linagliptin', 'saxagliptin',
                              'glipizide', 'glyburide', 'glimepiride',
                              'insulin', 'jardiance', 'ozempic', 'mounjaro', 'farxiga', 'januvia',
                              'trulicity', 'wegovy', 'victoza'],
        },
        'hyperlipidemia': {
            'icd_prefixes': ['E78'],
            'expected_classes': ['statin', 'PCSK9 inhibitor', 'ezetimibe', 'fibrate'],
            'drug_keywords': ['atorvastatin', 'rosuvastatin', 'simvastatin', 'pravastatin',
                              'lovastatin', 'pitavastatin', 'ezetimibe', 'fenofibrate',
                              'lipitor', 'crestor', 'zetia', 'repatha', 'praluent',
                              'evolocumab', 'alirocumab', 'gemfibrozil'],
        },
        'heart failure': {
            'icd_prefixes': ['I50'],
            'expected_classes': ['ACE inhibitor/ARB/ARNI', 'beta blocker', 'mineralocorticoid antagonist', 'SGLT2 inhibitor', 'diuretic'],
            'drug_keywords': ['lisinopril', 'losartan', 'sacubitril', 'entresto',
                              'carvedilol', 'metoprolol', 'bisoprolol',
                              'spironolactone', 'eplerenone',
                              'empagliflozin', 'dapagliflozin',
                              'furosemide', 'bumetanide', 'torsemide'],
        },
        'atrial fibrillation': {
            'icd_prefixes': ['I48'],
            'expected_classes': ['anticoagulant', 'rate control'],
            'drug_keywords': ['apixaban', 'rivaroxaban', 'warfarin', 'dabigatran', 'edoxaban',
                              'eliquis', 'xarelto', 'coumadin',
                              'metoprolol', 'diltiazem', 'digoxin', 'amiodarone'],
        },
        'hypothyroidism': {
            'icd_prefixes': ['E03'],
            'expected_classes': ['thyroid hormone'],
            'drug_keywords': ['levothyroxine', 'synthroid', 'liothyronine', 'armour thyroid',
                              'tirosint', 'cytomel', 'nature-throid'],
        },
        'GERD': {
            'icd_prefixes': ['K21'],
            'expected_classes': ['proton pump inhibitor', 'H2 blocker'],
            'drug_keywords': ['omeprazole', 'pantoprazole', 'lansoprazole', 'esomeprazole',
                              'rabeprazole', 'famotidine', 'ranitidine',
                              'prilosec', 'protonix', 'nexium', 'prevacid', 'pepcid'],
        },
        'asthma': {
            'icd_prefixes': ['J45'],
            'expected_classes': ['inhaled corticosteroid', 'SABA', 'LABA'],
            'drug_keywords': ['albuterol', 'fluticasone', 'budesonide', 'montelukast',
                              'ventolin', 'proair', 'advair', 'symbicort', 'breo',
                              'salmeterol', 'formoterol', 'mometasone', 'beclomethasone'],
        },
        'COPD': {
            'icd_prefixes': ['J44'],
            'expected_classes': ['LAMA', 'LABA', 'inhaled corticosteroid', 'SABA'],
            'drug_keywords': ['tiotropium', 'umeclidinium', 'albuterol',
                              'spiriva', 'incruse', 'trelegy', 'breo', 'anoro',
                              'fluticasone', 'budesonide', 'symbicort'],
        },
        'depression': {
            'icd_prefixes': ['F32', 'F33'],
            'expected_classes': ['SSRI', 'SNRI', 'bupropion', 'TCA', 'atypical antidepressant'],
            'drug_keywords': ['sertraline', 'fluoxetine', 'escitalopram', 'citalopram', 'paroxetine',
                              'venlafaxine', 'duloxetine', 'desvenlafaxine', 'bupropion',
                              'mirtazapine', 'trazodone', 'amitriptyline',
                              'zoloft', 'prozac', 'lexapro', 'cymbalta', 'wellbutrin', 'effexor'],
        },
        'anxiety': {
            'icd_prefixes': ['F41'],
            'expected_classes': ['SSRI', 'SNRI', 'buspirone', 'hydroxyzine'],
            'drug_keywords': ['sertraline', 'escitalopram', 'fluoxetine', 'paroxetine',
                              'venlafaxine', 'duloxetine', 'buspirone', 'hydroxyzine',
                              'zoloft', 'lexapro', 'prozac', 'cymbalta', 'effexor'],
        },
        'osteoporosis': {
            'icd_prefixes': ['M80', 'M81'],
            'expected_classes': ['bisphosphonate', 'denosumab', 'calcium/vitamin D'],
            'drug_keywords': ['alendronate', 'risedronate', 'ibandronate', 'zoledronic',
                              'denosumab', 'prolia', 'fosamax', 'boniva', 'reclast',
                              'calcium', 'vitamin d', 'cholecalciferol'],
        },
    }

    gaps = []
    for diag in diagnoses:
        icd = (diag.icd10_code or '').upper()
        for condition, mapping in CONDITION_DRUG_MAP.items():
            # Check if diagnosis matches condition ICD prefixes
            if not any(icd.startswith(prefix) for prefix in mapping['icd_prefixes']):
                continue
            # Check if any expected medication keyword is in the patient's med list
            has_treatment = any(
                kw in name for kw in mapping['drug_keywords']
                for name in med_names_lower
            )
            if not has_treatment:
                gaps.append({
                    'condition': condition.title(),
                    'diagnosis': diag.diagnosis_name,
                    'icd10': icd,
                    'expected_classes': mapping['expected_classes'],
                    'message': f"No {' / '.join(mapping['expected_classes'][:3])} found for {condition}",
                })
            break  # Only match first condition per diagnosis

    return jsonify({'gaps': gaps})


# ======================================================================
# NEW-E: Patient Education Content
# ======================================================================
@intel_bp.route('/api/patient/<mrn>/education')
@login_required
def patient_education(mrn):
    """
    Return patient education content from MedlinePlus for the patient's
    active diagnoses and medications.
    """
    diagnoses = PatientDiagnosis.query.filter_by(
        user_id=current_user.id, mrn=mrn, status='active'
    ).limit(5).all()
    medications = PatientMedication.query.filter_by(
        user_id=current_user.id, mrn=mrn, status='active'
    ).limit(5).all()

    education = []
    try:
        from app.services.api.medlineplus import MedlinePlusService
        svc = MedlinePlusService(db)

        # Education for top diagnoses
        for diag in diagnoses[:3]:
            icd = (diag.icd10_code or '').strip()
            if not icd:
                continue
            content = svc.get_for_icd10(icd)
            if content and content.get('title'):
                education.append({
                    'type': 'diagnosis',
                    'source_name': diag.diagnosis_name,
                    'title': content['title'],
                    'summary': content.get('summary', '')[:500],
                    'url': content.get('url', ''),
                    'language': content.get('language', 'en'),
                })

        # Education for medications
        for med in medications[:3]:
            cui = getattr(med, 'rxnorm_cui', '') or ''
            if not cui:
                continue
            content = svc.get_for_rxcui(cui)
            if content and content.get('title'):
                education.append({
                    'type': 'medication',
                    'source_name': med.drug_name,
                    'title': content['title'],
                    'summary': content.get('summary', '')[:500],
                    'url': content.get('url', ''),
                    'language': content.get('language', 'en'),
                })
    except Exception as e:
        logger.debug('Patient education fetch failed: %s', e)

    return jsonify({'education': education})


# ======================================================================
# F22: Morning Briefing
# ======================================================================
@intel_bp.route('/briefing')
@login_required
def morning_briefing():
    """
    Morning Briefing page — aggregates weather, schedule overview,
    recall alerts, care gap summary, and guideline pre-loads.
    """
    today = date.today()

    # Schedule overview
    appointments = Schedule.query.filter_by(
        user_id=current_user.id, appointment_date=today
    ).order_by(Schedule.appointment_time).all()

    # Weather
    weather = {}
    try:
        from app.services.api.open_meteo import OpenMeteoService
        weather_svc = OpenMeteoService(db)
        weather = weather_svc.get_current_conditions() or {}
    except Exception as e:
        logger.debug('Weather fetch failed: %s', e)

    # Recall alerts across all active medications for this provider's patients
    recall_alerts = []
    try:
        from app.services.api.openfda_recalls import OpenFDARecallsService
        recall_svc = OpenFDARecallsService(db)
        # Get unique drug names across all claimed patients
        med_names = [
            row[0] for row in
            db.session.query(PatientMedication.drug_name)
            .filter(
                PatientMedication.user_id == current_user.id,
                PatientMedication.status == 'active',
            )
            .distinct().limit(50).all()
            if row[0]
        ]
        if med_names:
            drug_first_words = list(set(n.split()[0] for n in med_names if n))
            results = recall_svc.check_drug_list_for_recalls(drug_first_words)
            recall_alerts = [r for r in results if r.get('priority') in ('critical', 'high')]
    except Exception as e:
        logger.debug('Briefing recall check failed: %s', e)

    # Care gap summary
    from models.caregap import CareGap
    open_gaps = CareGap.query.filter_by(
        user_id=current_user.id, is_addressed=False
    ).all()
    gap_count = len(open_gaps)

    # Claimed patient count
    claimed_count = PatientRecord.query.filter_by(
        claimed_by=current_user.id
    ).count()

    return render_template(
        'morning_briefing.html',
        today=today,
        appointments=appointments,
        weather=weather,
        recall_alerts=recall_alerts,
        gap_count=gap_count,
        open_gaps=open_gaps[:10],
        claimed_count=claimed_count,
        appointment_count=len(appointments),
    )


# ======================================================================
# Admin API Configuration
# ======================================================================
@intel_bp.route('/admin/api', methods=['GET', 'POST'])
@login_required
def admin_api_settings():
    """Admin page for managing API keys and cache."""
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin only'}), 403

    if request.method == 'POST':
        action = request.form.get('action', '')
        if action == 'flush_cache':
            api_name = request.form.get('api_name', '')
            if api_name:
                try:
                    from app.services.api.cache_manager import CacheManager
                    cache = CacheManager(db)
                    cache.flush_api(api_name)
                    from flask import flash
                    flash(f'Cache flushed for {api_name}.', 'success')
                except Exception as e:
                    from flask import flash
                    flash(f'Cache flush failed: {e}', 'danger')

    # Get cache stats
    cache_stats = {}
    try:
        from app.services.api.cache_manager import CacheManager
        cache = CacheManager(db)
        cache_stats = cache.get_all_api_stats()
    except Exception:
        pass

    return render_template(
        'admin_api.html',
        cache_stats=cache_stats,
    )

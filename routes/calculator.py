"""Phase 33.2 — Calculator Blueprint
Routes for the clinical calculator library and patient risk tool picker.
"""

from flask import Blueprint, render_template, jsonify, request, abort
from flask_login import current_user, login_required

calculator_bp = Blueprint('calculator', __name__)


@calculator_bp.route('/calculators')
@login_required
def calculator_index():
    """Full calculator library — standalone page with category tabs and search."""
    from app.services.calculator_registry import (
        CALCULATOR_REGISTRY, CALCULATOR_CATEGORIES, AUTOMATION_LABELS
    )
    return render_template(
        'calculators.html',
        registry=CALCULATOR_REGISTRY,
        categories=CALCULATOR_CATEGORIES,
        automation_labels=AUTOMATION_LABELS,
    )


@calculator_bp.route('/calculators/<key>')
@login_required
def calculator_detail(key):
    """Single calculator page — form with inputs and result display."""
    from app.services.calculator_registry import (
        CALCULATOR_REGISTRY, AUTOMATION_LABELS
    )
    calc = CALCULATOR_REGISTRY.get(key)
    if not calc:
        abort(404)
    return render_template(
        'calculator_detail.html',
        calc=calc,
        key=key,
        automation_labels=AUTOMATION_LABELS,
        mrn=None,
    )


@calculator_bp.route('/calculators/<key>/compute', methods=['POST'])
@login_required
def calculator_compute(key):
    """Compute a calculator result from submitted form data; persist CalculatorResult."""
    from app.services.calculator_registry import CALCULATOR_REGISTRY
    from app.services.calculator_engine import CalculatorEngine

    calc = CALCULATOR_REGISTRY.get(key)
    if not calc:
        return jsonify({'success': False, 'error': 'Unknown calculator'}), 404

    if calc.get('status') == 'restricted_or_licensed':
        return jsonify({'success': False, 'error': 'Licensed instrument — use manual entry only.'}), 400

    data = request.get_json(silent=True) or request.form.to_dict()
    if not data:
        return jsonify({'success': False, 'error': 'No input data provided'}), 400

    try:
        engine = CalculatorEngine()
        mrn = data.pop('mrn', None)
        user_id = current_user.id

        calc_type = calc.get('type', '')
        if calc_type == 'questionnaire' or key in engine.QUESTIONNAIRE_DEFS:
            result = engine.compute_questionnaire(key, data)
        elif calc_type == 'rule_based' or key in engine.RULE_DEFS:
            result = engine.compute_rule_calculator(key, data)
        elif key == 'bmi':
            result = engine.compute_bmi(data)
        elif key == 'ldl':
            result = engine.compute_ldl(data)
        elif key == 'pack_years':
            result = engine.compute_pack_years(data)
        elif key == 'prevent':
            demographics = {k: data.get(k) for k in ('age', 'sex', 'smoking_status', 'has_diabetes')}
            vitals = {k: data.get(k) for k in ('systolic_bp',)}
            labs = {k: data.get(k) for k in ('total_cholesterol', 'hdl', 'triglycerides', 'egfr')}
            meds = {k: data.get(k) for k in ('antihypertensive', 'statin', 'has_diabetes')}
            result = engine.compute_prevent(demographics, vitals, labs, meds)
        else:
            return jsonify({'success': False, 'error': f'No compute method for calculator: {key}'}), 400

        # Persist if MRN provided
        if mrn:
            try:
                engine._persist_result(result, mrn, user_id)
            except Exception:
                pass  # Persist failure should not block returning result

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@calculator_bp.route('/patient/<mrn>/risk-tools')
@login_required
def patient_risk_tools(mrn):
    """Risk Tool picker in patient context — pre-fills from EHR data."""
    from app.services.calculator_registry import (
        CALCULATOR_REGISTRY, CALCULATOR_CATEGORIES, AUTOMATION_LABELS
    )
    from app.services.calculator_engine import CalculatorEngine
    from models.calculator import CalculatorResult

    engine = CalculatorEngine()
    prefilled = {}
    for calc_key in CALCULATOR_REGISTRY:
        try:
            prefilled[calc_key] = engine.get_prefilled_inputs(calc_key, mrn)
        except Exception:
            prefilled[calc_key] = {}

    # Load latest scores for this patient
    latest_scores = {}
    try:
        latest_scores = engine.get_latest_scores(mrn, current_user.id)
    except Exception:
        pass

    return render_template(
        'patient_risk_tools.html',
        mrn=mrn,
        registry=CALCULATOR_REGISTRY,
        categories=CALCULATOR_CATEGORIES,
        automation_labels=AUTOMATION_LABELS,
        prefilled=prefilled,
        latest_scores=latest_scores,
    )


@calculator_bp.route('/patient/<mrn>/score-history/<key>')
@login_required
def score_history(mrn, key):
    """Phase 35.1 — Returns historical scores for a patient+calculator as JSON."""
    from models.calculator import CalculatorResult
    results = CalculatorResult.query.filter_by(
        user_id=current_user.id, mrn=mrn, calculator_key=key
    ).order_by(CalculatorResult.computed_at.desc()).all()
    return jsonify({'success': True, 'data': [r.to_dict() for r in results]})

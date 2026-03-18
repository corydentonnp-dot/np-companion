"""NP Companion — Medication Reference route (placeholder)."""
from flask import Blueprint, render_template
from flask_login import login_required

medref_bp = Blueprint('medref', __name__)


@medref_bp.route('/medref')
@login_required
def index():
    """Medication reference: condition-based, first/second line, popup."""
    return render_template('medref.html')

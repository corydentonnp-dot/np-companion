"""NP Companion — Tools hub route (placeholder)."""
from flask import Blueprint, render_template
from flask_login import login_required

tools_bp = Blueprint('tools', __name__)


@tools_bp.route('/tools')
@login_required
def index():
    """Tools hub: tickler, CS tracker, PA generator, referrals, macros, coding."""
    return render_template('tools.html')

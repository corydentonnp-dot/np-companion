---
applyTo: "routes/**/*.py"
---

# Route File Rules

## Required Decorators
- `@login_required` on EVERY endpoint (exceptions: `/login`, `/timer/room-widget`, `/oncall/handoff/<token>`).
- `@require_role('admin')` on all `/admin/*` routes.
- `@require_role('provider')` on billing, metrics, and oncall routes.

## Blueprint Pattern
```python
module_bp = Blueprint('module', __name__)

@module_bp.route('/path')
@login_required
def index():
    items = Model.query.filter_by(user_id=current_user.id).all()
    return render_template('module.html', items=items)
```

## Data Scoping
- ALWAYS filter queries by `user_id=current_user.id` for user-specific data.
- Shared data (`is_shared=True`): readable by all, editable by author only.
- Never return another user's data unless explicitly shared.

## JSON Response Format
All JSON endpoints MUST return: `{"success": bool, "data": ..., "error": str|None}`

## Error Handling
```python
except Exception as e:
    db.session.rollback()
    app.logger.error(f"Error in module.action: {str(e)}")
    return jsonify({"success": False, "error": "Operation failed"}), 500
```
- Never leak stack traces, internal paths, or model details in error responses.
- Always `db.session.rollback()` before returning error.

## Redirects
- Use `redirect(url_for('module.index'))` — never `redirect(request.referrer)`.

## HIPAA
- Never log patient names, MRNs, or DOBs. Use `hashlib.sha256(mrn.encode()).hexdigest()[:12]`.
- MRN display in templates: full MRN shown (`{{ mrn }}`).
- Audit patient data access via `log_access()`.

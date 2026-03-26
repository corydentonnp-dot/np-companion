"""
CareCompanion — Order Set Manager & Executor (F8, F8a–e)

File location: carecompanion/routes/orders.py

Order set CRUD, sharing, version history, execution with
PyAutoGUI, and partial execution recovery.
"""

import json
import os
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user

from models import db
from models.orderset import (
    OrderSet, OrderItem, MasterOrder, OrderSetVersion,
    OrderExecution, OrderExecutionItem, ORDER_TABS,
)
from utils.feature_gates import require_feature

orders_bp = Blueprint('orders', __name__)


# ======================================================================
# GET /orders — Main order set manager page
# ======================================================================
@orders_bp.route('/orders')
@login_required
@require_feature('orders')
def index():
    """Order set manager: list sets, show items, execute."""
    tab = request.args.get('tab', 'mine')  # 'mine' or 'community'
    selected_id = request.args.get('set', type=int)

    # User's own order sets
    my_sets = (
        OrderSet.query
        .filter_by(user_id=current_user.id)
        .order_by(OrderSet.name)
        .all()
    )

    # Community shared sets (F8a) — exclude retracted, exclude own
    community_sets = (
        OrderSet.query
        .filter(
            OrderSet.is_shared.is_(True),
            OrderSet.is_retracted.is_(False),
            OrderSet.user_id != current_user.id,
        )
        .order_by(OrderSet.name)
        .all()
    )

    # Currently selected order set
    selected_set = None
    if selected_id:
        selected_set = OrderSet.query.filter_by(
            id=selected_id, user_id=current_user.id
        ).first()

    # Check for interrupted execution (F8e)
    interrupted = (
        OrderExecution.query
        .filter_by(user_id=current_user.id, status='interrupted')
        .order_by(OrderExecution.started_at.desc())
        .first()
    )

    # Master orders for the "Add Order" search
    master_orders = MasterOrder.query.order_by(MasterOrder.order_name).all()

    return render_template(
        'orders.html',
        tab=tab,
        my_sets=my_sets,
        community_sets=community_sets,
        selected_set=selected_set,
        interrupted=interrupted,
        master_orders=master_orders,
    )


# ======================================================================
# POST /orders/create — Create new order set
# ======================================================================
@orders_bp.route('/orders/create', methods=['POST'])
@login_required
def create_set():
    """Create a new empty order set."""
    name = request.form.get('name', '').strip()
    if not name:
        flash('Order set name is required.', 'error')
        return redirect(url_for('orders.index'))
    if len(name) > 200:
        flash('Order set name is too long.', 'error')
        return redirect(url_for('orders.index'))

    os = OrderSet(
        user_id=current_user.id,
        name=name,
        visit_type=request.form.get('visit_type', '').strip(),
    )
    db.session.add(os)
    db.session.commit()

    flash(f'Order set "{name}" created.', 'success')
    return redirect(url_for('orders.index', set=os.id))


# ======================================================================
# GET /orders/<id>/edit — Edit order set page
# ======================================================================
@orders_bp.route('/orders/<int:set_id>/edit')
@login_required
def edit_set(set_id):
    """Edit order set — returns JSON with set details."""
    os = OrderSet.query.filter_by(id=set_id, user_id=current_user.id).first_or_404()
    return jsonify({
        'id': os.id,
        'name': os.name,
        'visit_type': os.visit_type,
        'items': [{
            'id': i.id,
            'order_name': i.order_name,
            'order_tab': i.order_tab,
            'order_label': i.order_label,
            'is_default': i.is_default,
            'sort_order': i.sort_order,
        } for i in os.items],
    })


# ======================================================================
# POST /orders/<id>/update — Save edits (with version snapshot, F8b)
# ======================================================================
@orders_bp.route('/orders/<int:set_id>/update', methods=['POST'])
@login_required
def update_set(set_id):
    """Update order set name/visit_type and items. Creates a version snapshot."""
    os = OrderSet.query.filter_by(id=set_id, user_id=current_user.id).first_or_404()

    # F8b: save version snapshot before editing
    version = OrderSetVersion(
        orderset_id=os.id,
        version_number=os.version,
        snapshot_json=os.snapshot_json(),
        saved_by_user_id=current_user.id,
    )
    db.session.add(version)

    # Update metadata
    os.name = request.form.get('name', os.name).strip()
    os.visit_type = request.form.get('visit_type', os.visit_type).strip()
    os.version += 1

    # Update items from JSON payload
    items_json = request.form.get('items', '[]')
    try:
        items_data = json.loads(items_json)
    except (json.JSONDecodeError, TypeError):
        items_data = []

    if items_data:
        # Clear existing items and rebuild
        OrderItem.query.filter_by(orderset_id=os.id).delete()
        for idx, item in enumerate(items_data):
            db.session.add(OrderItem(
                orderset_id=os.id,
                order_name=item.get('order_name', '').strip(),
                order_tab=item.get('order_tab', '').strip(),
                order_label=item.get('order_label', '').strip(),
                is_default=item.get('is_default', True),
                sort_order=idx,
            ))

    db.session.commit()
    flash(f'Order set "{os.name}" updated (v{os.version}).', 'success')
    return redirect(url_for('orders.index', set=os.id))


# ======================================================================
# POST /orders/<id>/delete — Delete order set
# ======================================================================
@orders_bp.route('/orders/<int:set_id>/delete', methods=['POST'])
@login_required
def delete_set(set_id):
    """Delete an order set (cascade deletes items and versions)."""
    os = OrderSet.query.filter_by(id=set_id, user_id=current_user.id).first_or_404()
    name = os.name
    db.session.delete(os)
    db.session.commit()
    flash(f'Order set "{name}" deleted.', 'success')
    return redirect(url_for('orders.index'))


# ======================================================================
# POST /orders/<id>/add-item — Add an item to an order set
# ======================================================================
@orders_bp.route('/orders/<int:set_id>/add-item', methods=['POST'])
@login_required
def add_item(set_id):
    """Add an order item to a set."""
    os = OrderSet.query.filter_by(id=set_id, user_id=current_user.id).first_or_404()

    order_name = request.form.get('order_name', '').strip()
    if not order_name:
        flash('Order name is required.', 'error')
        return redirect(url_for('orders.index', set=os.id))

    max_sort = max((i.sort_order for i in os.items), default=-1)
    item = OrderItem(
        orderset_id=os.id,
        order_name=order_name,
        order_tab=request.form.get('order_tab', '').strip(),
        order_label=request.form.get('order_label', order_name).strip(),
        is_default=True,
        sort_order=max_sort + 1,
    )
    db.session.add(item)
    db.session.commit()
    return redirect(url_for('orders.index', set=os.id))


# ======================================================================
# POST /orders/<id>/remove-item/<item_id> — Remove an item
# ======================================================================
@orders_bp.route('/orders/<int:set_id>/remove-item/<int:item_id>', methods=['POST'])
@login_required
def remove_item(set_id, item_id):
    """Remove an order item from a set."""
    os = OrderSet.query.filter_by(id=set_id, user_id=current_user.id).first_or_404()
    item = OrderItem.query.filter_by(id=item_id, orderset_id=os.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('orders.index', set=os.id))


# ======================================================================
# POST /orders/<id>/execute — Trigger PyAutoGUI execution (F8d, F8e)
# ======================================================================
@orders_bp.route('/orders/<int:set_id>/execute', methods=['POST'])
@login_required
def execute_set(set_id):
    """Execute an order set via PyAutoGUI runner. Returns JSON progress."""
    os = OrderSet.query.filter_by(id=set_id, user_id=current_user.id).first_or_404()

    # Get the checked item IDs from the form
    checked_ids = request.form.getlist('checked_items')
    items_to_execute = [i for i in os.items if str(i.id) in checked_ids] if checked_ids else [i for i in os.items if i.is_default]

    if not items_to_execute:
        return jsonify({'success': False, 'error': 'No items selected for execution.'})

    # F8e: Create execution record
    execution = OrderExecution(
        orderset_id=os.id,
        user_id=current_user.id,
        status='in_progress',
        total_items=len(items_to_execute),
    )
    db.session.add(execution)
    db.session.flush()  # Get execution.id

    for item in items_to_execute:
        db.session.add(OrderExecutionItem(
            execution_id=execution.id,
            order_name=item.order_name,
            order_tab=item.order_tab,
            order_label=item.order_label,
            sort_order=item.sort_order,
            status='pending',
        ))
    db.session.commit()

    # Run the PyAutoGUI executor
    from agent.pyautogui_runner import execute_order_set  # lint-ok: pyautogui — pending B5 async queue refactor
    result = execute_order_set(execution.id)

    return jsonify(result)


# ======================================================================
# POST /orders/<id>/resume — Resume interrupted execution (F8e)
# ======================================================================
@orders_bp.route('/orders/resume/<int:exec_id>', methods=['POST'])
@login_required
def resume_execution(exec_id):
    """Resume a previously interrupted execution."""
    execution = OrderExecution.query.filter_by(
        id=exec_id, user_id=current_user.id, status='interrupted'
    ).first_or_404()

    execution.status = 'in_progress'
    db.session.commit()

    from agent.pyautogui_runner import execute_order_set  # lint-ok: pyautogui — pending B5 async queue refactor
    result = execute_order_set(execution.id)

    return jsonify(result)


# ======================================================================
# POST /orders/dismiss-interrupted/<id> — Dismiss interrupted banner
# ======================================================================
@orders_bp.route('/orders/dismiss-interrupted/<int:exec_id>', methods=['POST'])
@login_required
def dismiss_interrupted(exec_id):
    """Mark an interrupted execution as dismissed (set to failed)."""
    execution = OrderExecution.query.filter_by(
        id=exec_id, user_id=current_user.id, status='interrupted'
    ).first_or_404()
    execution.status = 'failed'
    execution.finished_at = datetime.now(timezone.utc)
    db.session.commit()
    return redirect(url_for('orders.index'))


# ======================================================================
# GET /orders/<id>/history — Version history (F8b)
# ======================================================================
@orders_bp.route('/orders/<int:set_id>/history')
@login_required
def version_history(set_id):
    """Return last 10 versions of an order set as JSON."""
    os = OrderSet.query.filter_by(id=set_id, user_id=current_user.id).first_or_404()
    versions = (
        OrderSetVersion.query
        .filter_by(orderset_id=os.id)
        .order_by(OrderSetVersion.version_number.desc())
        .limit(10)
        .all()
    )
    return jsonify({
        'set_name': os.name,
        'current_version': os.version,
        'versions': [{
            'id': v.id,
            'version_number': v.version_number,
            'saved_at': v.saved_at.strftime('%m/%d/%Y %I:%M %p') if v.saved_at else '',
            'saved_by': v.saved_by.display_name if v.saved_by else 'Unknown',
            'items': json.loads(v.snapshot_json) if v.snapshot_json else [],
        } for v in versions],
    })


# ======================================================================
# POST /orders/<id>/restore/<version_id> — Restore a version (F8b)
# ======================================================================
@orders_bp.route('/orders/<int:set_id>/restore/<int:version_id>', methods=['POST'])
@login_required
def restore_version(set_id, version_id):
    """Restore an order set to a previous version (creates new version entry)."""
    os = OrderSet.query.filter_by(id=set_id, user_id=current_user.id).first_or_404()
    version = OrderSetVersion.query.filter_by(
        id=version_id, orderset_id=os.id
    ).first_or_404()

    # Save current state as a new version before restoring
    snapshot = OrderSetVersion(
        orderset_id=os.id,
        version_number=os.version,
        snapshot_json=os.snapshot_json(),
        saved_by_user_id=current_user.id,
    )
    db.session.add(snapshot)

    # Restore items from snapshot
    items_data = json.loads(version.snapshot_json) if version.snapshot_json else []
    OrderItem.query.filter_by(orderset_id=os.id).delete()
    for idx, item in enumerate(items_data):
        db.session.add(OrderItem(
            orderset_id=os.id,
            order_name=item.get('order_name', ''),
            order_tab=item.get('order_tab', ''),
            order_label=item.get('order_label', ''),
            is_default=item.get('is_default', True),
            sort_order=item.get('sort_order', idx),
        ))

    os.version += 1
    db.session.commit()

    flash(f'Restored "{os.name}" to version {version.version_number}.', 'success')
    return redirect(url_for('orders.index', set=os.id))


# ======================================================================
# POST /orders/share/<id> — Publish order set to shared library (F8a)
# ======================================================================
@orders_bp.route('/orders/share/<int:set_id>', methods=['POST'])
@login_required
def share_set(set_id):
    """Share an order set with all colleagues."""
    os = OrderSet.query.filter_by(id=set_id, user_id=current_user.id).first_or_404()
    os.is_shared = True
    os.shared_by_user_id = current_user.id
    db.session.commit()
    flash(f'"{os.name}" is now shared with colleagues.', 'success')
    return redirect(url_for('orders.index', set=os.id))


# ======================================================================
# POST /orders/unshare/<id> — Retract a shared order set (F8a)
# ======================================================================
@orders_bp.route('/orders/unshare/<int:set_id>', methods=['POST'])
@login_required
def unshare_set(set_id):
    """Retract a shared order set (existing forks unaffected)."""
    os = OrderSet.query.filter_by(id=set_id, user_id=current_user.id).first_or_404()
    os.is_retracted = True
    db.session.commit()
    flash(f'"{os.name}" has been retracted from sharing.', 'success')
    return redirect(url_for('orders.index', set=os.id))


# ======================================================================
# POST /orders/import/<id> — Import/fork a community order set (F8a)
# ======================================================================
@orders_bp.route('/orders/import/<int:set_id>', methods=['POST'])
@login_required
def import_set(set_id):
    """Copy a shared order set to user's personal library."""
    source = OrderSet.query.filter_by(id=set_id).first_or_404()
    if not source.is_shared or source.is_retracted:
        flash('This order set is not available for import.', 'error')
        return redirect(url_for('orders.index', tab='community'))

    forked = OrderSet(
        user_id=current_user.id,
        name=f'{source.name} (fork)',
        visit_type=source.visit_type,
        forked_from_id=source.id,
        shared_by_user_id=source.user_id,
    )
    db.session.add(forked)
    db.session.flush()

    for item in source.items:
        db.session.add(OrderItem(
            orderset_id=forked.id,
            order_name=item.order_name,
            order_tab=item.order_tab,
            order_label=item.order_label,
            is_default=item.is_default,
            sort_order=item.sort_order,
        ))

    db.session.commit()
    flash(f'Imported "{source.name}" to your library.', 'success')
    return redirect(url_for('orders.index', set=forked.id))


# ======================================================================
# GET /orders/master-list — View/edit master order list
# ======================================================================
@orders_bp.route('/orders/master-list')
@login_required
def master_list():
    """View and manage the master list of all known orders."""
    orders = MasterOrder.query.order_by(MasterOrder.category, MasterOrder.order_name).all()
    return render_template('orders_master.html', master_orders=orders)


# ======================================================================
# POST /orders/master-list/add — Add to master list
# ======================================================================
@orders_bp.route('/orders/master-list/add', methods=['POST'])
@login_required
def master_list_add():
    """Add a new order to the master list."""
    order_name = request.form.get('order_name', '').strip()
    if not order_name:
        flash('Order name is required.', 'error')
        return redirect(url_for('orders.master_list'))

    existing = MasterOrder.query.filter_by(order_name=order_name).first()
    if existing:
        flash(f'"{order_name}" already exists in the master list.', 'error')
        return redirect(url_for('orders.master_list'))

    mo = MasterOrder(
        order_name=order_name,
        order_tab=request.form.get('order_tab', '').strip(),
        order_label=request.form.get('order_label', order_name).strip(),
        category=request.form.get('category', '').strip(),
    )
    db.session.add(mo)
    db.session.commit()
    flash(f'Added "{order_name}" to master list.', 'success')
    return redirect(url_for('orders.master_list'))


# ======================================================================
# POST /orders/master-list/delete/<id> — Remove from master list
# ======================================================================
@orders_bp.route('/orders/master-list/delete/<int:order_id>', methods=['POST'])
@login_required
def master_list_delete(order_id):
    """Remove an order from the master list."""
    mo = MasterOrder.query.get_or_404(order_id)
    db.session.delete(mo)
    db.session.commit()
    flash('Order removed from master list.', 'success')
    return redirect(url_for('orders.master_list'))


# ======================================================================
# JSON API: search master orders (for "Add Order" dropdown)
# ======================================================================
@orders_bp.route('/api/orders/search')
@login_required
def search_master_orders():
    """Search master orders by name, returns JSON list."""
    q = request.args.get('q', '').strip()
    if len(q) < 1:
        return jsonify([])

    results = (
        MasterOrder.query
        .filter(MasterOrder.order_name.ilike(f'%{q}%'))
        .order_by(MasterOrder.is_common.desc(), MasterOrder.order_name)
        .limit(20)
        .all()
    )
    return jsonify([{
        'id': r.id,
        'order_name': r.order_name,
        'order_tab': r.order_tab,
        'order_label': r.order_label,
        'category': r.category,
        'is_common': r.is_common or False,
    } for r in results])


# ======================================================================
# JSON API: toggle is_common on a master order
# ======================================================================
@orders_bp.route('/api/orders/master/<int:order_id>/toggle-common', methods=['POST'])
@login_required
def toggle_common(order_id):
    """Toggle the is_common flag on a master order."""
    mo = MasterOrder.query.get_or_404(order_id)
    mo.is_common = not (mo.is_common or False)
    db.session.commit()
    return jsonify({'success': True, 'is_common': mo.is_common})


# ======================================================================
# JSON API: browse all master orders (for order set builder popup)
# ======================================================================
@orders_bp.route('/api/orders/master-browse')
@login_required
def master_browse():
    """Return all master orders grouped by tab/category for the builder popup."""
    from models.orderset import ORDER_TABS
    q = request.args.get('q', '').strip()
    tab = request.args.get('tab', '').strip()
    query = MasterOrder.query
    if q:
        query = query.filter(MasterOrder.order_name.ilike(f'%{q}%'))
    if tab:
        query = query.filter_by(order_tab=tab)
    orders = query.order_by(MasterOrder.is_common.desc(), MasterOrder.order_name).all()
    return jsonify({
        'tabs': ORDER_TABS,
        'orders': [{
            'id': o.id,
            'order_name': o.order_name,
            'order_tab': o.order_tab,
            'order_label': o.order_label,
            'category': o.category,
            'cpt_code': o.cpt_code,
            'is_common': o.is_common or False,
        } for o in orders],
    })


# ======================================================================
# JSON API: execution status polling (F8e)
# ======================================================================
@orders_bp.route('/api/orders/execution/<int:exec_id>')
@login_required
def execution_status(exec_id):
    """Return current execution status as JSON for live polling."""
    execution = OrderExecution.query.filter_by(
        id=exec_id, user_id=current_user.id
    ).first_or_404()
    return jsonify({
        'id': execution.id,
        'status': execution.status,
        'total_items': execution.total_items,
        'completed_items': execution.completed_items,
        'failed_items': execution.failed_items,
        'error_message': execution.error_message,
        'items': [{
            'order_name': i.order_name,
            'status': i.status,
            'error_message': i.error_message,
        } for i in execution.items],
    })


# ======================================================================
# GET /orders/calibrate — AC Calibration Wizard (UX-17)
# ======================================================================
CALIBRATION_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'data', 'ac_calibration.json'
)

CALIBRATION_POINTS = [
    {'key': 'INBOX_FILTER_DROPDOWN_XY', 'label': 'Inbox Filter Dropdown',
     'hint': 'Click the filter dropdown at the top of the AC Inbox.'},
    {'key': 'PATIENT_LIST_ID_SEARCH_XY', 'label': 'Patient List ID Search',
     'hint': 'Click the "ID" search field in the Patient List.'},
    {'key': 'VISIT_TEMPLATE_RADIO_XY', 'label': 'Visit Template Radio Button',
     'hint': 'Click the "Visit Template" radio button in the New Visit dialog.'},
    {'key': 'SELECT_TEMPLATE_DROPDOWN_XY', 'label': 'Template Dropdown',
     'hint': 'Click the template selection dropdown in the New Visit dialog.'},
    {'key': 'EXPORT_CLIN_SUM_MENU_XY', 'label': 'Export Clinical Summary Menu',
     'hint': 'Click Patient menu > Export Clinical Summary.'},
    {'key': 'EXPORT_BUTTON_XY', 'label': 'Export Button',
     'hint': 'Click the Export button in the export dialog.'},
]


@orders_bp.route('/orders/calibrate')
@login_required
def calibrate():
    """Show the AC calibration wizard."""
    saved = {}
    if os.path.exists(CALIBRATION_FILE):
        try:
            with open(CALIBRATION_FILE, 'r') as f:
                saved = json.load(f)
        except Exception:
            saved = {}
    return render_template(
        'ac_calibrate.html',
        points=CALIBRATION_POINTS,
        saved=saved,
    )


@orders_bp.route('/api/orders/calibrate/capture', methods=['POST'])
@login_required
def calibrate_capture():
    """Capture current mouse position for a calibration point."""
    try:
        import pyautogui
        x, y = pyautogui.position()
        return jsonify({'success': True, 'data': {'x': x, 'y': y}})
    except ImportError:
        return jsonify({'success': False, 'error': 'pyautogui not available'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@orders_bp.route('/api/orders/calibrate/save', methods=['POST'])
@login_required
def calibrate_save():
    """Save all calibration points."""
    data = request.get_json()
    if not data or 'points' not in data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    try:
        os.makedirs(os.path.dirname(CALIBRATION_FILE), exist_ok=True)
        with open(CALIBRATION_FILE, 'w') as f:
            json.dump(data['points'], f, indent=2)
        return jsonify({'success': True, 'data': 'Calibration saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

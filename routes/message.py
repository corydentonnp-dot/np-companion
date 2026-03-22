"""
CareCompanion — Delayed Message Routes
File: routes/message.py

Routes for the Delayed Message Queue (F18):
- GET  /messages           — list view (pending + history)
- GET  /messages/new       — compose form
- POST /messages           — create new delayed message
- POST /messages/<id>/cancel — cancel pending message
- GET  /api/messages/pending   — JSON endpoint for agent polling
- POST /api/messages/<id>/mark-sent — agent marks message as sent
"""

import logging
from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from models import db
from models.message import DelayedMessage
from models.result_template import ResultTemplate

logger = logging.getLogger(__name__)

message_bp = Blueprint('messages', __name__)


# ======================================================================
# UI Routes
# ======================================================================

@message_bp.route('/messages')
@login_required
def index():
    """List view: pending queue + sent/cancelled history."""
    pending = (
        DelayedMessage.query
        .filter_by(user_id=current_user.id, status='pending')
        .order_by(DelayedMessage.scheduled_send_at.asc())
        .all()
    )
    history = (
        DelayedMessage.query
        .filter_by(user_id=current_user.id)
        .filter(DelayedMessage.status.in_(['sent', 'failed', 'cancelled']))
        .order_by(DelayedMessage.created_at.desc())
        .limit(100)
        .all()
    )
    return render_template('messages.html', pending=pending, history=history)


@message_bp.route('/messages/new')
@login_required
def new():
    """Compose form for a new delayed message."""
    return render_template('message_new.html')


@message_bp.route('/messages', methods=['POST'])
@login_required
def create():
    """Create a new delayed message."""
    recipient = (request.form.get('recipient_identifier') or '').strip()
    content = (request.form.get('message_content') or '').strip()
    send_at_str = (request.form.get('scheduled_send_at') or '').strip()

    if not recipient or not content or not send_at_str:
        flash('All fields are required.', 'danger')
        return redirect(url_for('messages.new'))

    try:
        send_at = datetime.fromisoformat(send_at_str).replace(tzinfo=timezone.utc)
    except ValueError:
        flash('Invalid date/time format.', 'danger')
        return redirect(url_for('messages.new'))

    if send_at <= datetime.now(timezone.utc):
        flash('Scheduled time must be in the future.', 'danger')
        return redirect(url_for('messages.new'))

    # Recurring options (F18a)
    is_recurring = request.form.get('is_recurring') == '1'
    interval_str = (request.form.get('recurrence_interval_days') or '').strip()
    end_date_str = (request.form.get('recurrence_end_date') or '').strip()

    interval_days = None
    end_date = None
    if is_recurring:
        try:
            interval_days = int(interval_str)
            if interval_days < 1:
                raise ValueError
        except (ValueError, TypeError):
            flash('Recurrence interval must be a positive number of days.', 'danger')
            return redirect(url_for('messages.new'))
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str).replace(tzinfo=timezone.utc)
            except ValueError:
                flash('Invalid recurrence end date.', 'danger')
                return redirect(url_for('messages.new'))

    msg = DelayedMessage(
        user_id=current_user.id,
        recipient_identifier=recipient,
        message_content=content,
        scheduled_send_at=send_at,
        is_recurring=is_recurring,
        recurrence_interval_days=interval_days,
        recurrence_end_date=end_date,
    )
    db.session.add(msg)
    db.session.commit()
    label = 'Recurring message' if is_recurring else 'Message'
    flash(f'{label} scheduled successfully.', 'success')
    return redirect(url_for('messages.index'))


@message_bp.route('/messages/<int:msg_id>/cancel', methods=['POST'])
@login_required
def cancel(msg_id):
    """Cancel a pending delayed message."""
    msg = db.session.get(DelayedMessage, msg_id)
    if not msg or msg.user_id != current_user.id:
        flash('Message not found.', 'danger')
        return redirect(url_for('messages.index'))

    if msg.status != 'pending':
        flash('Only pending messages can be cancelled.', 'warning')
        return redirect(url_for('messages.index'))

    msg.status = 'cancelled'
    db.session.commit()
    flash('Message cancelled.', 'success')
    return redirect(url_for('messages.index'))


@message_bp.route('/messages/<int:msg_id>/cancel-series', methods=['POST'])
@login_required
def cancel_series(msg_id):
    """Cancel all future pending messages in a recurring series."""
    msg = db.session.get(DelayedMessage, msg_id)
    if not msg or msg.user_id != current_user.id:
        flash('Message not found.', 'danger')
        return redirect(url_for('messages.index'))

    # Find the series root
    root_id = msg.parent_message_id or msg.id
    cancelled = (
        DelayedMessage.query
        .filter(
            DelayedMessage.status == 'pending',
            DelayedMessage.user_id == current_user.id,
            db.or_(
                DelayedMessage.id == root_id,
                DelayedMessage.parent_message_id == root_id,
            ),
        )
        .all()
    )
    for m in cancelled:
        m.status = 'cancelled'
    db.session.commit()
    flash(f'Cancelled {len(cancelled)} message(s) in series.', 'success')
    return redirect(url_for('messages.index'))


# ======================================================================
# Recurring Message Helper (called by scheduler after send)
# ======================================================================

def create_next_occurrence(sent_msg):
    """After a recurring message is sent, create the next pending copy.

    Returns the new DelayedMessage or None if series is complete.
    """
    if not sent_msg.is_recurring or not sent_msg.recurrence_interval_days:
        return None

    next_send = sent_msg.scheduled_send_at + timedelta(
        days=sent_msg.recurrence_interval_days
    )

    # Stop if past end date
    if sent_msg.recurrence_end_date and next_send > sent_msg.recurrence_end_date:
        return None

    root_id = sent_msg.parent_message_id or sent_msg.id
    new_msg = DelayedMessage(
        user_id=sent_msg.user_id,
        recipient_identifier=sent_msg.recipient_identifier,
        message_content=sent_msg.message_content,
        scheduled_send_at=next_send,
        is_recurring=True,
        recurrence_interval_days=sent_msg.recurrence_interval_days,
        recurrence_end_date=sent_msg.recurrence_end_date,
        parent_message_id=root_id,
    )
    db.session.add(new_msg)
    db.session.commit()
    return new_msg


# ======================================================================
# Agent API Routes
# ======================================================================

@message_bp.route('/api/messages/pending')
@login_required
def api_pending():
    """JSON list of pending messages ready to send (scheduled_send_at <= now)."""
    now = datetime.now(timezone.utc)
    pending = (
        DelayedMessage.query
        .filter(
            DelayedMessage.status == 'pending',
            DelayedMessage.scheduled_send_at <= now,
        )
        .order_by(DelayedMessage.scheduled_send_at.asc())
        .all()
    )
    return jsonify([
        {
            'id': m.id,
            'user_id': m.user_id,
            'recipient_identifier': m.recipient_identifier,
            'message_content': m.message_content,
            'scheduled_send_at': m.scheduled_send_at.isoformat(),
        }
        for m in pending
    ])


@message_bp.route('/api/messages/<int:msg_id>/mark-sent', methods=['POST'])
@login_required
def api_mark_sent(msg_id):
    """Agent marks a message as sent after successful delivery."""
    msg = db.session.get(DelayedMessage, msg_id)
    if not msg:
        return jsonify({'error': 'not found'}), 404

    msg.status = 'sent'
    msg.sent_at = datetime.now(timezone.utc)
    msg.delivery_confirmed = True
    db.session.commit()

    # Auto-create next occurrence for recurring messages
    next_msg = create_next_occurrence(msg)
    result = {'ok': True, 'id': msg.id, 'status': 'sent'}
    if next_msg:
        result['next_id'] = next_msg.id
        result['next_send_at'] = next_msg.scheduled_send_at.isoformat()
    return jsonify(result)


# ======================================================================
# Result Template API (F19)
# ======================================================================

@message_bp.route('/api/result-templates')
@login_required
def api_result_templates():
    """Return active result templates grouped by category.

    Order: user's own templates first, then shared, then system.
    """
    from sqlalchemy import case

    uid = current_user.id
    templates = (
        ResultTemplate.query
        .filter_by(is_active=True)
        .filter(
            db.or_(
                ResultTemplate.user_id == uid,
                ResultTemplate.is_shared == True,
                ResultTemplate.user_id == None,
            )
        )
        .order_by(
            case(
                (ResultTemplate.user_id == uid, 0),
                (ResultTemplate.is_shared == True, 1),
                else_=2,
            ),
            ResultTemplate.category,
            ResultTemplate.display_order,
        )
        .all()
    )
    grouped = {}
    for t in templates:
        suffix = ''
        if t.user_id is None:
            suffix = ' (System)'
        elif t.user_id != uid and t.is_shared:
            suffix = ' (Shared)'
        grouped.setdefault(t.category, []).append({
            'id': t.id,
            'name': t.name + suffix,
            'category': t.category,
            'body_template': t.body_template,
        })
    return jsonify(grouped)


@message_bp.route('/api/result-templates', methods=['POST'])
@login_required
def api_create_result_template():
    """Create a custom result template (admin only)."""
    if not (current_user.role == 'admin'):
        return jsonify({'error': 'admin only'}), 403

    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    category = (data.get('category') or '').strip()
    body = (data.get('body_template') or '').strip()

    if not name or not category or not body:
        return jsonify({'error': 'name, category, and body_template are required'}), 400

    t = ResultTemplate(
        name=name,
        category=category,
        body_template=body,
    )
    db.session.add(t)
    db.session.commit()
    return jsonify({'ok': True, 'id': t.id}), 201

"""
CareCompanion — Inbox Monitor Routes

File location: carecompanion/routes/inbox.py

Provides:
  GET  /inbox            — Main inbox page with unresolved items
  GET  /inbox/held       — Held items management
  GET  /inbox/audit-log  — Review timestamp log (F5f)
  POST /inbox/<id>/hold  — Mark an item as held
  POST /inbox/<id>/resolve — Resolve an item
  GET  /api/inbox-status — JSON endpoint for dashboard polling

Feature: F5, F5c, F5d, F5f
"""

import csv
import io
from datetime import datetime, timedelta, timezone

from flask import (
    Blueprint, render_template, request, jsonify,
    flash, redirect, url_for, Response,
)
from flask_login import login_required, current_user
from models import db
from models.inbox import InboxSnapshot, InboxItem

inbox_bp = Blueprint('inbox', __name__)


@inbox_bp.route('/inbox/digest')
@login_required
def digest():
    """Inbox Digest Report — activity summary over a configurable window."""
    from agent.inbox_digest import generate_digest

    try:
        import config as cfg
        default_hours = getattr(cfg, 'INBOX_DIGEST_HOURS', 24)
    except ImportError:
        default_hours = 24

    hours = request.args.get('hours', default_hours, type=int)
    hours = max(1, min(hours, 168))  # clamp to 1h–7d

    digest_data = generate_digest(current_user.id, hours=hours)

    # CSV export
    if request.args.get('format') == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Period (hours)', digest_data['period_hours']])
        writer.writerow(['Period Start', digest_data['period_start'].isoformat()])
        writer.writerow(['Period End', digest_data['period_end'].isoformat()])
        writer.writerow(['Snapshots Taken', digest_data['snapshots_count']])
        writer.writerow(['New Items', digest_data['period_new']])
        writer.writerow(['Resolved Items', digest_data['period_resolved']])
        writer.writerow(['Still Unresolved', digest_data['still_unresolved']])
        writer.writerow(['Critical Seen', digest_data['critical_seen']])
        writer.writerow(['Held Items', digest_data['held_count']])
        writer.writerow(['Overdue Items', digest_data['overdue_count']])
        writer.writerow(['Trend', digest_data['trend']])
        writer.writerow([])
        writer.writerow(['Category', 'New Items'])
        for cat, count in digest_data.get('category_breakdown', {}).items():
            writer.writerow([cat, count])
        writer.writerow([])
        writer.writerow(['Current Totals', ''])
        for cat, count in digest_data.get('current_totals', {}).items():
            writer.writerow([cat, count])
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=inbox_digest.csv'},
        )

    return render_template(
        'inbox.html',
        items=[], snapshot=None,
        view='digest', digest=digest_data, digest_hours=hours,
    )


@inbox_bp.route('/inbox')
@login_required
def index():
    """Main inbox page — latest snapshot + unresolved items."""
    latest_snapshot = (
        InboxSnapshot.query
        .filter_by(user_id=current_user.id)
        .order_by(InboxSnapshot.captured_at.desc())
        .first()
    )

    items = (
        InboxItem.query
        .filter_by(user_id=current_user.id, is_resolved=False)
        .order_by(InboxItem.first_seen_at.desc())
        .all()
    )

    now = datetime.now(timezone.utc)
    warning_hours = 48
    critical_hours = 72

    try:
        import config
        warning_hours = getattr(config, 'INBOX_WARNING_HOURS', 48)
        critical_hours = getattr(config, 'INBOX_CRITICAL_HOURS', 72)
    except ImportError:
        pass

    for item in items:
        if item.first_seen_at:
            age = (now - item.first_seen_at).total_seconds() / 3600
        else:
            age = 0
        if age >= critical_hours:
            item._age_class = 'critical'
        elif age >= warning_hours:
            item._age_class = 'warning'
        else:
            item._age_class = 'normal'
        item._age_hours = int(age)

    return render_template(
        'inbox.html',
        snapshot=latest_snapshot,
        items=items,
    )


@inbox_bp.route('/inbox/held')
@login_required
def held_items():
    """Held items page — items intentionally placed on hold."""
    items = (
        InboxItem.query
        .filter_by(user_id=current_user.id, is_held=True, is_resolved=False)
        .order_by(InboxItem.first_seen_at.desc())
        .all()
    )
    return render_template('inbox.html', items=items, snapshot=None, view='held')


@inbox_bp.route('/inbox/audit-log')
@login_required
def audit_log():
    """Review timestamp log — snapshot history with counts."""
    start_str = request.args.get('start', '')
    end_str = request.args.get('end', '')

    query = InboxSnapshot.query.filter_by(user_id=current_user.id)

    if start_str:
        try:
            start_dt = datetime.fromisoformat(start_str).replace(tzinfo=timezone.utc)
            query = query.filter(InboxSnapshot.captured_at >= start_dt)
        except ValueError:
            pass

    if end_str:
        try:
            end_dt = datetime.fromisoformat(end_str).replace(tzinfo=timezone.utc)
            query = query.filter(InboxSnapshot.captured_at <= end_dt)
        except ValueError:
            pass

    snapshots = query.order_by(InboxSnapshot.captured_at.desc()).limit(200).all()

    # CSV export
    if request.args.get('format') == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Timestamp', 'Labs', 'Radiology', 'Messages', 'Refills', 'Other', 'Total'])
        for s in snapshots:
            total = s.labs_count + s.radiology_count + s.messages_count + s.refills_count + s.other_count
            writer.writerow([
                s.captured_at.isoformat(),
                s.labs_count, s.radiology_count, s.messages_count,
                s.refills_count, s.other_count, total,
            ])
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=inbox_audit_log.csv'},
        )

    return render_template('inbox.html', items=[], snapshot=None,
                           view='audit', snapshots=snapshots,
                           start=start_str, end=end_str)


@inbox_bp.route('/inbox/<int:item_id>/hold', methods=['POST'])
@login_required
def hold_item(item_id):
    """Mark an inbox item as held."""
    item = InboxItem.query.filter_by(id=item_id, user_id=current_user.id).first()
    if not item:
        flash('Item not found.', 'error')
        return redirect(url_for('inbox.index'))

    item.is_held = True
    reason = request.form.get('reason', '').strip()
    if reason:
        item.held_reason = reason
    db.session.commit()
    flash('Item placed on hold.', 'success')
    return redirect(url_for('inbox.index'))


@inbox_bp.route('/inbox/<int:item_id>/resolve', methods=['POST'])
@login_required
def resolve_item(item_id):
    """Resolve an inbox item."""
    item = InboxItem.query.filter_by(id=item_id, user_id=current_user.id).first()
    if not item:
        flash('Item not found.', 'error')
        return redirect(url_for('inbox.index'))

    item.is_resolved = True
    item.is_held = False
    db.session.commit()
    flash('Item resolved.', 'success')

    if request.referrer and 'held' in request.referrer:
        return redirect(url_for('inbox.held_items'))
    return redirect(url_for('inbox.index'))


@inbox_bp.route('/api/inbox-status')
@login_required
def inbox_status():
    """JSON endpoint for dashboard inbox status polling."""
    total_unresolved = InboxItem.query.filter_by(
        user_id=current_user.id, is_resolved=False
    ).count()

    critical = InboxItem.query.filter_by(
        user_id=current_user.id, is_resolved=False, priority='critical'
    ).count()

    held = InboxItem.query.filter_by(
        user_id=current_user.id, is_held=True, is_resolved=False
    ).count()

    # Overdue = unresolved items older than critical threshold
    try:
        import config
        critical_hours = getattr(config, 'INBOX_CRITICAL_HOURS', 72)
    except ImportError:
        critical_hours = 72

    cutoff = datetime.now(timezone.utc) - timedelta(hours=critical_hours)
    overdue = InboxItem.query.filter(
        InboxItem.user_id == current_user.id,
        InboxItem.is_resolved == False,
        InboxItem.first_seen_at <= cutoff,
    ).count()

    latest = (
        InboxSnapshot.query
        .filter_by(user_id=current_user.id)
        .order_by(InboxSnapshot.captured_at.desc())
        .first()
    )

    return jsonify({
        'total_unresolved': total_unresolved,
        'critical': critical,
        'held': held,
        'overdue': overdue,
        'last_checked': latest.captured_at.isoformat() if latest else None,
    })

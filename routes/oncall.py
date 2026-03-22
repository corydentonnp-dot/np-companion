"""
CareCompanion — On-Call Note Keeper (F7, F7a–e)

File location: carecompanion/routes/oncall.py

Mobile-first on-call note system with voice input, callback tracking,
colleague handoff, and kanban status flow.
"""

import json
import secrets
from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user

from models import db
from models.oncall import OnCallNote, HandoffLink
from models.user import User

oncall_bp = Blueprint('oncall', __name__)


# ======================================================================
# GET /oncall — Note list with callbacks-due section (F7, F7b, F7e)
# ======================================================================
@oncall_bp.route('/oncall')
@login_required
def index():
    """On-call note list grouped by date with callback tracker."""
    # Status filter: show "pending" by default on Mondays for F7e
    status_filter = request.args.get('status', '')
    monday_filter = request.args.get('monday', '')

    query = OnCallNote.query.filter_by(user_id=current_user.id)

    if status_filter:
        query = query.filter_by(documentation_status=status_filter)

    if monday_filter:
        # Monday morning view: weekend notes with pending status
        today = datetime.now(timezone.utc).date()
        # Find last Saturday 00:00
        days_since_sat = (today.weekday() + 2) % 7
        weekend_start = today - timedelta(days=days_since_sat)
        query = query.filter(
            OnCallNote.call_time >= datetime.combine(
                weekend_start, datetime.min.time()
            ),
            OnCallNote.documentation_status == 'pending',
        )

    notes = query.order_by(OnCallNote.call_time.desc()).all()

    # Callbacks due (overdue)
    now = datetime.now(timezone.utc)
    callbacks_due = (
        OnCallNote.query
        .filter_by(
            user_id=current_user.id,
            callback_promised=True,
            callback_completed=False,
        )
        .filter(OnCallNote.callback_by <= now)
        .order_by(OnCallNote.callback_by)
        .all()
    )

    # Pending documentation count for badge
    pending_count = OnCallNote.query.filter_by(
        user_id=current_user.id, documentation_status='pending'
    ).count()

    # Group notes by date for display
    grouped = {}
    for note in notes:
        key = note.call_time.strftime('%A, %B %d, %Y') if note.call_time else 'Unknown Date'
        grouped.setdefault(key, []).append(note)

    is_monday = datetime.now().weekday() == 0

    # Active users for forwarding dropdown
    active_users = User.query.filter(
        User.is_active_account == True,
        User.id != current_user.id
    ).order_by(User.display_name).all()

    return render_template(
        'oncall.html',
        grouped_notes=grouped,
        callbacks_due=callbacks_due,
        pending_count=pending_count,
        status_filter=status_filter,
        is_monday=is_monday,
        active_users=active_users,
    )


# ======================================================================
# GET /oncall/new — New note form (mobile-first, F7)
# ======================================================================
@oncall_bp.route('/oncall/new')
@login_required
def new_note():
    """Mobile-optimized new on-call note form."""
    return render_template('oncall_new.html')


# ======================================================================
# POST /oncall/new — Save new note (F7)
# ======================================================================
@oncall_bp.route('/oncall/new', methods=['POST'])
@login_required
def create_note():
    """Save a new on-call note."""
    call_time_str = request.form.get('call_time', '')
    try:
        call_time = datetime.fromisoformat(call_time_str) if call_time_str else datetime.now(timezone.utc)
    except ValueError:
        call_time = datetime.now(timezone.utc)

    callback_promised = request.form.get('callback_promised') == 'yes'
    callback_by = None
    if callback_promised:
        cb_str = request.form.get('callback_by', '')
        try:
            callback_by = datetime.fromisoformat(cb_str) if cb_str else None
        except ValueError:
            callback_by = None

    note = OnCallNote(
        user_id=current_user.id,
        patient_identifier=request.form.get('patient_identifier', '').strip(),
        call_time=call_time,
        chief_complaint=request.form.get('chief_complaint', '').strip(),
        recommendation=request.form.get('recommendation', '').strip(),
        callback_promised=callback_promised,
        callback_by=callback_by,
        documentation_status=request.form.get('documentation_status', 'pending'),
        note_content=request.form.get('note_content', '').strip(),
    )

    # Optional: forward to another provider at creation time
    forward_to_id = request.form.get('forward_to', '').strip()
    if forward_to_id and forward_to_id.isdigit():
        note.forwarded_to = int(forward_to_id)
        note.forwarded_at = datetime.now(timezone.utc)

    db.session.add(note)
    db.session.commit()

    flash('On-call note saved.', 'success')
    return redirect(url_for('oncall.index'))


# ======================================================================
# GET /oncall/<id> — View single note
# ======================================================================
@oncall_bp.route('/oncall/<int:note_id>')
@login_required
def view_note(note_id):
    """View a single on-call note."""
    note = OnCallNote.query.filter_by(
        id=note_id, user_id=current_user.id
    ).first_or_404()
    return render_template('oncall_view.html', note=note)


# ======================================================================
# POST /oncall/<id>/edit — Edit existing note
# ======================================================================
@oncall_bp.route('/oncall/<int:note_id>/edit', methods=['POST'])
@login_required
def edit_note(note_id):
    """Update an existing on-call note."""
    note = OnCallNote.query.filter_by(
        id=note_id, user_id=current_user.id
    ).first_or_404()

    note.patient_identifier = request.form.get('patient_identifier', note.patient_identifier).strip()
    note.chief_complaint = request.form.get('chief_complaint', note.chief_complaint).strip()
    note.recommendation = request.form.get('recommendation', note.recommendation).strip()
    note.note_content = request.form.get('note_content', note.note_content).strip()

    callback_promised = request.form.get('callback_promised') == 'yes'
    note.callback_promised = callback_promised
    if callback_promised:
        cb_str = request.form.get('callback_by', '')
        try:
            note.callback_by = datetime.fromisoformat(cb_str) if cb_str else note.callback_by
        except ValueError:
            pass
    else:
        note.callback_by = None
        note.callback_completed = False

    db.session.commit()
    flash('Note updated.', 'success')
    return redirect(url_for('oncall.view_note', note_id=note.id))


# ======================================================================
# POST /oncall/<id>/status — Update documentation status (F7e)
# ======================================================================
@oncall_bp.route('/oncall/<int:note_id>/status', methods=['POST'])
@login_required
def update_status(note_id):
    """Update documentation status (kanban flow)."""
    note = OnCallNote.query.filter_by(
        id=note_id, user_id=current_user.id
    ).first_or_404()

    new_status = request.form.get('status', '')
    if new_status in ('pending', 'entered', 'not_needed'):
        note.documentation_status = new_status
        db.session.commit()

    # Support AJAX and form POST
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'status': note.documentation_status})

    return redirect(url_for('oncall.index'))


# ======================================================================
# POST /oncall/<id>/complete-callback — Mark callback done (F7b)
# ======================================================================
@oncall_bp.route('/oncall/<int:note_id>/complete-callback', methods=['POST'])
@login_required
def complete_callback(note_id):
    """Mark a promised callback as completed."""
    note = OnCallNote.query.filter_by(
        id=note_id, user_id=current_user.id
    ).first_or_404()

    note.callback_completed = True
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})

    flash('Callback marked as completed.', 'success')
    return redirect(url_for('oncall.index'))


# ======================================================================
# GET /oncall/export/<id> — Formatted note for AC paste-in (F7)
# ======================================================================
@oncall_bp.route('/oncall/export/<int:note_id>')
@login_required
def export_note(note_id):
    """Export view formatted for Amazing Charts copy-paste."""
    note = OnCallNote.query.filter_by(
        id=note_id, user_id=current_user.id
    ).first_or_404()

    # Build formatted text
    ct = note.call_time.strftime('%m/%d/%Y %I:%M %p') if note.call_time else 'Unknown'
    lines = [f'After-hours call {ct}:']
    if note.patient_identifier:
        lines.append(f'Patient {note.patient_identifier} called regarding {note.chief_complaint}.')
    else:
        lines.append(f'Call regarding {note.chief_complaint}.')
    if note.recommendation:
        lines.append(f'Recommendation: {note.recommendation}.')
    if note.callback_promised:
        cb_time = note.callback_by.strftime('%m/%d/%Y %I:%M %p') if note.callback_by else 'TBD'
        status = 'completed' if note.callback_completed else 'pending'
        lines.append(f'Callback promised by {cb_time} ({status}).')
    if note.note_content:
        lines.append(f'Additional notes: {note.note_content}')

    formatted_text = ' '.join(lines)

    return render_template('oncall_export.html', note=note, formatted_text=formatted_text)


# ======================================================================
# GET /oncall/handoff — Handoff summary (F7d)
# ======================================================================
@oncall_bp.route('/oncall/handoff')
@login_required
def handoff():
    """Generate de-identified handoff summary of current call period."""
    # Get notes from the last 72 hours (typical weekend call period)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=72)
    notes = (
        OnCallNote.query
        .filter_by(user_id=current_user.id)
        .filter(OnCallNote.call_time >= cutoff)
        .order_by(OnCallNote.call_time)
        .all()
    )

    summary_items = []
    for n in notes:
        summary_items.append({
            'call_time': n.call_time.strftime('%a %I:%M %p') if n.call_time else '',
            'chief_complaint': n.chief_complaint or 'No complaint recorded',
            'status': n.documentation_status,
            'callback_pending': n.callback_promised and not n.callback_completed,
        })

    return render_template(
        'oncall_handoff.html',
        summary_items=summary_items,
        note_count=len(notes),
    )


# ======================================================================
# POST /oncall/handoff/share — Generate temporary handoff link (F7d)
# ======================================================================
@oncall_bp.route('/oncall/handoff/share', methods=['POST'])
@login_required
def share_handoff():
    """Generate a 1-hour temporary link with de-identified summary."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=72)
    notes = (
        OnCallNote.query
        .filter_by(user_id=current_user.id)
        .filter(OnCallNote.call_time >= cutoff)
        .order_by(OnCallNote.call_time)
        .all()
    )

    # De-identified summary: NO patient identifiers
    summary = []
    for n in notes:
        summary.append({
            'call_time': n.call_time.strftime('%a %I:%M %p') if n.call_time else '',
            'chief_complaint': n.chief_complaint or 'No complaint recorded',
            'status': n.documentation_status,
            'callback_pending': n.callback_promised and not n.callback_completed,
        })

    link = HandoffLink(
        user_id=current_user.id,
        token=secrets.token_urlsafe(32),
        summary_json=json.dumps(summary),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.session.add(link)
    db.session.commit()

    handoff_url = url_for('oncall.view_handoff', token=link.token, _external=True)
    return jsonify({'success': True, 'url': handoff_url, 'expires_in': '1 hour'})


# ======================================================================
# GET /oncall/handoff/<token> — View shared handoff (NO LOGIN, F7d)
# ======================================================================
@oncall_bp.route('/oncall/handoff/<token>')
def view_handoff(token):
    """Public read-only handoff view. No login required, time-limited."""
    link = HandoffLink.query.filter_by(token=token).first_or_404()

    if datetime.now(timezone.utc) > link.expires_at:
        return render_template('oncall_handoff_expired.html'), 410

    summary = json.loads(link.summary_json)
    return render_template('oncall_handoff_public.html', summary=summary)


# ======================================================================
# JSON API: Pending count for nav badge (F7e)
# ======================================================================
@oncall_bp.route('/api/oncall/pending-count')
@login_required
def pending_count_api():
    """Return pending documentation count for nav badge."""
    count = OnCallNote.query.filter_by(
        user_id=current_user.id, documentation_status='pending'
    ).count()
    return jsonify({'count': count})


# ======================================================================
# POST /oncall/<id>/forward — Forward note to another provider (F7)
# ======================================================================
@oncall_bp.route('/oncall/<int:note_id>/forward', methods=['POST'])
@login_required
def forward_note(note_id):
    """Forward an on-call note to another provider."""
    note = OnCallNote.query.filter_by(
        id=note_id, user_id=current_user.id
    ).first_or_404()

    provider_id = request.form.get('provider_id', '').strip()
    if not provider_id or not provider_id.isdigit():
        flash('Please select a provider to forward to.', 'error')
        return redirect(url_for('oncall.index'))

    target_user = db.session.get(User, int(provider_id))
    if not target_user or not target_user.is_active_account:
        flash('Invalid provider selected.', 'error')
        return redirect(url_for('oncall.index'))

    note.forwarded_to = target_user.id
    note.forwarded_at = datetime.now(timezone.utc)
    db.session.commit()

    flash(f'Note forwarded to {target_user.display_name}.', 'success')
    return redirect(url_for('oncall.index'))

"""
CareCompanion — Note Reformatter Model

File location: carecompanion/models/reformatter.py

Tracks each note-reformatting session (Phase 9).  When a provider
runs the reformatter wizard, this record logs which note was
processed, its status, and any items the classifier could not
automatically template (stored as JSON in flagged_items).

HIPAA note: This table does NOT store the note text itself —
only metadata about the reformatting session.  The actual note
content lives in Amazing Charts.
"""

import json
from datetime import datetime, timezone
from models import db


class ReformatLog(db.Model):
    """
    One row per note-reformatting session.  The flagged_items
    JSON column holds a list of dicts describing items that
    need human review before the reformat is finalized.

    Example flagged_items entry:
    [
        {
            "text": "Lisinopril 10mg",
            "section": "medications",
            "reason": "Could not match to known medication list",
            "flagged_at": "2025-06-15T14:30:00"
        }
    ]
    """
    __tablename__ = 'reformat_logs'

    # ---- Primary key -----------------------------------------------------
    id = db.Column(db.Integer, primary_key=True)

    # ---- Who ran the reformatter -----------------------------------------
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )

    # ---- Source note metadata --------------------------------------------
    source_note_date = db.Column(db.DateTime, nullable=True)
    source_provider = db.Column(db.String(120), default='')
    visit_type = db.Column(db.String(50), default='')

    # ---- Reformat status -------------------------------------------------
    # Values: 'pending', 'complete', 'needs_review'
    reformat_status = db.Column(
        db.String(20), nullable=False, default='pending'
    )

    # ---- Flagged items (JSON) --------------------------------------------
    # Items the classifier could not automatically place into the template.
    # Stored as a JSON string; use the helper properties below to read/write.
    _flagged_items = db.Column('flagged_items', db.Text, default='[]')

    # ---- Timestamps ------------------------------------------------------
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    completed_at = db.Column(db.DateTime, nullable=True)

    # ---- Relationships ---------------------------------------------------
    user = db.relationship('User', backref='reformat_logs', lazy=True)

    # ------------------------------------------------------------------
    # Flagged items helpers — read and write the JSON column safely
    # ------------------------------------------------------------------
    @property
    def flagged_items(self):
        """Return the flagged items list (parsed from JSON)."""
        try:
            return json.loads(self._flagged_items or '[]')
        except (json.JSONDecodeError, TypeError):
            return []

    @flagged_items.setter
    def flagged_items(self, value):
        """Accept a Python list and store it as JSON text."""
        self._flagged_items = json.dumps(value)

    def __repr__(self):
        return f'<ReformatLog {self.id} status={self.reformat_status}>'

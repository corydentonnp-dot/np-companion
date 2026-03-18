"""
NP Companion — Inbox Monitoring Models

File location: np-companion/models/inbox.py

Two tables work together:
  - InboxSnapshot: a point-in-time count of items per category
    (captured every time the inbox monitor OCR job runs).
  - InboxItem: individual items tracked across snapshots so the
    app can detect new arrivals, aging items, and resolution.

HIPAA note: InboxItem stores only a hash of the item content,
never the actual patient name or clinical detail.
"""

from datetime import datetime, timezone
from models import db


class InboxSnapshot(db.Model):
    """
    One row per inbox OCR scan.  Stores category counts so the
    dashboard and briefing can show trends over time.
    """
    __tablename__ = 'inbox_snapshots'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )

    # When this snapshot was captured (UTC)
    captured_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    # ---- Category counts -------------------------------------------------
    labs_count = db.Column(db.Integer, default=0)
    radiology_count = db.Column(db.Integer, default=0)
    messages_count = db.Column(db.Integer, default=0)
    refills_count = db.Column(db.Integer, default=0)
    other_count = db.Column(db.Integer, default=0)

    # ---- Relationships ---------------------------------------------------
    user = db.relationship('User', backref='inbox_snapshots', lazy=True)

    def __repr__(self):
        total = (self.labs_count + self.radiology_count +
                 self.messages_count + self.refills_count + self.other_count)
        return f'<InboxSnapshot {self.id} total={total}>'


class InboxItem(db.Model):
    """
    One row per unique inbox item detected by the OCR diff engine.
    The item_hash is a non-reversible identifier so we can track
    the same item across multiple snapshots without storing PHI.
    """
    __tablename__ = 'inbox_items'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )

    # Non-reversible hash that uniquely identifies this inbox entry
    item_hash = db.Column(db.String(64), nullable=False, index=True)

    # Category: lab, rad, message, refill, other
    item_type = db.Column(db.String(20), nullable=False, default='other')

    # ---- Tracking dates --------------------------------------------------
    first_seen_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    last_seen_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # ---- Status ----------------------------------------------------------
    is_resolved = db.Column(db.Boolean, default=False)
    is_held = db.Column(db.Boolean, default=False)
    held_reason = db.Column(db.String(200), default='')

    # normal or critical (critical = immediate push notification)
    priority = db.Column(db.String(20), default='normal')

    # ---- Relationships ---------------------------------------------------
    user = db.relationship('User', backref='inbox_items', lazy=True)

    def __repr__(self):
        return f'<InboxItem {self.id} type={self.item_type} resolved={self.is_resolved}>'

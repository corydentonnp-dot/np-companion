"""
CareCompanion — Order Set Models

File location: carecompanion/models/orderset.py

Tables:
  - OrderSet: a named collection of orders tied to a visit type.
    Can be personal or shared with the practice.
  - OrderItem: one specific order within a set, including the
    exact tab and label text used by the PyAutoGUI executor to
    click the right item in Amazing Charts.
  - MasterOrder: the master list of all known orders available
    for adding to order sets.
  - OrderSetVersion: snapshot history for rollback (F8b).
  - OrderExecution / OrderExecutionItem: execution state tracking (F8e).
"""

import json
from datetime import datetime, timezone
from models import db

# Valid AC order tab names (confirmed from AC orders spreadsheet + v4 screenshots).
# These are the exact tab labels in the AC Orders window.
# The first 4 are populated with orders; the last 4 are currently empty in AC.
ORDER_TABS = [
    'Nursing', 'Labs', 'Imaging', 'Diagnostics',
    'Referrals', 'Follow Up', 'Patient Education', 'Other',
]


class OrderSet(db.Model):
    """
    A named, reusable group of orders.  When executed, the
    PyAutoGUI runner walks through each OrderItem in sort_order.
    """
    __tablename__ = 'order_sets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )

    name = db.Column(db.String(120), nullable=False)
    visit_type = db.Column(db.String(50), default='')
    is_shared = db.Column(db.Boolean, default=False)
    is_retracted = db.Column(db.Boolean, default=False)

    # F8a: who shared this set (original author)
    shared_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    # F8a: if forked, which set it was copied from
    forked_from_id = db.Column(db.Integer, db.ForeignKey('order_sets.id'), nullable=True)

    version = db.Column(db.Integer, default=1)

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship('User', foreign_keys=[user_id], backref='order_sets', lazy=True)
    shared_by_user = db.relationship('User', foreign_keys=[shared_by_user_id], lazy=True)
    items = db.relationship(
        'OrderItem', backref='order_set', lazy=True,
        cascade='all, delete-orphan', order_by='OrderItem.sort_order'
    )
    versions = db.relationship(
        'OrderSetVersion', backref='order_set', lazy=True,
        cascade='all, delete-orphan', order_by='OrderSetVersion.version_number.desc()'
    )

    def __repr__(self):
        return f'<OrderSet {self.id} "{self.name}" v{self.version}>'

    def snapshot_json(self):
        """Serialize current items to JSON for version history."""
        return json.dumps([{
            'order_name': i.order_name,
            'order_tab': i.order_tab,
            'order_label': i.order_label,
            'is_default': i.is_default,
            'sort_order': i.sort_order,
        } for i in self.items])


class OrderItem(db.Model):
    """
    One clickable order within an OrderSet.  The order_tab and
    order_label fields must match exactly what appears in Amazing
    Charts so the PyAutoGUI executor can locate them.
    """
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    orderset_id = db.Column(
        db.Integer, db.ForeignKey('order_sets.id'), nullable=False, index=True
    )
    order_name = db.Column(db.String(200), nullable=False)
    order_tab = db.Column(db.String(100), default='')
    order_label = db.Column(db.String(200), default='')
    is_default = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<OrderItem {self.id} "{self.order_name}">'


class MasterOrder(db.Model):
    """Master list of all known orders available for use in any order set."""
    __tablename__ = 'master_orders'

    id = db.Column(db.Integer, primary_key=True)
    order_name = db.Column(db.String(200), nullable=False, unique=True)
    order_tab = db.Column(db.String(100), default='')
    order_label = db.Column(db.String(200), default='')
    category = db.Column(db.String(100), default='')
    # CPT procedure code or LabCorp test number (from AC orders spreadsheet)
    cpt_code = db.Column(db.String(20), default='')
    # Starred as commonly ordered — shows at top of browser
    is_common = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<MasterOrder {self.id} "{self.order_name}">'


class OrderSetVersion(db.Model):
    """Snapshot of an order set at a point in time for rollback (F8b)."""
    __tablename__ = 'order_set_versions'

    id = db.Column(db.Integer, primary_key=True)
    orderset_id = db.Column(
        db.Integer, db.ForeignKey('order_sets.id'), nullable=False, index=True
    )
    version_number = db.Column(db.Integer, nullable=False)
    snapshot_json = db.Column(db.Text, nullable=False)
    saved_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    saved_by_user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False
    )

    saved_by = db.relationship('User', lazy=True)

    def __repr__(self):
        return f'<OrderSetVersion set={self.orderset_id} v{self.version_number}>'


class OrderExecution(db.Model):
    """Tracks a single execution attempt of an order set (F8e)."""
    __tablename__ = 'order_executions'

    id = db.Column(db.Integer, primary_key=True)
    orderset_id = db.Column(
        db.Integer, db.ForeignKey('order_sets.id'), nullable=False, index=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False
    )
    # 'in_progress', 'completed', 'failed', 'interrupted'
    status = db.Column(db.String(20), default='in_progress')
    total_items = db.Column(db.Integer, default=0)
    completed_items = db.Column(db.Integer, default=0)
    failed_items = db.Column(db.Integer, default=0)
    pre_screenshot = db.Column(db.String(400), default='')
    error_message = db.Column(db.Text, default='')
    started_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    finished_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', lazy=True)
    items = db.relationship(
        'OrderExecutionItem', backref='execution', lazy=True,
        cascade='all, delete-orphan', order_by='OrderExecutionItem.sort_order'
    )

    def __repr__(self):
        return f'<OrderExecution {self.id} {self.status}>'


class OrderExecutionItem(db.Model):
    """Tracks individual order item execution status within an execution (F8e)."""
    __tablename__ = 'order_execution_items'

    id = db.Column(db.Integer, primary_key=True)
    execution_id = db.Column(
        db.Integer, db.ForeignKey('order_executions.id'), nullable=False, index=True
    )
    order_name = db.Column(db.String(200), nullable=False)
    order_tab = db.Column(db.String(100), default='')
    order_label = db.Column(db.String(200), default='')
    sort_order = db.Column(db.Integer, default=0)
    # 'pending', 'completed', 'failed', 'skipped'
    status = db.Column(db.String(20), default='pending')
    error_screenshot = db.Column(db.String(400), default='')
    error_message = db.Column(db.Text, default='')

    def __repr__(self):
        return f'<OrderExecutionItem {self.id} "{self.order_name}" {self.status}>'

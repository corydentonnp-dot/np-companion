"""
CareCompanion — Bookmark Models
File: models/bookmark.py

ORM model for practice-wide bookmarks (admin-managed).
Personal bookmarks are stored in user.preferences['bookmarks'] JSON.
"""

from datetime import datetime, timezone
from models import db


class PracticeBookmark(db.Model):
    """Practice-wide bookmark visible to all users, managed by admins."""
    __tablename__ = 'practice_bookmark'

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    icon_url = db.Column(db.String(500), default='')
    sort_order = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<PracticeBookmark id={self.id} label={self.label!r}>'

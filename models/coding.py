from datetime import datetime, timezone

from models import db


class CodeFavorite(db.Model):
    """F17: Provider's saved ICD-10 code favorites for quick access."""
    __tablename__ = 'code_favorite'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    icd10_code = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(300), default='')
    use_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'icd10_code', name='uq_user_code_fav'),
    )

    def __repr__(self):
        return f'<CodeFavorite id={self.id} code={self.icd10_code!r}>'


class CodePairing(db.Model):
    """F17c: Tracks ICD-10 code pairs used together for pairing suggestions."""
    __tablename__ = 'code_pairing'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    code_a = db.Column(db.String(20), nullable=False)
    code_b = db.Column(db.String(20), nullable=False)
    pair_count = db.Column(db.Integer, default=1)
    last_used = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'code_a', 'code_b', name='uq_user_code_pair'),
    )

    def __repr__(self):
        return f'<CodePairing id={self.id} {self.code_a}-{self.code_b}>'

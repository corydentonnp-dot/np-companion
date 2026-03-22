"""
Phase 31 — Clinical Calculator Result Storage Model

Stores computed risk scores for patients, with full input snapshot for audit trail
and is_current flag for supersession tracking.
"""

from datetime import datetime, timezone
from models import db
from sqlalchemy import Column, Integer, Float, String, Boolean, Text, DateTime, ForeignKey, Index


class CalculatorResult(db.Model):
    """Stores a computed calculator score for a patient."""
    __tablename__ = 'calculator_result'

    id              = Column(Integer, primary_key=True)
    user_id         = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    mrn             = Column(String(50), nullable=False, index=True)
    calculator_key  = Column(String(50), nullable=False, index=True)
    score_value     = Column(Float, nullable=True)
    score_label     = Column(String(100), nullable=True)
    score_detail    = Column(Text, nullable=True)   # JSON: component values, sub-scores
    input_snapshot  = Column(Text, nullable=True)   # JSON: all inputs used (audit trail)
    data_source     = Column(String(20), default='auto_ehr')   # auto_ehr | semi_auto | manual
    is_current      = Column(Boolean, default=True, nullable=False)
    computed_at     = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_calc_result_mrn_key_current', 'mrn', 'calculator_key', 'is_current'),
    )

    def __repr__(self):
        return f'<CalculatorResult id={self.id} key={self.calculator_key!r}>'

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'mrn': self.mrn,
            'calculator_key': self.calculator_key,
            'score_value': self.score_value,
            'score_label': self.score_label,
            'score_detail': json.loads(self.score_detail) if self.score_detail else {},
            'input_snapshot': json.loads(self.input_snapshot) if self.input_snapshot else {},
            'data_source': self.data_source,
            'is_current': self.is_current,
            'computed_at': self.computed_at.isoformat() if self.computed_at else None,
        }

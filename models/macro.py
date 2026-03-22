"""
CareCompanion — Macro & Dot Phrase Models
File: models/macro.py

Models for the AutoHotkey Macro Manager & Dot Phrase Engine (F23):
- AhkMacro: Named macros with hotkeys and AHK script content
- DotPhrase: Text-expansion shortcodes (map to AHK hotstrings)
- MacroStep: Individual recorded steps within a macro
- MacroVariable: User-defined input variables for macro runtime prompts
"""

from datetime import datetime, timezone
from models import db


class AhkMacro(db.Model):
    """An AutoHotkey macro with optional hotkey binding and generated script."""
    __tablename__ = 'ahk_macros'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    hotkey = db.Column(db.String(50), default='')
    script_content = db.Column(db.Text, default='')
    category = db.Column(db.String(50), default='custom', index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    steps = db.relationship('MacroStep', backref='macro', cascade='all, delete-orphan',
                            order_by='MacroStep.step_order')
    variables = db.relationship('MacroVariable', backref='macro', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<AhkMacro {self.id} {self.name}>'


class DotPhrase(db.Model):
    """A text-expansion dot phrase that maps to an AHK hotstring."""
    __tablename__ = 'dot_phrases'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    abbreviation = db.Column(db.String(50), nullable=False)
    expansion = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='custom', index=True)
    placeholders = db.Column(db.Text, default='')  # JSON list of {placeholder} tokens
    use_count = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_shared = db.Column(db.Boolean, default=False)
    copied_from_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'abbreviation', name='uq_dot_phrase_user_abbrev'),
    )

    def __repr__(self):
        return f'<DotPhrase {self.id} {self.abbreviation}>'


class MacroStep(db.Model):
    """A single recorded step within a macro (click, send_keys, sleep, etc.)."""
    __tablename__ = 'macro_steps'

    id = db.Column(db.Integer, primary_key=True)
    macro_id = db.Column(db.Integer, db.ForeignKey('ahk_macros.id', ondelete='CASCADE'),
                         nullable=False, index=True)
    step_order = db.Column(db.Integer, nullable=False)
    action_type = db.Column(db.String(30), nullable=False)
    target_x = db.Column(db.Integer, nullable=True)
    target_y = db.Column(db.Integer, nullable=True)
    key_sequence = db.Column(db.String(200), nullable=True)
    delay_ms = db.Column(db.Integer, default=100)
    window_title = db.Column(db.String(200), nullable=True)
    comment = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<MacroStep {self.id} #{self.step_order} {self.action_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'macro_id': self.macro_id,
            'step_order': self.step_order,
            'action_type': self.action_type,
            'target_x': self.target_x,
            'target_y': self.target_y,
            'key_sequence': self.key_sequence,
            'delay_ms': self.delay_ms,
            'window_title': self.window_title,
            'comment': self.comment,
        }


class MacroVariable(db.Model):
    """A user-defined input variable for a macro — becomes an InputBox prompt in AHK."""
    __tablename__ = 'macro_variables'

    id = db.Column(db.Integer, primary_key=True)
    macro_id = db.Column(db.Integer, db.ForeignKey('ahk_macros.id', ondelete='CASCADE'),
                         nullable=False, index=True)
    var_name = db.Column(db.String(50), nullable=False)
    var_label = db.Column(db.String(100), default='')
    default_value = db.Column(db.String(200), default='')
    var_type = db.Column(db.String(20), default='text')
    choices = db.Column(db.Text, nullable=True)  # JSON for dropdown options

    def __repr__(self):
        return f'<MacroVariable {self.id} {self.var_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'macro_id': self.macro_id,
            'var_name': self.var_name,
            'var_label': self.var_label,
            'default_value': self.default_value,
            'var_type': self.var_type,
            'choices': self.choices,
        }

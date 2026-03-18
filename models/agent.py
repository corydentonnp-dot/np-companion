"""
NP Companion — Agent Log & Error Models

File location: np-companion/models/agent.py

Two tables for tracking the background agent's health:
  - AgentLog: startup/shutdown/heartbeat events and crash recovery info.
  - AgentError: detailed error records with full tracebacks so the
    admin can diagnose failures without reading log files.
"""

from datetime import datetime, timezone
from models import db


class AgentLog(db.Model):
    """
    Records agent lifecycle events: startup, shutdown, heartbeat,
    and crash-recovery actions.  The admin agent dashboard reads
    this table to show uptime and last heartbeat.
    """
    __tablename__ = 'agent_logs'

    id = db.Column(db.Integer, primary_key=True)

    # Event type: 'startup', 'shutdown', 'heartbeat', 'crash_recovery'
    event = db.Column(db.String(50), nullable=False)

    # Process ID of the agent (useful for detecting stale entries)
    pid = db.Column(db.Integer, nullable=True)

    # Extra details — e.g. "Recovered 2 incomplete time logs"
    details = db.Column(db.Text, default='')

    timestamp = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    def __repr__(self):
        return f'<AgentLog {self.id} {self.event}>'


class AgentError(db.Model):
    """
    Stores errors caught by the agent's try/except wrappers.
    Each job failure creates one row with the full traceback.
    """
    __tablename__ = 'agent_errors'

    id = db.Column(db.Integer, primary_key=True)

    # Which job or component failed — e.g. 'inbox_check', 'mrn_reader'
    job_name = db.Column(db.String(100), nullable=False)

    # The error message (str(exception))
    error_message = db.Column(db.Text, nullable=False)

    # Full traceback for debugging
    traceback = db.Column(db.Text, default='')

    # Which user was active when the error happened (nullable)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=True
    )

    timestamp = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    # ---- Relationships ---------------------------------------------------
    user = db.relationship('User', backref='agent_errors', lazy=True)

    def __repr__(self):
        return f'<AgentError {self.id} job={self.job_name}>'

"""
CareCompanion — Lab Tracking Models

File location: carecompanion/models/labtrack.py

Tables:
  - LabTrack: defines WHICH lab to monitor for a patient, how
    often, and what thresholds trigger alerts.
  - LabResult: individual result values linked to a LabTrack
    record, used for trend graphing and critical-value detection.
  - LabPanel: predefined groupings of related labs (F11d).

HIPAA note: Full MRN is stored for clinical accuracy.
Display in the UI should show only the last 4 digits.
"""

from datetime import datetime, timezone
from models import db


class LabTrack(db.Model):
    """
    One row per lab-being-monitored for a specific patient.
    Example: user 3 monitors 'HbA1c' for MRN 123456 every 90 days.
    """
    __tablename__ = 'lab_tracks'

    # ---- Primary key -----------------------------------------------------
    id = db.Column(db.Integer, primary_key=True)

    # ---- Who set this up and for which patient ---------------------------
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )
    mrn = db.Column(db.String(20), nullable=False, index=True)

    # ---- What lab and how often ------------------------------------------
    lab_name = db.Column(db.String(100), nullable=False)
    interval_days = db.Column(db.Integer, default=90)

    # ---- Alert thresholds (F11b) -----------------------------------------
    alert_low = db.Column(db.Float, nullable=True)
    alert_high = db.Column(db.Float, nullable=True)
    critical_low = db.Column(db.Float, nullable=True)
    critical_high = db.Column(db.Float, nullable=True)

    # ---- Panel grouping (F11d) -------------------------------------------
    panel_name = db.Column(db.String(80), default='')

    # ---- Status tracking -------------------------------------------------
    is_overdue = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    last_checked = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, default='')
    source = db.Column(db.String(20), default='manual')  # 'manual' or 'inbox'

    # ---- Relationships ---------------------------------------------------
    user = db.relationship('User', backref='lab_tracks', lazy=True)
    results = db.relationship(
        'LabResult', backref='lab_track', lazy=True,
        cascade='all, delete-orphan', order_by='LabResult.result_date.desc()'
    )

    @property
    def next_due(self):
        """Calculate next due date from last_checked + interval_days."""
        if self.last_checked and self.interval_days:
            from datetime import timedelta
            return self.last_checked + timedelta(days=self.interval_days)
        return None

    @property
    def status(self):
        """Return status string: 'critical', 'overdue', 'due_soon', 'on_track'."""
        from datetime import timedelta
        now = datetime.now(timezone.utc)

        # Check most recent result for critical value
        if self.results:
            latest = self.results[0]
            if latest.is_critical:
                return 'critical'

        # Check overdue
        if self.next_due and now > self.next_due:
            return 'overdue'

        # Check due soon (within 14 days)
        if self.next_due:
            if now > self.next_due - timedelta(days=14):
                return 'due_soon'

        return 'on_track'

    @property
    def trend(self):
        """Compute trend from last 3 results: 'up', 'down', or 'stable'."""
        vals = []
        for r in self.results[:3]:
            try:
                vals.append(float(r.result_value))
            except (ValueError, TypeError):
                continue
        if len(vals) < 2:
            return 'stable'
        if vals[0] > vals[1]:
            return 'up'
        elif vals[0] < vals[1]:
            return 'down'
        return 'stable'

    def __repr__(self):
        return f'<LabTrack {self.id} {self.lab_name} mrn={self.mrn or ""}>'


class LabResult(db.Model):
    """
    One lab result value for a tracked lab.  result_value is stored
    as a string because some results are non-numeric (e.g. 'Positive').
    """
    __tablename__ = 'lab_results'

    # ---- Primary key -----------------------------------------------------
    id = db.Column(db.Integer, primary_key=True)

    # ---- Parent tracker --------------------------------------------------
    labtrack_id = db.Column(
        db.Integer, db.ForeignKey('lab_tracks.id'), nullable=False, index=True
    )

    # ---- Result data -----------------------------------------------------
    result_value = db.Column(db.String(50), nullable=False)
    result_date = db.Column(db.DateTime, nullable=False)
    is_critical = db.Column(db.Boolean, default=False)

    # up, down, or stable compared to previous result
    trend_direction = db.Column(db.String(10), default='stable')

    def __repr__(self):
        return f'<LabResult {self.id} value={self.result_value}>'


# ======================================================================
# F11d: Lab Panel Definitions
# ======================================================================

# Standard panels — used to seed the LabPanel table and as defaults
STANDARD_PANELS = {
    'BMP': ['Na', 'K', 'Cl', 'CO2', 'BUN', 'Cr', 'Glucose'],
    'CMP': ['Na', 'K', 'Cl', 'CO2', 'BUN', 'Cr', 'Glucose',
            'AST', 'ALT', 'Alk Phos', 'Total Bilirubin', 'Albumin', 'Total Protein'],
    'CBC': ['WBC', 'RBC', 'Hgb', 'Hct', 'Platelets', 'MCV', 'MCH', 'MCHC', 'RDW'],
    'Lipids': ['Total Cholesterol', 'LDL', 'HDL', 'Triglycerides'],
    'Thyroid': ['TSH', 'Free T4', 'Free T3'],
    'Diabetes': ['HbA1c', 'Fasting Glucose', 'Microalbumin'],
}


class LabPanel(db.Model):
    """
    Predefined panel groupings for related labs (F11d).
    Users can add tracking for an entire panel at once.
    """
    __tablename__ = 'lab_panels'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    components_json = db.Column(db.Text, nullable=False, default='[]')

    def __repr__(self):
        return f'<LabPanel {self.id} "{self.name}">'

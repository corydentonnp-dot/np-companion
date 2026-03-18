"""
NP Companion — Schedule Model

File location: np-companion/models/schedule.py

Stores appointment data scraped from NetPractice.  Each row is one
appointment slot for one day.  The scraper runs nightly (for tomorrow)
and on demand (for today).

The is_new_patient flag is set by comparing the patient name against
prior appointments in the database.  A gold "NEW" badge shows in
the Today View for any is_new_patient=True appointment.

HIPAA note: patient_name is stored for schedule display only.
The UI should never expose full names outside the authenticated app.
"""

from datetime import datetime, timezone
from models import db


class Schedule(db.Model):
    """One row per appointment slot on a given date."""
    __tablename__ = 'schedules'

    # ---- Primary key -----------------------------------------------------
    id = db.Column(db.Integer, primary_key=True)

    # ---- Who scraped this ------------------------------------------------
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True
    )

    # ---- Appointment details ---------------------------------------------
    appointment_date = db.Column(db.Date, nullable=False, index=True)
    appointment_time = db.Column(db.String(10), nullable=False)   # e.g. "09:30"
    patient_name = db.Column(db.String(200), default='')
    patient_mrn = db.Column(db.String(20), default='')            # e.g. "54391"
    patient_dob = db.Column(db.String(20), default='')            # MM/DD/YYYY
    patient_phone = db.Column(db.String(30), default='')
    visit_type = db.Column(db.String(100), default='')            # e.g. "PHYSICAL/EST" (from title attr)
    visit_type_code = db.Column(db.String(10), default='')        # e.g. "PE", "GV", "AV" (from jsModApt)
    reason = db.Column(db.String(300), default='')                # e.g. "COUGHING + CONG" (detail page only)
    duration_minutes = db.Column(db.Integer, default=15)           # booked slot length
    units = db.Column(db.Integer, default=1)                       # scheduling units
    provider_name = db.Column(db.String(100), default='')
    location = db.Column(db.String(100), default='')
    status = db.Column(db.String(50), default='scheduled')        # e.g. "TEXT SENT (TS)"
    comment = db.Column(db.String(500), default='')
    entered_by = db.Column(db.String(100), default='')            # who booked the appointment
    bg_color = db.Column(db.String(20), default='')               # schedule row color (e.g. "#FF99CC")
    verification = db.Column(db.String(200), default='')          # insurance verification status

    # ---- New patient detection -------------------------------------------
    is_new_patient = db.Column(db.Boolean, default=False)

    # ---- Anomaly flags (JSON string) -------------------------------------
    # e.g. '["back_to_back_complex", "short_appointment"]'
    anomaly_flags = db.Column(db.Text, default='[]')

    # ---- Scrape metadata -------------------------------------------------
    scraped_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # ---- Relationships ---------------------------------------------------
    user = db.relationship('User', backref='schedules', lazy=True)

    def __repr__(self):
        return (
            f'<Schedule {self.id} '
            f'{self.appointment_date} {self.appointment_time} '
            f'{self.visit_type}>'
        )

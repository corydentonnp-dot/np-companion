"""
NP Companion — Database Models Package

File location: np-companion/models/__init__.py

Creates the shared SQLAlchemy database instance that every model
file and every route file imports.  Binding to the Flask app happens
inside create_app() in app.py via db.init_app(app).

As you build each model file, uncomment the matching import line
below so SQLAlchemy registers the table when db.create_all() runs.
"""

from flask_sqlalchemy import SQLAlchemy

# Shared database instance.
# Usage in other files:  from models import db
db = SQLAlchemy()

# ------------------------------------------------------------------
# Import every model here so SQLAlchemy discovers the tables.
# Uncomment each line once you create the corresponding file.
# ------------------------------------------------------------------
from models.user import User
from models.audit import AuditLog
from models.timelog import TimeLog
from models.inbox import InboxSnapshot, InboxItem
from models.oncall import OnCallNote, HandoffLink  # noqa: F811 — extends oncall imports
from models.orderset import (
    OrderSet, OrderItem, MasterOrder, OrderSetVersion,
    OrderExecution, OrderExecutionItem,
)
from models.medication import MedicationEntry
from models.labtrack import LabTrack, LabResult, LabPanel
from models.caregap import CareGap, CareGapRule
from models.tickler import Tickler
from models.message import DelayedMessage
from models.reformatter import ReformatLog
from models.agent import AgentLog, AgentError
from models.schedule import Schedule
from models.notification import Notification
from models.patient import (
    PatientVitals, PatientRecord, PatientMedication,
    PatientDiagnosis, PatientAllergy, PatientImmunization,
    PatientNoteDraft, PatientSpecialist, Icd10Cache, RxNormCache,
)
from models.billing import BillingOpportunity, BillingRuleCache
from models.tools import ControlledSubstanceEntry, CodeFavorite, CodePairing, PriorAuthorization

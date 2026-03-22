"""
CareCompanion — TCM Detector
billing_engine/detectors/tcm.py

Transitional Care Management — 99495 (moderate), 99496 (high complexity).
30-day post-discharge window with 2-business-day contact deadline.
"""

from datetime import datetime, date, timedelta

from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn, add_business_days


class TCMDetector(BaseDetector):
    """Transitional Care Management (TCM) detector."""

    CATEGORY = "tcm"
    DESCRIPTION = "TCM billing within 30-day post-discharge window"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        discharge_date = pd.get("discharge_date")
        if not discharge_date:
            return []

        if isinstance(discharge_date, str):
            try:
                discharge_date = datetime.strptime(discharge_date[:10], "%Y-%m-%d").date()
            except ValueError:
                return []

        today = date.today()
        days_since_discharge = (today - discharge_date).days

        if days_since_discharge > 30:
            return []

        contact_deadline = add_business_days(discharge_date, 2)
        days_until_deadline = (contact_deadline - today).days

        days_available_for_f2f = (discharge_date + timedelta(days=7)) - today
        mdm_complexity = (pd.get("mdm_complexity") or "").lower()

        if mdm_complexity == "high" and days_available_for_f2f.days >= 0:
            code = "99496"
        else:
            # Default to 99495 (moderate); 99496 requires documented high MDM
            code = "99495"
        est_revenue = self._get_rate(code)

        if days_until_deadline < 0:
            urgency = "OVERDUE — contact deadline passed"
            confidence = "LOW"
        elif days_until_deadline == 0:
            urgency = "URGENT — contact required TODAY"
            confidence = "HIGH"
        elif days_until_deadline <= 1:
            urgency = f"URGENT — contact deadline: {contact_deadline}"
            confidence = "HIGH"
        else:
            urgency = f"Contact deadline: {contact_deadline} ({days_until_deadline} business days)"
            confidence = "MEDIUM"

        eligibility = (
            f"Discharge detected {days_since_discharge} days ago. "
            f"{urgency}. "
            f"F2F visit required within {'7' if code == '99496' else '14'} days of discharge."
        )

        doc_required = (
            f"Document: (1) Date of discharge and facility name. "
            f"(2) Date of initial interactive contact within 2 business days. "
            f"(3) Face-to-face visit within {'7' if code == '99496' else '14'} days. "
            f"(4) Medication reconciliation. "
            f"(5) Care plan review with patient/caregiver."
        )

        insurer = pd.get("insurer_type") or "unknown"
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        opp = self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="TCM",
            codes=[code],
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=doc_required,
            confidence_level=confidence,
            insurer_caveat=None,
            insurer_type=insurer,
        )
        return [opp]

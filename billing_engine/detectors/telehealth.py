"""
CareCompanion — Telehealth Detector
billing_engine/detectors/telehealth.py

Phone E/M (99441-99443), digital E/M (99421-99423),
interprofessional consultation (99452).  Phase 19C.1.
"""

from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn


class TelehealthDetector(BaseDetector):
    """Telehealth / virtual visit billing detector."""

    CATEGORY = "telehealth"
    DESCRIPTION = "Phone E/M, digital E/M, interprofessional consult"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        opps = []

        # ── TELE_PHONE_EM ──
        phone_minutes = pd.get("phone_encounter_minutes") or 0
        phone_resulted_in_visit = pd.get("phone_resulted_in_visit_24hr") or False

        if phone_minutes >= 5 and not phone_resulted_in_visit:
            if phone_minutes >= 21:
                code = "99443"
            elif phone_minutes >= 11:
                code = "99442"
            else:
                code = "99441"

            opps.append(self._build(pd, code,
                opportunity_code="TELE_PHONE_EM",
                eligibility=(
                    f"Telephone encounter: {phone_minutes} min of medical discussion. "
                    "Did not result in an in-person visit within 24 hours."
                ),
                doc=(
                    "Document phone encounter: duration, reason for call, "
                    "clinical decision-making, assessment and plan. "
                    "Must NOT result in an office visit within 24 hours."
                ),
                checklist='["Document call duration","Document clinical reason","Document assessment and plan","Verify no in-person visit within 24hr"]',
            ))

        # ── TELE_DIGITAL_EM ──
        portal_minutes_7day = pd.get("portal_message_minutes_7day") or 0

        if portal_minutes_7day >= 5:
            if portal_minutes_7day >= 21:
                code = "99423"
            elif portal_minutes_7day >= 11:
                code = "99422"
            else:
                code = "99421"

            opps.append(self._build(pd, code,
                opportunity_code="TELE_DIGITAL_EM",
                eligibility=(
                    f"Patient-initiated portal messages: {portal_minutes_7day} min "
                    "cumulative provider time over 7-day period."
                ),
                doc=(
                    "Document cumulative time spent on patient-initiated "
                    "digital/portal communications over 7-day period. "
                    "Must be patient-initiated (not provider-initiated)."
                ),
                checklist='["Verify messages are patient-initiated","Track cumulative time over 7 days","Document clinical content of messages","Document assessment and plan"]',
            ))

        # ── TELE_INTERPROF ──
        interprof_minutes = pd.get("interprofessional_consult_minutes") or 0

        if interprof_minutes >= 16:
            opps.append(self._build(pd, "99452",
                opportunity_code="TELE_INTERPROF",
                eligibility=(
                    f"Interprofessional consult: {interprof_minutes} min reviewing "
                    "specialist phone/electronic consultation."
                ),
                doc=(
                    "Document specialist consulted, clinical question, "
                    "time spent reviewing (16+ min required), "
                    "verbal/written report to patient/family."
                ),
                checklist='["Document specialist name and specialty","Document clinical question","Document review time (16+ min)","Provide verbal/written report to patient"]',
            ))

        return opps

    def _build(self, pd, code, *, opportunity_code, eligibility, doc, checklist):
        insurer = pd.get("insurer_type") or "unknown"
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        return self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="telehealth",
            codes=[code],
            est_revenue=self._get_rate(code),
            eligibility_basis=eligibility,
            documentation_required=doc,
            confidence_level="MEDIUM",
            insurer_caveat=None,
            insurer_type=insurer,
            opportunity_code=opportunity_code,
            priority="medium",
            documentation_checklist=checklist,
        )

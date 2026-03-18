"""
NP Companion — Billing Opportunity Rules Engine
File: app/services/billing_rules.py

Implements seven billing rule categories based on 2025 CMS guidelines.
Cross-references patient diagnoses, medications, insurer type, visit type,
and time tracking data to surface billing opportunities the provider
might otherwise miss.

Rule categories (all hardcoded from CY 2025 CMS Final Rule):
1. Chronic Care Management (CCM) — 99490, 99439, 99491, 99437, 99487, 99489
2. Annual Wellness Visit (AWV) — G0402, G0438, G0439 + 2025 add-on stack
3. G2211 Complexity Add-On — established patients with serious/complex conditions
4. Transitional Care Management (TCM) — 99495, 99496 with 2-business-day window
5. Prolonged Service (99417) — 99214 and 99215 time thresholds
6. Behavioral Health Integration (BHI) — 99484 with behavioral health diagnosis
7. Remote Patient Monitoring (RPM) — 99453, 99454, 99457, 99458

All billing decisions remain with the provider. This engine only flags and
suggests — it never submits anything to a payer.

Dependencies:
- models/billing.py (BillingOpportunity model)
- models (db instance)
- app/api_config.py (CCM, AWV, BHI, RPM code constants, condition prefix lists)
- app/services/api/cms_pfs.py (payment rate lookups)

NP Companion features that rely on this module:
- Today View billing card (pre-visit opportunities)
- Post-visit billing review (Timer/Billing module)
- Monthly Billing Report (F14c)
- Metrics dashboard (F13) — opportunity gap tracking

HIPAA note: patient_mrn_hash (SHA-256) is used — never the plain MRN.
"""

import hashlib
import logging
from datetime import datetime, date, timezone, timedelta

from app.api_config import (
    CCM_CODES,
    AWV_CODES,
    AWV_ADDON_CODES,
    TCM_CODES,
    EM_ADDON_CODES,
    BHI_CODES,
    RPM_CODES,
    PROLONGED_SERVICE_THRESHOLDS,
    CCM_CHRONIC_CONDITION_PREFIXES,
    BHI_CONDITION_PREFIXES,
    RPM_CONDITION_PREFIXES,
    CURRENT_FEE_SCHEDULE_YEAR,
)

logger = logging.getLogger(__name__)


def hash_mrn(mrn: str) -> str:
    """SHA-256 hash of MRN for safe storage. Never store plain MRN in billing tables."""
    return hashlib.sha256(str(mrn).encode()).hexdigest()


class BillingRulesEngine:
    """
    Evaluates all seven billing rule categories for a patient visit and
    returns a list of BillingOpportunity objects (not yet saved to DB).
    The caller is responsible for committing or discarding them.
    """

    def __init__(self, db, cms_pfs_service=None):
        """
        Parameters
        ----------
        db : SQLAlchemy db instance
        cms_pfs_service : CMSPhysicianFeeScheduleService or None
            If provided, used for live payment rate lookups.
            If None, falls back to hardcoded estimates from api_config.py.
        """
        self.db = db
        self._cms = cms_pfs_service

    def evaluate_patient(self, patient_data: dict) -> list:
        """
        Run all billing rules for a single patient/visit combination.

        Parameters
        ----------
        patient_data : dict
            Must contain:
                mrn (str) — plain MRN (will be hashed immediately, never stored)
                user_id (int) — provider user ID
                visit_date (date) — the scheduled or actual visit date
                visit_type (str) — "office_visit", "awv", "tcm", etc.
                diagnoses (list) — list of dicts: {icd10_code, diagnosis_name, status}
                medications (list) — list of dicts: {drug_name, rxcui, status}
                insurer_type (str) — "medicare", "medicaid", "commercial", "unknown"
                awv_history (dict) — {last_awv_date, awv_code_history, medicare_start_date}
                ccm_minutes_this_month (int) — accumulated non-F2F minutes this month
                face_to_face_minutes (int) — F2F timer for this visit
                prior_encounters_count (int) — count of prior encounters in NP Companion
                discharge_date (date or None) — if TCM candidate, date of discharge
                behavioral_dx_minutes (int) — minutes of BHI care management this month
                rpm_enrolled (bool) — whether patient is enrolled in RPM program

        Returns
        -------
        list of BillingOpportunity objects (unsaved, ready for db.session.add())
        """
        opportunities = []
        mrn = patient_data.get("mrn") or ""
        mrn_hash = hash_mrn(mrn)
        user_id = patient_data.get("user_id")
        visit_date = patient_data.get("visit_date") or date.today()
        insurer = patient_data.get("insurer_type") or "unknown"

        # Run each rule category
        opp = self._check_ccm(patient_data, mrn_hash, user_id, visit_date, insurer)
        if opp:
            opportunities.append(opp)

        opp = self._check_awv(patient_data, mrn_hash, user_id, visit_date, insurer)
        if opp:
            opportunities.append(opp)

        opp = self._check_g2211(patient_data, mrn_hash, user_id, visit_date, insurer)
        if opp:
            opportunities.append(opp)

        opp = self._check_tcm(patient_data, mrn_hash, user_id, visit_date, insurer)
        if opp:
            opportunities.append(opp)

        opp = self._check_prolonged_service(patient_data, mrn_hash, user_id, visit_date, insurer)
        if opp:
            opportunities.append(opp)

        opp = self._check_bhi(patient_data, mrn_hash, user_id, visit_date, insurer)
        if opp:
            opportunities.append(opp)

        opp = self._check_rpm(patient_data, mrn_hash, user_id, visit_date, insurer)
        if opp:
            opportunities.append(opp)

        return opportunities

    # -----------------------------------------------------------------------
    # Rule Category 1 — Chronic Care Management (CCM)
    # -----------------------------------------------------------------------

    def _check_ccm(self, pd, mrn_hash, user_id, visit_date, insurer) -> object:
        """
        CCM eligibility: patient has 2+ chronic conditions from the CMS list.
        Monthly billing based on accumulated non-face-to-face minutes.
        """
        diagnoses = pd.get("diagnoses") or []
        active_chronic = _count_chronic_conditions(diagnoses)

        if active_chronic < 2:
            return None

        minutes = pd.get("ccm_minutes_this_month") or 0

        # Determine which CCM code applies based on accumulated minutes
        if minutes >= 60:
            primary_code = "99487"  # Complex CCM first 60 min
            codes = ["99487"]
            if minutes >= 90:
                codes.append("99489")  # Complex CCM add-on 30 min
            est_revenue = self._get_rate("99487") + (self._get_rate("99489") if minutes >= 90 else 0)
        elif minutes >= 40:
            primary_code = "99490"
            codes = ["99490", "99439"]
            est_revenue = self._get_rate("99490") + self._get_rate("99439")
        elif minutes >= 20:
            primary_code = "99490"
            codes = ["99490"]
            est_revenue = self._get_rate("99490")
        else:
            # Not yet at minimum threshold but patient is eligible
            # Flag as future opportunity
            primary_code = "99490"
            codes = ["99490"]
            est_revenue = self._get_rate("99490")

        # Build eligibility description
        chronic_conditions = _get_chronic_condition_names(diagnoses)
        eligibility = (
            f"Patient has {active_chronic} chronic conditions: "
            f"{', '.join(chronic_conditions[:3])}"
            + (" and more" if active_chronic > 3 else "")
        )
        if minutes > 0:
            eligibility += f". Accrued {minutes} non-F2F minutes this month."

        doc_required = (
            "Comprehensive care plan in chart. "
            "Patient consent on file. "
            "Document all time spent on care coordination. "
            "Provide copy of care plan to patient."
        )

        insurer_caveat = None
        if insurer == "medicaid":
            insurer_caveat = "Verify CCM coverage and requirements with Virginia Medicaid/managed care plan."
        elif insurer == "commercial":
            insurer_caveat = "Verify CCM coverage with commercial payer — requirements vary."

        return self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=user_id,
            visit_date=visit_date,
            opportunity_type="CCM",
            codes=codes,
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=doc_required,
            confidence_level="HIGH" if active_chronic >= 3 else "MEDIUM",
            insurer_caveat=insurer_caveat,
            insurer_type=insurer,
        )

    # -----------------------------------------------------------------------
    # Rule Category 2 — Annual Wellness Visit (AWV) + 2025 Add-On Stack
    # -----------------------------------------------------------------------

    def _check_awv(self, pd, mrn_hash, user_id, visit_date, insurer) -> object:
        """
        AWV sequence: G0402 (Welcome to Medicare), G0438 (initial AWV), G0439 (subsequent).
        Includes 2025-approved add-on stack: G2211, G0444, G0442, G0443, 99497, G0136.
        """
        if insurer not in ("medicare", "unknown"):
            # AWV codes are Medicare-specific; surface as informational for others
            if insurer != "commercial":
                return None

        awv_history = pd.get("awv_history") or {}
        last_awv_date = awv_history.get("last_awv_date")
        medicare_start_date = awv_history.get("medicare_start_date")
        visit_type = pd.get("visit_type") or ""

        # Determine which AWV code applies
        awv_code = None
        awv_reason = ""

        if not last_awv_date:
            if medicare_start_date and _months_since(medicare_start_date) <= 12:
                awv_code = "G0402"
                awv_reason = "No prior AWV — within 12 months of Medicare Part B enrollment"
            else:
                awv_code = "G0438"
                awv_reason = "No prior AWV documented in chart"
        elif _months_since(last_awv_date) >= 12:
            awv_code = "G0439"
            awv_reason = f"Last AWV: {last_awv_date} — 12+ months ago"
        else:
            return None  # Not yet eligible

        # Build the add-on code stack
        codes = [awv_code]
        est_revenue = self._get_rate(awv_code)

        diagnoses = pd.get("diagnoses") or []
        has_complex_condition = _count_chronic_conditions(diagnoses) >= 1

        # G2211: complexity add-on (as of 2025, billable with AWV)
        if has_complex_condition:
            codes.append("G2211")
            est_revenue += self._get_rate("G2211")

        # G0444: annual depression screening (subsequent AWV G0439 only — NOT with G0438)
        if awv_code == "G0439":
            codes.append("G0444")
            est_revenue += self._get_rate("G0444")

        # 99497: Advance Care Planning (billable with AWV, co-pay waived with -33)
        codes.append("99497")
        est_revenue += self._get_rate("99497")

        # G0136: SDOH Risk Assessment (new 2025)
        codes.append("G0136")
        est_revenue += self._get_rate("G0136")

        # G0442/G0443: alcohol screening pair (must bill together or not at all)
        # Include as optional pair — provider decides if applicable
        alcohol_codes_note = "G0442+G0443 (alcohol screening pair) also available if clinically applicable."

        doc_required = (
            f"Document {awv_code} AWV components per CMS requirements. "
            "If billing G2211: document longitudinal care relationship and serious/complex condition. "
            "If billing 99497: document face-to-face ACP discussion, goals of care, duration. "
            "If billing G0136: document SDOH screening instrument and results. "
            "If billing G0444 (subsequent AWV only): document depression screening instrument and score. "
            + alcohol_codes_note
        )

        insurer_caveat = None
        if insurer == "commercial":
            insurer_caveat = (
                "AWV codes are Medicare-specific. "
                "For commercial payers use 99381-99397 preventive E&M codes instead."
            )

        return self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=user_id,
            visit_date=visit_date,
            opportunity_type="AWV",
            codes=codes,
            est_revenue=est_revenue,
            eligibility_basis=awv_reason,
            documentation_required=doc_required,
            confidence_level="HIGH",
            insurer_caveat=insurer_caveat,
            insurer_type=insurer,
        )

    # -----------------------------------------------------------------------
    # Rule Category 3 — G2211 Complexity Add-On
    # -----------------------------------------------------------------------

    def _check_g2211(self, pd, mrn_hash, user_id, visit_date, insurer) -> object:
        """
        G2211 is appropriate for established Medicare patients with serious/complex
        conditions where the provider serves as the focal point of longitudinal care.
        Approximately $16 national average.

        Note: G2211 is NOT checked here if AWV was already found (AWV rule includes it).
        """
        # Only for established patients (prior encounter exists)
        if (pd.get("prior_encounters_count") or 0) < 1:
            return None

        # Only for Medicare or similar (commercial plans may not cover G2211)
        if insurer == "medicaid":
            return None

        diagnoses = pd.get("diagnoses") or []
        chronic_count = _count_chronic_conditions(diagnoses)

        if chronic_count < 1:
            return None

        # Don't duplicate with AWV — AWV rule already includes G2211
        visit_type = pd.get("visit_type") or ""
        if "awv" in visit_type.lower() or "wellness" in visit_type.lower():
            return None

        chronic_names = _get_chronic_condition_names(diagnoses)
        eligibility = (
            f"Established patient with {chronic_count} chronic condition(s): "
            f"{', '.join(chronic_names[:2])}. "
            "Provider serves as longitudinal care focal point."
        )

        est_revenue = self._get_rate("G2211")

        insurer_caveat = None
        if insurer == "commercial":
            insurer_caveat = "G2211 add-on may not be covered by all commercial plans — verify with payer."

        return self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=user_id,
            visit_date=visit_date,
            opportunity_type="G2211",
            codes=["G2211"],
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=(
                "In Assessment/Plan: document longitudinal care relationship. "
                "Note that you are the patient's primary focal point for serious/complex condition management."
            ),
            confidence_level="HIGH" if chronic_count >= 2 else "MEDIUM",
            insurer_caveat=insurer_caveat,
            insurer_type=insurer,
        )

    # -----------------------------------------------------------------------
    # Rule Category 4 — Transitional Care Management (TCM)
    # -----------------------------------------------------------------------

    def _check_tcm(self, pd, mrn_hash, user_id, visit_date, insurer) -> object:
        """
        TCM: billing for care coordination within 30 days of hospital discharge.
        Hard deadline: initial contact must be within 2 business days of discharge.
        """
        discharge_date = pd.get("discharge_date")
        if not discharge_date:
            return None

        if isinstance(discharge_date, str):
            try:
                discharge_date = datetime.strptime(discharge_date[:10], "%Y-%m-%d").date()
            except ValueError:
                return None

        today = date.today()
        days_since_discharge = (today - discharge_date).days

        # TCM window is 30 days from discharge
        if days_since_discharge > 30:
            return None

        # Calculate 2 business day deadline for initial contact
        contact_deadline = _add_business_days(discharge_date, 2)
        days_until_deadline = (contact_deadline - today).days

        # Determine which TCM code to suggest
        # 99496 (high complexity) vs 99495 (moderate complexity)
        # Use 99496 if discharge was recent and F2F can happen within 7 days
        days_available_for_f2f = (discharge_date + timedelta(days=7)) - today
        code = "99496" if days_available_for_f2f.days >= 0 else "99495"
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

        return self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=user_id,
            visit_date=visit_date,
            opportunity_type="TCM",
            codes=[code],
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=doc_required,
            confidence_level=confidence,
            insurer_caveat=None,
            insurer_type=insurer,
        )

    # -----------------------------------------------------------------------
    # Rule Category 5 — Prolonged Service (99417)
    # -----------------------------------------------------------------------

    def _check_prolonged_service(self, pd, mrn_hash, user_id, visit_date, insurer) -> object:
        """
        99417: each 15-minute increment beyond the maximum time for 99214 or 99215.
        Thresholds per 2023 AMA guidelines:
        - 99214 max: 39 min → 99417 at 40+ min
        - 99215 max: 54 min → 99417 at 55+ min
        """
        f2f_minutes = pd.get("face_to_face_minutes") or 0
        if f2f_minutes <= 0:
            return None

        # Check against thresholds
        eligible_base = None
        for base_code, threshold in PROLONGED_SERVICE_THRESHOLDS.items():
            if f2f_minutes >= threshold:
                eligible_base = base_code

        if not eligible_base:
            return None

        threshold = PROLONGED_SERVICE_THRESHOLDS[eligible_base]
        extra_minutes = f2f_minutes - (threshold - 15)  # Minutes beyond base max
        units = max(1, extra_minutes // 15)
        est_revenue = self._get_rate("99417") * units

        eligibility = (
            f"Visit time {f2f_minutes} minutes. "
            f"Exceeds {eligible_base} maximum by {f2f_minutes - (threshold - 15)} minutes. "
            f"Eligible for {units} unit(s) of 99417."
        )

        return self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=user_id,
            visit_date=visit_date,
            opportunity_type="99417",
            codes=["99417"],
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=(
                f"Document total visit time of {f2f_minutes} minutes. "
                f"Note that time exceeded maximum for {eligible_base}. "
                f"Bill 99417 × {units} in addition to the primary E&M code."
            ),
            confidence_level="HIGH",
            insurer_caveat=None,
            insurer_type=insurer,
        )

    # -----------------------------------------------------------------------
    # Rule Category 6 — Behavioral Health Integration (BHI)
    # -----------------------------------------------------------------------

    def _check_bhi(self, pd, mrn_hash, user_id, visit_date, insurer) -> object:
        """
        BHI: monthly billing for integrating behavioral health into primary care.
        Requires behavioral health diagnosis and 20+ minutes of care management.
        """
        diagnoses = pd.get("diagnoses") or []
        bhi_dx = [
            d for d in diagnoses
            if any(
                (d.get("icd10_code") or "").startswith(prefix)
                for prefix in BHI_CONDITION_PREFIXES
            )
            and (d.get("status") or "").lower() != "resolved"
        ]

        if not bhi_dx:
            return None

        bhi_minutes = pd.get("behavioral_dx_minutes") or 0
        dx_names = [d.get("diagnosis_name") or d.get("icd10_code") for d in bhi_dx[:2]]

        eligibility = (
            f"Behavioral health diagnosis: {', '.join(dx_names)}. "
            + (f"Accrued {bhi_minutes} BHI care management minutes this month." if bhi_minutes else
               "BHI eligible — track care management time to meet 20-min threshold.")
        )

        est_revenue = self._get_rate("99484") if bhi_minutes >= 20 else 0.0

        return self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=user_id,
            visit_date=visit_date,
            opportunity_type="BHI",
            codes=["99484"],
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=(
                "Document 20+ minutes of behavioral health care management activities per month. "
                "Activities include: monitoring symptoms, coordinating with BH specialists, "
                "patient/caregiver education, medication management, care planning. "
                "Billing staff or clinical staff under supervision may provide services."
            ),
            confidence_level="HIGH" if bhi_minutes >= 20 else "MEDIUM",
            insurer_caveat=None,
            insurer_type=insurer,
        )

    # -----------------------------------------------------------------------
    # Rule Category 7 — Remote Patient Monitoring (RPM)
    # -----------------------------------------------------------------------

    def _check_rpm(self, pd, mrn_hash, user_id, visit_date, insurer) -> object:
        """
        RPM: billing for monitoring physiologic data from devices between visits.
        Flagged as a program-level opportunity — requires practice infrastructure.
        """
        diagnoses = pd.get("diagnoses") or []
        rpm_eligible_dx = [
            d for d in diagnoses
            if any(
                (d.get("icd10_code") or "").startswith(prefix)
                for prefix in RPM_CONDITION_PREFIXES
            )
        ]

        if not rpm_eligible_dx:
            return None

        rpm_enrolled = pd.get("rpm_enrolled") or False
        dx_names = [d.get("diagnosis_name") or d.get("icd10_code") for d in rpm_eligible_dx[:2]]

        if rpm_enrolled:
            codes = ["99457"]
            est_revenue = self._get_rate("99457")
            eligibility = f"RPM enrolled. Conditions: {', '.join(dx_names)}. Bill monthly monitoring."
            confidence = "HIGH"
        else:
            codes = ["99453", "99454", "99457"]
            est_revenue = self._get_rate("99453")
            eligibility = (
                f"RPM-eligible conditions: {', '.join(dx_names)}. "
                "Patient not currently enrolled — program enrollment opportunity."
            )
            confidence = "LOW"

        return self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=user_id,
            visit_date=visit_date,
            opportunity_type="RPM",
            codes=codes,
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=(
                "RPM requires: (1) Physician order for device. "
                "(2) Patient consent and device education (99453 — one time). "
                "(3) Device supplies with 16+ days of data transmission per month (99454). "
                "(4) 20+ minutes of monitoring and management per month (99457). "
                "NOTE: RPM requires practice-level device program infrastructure."
            ),
            confidence_level=confidence,
            insurer_caveat=(
                "RPM coverage varies by payer. Verify benefits before enrollment."
                if insurer in ("commercial", "medicaid") else None
            ),
            insurer_type=insurer,
        )

    # -----------------------------------------------------------------------
    # Helper methods
    # -----------------------------------------------------------------------

    def _get_rate(self, code: str) -> float:
        """
        Get the estimated payment rate for a billing code.
        Tries the CMS PFS service first, falls back to api_config estimates.
        """
        if self._cms:
            info = self._cms.get_code_info(code)
            if info and info.get("non_facility_pricing_amount"):
                return info["non_facility_pricing_amount"]

        # Fallback to hardcoded estimates in api_config.py
        from app.api_config import (
            CCM_CODES, AWV_CODES, AWV_ADDON_CODES, TCM_CODES,
            EM_ADDON_CODES, BHI_CODES, RPM_CODES
        )
        for code_dict in [CCM_CODES, AWV_CODES, AWV_ADDON_CODES, TCM_CODES,
                          EM_ADDON_CODES, BHI_CODES, RPM_CODES]:
            if code in code_dict:
                return code_dict[code].get("rate_est", 0.0)
        return 0.0

    def _make_opportunity(self, *, mrn_hash, user_id, visit_date, opportunity_type,
                          codes, est_revenue, eligibility_basis, documentation_required,
                          confidence_level, insurer_caveat, insurer_type) -> object:
        """
        Build a BillingOpportunity ORM object.
        """
        from models.billing import BillingOpportunity
        return BillingOpportunity(
            patient_mrn_hash=mrn_hash,
            user_id=user_id,
            visit_date=visit_date,
            opportunity_type=opportunity_type,
            applicable_codes=",".join(codes),
            estimated_revenue=round(est_revenue, 2),
            eligibility_basis=eligibility_basis,
            documentation_required=documentation_required,
            confidence_level=confidence_level,
            insurer_caveat=insurer_caveat,
            insurer_type=insurer_type,
            status="pending",
        )


# -----------------------------------------------------------------------
# Module-level helper functions
# -----------------------------------------------------------------------

def _count_chronic_conditions(diagnoses: list) -> int:
    """
    Count how many active chronic conditions from the CCM eligibility list
    are present in the patient's diagnosis list.
    """
    count = 0
    seen_prefixes = set()  # Avoid counting the same condition category twice
    for dx in diagnoses:
        code = (dx.get("icd10_code") or "").upper()
        status = (dx.get("status") or "").lower()
        if status == "resolved":
            continue
        for prefix in CCM_CHRONIC_CONDITION_PREFIXES:
            if code.startswith(prefix) and prefix not in seen_prefixes:
                count += 1
                seen_prefixes.add(prefix)
                break
    return count


def _get_chronic_condition_names(diagnoses: list) -> list:
    """Return names of chronic conditions for the eligibility description."""
    names = []
    seen_prefixes = set()
    for dx in diagnoses:
        code = (dx.get("icd10_code") or "").upper()
        status = (dx.get("status") or "").lower()
        if status == "resolved":
            continue
        for prefix in CCM_CHRONIC_CONDITION_PREFIXES:
            if code.startswith(prefix) and prefix not in seen_prefixes:
                name = dx.get("diagnosis_name") or code
                names.append(name)
                seen_prefixes.add(prefix)
                break
    return names


def _months_since(date_value) -> int:
    """
    Calculate whole months between a past date and today.
    Accepts date object, datetime object, or YYYY-MM-DD string.
    """
    if not date_value:
        return 0
    if isinstance(date_value, str):
        try:
            date_value = datetime.strptime(date_value[:10], "%Y-%m-%d").date()
        except ValueError:
            return 0
    if isinstance(date_value, datetime):
        date_value = date_value.date()
    today = date.today()
    return (today.year - date_value.year) * 12 + (today.month - date_value.month)


def _add_business_days(start_date: date, days: int) -> date:
    """
    Add N business days to a date (skipping weekends only — no holidays).
    Used for TCM 2-business-day contact window calculation.
    """
    current = start_date
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # 0=Monday, 4=Friday
            added += 1
    return current

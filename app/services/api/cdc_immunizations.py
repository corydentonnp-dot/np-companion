"""
CareCompanion — CDC Immunization Schedule Service
File: app/services/api/cdc_immunizations.py

CDC CVX (Clinical Vaccine administered) codes are part of the RxNorm dataset.
The CDC adult immunization schedule is used to identify immunization gaps
from the Clinical Summary XML immunization history.

Access via: RxNorm API (CVX codes), supplemented by locally maintained
CDC adult schedule data.

Dependencies:
- app/services/api/rxnorm.py (RxNormService for CVX lookup)
- app/api_config.py (CDC_IMMUNIZATION_CACHE_TTL_DAYS)

CareCompanion features that rely on this module:
- Care Gap Tracker (F15) — immunization gap detection alongside USPSTF gaps
- Patient Chart View — immunization status per CDC adult schedule
- Morning Briefing (F22) — immunization gaps for scheduled patients
"""

import logging
from datetime import datetime, timezone
from app.api_config import CDC_IMMUNIZATION_CACHE_TTL_DAYS
from models.api_cache import CdcImmunizationCache

logger = logging.getLogger(__name__)

# CDC Adult Immunization Schedule — hardcoded from CDC 2025 recommendations.
# Each entry defines: vaccine name, CVX code, recommended age range,
# and whether it requires risk factor evaluation.
# Source: https://www.cdc.gov/vaccines/schedules/hcp/imz/adult.html
CDC_ADULT_SCHEDULE = [
    {
        "vaccine": "Influenza (flu)",
        "cvx": "141",
        "min_age": 19,
        "max_age": 999,
        "frequency": "annual",
        "risk_factors": None,
        "notes": "Recommended annually for all adults",
    },
    {
        "vaccine": "COVID-19",
        "cvx": "500",
        "min_age": 19,
        "max_age": 999,
        "frequency": "annual",
        "risk_factors": None,
        "notes": "Updated COVID-19 vaccine recommended annually",
    },
    {
        "vaccine": "Tdap / Td (tetanus/diphtheria/pertussis)",
        "cvx": "115",
        "min_age": 19,
        "max_age": 999,
        "frequency": "10-year",
        "risk_factors": None,
        "notes": "Tdap once, then Td every 10 years",
    },
    {
        "vaccine": "Pneumococcal PCV21 (Prevnar 21)",
        "cvx": "216",
        "min_age": 65,
        "max_age": 999,
        "frequency": "once",
        "risk_factors": ["chronic_lung", "chronic_heart", "diabetes", "immunocompromised"],
        "notes": "Age 65+ or risk-based. Supersedes PCV15/PPSV23 for most adults.",
    },
    {
        "vaccine": "Hepatitis B",
        "cvx": "45",
        "min_age": 19,
        "max_age": 59,
        "frequency": "series",
        "risk_factors": None,
        "notes": "3-dose series. Adults 19-59 if not previously vaccinated.",
    },
    {
        "vaccine": "Shingrix (Zoster recombinant)",
        "cvx": "187",
        "min_age": 50,
        "max_age": 999,
        "frequency": "2-dose-series",
        "risk_factors": None,
        "notes": "2-dose series (0 and 2-6 months). Age 50+. Highest priority.",
    },
    {
        "vaccine": "RSV (ABRYSVO / mRESVIA)",
        "cvx": "300",
        "min_age": 60,
        "max_age": 999,
        "frequency": "once",
        "risk_factors": None,
        "notes": "Single dose for adults 60+ (ACIP 2024 recommendation).",
    },
    {
        "vaccine": "Hepatitis A",
        "cvx": "83",
        "min_age": 19,
        "max_age": 999,
        "frequency": "series",
        "risk_factors": ["liver_disease", "travel_risk", "MSM"],
        "notes": "Risk-based. 2-dose series.",
    },
    {
        "vaccine": "MMR (measles/mumps/rubella)",
        "cvx": "03",
        "min_age": 19,
        "max_age": 999,
        "frequency": "1-2-doses",
        "risk_factors": None,
        "notes": "1-2 doses if not previously vaccinated or documented immunity.",
    },
]


class CDCImmunizationsService:
    """
    Evaluates immunization gaps from patient history against the CDC adult schedule.

    Phase 17.2: Supplemented with VSAC value sets when available. The hardcoded
    CDC_ADULT_SCHEDULE is the offline fallback (Pattern C architecture).
    When VSAC is reachable, additional vaccine recommendations beyond the
    hardcoded 10 are included in gap evaluation.
    """

    def __init__(self, db=None):
        self._db = db
        self._vsac_vaccines = None  # Lazy-loaded from VSAC

    def _load_vsac_vaccines(self) -> list:
        """
        Attempt to load additional vaccines from VSAC value sets.
        Returns a list of CVX codes from VSAC, or empty list if unavailable.
        """
        if self._vsac_vaccines is not None:
            return self._vsac_vaccines
        self._vsac_vaccines = []
        if not self._db:
            return self._vsac_vaccines
        try:
            from app.services.api.umls import UMLSService
            from app.api_config import UMLS_API_KEY
            if not UMLS_API_KEY:
                return self._vsac_vaccines
            svc = UMLSService(self._db, api_key=UMLS_API_KEY)
            vsac_results = svc.get_immunization_value_set()
            if vsac_results:
                self._vsac_vaccines = vsac_results
                logger.info("VSAC immunization supplement: %d vaccines loaded", len(vsac_results))
        except Exception as e:
            logger.debug("VSAC immunization load failed: %s", e)
        return self._vsac_vaccines

    def evaluate_gaps(self, patient_age: int, patient_sex: str,
                      patient_diagnoses: list, immunization_history: list) -> list:
        """
        Identify immunization gaps for a patient.

        Parameters
        ----------
        patient_age : int
            Patient age in years (from PatientRecord.dob)
        patient_sex : str
            "M" or "F"
        patient_diagnoses : list of dicts
            Each dict has: icd10_code (str), diagnosis_name (str), status (str)
            Used to evaluate risk-factor-based vaccine recommendations.
        immunization_history : list of dicts
            Each dict has: vaccine_name (str), cvx_code (str), date_given (str)
            From the Immunizations section of the Clinical Summary XML.

        Returns
        -------
        list of dicts, each representing one immunization gap:
            vaccine (str) — vaccine name
            cvx (str) — CVX code
            reason (str) — why this is flagged (age, risk factor, overdue)
            priority (str) — "high", "medium", or "low"
            notes (str) — clinical guidance
        """
        gaps = []
        today = datetime.now(timezone.utc).date()

        # Build a set of CVX codes already in the patient's history
        received_cvx = {
            h.get("cvx_code") or ""
            for h in immunization_history
            if h.get("cvx_code")
        }

        # Build risk factor flags from diagnoses
        risk_flags = _extract_risk_flags(patient_diagnoses)

        for vaccine in CDC_ADULT_SCHEDULE:
            min_age = vaccine.get("min_age", 0)
            max_age = vaccine.get("max_age", 999)
            cvx = vaccine.get("cvx")
            required_risks = vaccine.get("risk_factors")

            # Check age eligibility
            if not (min_age <= patient_age <= max_age):
                continue

            # Check risk factor requirements (if any)
            if required_risks:
                # Patient must have at least one of the listed risk factors
                has_risk = any(r in risk_flags for r in required_risks)
                if not has_risk:
                    continue

            # Check if already received
            if cvx in received_cvx:
                # For annual vaccines, check if it was given within the past year
                if vaccine.get("frequency") == "annual":
                    recent = _was_given_within_months(
                        immunization_history, cvx, months=14  # Allow 2-month grace
                    )
                    if recent:
                        continue  # Up to date
                    # Fall through — annual vaccine is overdue
                else:
                    continue  # Non-annual vaccine — series complete

            # This vaccine has a gap
            gaps.append({
                "vaccine": vaccine["vaccine"],
                "cvx": cvx,
                "reason": _build_reason(vaccine, risk_flags, patient_age),
                "priority": _get_priority(vaccine, patient_age),
                "notes": vaccine.get("notes", ""),
            })

        # --- Phase 17.2: Supplement with VSAC vaccines ---
        # VSAC may include vaccines not in the hardcoded schedule
        hardcoded_cvx = {v.get("cvx") for v in CDC_ADULT_SCHEDULE}
        vsac_vaccines = self._load_vsac_vaccines()
        for vac in vsac_vaccines:
            cvx = vac.get("cvx_code", "")
            name = vac.get("vaccine_name", "")
            if not cvx or cvx in hardcoded_cvx:
                continue  # Already covered by hardcoded schedule
            if cvx in received_cvx:
                continue  # Already received
            # VSAC vaccines without detailed age/risk data — flag as low priority
            gaps.append({
                "vaccine": name,
                "cvx": cvx,
                "reason": f"VSAC-recommended vaccine — verify applicability for age {patient_age}",
                "priority": "low",
                "notes": "Source: VSAC value set. Review clinical applicability.",
                "source": "vsac",
            })

        return gaps

    @staticmethod
    def populate_structured_cache(db):
        """Seed CdcImmunizationCache from the hardcoded CDC schedule."""
        try:
            for v in CDC_ADULT_SCHEDULE:
                cvx = v.get('cvx', '')
                existing = CdcImmunizationCache.query.filter_by(vaccine_code=cvx).first()
                if not existing:
                    db.session.add(CdcImmunizationCache(
                        vaccine_code=cvx,
                        vaccine_name=v.get('vaccine', ''),
                        schedule_description=v.get('notes', ''),
                        min_age=str(v.get('min_age', '')),
                        max_age=str(v.get('max_age', '')),
                    ))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.debug(f'CdcImmunizationCache populate error: {e}')


def _extract_risk_flags(diagnoses: list) -> set:
    """
    Map patient ICD-10 diagnoses to risk factor categories for vaccine eligibility.
    """
    flags = set()
    for dx in diagnoses:
        code = (dx.get("icd10_code") or "").upper()
        if code.startswith(("J44", "J45")):  # COPD, Asthma
            flags.add("chronic_lung")
        if code.startswith(("I50", "I25", "I48")):  # Heart failure, CAD, AFib
            flags.add("chronic_heart")
        if code.startswith(("E10", "E11")):  # Diabetes
            flags.add("diabetes")
        if code.startswith(("K70", "K71", "K72", "K73", "K74", "B18", "B19")):  # Liver
            flags.add("liver_disease")
        if code.startswith("Z87.891"):  # Tobacco use history
            flags.add("tobacco")
    return flags


def _was_given_within_months(history: list, cvx: str, months: int) -> bool:
    """Check if a CVX vaccine was given within the past N months."""
    from datetime import date
    today = date.today()
    for h in history:
        if h.get("cvx_code") != cvx:
            continue
        date_str = h.get("date_given") or ""
        if not date_str:
            continue
        try:
            given = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
            months_ago = (today.year - given.year) * 12 + (today.month - given.month)
            if months_ago <= months:
                return True
        except (ValueError, AttributeError):
            pass
    return False


def _build_reason(vaccine: dict, risk_flags: set, age: int) -> str:
    required_risks = vaccine.get("risk_factors")
    if required_risks:
        matched = [r for r in required_risks if r in risk_flags]
        return f"Risk-based: {', '.join(matched)} — age {age}"
    return f"Recommended for age {age}+"


def _get_priority(vaccine: dict, age: int) -> str:
    """Assign a priority level to the gap based on the vaccine and patient age."""
    high_priority = ["Influenza", "Pneumococcal", "COVID-19", "Shingrix"]
    for name in high_priority:
        if name in vaccine.get("vaccine", ""):
            return "high"
    return "medium"

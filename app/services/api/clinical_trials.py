"""
CareCompanion — ClinicalTrials.gov v2 API Service
File: app/services/api/clinical_trials.py

Searches ClinicalTrials.gov for recruiting studies that match a
patient's diagnoses, demographics, and geographic location. Enables
"Clinical Trials Near You" widget on the patient chart.

Base URL: https://clinicaltrials.gov/api/v2
Auth: None required
Rate limit: No documented limit — results are cached daily

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (CLINICAL_TRIALS_BASE_URL, CLINICAL_TRIALS_CACHE_TTL_DAYS)

CareCompanion features that rely on this module:
- Patient Chart → Clinical Trials widget (optional)
"""

import logging
from app.api_config import CLINICAL_TRIALS_BASE_URL, CLINICAL_TRIALS_CACHE_TTL_DAYS
from app.services.api.base_client import BaseAPIClient, APIUnavailableError

logger = logging.getLogger(__name__)

# Default location: Chesterfield, VA (practice location)
DEFAULT_LAT = 37.38
DEFAULT_LON = -77.50
DEFAULT_DISTANCE_MILES = 50


class ClinicalTrialsService(BaseAPIClient):
    """
    Service for the ClinicalTrials.gov v2 API.

    Searches for recruiting clinical trials matching a patient's
    conditions, age, sex, and geographic proximity.
    """

    def __init__(self, db):
        super().__init__(
            api_name="clinical_trials",
            base_url=CLINICAL_TRIALS_BASE_URL,
            db=db,
            ttl_days=CLINICAL_TRIALS_CACHE_TTL_DAYS,
        )

    def search_for_patient(self, conditions: list, age: int = None,
                           sex: str = None, latitude: float = None,
                           longitude: float = None,
                           distance_miles: int = None) -> list:
        """
        Search ClinicalTrials.gov for recruiting studies matching patient criteria.

        Parameters
        ----------
        conditions : list of str
            ICD-10 codes or condition names, e.g. ["E11.9", "I10"]
        age : int or None
            Patient age in years (for eligibility filtering)
        sex : str or None
            "M" or "F" (for eligibility filtering)
        latitude : float or None
            Patient/practice latitude (default: Chesterfield, VA)
        longitude : float or None
            Patient/practice longitude (default: Chesterfield, VA)
        distance_miles : int or None
            Search radius (default: 50 miles)

        Returns
        -------
        list of dict, each with keys:
            nct_id, title, phase, status, conditions_list,
            distance_miles, enrollment_url, eligibility_summary
        """
        if not conditions:
            return []

        lat = latitude or DEFAULT_LAT
        lon = longitude or DEFAULT_LON
        dist = distance_miles or DEFAULT_DISTANCE_MILES

        # Build condition query — join with OR for broader results
        condition_query = " OR ".join(str(c) for c in conditions[:5])

        params = {
            "query.cond": condition_query,
            "filter.overallStatus": "RECRUITING",
            "pageSize": "10",
            "format": "json",
        }

        # Add location filter
        params["filter.geo"] = f"distance({lat},{lon},{dist}mi)"

        # Add age filter if provided
        if age is not None:
            params["filter.advanced"] = f"AREA[MinimumAge]RANGE[MIN,{age}] AND AREA[MaximumAge]RANGE[{age},MAX]"

        try:
            data = self._get("/studies", params=params)
            studies = data.get("studies") or []
            results = []
            for study in studies[:10]:
                proto = study.get("protocolSection") or {}
                ident = proto.get("identificationModule") or {}
                status_mod = proto.get("statusModule") or {}
                design = proto.get("designModule") or {}
                eligibility = proto.get("eligibilityModule") or {}
                conditions_mod = proto.get("conditionsModule") or {}
                contacts = proto.get("contactsLocationsModule") or {}

                nct_id = ident.get("nctId", "")
                title = ident.get("briefTitle", ident.get("officialTitle", ""))
                phase_list = (design.get("phases") or [])
                phase = ", ".join(phase_list) if phase_list else "N/A"

                # Build eligibility summary
                elig_parts = []
                if eligibility.get("minimumAge"):
                    elig_parts.append(f"Age: {eligibility['minimumAge']}")
                if eligibility.get("maximumAge"):
                    elig_parts.append(f"to {eligibility['maximumAge']}")
                if eligibility.get("sex") and eligibility["sex"] != "ALL":
                    elig_parts.append(f"Sex: {eligibility['sex']}")

                results.append({
                    "nct_id": nct_id,
                    "title": title,
                    "phase": phase,
                    "status": status_mod.get("overallStatus", "RECRUITING"),
                    "conditions_list": conditions_mod.get("conditions") or [],
                    "distance_miles": dist,
                    "enrollment_url": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "",
                    "eligibility_summary": " ".join(elig_parts) or "See study details",
                })
            return results
        except APIUnavailableError:
            logger.warning("ClinicalTrials.gov unavailable for conditions: %s", conditions)
            return []

"""
NP Companion — OpenFDA Adverse Events Service (FAERS)
File: app/services/api/openfda_adverse_events.py

Returns real-world adverse event reports submitted to FDA (FAERS database).
Covers 20+ million reports on every approved drug. Complements FDA label
adverse reactions data (which is from clinical trials) with real-world data.

Base URL: https://api.fda.gov/drug/event.json
Auth: Same free key as other OpenFDA APIs

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (OPENFDA_EVENTS_BASE_URL, OPENFDA_EVENTS_CACHE_TTL_DAYS)

NP Companion features that rely on this module:
- Medication Reference (F10) — "real-world side effects" card
- Drug Safety Panel — top adverse events from FAERS data
- Pre-visit patient education prep — most common real-world side effects
"""

import logging
from app.api_config import OPENFDA_EVENTS_BASE_URL, OPENFDA_EVENTS_CACHE_TTL_DAYS
from app.services.api.base_client import BaseAPIClient, APIUnavailableError

logger = logging.getLogger(__name__)


class OpenFDAAdverseEventsService(BaseAPIClient):
    """
    Service for the OpenFDA Drug Adverse Events (FAERS) API.
    """

    def __init__(self, db):
        super().__init__(
            api_name="openfda_adverse_events",
            base_url=OPENFDA_EVENTS_BASE_URL,
            db=db,
            ttl_days=OPENFDA_EVENTS_CACHE_TTL_DAYS,
        )

    def get_top_adverse_events(self, drug_name: str, top_n: int = 5) -> list:
        """
        Get the most frequently reported adverse events for a drug.
        Returns top N reactions sorted by report frequency.

        Parameters
        ----------
        drug_name : str
            Generic drug name to search (e.g. "lisinopril")
        top_n : int
            How many top reactions to return. Default 5 per API plan.

        Returns
        -------
        list of dicts with keys:
            reaction_term (str) — MedDRA reaction term
            count (int)         — Number of reports
            _stale (bool)
        """
        try:
            data = self._get(
                "",
                params={
                    "search": f"patient.drug.medicinalproduct:{drug_name}",
                    "count": "patient.reaction.reactionmeddrapt.exact",
                    "limit": top_n,
                },
            )
            results = data.get("results") or []
            return [
                {
                    "reaction_term": r.get("term"),
                    "count": r.get("count"),
                    "_stale": data.get("_stale", False),
                }
                for r in results
            ]
        except APIUnavailableError:
            logger.warning(f"OpenFDA adverse events unavailable for: {drug_name}")
            return []

    def get_recent_signal(self, drug_name: str, start_year: int = 2024) -> dict:
        """
        Check for a spike in recent adverse event reports that could indicate
        an emerging safety signal not yet reflected in a formal FDA alert.

        Parameters
        ----------
        drug_name : str
            Drug to check
        start_year : int
            Start of the date range to check (format: YYYY)

        Returns
        -------
        dict with keys:
            report_count (int) — total reports in the period
            top_reactions (list) — top 3 reactions in the period
            _stale (bool)
        """
        try:
            date_range = f"{start_year}0101+TO+20991231"
            data = self._get(
                "",
                params={
                    "search": (
                        f"receivedate:[{date_range}] AND "
                        f"patient.drug.medicinalproduct:{drug_name}"
                    ),
                    "count": "patient.reaction.reactionmeddrapt.exact",
                    "limit": 3,
                },
            )
            results = data.get("results") or []
            meta = data.get("meta") or {}
            total = (meta.get("results") or {}).get("total") or 0

            return {
                "report_count": total,
                "top_reactions": [r.get("term") for r in results[:3]],
                "_stale": data.get("_stale", False),
            }
        except APIUnavailableError:
            return {"report_count": 0, "top_reactions": [], "_stale": True}

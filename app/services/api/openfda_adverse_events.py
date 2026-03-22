"""
CareCompanion — OpenFDA Adverse Events Service (FAERS)
File: app/services/api/openfda_adverse_events.py

Returns real-world adverse event reports submitted to FDA (FAERS database).
Covers 20+ million reports on every approved drug. Complements FDA label
adverse reactions data (which is from clinical trials) with real-world data.

Base URL: https://api.fda.gov/drug/event.json
Auth: Same free key as other OpenFDA APIs

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (OPENFDA_EVENTS_BASE_URL, OPENFDA_EVENTS_CACHE_TTL_DAYS)

CareCompanion features that rely on this module:
- Medication Reference (F10) — "real-world side effects" card
- Drug Safety Panel — top adverse events from FAERS data
- Pre-visit patient education prep — most common real-world side effects
"""

import logging
from app.api_config import OPENFDA_EVENTS_BASE_URL, OPENFDA_EVENTS_CACHE_TTL_DAYS
from app.services.api.base_client import BaseAPIClient, APIUnavailableError
from models.api_cache import FaersCache

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

    def get_serious_event_stats(self, drug_name: str) -> dict:
        """
        Get seriousness classification and age stratification for a drug.

        Returns
        -------
        dict with keys:
            total_reports (int)
            serious_count (int) — reports classified as serious (seriousnessdeath,
                seriousnesshospitalization, etc.)
            serious_percentage (float) — 0-100
            age_buckets (list of dict) — [{age_group, count}, ...]
            _stale (bool)
        """
        total_reports = 0
        serious_count = 0

        # Get total report count
        try:
            data = self._get(
                "",
                params={
                    "search": f"patient.drug.medicinalproduct:{drug_name}",
                    "count": "serious",
                    "limit": 2,
                },
            )
            results = data.get("results") or []
            for r in results:
                count = r.get("count", 0)
                total_reports += count
                if r.get("term") == 1:  # 1 = serious
                    serious_count = count
        except APIUnavailableError:
            logger.warning("FAERS serious stats unavailable for: %s", drug_name)
            return {"total_reports": 0, "serious_count": 0, "serious_percentage": 0.0,
                    "age_buckets": [], "_stale": True}

        serious_pct = round((serious_count / total_reports * 100), 1) if total_reports > 0 else 0.0

        # Get age stratification
        age_buckets = []
        try:
            age_data = self._get(
                "",
                params={
                    "search": f"patient.drug.medicinalproduct:{drug_name}",
                    "count": "patient.patientonsetage",
                    "limit": 10,
                },
            )
            age_results = age_data.get("results") or []
            # Group into clinical age ranges
            buckets = {"0-17": 0, "18-44": 0, "45-64": 0, "65-74": 0, "75+": 0}
            for r in age_results:
                age = r.get("term", 0)
                count = r.get("count", 0)
                if age < 18:
                    buckets["0-17"] += count
                elif age < 45:
                    buckets["18-44"] += count
                elif age < 65:
                    buckets["45-64"] += count
                elif age < 75:
                    buckets["65-74"] += count
                else:
                    buckets["75+"] += count
            age_buckets = [{"age_group": k, "count": v} for k, v in buckets.items() if v > 0]
            age_buckets.sort(key=lambda x: x["count"], reverse=True)
        except APIUnavailableError:
            pass

        return {
            "total_reports": total_reports,
            "serious_count": serious_count,
            "serious_percentage": serious_pct,
            "age_buckets": age_buckets,
            "_stale": False,
        }

    def _save_to_structured_cache(self, rxcui, total_reports, serious_count, top_reactions, period):
        """Persist aggregated FAERS data to the structured FaersCache table."""
        if not rxcui:
            return
        db = self.cache.db
        try:
            existing = FaersCache.query.filter_by(rxcui=rxcui).first()
            if existing:
                existing.total_reports = total_reports
                existing.serious_count = serious_count
                existing.top_reactions = top_reactions
                existing.report_period = period
            else:
                db.session.add(FaersCache(
                    rxcui=rxcui,
                    total_reports=total_reports,
                    serious_count=serious_count,
                    top_reactions=top_reactions,
                    report_period=period,
                ))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.debug(f'FaersCache save error: {e}')

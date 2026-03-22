"""
CareCompanion — NLM Conditions API Service
File: app/services/api/nlm_conditions.py

Clinical condition search from NLM Clinical Tables. Powers the
Differential Diagnosis Widget (NEW-G) by querying chief complaint
text and returning related clinical conditions with ICD-10 codes.

Base URL: https://clinicaltables.nlm.nih.gov/api/conditions/v3/search
Auth: None required

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (NLM_CONDITIONS_BASE_URL, NLM_CONDITIONS_CACHE_TTL_DAYS)

CareCompanion features that rely on this module:
- Differential Diagnosis Widget (NEW-G) — chief complaint → related conditions
- Care Gap Engine — condition relationship queries
"""

import json
import logging
from app.api_config import NLM_CONDITIONS_BASE_URL, NLM_CONDITIONS_CACHE_TTL_DAYS
from app.services.api.base_client import BaseAPIClient, APIUnavailableError
from models.api_cache import NlmConditionsCache

logger = logging.getLogger(__name__)


class NLMConditionsService(BaseAPIClient):
    """
    Service for the NLM Clinical Tables Conditions API.

    No authentication required. Returns clinical condition names
    matching a search query, suitable for differential diagnosis
    generation from chief complaint text.
    """

    def __init__(self, db):
        super().__init__(
            api_name="nlm_conditions",
            base_url=NLM_CONDITIONS_BASE_URL,
            db=db,
            ttl_days=NLM_CONDITIONS_CACHE_TTL_DAYS,
        )

    def search_conditions(self, query: str, max_results: int = 20) -> list:
        """
        Search for clinical conditions related to a query term.

        Parameters
        ----------
        query : str
            Chief complaint or symptom text, e.g. "chest pain", "headache"
        max_results : int
            Maximum number of results (default 20)

        Returns
        -------
        list of dicts with keys:
            name (str) — condition name
            icd10_codes (list of str) — associated ICD-10 codes (if available)
        """
        if not query or not query.strip():
            return []

        query = query.strip()

        # Check structured cache first
        cached = self._get_from_cache(query)
        if cached is not None:
            return cached

        try:
            data = self._get(
                "",  # Base URL is the search endpoint itself
                params={
                    "terms": query,
                    "maxList": max_results,
                },
            )

            # NLM Clinical Tables response format:
            # [total_count, [matched_terms], [extra_data], [[field1, field2], ...]]
            if not data or not isinstance(data, list) or len(data) < 2:
                return []

            matched_terms = data[1] or []

            conditions = []
            for term in matched_terms:
                if isinstance(term, str) and term.strip():
                    conditions.append({
                        "name": term.strip(),
                        "icd10_codes": [],  # NLM Conditions doesn't return ICD codes inline
                    })

            self._save_to_structured_cache(query, conditions)
            return conditions

        except APIUnavailableError:
            logger.warning(f"NLM Conditions unavailable for query: {query}")
            return []

    def _get_from_cache(self, query: str) -> list:
        """Check NlmConditionsCache for a non-expired entry."""
        from datetime import datetime, timezone, timedelta
        try:
            normalized = query.strip().lower()
            entry = NlmConditionsCache.query.filter_by(search_term=normalized).first()
            if entry and entry.cached_at:
                age = datetime.now(timezone.utc) - entry.cached_at
                if age < timedelta(days=NLM_CONDITIONS_CACHE_TTL_DAYS):
                    return entry.conditions if entry.conditions else []
        except Exception as e:
            logger.debug(f"NLM Conditions cache read error: {e}")
        return None

    def _save_to_structured_cache(self, query: str, conditions: list):
        """Persist condition search results to NlmConditionsCache."""
        db = self.cache.db
        try:
            normalized = query.strip().lower()
            existing = NlmConditionsCache.query.filter_by(search_term=normalized).first()
            if existing:
                existing.conditions = conditions
                existing.result_count = len(conditions)
                from datetime import datetime, timezone
                existing.cached_at = datetime.now(timezone.utc)
            else:
                db.session.add(NlmConditionsCache(
                    search_term=normalized,
                    conditions=conditions,
                    result_count=len(conditions),
                ))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.debug(f"NLM Conditions cache save error: {e}")

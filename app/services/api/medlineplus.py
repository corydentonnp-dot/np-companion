"""
CareCompanion — NLM MedlinePlus Connect Service
File: app/services/api/medlineplus.py

Returns curated, patient-facing health information for ICD-10, SNOMED,
RxNorm, or LOINC codes. Content is at 6th-8th grade reading level in
English and Spanish. Maintained by NLM.

Base URL: https://connect.medlineplus.gov/service
Auth: None required

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (MEDLINEPLUS_BASE_URL, MEDLINEPLUS_CACHE_TTL_DAYS)

CareCompanion features that rely on this module:
- Patient Education Auto-Draft (Feature E) — care gap addressed trigger
- New prescription patient education — drug info for new medications
- Care Gap closure documentation — pre-populated patient message
"""

import logging
from app.api_config import MEDLINEPLUS_BASE_URL, MEDLINEPLUS_CACHE_TTL_DAYS
from app.services.api.base_client import BaseAPIClient, APIUnavailableError
from models.api_cache import MedlinePlusCache

logger = logging.getLogger(__name__)

# NLM code system OIDs (required by MedlinePlus Connect API)
CODE_SYSTEM_ICD10 = "2.16.840.1.113883.6.90"
CODE_SYSTEM_RXNORM = "2.16.840.1.113883.6.88"
CODE_SYSTEM_SNOMED = "2.16.840.1.113883.6.96"
CODE_SYSTEM_LOINC = "2.16.840.1.113883.6.1"


class MedlinePlusService(BaseAPIClient):
    """
    Service for the NLM MedlinePlus Connect API.
    Returns patient education content in English or Spanish.
    """

    def __init__(self, db, language: str = "en"):
        """
        Parameters
        ----------
        language : str
            "en" for English (default) or "es" for Spanish
        """
        super().__init__(
            api_name="medlineplus",
            base_url=MEDLINEPLUS_BASE_URL,
            db=db,
            ttl_days=MEDLINEPLUS_CACHE_TTL_DAYS,
        )
        self._language = language if language in ("en", "es") else "en"

    def get_for_icd10(self, icd10_code: str) -> dict:
        """
        Get patient education content for a diagnosis by ICD-10 code.
        Used when a care gap is addressed (trigger 1 in Feature E).

        Returns
        -------
        dict with keys: title (str), summary (str), url (str),
        language (str), _stale (bool)
        Returns empty dict if no content found.
        """
        try:
            data = self._get(
                "",
                params={
                    "mainSearchCriteria.v.c": icd10_code,
                    "mainSearchCriteria.v.cs": CODE_SYSTEM_ICD10,
                    "knowledgeResponseType": "application/json",
                    "lang": self._language,
                },
            )
            return self._parse_and_cache(icd10_code, data)
        except APIUnavailableError:
            logger.warning(f"MedlinePlus unavailable for ICD-10: {icd10_code}")
            return {}

    def get_for_rxcui(self, rxcui: str) -> dict:
        """
        Get patient education content for a medication by RxCUI.
        Used when a new medication is detected (trigger 2 in Feature E).

        Returns
        -------
        dict with keys: title (str), summary (str), url (str),
        language (str), _stale (bool)
        """
        try:
            data = self._get(
                "",
                params={
                    "mainSearchCriteria.v.c": rxcui,
                    "mainSearchCriteria.v.cs": CODE_SYSTEM_RXNORM,
                    "knowledgeResponseType": "application/json",
                    "lang": self._language,
                },
            )
            return self._parse_and_cache(rxcui, data)
        except APIUnavailableError:
            logger.warning(f"MedlinePlus unavailable for RxCUI: {rxcui}")
            return {}

    def _parse_response(self, data: dict) -> dict:
        """
        Parse the MedlinePlus Connect API response.
        The response is in HL7 InfoButton format, which is nested XML-like JSON.
        """
        if not data:
            return {}

        # Navigate the HL7 InfoButton response structure
        try:
            feed = data.get("feed") or {}
            entries = feed.get("entry") or []

            if not entries:
                return {}

            first_entry = entries[0] if isinstance(entries, list) else entries
            if not isinstance(first_entry, dict):
                return {}

            title = first_entry.get("title", {})
            if isinstance(title, dict):
                title_text = title.get("_value") or ""
            else:
                title_text = str(title)

            summary = first_entry.get("summary", {})
            if isinstance(summary, dict):
                summary_text = summary.get("_value") or ""
            else:
                summary_text = str(summary)

            # Get the URL for "more information" link
            links = first_entry.get("link") or []
            url = ""
            if links and isinstance(links, list):
                url = links[0].get("href") or ""
            elif isinstance(links, dict):
                url = links.get("href") or ""

            return {
                "title": title_text[:200],
                "summary": summary_text[:1000],
                "url": url,
                "language": self._language,
                "_stale": data.get("_stale", False),
            }

        except (KeyError, TypeError, AttributeError) as e:
            logger.warning(f"MedlinePlus parse error: {e}")
            return {}

    def _parse_and_cache(self, topic_id, data):
        """Parse response and persist to structured MedlinePlusCache."""
        result = self._parse_response(data)
        if result and topic_id:
            db = self.cache.db
            try:
                existing = MedlinePlusCache.query.filter_by(topic_id=topic_id[:30]).first()
                if not existing:
                    db.session.add(MedlinePlusCache(
                        topic_id=topic_id[:30],
                        title=result.get('title', ''),
                        url=result.get('url', '')[:500],
                        summary=result.get('summary', ''),
                        language=result.get('language', 'en'),
                    ))
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.debug(f'MedlinePlusCache save error: {e}')
        return result

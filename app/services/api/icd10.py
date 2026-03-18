"""
NP Companion — ICD-10-CM Clinical Tables Search Service
File: app/services/api/icd10.py

Live search of the complete ICD-10-CM dataset from NLM Clinical Tables.
Powers autocomplete in the Coding Suggester (F17), diagnosis lookup in the
Note Reformatter (F31), and care gap evaluation.

Base URL: https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search
Auth: None required

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (ICD10_BASE_URL, ICD10_CACHE_TTL_DAYS)

NP Companion features that rely on this module:
- Coding Suggester (F17) — primary autocomplete search engine
- Specificity reminder (F17b) — parent/child code hierarchy
- Code pairing suggestions (F17c)
- Note Reformatter (F31) — diagnosis classification
- Care Gap Tracker (F15) — trigger evaluation by ICD-10 code
- Billing anomaly detection (F14b)
"""

import logging
from app.api_config import ICD10_BASE_URL, ICD10_CACHE_TTL_DAYS
from app.services.api.base_client import BaseAPIClient, APIUnavailableError

logger = logging.getLogger(__name__)


class ICD10Service(BaseAPIClient):
    """
    Service for the NLM ICD-10-CM Clinical Table Search API.
    """

    def __init__(self, db):
        super().__init__(
            api_name="icd10",
            base_url=ICD10_BASE_URL,
            db=db,
            ttl_days=ICD10_CACHE_TTL_DAYS,
        )

    def search(self, search_term: str, max_results: int = 20) -> list:
        """
        Search ICD-10-CM codes by diagnosis name or code string.
        Powers the Coding Suggester (F17) autocomplete field.

        Parameters
        ----------
        search_term : str
            What the provider is typing, e.g. "hypert", "I10", "diabetes"
        max_results : int
            Maximum number of results to return (default 20)

        Returns
        -------
        list of dicts with keys: code (str), description (str)
        """
        try:
            data = self._get(
                "",  # Base URL is the search endpoint
                params={
                    "sf": "code,name",
                    "terms": search_term,
                    "maxList": max_results,
                },
            )
            # Response format: [total, [codes], [extra], [[code, name], ...]]
            if not data or not isinstance(data, list) or len(data) < 4:
                return []

            code_pairs = data[3] or []
            return [
                {"code": pair[0], "description": pair[1]}
                for pair in code_pairs
                if pair and len(pair) >= 2
            ]
        except (APIUnavailableError, Exception) as e:
            logger.warning(f"ICD-10 search error for '{search_term}': {e}")
            return []

    def lookup_code(self, code: str) -> dict:
        """
        Reverse lookup: given a code, return its description.
        Used when the Clinical Summary XML contains a code without a description.

        Returns
        -------
        dict with keys: code (str), description (str), or empty dict if not found
        """
        results = self.search(code, max_results=5)
        for result in results:
            if result.get("code", "").upper() == code.upper():
                return result
        # If exact match not found, return the first result as best guess
        return results[0] if results else {}

    def get_children(self, parent_code: str) -> list:
        """
        Get child codes for a given ICD-10 code.
        Used by the specificity reminder (F17b) to suggest more specific codes.

        Example: parent_code="E11" returns E11.0, E11.1, E11.2, etc.

        Returns
        -------
        list of dicts with keys: code, description
        """
        # The NLM API does not have an explicit children endpoint.
        # We simulate it by searching for the parent code prefix and filtering
        # to codes that start with the parent code followed by a dot.
        try:
            results = self.search(parent_code, max_results=50)
            children = [
                r for r in results
                if r.get("code", "").startswith(parent_code + ".")
                and r.get("code") != parent_code
            ]
            return children
        except Exception as e:
            logger.warning(f"ICD-10 children error for {parent_code}: {e}")
            return []

    def is_valid_billing_code(self, code: str) -> bool:
        """
        Check if a code is a valid billing code (not a header/category code).
        Header codes like "E11" are not valid for billing — "E11.9" is.
        A code is a valid billing code if it has a decimal point.
        """
        return "." in code

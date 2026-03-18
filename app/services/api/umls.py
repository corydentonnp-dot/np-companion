"""
NP Companion — UMLS Unified Medical Language System Service
File: app/services/api/umls.py

The UMLS is the master crosswalk between all medical terminologies:
ICD-10, SNOMED CT, RxNorm, LOINC, MeSH, CPT, and ~150 others.
Used by the Note Reformatter for diagnosis disambiguation and by the
Coding Suggester for synonym resolution.

Base URL: https://uts.nlm.nih.gov/uts/rest
Auth: Free UMLS account at https://uts.nlm.nih.gov/uts/signup-login
API key: Provided after registration

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (UMLS_BASE_URL, UMLS_CACHE_TTL_DAYS)

NP Companion features that rely on this module:
- Note Reformatter (F31) — diagnosis normalization ("HTN" → ICD-10 I10)
- Coding Suggester (F17) — synonym resolution for search
- Code pairing (F17c) — clinical relationship queries
- ICD-10 specificity (F17b) — hierarchy navigation
"""

import logging
from app.api_config import UMLS_BASE_URL, UMLS_CACHE_TTL_DAYS
from app.services.api.base_client import BaseAPIClient, APIUnavailableError

logger = logging.getLogger(__name__)


class UMLSService(BaseAPIClient):
    """
    Service for the NLM UMLS API.

    Requires a UMLS API key stored in admin settings (umls_api_key).
    All methods gracefully return empty results if no API key is configured.
    """

    def __init__(self, db, api_key: str = None):
        """
        Parameters
        ----------
        api_key : str or None
            UMLS API key from admin settings. If None, service returns empty results.
        """
        super().__init__(
            api_name="umls",
            base_url=UMLS_BASE_URL,
            db=db,
            ttl_days=UMLS_CACHE_TTL_DAYS,
        )
        self._api_key = api_key

    def _require_api_key(self) -> bool:
        """Return True if API key is available, False with a warning if not."""
        if not self._api_key:
            logger.warning("UMLS API key not configured — set umls_api_key in admin settings")
            return False
        return True

    def search(self, term: str) -> list:
        """
        Search UMLS for a medical term and return matching concepts with all
        associated terminology codes.

        Example: search("hypertension") returns CUI C0020538 with
        ICD-10 I10, SNOMED 38341003, MeSH D006973, etc.

        Returns
        -------
        list of dicts, each with keys:
            cui (str) — UMLS Concept Unique Identifier
            name (str) — canonical concept name
            semantic_type (str) — e.g. "Disease or Syndrome"
        """
        if not self._require_api_key():
            return []

        try:
            data = self._get(
                "/search/current",
                params={
                    "string": term,
                    "searchType": "normalizedString",
                    "apiKey": self._api_key,
                    "returnIdType": "concept",
                    "pageSize": 10,
                },
            )
            results = (data.get("result") or {}).get("results") or []
            return [
                {
                    "cui": r.get("ui"),
                    "name": r.get("name"),
                    "semantic_type": r.get("semanticTypes"),
                }
                for r in results
                if r.get("ui") != "NONE"
            ]
        except APIUnavailableError:
            logger.warning(f"UMLS unavailable for term: {term}")
            return []

    def get_icd10_for_concept(self, cui: str) -> list:
        """
        Get ICD-10 codes for a UMLS concept identifier.
        Used by the Note Reformatter to resolve abbreviated or non-standard
        diagnosis terms to their ICD-10 billing codes.

        Returns
        -------
        list of dicts with keys: code (str), description (str), vocabulary (str)
        """
        if not self._require_api_key():
            return []

        try:
            data = self._get(
                f"/content/current/CUI/{cui}/atoms",
                params={
                    "sabs": "ICD10CM",
                    "apiKey": self._api_key,
                    "pageSize": 20,
                },
            )
            atoms = (data.get("result") or [])
            codes = []
            for atom in atoms:
                root_source = atom.get("rootSource") or ""
                if "ICD10" in root_source:
                    codes.append({
                        "code": atom.get("ui"),
                        "description": atom.get("name"),
                        "vocabulary": root_source,
                    })
            return codes
        except APIUnavailableError:
            return []

    def resolve_abbreviation(self, abbreviated_term: str) -> dict:
        """
        Convenience method: resolve a clinical abbreviation to its canonical
        term and ICD-10 code. Used by Note Reformatter.

        Example: "HTN" → {"term": "Hypertension", "icd10_code": "I10"}

        Returns
        -------
        dict with keys: term (str or None), icd10_code (str or None)
        """
        concepts = self.search(abbreviated_term)
        if not concepts:
            return {"term": None, "icd10_code": None}

        # Take the first matching concept
        first = concepts[0]
        cui = first.get("cui")
        term = first.get("name")

        # Get ICD-10 code for this concept
        icd10_results = self.get_icd10_for_concept(cui) if cui else []
        icd10_code = icd10_results[0].get("code") if icd10_results else None

        return {"term": term, "icd10_code": icd10_code}

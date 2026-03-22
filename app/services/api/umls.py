"""
CareCompanion — UMLS Unified Medical Language System Service
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

CareCompanion features that rely on this module:
- Note Reformatter (F31) — diagnosis normalization ("HTN" → ICD-10 I10)
- Coding Suggester (F17) — synonym resolution for search
- Code pairing (F17c) — clinical relationship queries
- ICD-10 specificity (F17b) — hierarchy navigation
"""

import logging
from app.api_config import (
    UMLS_BASE_URL, UMLS_CACHE_TTL_DAYS, SNOMED_SEARCH_SAB,
    VSAC_BASE_URL, VSAC_CACHE_TTL_DAYS,
)
from app.services.api.base_client import BaseAPIClient, APIUnavailableError
from models.api_cache import UmlsCache

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
            concepts = [
                {
                    "cui": r.get("ui"),
                    "name": r.get("name"),
                    "semantic_type": r.get("semanticTypes"),
                }
                for r in results
                if r.get("ui") != "NONE"
            ]
            self._save_to_structured_cache(concepts)
            return concepts
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

    def get_snomed_for_concept(self, cui: str) -> list:
        """
        Get SNOMED CT codes for a UMLS concept identifier.
        Queries UMLS atoms with sabs=SNOMEDCT_US to return SNOMED CT codes.

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
                    "sabs": SNOMED_SEARCH_SAB,
                    "apiKey": self._api_key,
                    "pageSize": 20,
                },
            )
            atoms = (data.get("result") or [])
            codes = []
            for atom in atoms:
                root_source = atom.get("rootSource") or ""
                if "SNOMEDCT" in root_source:
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

    def _save_to_structured_cache(self, concepts):
        """Persist UMLS concepts to the structured UmlsCache table."""
        db = self.cache.db
        try:
            for c in concepts:
                cui = c.get('cui')
                if not cui:
                    continue
                existing = UmlsCache.query.filter_by(cui=cui).first()
                if not existing:
                    st = c.get('semantic_type', '')
                    if isinstance(st, list):
                        st = ', '.join(s.get('name', '') if isinstance(s, dict) else str(s) for s in st)
                    db.session.add(UmlsCache(
                        cui=cui,
                        preferred_name=c.get('name', ''),
                        semantic_type=str(st)[:200],
                    ))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.debug(f'UmlsCache save error: {e}')

    # ------------------------------------------------------------------
    # VSAC — Value Set Authority Center (FHIR R4)
    # ------------------------------------------------------------------

    def get_vsac_value_set(self, oid: str) -> list:
        """
        Retrieve a VSAC value set by OID and return its member codes.

        VSAC value sets contain curated lists of codes (CVX, ICD-10,
        SNOMED, etc.) maintained by clinical expert panels. Used for
        immunization recommendations, quality measures, and more.

        Parameters
        ----------
        oid : str
            The OID of the value set (e.g., "2.16.840.1.113883.3.464.1003.196.12.1001")

        Returns
        -------
        list of dicts with keys: code (str), display (str), system (str)
        """
        if not self._require_api_key():
            return []
        if not oid:
            return []

        try:
            original_base = self.base_url
            self.base_url = VSAC_BASE_URL.rstrip("/")
            try:
                data = self._get(
                    f"/ValueSet/{oid}/$expand",
                    params={"apiKey": self._api_key},
                    ttl_days=VSAC_CACHE_TTL_DAYS,
                )
            finally:
                self.base_url = original_base

            codes = []
            expansion = (data.get("expansion") or {})
            for item in expansion.get("contains") or []:
                codes.append({
                    "code": item.get("code", ""),
                    "display": item.get("display", ""),
                    "system": item.get("system", ""),
                })
            return codes
        except APIUnavailableError:
            logger.warning("VSAC unavailable for OID: %s", oid)
            return []

    def get_immunization_value_set(self) -> list:
        """
        Retrieve the ACIP-recommended adult immunization value set from VSAC.

        Uses the CVX vaccine-administered value set OID to get
        immunization codes beyond the hardcoded CDC schedule.

        Returns
        -------
        list of dicts with keys: cvx_code (str), vaccine_name (str)
        """
        # CVX value set OID for administered vaccines
        CVX_VALUESET_OID = "2.16.840.1.113762.1.4.1010.6"
        codes = self.get_vsac_value_set(CVX_VALUESET_OID)

        vaccines = []
        for item in codes:
            system = item.get("system", "")
            if "cvx" in system.lower() or "2.16.840.1.113883.12.292" in system:
                vaccines.append({
                    "cvx_code": item.get("code", ""),
                    "vaccine_name": item.get("display", ""),
                })
        return vaccines

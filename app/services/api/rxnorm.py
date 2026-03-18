"""
NP Companion — RxNorm API Service
File: app/services/api/rxnorm.py

Normalizes drug names into canonical RxCUI identifiers and retrieves
pharmacological properties. RxNorm is the foundation of the drug
intelligence layer — all other drug-related API calls use RxCUI, not
raw drug strings.

Base URL: https://rxnav.nlm.nih.gov/REST
Auth: None required
Rate limit: ~20 req/sec (soft limit)

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (RXNORM_BASE_URL, RXNORM_CACHE_TTL_DAYS, etc.)

NP Companion features that rely on this module:
- Medication Reference (F10) — all drug lookups
- Note Reformatter (F31) — medication classification
- Drug Interaction Checker — cross-references via RxCUI
- Drug Recall Alert System — RxCUI for OpenFDA recall matching
- PA Generator (F26) — drug class / step therapy language
- Billing Opportunity Engine — CCM medication cross-reference
- Clinical Summary XML import enrichment (agent/clinical_summary_parser.py)
"""

import logging
from app.api_config import RXNORM_BASE_URL, RXNORM_CACHE_TTL_DAYS, RXNORM_NDC_TTL_DAYS
from app.services.api.base_client import BaseAPIClient, APIUnavailableError

logger = logging.getLogger(__name__)


class RxNormService(BaseAPIClient):
    """
    Service for the NIH RxNorm API.

    Primary use: convert any drug name string into a stable RxCUI,
    then retrieve structured pharmacological data using that RxCUI.
    """

    def __init__(self, db):
        super().__init__(
            api_name="rxnorm",
            base_url=RXNORM_BASE_URL,
            db=db,
            ttl_days=RXNORM_CACHE_TTL_DAYS,
        )

    def get_rxcui(self, drug_name: str) -> dict:
        """
        Resolve any drug string to an RxCUI.

        Parameters
        ----------
        drug_name : str
            Any drug string — brand name, generic, abbreviation, or partial name.
            Example: "Lisinopril 10 mg tablet" or "lisinopril" or "zestril"

        Returns
        -------
        dict with keys:
            rxcui (str or None) — The RxCUI if found, else None
            name  (str or None) — The normalized drug name from RxNorm
            _stale (bool)       — True if data came from stale cache
        """
        try:
            data = self._get("/rxcui.json", params={"name": drug_name, "allsrc": 0})
            concepts = (data.get("idGroup") or {}).get("rxnormId") or []
            rxcui = concepts[0] if concepts else None
            name = (data.get("idGroup") or {}).get("name")
            return {"rxcui": rxcui, "name": name, "_stale": data.get("_stale", False)}
        except APIUnavailableError:
            logger.warning(f"RxNorm unavailable for drug: {drug_name}")
            return {"rxcui": None, "name": None, "_stale": True}

    def get_properties(self, rxcui: str) -> dict:
        """
        Get canonical drug properties for a known RxCUI.

        Returns
        -------
        dict with keys: name, synonym, tty (term type), language, suppress,
        umlscui, _stale
        """
        try:
            data = self._get(f"/rxcui/{rxcui}/properties.json")
            props = (data.get("properties") or {})
            return {
                "name": props.get("name"),
                "synonym": props.get("synonym"),
                "tty": props.get("tty"),
                "language": props.get("language"),
                "suppress": props.get("suppress"),
                "umlscui": props.get("umlscui"),
                "_stale": data.get("_stale", False),
            }
        except APIUnavailableError:
            logger.warning(f"RxNorm properties unavailable for RxCUI: {rxcui}")
            return {}

    def get_ingredient(self, rxcui: str) -> dict:
        """
        Get the ingredient-level RxCUI for a given drug RxCUI.
        This strips dose form and strength to get the pure active ingredient.
        Example: "Lisinopril 10 mg tablet" → ingredient RxCUI for "lisinopril"

        Used by interaction and class queries which operate at the ingredient level.
        """
        try:
            data = self._get(f"/rxcui/{rxcui}/related.json", params={"tty": "IN"})
            related = (data.get("relatedGroup") or {})
            concept_group = related.get("conceptGroup") or []
            for group in concept_group:
                if group.get("tty") == "IN":
                    properties = group.get("conceptProperties") or []
                    if properties:
                        first = properties[0]
                        return {
                            "ingredient_rxcui": first.get("rxcui"),
                            "ingredient_name": first.get("name"),
                            "_stale": data.get("_stale", False),
                        }
            return {"ingredient_rxcui": rxcui, "ingredient_name": None, "_stale": False}
        except APIUnavailableError:
            return {"ingredient_rxcui": rxcui, "ingredient_name": None, "_stale": True}

    def get_ndcs(self, rxcui: str) -> dict:
        """
        Get National Drug Codes (NDCs) associated with an RxCUI.
        NDCs are needed for OpenFDA label and recall queries.
        """
        try:
            data = self._get(
                f"/rxcui/{rxcui}/ndcs.json",
                ttl_days=RXNORM_NDC_TTL_DAYS,  # NDCs change more often
            )
            ndcs = (data.get("ndcGroup") or {}).get("ndcList") or {}
            return {
                "ndcs": ndcs.get("ndc") or [],
                "_stale": data.get("_stale", False),
            }
        except APIUnavailableError:
            return {"ndcs": [], "_stale": True}

    def get_spelling_suggestions(self, drug_name: str) -> list:
        """
        Get spelling suggestions when a drug name cannot be resolved.
        Used when OCR produces garbled medication names from the AC export.

        Returns
        -------
        list of str — suggested normalized drug name strings
        """
        try:
            data = self._get(
                "/spellingsuggestions.json",
                params={"name": drug_name},
                ttl_days=7,
            )
            suggestions = (data.get("suggestionGroup") or {}).get("suggestionList") or {}
            return suggestions.get("suggestion") or []
        except APIUnavailableError:
            return []

    def normalize_drug_list(self, drug_names: list) -> list:
        """
        Normalize a list of drug name strings to RxCUI.
        Returns a list of dicts, one per input drug, with rxcui and name resolved.

        This is the bulk import path used by clinical_summary_parser.py when
        processing the medications section of a Clinical Summary XML.
        """
        results = []
        for name in drug_names:
            result = self.get_rxcui(name)
            result["original_name"] = name
            results.append(result)
        return results

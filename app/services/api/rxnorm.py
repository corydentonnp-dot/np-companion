"""
CareCompanion — RxNorm API Service
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

CareCompanion features that rely on this module:
- Medication Reference (F10) — all drug lookups
- Note Reformatter (F31) — medication classification
- Drug Interaction Checker — cross-references via RxCUI
- Drug Recall Alert System — RxCUI for OpenFDA recall matching
- PA Generator (F26) — drug class / step therapy language
- Billing Opportunity Engine — CCM medication cross-reference
- Clinical Summary XML import enrichment (agent/clinical_summary_parser.py)
"""

import logging
from app.api_config import (
    RXNORM_BASE_URL, RXNORM_CACHE_TTL_DAYS, RXNORM_NDC_TTL_DAYS,
    RXTERMS_BASE_URL, RXTERMS_CACHE_TTL_DAYS,
    RXCLASS_BASE_URL, RXCLASS_CACHE_TTL_DAYS,
)
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

    def get_rxterms_info(self, rxcui: str) -> dict:
        """
        Get structured drug terminology from RxTerms for a known RxCUI.

        RxTerms provides standardized drug name + strength + dosage form + route,
        used by Note Generator, Patient Education, and PA Generator.

        Parameters
        ----------
        rxcui : str
            The RxCUI identifier

        Returns
        -------
        dict with keys:
            display_name (str) — Full standardized name (e.g. "Metformin 500 mg oral tablet")
            generic_name (str) — Generic drug name
            brand_name (str) — Brand name if available
            strength (str) — Dosage strength (e.g. "500 mg")
            route (str) — Administration route (e.g. "Oral")
            dose_form (str) — Dosage form (e.g. "Tab")
            _stale (bool)
        """
        if not rxcui:
            return {}
        try:
            # RxTerms uses a different base URL than the core RxNorm API
            # We temporarily override base_url for this call
            original_base = self.base_url
            self.base_url = RXTERMS_BASE_URL.rstrip("/")
            try:
                data = self._get(
                    f"/rxcui/{rxcui}/allinfo.json",
                    ttl_days=RXTERMS_CACHE_TTL_DAYS,
                )
            finally:
                self.base_url = original_base

            info = (data.get("rxtermsProperties") or {})
            return {
                "display_name": info.get("fullName", ""),
                "generic_name": info.get("fullGenericName", ""),
                "brand_name": info.get("brandName", ""),
                "strength": info.get("strength", ""),
                "route": info.get("route", ""),
                "dose_form": info.get("doseForm", ""),
                "_stale": data.get("_stale", False),
            }
        except APIUnavailableError:
            logger.warning("RxTerms unavailable for RxCUI: %s", rxcui)
            return {}

    # ------------------------------------------------------------------
    # RxClass API — therapeutic class lookups
    # ------------------------------------------------------------------

    def get_classes_for_drug(self, drug_name: str) -> list:
        """
        Get therapeutic classes for a drug via the RxClass API.

        Uses the /class/byDrugName endpoint with EPC (Established
        Pharmacologic Class) relation for FDA-recognized therapeutic classes.

        Returns list of dicts: [{class_id, class_name, class_type}, ...]
        """
        if not drug_name:
            return []
        try:
            original_base = self.base_url
            self.base_url = RXCLASS_BASE_URL.rstrip("/")
            try:
                data = self._get(
                    "/class/byDrugName.json",
                    params={
                        "drugName": drug_name,
                        "relaSource": "MEDRT",
                        "rela": "may_treat",
                    },
                    ttl_days=RXCLASS_CACHE_TTL_DAYS,
                )
            finally:
                self.base_url = original_base

            classes = []
            for group in (data.get("rxclassDrugInfoList") or {}).get("rxclassDrugInfo") or []:
                cls_info = group.get("rxclassMinConceptItem") or {}
                class_id = cls_info.get("classId", "")
                class_name = cls_info.get("className", "")
                class_type = cls_info.get("classType", "")
                if class_name and not any(c["class_name"] == class_name for c in classes):
                    classes.append({
                        "class_id": class_id,
                        "class_name": class_name,
                        "class_type": class_type,
                    })
            return classes
        except APIUnavailableError:
            logger.warning("RxClass unavailable for drug: %s", drug_name)
            return []

    def get_drugs_for_class(self, class_id: str) -> list:
        """
        Get drugs belonging to a therapeutic class via RxClass API.

        Uses /class/classMembers endpoint with EPC relation.

        Returns list of dicts: [{rxcui, drug_name}, ...]
        """
        if not class_id:
            return []
        try:
            original_base = self.base_url
            self.base_url = RXCLASS_BASE_URL.rstrip("/")
            try:
                data = self._get(
                    "/classMembers.json",
                    params={
                        "classId": class_id,
                        "relaSource": "MEDRT",
                        "rela": "may_treat",
                    },
                    ttl_days=RXCLASS_CACHE_TTL_DAYS,
                )
            finally:
                self.base_url = original_base

            drugs = []
            for member in (data.get("drugMemberGroup") or {}).get("drugMember") or []:
                concept = member.get("minConcept") or {}
                rxcui = concept.get("rxcui", "")
                name = concept.get("name", "")
                if name:
                    drugs.append({"rxcui": rxcui, "drug_name": name})
            return drugs
        except APIUnavailableError:
            logger.warning("RxClass classMembers unavailable for class: %s", class_id)
            return []

    def get_therapeutic_classes_for_rxcui(self, rxcui: str) -> list:
        """
        Get therapeutic class names for a specific RxCUI.

        Uses /class/byRxcui endpoint with EPC relation. Used by the
        formulary gap engine to determine if a patient's medications
        match expected therapeutic classes for their conditions.

        Returns list of class name strings.
        """
        if not rxcui:
            return []
        try:
            original_base = self.base_url
            self.base_url = RXCLASS_BASE_URL.rstrip("/")
            try:
                data = self._get(
                    "/class/byRxcui.json",
                    params={
                        "rxcui": rxcui,
                        "relaSource": "MEDRT",
                        "rela": "may_treat",
                    },
                    ttl_days=RXCLASS_CACHE_TTL_DAYS,
                )
            finally:
                self.base_url = original_base

            class_names = []
            for group in (data.get("rxclassDrugInfoList") or {}).get("rxclassDrugInfo") or []:
                cls_info = group.get("rxclassMinConceptItem") or {}
                name = cls_info.get("className", "")
                if name and name not in class_names:
                    class_names.append(name)
            return class_names
        except APIUnavailableError:
            logger.warning("RxClass unavailable for RxCUI: %s", rxcui)
            return []

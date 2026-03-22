"""
CareCompanion — RxClass API Service
File: app/services/api/rxclass.py

Maps drugs to therapeutic drug classes across multiple classification systems:
ATC (Anatomical Therapeutic Chemical), EPC (FDA Established Pharmacologic Class),
VA class, and MeSH pharmacological actions.

Base URL: https://rxnav.nlm.nih.gov/REST/rxclass
Auth: None required

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (RXCLASS_BASE_URL, RXCLASS_CACHE_TTL_DAYS)

CareCompanion features that rely on this module:
- Medication Reference (F10) — condition → drug class → drug list
- PA Generator (F26) — step therapy position ("this is a third-line agent")
- Formulary Gap Detection — "patient has [condition] but no [drug class]"
- Pre-visit note prep — Assessment/Plan boilerplate by drug class
- Drug Interaction Checker — class-level interaction warnings
"""

import logging
from app.api_config import RXCLASS_BASE_URL, RXCLASS_CACHE_TTL_DAYS
from app.services.api.base_client import BaseAPIClient, APIUnavailableError
from models.api_cache import RxClassCache

logger = logging.getLogger(__name__)


class RxClassService(BaseAPIClient):
    """
    Service for the NIH RxClass API.

    Maps drugs (via RxCUI) to therapeutic drug classes and vice versa.
    """

    def __init__(self, db):
        super().__init__(
            api_name="rxclass",
            base_url=RXCLASS_BASE_URL,
            db=db,
            ttl_days=RXCLASS_CACHE_TTL_DAYS,
        )

    def get_classes_for_drug(self, rxcui: str) -> list:
        """
        Get all drug class memberships for an RxCUI.

        Returns
        -------
        list of dicts, each with keys:
            class_id   (str) — class identifier
            class_name (str) — human-readable class name
            class_type (str) — classification system (ATC, EPC, VA, MESH)
            source     (str) — data source for this classification
        """
        try:
            data = self._get("/class/byRxcui.json", params={"rxcui": rxcui})
            groups = (data.get("rxclassDrugInfoList") or {}).get("rxclassDrugInfo") or []
            classes = []
            for item in groups:
                rxclass = item.get("rxclassMinConceptItem") or {}
                classes.append({
                    "class_id": rxclass.get("classId"),
                    "class_name": rxclass.get("className"),
                    "class_type": rxclass.get("classType"),
                    "source": item.get("rela"),
                })
            self._save_to_structured_cache(rxcui, classes)
            return classes
        except APIUnavailableError:
            logger.warning(f"RxClass unavailable for RxCUI: {rxcui}")
            return []

    def _save_to_structured_cache(self, rxcui, classes):
        """Persist class mappings to the structured RxClassCache table."""
        db = self.cache.db
        try:
            for c in classes:
                exists = RxClassCache.query.filter_by(
                    rxcui=rxcui, class_id=c.get('class_id', '')
                ).first()
                if not exists:
                    db.session.add(RxClassCache(
                        rxcui=rxcui,
                        class_id=c.get('class_id', ''),
                        class_name=c.get('class_name', ''),
                        class_type=c.get('class_type', ''),
                        source=c.get('source', 'rxclass_api'),
                    ))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.debug(f'RxClassCache save error: {e}')

    def get_drugs_in_class(self, class_id: str, relation_source: str = "ATC") -> list:
        """
        Get all drugs in a given drug class.

        Parameters
        ----------
        class_id : str
            The drug class identifier, e.g. "C03AA" for thiazide diuretics
        relation_source : str
            Classification system: "ATC", "EPC", "VA", "MESH"

        Returns
        -------
        list of dicts with keys: rxcui, name, tty (term type)
        """
        try:
            data = self._get(
                "/classMembers.json",
                params={"classId": class_id, "relaSource": relation_source, "ttys": "IN"},
            )
            members = (data.get("drugMemberGroup") or {}).get("drugMember") or []
            return [
                {
                    "rxcui": m.get("minConcept", {}).get("rxcui"),
                    "name": m.get("minConcept", {}).get("name"),
                    "tty": m.get("minConcept", {}).get("tty"),
                }
                for m in members
            ]
        except APIUnavailableError:
            logger.warning(f"RxClass members unavailable for class: {class_id}")
            return []

    def get_classes_for_drug_name(self, drug_name: str) -> list:
        """
        Shortcut: combine name lookup and class assignment in one call.
        Useful when you have a drug name but not yet its RxCUI.
        """
        try:
            data = self._get(
                "/class/byDrugName.json",
                params={"drugName": drug_name, "relaSource": "ATC"},
            )
            groups = (data.get("rxclassDrugInfoList") or {}).get("rxclassDrugInfo") or []
            return [
                {
                    "class_id": (item.get("rxclassMinConceptItem") or {}).get("classId"),
                    "class_name": (item.get("rxclassMinConceptItem") or {}).get("className"),
                    "class_type": (item.get("rxclassMinConceptItem") or {}).get("classType"),
                }
                for item in groups
            ]
        except APIUnavailableError:
            return []

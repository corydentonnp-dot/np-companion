"""
NP Companion — OpenFDA Drug Recalls Service
File: app/services/api/openfda_recalls.py

Returns active and historical FDA drug recall enforcement actions.
Used by the Drug Recall Alert System to check patient medications against
current recalls daily and surface Class I/II recalls immediately.

Base URL: https://api.fda.gov/drug/enforcement.json
Auth: Same free key as drug labels API

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (OPENFDA_RECALLS_BASE_URL, OPENFDA_RECALLS_CACHE_TTL_DAYS)

NP Companion features that rely on this module:
- Drug Recall Alert System (new Feature A from API intelligence plan)
- Morning Briefing (F22) — "No active recalls" or recall count
- Patient Chart View — recall badge on Medications tab
- Delayed Message Sender (F18) — auto-draft patient notification for Class I recalls
"""

import logging
from app.api_config import OPENFDA_RECALLS_BASE_URL, OPENFDA_RECALLS_CACHE_TTL_DAYS
from app.services.api.base_client import BaseAPIClient, APIUnavailableError

logger = logging.getLogger(__name__)

# Alert priority by recall classification (per CMS/FDA policy)
# Class I: risk of serious adverse health consequences or death
# Class II: may cause temporary adverse health consequences
# Class III: unlikely to cause adverse health consequences
RECALL_CLASS_PRIORITY = {
    "Class I":   "critical",    # Push notification priority 2 (emergency)
    "Class II":  "high",        # Push notification priority 1
    "Class III": "low",         # Morning briefing mention only
}


class OpenFDARecallsService(BaseAPIClient):
    """
    Service for the OpenFDA Drug Enforcement (Recalls) API.
    """

    def __init__(self, db):
        super().__init__(
            api_name="openfda_recalls",
            base_url=OPENFDA_RECALLS_BASE_URL,
            db=db,
            ttl_days=OPENFDA_RECALLS_CACHE_TTL_DAYS,  # Check daily — recalls are urgent
        )

    def check_drug_for_recalls(self, drug_name: str, rxcui: str = None) -> list:
        """
        Check if a specific drug has any active recalls.

        Parameters
        ----------
        drug_name : str
            The drug name to check (generic or brand)
        rxcui : str or None
            If provided, also search by RxCUI for more complete matching.

        Returns
        -------
        list of dicts — each dict is one recall record with keys:
            recall_number, reason_for_recall, classification,
            recalling_firm, distribution_pattern, product_description,
            recall_initiation_date, alert_priority (derived from classification)
        """
        try:
            # Search for ongoing recalls by drug name
            results = self._get(
                "",
                params={
                    "search": f"status:Ongoing AND product_description:{drug_name}",
                    "limit": 10,
                },
            )
            recalls = results.get("results") or []
            return [self._parse_recall(r) for r in recalls]

        except APIUnavailableError:
            logger.warning(f"OpenFDA recalls unavailable for drug: {drug_name}")
            return []

    def check_drug_list_for_recalls(self, drug_list: list) -> dict:
        """
        Check a list of drugs for recalls in batch.
        Used by the morning briefing job and pre-visit overnight prep.

        Parameters
        ----------
        drug_list : list of dicts
            Each dict must have at least 'drug_name' key.
            Optional 'rxcui' key improves matching accuracy.

        Returns
        -------
        dict — keyed by drug_name, values are lists of recall records.
        Only includes drugs that have at least one active recall.
        """
        recall_hits = {}
        for drug in drug_list:
            drug_name = drug.get("drug_name") or ""
            rxcui = drug.get("rxcui")
            if not drug_name:
                continue
            recalls = self.check_drug_for_recalls(drug_name, rxcui)
            if recalls:
                recall_hits[drug_name] = recalls
        return recall_hits

    def _parse_recall(self, raw: dict) -> dict:
        """
        Extract key fields from a raw recall enforcement action record.
        """
        classification = raw.get("classification") or "Unknown"
        return {
            "recall_number": raw.get("recall_number"),
            "reason_for_recall": raw.get("reason_for_recall"),
            "classification": classification,
            "recalling_firm": raw.get("recalling_firm"),
            "distribution_pattern": raw.get("distribution_pattern"),
            "product_description": raw.get("product_description"),
            "recall_initiation_date": raw.get("recall_initiation_date"),
            "status": raw.get("status"),
            "alert_priority": RECALL_CLASS_PRIORITY.get(classification, "low"),
        }

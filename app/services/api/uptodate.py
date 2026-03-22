"""
CareCompanion — UpToDate / DynaMed API Service (Optional Premium)
File: app/services/api/uptodate.py

Phase 23 deliverable — optional premium clinical reference API client.
Gated on UPTODATE_API_KEY or DYNAMED_API_KEY in config.py.

If no API key is configured, the service disables itself and all public
methods return empty lists immediately — the MonitoringRuleEngine
waterfall step 5 proceeds silently.

Dependencies:
- app/api_config.py (UPTODATE_API_KEY, DYNAMED_API_KEY, UPTODATE_BASE_URL,
  UPTODATE_CACHE_TTL_DAYS)
- app/services/api/base_client.py (BaseAPIClient, APIUnavailableError)
"""

import logging

from app.api_config import (
    UPTODATE_API_KEY,
    DYNAMED_API_KEY,
    UPTODATE_BASE_URL,
    UPTODATE_CACHE_TTL_DAYS,
)
from app.services.api.base_client import BaseAPIClient, APIUnavailableError

logger = logging.getLogger(__name__)


class UpToDateService(BaseAPIClient):
    """
    Optional UpToDate / DynaMed clinical reference API client.

    Premium, license-gated. If no API key is configured in config.py,
    ``self.enabled`` is ``False`` and all public methods return ``[]``.
    """

    def __init__(self, db):
        self.enabled = bool(UPTODATE_API_KEY or DYNAMED_API_KEY)
        if self.enabled:
            super().__init__(
                api_name="uptodate",
                base_url=UPTODATE_BASE_URL,
                db=db,
                ttl_days=UPTODATE_CACHE_TTL_DAYS,
            )
        else:
            # Skip BaseAPIClient init — no HTTP calls will ever be made.
            self._db = db

    def get_monitoring_recommendations(self, drug_name):
        """
        Query UpToDate or DynaMed for drug monitoring recommendations.

        Parameters
        ----------
        drug_name : str
            Drug name or RxCUI to look up.

        Returns
        -------
        list[dict]
            List of monitoring recommendation dicts with keys:
            ``lab_loinc_code``, ``lab_name``, ``interval_days``,
            ``priority``, ``clinical_context``.
            Returns ``[]`` if the service is disabled, the API is
            unavailable, or no recommendations are found.
        """
        if not self.enabled or not drug_name:
            return []

        try:
            data = self._get(
                "/search",
                params={"search": drug_name, "type": "drug-monitoring"},
            )
            return self._parse_recommendations(data)
        except APIUnavailableError:
            logger.info("UpToDate API unavailable for drug %s", drug_name)
            return []
        except Exception:
            logger.debug(
                "UpToDate lookup error for %s", drug_name, exc_info=True
            )
            return []

    def _parse_recommendations(self, data):
        """Parse API response into standardized monitoring recommendation dicts."""
        if not data or not isinstance(data, dict):
            return []

        results = []
        for item in data.get("data", data.get("results", [])):
            rec = {
                "lab_loinc_code": item.get("loinc_code", ""),
                "lab_name": item.get("lab_name", ""),
                "interval_days": item.get("interval_days", 90),
                "priority": item.get("priority", "routine"),
                "clinical_context": item.get("clinical_context", ""),
            }
            if rec["lab_name"]:
                results.append(rec)
        return results

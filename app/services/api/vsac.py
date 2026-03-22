"""
CareCompanion — VSAC (Value Set Authority Center) Service
File: app/services/api/vsac.py

VSAC provides standardized value sets used in eCQMs (electronic Clinical
Quality Measures), C-CDA documents, and clinical decision support rules.
Value sets define groups of codes (ICD-10, SNOMED, RxNorm, LOINC, etc.)
that represent a clinical concept (e.g., "Diabetes" = all ICD-10 codes
for diabetes mellitus).

Base URL: https://cts.nlm.nih.gov/fhir
Auth: Same UMLS API key (Bearer token)

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (VSAC_BASE_URL, VSAC_CACHE_TTL_DAYS)

CareCompanion features that rely on this module:
- Care Gap Engine — standardized condition definitions from eCQM value sets
- Billing Rules — condition group definitions for CCM/AWV eligibility
- Clinical Quality Measures — future eCQM reporting
"""

import logging
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from app.api_config import VSAC_BASE_URL, VSAC_CACHE_TTL_DAYS, HTTP_TIMEOUT_SECONDS
from app.services.api.base_client import BaseAPIClient, APIUnavailableError
from models.api_cache import VsacValueSetCache

logger = logging.getLogger(__name__)


class VSACService(BaseAPIClient):
    """
    Service for the NLM Value Set Authority Center (VSAC) FHIR R4 API.

    Requires a UMLS API key (same key used for UMLSService).
    All methods gracefully return empty results if no API key is configured.
    """

    def __init__(self, db, api_key: str = None):
        super().__init__(
            api_name="vsac",
            base_url=VSAC_BASE_URL,
            db=db,
            ttl_days=VSAC_CACHE_TTL_DAYS,
        )
        self._api_key = api_key

    def _require_api_key(self) -> bool:
        if not self._api_key:
            logger.warning("VSAC API key not configured — uses same key as UMLS")
            return False
        return True

    def expand_value_set(self, oid: str) -> dict:
        """
        Expand a value set by its OID, returning all codes in the set.

        Parameters
        ----------
        oid : str
            Value set OID, e.g. "2.16.840.1.113883.3.464.1003.103.12.1001" (Diabetes)

        Returns
        -------
        dict with keys:
            oid (str) — the value set OID
            name (str) — display name of the value set
            codes (list of dict) — each with {code, system, display}
        """
        if not self._require_api_key():
            return {"oid": oid, "name": "", "codes": []}

        # Check structured cache first
        cached = self._get_from_cache(oid)
        if cached:
            return cached

        try:
            url = f"{self.base_url}/ValueSet/{oid}/$expand"
            req = Request(url)
            req.add_header("Authorization", f"Bearer {self._api_key}")
            req.add_header("Accept", "application/fhir+json")

            with urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            expansion = data.get("expansion", {})
            contains = expansion.get("contains", [])

            result = {
                "oid": oid,
                "name": data.get("name", ""),
                "codes": [
                    {
                        "code": c.get("code", ""),
                        "system": c.get("system", ""),
                        "display": c.get("display", ""),
                    }
                    for c in contains
                ],
            }

            self._save_to_cache(oid, result)
            return result

        except (URLError, HTTPError) as e:
            logger.warning(f"VSAC unavailable for OID {oid}: {e}")
            return {"oid": oid, "name": "", "codes": []}

    def search_value_sets(self, keyword: str) -> list:
        """
        Search for value sets by keyword.

        Returns
        -------
        list of dicts with keys: oid (str), name (str), status (str)
        """
        if not self._require_api_key():
            return []

        try:
            url = f"{self.base_url}/ValueSet?name:contains={keyword}&_count=20"
            req = Request(url)
            req.add_header("Authorization", f"Bearer {self._api_key}")
            req.add_header("Accept", "application/fhir+json")

            with urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            entries = data.get("entry", [])
            results = []
            for entry in entries:
                resource = entry.get("resource", {})
                oid = ""
                for ident in resource.get("identifier", []):
                    if ident.get("system") == "urn:ietf:rfc:3986":
                        oid = ident.get("value", "").replace("urn:oid:", "")
                        break
                results.append({
                    "oid": oid,
                    "name": resource.get("name", ""),
                    "status": resource.get("status", ""),
                })
            return results

        except (URLError, HTTPError) as e:
            logger.warning(f"VSAC search unavailable for keyword '{keyword}': {e}")
            return []

    def _get_from_cache(self, oid: str) -> dict:
        """Check VsacValueSetCache for a non-expired entry."""
        from datetime import datetime, timezone, timedelta
        try:
            entry = VsacValueSetCache.query.filter_by(oid=oid).first()
            if entry and entry.cached_at:
                age = datetime.now(timezone.utc) - entry.cached_at
                if age < timedelta(days=VSAC_CACHE_TTL_DAYS):
                    codes = json.loads(entry.codes_json) if entry.codes_json else []
                    return {"oid": oid, "name": entry.name, "codes": codes}
        except Exception as e:
            logger.debug(f"VSAC cache read error: {e}")
        return None

    def _save_to_cache(self, oid: str, result: dict):
        """Persist expanded value set to VsacValueSetCache."""
        from datetime import datetime, timezone
        db = self.cache.db
        try:
            existing = VsacValueSetCache.query.filter_by(oid=oid).first()
            codes_json = json.dumps(result.get("codes", []))
            if existing:
                existing.name = result.get("name", "")
                existing.codes_json = codes_json
                existing.code_count = len(result.get("codes", []))
                existing.cached_at = datetime.now(timezone.utc)
            else:
                db.session.add(VsacValueSetCache(
                    oid=oid,
                    name=result.get("name", ""),
                    codes_json=codes_json,
                    code_count=len(result.get("codes", [])),
                ))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.debug(f"VSAC cache save error: {e}")

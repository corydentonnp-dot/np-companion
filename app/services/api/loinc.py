"""
CareCompanion — LOINC Lab Code Service
File: app/services/api/loinc.py

LOINC (Logical Observation Identifiers Names and Codes) is the universal
standard for lab test identification. Resolves LOINC codes from Clinical
Summary XML to human-readable test names, units, and reference ranges.

Base URL: https://fhir.loinc.org (FHIR R4)
Auth: Free account required at https://loinc.org/join/
LOINC license: Free for US healthcare use

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (LOINC_BASE_URL, LOINC_CACHE_TTL_DAYS)

CareCompanion features that rely on this module:
- Lab Value Tracker (F11) — test identification, units, reference ranges
- Lab Panel Grouping (F11d) — automatic panel assembly
- Abnormal Lab Interpretation (Feature B) — reference range comparison
- Pre-visit note prep — lab section of pre-visit note
- Clinical Summary XML parsing — LOINC code resolution on import
"""

import logging
import base64
from app.api_config import LOINC_BASE_URL, LOINC_CACHE_TTL_DAYS
from app.services.api.base_client import BaseAPIClient, APIUnavailableError
from models.api_cache import LoincCache

logger = logging.getLogger(__name__)

# Common primary care LOINC panel codes
# These are the standard panel codes used for automatic lab grouping (F11d)
COMMON_PANEL_CODES = {
    "24323-8": "Comprehensive Metabolic Panel (CMP)",
    "24322-0": "Basic Metabolic Panel (BMP)",
    "58410-2": "CBC with Differential",
    "57698-3": "Lipid Panel",
    "24360-0": "Hemoglobin A1c",
    "11580-8": "Thyroid Stimulating Hormone (TSH)",
    "2823-3":  "Potassium",
    "2160-0":  "Creatinine",
    "33914-3": "eGFR (CKD-EPI)",
    "1751-7":  "Albumin",
    "14804-9": "LDL Cholesterol",
}


class LOINCService(BaseAPIClient):
    """
    Service for the Regenstrief LOINC FHIR Server.

    Requires a LOINC account. Credentials are stored in the User model's
    preferences JSON (loinc_username, loinc_password). The service will
    gracefully return empty results when credentials are not configured.
    """

    def __init__(self, db, username: str = None, password: str = None):
        """
        Parameters
        ----------
        username : str or None
            LOINC account username (from user preferences or admin settings)
        password : str or None
            LOINC account password
        """
        super().__init__(
            api_name="loinc",
            base_url=LOINC_BASE_URL,
            db=db,
            ttl_days=LOINC_CACHE_TTL_DAYS,
        )
        self._username = username
        self._password = password

    def _get_auth_header(self) -> dict:
        """Build Basic Auth header from stored credentials."""
        if self._username and self._password:
            token = base64.b64encode(
                f"{self._username}:{self._password}".encode()
            ).decode()
            return {"Authorization": f"Basic {token}"}
        return {}

    def lookup_code(self, loinc_code: str) -> dict:
        """
        Get full LOINC properties for a lab test code.
        Used when parsing Clinical Summary XML lab results.

        Returns
        -------
        dict with keys:
            loinc_code (str), display_name (str), long_name (str),
            component (str), system (str), scale_type (str),
            units (str), reference_range_text (str), _stale (bool)
        """
        try:
            # Using the FHIR $lookup operation
            data = self._get(
                "/CodeSystem/$lookup",
                params={
                    "system": "http://loinc.org",
                    "code": loinc_code,
                },
            )
            result = self._parse_lookup(loinc_code, data)
            self._save_to_structured_cache(result)
            return result
        except APIUnavailableError:
            logger.warning(f"LOINC unavailable for code: {loinc_code}")
            return {"loinc_code": loinc_code, "_stale": True}
        except Exception as e:
            logger.warning(f"LOINC lookup error for {loinc_code}: {e}")
            return {"loinc_code": loinc_code}

    def _save_to_structured_cache(self, result):
        """Persist lookup result to the structured LoincCache table."""
        code = result.get('loinc_code')
        if not code:
            return
        db = self.cache.db
        try:
            existing = LoincCache.query.filter_by(loinc_code=code).first()
            if not existing:
                db.session.add(LoincCache(
                    loinc_code=code,
                    display_name=result.get('display_name', ''),
                    component=result.get('long_name', ''),
                ))
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.debug(f'LoincCache save error: {e}')

    def _parse_lookup(self, loinc_code: str, data: dict) -> dict:
        """Parse the FHIR CodeSystem $lookup response."""
        parameters = data.get("parameter") or []
        result = {"loinc_code": loinc_code, "_stale": data.get("_stale", False)}

        for param in parameters:
            name = param.get("name")
            value = (
                param.get("valueString") or
                param.get("valueCode") or
                param.get("valueCoding", {}).get("display") or
                ""
            )
            if name == "display":
                result["display_name"] = value
            elif name == "designation":
                # Long name is in the designation list
                parts = param.get("part") or []
                for p in parts:
                    if p.get("name") == "value":
                        result["long_name"] = p.get("valueString") or value

        return result

    def expand_panel(self, panel_loinc_code: str) -> list:
        """
        Get all component tests in a standard lab panel.
        Used by Lab Panel Grouping (F11d) for automatic panel assembly.

        Returns
        -------
        list of dicts with keys: loinc_code, display_name
        """
        try:
            data = self._get(
                "/ValueSet/$expand",
                params={"url": f"http://loinc.org/vs/{panel_loinc_code}"},
            )
            expansion = data.get("expansion") or {}
            contains = expansion.get("contains") or []
            return [
                {"loinc_code": item.get("code"), "display_name": item.get("display")}
                for item in contains
            ]
        except APIUnavailableError:
            return []

    def get_panel_name(self, panel_code: str) -> str:
        """
        Return the human-readable name for a panel LOINC code.
        Falls back to the COMMON_PANEL_CODES lookup table before hitting the API.
        """
        return COMMON_PANEL_CODES.get(panel_code) or ""

"""
CareCompanion — NPPES NPI Registry API Service
File: app/services/api/nppes.py

Queries the CMS NPPES NPI Registry v2.1 for provider lookup,
search, and NPI validation. Used to verify specialist referral
information and auto-populate PA Generator forms.

Base URL: https://npiregistry.cms.hhs.gov/api
Auth: None required
Rate limit: No documented limit — cache aggressively

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (NPPES_BASE_URL, NPPES_CACHE_TTL_DAYS)

CareCompanion features that rely on this module:
- Specialists widget — verify NPI and licensing status
- PA Generator (F26) — auto-populate specialist NPI on forms
"""

import logging
from app.api_config import NPPES_BASE_URL, NPPES_CACHE_TTL_DAYS
from app.services.api.base_client import BaseAPIClient, APIUnavailableError

logger = logging.getLogger(__name__)


class NppesService(BaseAPIClient):
    """
    Service for the CMS NPPES NPI Registry API v2.1.

    Provides NPI lookup, provider search, and active-status validation.
    """

    def __init__(self, db):
        super().__init__(
            api_name="nppes",
            base_url=NPPES_BASE_URL,
            db=db,
            ttl_days=NPPES_CACHE_TTL_DAYS,
        )

    def lookup_npi(self, npi: str) -> dict:
        """
        Look up a provider by NPI number.

        Parameters
        ----------
        npi : str
            10-digit NPI number

        Returns
        -------
        dict with keys:
            npi (str), name (str), credential (str), specialty (str),
            address (str), phone (str), enumeration_type (str),
            status (str — "A" for active), _stale (bool)
        Returns empty dict if not found.
        """
        if not npi or not str(npi).strip().isdigit():
            return {}
        try:
            data = self._get("/", params={"version": "2.1", "number": str(npi).strip()})
            results = data.get("results") or []
            if not results:
                return {"npi": npi, "name": None, "status": "NOT_FOUND",
                        "_stale": data.get("_stale", False)}
            provider = results[0]
            basic = provider.get("basic") or {}
            addresses = provider.get("addresses") or []
            taxonomies = provider.get("taxonomies") or []

            # Build name
            name_parts = []
            if basic.get("first_name"):
                name_parts.append(basic["first_name"])
            if basic.get("last_name"):
                name_parts.append(basic["last_name"])
            if not name_parts and basic.get("organization_name"):
                name_parts.append(basic["organization_name"])

            # Primary practice address
            address = ""
            for addr in addresses:
                if addr.get("address_purpose") == "LOCATION":
                    parts = [addr.get("address_1", ""), addr.get("city", ""),
                             addr.get("state", ""), addr.get("postal_code", "")[:5]]
                    address = ", ".join(p for p in parts if p)
                    break

            # Primary taxonomy (specialty)
            specialty = ""
            for tax in taxonomies:
                if tax.get("primary"):
                    specialty = tax.get("desc", "")
                    break
            if not specialty and taxonomies:
                specialty = taxonomies[0].get("desc", "")

            phone = ""
            for addr in addresses:
                if addr.get("telephone_number"):
                    phone = addr["telephone_number"]
                    break

            return {
                "npi": str(provider.get("number", npi)),
                "name": " ".join(name_parts),
                "credential": basic.get("credential", ""),
                "specialty": specialty,
                "address": address,
                "phone": phone,
                "enumeration_type": provider.get("enumeration_type", ""),
                "status": basic.get("status", "A"),
                "_stale": data.get("_stale", False),
            }
        except APIUnavailableError:
            logger.warning("NPPES unavailable for NPI: %s", npi)
            return {}

    def search_provider(self, name: str = None, state: str = None,
                        taxonomy: str = None) -> list:
        """
        Search for providers by name, state, and/or taxonomy.

        Parameters
        ----------
        name : str or None
            Provider last name or organization name
        state : str or None
            Two-letter state code (e.g. "VA")
        taxonomy : str or None
            Taxonomy description (e.g. "Family Medicine")

        Returns
        -------
        list of dict, each with: npi, name, credential, specialty, address, status
        """
        params = {"version": "2.1", "limit": "10"}
        if name:
            # Try last name first; NPPES requires exact field names
            params["last_name"] = name
        if state:
            params["state"] = state
        if taxonomy:
            params["taxonomy_description"] = taxonomy

        if len(params) <= 2:
            # Only version and limit — need at least one search term
            return []

        try:
            data = self._get("/", params=params)
            results = data.get("results") or []
            providers = []
            for provider in results[:10]:
                basic = provider.get("basic") or {}
                taxonomies = provider.get("taxonomies") or []
                addresses = provider.get("addresses") or []

                name_parts = []
                if basic.get("first_name"):
                    name_parts.append(basic["first_name"])
                if basic.get("last_name"):
                    name_parts.append(basic["last_name"])
                if not name_parts and basic.get("organization_name"):
                    name_parts.append(basic["organization_name"])

                specialty = ""
                for tax in taxonomies:
                    if tax.get("primary"):
                        specialty = tax.get("desc", "")
                        break

                address = ""
                for addr in addresses:
                    if addr.get("address_purpose") == "LOCATION":
                        parts = [addr.get("city", ""), addr.get("state", "")]
                        address = ", ".join(p for p in parts if p)
                        break

                providers.append({
                    "npi": str(provider.get("number", "")),
                    "name": " ".join(name_parts),
                    "credential": basic.get("credential", ""),
                    "specialty": specialty,
                    "address": address,
                    "status": basic.get("status", "A"),
                })
            return providers
        except APIUnavailableError:
            logger.warning("NPPES search unavailable for name=%s state=%s", name, state)
            return []

    def validate_active(self, npi: str) -> bool:
        """
        Check whether an NPI is currently active.

        Returns True if the NPI exists and has status "A" (active).
        Returns False if not found, deactivated, or API unavailable.
        """
        result = self.lookup_npi(npi)
        return result.get("status") == "A"

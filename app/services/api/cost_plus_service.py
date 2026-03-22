"""
CareCompanion — Cost Plus Drugs API Service (Tier 1 Pricing)
File: app/services/api/cost_plus_service.py

Primary pricing source in the Three-Tier Waterfall:
  Tier 1: Cost Plus Drugs (this module) — free, no auth
  Tier 2: GoodRx Price Compare — secondary, only when Tier 1 misses
  Tier 3: NeedyMeds/RxAssist — assistance programs

INTENTIONALLY UNAUTHENTICATED — Cost Plus Drugs is a free public API
with no key, no registration, no rate limits, and no usage minimums.
This is not a missing configuration — this is by design.

Dependencies:
- app/api_config.py (COST_PLUS_BASE_URL, COST_PLUS_CACHE_TTL_DAYS,
  COST_PLUS_DEFAULT_QUANTITY)
- app/services/api/base_client.py (BaseAPIClient, APIUnavailableError)
"""

import logging

from app.api_config import (
    COST_PLUS_BASE_URL,
    COST_PLUS_CACHE_TTL_DAYS,
    COST_PLUS_DEFAULT_QUANTITY,
)
from app.services.api.base_client import BaseAPIClient, APIUnavailableError

logger = logging.getLogger(__name__)


class CostPlusService(BaseAPIClient):
    """
    Cost Plus Drugs public pricing API.

    No API key required. Queries drug pricing by NDC or drug name.
    Returns structured pricing data or None when the drug is not
    in the Cost Plus catalog (not an error — just not stocked).
    """

    def __init__(self, db):
        super().__init__(
            api_name="cost_plus",
            base_url=COST_PLUS_BASE_URL,
            db=db,
            ttl_days=COST_PLUS_CACHE_TTL_DAYS,
        )

    def lookup_by_ndc(self, ndc, quantity=None):
        """
        Look up pricing by NDC code (most precise path).

        Parameters
        ----------
        ndc : str
            National Drug Code, e.g. "00093-7180-01"
        quantity : int or None
            Number of units (default: COST_PLUS_DEFAULT_QUANTITY)

        Returns
        -------
        dict or None
            Pricing data dict if found, None if not in catalog.
        """
        if not ndc:
            return None
        qty = quantity or COST_PLUS_DEFAULT_QUANTITY
        try:
            data = self._get("", params={"ndc": ndc, "quantity_units": qty})
            return self._parse_response(data, qty)
        except APIUnavailableError:
            logger.info("Cost Plus API unavailable for NDC %s", ndc)
            return None
        except Exception:
            logger.debug("Cost Plus lookup_by_ndc error for %s", ndc, exc_info=True)
            return None

    def lookup_by_name(self, medication_name, strength=None, quantity=None):
        """
        Look up pricing by medication name (fallback when NDC unavailable).

        Parameters
        ----------
        medication_name : str
            Drug name, e.g. "atorvastatin"
        strength : str or None
            Dose strength, e.g. "20 mg"
        quantity : int or None
            Number of units (default: COST_PLUS_DEFAULT_QUANTITY)

        Returns
        -------
        dict or None
            Pricing data dict if found, None if not in catalog.
        """
        if not medication_name:
            return None
        qty = quantity or COST_PLUS_DEFAULT_QUANTITY
        params = {"medication_name": medication_name, "quantity_units": qty}
        if strength:
            params["strength"] = strength
        try:
            data = self._get("", params=params)
            return self._parse_response(data, qty)
        except APIUnavailableError:
            logger.info("Cost Plus API unavailable for %s", medication_name)
            return None
        except Exception:
            logger.debug("Cost Plus lookup_by_name error for %s", medication_name, exc_info=True)
            return None

    def get_price(self, rxcui=None, ndc=None, drug_name=None,
                  strength=None, quantity=None):
        """
        Unified entry point — tries NDC first, then name fallback.

        Returns
        -------
        dict
            Always returns a dict with at minimum {found: bool, source: "cost_plus"}.
            If found=True, includes full pricing fields.
        """
        qty = quantity or COST_PLUS_DEFAULT_QUANTITY
        result = None

        # Priority 1: NDC (most precise)
        if ndc:
            result = self.lookup_by_ndc(ndc, qty)

        # Priority 2: drug name + strength
        if not result and drug_name:
            result = self.lookup_by_name(drug_name, strength, qty)

        if result:
            result["found"] = True
            result["source"] = "cost_plus"
            return result

        return {"found": False, "source": "cost_plus"}

    def _parse_response(self, data, quantity):
        """
        Parse Cost Plus API response into a standardized pricing dict.

        Returns None if the response indicates the drug is not in catalog.
        """
        if not data or not isinstance(data, dict):
            return None

        # The API may return an error field or empty result for unlisted drugs
        if data.get("error") or not data.get("medication_name", data.get("name")):
            return None

        unit_price = data.get("unit_price") or data.get("price")
        if unit_price is None:
            return None

        try:
            unit_price = float(unit_price)
        except (ValueError, TypeError):
            return None

        monthly_price = data.get("requested_quote") or (unit_price * quantity)
        try:
            monthly_price = float(monthly_price)
        except (ValueError, TypeError):
            monthly_price = unit_price * quantity

        return {
            "medication_name": data.get("medication_name", data.get("name", "")),
            "brand_name": data.get("brand_name", ""),
            "form": data.get("form", ""),
            "strength": data.get("strength", ""),
            "ndc": data.get("ndc", ""),
            "unit_price": unit_price,
            "monthly_price": round(monthly_price, 2),
            "price_display": f"${monthly_price:.2f}/month",
            "url": data.get("url", ""),
            "quantity": quantity,
        }

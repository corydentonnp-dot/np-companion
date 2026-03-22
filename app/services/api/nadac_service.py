"""
CareCompanion — NADAC Pricing Service (Tier 1b Reference)
File: app/services/api/nadac_service.py

NADAC (National Average Drug Acquisition Cost) — free CMS data showing
what pharmacies pay wholesalers. This is a REFERENCE price that augments
the primary pricing tier, not a replacement.

INTENTIONALLY UNAUTHENTICATED — NADAC is a free public CMS dataset
with no key, no registration, and no rate limits.

Dependencies:
- app/api_config.py (NADAC_BASE_URL, NADAC_DATASET_ID, NADAC_CACHE_TTL_DAYS,
  NADAC_DEFAULT_QUANTITY)
- app/services/api/base_client.py (BaseAPIClient, APIUnavailableError)
"""

import logging

from app.api_config import (
    NADAC_BASE_URL,
    NADAC_DATASET_ID,
    NADAC_CACHE_TTL_DAYS,
    NADAC_DEFAULT_QUANTITY,
)
from app.services.api.base_client import BaseAPIClient, APIUnavailableError

logger = logging.getLogger(__name__)


class NADACService(BaseAPIClient):
    """
    NADAC public pricing API (CMS Medicaid.gov open data).

    No API key required. Queries the National Average Drug Acquisition
    Cost by NDC or drug name. Returns structured reference pricing data
    or None when no NADAC record exists for the drug.
    """

    def __init__(self, db):
        super().__init__(
            api_name="nadac",
            base_url=NADAC_BASE_URL,
            db=db,
            ttl_days=NADAC_CACHE_TTL_DAYS,
        )

    def get_nadac_price(self, ndc, quantity=None):
        """
        Look up NADAC reference price by NDC code.

        Parameters
        ----------
        ndc : str
            National Drug Code (NDC-11 format preferred).
        quantity : int or None
            Number of units for monthly estimate (default: NADAC_DEFAULT_QUANTITY).

        Returns
        -------
        dict or None
            NADAC pricing dict if found, None otherwise.
        """
        if not ndc:
            return None
        qty = quantity or NADAC_DEFAULT_QUANTITY
        # Strip hyphens for consistent NDC format
        ndc_clean = ndc.replace("-", "")
        try:
            data = self._get(
                f"/{NADAC_DATASET_ID}",
                params={
                    "conditions[0][property]": "ndc",
                    "conditions[0][value]": ndc_clean,
                    "conditions[0][operator]": "=",
                    "sort": "effective_date",
                    "order": "desc",
                    "limit": 1,
                },
            )
            return self._parse_response(data, qty)
        except APIUnavailableError:
            logger.info("NADAC API unavailable for NDC %s", ndc)
            return None
        except Exception:
            logger.debug("NADAC lookup error for NDC %s", ndc, exc_info=True)
            return None

    def get_nadac_price_by_name(self, drug_name, quantity=None):
        """
        Look up NADAC reference price by drug name (fallback).

        Parameters
        ----------
        drug_name : str
            Drug name, e.g. "atorvastatin".
        quantity : int or None
            Number of units for monthly estimate.

        Returns
        -------
        dict or None
            NADAC pricing dict if found, None otherwise.
        """
        if not drug_name:
            return None
        qty = quantity or NADAC_DEFAULT_QUANTITY
        try:
            data = self._get(
                f"/{NADAC_DATASET_ID}",
                params={
                    "conditions[0][property]": "ndc_description",
                    "conditions[0][value]": drug_name,
                    "conditions[0][operator]": "contains",
                    "sort": "effective_date",
                    "order": "desc",
                    "limit": 1,
                },
            )
            return self._parse_response(data, qty)
        except APIUnavailableError:
            logger.info("NADAC API unavailable for drug %s", drug_name)
            return None
        except Exception:
            logger.debug("NADAC lookup error for %s", drug_name, exc_info=True)
            return None

    def get_price(self, ndc=None, drug_name=None, quantity=None):
        """
        Unified entry point — tries NDC first, then name fallback.

        Returns
        -------
        dict
            Always returns a dict with at minimum {found: bool, source: "nadac"}.
        """
        result = None

        if ndc:
            result = self.get_nadac_price(ndc, quantity)

        if not result and drug_name:
            result = self.get_nadac_price_by_name(drug_name, quantity)

        if result:
            result["found"] = True
            result["source"] = "nadac"
            return result

        return {"found": False, "source": "nadac"}

    def _parse_response(self, data, quantity):
        """
        Parse NADAC API response into a standardized pricing dict.

        Returns None if no valid pricing data found.
        """
        if not data or not isinstance(data, dict):
            return None

        results = data.get("results") or []
        if not results:
            return None

        record = results[0] if isinstance(results, list) else None
        if not record or not isinstance(record, dict):
            return None

        nadac_per_unit = record.get("nadac_per_unit")
        if nadac_per_unit is None:
            return None

        try:
            nadac_per_unit = float(nadac_per_unit)
        except (ValueError, TypeError):
            return None

        nadac_monthly = round(nadac_per_unit * quantity, 2)

        return {
            "ndc_description": record.get("ndc_description", ""),
            "ndc": record.get("ndc", ""),
            "nadac_per_unit": round(nadac_per_unit, 4),
            "nadac_monthly": nadac_monthly,
            "pricing_unit": record.get("pricing_unit", ""),
            "effective_date": record.get("effective_date", ""),
            "pharmacy_type": record.get("pharmacy_type_indicator", ""),
            "price_display": f"${nadac_monthly:.2f}/month",
            "quantity": quantity,
        }

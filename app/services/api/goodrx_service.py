"""
CareCompanion — GoodRx Price Compare API Service (Tier 2 Pricing)
File: app/services/api/goodrx_service.py

PRICE COMPARE API ONLY (/v2/price/compare)
The Coupon API (/v2/coupon) is INTENTIONALLY EXCLUDED.
Reason: requires 3,000 coupon accesses/month minimum — a single-provider
practice with 20-25 patients/day cannot reliably meet this volume.
This module uses ONLY the Price Compare endpoint for cash price data.

Secondary pricing source in the Three-Tier Waterfall:
  Tier 1: Cost Plus Drugs — free, no auth (primary)
  Tier 2: GoodRx Price Compare (this module) — only when Tier 1 misses
  Tier 3: NeedyMeds/RxAssist — assistance programs

ToS NO-AGGREGATION CONSTRAINT: GoodRx prices must NEVER appear alongside
competing pricing data in the same UI component. The waterfall architecture
satisfies this — GoodRx is only queried when Cost Plus returns no result.

Dependencies:
- app/api_config.py (GOODRX_BASE_URL, GOODRX_CACHE_TTL_DAYS,
  GOODRX_DEFAULT_ZIP, GOODRX_API_KEY, GOODRX_SECRET_KEY)
- app/services/api/base_client.py (BaseAPIClient, APIUnavailableError)
"""

import hmac
import hashlib
import base64
import logging
from urllib.parse import urlencode

from app.api_config import (
    GOODRX_BASE_URL,
    GOODRX_CACHE_TTL_DAYS,
    GOODRX_DEFAULT_ZIP,
    GOODRX_API_KEY,
    GOODRX_SECRET_KEY,
)
from app.services.api.base_client import BaseAPIClient, APIUnavailableError

logger = logging.getLogger(__name__)

# Attribution text required by GoodRx ToS on every result
GOODRX_ATTRIBUTION = "Powered by GoodRx"


class GoodRxService(BaseAPIClient):
    """
    GoodRx Price Compare API — cash price comparison across pharmacies.

    HMAC-SHA256 signed requests.  Returns structured pricing data or
    graceful "not configured" / "not found" dicts when the API key is
    missing or data is unavailable.
    """

    def __init__(self, db):
        super().__init__(
            api_name="goodrx",
            base_url=GOODRX_BASE_URL,
            db=db,
            ttl_days=GOODRX_CACHE_TTL_DAYS,
        )

    # ------------------------------------------------------------------
    # 22.2 — HMAC-SHA256 Request Signing
    # ------------------------------------------------------------------

    def _sign_request(self, params):
        """
        Sign request parameters with HMAC-SHA256 per GoodRx spec.

        Steps:
        1. Sort params alphabetically by key
        2. Build query string
        3. Compute HMAC-SHA256 with GOODRX_SECRET_KEY
        4. Append base64-encoded signature as ``sig`` param

        Returns
        -------
        dict or None
            Signed params dict (original + api_key + sig), or None if
            the secret key is not configured.
        """
        if not GOODRX_SECRET_KEY:
            logger.warning("GoodRx secret key not configured — cannot sign request")
            return None

        # Ensure api_key is in the params before signing
        signed = dict(params)
        signed["api_key"] = GOODRX_API_KEY

        # Sort alphabetically and build query string
        sorted_params = sorted(signed.items())
        query_string = urlencode(sorted_params)

        # HMAC-SHA256 signature
        digest = hmac.new(
            GOODRX_SECRET_KEY.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        sig = base64.b64encode(digest).decode("utf-8")

        signed["sig"] = sig
        return signed

    # ------------------------------------------------------------------
    # 22.3 — Drug Name Search / Normalization
    # ------------------------------------------------------------------

    def search_drug(self, drug_name):
        """
        Normalize a drug name to GoodRx-canonical form.

        Parameters
        ----------
        drug_name : str
            Drug name (e.g. "atorvastatin", "Lipitor")

        Returns
        -------
        str or None
            GoodRx drug slug/identifier, or None if not found or API
            key is not configured.
        """
        if not drug_name:
            return None

        if not GOODRX_API_KEY or not GOODRX_SECRET_KEY:
            logger.info("GoodRx API key not configured — skipping drug search")
            return None

        params = {"name": drug_name.strip().lower()}
        signed = self._sign_request(params)
        if signed is None:
            return None

        try:
            data = self._get("/v2/drug/search", params=signed)
            if not data:
                return None
            # GoodRx returns candidates; take the first match
            candidates = data.get("data", data.get("results", []))
            if isinstance(candidates, list) and candidates:
                first = candidates[0]
                return first.get("slug", first.get("name", drug_name))
            # If the response is a flat dict with a slug
            if isinstance(data, dict) and data.get("slug"):
                return data["slug"]
            return drug_name.strip().lower()
        except APIUnavailableError:
            logger.info("GoodRx API unavailable for drug search: %s", drug_name)
            return None
        except Exception:
            logger.debug("GoodRx search_drug error for %s", drug_name, exc_info=True)
            return None

    # ------------------------------------------------------------------
    # 22.4 — Price Compare
    # ------------------------------------------------------------------

    def get_price_compare(self, drug_name, quantity=30, zip_code=None):
        """
        Query GoodRx /v2/price/compare for cash prices.

        Parameters
        ----------
        drug_name : str
            Drug name (preferably GoodRx-normalized via search_drug)
        quantity : int
            Number of units (default 30-day supply)
        zip_code : str or None
            ZIP code for local pricing. Falls back to GOODRX_DEFAULT_ZIP.

        Returns
        -------
        dict or None
            GoodRxResult dict with pricing data, or None if not found
            or API unavailable.  Every result includes attribution_text.
        """
        if not drug_name:
            return None

        if not GOODRX_API_KEY or not GOODRX_SECRET_KEY:
            return None

        effective_zip = zip_code or GOODRX_DEFAULT_ZIP

        params = {
            "name": drug_name.strip().lower(),
            "quantity": str(quantity),
            "zip_code": effective_zip,
        }
        signed = self._sign_request(params)
        if signed is None:
            return None

        try:
            data = self._get("/v2/price/compare", params=signed)
            if not data:
                return None

            return self._parse_compare_response(data, drug_name, quantity, effective_zip)
        except APIUnavailableError:
            logger.info("GoodRx API unavailable for price compare: %s", drug_name)
            return None
        except Exception:
            logger.debug("GoodRx get_price_compare error for %s", drug_name, exc_info=True)
            return None

    def _parse_compare_response(self, data, drug_name, quantity, zip_code):
        """
        Parse GoodRx price compare response into a standardized dict.

        Returns None if the response does not contain usable pricing.
        """
        if not data or not isinstance(data, dict):
            return None

        # GoodRx may nest prices under various keys
        prices = data.get("prices", data.get("data", []))
        if not prices:
            return None

        # Extract the lowest cash price
        lowest_price = None
        pharmacy_names = []

        if isinstance(prices, list):
            for entry in prices:
                price_val = entry.get("price", entry.get("cash_price"))
                if price_val is not None:
                    try:
                        price_val = float(price_val)
                    except (ValueError, TypeError):
                        continue
                    pharmacy = entry.get("pharmacy", entry.get("pharmacy_name", ""))
                    if lowest_price is None or price_val < lowest_price:
                        lowest_price = price_val
                    if pharmacy:
                        pharmacy_names.append(pharmacy)
        elif isinstance(prices, dict):
            lowest_price = prices.get("lowest_price", prices.get("price"))
            if lowest_price is not None:
                try:
                    lowest_price = float(lowest_price)
                except (ValueError, TypeError):
                    lowest_price = None

        if lowest_price is None:
            return None

        # Build a deep link to the GoodRx medication page (NOT a coupon link)
        url_name = drug_name.strip().lower().replace(" ", "-")
        deep_link = f"https://www.goodrx.com/{url_name}"

        return {
            "drug_name": data.get("display_name", drug_name),
            "lowest_price": round(lowest_price, 2),
            "pharmacy_names": pharmacy_names[:5],  # Top 5 pharmacies
            "deep_link_url": deep_link,
            "brand_price": data.get("brand_price"),
            "generic_price": data.get("generic_price"),
            "attribution_text": GOODRX_ATTRIBUTION,
            "zip_code_queried": zip_code,
            "quantity": quantity,
        }

    # ------------------------------------------------------------------
    # 22.5 — Unified Entry Point
    # ------------------------------------------------------------------

    def get_price(self, rxcui=None, drug_name=None, quantity=30, zip_code=None):
        """
        Unified entry point — normalize drug name, then query price.

        Returns
        -------
        dict
            Always returns a dict with at minimum
            ``{found: bool, source: "goodrx"}``.
            If found=True, includes full pricing fields plus attribution.
        """
        # Guard: API key must be configured
        if not GOODRX_API_KEY or not GOODRX_SECRET_KEY:
            return {
                "found": False,
                "source": "goodrx",
                "reason": "api_key_not_configured",
            }

        # Determine the drug name to query
        name = drug_name
        if not name:
            return {
                "found": False,
                "source": "goodrx",
                "reason": "no_drug_name",
            }

        # Step 1: Normalize via GoodRx drug search
        normalized = self.search_drug(name)
        query_name = normalized or name

        # Step 2: Query price compare
        result = self.get_price_compare(query_name, quantity=quantity, zip_code=zip_code)

        if result:
            result["found"] = True
            result["source"] = "goodrx"
            return result

        return {
            "found": False,
            "source": "goodrx",
            "reason": "not_found",
            "attribution_text": GOODRX_ATTRIBUTION,
        }

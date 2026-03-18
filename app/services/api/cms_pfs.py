"""
NP Companion — CMS Physician Fee Schedule Service
File: app/services/api/cms_pfs.py

Queries the CMS Physician Fee Schedule REST API for CPT/HCPCS code rates,
RVU components, and locality-adjusted payment amounts. Virginia falls under
MAC Jurisdiction M (Palmetto GBA).

Base URL: https://pfs.data.cms.gov/api
Auth: None required — fully public

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (CMS_PFS_BASE_URL, CMS_PFS_CACHE_TTL_DAYS,
  CMS_LOCALITY_NUMBER, CY2025_CONVERSION_FACTOR, CURRENT_FEE_SCHEDULE_YEAR)

NP Companion features that rely on this module:
- Billing Opportunity Engine — payment rate lookups for all billing rules
- E&M Calculator (F14a) — RVU-based revenue estimation
- Monthly Billing Report (F14c) — aggregate RVU totals
- AWV Billing Stack display — estimated revenue per code
- Today View billing card — "estimated if documented: $X"
"""

import logging
from app.api_config import (
    CMS_PFS_BASE_URL,
    CMS_PFS_CACHE_TTL_DAYS,
    CMS_LOCALITY_NUMBER,
    CY2025_CONVERSION_FACTOR,
    CURRENT_FEE_SCHEDULE_YEAR,
)
from app.services.api.base_client import BaseAPIClient, APIUnavailableError

logger = logging.getLogger(__name__)


class CMSPhysicianFeeScheduleService(BaseAPIClient):
    """
    Service for the CMS Physician Fee Schedule public REST API.
    Returns RVU components and payment amounts for CPT/HCPCS codes.
    """

    def __init__(self, db):
        super().__init__(
            api_name="cms_pfs",
            base_url=CMS_PFS_BASE_URL,
            db=db,
            ttl_days=CMS_PFS_CACHE_TTL_DAYS,
        )

    def get_code_info(self, hcpcs_code: str, year: int = None) -> dict:
        """
        Get fee schedule information for a specific CPT or HCPCS code.

        Parameters
        ----------
        hcpcs_code : str
            The CPT or HCPCS code, e.g. "99214" or "G0439"
        year : int or None
            Fee schedule year. Defaults to CURRENT_FEE_SCHEDULE_YEAR from api_config.

        Returns
        -------
        dict with keys:
            hcpcs_code (str), description (str), work_rvu (float),
            non_facility_pe_rvu (float), mp_rvu (float),
            total_rvu_non_facility (float), non_facility_pricing_amount (float),
            facility_pricing_amount (float), status_code (str),
            is_payable (bool), _stale (bool)
        Returns empty dict if code not found.
        """
        if year is None:
            year = CURRENT_FEE_SCHEDULE_YEAR

        try:
            data = self._get(
                "",
                params={
                    "hcpcs_code": hcpcs_code.upper(),
                    "locality_number": CMS_LOCALITY_NUMBER,
                    "year": year,
                    "limit": 1,
                },
            )
            results = data.get("data") or data.get("results") or []
            if not results:
                return {}
            return self._parse_pfs_record(results[0], data.get("_stale", False))

        except APIUnavailableError:
            logger.warning(f"CMS PFS unavailable for code: {hcpcs_code}")
            return {}

    def get_multiple_codes(self, hcpcs_codes: list, year: int = None) -> dict:
        """
        Get fee schedule information for multiple codes.
        Used by the billing opportunity engine to price entire code stacks.

        Returns
        -------
        dict — keyed by HCPCS code, values are individual code info dicts.
        Missing codes (not found or API unavailable) are omitted.
        """
        results = {}
        for code in hcpcs_codes:
            info = self.get_code_info(code, year=year)
            if info:
                results[code] = info
        return results

    def calculate_estimated_revenue(self, hcpcs_codes: list, year: int = None) -> dict:
        """
        Calculate estimated total revenue for a set of CPT/HCPCS codes.
        Uses the CMS PFS API first; falls back to hardcoded estimates from
        api_config.py when the API is unavailable.

        Returns
        -------
        dict with keys:
            total_estimated (float) — sum of all non-facility payment amounts
            per_code (dict) — per-code payment amounts
            source (str) — "api" or "config_estimate"
            year (int) — fee schedule year used
        """
        code_data = self.get_multiple_codes(hcpcs_codes, year=year)

        total = 0.0
        per_code = {}

        for code in hcpcs_codes:
            if code in code_data:
                amount = code_data[code].get("non_facility_pricing_amount") or 0.0
                per_code[code] = amount
                total += amount
            else:
                # Fallback to hardcoded estimates from api_config.py
                estimate = _get_config_estimate(code)
                if estimate:
                    per_code[code] = estimate
                    total += estimate

        return {
            "total_estimated": round(total, 2),
            "per_code": per_code,
            "source": "api" if code_data else "config_estimate",
            "year": year or CURRENT_FEE_SCHEDULE_YEAR,
        }

    def _parse_pfs_record(self, record: dict, stale: bool = False) -> dict:
        """Parse a raw CMS PFS API record into a clean dict."""
        # CMS API returns strings for numeric values — convert to float
        def to_float(val):
            try:
                return float(str(val).replace(",", "")) if val else 0.0
            except (ValueError, TypeError):
                return 0.0

        status_code = record.get("status_code") or record.get("stat_cd") or ""
        return {
            "hcpcs_code": record.get("hcpcs_code") or record.get("hcpcs_cd", ""),
            "description": record.get("hcpcs_description") or record.get("mod_desc") or "",
            "work_rvu": to_float(record.get("work_rvu") or record.get("wrk_rvu")),
            "non_facility_pe_rvu": to_float(record.get("non_facility_pe_rvu") or record.get("nf_pe_rvu")),
            "mp_rvu": to_float(record.get("mp_rvu") or record.get("mal_rvu")),
            "total_rvu_non_facility": to_float(record.get("total_rvu_non_facility") or record.get("total_rvu")),
            "non_facility_pricing_amount": to_float(record.get("non_facility_pricing_amount") or record.get("nf_price")),
            "facility_pricing_amount": to_float(record.get("facility_pricing_amount") or record.get("fac_price")),
            "status_code": status_code,
            "is_payable": status_code.upper() in ("A", "R", "T"),  # Active, Restricted, Telemedicine
            "_stale": stale,
        }


def _get_config_estimate(hcpcs_code: str) -> float:
    """
    Fallback: return the hardcoded estimated rate from api_config.py when
    the CMS PFS API is unavailable or does not return a result for the code.
    """
    from app.api_config import (
        CCM_CODES, AWV_CODES, AWV_ADDON_CODES, TCM_CODES,
        EM_ADDON_CODES, BHI_CODES, RPM_CODES
    )
    all_code_dicts = [
        CCM_CODES, AWV_CODES, AWV_ADDON_CODES, TCM_CODES,
        EM_ADDON_CODES, BHI_CODES, RPM_CODES
    ]
    for code_dict in all_code_dicts:
        if hcpcs_code in code_dict:
            return code_dict[hcpcs_code].get("rate_est", 0.0)
    return 0.0

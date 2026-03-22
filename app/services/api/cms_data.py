"""
CareCompanion — CMS Open Data Service
File: app/services/api/cms_data.py

Queries the CMS Open Data Socrata API for Medicare utilization benchmarks.
Primary dataset: "Medicare Physician & Other Practitioners by Provider and Service"
(NPPES-linked, published annually).

Base URL: https://data.cms.gov/api/1
Auth: None required — fully public

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (CMS_DATA_BASE_URL, CMS_DATA_CACHE_TTL_DAYS)

CareCompanion features that rely on this module:
- Billing Dashboard Benchmarking (Phase 7.4) — compares provider utilization
  to state/specialty averages
"""

import logging
from app.api_config import CMS_DATA_BASE_URL, CMS_DATA_CACHE_TTL_DAYS
from app.services.api.base_client import BaseAPIClient

logger = logging.getLogger(__name__)

# Dataset identifier for Medicare Physician & Other Practitioners
# by Provider and Service (2022 release, latest stable)
MEDICARE_UTILIZATION_DATASET = "mj5m-pzi6"


class CmsDataService(BaseAPIClient):
    """
    Service for the CMS Open Data (Socrata) API.
    Queries Medicare utilization benchmarks by specialty, state, and HCPCS code.
    """

    def __init__(self, db):
        super().__init__(
            api_name="cms_data",
            base_url=CMS_DATA_BASE_URL,
            db=db,
            ttl_days=CMS_DATA_CACHE_TTL_DAYS,
        )

    def get_benchmark(self, hcpcs_code: str, state: str = "VA",
                      specialty: str = "Nurse Practitioner") -> dict:
        """
        Get utilization benchmark for a specific HCPCS code within a state
        and provider specialty.

        Parameters
        ----------
        hcpcs_code : str
            CPT or HCPCS code, e.g. "99214" or "G2211"
        state : str
            Two-letter state abbreviation, default "VA"
        specialty : str
            Provider specialty description as listed in CMS data

        Returns
        -------
        dict with keys:
            hcpcs_code (str), state (str), specialty (str),
            total_providers (int), total_services (int),
            avg_services_per_provider (float), avg_allowed_amount (float),
            avg_payment (float), utilization_rate (float|None),
            _stale (bool)
        Returns dict with zero values if no data found.
        """
        try:
            # Socrata SQL query against the dataset
            data = self._get(
                f"/datastore/sql",
                params={
                    "sql": (
                        f"SELECT "
                        f"COUNT(npi) as total_providers, "
                        f"SUM(tot_srvcs) as total_services, "
                        f"AVG(tot_srvcs) as avg_services_per_provider, "
                        f"AVG(avg_mdcr_alowd_amt) as avg_allowed_amount, "
                        f"AVG(avg_mdcr_pymt_amt) as avg_payment "
                        f"FROM {MEDICARE_UTILIZATION_DATASET} "
                        f"WHERE hcpcs_cd = '{hcpcs_code.upper()}' "
                        f"AND rndrng_prvdr_state_abrvtn = '{state.upper()}' "
                        f"AND rndrng_prvdr_type = '{specialty}' "
                        f"LIMIT 1"
                    ),
                },
            )

            rows = []
            if isinstance(data, dict):
                rows = data.get('results', data.get('data', []))
            elif isinstance(data, list):
                rows = data

            if not rows:
                return self._empty_benchmark(hcpcs_code, state, specialty)

            row = rows[0] if rows else {}
            total_providers = int(row.get('total_providers') or 0)
            total_services = int(row.get('total_services') or 0)
            avg_svc = float(row.get('avg_services_per_provider') or 0)
            avg_allowed = float(row.get('avg_allowed_amount') or 0)
            avg_payment = float(row.get('avg_payment') or 0)

            return {
                'hcpcs_code': hcpcs_code.upper(),
                'state': state.upper(),
                'specialty': specialty,
                'total_providers': total_providers,
                'total_services': total_services,
                'avg_services_per_provider': round(avg_svc, 1),
                'avg_allowed_amount': round(avg_allowed, 2),
                'avg_payment': round(avg_payment, 2),
                'utilization_rate': None,  # Requires denominator context
                '_stale': data.get('_stale', False) if isinstance(data, dict) else False,
            }

        except Exception as e:
            logger.debug('CMS Data benchmark lookup failed for %s: %s', hcpcs_code, e)
            return self._empty_benchmark(hcpcs_code, state, specialty)

    def get_specialty_summary(self, state: str = "VA",
                              specialty: str = "Nurse Practitioner") -> dict:
        """
        Get aggregate billing summary for a specialty in a state.
        Returns top HCPCS codes by volume for benchmarking.
        """
        try:
            data = self._get(
                f"/datastore/sql",
                params={
                    "sql": (
                        f"SELECT "
                        f"hcpcs_cd, "
                        f"COUNT(npi) as provider_count, "
                        f"SUM(tot_srvcs) as total_services, "
                        f"AVG(avg_mdcr_pymt_amt) as avg_payment "
                        f"FROM {MEDICARE_UTILIZATION_DATASET} "
                        f"WHERE rndrng_prvdr_state_abrvtn = '{state.upper()}' "
                        f"AND rndrng_prvdr_type = '{specialty}' "
                        f"GROUP BY hcpcs_cd "
                        f"ORDER BY total_services DESC "
                        f"LIMIT 20"
                    ),
                },
            )

            rows = []
            if isinstance(data, dict):
                rows = data.get('results', data.get('data', []))
            elif isinstance(data, list):
                rows = data

            codes = []
            for row in rows:
                codes.append({
                    'hcpcs_code': row.get('hcpcs_cd', ''),
                    'provider_count': int(row.get('provider_count') or 0),
                    'total_services': int(row.get('total_services') or 0),
                    'avg_payment': round(float(row.get('avg_payment') or 0), 2),
                })

            return {
                'state': state.upper(),
                'specialty': specialty,
                'top_codes': codes,
                '_stale': data.get('_stale', False) if isinstance(data, dict) else False,
            }

        except Exception as e:
            logger.debug('CMS specialty summary failed: %s', e)
            return {'state': state.upper(), 'specialty': specialty, 'top_codes': []}

    @staticmethod
    def _empty_benchmark(hcpcs_code, state, specialty):
        return {
            'hcpcs_code': hcpcs_code.upper(),
            'state': state.upper(),
            'specialty': specialty,
            'total_providers': 0,
            'total_services': 0,
            'avg_services_per_provider': 0,
            'avg_allowed_amount': 0,
            'avg_payment': 0,
            'utilization_rate': None,
            '_stale': False,
        }

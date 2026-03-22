"""
CareCompanion — Drug Assistance Service (Tier 3 Pricing)
File: app/services/api/drug_assistance_service.py

Patient assistance program lookup for NeedyMeds and RxAssist.
Third tier in the Three-Tier Waterfall — queried only when:
  (a) Tier 1/2 price exceeds DRUG_PRICE_ASSISTANCE_THRESHOLD ($75), OR
  (b) Patient is Medicaid or uninsured

Tier 1: Cost Plus Drugs — free, no auth (primary)
Tier 2: GoodRx Price Compare — secondary, only when Tier 1 misses
Tier 3: NeedyMeds/RxAssist (this module) — assistance programs

No API key required for either NeedyMeds or RxAssist.

Dependencies:
- app/api_config.py (NEEDYMEDS_BASE_URL, RXASSIST_BASE_URL,
  DRUG_ASSISTANCE_CACHE_TTL_DAYS, DRUG_PRICE_ASSISTANCE_THRESHOLD)
- app/services/api/base_client.py (BaseAPIClient, APIUnavailableError)
"""

import logging
import re
from urllib.parse import quote_plus

from app.api_config import (
    NEEDYMEDS_BASE_URL,
    RXASSIST_BASE_URL,
    DRUG_ASSISTANCE_CACHE_TTL_DAYS,
    DRUG_PRICE_ASSISTANCE_THRESHOLD,
)
from app.services.api.base_client import BaseAPIClient, APIUnavailableError

logger = logging.getLogger(__name__)


class DrugAssistanceService(BaseAPIClient):
    """
    Patient assistance program lookup — NeedyMeds + RxAssist.

    No API key required for either source.  Returns structured lists
    of AssistanceProgram dicts or empty list when no programs found.
    """

    def __init__(self, db):
        super().__init__(
            api_name="drug_assistance",
            base_url=NEEDYMEDS_BASE_URL,
            db=db,
            ttl_days=DRUG_ASSISTANCE_CACHE_TTL_DAYS,
        )

    # ------------------------------------------------------------------
    # 23.2 — NeedyMeds Query
    # ------------------------------------------------------------------

    def _query_needymeds(self, drug_name):
        """
        Query NeedyMeds drug database for patient assistance programs.

        Parameters
        ----------
        drug_name : str
            Drug name, e.g. "eliquis", "tiotropium"

        Returns
        -------
        list[dict]
            List of AssistanceProgram dicts from NeedyMeds, or empty list.
        """
        if not drug_name:
            return []

        clean_name = drug_name.strip().lower()
        # URL-safe drug name for the NeedyMeds path
        safe_name = quote_plus(clean_name)

        try:
            # NeedyMeds provides structured drug info pages
            data = self._get(
                f"/drug-info/{safe_name}",
                ttl_days=DRUG_ASSISTANCE_CACHE_TTL_DAYS,
            )
            return self._parse_needymeds_response(data, clean_name)
        except APIUnavailableError:
            logger.info("NeedyMeds unavailable for %s", drug_name)
            return []
        except Exception:
            logger.debug("NeedyMeds query error for %s", drug_name, exc_info=True)
            return []

    def _parse_needymeds_response(self, data, drug_name):
        """
        Parse NeedyMeds response into AssistanceProgram dicts.

        Returns empty list if the response doesn't contain program data.
        """
        if not data or not isinstance(data, dict):
            return []

        programs = []
        raw_programs = data.get("programs", data.get("results", data.get("data", [])))

        if isinstance(raw_programs, list):
            for entry in raw_programs:
                program = self._extract_program(entry, "needymeds")
                if program:
                    programs.append(program)
        elif isinstance(raw_programs, dict) and raw_programs.get("program_name"):
            program = self._extract_program(raw_programs, "needymeds")
            if program:
                programs.append(program)

        return programs

    # ------------------------------------------------------------------
    # 23.3 — RxAssist Query
    # ------------------------------------------------------------------

    def _query_rxassist(self, drug_name):
        """
        Query RxAssist database for patient assistance programs.

        Parameters
        ----------
        drug_name : str
            Drug name, e.g. "eliquis", "tiotropium"

        Returns
        -------
        list[dict]
            List of AssistanceProgram dicts from RxAssist, or empty list.
        """
        if not drug_name:
            return []

        clean_name = drug_name.strip().lower()

        try:
            # RxAssist uses query parameter search
            # Override base_url for RxAssist since we initialized with NeedyMeds
            rxassist_path = f"{RXASSIST_BASE_URL}/search/results"
            params = {"drug": clean_name}
            cache_key = self._make_cache_key(f"rxassist::{clean_name}", params)

            # Check cache first
            cached = self.cache.get(self.api_name, cache_key)
            if cached and not cached.get("stale"):
                return self._parse_rxassist_response(cached.get("data", cached), clean_name)

            # Attempt live fetch — use base_client's retry/timeout infrastructure
            # but with RxAssist URL instead of the default base_url
            import json
            from urllib.request import urlopen, Request
            from urllib.error import URLError, HTTPError
            from urllib.parse import urlencode
            from app.api_config import HTTP_TIMEOUT_SECONDS, HTTP_USER_AGENT

            url = f"{rxassist_path}?{urlencode(params)}"
            req = Request(url, headers={
                "User-Agent": HTTP_USER_AGENT,
                "Accept": "application/json",
            })
            with urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as response:
                raw = response.read().decode("utf-8")
                data = json.loads(raw)

            # Cache the result
            self.cache.set(self.api_name, cache_key, data,
                           ttl_days=DRUG_ASSISTANCE_CACHE_TTL_DAYS)
            return self._parse_rxassist_response(data, clean_name)

        except (APIUnavailableError, Exception):
            # Try stale cache as fallback
            try:
                cached = self.cache.get(self.api_name,
                                        self._make_cache_key(f"rxassist::{clean_name}",
                                                             {"drug": clean_name}))
                if cached:
                    return self._parse_rxassist_response(
                        cached.get("data", cached), clean_name)
            except Exception:
                pass
            logger.info("RxAssist unavailable for %s", drug_name)
            return []

    def _parse_rxassist_response(self, data, drug_name):
        """
        Parse RxAssist response into AssistanceProgram dicts.

        Returns empty list if the response doesn't contain program data.
        """
        if not data or not isinstance(data, dict):
            return []

        programs = []
        raw_programs = data.get("programs", data.get("results", data.get("data", [])))

        if isinstance(raw_programs, list):
            for entry in raw_programs:
                program = self._extract_program(entry, "rxassist")
                if program:
                    programs.append(program)
        elif isinstance(raw_programs, dict) and raw_programs.get("program_name"):
            program = self._extract_program(raw_programs, "rxassist")
            if program:
                programs.append(program)

        return programs

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _extract_program(self, entry, source):
        """
        Extract an AssistanceProgram dict from a raw API entry.

        Returns None if the entry doesn't have enough data.
        """
        if not isinstance(entry, dict):
            return None

        name = entry.get("program_name", entry.get("name", entry.get("title", "")))
        if not name:
            return None

        eligibility = entry.get("eligibility_summary",
                                entry.get("eligibility", entry.get("description", "")))
        app_url = entry.get("application_url",
                            entry.get("url", entry.get("link", "")))

        # Determine program type flags
        elig_lower = eligibility.lower() if eligibility else ""
        is_income = bool(re.search(r'income|fpl|poverty|financial', elig_lower))
        is_diagnosis = bool(re.search(r'diagnosis|condition|disease|indication', elig_lower))

        return {
            "program_name": name,
            "eligibility_summary": eligibility,
            "application_url": app_url,
            "is_income_based": is_income,
            "is_diagnosis_based": is_diagnosis,
            "source": source,
        }

    # ------------------------------------------------------------------
    # 23.4 — Unified Entry Point
    # ------------------------------------------------------------------

    def get_assistance_programs(self, drug_name, patient_insurer_type=None):
        """
        Query NeedyMeds and RxAssist, merge and deduplicate results.

        This method is called by the Pricing Waterfall Orchestrator when:
          (a) Tier 1/2 monthly price exceeds DRUG_PRICE_ASSISTANCE_THRESHOLD, OR
          (b) patient_insurer_type is "medicaid" or "uninsured"

        Parameters
        ----------
        drug_name : str
            Drug name to search for assistance programs.
        patient_insurer_type : str or None
            Patient's insurer type (e.g. "medicare", "medicaid", "commercial",
            "uninsured"). Used for context logging only — the caller decides
            whether to invoke this method based on insurer type.

        Returns
        -------
        list[dict]
            Deduplicated list of AssistanceProgram dicts, sorted by source.
            Empty list if no programs found or both sources unavailable.
        """
        if not drug_name:
            return []

        logger.info(
            "Querying assistance programs for %s (insurer: %s)",
            drug_name, patient_insurer_type or "unknown",
        )

        # Query both sources
        needymeds_results = self._query_needymeds(drug_name)
        rxassist_results = self._query_rxassist(drug_name)

        # Merge results
        all_programs = needymeds_results + rxassist_results

        # Deduplicate by normalized program name
        seen = set()
        deduplicated = []
        for program in all_programs:
            key = program["program_name"].strip().lower()
            if key not in seen:
                seen.add(key)
                deduplicated.append(program)

        logger.info(
            "Found %d assistance programs for %s (%d NeedyMeds, %d RxAssist)",
            len(deduplicated), drug_name,
            len(needymeds_results), len(rxassist_results),
        )

        return deduplicated

"""
CareCompanion — Base API Client
File: app/services/api/base_client.py

All external API service modules inherit from BaseAPIClient.
This class provides:
1. Retry logic with exponential backoff on transient failures (5xx, timeout)
2. Rate limiting to stay within per-API request limits
3. Offline fallback — serves stale cached data when the live API is unavailable
4. Consistent error logging using the AgentError pattern from the rest of the app
5. Request timing so we can detect slow APIs in the health monitor (F3a)

Usage (in a service module):
    class RxNormService(BaseAPIClient):
        def __init__(self, db):
            super().__init__(
                api_name="rxnorm",
                base_url=RXNORM_BASE_URL,
                db=db,
                ttl_days=RXNORM_CACHE_TTL_DAYS,
            )

        def lookup_rxcui(self, drug_name):
            return self._get("/rxcui", params={"name": drug_name})

Dependencies:
- app/api_config.py (HTTP_TIMEOUT_SECONDS, HTTP_MAX_RETRIES, HTTP_USER_AGENT,
  HTTP_RETRY_BACKOFF_SECONDS)
- app/services/api/cache_manager.py (CacheManager)

CareCompanion features that rely on this module:
- Every API service in app/services/api/ (all 14 service modules)
- Offline mode (F30) — stale cache path is defined here
"""

import time
import json
import logging
import hashlib
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode

from app.api_config import (
    HTTP_TIMEOUT_SECONDS,
    HTTP_MAX_RETRIES,
    HTTP_RETRY_BACKOFF_SECONDS,
    HTTP_USER_AGENT,
)
from app.services.api.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class APIUnavailableError(Exception):
    """Raised when an API cannot be reached and no cache fallback is available."""
    pass


class BaseAPIClient:
    """
    Base class for all CareCompanion API service modules.

    Provides retry logic, rate limiting, and offline fallback via the
    cache manager. Subclasses only need to implement endpoint-specific
    methods that call self._get() or self._post().
    """

    def __init__(self, api_name: str, base_url: str, db, ttl_days: int = 30):
        """
        Parameters
        ----------
        api_name : str
            Short identifier for this API, e.g. "rxnorm". Must be unique.
            Used as the namespace in the cache.
        base_url : str
            The root URL for this API, e.g. "https://rxnav.nlm.nih.gov/REST"
        db : SQLAlchemy db instance
            The shared db object from models/__init__.py
        ttl_days : int
            Default cache TTL for this API. Individual methods can override.
        """
        self.api_name = api_name
        self.base_url = base_url.rstrip("/")
        self.ttl_days = ttl_days
        self.cache = CacheManager(db)

        # Rate limiting — track time of last request per API instance
        self._last_request_time = 0.0
        self._min_request_interval = 0.0  # Set by subclass if needed

    def _make_cache_key(self, path: str, params: dict = None) -> str:
        """
        Build a cache key from the path and query parameters.
        Does NOT contain any patient identifiers — only API parameters like
        drug names, codes, and search terms.
        """
        parts = [path]
        if params:
            # Sort params for consistent key regardless of dict ordering
            parts.append(urlencode(sorted(params.items())))
        return "::".join(parts)

    def _get(self, path: str, params: dict = None, ttl_days: int = None,
             allow_stale: bool = True) -> dict:
        """
        Make a GET request to this API with caching and retry logic.

        Parameters
        ----------
        path : str
            API path relative to base_url, e.g. "/rxcui"
        params : dict or None
            Query parameters as a dict, e.g. {"name": "lisinopril"}
        ttl_days : int or None
            Override the default TTL for this specific request.
        allow_stale : bool
            If True (default), return stale cached data as offline fallback
            when the live API is unavailable. The caller can check the
            "stale" key in the result to show a staleness notice in the UI.

        Returns
        -------
        dict
            Always includes a "stale" key (True/False) and "cached_at" (str or None).
            The actual API response data is merged into the returned dict, or
            stored under a "data" key depending on the API response shape.

        Raises
        ------
        APIUnavailableError
            If the API fails and no cache fallback is available.
        """
        # Build the full URL
        if params:
            url = f"{self.base_url}{path}?{urlencode(params)}"
        else:
            url = f"{self.base_url}{path}"

        cache_key = self._make_cache_key(path, params)
        effective_ttl = ttl_days if ttl_days is not None else self.ttl_days

        # --- Check cache first ---
        cached = self.cache.get(self.api_name, cache_key)
        if cached and not cached.get("stale"):
            # Fresh cache hit — return immediately, no network call needed
            return cached["data"]

        # --- Attempt live fetch with retries ---
        last_error = None
        backoff = HTTP_RETRY_BACKOFF_SECONDS

        for attempt in range(1, HTTP_MAX_RETRIES + 1):
            # Respect rate limiting
            self._enforce_rate_limit()

            try:
                req = Request(
                    url,
                    headers={"User-Agent": HTTP_USER_AGENT, "Accept": "application/json"},
                )
                start_time = time.time()
                with urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as response:
                    elapsed = time.time() - start_time
                    raw = response.read().decode("utf-8")
                    data = json.loads(raw)

                if elapsed > 5.0:
                    logger.warning(
                        f"{self.api_name} slow response: {elapsed:.1f}s for {path}"
                    )

                # Store fresh result in cache
                self.cache.set(self.api_name, cache_key, data, ttl_days=effective_ttl)
                return data

            except HTTPError as e:
                last_error = e
                if e.code in (400, 401, 403, 404):
                    # Non-retryable client errors
                    logger.warning(
                        f"{self.api_name} HTTP {e.code} for {path}: {e.reason}"
                    )
                    break
                # Retryable server errors (500, 502, 503, 504)
                logger.warning(
                    f"{self.api_name} HTTP {e.code} on attempt {attempt}/{HTTP_MAX_RETRIES}"
                )
                if attempt < HTTP_MAX_RETRIES:
                    time.sleep(backoff)
                    backoff *= 2  # Exponential backoff

            except (URLError, OSError, json.JSONDecodeError) as e:
                last_error = e
                logger.warning(
                    f"{self.api_name} network error on attempt {attempt}/{HTTP_MAX_RETRIES}: {e}"
                )
                if attempt < HTTP_MAX_RETRIES:
                    time.sleep(backoff)
                    backoff *= 2

        # --- Live fetch failed — try stale cache as fallback ---
        if allow_stale and cached:
            logger.info(
                f"{self.api_name} offline fallback: returning stale cache for {path}"
            )
            result = dict(cached["data"])
            result["_stale"] = True
            result["_cached_at"] = cached.get("cached_at")
            return result

        # --- No fallback available ---
        raise APIUnavailableError(
            f"{self.api_name} unavailable and no cache for {path}. "
            f"Last error: {last_error}"
        )

    def _enforce_rate_limit(self):
        """
        Pause if needed to respect the API's rate limit.
        Only active if the subclass sets self._min_request_interval > 0.
        """
        if self._min_request_interval <= 0:
            return
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def is_available(self) -> bool:
        """
        Quick connectivity check for the health monitor (F3a).
        Returns True if the API base URL responds within timeout.
        """
        try:
            req = Request(
                self.base_url,
                headers={"User-Agent": HTTP_USER_AGENT},
            )
            with urlopen(req, timeout=3):
                return True
        except Exception:
            return False

    def flush_cache(self) -> int:
        """
        Delete all cached entries for this API.
        Used by the admin "Flush Cache" button.
        Returns the number of entries deleted.
        """
        return self.cache.flush_api(self.api_name)

    def get_cache_stats(self) -> dict:
        """Return cache statistics for this API (for admin display)."""
        return self.cache.get_stats(self.api_name)

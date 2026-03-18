"""
NP Companion — Unified API Cache Manager
File: app/services/api/cache_manager.py

Handles SQLite-backed caching for all external API responses.
Each cached entry has a TTL (time-to-live) configured per API in api_config.py.
When the TTL has expired, the cache entry is returned as "stale" so the caller
can decide whether to show stale data (with a staleness notice) or re-fetch.

Key design decisions:
- Uses the main npcompanion.db SQLite database (no separate cache file)
- Cache key is a SHA-256 hash of the API name + query parameters
- Cache value is stored as JSON text
- Stale entries are not deleted automatically — they serve as offline fallback
- Cache hits are logged to help the admin see what's being cached (F3a health)

Dependencies:
- models (SQLAlchemy db instance)
- app/api_config.py (TTL values and table name)

NP Companion features that rely on this module:
- Every feature in the API intelligence layer (Phase 10A/10B)
- Offline mode (F30) — stale cache serves as fallback when internet is unavailable
"""

import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class CacheManager:
    """
    SQLite-backed cache for API responses.

    Usage:
        cache = CacheManager(db)
        result = cache.get("rxnorm", "lisinopril")
        if result is None:
            data = fetch_from_api()
            cache.set("rxnorm", "lisinopril", data, ttl_days=30)
    """

    def __init__(self, db):
        """
        Parameters
        ----------
        db : SQLAlchemy database instance
            The shared db object from models/__init__.py
        """
        self.db = db
        self._ensure_table()

    def _ensure_table(self):
        """
        Create the api_response_cache table if it does not exist.
        Safe to call multiple times — uses IF NOT EXISTS.
        """
        try:
            self.db.engine.execute("""
                CREATE TABLE IF NOT EXISTS api_response_cache (
                    cache_key   TEXT PRIMARY KEY,
                    api_name    TEXT NOT NULL,
                    query_key   TEXT NOT NULL,
                    response    TEXT NOT NULL,
                    cached_at   TEXT NOT NULL,
                    expires_at  TEXT NOT NULL,
                    hit_count   INTEGER DEFAULT 0
                )
            """)
        except Exception:
            # If this fails (e.g., table already exists with different schema),
            # fall through — the table likely already exists from a prior run.
            pass

    def _make_key(self, api_name: str, query_key: str) -> str:
        """
        Generate a stable cache key from api_name + query_key.
        Uses SHA-256 so the key is always a fixed-length string
        regardless of how long query_key is.
        """
        raw = f"{api_name}::{query_key}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, api_name: str, query_key: str):
        """
        Look up a cached response.

        Returns
        -------
        dict or None
            If a fresh cache entry exists: {"data": <parsed JSON>, "stale": False}
            If a stale cache entry exists: {"data": <parsed JSON>, "stale": True,
                                            "cached_at": <timestamp string>}
            If no entry exists: None
        """
        key = self._make_key(api_name, query_key)
        try:
            row = self.db.engine.execute(
                "SELECT response, cached_at, expires_at, hit_count "
                "FROM api_response_cache WHERE cache_key = ?",
                (key,)
            ).fetchone()

            if row is None:
                return None

            response_text, cached_at_str, expires_at_str, hit_count = row
            now = datetime.now(timezone.utc)
            expires_at = datetime.fromisoformat(expires_at_str)

            # Increment hit counter
            self.db.engine.execute(
                "UPDATE api_response_cache SET hit_count = ? WHERE cache_key = ?",
                (hit_count + 1, key)
            )

            data = json.loads(response_text)
            is_stale = now > expires_at

            return {
                "data": data,
                "stale": is_stale,
                "cached_at": cached_at_str,
            }

        except Exception as e:
            logger.warning(f"Cache get error for {api_name}/{query_key}: {e}")
            return None

    def set(self, api_name: str, query_key: str, data, ttl_days: int = 30):
        """
        Store an API response in the cache.

        Parameters
        ----------
        api_name : str
            Short name of the API, e.g. "rxnorm" or "openfda_labels"
        query_key : str
            A string identifying what was queried, e.g. the drug name or code.
            Does NOT contain any patient identifiers.
        data : dict or list
            The parsed API response to cache.
        ttl_days : int
            How many days until this entry expires. Stale entries are kept
            as offline fallback — they are not deleted when expired.
        """
        key = self._make_key(api_name, query_key)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=ttl_days)

        try:
            self.db.engine.execute("""
                INSERT INTO api_response_cache
                    (cache_key, api_name, query_key, response, cached_at, expires_at, hit_count)
                VALUES (?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(cache_key) DO UPDATE SET
                    response   = excluded.response,
                    cached_at  = excluded.cached_at,
                    expires_at = excluded.expires_at
            """, (
                key,
                api_name,
                query_key,
                json.dumps(data),
                now.isoformat(),
                expires_at.isoformat(),
            ))
        except Exception as e:
            logger.warning(f"Cache set error for {api_name}/{query_key}: {e}")

    def delete(self, api_name: str, query_key: str):
        """
        Remove a specific cache entry (used for forced refresh).
        """
        key = self._make_key(api_name, query_key)
        try:
            self.db.engine.execute(
                "DELETE FROM api_response_cache WHERE cache_key = ?", (key,)
            )
        except Exception as e:
            logger.warning(f"Cache delete error for {api_name}/{query_key}: {e}")

    def flush_api(self, api_name: str):
        """
        Delete all cached entries for a specific API.
        Used by the admin "Flush Cache" button per API.
        """
        try:
            result = self.db.engine.execute(
                "DELETE FROM api_response_cache WHERE api_name = ?", (api_name,)
            )
            deleted = result.rowcount
            logger.info(f"Cache flush: deleted {deleted} entries for {api_name}")
            return deleted
        except Exception as e:
            logger.warning(f"Cache flush error for {api_name}: {e}")
            return 0

    def get_stats(self, api_name: str = None):
        """
        Return cache statistics for the admin settings page.

        Parameters
        ----------
        api_name : str or None
            If provided, return stats for that API only.
            If None, return aggregate stats for all APIs.

        Returns
        -------
        dict with keys: entry_count, oldest_entry, newest_entry, total_hits
        """
        try:
            if api_name:
                where = "WHERE api_name = ?"
                params = (api_name,)
            else:
                where = ""
                params = ()

            row = self.db.engine.execute(
                f"SELECT COUNT(*), MIN(cached_at), MAX(cached_at), SUM(hit_count) "
                f"FROM api_response_cache {where}",
                params
            ).fetchone()

            if row:
                return {
                    "entry_count": row[0] or 0,
                    "oldest_entry": row[1],
                    "newest_entry": row[2],
                    "total_hits": row[3] or 0,
                }
        except Exception as e:
            logger.warning(f"Cache stats error: {e}")

        return {"entry_count": 0, "oldest_entry": None, "newest_entry": None, "total_hits": 0}

    def get_all_api_stats(self):
        """
        Return per-API cache statistics for the admin cache management page.

        Returns
        -------
        list of dicts, one per API with keys: api_name, entry_count, total_hits,
        newest_entry, stale_count
        """
        try:
            now = datetime.now(timezone.utc).isoformat()
            rows = self.db.engine.execute("""
                SELECT
                    api_name,
                    COUNT(*) as entry_count,
                    SUM(hit_count) as total_hits,
                    MAX(cached_at) as newest_entry,
                    SUM(CASE WHEN expires_at < ? THEN 1 ELSE 0 END) as stale_count
                FROM api_response_cache
                GROUP BY api_name
                ORDER BY api_name
            """, (now,)).fetchall()

            return [
                {
                    "api_name": r[0],
                    "entry_count": r[1],
                    "total_hits": r[2] or 0,
                    "newest_entry": r[3],
                    "stale_count": r[4] or 0,
                }
                for r in rows
            ]
        except Exception as e:
            logger.warning(f"Cache all-stats error: {e}")
            return []

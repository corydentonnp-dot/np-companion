"""
NP Companion — NCBI PubMed Literature Search Service
File: app/services/api/pubmed.py

Programmatic access to PubMed's 35+ million biomedical citations.
Pre-loads recent guideline articles for scheduled patients' top diagnoses
so the provider sees relevant literature when opening a patient chart.

Base URL: https://eutils.ncbi.nlm.nih.gov/entrez/eutils
Auth: Free API key recommended for higher rate limits
Register at: https://www.ncbi.nlm.nih.gov/account/

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (PUBMED_BASE_URL, PUBMED_CACHE_TTL_DAYS,
  PUBMED_MAX_RESULTS, PUBMED_LOOKBACK_YEARS)

NP Companion features that rely on this module:
- Guideline Lookup Panel (Feature C from API intelligence plan)
- Pre-visit note prep — evidence-based pre-loading for scheduled patients
- Morning Briefing — guideline freshness checking
"""

import logging
from datetime import datetime, timezone
from app.api_config import (
    PUBMED_BASE_URL,
    PUBMED_CACHE_TTL_DAYS,
    PUBMED_MAX_RESULTS,
    PUBMED_LOOKBACK_YEARS,
)
from app.services.api.base_client import BaseAPIClient, APIUnavailableError

logger = logging.getLogger(__name__)

# High-impact primary care journals — articles from these get a badge in the UI
PRIMARY_CARE_JOURNALS = {
    "N Engl J Med", "JAMA", "BMJ", "Lancet",
    "Ann Intern Med", "JAMA Intern Med",
    "Am Fam Physician", "J Am Board Fam Med",
    "Ann Fam Med", "Fam Pract",
}


class PubMedService(BaseAPIClient):
    """
    Service for the NCBI E-utilities API (PubMed).
    """

    def __init__(self, db, api_key: str = None):
        """
        Parameters
        ----------
        api_key : str or None
            NCBI API key (optional, but increases rate limits from 3 to 10 req/sec)
        """
        super().__init__(
            api_name="pubmed",
            base_url=PUBMED_BASE_URL,
            db=db,
            ttl_days=PUBMED_CACHE_TTL_DAYS,
        )
        self._api_key = api_key
        # Default min interval between requests (conservative for no-key mode)
        self._min_request_interval = 0.4 if not api_key else 0.1

    def search_guidelines(self, condition: str, max_results: int = None) -> list:
        """
        Search PubMed for recent clinical guidelines and systematic reviews
        for a given condition. Results are cached for PUBMED_CACHE_TTL_DAYS.

        Parameters
        ----------
        condition : str
            Clinical condition to search, e.g. "type 2 diabetes" or "hypertension"
        max_results : int or None
            Override default max results from api_config

        Returns
        -------
        list of dicts, each representing one article:
            pmid (str), title (str), journal (str), year (int),
            abstract (str) — first 300 chars, authors (str),
            doi (str or None), is_primary_care_journal (bool), _stale (bool)
        """
        limit = max_results or PUBMED_MAX_RESULTS
        lookback_year = datetime.now(timezone.utc).year - PUBMED_LOOKBACK_YEARS

        try:
            # Phase 1: Search for PMIDs
            search_data = self._get(
                "/esearch.fcgi",
                params={
                    "db": "pubmed",
                    "term": (
                        f"{condition}[title/abstract] AND "
                        f"({lookback_year}:{datetime.now().year}[pdat]) AND "
                        "(guideline[pt] OR \"systematic review\"[pt] OR "
                        "\"clinical practice\"[ti] OR \"meta-analysis\"[pt])"
                    ),
                    "retmax": limit,
                    "sort": "pub date",
                    "retmode": "json",
                    **({"api_key": self._api_key} if self._api_key else {}),
                },
            )

            pmids = (
                search_data.get("esearchresult", {}).get("idlist") or []
            )
            if not pmids:
                return []

            # Phase 2: Fetch abstracts for found PMIDs
            fetch_data = self._get(
                "/esummary.fcgi",
                params={
                    "db": "pubmed",
                    "id": ",".join(pmids),
                    "retmode": "json",
                    **({"api_key": self._api_key} if self._api_key else {}),
                },
            )
            return self._parse_summaries(fetch_data, search_data.get("_stale", False))

        except APIUnavailableError:
            logger.warning(f"PubMed unavailable for condition: {condition}")
            return []

    def _parse_summaries(self, data: dict, stale: bool = False) -> list:
        """Parse eSummary JSON response into article records."""
        result_map = data.get("result") or {}
        uids = result_map.get("uids") or []
        articles = []

        for uid in uids:
            article = result_map.get(uid) or {}
            if not article:
                continue

            journal = article.get("fulljournalname") or article.get("source") or ""
            pub_date = article.get("pubdate") or ""
            year = int(pub_date[:4]) if pub_date and len(pub_date) >= 4 else 0

            # Get authors as "Last FM, Last2 FM2"
            author_list = article.get("authors") or []
            authors = ", ".join(
                a.get("name") for a in author_list[:3] if a.get("name")
            )
            if len(author_list) > 3:
                authors += " et al."

            # Extract DOI from articleids
            doi = None
            for aid in (article.get("articleids") or []):
                if aid.get("idtype") == "doi":
                    doi = aid.get("value")
                    break

            articles.append({
                "pmid": uid,
                "title": article.get("title") or "",
                "journal": journal,
                "year": year,
                "abstract": article.get("sorttitle") or "",  # eSummary doesn't include full abstract
                "authors": authors,
                "doi": doi,
                "is_primary_care_journal": any(
                    j.lower() in journal.lower() for j in PRIMARY_CARE_JOURNALS
                ),
                "_stale": stale,
            })

        return articles

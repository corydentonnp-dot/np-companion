"""
NP Companion — AHRQ HealthFinder Preventive Care Service
File: app/services/api/healthfinder.py

Returns USPSTF-aligned preventive care recommendations personalized to
a patient's age, sex, and pregnancy status. This is the US government's
official USPSTF recommendation engine as a queryable API.

Base URL: https://health.gov/myhealthfinder/api/v3
Auth: None required

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (HEALTHFINDER_BASE_URL, HEALTHFINDER_CACHE_TTL_DAYS)

NP Companion features that rely on this module:
- Care Gap Tracker (F15) — replaces all hardcoded USPSTF rules
- Care gap auto-population (F15a) — evaluates gaps on schedule pull
- Panel-wide gap report (F15c) — consistent recommendation definitions
- Billing capture suggestions (F16) — linked via recommendation category
- Morning Briefing (F22) — "N care gaps for today's patients"
- Today View — care gap badges per patient
"""

import logging
from app.api_config import HEALTHFINDER_BASE_URL, HEALTHFINDER_CACHE_TTL_DAYS
from app.services.api.base_client import BaseAPIClient, APIUnavailableError

logger = logging.getLogger(__name__)


class HealthFinderService(BaseAPIClient):
    """
    Service for the AHRQ MyHealthFinder API (USPSTF recommendations).
    """

    def __init__(self, db):
        super().__init__(
            api_name="healthfinder",
            base_url=HEALTHFINDER_BASE_URL,
            db=db,
            ttl_days=HEALTHFINDER_CACHE_TTL_DAYS,
        )

    def get_recommendations(self, age: int, sex: str, pregnant: bool = False) -> list:
        """
        Get all USPSTF preventive care recommendations for a patient's demographics.

        Parameters
        ----------
        age : int
            Patient age in years
        sex : str
            "M" or "F" (as stored in PatientRecord)
        pregnant : bool
            Whether the patient is currently pregnant (default False)

        Returns
        -------
        list of dicts, each representing one recommendation:
            title (str) — short recommendation name
            category (str) — "Screening", "Counseling", or "Preventive Medication"
            grade (str) — USPSTF grade: "A", "B", "C", "D", or "I"
            description (str) — brief recommendation description
            frequency (str) — how often the service is recommended
            topics (list) — related topic tags
            _stale (bool)
        """
        try:
            # HealthFinder uses "male" / "female" not M/F
            sex_param = "male" if sex.upper() == "M" else "female"
            data = self._get(
                "/topicsearch.json",
                params={
                    "lang": "en",
                    "age": age,
                    "sex": sex_param,
                    "pregnant": 1 if pregnant else 0,
                },
            )
            return self._parse_recommendations(data)
        except APIUnavailableError:
            logger.warning(f"HealthFinder unavailable for age={age}, sex={sex}")
            return []

    def _parse_recommendations(self, data: dict) -> list:
        """
        Parse HealthFinder API response into structured recommendations.
        """
        if not data:
            return []

        # HealthFinder response structure varies by version
        # Try multiple paths to find the topics list
        topics = (
            data.get("Result", {}).get("Resources", {}).get("Resource") or
            data.get("resources", {}).get("resource") or
            []
        )

        recommendations = []
        for topic in topics:
            if not isinstance(topic, dict):
                continue

            # Extract grade information if present
            sections = topic.get("Sections", {}).get("section") or []
            grade = "B"  # Default to Grade B if not specified
            description = ""
            frequency = ""

            for section in sections:
                if isinstance(section, dict):
                    section_title = section.get("Title") or ""
                    section_content = section.get("Content") or ""
                    if "grade" in section_title.lower():
                        grade = _extract_grade(section_content)
                    if "how often" in section_title.lower() or "frequency" in section_title.lower():
                        frequency = section_content[:200]
                    if not description and section_content:
                        description = section_content[:300]

            recommendations.append({
                "title": topic.get("Title") or topic.get("title") or "",
                "category": topic.get("Categories", {}).get("Category") or "Screening",
                "grade": grade,
                "description": description,
                "frequency": frequency,
                "topics": topic.get("MyHFTopics", {}).get("MyHFTopic") or [],
                "_stale": data.get("_stale", False),
            })

        return recommendations


def _extract_grade(text: str) -> str:
    """
    Extract USPSTF grade letter from text.
    Returns "A", "B", "C", "D", or "I" (insufficient evidence).
    """
    if not text:
        return "B"
    text_upper = text.upper()
    for grade in ["A", "B", "C", "D"]:
        if f"GRADE {grade}" in text_upper or f"GRADE: {grade}" in text_upper:
            return grade
    return "B"  # Default

"""
NP Companion — Open-Meteo Weather Service
File: app/services/api/open_meteo.py

Returns current weather and precipitation probability for the morning briefing.
No registration, no API key, completely free.

Base URL: https://api.open-meteo.com/v1
Auth: None required
Rate limit: 10,000 requests/day (free tier)

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (OPEN_METEO_BASE_URL, OPEN_METEO_CACHE_TTL_HOURS,
  DEFAULT_CLINIC_LATITUDE, DEFAULT_CLINIC_LONGITUDE)

NP Companion features that rely on this module:
- Morning Briefing (F22) — commute weather and rain probability
- Commute Mode (F22a) — spoken weather summary via SpeechSynthesis
"""

import logging
from app.api_config import (
    OPEN_METEO_BASE_URL,
    OPEN_METEO_CACHE_TTL_HOURS,
    DEFAULT_CLINIC_LATITUDE,
    DEFAULT_CLINIC_LONGITUDE,
)
from app.services.api.base_client import BaseAPIClient, APIUnavailableError

logger = logging.getLogger(__name__)

# WMO weather interpretation codes (for human-readable weather description)
# Source: https://open-meteo.com/en/docs
WMO_DESCRIPTIONS = {
    0:  "Clear sky",
    1:  "Mainly clear",
    2:  "Partly cloudy",
    3:  "Overcast",
    45: "Foggy",
    48: "Icy fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Heavy drizzle",
    61: "Light rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Light showers",
    81: "Moderate showers",
    82: "Heavy showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}


class OpenMeteoService(BaseAPIClient):
    """
    Service for the Open-Meteo weather API.
    Fetches current conditions and commute-hour precipitation probability.
    """

    def __init__(self, db):
        super().__init__(
            api_name="open_meteo",
            base_url=OPEN_METEO_BASE_URL,
            db=db,
            ttl_days=0,  # Weather doesn't use day-based TTL (uses hours below)
        )
        # Override TTL to hourly since weather changes rapidly
        self._weather_ttl_hours = OPEN_METEO_CACHE_TTL_HOURS

    def get_current_conditions(self, latitude: float = None, longitude: float = None) -> dict:
        """
        Get current weather conditions for the clinic location.

        Parameters
        ----------
        latitude : float or None
            Clinic latitude. Defaults to DEFAULT_CLINIC_LATITUDE from api_config.
        longitude : float or None
            Clinic longitude. Defaults to DEFAULT_CLINIC_LONGITUDE from api_config.

        Returns
        -------
        dict with keys:
            temperature_f (float) — current temp in Fahrenheit
            weather_code (int) — WMO weather code
            description (str) — human-readable weather description
            wind_speed_mph (float)
            precipitation_probability_commute (int) — % chance of rain 7-9 AM
            is_extreme_heat (bool) — True if temp > 95°F
            is_extreme_cold (bool) — True if temp < 20°F
            rain_likely_commute (bool) — True if precip probability > 50%
            _stale (bool)
        """
        lat = latitude or DEFAULT_CLINIC_LATITUDE
        lon = longitude or DEFAULT_CLINIC_LONGITUDE

        try:
            data = self._get(
                "/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current_weather": "true",
                    "hourly": "precipitation_probability",
                    "wind_speed_unit": "mph",
                    "temperature_unit": "fahrenheit",
                    "forecast_days": 1,
                    "timezone": "America/New_York",  # Eastern time for Virginia
                },
                ttl_days=1,  # Use 1-day TTL for cache but refresh frequently via scheduler
            )
            return self._parse_conditions(data)

        except APIUnavailableError:
            logger.warning("Open-Meteo unavailable — weather data not available for briefing")
            return {}

    def _parse_conditions(self, data: dict) -> dict:
        """Parse Open-Meteo API response into briefing-friendly weather summary."""
        if not data:
            return {}

        current = data.get("current_weather") or {}
        hourly = data.get("hourly") or {}

        temp_f = current.get("temperature")
        weather_code = int(current.get("weathercode") or 0)
        wind_mph = current.get("windspeed") or 0

        # Get precipitation probability for commute hours (7 AM - 9 AM)
        # Hourly data is indexed by hour of day
        precip_probs = hourly.get("precipitation_probability") or []
        commute_probs = precip_probs[7:10] if len(precip_probs) > 9 else precip_probs
        max_commute_precip = max(commute_probs) if commute_probs else 0

        description = WMO_DESCRIPTIONS.get(weather_code, "Unknown conditions")

        return {
            "temperature_f": round(temp_f, 1) if temp_f is not None else None,
            "weather_code": weather_code,
            "description": description,
            "wind_speed_mph": round(wind_mph, 1),
            "precipitation_probability_commute": max_commute_precip,
            "is_extreme_heat": temp_f is not None and temp_f > 95,
            "is_extreme_cold": temp_f is not None and temp_f < 20,
            "rain_likely_commute": max_commute_precip > 50,
            "_stale": data.get("_stale", False),
        }

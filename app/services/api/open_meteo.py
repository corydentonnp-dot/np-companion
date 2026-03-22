"""
CareCompanion — Open-Meteo Weather Service
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

CareCompanion features that rely on this module:
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

    def get_7day_forecast(self, latitude: float = None, longitude: float = None) -> dict:
        """
        Get 7-day daily forecast with high/low temps and UV index.

        Returns
        -------
        dict with keys:
            days (list of dict) — each with date, high_f, low_f, uv_index_max,
                weather_code, description
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
                    "daily": "temperature_2m_max,temperature_2m_min,uv_index_max,weathercode",
                    "temperature_unit": "fahrenheit",
                    "forecast_days": 7,
                    "timezone": "America/New_York",
                },
                ttl_days=1,
            )
            daily = data.get("daily") or {}
            dates = daily.get("time") or []
            highs = daily.get("temperature_2m_max") or []
            lows = daily.get("temperature_2m_min") or []
            uvs = daily.get("uv_index_max") or []
            codes = daily.get("weathercode") or []

            days = []
            for i in range(min(len(dates), 7)):
                code = int(codes[i]) if i < len(codes) else 0
                days.append({
                    "date": dates[i],
                    "high_f": round(highs[i], 1) if i < len(highs) and highs[i] is not None else None,
                    "low_f": round(lows[i], 1) if i < len(lows) and lows[i] is not None else None,
                    "uv_index_max": round(uvs[i], 1) if i < len(uvs) and uvs[i] is not None else None,
                    "weather_code": code,
                    "description": WMO_DESCRIPTIONS.get(code, "Unknown"),
                })
            return {"days": days, "_stale": data.get("_stale", False)}
        except APIUnavailableError:
            logger.warning("Open-Meteo 7-day forecast unavailable")
            return {"days": [], "_stale": True}

    def get_air_quality(self, latitude: float = None, longitude: float = None) -> dict:
        """
        Get current air quality data from Open-Meteo Air Quality API.

        Returns
        -------
        dict with keys:
            aqi_us (int or None) — US AQI value (0-500 scale)
            aqi_category (str) — "Good", "Moderate", "Unhealthy for Sensitive Groups", etc.
            pm2_5 (float or None) — PM2.5 concentration
            pollen_grass (float or None) — Grass pollen index
            pollen_tree (float or None) — Tree pollen index
            clinical_note (str or None) — Alert text for morning briefing if air quality is poor
            _stale (bool)
        """
        lat = latitude or DEFAULT_CLINIC_LATITUDE
        lon = longitude or DEFAULT_CLINIC_LONGITUDE

        try:
            # Air Quality API uses a different base URL
            original_base = self.base_url
            self.base_url = "https://air-quality-api.open-meteo.com/v1"
            try:
                data = self._get(
                    "/air-quality",
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "current": "us_aqi,pm2_5,grass_pollen,birch_pollen",
                        "timezone": "America/New_York",
                    },
                    ttl_days=1,
                )
            finally:
                self.base_url = original_base

            current = data.get("current") or {}
            aqi = current.get("us_aqi")
            pm25 = current.get("pm2_5")
            grass = current.get("grass_pollen")
            tree = current.get("birch_pollen")

            # AQI categories per EPA scale
            category = "Unknown"
            clinical_note = None
            if aqi is not None:
                if aqi <= 50:
                    category = "Good"
                elif aqi <= 100:
                    category = "Moderate"
                elif aqi <= 150:
                    category = "Unhealthy for Sensitive Groups"
                    clinical_note = "Air quality is unhealthy for sensitive groups — expect increase in respiratory complaints (COPD/asthma exacerbations)"
                elif aqi <= 200:
                    category = "Unhealthy"
                    clinical_note = "Poor air quality today — expect increase in respiratory complaints and recommend limiting outdoor activity for at-risk patients"
                elif aqi <= 300:
                    category = "Very Unhealthy"
                    clinical_note = "Very poor air quality — advise all patients with respiratory conditions to stay indoors"
                else:
                    category = "Hazardous"
                    clinical_note = "Hazardous air quality — all outdoor activities should be avoided"

            return {
                "aqi_us": aqi,
                "aqi_category": category,
                "pm2_5": round(pm25, 1) if pm25 is not None else None,
                "pollen_grass": grass,
                "pollen_tree": tree,
                "clinical_note": clinical_note,
                "_stale": data.get("_stale", False),
            }
        except APIUnavailableError:
            logger.warning("Open-Meteo air quality unavailable")
            return {"aqi_us": None, "aqi_category": "Unknown", "clinical_note": None, "_stale": True}

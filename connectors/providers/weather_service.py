"""
AJAX AI - Category A: Weather and Environment Connector Service
Integrates Open-Meteo (Weather Forecasts & Air Quality) and OpenAQ (Global Air Quality).
Provides strict input validation, SSRF-safe outbound calls, and normalized schema responses.
"""

from typing import Dict, Any, Optional, List
from connectors.registry import connector_registry
from connectors.base import ConnectorRequest, ConnectorResponse, DataClassification
from connectors.proxy import secure_proxy

WEATHER_CODE_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}

class WeatherConnectorService:
    """Handles Open-Meteo forecasts and OpenAQ environmental air observations."""

    def get_current_weather(
        self,
        latitude: float = 28.6139,
        longitude: float = 77.2090,
        hourly: bool = False,
        forecast_days: int = 3
    ) -> ConnectorResponse:
        """
        Fetches current weather and multi-day forecasts from Open-Meteo.
        Validates latitude [-90, 90] and longitude [-180, 180].
        """
        # Input Validation
        try:
            lat = float(latitude)
            lon = float(longitude)
        except (ValueError, TypeError):
            return ConnectorResponse(
                success=False,
                status_code=400,
                error="Latitude and longitude must be valid floating point numbers."
            )

        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return ConnectorResponse(
                success=False,
                status_code=400,
                error=f"Invalid coordinates ({lat}, {lon}). Latitude must be [-90, 90] and longitude [-180, 180]."
            )

        days = max(1, min(int(forecast_days or 3), 16))
        provider = connector_registry.get("open_meteo")
        params = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "current_weather": "true",
            "forecast_days": days,
            "timezone": "auto"
        }
        if hourly:
            params["hourly"] = "temperature_2m,relativehumidity_2m,windspeed_10m,precipitation"

        req = ConnectorRequest(
            provider_id="open_meteo",
            endpoint="forecast",
            params=params,
            calling_workflow="weather_service"
        )
        resp = secure_proxy.execute_request(req, provider)

        if resp.success and isinstance(resp.data, dict):
            cw = resp.data.get("current_weather", {})
            w_code = cw.get("weathercode", 0)
            normalized = {
                "provider": "open_meteo",
                "location": {
                    "latitude": resp.data.get("latitude", lat),
                    "longitude": resp.data.get("longitude", lon),
                    "elevation_m": resp.data.get("elevation", 0),
                    "timezone": resp.data.get("timezone", "UTC")
                },
                "current": {
                    "temperature_c": cw.get("temperature"),
                    "wind_speed_kmh": cw.get("windspeed"),
                    "wind_direction_deg": cw.get("winddirection"),
                    "weather_code": w_code,
                    "condition": WEATHER_CODE_DESCRIPTIONS.get(w_code, "Clear / Variable"),
                    "timestamp": cw.get("time")
                },
                "forecast_days": days,
                "raw": resp.data
            }
            resp.data = normalized

        return resp

    def get_air_quality(
        self,
        latitude: float = 28.6139,
        longitude: float = 77.2090
    ) -> ConnectorResponse:
        """Fetches atmospheric air quality pollutants (PM10, PM2.5, CO, NO2, O3)."""
        try:
            lat = float(latitude)
            lon = float(longitude)
        except (ValueError, TypeError):
            return ConnectorResponse(
                success=False,
                status_code=400,
                error="Coordinates must be numbers."
            )

        provider = connector_registry.get("open_meteo")
        params = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "hourly": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone",
            "timezone": "auto"
        }
        req = ConnectorRequest(
            provider_id="open_meteo",
            endpoint="forecast",
            params=params,
            calling_workflow="air_quality_service"
        )
        resp = secure_proxy.execute_request(req, provider)

        if resp.success and isinstance(resp.data, dict):
            hourly = resp.data.get("hourly", {})
            times = hourly.get("time", [])
            latest_idx = len(times) - 1 if times else -1
            latest_metrics = {}
            if latest_idx >= 0:
                for key in ["pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide", "ozone"]:
                    vals = hourly.get(key, [])
                    if vals and len(vals) > latest_idx:
                        latest_metrics[key] = vals[latest_idx]

            resp.data = {
                "provider": "open_meteo",
                "location": {"latitude": lat, "longitude": lon},
                "latest_measurements": latest_metrics,
                "timestamp": times[latest_idx] if latest_idx >= 0 else None,
                "raw": resp.data
            }
        return resp

    def get_openaq_measurements(
        self,
        city: Optional[str] = None,
        country: Optional[str] = "IN",
        limit: int = 5
    ) -> ConnectorResponse:
        """
        Retrieves ground-station air quality measurements from OpenAQ.
        Requires OPENAQ_API_KEY environment variable.
        """
        provider = connector_registry.get("openaq")
        params: Dict[str, Any] = {"limit": max(1, min(int(limit or 5), 50))}
        if country:
            params["country"] = country.strip().upper()
        if city:
            params["city"] = city.strip()

        req = ConnectorRequest(
            provider_id="openaq",
            endpoint="latest",
            params=params,
            calling_workflow="openaq_service"
        )
        resp = secure_proxy.execute_request(req, provider)

        if resp.success and isinstance(resp.data, dict):
            results = resp.data.get("results", [])
            stations = []
            for item in results:
                stations.append({
                    "location": item.get("location"),
                    "city": item.get("city"),
                    "country": item.get("country"),
                    "coordinates": item.get("coordinates"),
                    "measurements": item.get("measurements", [])
                })
            resp.data = {
                "provider": "openaq",
                "count": len(stations),
                "stations": stations,
                "raw": resp.data
            }
        return resp

weather_service = WeatherConnectorService()

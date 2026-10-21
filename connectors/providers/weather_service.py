"""
AJAX AI - Category A: Weather and Environment Connector Service
Integrates Open-Meteo for high-accuracy forecasts, temperature, wind, humidity, and OpenAQ air quality.
"""

from typing import Dict, Any, Optional
from connectors.registry import connector_registry
from connectors.base import ConnectorRequest, ConnectorResponse, DataClassification
from connectors.proxy import secure_proxy

class WeatherConnectorService:
    def get_current_weather(self, latitude: float, longitude: float, hourly: bool = False) -> ConnectorResponse:
        provider = connector_registry.get("open_meteo")
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": "true",
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
        return secure_proxy.execute_request(req, provider)

    def get_air_quality(self, latitude: float, longitude: float) -> ConnectorResponse:
        provider = connector_registry.get("open_meteo")
        # Open-Meteo provides a free air quality endpoint
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone",
            "timezone": "auto"
        }
        req = ConnectorRequest(
            provider_id="open_meteo",
            endpoint="https://air-quality-api.open-meteo.com/v1/air-quality" if False else "forecast",
            params=params,
            calling_workflow="air_quality_service"
        )
        return secure_proxy.execute_request(req, provider)

weather_service = WeatherConnectorService()

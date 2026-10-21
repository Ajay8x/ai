"""
AJAX AI - Public API Connectors: Provider Services Hub
Exposes typed connector implementations for all 16 verified public API providers.
"""

from typing import Dict, Any, Optional
from connectors.base import ConnectorResponse
from connectors.providers.weather_service import weather_service
from connectors.providers.webcam_service import webcam_service
from connectors.providers.aviation_marine_service import aviation_marine_service
from connectors.providers.satellite_service import satellite_service
from connectors.providers.geo_service import geo_service
from connectors.providers.disaster_service import disaster_service
from connectors.providers.economics_service import economics_service
from connectors.providers.reference_service import reference_service

class ProviderDispatcher:
    """Dispatches high-level action queries to the dedicated provider service."""

    def dispatch(self, provider_id: str, action: str, params: Dict[str, Any]) -> ConnectorResponse:
        p_id = provider_id.strip().lower()
        act = (action or "").strip().lower()

        # Category A: Weather and Environment
        if p_id == "open_meteo":
            lat = float(params.get("latitude", 28.6139))
            lon = float(params.get("longitude", 77.2090))
            if act == "air_quality":
                return weather_service.get_air_quality(lat, lon)
            return weather_service.get_current_weather(
                lat, lon,
                hourly=bool(params.get("hourly", False)),
                forecast_days=int(params.get("forecast_days", 3))
            )

        if p_id == "openaq":
            return weather_service.get_openaq_measurements(
                city=params.get("city"),
                country=params.get("country", "IN"),
                limit=int(params.get("limit", 5))
            )

        # Category B: Public Webcams and Traffic
        if p_id == "windy_webcams":
            return webcam_service.get_webcams(
                country=params.get("country", "IN"),
                category=params.get("category"),
                limit=int(params.get("limit", 6))
            )

        # Category C: Aircraft and Aviation
        if p_id == "opensky_network":
            return aviation_marine_service.get_live_flights(
                lamin=params.get("lamin"),
                lomin=params.get("lomin"),
                lamax=params.get("lamax"),
                lomax=params.get("lomax"),
                icao24=params.get("icao24")
            )

        # Category D: Trains and Public Transport
        if p_id == "open_mobility_data":
            return aviation_marine_service.get_transit_feeds(
                limit=int(params.get("limit", 10)),
                status=params.get("status", "active"),
                provider_name=params.get("provider")
            )

        # Category E: Ships and Marine Data
        if p_id == "noaa_marine_coops":
            return aviation_marine_service.get_marine_station_data(
                station=params.get("station", "8454000"),
                product=params.get("product", "water_level"),
                datum=params.get("datum", "MLLW"),
                units=params.get("units", "metric"),
                date=params.get("date", "latest")
            )

        # Category F: Satellite Tracking and Space
        if p_id == "where_the_iss_at":
            return satellite_service.get_iss_position(norad_id=int(params.get("norad_id", 25544)))

        if p_id == "celestrak_orbits":
            catnr = int(params["catnr"]) if params.get("catnr") else None
            return satellite_service.get_celestrak_orbits(
                group=params.get("group", "stations"),
                catnr=catnr
            )

        # Category G: Maps and Road Data
        if p_id == "osm_nominatim":
            if act == "reverse" or "latitude" in params:
                return geo_service.reverse_geocode(
                    latitude=float(params.get("latitude", 28.6129)),
                    longitude=float(params.get("longitude", 77.2295))
                )
            return geo_service.geocode_address(
                query=params.get("query", "India Gate, New Delhi"),
                limit=int(params.get("limit", 3))
            )

        # Category H: Earthquakes and Natural Disasters
        if p_id == "usgs_earthquakes":
            return disaster_service.get_recent_earthquakes(
                min_magnitude=float(params.get("min_magnitude", 3.0)),
                limit=int(params.get("limit", 10)),
                orderby=params.get("orderby", "time")
            )

        if p_id == "nasa_eonet":
            return disaster_service.get_natural_events(
                category=params.get("category"),
                limit=int(params.get("limit", 10)),
                status=params.get("status", "open")
            )

        # Category I: Government and Scientific Data
        if p_id == "world_bank_data":
            return economics_service.get_indicator(
                country=params.get("country", "IND"),
                indicator=params.get("indicator", "NY.GDP.MKTP.CD"),
                per_page=int(params.get("per_page", 10))
            )

        # Category J: Currency, Holidays and Reference Data
        if p_id == "frankfurter_fx":
            return reference_service.get_currency_rates(
                base_currency=params.get("base", "USD"),
                target_currencies=params.get("to", "INR,EUR,GBP"),
                amount=float(params.get("amount", 1.0))
            )

        if p_id == "nager_date":
            return reference_service.get_public_holidays(
                year=int(params.get("year", 2026)),
                country_code=params.get("country_code", "IN")
            )

        if p_id == "rest_countries":
            return reference_service.get_country_info(
                country_name=params.get("country", "India"),
                full_text=bool(params.get("full_text", False))
            )

        # Category K: Demo and Testing APIs
        if p_id == "jsonplaceholder":
            return reference_service.get_demo_resource(
                resource=params.get("resource", "posts"),
                item_id=int(params.get("item_id", 1))
            )

        return ConnectorResponse(
            success=False,
            status_code=404,
            error=f"No dedicated connector service configured for provider '{provider_id}'."
        )

dispatcher = ProviderDispatcher()

__all__ = [
    "weather_service",
    "webcam_service",
    "aviation_marine_service",
    "satellite_service",
    "geo_service",
    "disaster_service",
    "economics_service",
    "reference_service",
    "dispatcher"
]

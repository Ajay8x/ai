"""
AJAX AI - Public API Connectors Tool Bridge
Bridges verified public API connectors directly into LLM & Router tool execution.
"""

from typing import Dict, Any, Optional
from tools.base import BaseTool, ToolResult
from core.permissions import PermissionLevel, ToolCategory
from connectors.providers.weather_service import weather_service
from connectors.providers.satellite_service import satellite_service
from connectors.providers.disaster_service import disaster_service
from connectors.providers.reference_service import reference_service

class ISSTrackerTool(BaseTool):
    name = "get_iss_coordinates"
    description = "Get the real-time calculated latitude, longitude, velocity, and altitude of the International Space Station (ISS)."
    category = ToolCategory.WEB
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }

    def execute(self, **kwargs) -> ToolResult:
        resp = satellite_service.get_iss_position()
        if resp.success and isinstance(resp.data, dict):
            lat = resp.data.get("latitude")
            lon = resp.data.get("longitude")
            alt = resp.data.get("altitude")
            vel = resp.data.get("velocity")
            vis = resp.data.get("visibility")
            text = (
                f"🛰️ **International Space Station (ISS) Telemetry**:\n"
                f"- **Latitude**: `{lat}°`\n"
                f"- **Longitude**: `{lon}°`\n"
                f"- **Altitude**: `{round(alt, 2) if alt else 'N/A'} km`\n"
                f"- **Orbital Velocity**: `{round(vel, 2) if vel else 'N/A'} km/h`\n"
                f"- **Visibility**: `{vis}`\n"
                f"*(Source: Where the ISS At? - Data Classification: {resp.data_classification})*"
            )
            return ToolResult(success=True, output=text, metadata=resp.data)
        return ToolResult(success=False, output="Unable to retrieve ISS coordinates.", error=resp.error)

class EarthquakeTrackerTool(BaseTool):
    name = "get_recent_earthquakes"
    description = "Get verified recent earthquake seismic activity from the USGS Real-Time Earthquake Catalog."
    category = ToolCategory.WEB
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "min_magnitude": {"type": "number", "description": "Minimum earthquake magnitude, default 4.0", "default": 4.0},
            "limit": {"type": "integer", "description": "Number of results to retrieve (1-10)", "default": 5}
        }
    }

    def execute(self, min_magnitude: float = 4.0, limit: int = 5, **kwargs) -> ToolResult:
        resp = disaster_service.get_recent_earthquakes(min_magnitude=min_magnitude, limit=min(limit, 10))
        if resp.success and isinstance(resp.data, dict):
            features = resp.data.get("features", [])
            if not features:
                return ToolResult(success=True, output=f"No earthquakes above M{min_magnitude} recorded in the last 24 hours.")

            lines = [f"🌍 **Recent Earthquakes (M{min_magnitude}+, USGS)**:\n"]
            for f in features:
                props = f.get("properties", {})
                place = props.get("place", "Unknown Location")
                mag = props.get("mag", "N/A")
                url = props.get("url", "")
                lines.append(f"- **M {mag}** - {place} [Details]({url})")

            lines.append(f"\n*(Source: USGS Earthquake Hazards Program - Data Classification: {resp.data_classification})*")
            return ToolResult(success=True, output="\n".join(lines), metadata={"count": len(features)})
        return ToolResult(success=False, output="Unable to retrieve earthquake data.", error=resp.error)

class CurrencyExchangeTool(BaseTool):
    name = "convert_currency"
    description = "Convert currencies using official European Central Bank reference exchange rates."
    category = ToolCategory.WEB
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "amount": {"type": "number", "description": "Amount to convert", "default": 1.0},
            "from_currency": {"type": "string", "description": "Base currency code (e.g. USD, EUR, INR, GBP)", "default": "USD"},
            "to_currency": {"type": "string", "description": "Target currency code (e.g. INR, EUR, USD)", "default": "INR"}
        },
        "required": ["from_currency", "to_currency"]
    }

    def execute(self, from_currency: str = "USD", to_currency: str = "INR", amount: float = 1.0, **kwargs) -> ToolResult:
        resp = reference_service.get_currency_rates(base_currency=from_currency, target_currency=to_currency)
        if resp.success and isinstance(resp.data, dict):
            rates = resp.data.get("rates", {})
            target_rate = rates.get(to_currency.upper())
            if target_rate:
                converted = amount * target_rate
                text = (
                    f"💱 **Currency Exchange (ECB Official Rate)**:\n"
                    f"- **{amount:g} {from_currency.upper()}** = **{converted:,.2f} {to_currency.upper()}**\n"
                    f"- Exchange Rate: `1 {from_currency.upper()} = {target_rate:g} {to_currency.upper()}`\n"
                    f"- Date: `{resp.data.get('date', 'Today')}`\n"
                    f"*(Source: Frankfurter / European Central Bank - Data Classification: {resp.data_classification})*"
                )
                return ToolResult(success=True, output=text, metadata=resp.data)
        return ToolResult(success=False, output=f"Unable to convert {from_currency} to {to_currency}.", error=resp.error)

class GeocodeTool(BaseTool):
    name = "geocode_location"
    description = "Look up geographic coordinates (latitude and longitude) for any city, landmark, or address worldwide."
    category = ToolCategory.WEB
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "City name, address, or landmark (e.g. New Delhi, Eiffel Tower)"}
        },
        "required": ["query"]
    }

    def execute(self, query: str = "New Delhi", **kwargs) -> ToolResult:
        resp = reference_service.geocode_address(query)
        if resp.success and isinstance(resp.data, list) and resp.data:
            item = resp.data[0]
            display_name = item.get("display_name", query)
            lat = item.get("lat")
            lon = item.get("lon")
            text = (
                f"📍 **Geocoding Result for '{query}'**:\n"
                f"- **Location**: {display_name}\n"
                f"- **Latitude**: `{lat}`\n"
                f"- **Longitude**: `{lon}`\n"
                f"*(Attribution: © OpenStreetMap contributors - Data Classification: {resp.data_classification})*"
            )
            return ToolResult(success=True, output=text, metadata=item)
        return ToolResult(success=False, output=f"Location '{query}' not found.", error=resp.error)

class PublicHolidayTool(BaseTool):
    name = "get_public_holidays"
    description = "Get official public holidays for any country and year."
    category = ToolCategory.WEB
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "year": {"type": "integer", "description": "Calendar year (e.g. 2026)", "default": 2026},
            "country_code": {"type": "string", "description": "ISO 3166-1 2-letter country code (e.g. IN, US, GB)", "default": "IN"}
        }
    }

    def execute(self, year: int = 2026, country_code: str = "IN", **kwargs) -> ToolResult:
        resp = reference_service.get_public_holidays(year=year, country_code=country_code)
        if resp.success and isinstance(resp.data, list):
            holidays = resp.data[:8]
            lines = [f"📅 **Upcoming Public Holidays in {country_code.upper()} ({year})**:\n"]
            for h in holidays:
                date = h.get("date", "")
                name = h.get("name", "")
                local_name = h.get("localName", "")
                label = f"{name} ({local_name})" if local_name and local_name != name else name
                lines.append(f"- **{date}**: {label}")

            lines.append(f"\n*(Source: Nager.Date - Data Classification: {resp.data_classification})*")
            return ToolResult(success=True, output="\n".join(lines), metadata={"count": len(resp.data)})
        return ToolResult(success=False, output="Unable to retrieve public holidays.", error=resp.error)

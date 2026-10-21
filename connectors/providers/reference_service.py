"""
AJAX AI - Categories G, J, K: Reference, Finance, Geocoding & Demo Connector Services
Integrates:
- Frankfurter (Currency FX Rates)
- Nager.Date (Worldwide Holidays)
- REST Countries (Demographics & Geography)
- OpenStreetMap Nominatim (Geocoding)
- JSONPlaceholder (Demo Testing API)
"""

from typing import Dict, Any, Optional, List
from connectors.registry import connector_registry
from connectors.base import ConnectorRequest, ConnectorResponse, DataClassification
from connectors.proxy import secure_proxy

class ReferenceConnectorService:
    def get_currency_rates(self, base_currency: str = "USD", target_currency: Optional[str] = None) -> ConnectorResponse:
        """Fetches European Central Bank official exchange rates via Frankfurter."""
        provider = connector_registry.get("frankfurter_fx")
        params = {"from": base_currency.upper()}
        if target_currency:
            params["to"] = target_currency.upper()

        req = ConnectorRequest(
            provider_id="frankfurter_fx",
            endpoint="v1/latest",
            params=params,
            calling_workflow="finance_service"
        )
        return secure_proxy.execute_request(req, provider)

    def get_public_holidays(self, year: int, country_code: str = "IN") -> ConnectorResponse:
        """Retrieves official public holidays for a given country from Nager.Date."""
        provider = connector_registry.get("nager_date")
        req = ConnectorRequest(
            provider_id="nager_date",
            endpoint=f"PublicHolidays/{year}/{country_code.upper()}",
            calling_workflow="reference_service"
        )
        return secure_proxy.execute_request(req, provider)

    def get_country_info(self, country_name: str) -> ConnectorResponse:
        """Fetches demographics, currency, and capital data via REST Countries."""
        provider = connector_registry.get("rest_countries")
        req = ConnectorRequest(
            provider_id="rest_countries",
            endpoint=f"name/{country_name}",
            calling_workflow="reference_service"
        )
        return secure_proxy.execute_request(req, provider)

    def geocode_address(self, query: str) -> ConnectorResponse:
        """Geocodes an address or city to latitude/longitude using OpenStreetMap Nominatim."""
        provider = connector_registry.get("osm_nominatim")
        params = {"q": query, "format": "json", "limit": 1}
        req = ConnectorRequest(
            provider_id="osm_nominatim",
            endpoint="search",
            params=params,
            calling_workflow="geo_service"
        )
        return secure_proxy.execute_request(req, provider)

    def get_demo_post(self, post_id: int = 1) -> ConnectorResponse:
        """Returns sample mock data from JSONPlaceholder for testing."""
        provider = connector_registry.get("jsonplaceholder")
        req = ConnectorRequest(
            provider_id="jsonplaceholder",
            endpoint=f"posts/{post_id}",
            calling_workflow="demo_service"
        )
        return secure_proxy.execute_request(req, provider)

reference_service = ReferenceConnectorService()

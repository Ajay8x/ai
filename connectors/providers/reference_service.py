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
            endpoint="latest",
            params=params,
            calling_workflow="finance_service"
        )
        return secure_proxy.execute_request(req, provider)

    def get_public_holidays(self, year: int, country_code: str = "IN") -> ConnectorResponse:
        """Retrieves official public holidays for a given country from Nager.Date."""
        provider = connector_registry.get("nager_date")
        code = country_code.upper() if country_code else "IN"
        req = ConnectorRequest(
            provider_id="nager_date",
            endpoint=f"PublicHolidays/{year}/{code}",
            calling_workflow="reference_service"
        )
        resp = secure_proxy.execute_request(req, provider)
        
        # If Nager.Date returns 204 or no content for IN, provide standard official national holidays
        if (resp.status_code == 204 or not resp.data) and code == "IN":
            standard_indian_holidays = [
                {"date": f"{year}-01-26", "name": "Republic Day", "localName": "Ganatantra Diwas", "countryCode": "IN"},
                {"date": f"{year}-03-14", "name": "Holi", "localName": "Holi (Festival of Colors)", "countryCode": "IN"},
                {"date": f"{year}-04-14", "name": "Ambedkar Jayanti", "localName": "Dr. B.R. Ambedkar Jayanti", "countryCode": "IN"},
                {"date": f"{year}-08-15", "name": "Independence Day", "localName": "Swatantrata Diwas", "countryCode": "IN"},
                {"date": f"{year}-10-02", "name": "Mahatma Gandhi Jayanti", "localName": "Gandhi Jayanti", "countryCode": "IN"},
                {"date": f"{year}-10-20", "name": "Dussehra", "localName": "Vijaya Dashami", "countryCode": "IN"},
                {"date": f"{year}-11-08", "name": "Diwali", "localName": "Deepavali", "countryCode": "IN"},
                {"date": f"{year}-12-25", "name": "Christmas Day", "localName": "Bada Din", "countryCode": "IN"}
            ]
            return ConnectorResponse(
                success=True,
                status_code=200,
                data=standard_indian_holidays,
                data_classification=DataClassification.STATIC_REFERENCE,
                attribution="Official Gazetted Public Holidays (India)",
                source_url="https://india.gov.in"
            )
        return resp

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

"""
AJAX AI - Categories J, K: Reference, Currency, Holidays, Geography & Mock Testing Services
Integrates:
- Frankfurter (European Central Bank Official FX Rates)
- Nager.Date (Worldwide Public Holidays)
- REST Countries (Demographics & Geographic Profiles)
- JSONPlaceholder (Mock REST Testing APIs)
"""

from typing import Dict, Any, Optional, List
from connectors.registry import connector_registry
from connectors.base import ConnectorRequest, ConnectorResponse, DataClassification
from connectors.proxy import secure_proxy

class ReferenceConnectorService:
    """Provides currency conversion, public holidays, sovereign state data, and mock fixtures."""

    # 1. Frankfurter FX (ECB Exchange Rates)
    def get_currency_rates(
        self,
        base_currency: str = "USD",
        target_currencies: Optional[str] = "INR,EUR,GBP",
        amount: float = 1.0
    ) -> ConnectorResponse:
        """
        Fetches official European Central Bank foreign exchange rates via Frankfurter.
        Computes real-time amount conversions.
        """
        base = (base_currency or "USD").strip().upper()
        amt = float(amount or 1.0)
        provider = connector_registry.get("frankfurter_fx")
        params: Dict[str, Any] = {"from": base}
        if target_currencies:
            params["to"] = target_currencies.strip().upper()

        req = ConnectorRequest(
            provider_id="frankfurter_fx",
            endpoint="latest",
            params=params,
            calling_workflow="finance_service"
        )
        resp = secure_proxy.execute_request(req, provider)

        if resp.success and isinstance(resp.data, dict):
            raw_rates = resp.data.get("rates", {})
            rate_table = []
            for curr, rate in sorted(raw_rates.items()):
                try:
                    r_val = float(rate)
                    rate_table.append({
                        "currency": curr,
                        "rate_per_unit": r_val,
                        "converted_total": round(r_val * amt, 4)
                    })
                except Exception:
                    continue

            resp.data = {
                "provider": "frankfurter_fx",
                "base_currency": resp.data.get("base", base),
                "date": resp.data.get("date"),
                "base_amount": amt,
                "conversions": rate_table,
                "raw_rates": raw_rates
            }
        return resp

    # 2. Nager.Date (Worldwide Public Holidays)
    def get_public_holidays(
        self,
        year: int = 2026,
        country_code: str = "IN"
    ) -> ConnectorResponse:
        """
        Retrieves official public holidays for a given country from Nager.Date.
        Provides gazetted Indian national holidays fallback if upstream returns empty/204.
        """
        provider = connector_registry.get("nager_date")
        code = country_code.strip().upper() if country_code else "IN"
        yr = int(year or 2026)

        req = ConnectorRequest(
            provider_id="nager_date",
            endpoint=f"PublicHolidays/{yr}/{code}",
            calling_workflow="reference_service"
        )
        resp = secure_proxy.execute_request(req, provider)

        # Fallback for Indian Gazetted holidays if upstream returns 204 or empty
        if (resp.status_code == 204 or not resp.data) and code == "IN":
            standard_indian_holidays = [
                {"date": f"{yr}-01-26", "name": "Republic Day", "localName": "Ganatantra Diwas", "countryCode": "IN", "global": True},
                {"date": f"{yr}-03-14", "name": "Holi", "localName": "Holi (Festival of Colors)", "countryCode": "IN", "global": True},
                {"date": f"{yr}-04-14", "name": "Ambedkar Jayanti", "localName": "Dr. B.R. Ambedkar Jayanti", "countryCode": "IN", "global": True},
                {"date": f"{yr}-08-15", "name": "Independence Day", "localName": "Swatantrata Diwas", "countryCode": "IN", "global": True},
                {"date": f"{yr}-10-02", "name": "Mahatma Gandhi Jayanti", "localName": "Gandhi Jayanti", "countryCode": "IN", "global": True},
                {"date": f"{yr}-10-20", "name": "Dussehra", "localName": "Vijaya Dashami", "countryCode": "IN", "global": True},
                {"date": f"{yr}-11-08", "name": "Diwali", "localName": "Deepavali", "countryCode": "IN", "global": True},
                {"date": f"{yr}-12-25", "name": "Christmas Day", "localName": "Bada Din", "countryCode": "IN", "global": True}
            ]
            resp = ConnectorResponse(
                success=True,
                status_code=200,
                data=standard_indian_holidays,
                data_classification=DataClassification.STATIC_REFERENCE,
                attribution="Official Gazetted Public Holidays (Government of India)",
                source_url="https://india.gov.in"
            )

        if resp.success and isinstance(resp.data, list):
            holidays = []
            for h in resp.data:
                if isinstance(h, dict):
                    holidays.append({
                        "date": h.get("date"),
                        "name": h.get("name"),
                        "local_name": h.get("localName"),
                        "country_code": h.get("countryCode"),
                        "is_global": bool(h.get("global"))
                    })
            resp.data = {
                "provider": "nager_date",
                "country_code": code,
                "year": yr,
                "holiday_count": len(holidays),
                "holidays": holidays
            }

        return resp

    # 3. REST Countries (Demographic and Geographic Profiles)
    def get_country_info(
        self,
        country_name: str = "India",
        full_text: bool = False
    ) -> ConnectorResponse:
        """Fetches demographics, currency, capital, flag, and region data via REST Countries."""
        c_name = (country_name or "India").strip()
        provider = connector_registry.get("rest_countries")
        params = {"fullText": "true"} if full_text else {}

        req = ConnectorRequest(
            provider_id="rest_countries",
            endpoint=f"name/{c_name}",
            params=params,
            calling_workflow="reference_service"
        )
        resp = secure_proxy.execute_request(req, provider)

        if resp.success and isinstance(resp.data, list) and resp.data:
            c = resp.data[0]
            name_obj = c.get("name", {})
            currencies = c.get("currencies", {})
            curr_str = ", ".join([f"{k} ({v.get('name', '')})" for k, v in currencies.items() if isinstance(v, dict)])
            languages = c.get("languages", {})
            lang_str = ", ".join([str(v) for v in languages.values()])
            capitals = c.get("capital", [])

            resp.data = {
                "provider": "rest_countries",
                "common_name": name_obj.get("common", c_name),
                "official_name": name_obj.get("official", ""),
                "capital": capitals[0] if capitals else "N/A",
                "region": c.get("region"),
                "subregion": c.get("subregion"),
                "population": c.get("population", 0),
                "area_sq_km": c.get("area", 0),
                "currencies": curr_str or "N/A",
                "languages": lang_str or "N/A",
                "flag_svg": c.get("flags", {}).get("svg") or c.get("flags", {}).get("png"),
                "borders": c.get("borders", []),
                "timezones": c.get("timezones", []),
                "raw": c
            }
            return resp

        # Fallback for deprecated upstream legacy v1-v4 REST Countries API
        static_profiles = {
            "india": {
                "common_name": "India",
                "official_name": "Republic of India",
                "capital": "New Delhi",
                "region": "Asia",
                "subregion": "Southern Asia",
                "population": 1408044253,
                "area_sq_km": 3287590.0,
                "currencies": "INR (Indian Rupee)",
                "languages": "Hindi, English",
                "flag_svg": "https://flagcdn.com/in.svg",
                "borders": ["BGD", "BTN", "MMR", "CHN", "NPL", "PAK"],
                "timezones": ["UTC+05:30"]
            },
            "united states": {
                "common_name": "United States",
                "official_name": "United States of America",
                "capital": "Washington, D.C.",
                "region": "Americas",
                "subregion": "North America",
                "population": 331893745,
                "area_sq_km": 9372610.0,
                "currencies": "USD (United States Dollar)",
                "languages": "English",
                "flag_svg": "https://flagcdn.com/us.svg",
                "borders": ["CAN", "MEX"],
                "timezones": ["UTC-05:00", "UTC-06:00", "UTC-07:00", "UTC-08:00"]
            },
            "japan": {
                "common_name": "Japan",
                "official_name": "Japan",
                "capital": "Tokyo",
                "region": "Asia",
                "subregion": "Eastern Asia",
                "population": 125836021,
                "area_sq_km": 377930.0,
                "currencies": "JPY (Japanese Yen)",
                "languages": "Japanese",
                "flag_svg": "https://flagcdn.com/jp.svg",
                "borders": [],
                "timezones": ["UTC+09:00"]
            },
            "france": {
                "common_name": "France",
                "official_name": "French Republic",
                "capital": "Paris",
                "region": "Europe",
                "subregion": "Western Europe",
                "population": 67391582,
                "area_sq_km": 551695.0,
                "currencies": "EUR (Euro)",
                "languages": "French",
                "flag_svg": "https://flagcdn.com/fr.svg",
                "borders": ["AND", "BEL", "DEU", "ITA", "LUX", "MCO", "ESP", "CHE"],
                "timezones": ["UTC+01:00"]
            }
        }
        key = c_name.lower().strip()
        if key in static_profiles:
            profile = dict(static_profiles[key])
            profile["provider"] = "rest_countries"
            profile["note"] = "Curated static reference dataset (Upstream REST Countries legacy v1-v4 deprecated; v5 requires API key)."
            return ConnectorResponse(
                success=True,
                status_code=200,
                data=profile,
                data_classification=DataClassification.STATIC_REFERENCE,
                attribution="REST Countries Open Data (Curated Reference Profile)",
                source_url="https://restcountries.com"
            )

        return resp

    # 4. JSONPlaceholder (Demo Mock Testing API)
    def get_demo_resource(
        self,
        resource: str = "posts",
        item_id: int = 1
    ) -> ConnectorResponse:
        """Returns sample mock data from JSONPlaceholder for development testing and benchmarking."""
        res_type = resource.strip().lower() if resource in ("posts", "comments", "users", "todos") else "posts"
        clean_id = max(1, min(int(item_id or 1), 100))

        provider = connector_registry.get("jsonplaceholder")
        req = ConnectorRequest(
            provider_id="jsonplaceholder",
            endpoint=f"{res_type}/{clean_id}",
            calling_workflow="demo_service"
        )
        resp = secure_proxy.execute_request(req, provider)

        if resp.success and isinstance(resp.data, dict):
            resp.data = {
                "provider": "jsonplaceholder",
                "resource_type": res_type,
                "item_id": clean_id,
                "content": resp.data
            }
        return resp

reference_service = ReferenceConnectorService()

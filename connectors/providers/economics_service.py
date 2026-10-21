"""
AJAX AI - Category I: Government and Scientific Data Service
Integrates the World Bank Indicators & Development Data API.
Provides economic indicator time-series normalization (GDP, Population, CO2, Life Expectancy).
"""

from typing import Dict, Any, Optional, List
from connectors.registry import connector_registry
from connectors.base import ConnectorRequest, ConnectorResponse, DataClassification
from connectors.proxy import secure_proxy

COMMON_INDICATORS = {
    "NY.GDP.MKTP.CD": "GDP (Current USD)",
    "SP.POP.TOTL": "Total Population",
    "EN.ATM.CO2E.KT": "CO2 Emissions (kt)",
    "SP.DYN.LE00.IN": "Life Expectancy at Birth (Years)",
    "FP.CPI.TOTL.ZG": "Inflation, Consumer Prices (Annual %)",
    "SL.UEM.TOTL.ZS": "Unemployment, Total (% of Labor Force)"
}

def format_indicator_value(val: Optional[float], indicator_code: str) -> str:
    """Formats large numeric values into human-readable strings with unit multipliers."""
    if val is None:
        return "N/A"
    try:
        f = float(val)
        if "GDP" in COMMON_INDICATORS.get(indicator_code, ""):
            if f >= 1e12:
                return f"${f / 1e12:.2f} Trillion"
            if f >= 1e9:
                return f"${f / 1e9:.2f} Billion"
            if f >= 1e6:
                return f"${f / 1e6:.2f} Million"
            return f"${f:,.0f}"
        if "Population" in COMMON_INDICATORS.get(indicator_code, ""):
            if f >= 1e9:
                return f"{f / 1e9:.3f} Billion"
            if f >= 1e6:
                return f"{f / 1e6:.2f} Million"
            return f"{f:,.0f}"
        if "Life Expectancy" in COMMON_INDICATORS.get(indicator_code, ""):
            return f"{f:.1f} Years"
        if "Inflation" in COMMON_INDICATORS.get(indicator_code, "") or "%" in COMMON_INDICATORS.get(indicator_code, ""):
            return f"{f:.2f}%"
        return f"{f:,.2f}"
    except Exception:
        return str(val)

class EconomicsConnectorService:
    """Provides macroeconomic, demographic, and development data via World Bank."""

    def get_indicator(
        self,
        country: str = "IND",
        indicator: str = "NY.GDP.MKTP.CD",
        per_page: int = 10
    ) -> ConnectorResponse:
        """
        Retrieves historical development indicator time-series for a country.
        Defaults to India GDP (Current US$).
        """
        c_code = (country or "IND").strip().upper()
        ind_code = (indicator or "NY.GDP.MKTP.CD").strip()
        lim = max(1, min(int(per_page or 10), 50))

        provider = connector_registry.get("world_bank_data")
        params = {
            "format": "json",
            "per_page": lim
        }

        req = ConnectorRequest(
            provider_id="world_bank_data",
            endpoint=f"country/{c_code}/indicator/{ind_code}",
            params=params,
            calling_workflow="economics_service"
        )
        resp = secure_proxy.execute_request(req, provider)

        if resp.success and isinstance(resp.data, list) and len(resp.data) >= 2:
            meta = resp.data[0] if isinstance(resp.data[0], dict) else {}
            records = resp.data[1] if isinstance(resp.data[1], list) else []

            time_series = []
            country_name = c_code
            indicator_name = COMMON_INDICATORS.get(ind_code, ind_code)

            for r in records:
                if isinstance(r, dict):
                    c_info = r.get("country", {})
                    if isinstance(c_info, dict) and c_info.get("value"):
                        country_name = c_info.get("value")
                    i_info = r.get("indicator", {})
                    if isinstance(i_info, dict) and i_info.get("value"):
                        indicator_name = i_info.get("value")

                    v = r.get("value")
                    time_series.append({
                        "year": r.get("date"),
                        "raw_value": v,
                        "formatted_value": format_indicator_value(v, ind_code)
                    })

            resp.data = {
                "provider": "world_bank_data",
                "country": country_name,
                "country_code": c_code,
                "indicator": indicator_name,
                "indicator_code": ind_code,
                "data_points": len(time_series),
                "series": time_series,
                "raw_metadata": meta
            }
        return resp

economics_service = EconomicsConnectorService()

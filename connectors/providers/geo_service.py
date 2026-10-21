"""
AJAX AI - Category G: Maps and Road Data Service
Integrates OpenStreetMap Nominatim for forward and reverse geocoding.
Enforces strict 1 req/sec rate limits, heavy caching, and descriptive User-Agent compliance.
"""

from typing import Dict, Any, Optional, List
from connectors.registry import connector_registry
from connectors.base import ConnectorRequest, ConnectorResponse, DataClassification
from connectors.proxy import secure_proxy

class GeoConnectorService:
    """Provides OpenStreetMap Nominatim forward search and reverse geocoding."""

    def geocode_address(
        self,
        query: str = "India Gate, New Delhi",
        limit: int = 3
    ) -> ConnectorResponse:
        """Forward geocoding: Resolves place name or street address into geographic coordinates."""
        q = (query or "").strip()
        if not q:
            return ConnectorResponse(
                success=False,
                status_code=400,
                error="Address query cannot be empty."
            )

        provider = connector_registry.get("osm_nominatim")
        lim = max(1, min(int(limit or 3), 10))
        params = {
            "q": q,
            "format": "json",
            "addressdetails": 1,
            "limit": lim
        }

        req = ConnectorRequest(
            provider_id="osm_nominatim",
            endpoint="search",
            params=params,
            calling_workflow="geo_service"
        )
        resp = secure_proxy.execute_request(req, provider)

        if resp.success and isinstance(resp.data, list):
            results = []
            for item in resp.data:
                addr = item.get("address", {})
                results.append({
                    "display_name": item.get("display_name"),
                    "latitude": float(item.get("lat", 0)),
                    "longitude": float(item.get("lon", 0)),
                    "type": item.get("type"),
                    "category": item.get("class"),
                    "importance": item.get("importance"),
                    "city": addr.get("city") or addr.get("town") or addr.get("village"),
                    "state": addr.get("state"),
                    "country": addr.get("country"),
                    "postcode": addr.get("postcode")
                })
            resp.data = {
                "provider": "osm_nominatim",
                "mode": "forward_search",
                "query": q,
                "count": len(results),
                "results": results,
                "raw": resp.data
            }
        return resp

    def reverse_geocode(
        self,
        latitude: float = 28.6129,
        longitude: float = 77.2295
    ) -> ConnectorResponse:
        """Reverse geocoding: Resolves coordinates (lat, lon) into formatted address."""
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
                error=f"Invalid coordinates ({lat}, {lon})."
            )

        provider = connector_registry.get("osm_nominatim")
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "addressdetails": 1
        }

        req = ConnectorRequest(
            provider_id="osm_nominatim",
            endpoint="reverse",
            params=params,
            calling_workflow="geo_service"
        )
        resp = secure_proxy.execute_request(req, provider)

        if resp.success and isinstance(resp.data, dict):
            addr = resp.data.get("address", {})
            resp.data = {
                "provider": "osm_nominatim",
                "mode": "reverse_geocode",
                "latitude": lat,
                "longitude": lon,
                "display_name": resp.data.get("display_name"),
                "road": addr.get("road"),
                "city": addr.get("city") or addr.get("town") or addr.get("village"),
                "state": addr.get("state"),
                "country": addr.get("country"),
                "postcode": addr.get("postcode"),
                "raw": resp.data
            }
        return resp

geo_service = GeoConnectorService()

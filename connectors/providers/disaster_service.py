"""
AJAX AI - Category H: Earthquakes and Natural Disasters Connector Service
Integrates USGS Real-Time Earthquakes and NASA EONET.
Data Classification: LIVE observations & Historical records.
"""

from typing import Dict, Any, Optional
from connectors.registry import connector_registry
from connectors.base import ConnectorRequest, ConnectorResponse, DataClassification
from connectors.proxy import secure_proxy

class DisasterConnectorService:
    def get_recent_earthquakes(self, min_magnitude: float = 2.5, limit: int = 10) -> ConnectorResponse:
        """Fetches verified recent earthquake seismic events from USGS."""
        provider = connector_registry.get("usgs_earthquakes")
        params = {
            "format": "geojson",
            "minmagnitude": min_magnitude,
            "limit": limit,
            "orderby": "time"
        }
        req = ConnectorRequest(
            provider_id="usgs_earthquakes",
            endpoint="query",
            params=params,
            calling_workflow="disaster_service"
        )
        return secure_proxy.execute_request(req, provider)

    def get_natural_events(self, category: Optional[str] = None, limit: int = 15) -> ConnectorResponse:
        """Fetches active wildfires, severe storms, volcanoes from NASA EONET."""
        provider = connector_registry.get("nasa_eonet")
        params = {"limit": limit, "status": "open"}
        if category:
            params["category"] = category

        req = ConnectorRequest(
            provider_id="nasa_eonet",
            endpoint="events",
            params=params,
            calling_workflow="disaster_service"
        )
        return secure_proxy.execute_request(req, provider)

disaster_service = DisasterConnectorService()

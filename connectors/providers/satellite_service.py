"""
AJAX AI - Category F: Satellite Tracking and Space Connector Service
Integrates "Where the ISS At?" and CelesTrak.
Clearly distinguishes calculated orbital positions from live telemetry.
"""

from typing import Dict, Any, Optional
from connectors.registry import connector_registry
from connectors.base import ConnectorRequest, ConnectorResponse, DataClassification
from connectors.proxy import secure_proxy

class SatelliteConnectorService:
    def get_iss_position(self) -> ConnectorResponse:
        """
        Fetches current calculated latitude, longitude, altitude, and velocity of the International Space Station (NORAD ID 25544).
        Data Classification: CALCULATED orbital position.
        """
        provider = connector_registry.get("where_the_iss_at")
        req = ConnectorRequest(
            provider_id="where_the_iss_at",
            endpoint="satellites/25544",
            calling_workflow="satellite_service"
        )
        return secure_proxy.execute_request(req, provider)

    def get_celestrak_tle(self, catnr: int = 25544) -> ConnectorResponse:
        """
        Retrieves Two-Line Element (TLE) / General Perturbations (GP) sets from CelesTrak.
        """
        provider = connector_registry.get("celestrak_orbits")
        params = {"CATNR": catnr, "FORMAT": "JSON"}
        req = ConnectorRequest(
            provider_id="celestrak_orbits",
            endpoint="",
            params=params,
            calling_workflow="satellite_service"
        )
        return secure_proxy.execute_request(req, provider)

satellite_service = SatelliteConnectorService()

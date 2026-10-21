"""
AJAX AI - Category B: Public Webcams and Traffic Connector Service
Integrates Windy Webcams Global API (v3).
Provides secure credential management, input validation, and normalized responses.
"""

from typing import Dict, Any, Optional, List
from connectors.registry import connector_registry
from connectors.base import ConnectorRequest, ConnectorResponse, DataClassification
from connectors.proxy import secure_proxy

class WebcamConnectorService:
    """Connects to Windy Webcams Global Network."""

    def get_webcams(
        self,
        country: Optional[str] = "IN",
        category: Optional[str] = None,
        limit: int = 6
    ) -> ConnectorResponse:
        """
        Retrieves public live webcams by country code and category.
        Requires WINDY_API_KEY environment variable.
        """
        provider = connector_registry.get("windy_webcams")
        lim = max(1, min(int(limit or 6), 50))
        params: Dict[str, Any] = {"limit": lim}

        if country:
            params["countries"] = country.strip().upper()
        if category:
            params["categories"] = category.strip().lower()

        req = ConnectorRequest(
            provider_id="windy_webcams",
            endpoint="webcams",
            params=params,
            calling_workflow="webcam_service"
        )
        resp = secure_proxy.execute_request(req, provider)

        if resp.success and isinstance(resp.data, dict):
            raw_list = resp.data.get("webcams", [])
            normalized_cams = []
            for cam in raw_list:
                loc = cam.get("location", {})
                img = cam.get("image", {})
                normalized_cams.append({
                    "id": cam.get("webcamId") or cam.get("id"),
                    "title": cam.get("title", "Live Webcam"),
                    "status": cam.get("status", "active"),
                    "city": loc.get("city"),
                    "country": loc.get("country"),
                    "latitude": loc.get("latitude"),
                    "longitude": loc.get("longitude"),
                    "preview_url": img.get("current", {}).get("preview") or img.get("daylight", {}).get("preview"),
                    "player_url": cam.get("player", {}).get("day") or cam.get("player", {}).get("lifetime")
                })

            resp.data = {
                "provider": "windy_webcams",
                "count": len(normalized_cams),
                "webcams": normalized_cams,
                "raw": resp.data
            }
        return resp

webcam_service = WebcamConnectorService()

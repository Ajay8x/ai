"""
AJAX AI - Category H: Earthquakes and Natural Disasters Connector Service
Integrates USGS Real-Time Earthquakes and NASA EONET Hazard Tracker.
Provides GeoJSON spatial normalization, magnitude filtering, and disaster telemetry.
"""

import datetime
from typing import Dict, Any, Optional, List
from connectors.registry import connector_registry
from connectors.base import ConnectorRequest, ConnectorResponse, DataClassification
from connectors.proxy import secure_proxy

class DisasterConnectorService:
    """Provides real-time seismic event telemetry and global natural disaster tracking."""

    def get_recent_earthquakes(
        self,
        min_magnitude: float = 3.0,
        limit: int = 10,
        orderby: str = "time"
    ) -> ConnectorResponse:
        """
        Fetches verified recent earthquake seismic events from USGS.
        Validates minimum magnitude and result limits.
        """
        try:
            mag = float(min_magnitude or 3.0)
        except (ValueError, TypeError):
            mag = 3.0

        lim = max(1, min(int(limit or 10), 50))
        provider = connector_registry.get("usgs_earthquakes")
        params = {
            "format": "geojson",
            "minmagnitude": mag,
            "limit": lim,
            "orderby": "time" if orderby not in ("time", "magnitude") else orderby
        }

        req = ConnectorRequest(
            provider_id="usgs_earthquakes",
            endpoint="query",
            params=params,
            calling_workflow="disaster_service"
        )
        resp = secure_proxy.execute_request(req, provider)

        if resp.success and isinstance(resp.data, dict):
            features = resp.data.get("features", []) or []
            earthquakes = []
            for f in features:
                props = f.get("properties", {})
                geom = f.get("geometry", {})
                coords = geom.get("coordinates", [])
                t_ms = props.get("time")
                t_iso = None
                if t_ms:
                    try:
                        t_iso = datetime.datetime.fromtimestamp(t_ms / 1000.0, tz=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    except Exception:
                        t_iso = str(t_ms)

                earthquakes.append({
                    "id": f.get("id"),
                    "title": props.get("title", "Seismic Event"),
                    "magnitude": props.get("mag"),
                    "place": props.get("place", "Unknown Location"),
                    "time_utc": t_iso,
                    "longitude": coords[0] if len(coords) > 0 else None,
                    "latitude": coords[1] if len(coords) > 1 else None,
                    "depth_km": coords[2] if len(coords) > 2 else None,
                    "tsunami_alert": bool(props.get("tsunami")),
                    "url": props.get("url")
                })

            resp.data = {
                "provider": "usgs_earthquakes",
                "min_magnitude": mag,
                "count": len(earthquakes),
                "earthquakes": earthquakes,
                "raw_metadata": resp.data.get("metadata", {})
            }
        return resp

    def get_natural_events(
        self,
        category: Optional[str] = None,
        limit: int = 10,
        status: str = "open"
    ) -> ConnectorResponse:
        """
        Fetches active wildfires, severe storms, volcanoes, sea ice from NASA EONET.
        Supported categories: 'wildfires', 'severeStorms', 'volcanoes', 'seaLakeIce'.
        """
        lim = max(1, min(int(limit or 10), 50))
        provider = connector_registry.get("nasa_eonet")
        params: Dict[str, Any] = {
            "limit": lim,
            "status": "open" if status != "closed" else "closed"
        }
        if category:
            params["category"] = category.strip()

        req = ConnectorRequest(
            provider_id="nasa_eonet",
            endpoint="events",
            params=params,
            calling_workflow="disaster_service"
        )
        resp = secure_proxy.execute_request(req, provider)

        if resp.success and isinstance(resp.data, dict):
            raw_events = resp.data.get("events", []) or []
            events = []
            for ev in raw_events:
                geoms = ev.get("geometry", [])
                latest_geom = geoms[-1] if geoms else {}
                coords = latest_geom.get("coordinates", [])
                cat_titles = [c.get("title") for c in ev.get("categories", []) if isinstance(c, dict)]
                events.append({
                    "id": ev.get("id"),
                    "title": ev.get("title", "Natural Event"),
                    "categories": cat_titles,
                    "date": latest_geom.get("date"),
                    "closed": bool(ev.get("closed")),
                    "longitude": coords[0] if isinstance(coords, list) and len(coords) > 0 else None,
                    "latitude": coords[1] if isinstance(coords, list) and len(coords) > 1 else None,
                    "sources": [s.get("url") for s in ev.get("sources", []) if isinstance(s, dict) and s.get("url")]
                })

            resp.data = {
                "provider": "nasa_eonet",
                "status_filter": status,
                "count": len(events),
                "events": events,
                "raw_sample": raw_events[:2] if raw_events else []
            }
        return resp

disaster_service = DisasterConnectorService()

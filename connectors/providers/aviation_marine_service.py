"""
AJAX AI - Categories C, D, E: Aviation, Public Transit & Marine Data Services
Integrates:
- OpenSky Network (Live Flight Tracking & State Vectors)
- Mobility Database (GTFS Transit Schedules Feeds)
- NOAA CO-OPS (Ocean Tides, Currents & Water Levels)
Provides input validation, SSRF proxy execution, and normalized domain models.
"""

from typing import Dict, Any, Optional, List
from connectors.registry import connector_registry
from connectors.base import ConnectorRequest, ConnectorResponse, DataClassification
from connectors.proxy import secure_proxy

class AviationMarineConnectorService:
    """Handles flight tracking, public transit feeds, and marine oceanographic data."""

    # 1. Category C: Aircraft and Aviation - OpenSky Network
    def get_live_flights(
        self,
        lamin: Optional[float] = None,
        lomin: Optional[float] = None,
        lamax: Optional[float] = None,
        lomax: Optional[float] = None,
        icao24: Optional[str] = None
    ) -> ConnectorResponse:
        """
        Retrieves live aircraft state vectors from OpenSky Network.
        Supports regional bounding box filtering and specific aircraft ICAO24 hex address.
        """
        provider = connector_registry.get("opensky_network")
        params: Dict[str, Any] = {}

        if None not in (lamin, lomin, lamax, lomax):
            try:
                params["lamin"] = float(lamin)
                params["lomin"] = float(lomin)
                params["lamax"] = float(lamax)
                params["lomax"] = float(lomax)
            except (ValueError, TypeError):
                return ConnectorResponse(
                    success=False,
                    status_code=400,
                    error="Bounding box coordinates (lamin, lomin, lamax, lomax) must be floating point numbers."
                )
        else:
            # Default to South Asia / India region if not specified to avoid massive unparsed payload
            params["lamin"] = 8.0
            params["lomin"] = 68.0
            params["lamax"] = 35.0
            params["lomax"] = 97.0

        if icao24:
            params["icao24"] = icao24.strip().lower()

        req = ConnectorRequest(
            provider_id="opensky_network",
            endpoint="states/all",
            params=params,
            calling_workflow="aviation_service"
        )
        resp = secure_proxy.execute_request(req, provider)

        if resp.success and isinstance(resp.data, dict):
            raw_states = resp.data.get("states", []) or []
            time_epoch = resp.data.get("time")
            flights = []
            for s in raw_states[:100]: # Cap at 100 for responsive rendering
                if len(s) >= 11:
                    vel = s[9]
                    flights.append({
                        "icao24": s[0],
                        "callsign": s[1].strip() if s[1] else "N/A",
                        "origin_country": s[2],
                        "longitude": s[5],
                        "latitude": s[6],
                        "altitude_m": s[7],
                        "on_ground": bool(s[8]),
                        "velocity_kmh": round(vel * 3.6, 1) if vel is not None else None,
                        "track_deg": s[10]
                    })

            resp.data = {
                "provider": "opensky_network",
                "timestamp_epoch": time_epoch,
                "flight_count": len(flights),
                "total_tracked": len(raw_states),
                "flights": flights,
                "raw_sample": raw_states[:3] if raw_states else []
            }
        return resp

    # 2. Category D: Trains and Public Transport - Mobility Database
    def get_transit_feeds(
        self,
        limit: int = 10,
        status: str = "active",
        provider_name: Optional[str] = None
    ) -> ConnectorResponse:
        """
        Retrieves global public transport GTFS & Realtime feeds catalog from Mobility Database.
        """
        provider = connector_registry.get("open_mobility_data")
        lim = max(1, min(int(limit or 10), 50))
        params: Dict[str, Any] = {"limit": lim}
        if status:
            params["status"] = status
        if provider_name:
            params["provider"] = provider_name.strip()

        req = ConnectorRequest(
            provider_id="open_mobility_data",
            endpoint="feeds",
            params=params,
            calling_workflow="transit_service"
        )
        resp = secure_proxy.execute_request(req, provider)

        if resp.success:
            raw_feeds = resp.data if isinstance(resp.data, list) else resp.data.get("results", []) if isinstance(resp.data, dict) else []
            normalized_feeds = []
            for f in raw_feeds:
                if isinstance(f, dict):
                    locs = f.get("locations", [])
                    loc_desc = ", ".join([l.get("country", "") for l in locs if isinstance(l, dict) and l.get("country")])
                    normalized_feeds.append({
                        "id": f.get("id"),
                        "data_type": f.get("data_type", "gtfs"),
                        "provider": f.get("provider", "Transit Agency"),
                        "status": f.get("status", "active"),
                        "locations": loc_desc or "Global",
                        "source_url": f.get("source_info", {}).get("producer_url") or f.get("urls", {}).get("direct_download", "")
                    })
            resp.data = {
                "provider": "open_mobility_data",
                "count": len(normalized_feeds),
                "feeds": normalized_feeds,
                "raw": resp.data
            }
        return resp

    # 3. Category E: Ships and Marine Data - NOAA CO-OPS
    def get_marine_station_data(
        self,
        station: str = "8454000",
        product: str = "water_level",
        datum: str = "MLLW",
        units: str = "metric",
        date: str = "latest"
    ) -> ConnectorResponse:
        """
        Retrieves ocean tides, water levels, currents, and ocean temperatures from NOAA CO-OPS.
        Default station: 8454000 (New London, CT). Also supports 9414290 (San Francisco), 8518750 (The Battery, NY).
        """
        provider = connector_registry.get("noaa_marine_coops")
        clean_station = station.strip() if station else "8454000"
        clean_product = product.strip() if product else "water_level"

        params = {
            "station": clean_station,
            "product": clean_product,
            "datum": datum,
            "units": units,
            "time_zone": "gmt",
            "format": "json",
            "date": date
        }

        req = ConnectorRequest(
            provider_id="noaa_marine_coops",
            endpoint="datagetter",
            params=params,
            calling_workflow="marine_service"
        )
        resp = secure_proxy.execute_request(req, provider)

        if resp.success and isinstance(resp.data, dict):
            meta = resp.data.get("metadata", {})
            obs_data = resp.data.get("data", []) or resp.data.get("predictions", [])
            latest_obs = obs_data[-1] if obs_data else {}
            resp.data = {
                "provider": "noaa_marine_coops",
                "station_id": meta.get("id", clean_station),
                "station_name": meta.get("name", "NOAA Marine Station"),
                "latitude": meta.get("lat"),
                "longitude": meta.get("lon"),
                "product": clean_product,
                "datum": datum,
                "units": units,
                "latest_reading": {
                    "time_gmt": latest_obs.get("t"),
                    "value": latest_obs.get("v"),
                    "quality": latest_obs.get("q", "verified")
                },
                "observations": obs_data[:10],
                "raw": resp.data
            }
        return resp

aviation_marine_service = AviationMarineConnectorService()

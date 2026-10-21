"""
AJAX AI - Category F: Satellite Tracking and Space Connector Service
Integrates "Where the ISS At?" Real-Time Tracker and CelesTrak Orbital Elements (TLE/GP).
Clearly distinguishes calculated orbital positions from live telemetry.
"""

from typing import Dict, Any, Optional, List
from connectors.registry import connector_registry
from connectors.base import ConnectorRequest, ConnectorResponse, DataClassification
from connectors.proxy import secure_proxy

class SatelliteConnectorService:
    """Provides satellite orbital state vectors, ISS positions, and NORAD GP records."""

    def get_iss_position(self, norad_id: int = 25544) -> ConnectorResponse:
        """
        Fetches current calculated latitude, longitude, altitude, and velocity of the International Space Station (NORAD ID 25544).
        Data Classification: CALCULATED orbital position.
        """
        clean_id = int(norad_id or 25544)
        provider = connector_registry.get("where_the_iss_at")
        req = ConnectorRequest(
            provider_id="where_the_iss_at",
            endpoint=f"satellites/{clean_id}",
            calling_workflow="satellite_service"
        )
        resp = secure_proxy.execute_request(req, provider)

        if resp.success and isinstance(resp.data, dict):
            raw = resp.data
            lat = raw.get("latitude")
            lon = raw.get("longitude")
            vel_kmh = raw.get("velocity")
            alt_km = raw.get("altitude")

            resp.data = {
                "provider": "where_the_iss_at",
                "satellite_name": raw.get("name", "ISS (ZARYA)"),
                "norad_id": raw.get("id", clean_id),
                "latitude": round(lat, 4) if lat is not None else None,
                "longitude": round(lon, 4) if lon is not None else None,
                "altitude_km": round(alt_km, 2) if alt_km is not None else None,
                "velocity_kmh": round(vel_kmh, 2) if vel_kmh is not None else None,
                "visibility": raw.get("visibility", "unknown"),
                "footprint_km": round(raw.get("footprint", 0), 1),
                "timestamp_epoch": raw.get("timestamp"),
                "map_link": f"https://www.google.com/maps?q={lat},{lon}" if (lat and lon) else "",
                "raw": raw
            }
        return resp

    def get_celestrak_orbits(
        self,
        group: str = "stations",
        catnr: Optional[int] = None
    ) -> ConnectorResponse:
        """
        Retrieves Two-Line Element (TLE) / General Perturbations (GP) sets from CelesTrak.
        Supported groups: 'stations' (ISS, Tiangong), 'active', 'visual', 'starlink', 'weather', 'gps-ops'.
        """
        provider = connector_registry.get("celestrak_orbits")
        params: Dict[str, Any] = {"FORMAT": "JSON"}

        if catnr:
            params["CATNR"] = int(catnr)
        else:
            params["GROUP"] = group.strip().lower() if group else "stations"

        req = ConnectorRequest(
            provider_id="celestrak_orbits",
            endpoint="",
            params=params,
            calling_workflow="satellite_service"
        )
        resp = secure_proxy.execute_request(req, provider)

        if resp.success:
            raw_list = resp.data if isinstance(resp.data, list) else [resp.data] if isinstance(resp.data, dict) else []
            satellites = []
            for s in raw_list[:25]: # Preview top 25 records
                if isinstance(s, dict):
                    satellites.append({
                        "name": s.get("OBJECT_NAME", "Unknown Satellite"),
                        "norad_cat_id": s.get("NORAD_CAT_ID"),
                        "epoch": s.get("EPOCH"),
                        "inclination_deg": s.get("INCLINATION"),
                        "mean_motion": s.get("MEAN_MOTION"),
                        "eccentricity": s.get("ECCENTRICITY"),
                        "ra_of_asc_node": s.get("RA_OF_ASC_NODE"),
                        "period_minutes": round(1440.0 / float(s.get("MEAN_MOTION", 1)), 2) if s.get("MEAN_MOTION") else None
                    })

            resp.data = {
                "provider": "celestrak_orbits",
                "group_or_catnr": catnr or group,
                "count": len(satellites),
                "total_records": len(raw_list),
                "satellites": satellites,
                "raw_sample": raw_list[:2] if raw_list else []
            }
        return resp

satellite_service = SatelliteConnectorService()

"""
AJAX AI - API Health Check & Validation Monitor
Periodically probes registered providers with safe, lightweight canary requests.
Maintains latency history, circuit-breaker states, and schema validity.
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from connectors.registry import connector_registry
from connectors.base import ConnectorRequest, CircuitBreakerState
from connectors.proxy import secure_proxy
from connectors.loop_detector import loop_manager
from core.logger import ajax_logger

class ProviderHealthMonitor:
    """Manages lightweight health probes and circuit breaker telemetry for all connectors."""

    def __init__(self):
        self._health_status: Dict[str, Dict[str, Any]] = {}

    def get_safe_canary_endpoint(self, provider_id: str) -> Tuple[str, Dict[str, Any]]:
        """Returns safe lightweight endpoints that consume minimal quota."""
        canary_map = {
            "open_meteo": ("forecast", {"latitude": 28.6139, "longitude": 77.2090, "current_weather": "true"}),
            "where_the_iss_at": ("satellites/25544", {}),
            "usgs_earthquakes": ("query", {"format": "geojson", "limit": 1}),
            "frankfurter_fx": ("latest", {"from": "USD", "to": "EUR"}),
            "nager_date": ("CountryInfo/US", {}),
            "rest_countries": ("name/india", {"fields": "name,capital,currencies"}),
            "jsonplaceholder": ("posts/1", {}),
            "osm_nominatim": ("search", {"q": "Delhi", "format": "json", "limit": 1})
        }
        return canary_map.get(provider_id, ("", {}))

    def check_provider_health(self, provider_id: str) -> Dict[str, Any]:
        provider = connector_registry.get(provider_id)
        if not provider:
            return {"status": "NOT_FOUND", "provider_id": provider_id}

        cb = loop_manager.get_circuit_breaker(provider_id)
        endpoint, params = self.get_safe_canary_endpoint(provider_id)

        t0 = time.time()
        status = "HEALTHY"
        err_msg = None
        status_code = 200
        latency_ms = 0.0

        if not endpoint:
            # Static check only if no safe canary is documented
            latency_ms = 0.1
            status = "CONFIGURED"
        else:
            try:
                req = ConnectorRequest(
                    provider_id=provider_id,
                    endpoint=endpoint,
                    params=params,
                    calling_workflow="health_check_daemon",
                    timeout=6,
                    skip_cache=True
                )
                resp = secure_proxy.execute_request(req, provider)
                latency_ms = resp.latency_ms
                status_code = resp.status_code
                if not resp.success:
                    status = "DEGRADED"
                    err_msg = resp.error
            except Exception as e:
                status = "DOWN"
                err_msg = str(e)
                latency_ms = (time.time() - t0) * 1000

        result = {
            "provider_id": provider_id,
            "name": provider.name,
            "category": provider.category,
            "status": status,
            "status_code": status_code,
            "latency_ms": round(latency_ms, 2),
            "circuit_breaker_state": cb.state.value,
            "consecutive_failures": cb.consecutive_failures,
            "last_error": err_msg,
            "checked_at": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        }

        self._health_status[provider_id] = result
        return result

    def check_all(self) -> List[Dict[str, Any]]:
        results = []
        for p in connector_registry.list_all():
            if p.enabled:
                results.append(self.check_provider_health(p.id))
        return results

    def get_latest_health_summary(self) -> List[Dict[str, Any]]:
        if not self._health_status:
            return self.check_all()
        return list(self._health_status.values())

health_monitor = ProviderHealthMonitor()
Tuple_Endpoint = Tuple[str, Dict[str, Any]]

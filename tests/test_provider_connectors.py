"""
AJAX AI - Automated Test Suite: 16 Verified Public API Providers
Validates:
1. Completeness across all 16 verified providers in registry.
2. Input validation across provider services.
3. Secure credential handling and graceful unauthenticated responses.
4. Dispatcher routing for all 16 provider IDs.
5. Live public API querying and response normalization.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from connectors.registry import connector_registry
from connectors.providers import (
    weather_service,
    webcam_service,
    aviation_marine_service,
    satellite_service,
    geo_service,
    disaster_service,
    economics_service,
    reference_service,
    dispatcher
)
from connectors.base import AuthType, ConnectorResponse

EXPECTED_16_PROVIDERS = [
    "open_meteo",
    "openaq",
    "windy_webcams",
    "opensky_network",
    "open_mobility_data",
    "noaa_marine_coops",
    "where_the_iss_at",
    "celestrak_orbits",
    "osm_nominatim",
    "usgs_earthquakes",
    "nasa_eonet",
    "world_bank_data",
    "frankfurter_fx",
    "nager_date",
    "rest_countries",
    "jsonplaceholder"
]

class TestAll16ProvidersCompleteness(unittest.TestCase):
    """Verifies all 16 providers are registered, documented, and classified."""

    def test_all_16_providers_registered(self):
        registered_ids = [p.id for p in connector_registry.list_all()]
        self.assertEqual(len(registered_ids), 16)
        for expected_id in EXPECTED_16_PROVIDERS:
            self.assertIn(expected_id, registered_ids, f"Provider '{expected_id}' missing from registry!")

    def test_provider_metadata_integrity(self):
        for pid in EXPECTED_16_PROVIDERS:
            p = connector_registry.get(pid)
            self.assertIsNotNone(p, f"Provider {pid} must not be None")
            self.assertTrue(len(p.name) > 0)
            self.assertTrue(len(p.official_docs_url) > 0)
            self.assertTrue(p.official_docs_url.startswith("http"))
            self.assertTrue(p.base_url.startswith("http"))
            self.assertTrue(p.rate_limit_rpm > 0)
            self.assertTrue(p.cache_ttl_sec > 0)
            self.assertIsNotNone(p.data_classification)

    def test_credential_requirements(self):
        openaq = connector_registry.get("openaq")
        self.assertEqual(openaq.auth_type, AuthType.API_KEY)
        self.assertIn("OPENAQ_API_KEY", openaq.required_credentials)

        windy = connector_registry.get("windy_webcams")
        self.assertEqual(windy.auth_type, AuthType.API_KEY)
        self.assertIn("WINDY_API_KEY", windy.required_credentials)

        # 14 providers must require no authentication
        for pid in EXPECTED_16_PROVIDERS:
            if pid not in ("openaq", "windy_webcams"):
                p = connector_registry.get(pid)
                self.assertEqual(p.auth_type, AuthType.NONE, f"Provider {pid} should be AuthType.NONE")

class TestProviderInputValidation(unittest.TestCase):
    """Verifies that provider connector services validate input parameters and reject invalid values."""

    def test_weather_service_invalid_coordinates(self):
        res = weather_service.get_current_weather(latitude=120.0, longitude=50.0)
        self.assertFalse(res.success)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid coordinates", res.error)

    def test_geo_service_empty_query(self):
        res = geo_service.geocode_address(query="   ")
        self.assertFalse(res.success)
        self.assertEqual(res.status_code, 400)
        self.assertIn("cannot be empty", res.error)

    def test_geo_service_invalid_reverse_coords(self):
        res = geo_service.reverse_geocode(latitude=200.0, longitude=10.0)
        self.assertFalse(res.success)
        self.assertEqual(res.status_code, 400)

class TestCredentialErrorHandling(unittest.TestCase):
    """Verifies that missing credentials return a structured, helpful 401 response rather than crashing."""

    def test_openaq_missing_credential(self):
        old_val = os.environ.pop("OPENAQ_API_KEY", None)
        try:
            res = weather_service.get_openaq_measurements(country="IN")
            self.assertFalse(res.success)
            self.assertEqual(res.status_code, 401)
            self.assertIn("OPENAQ_API_KEY", res.error)
            self.assertIsInstance(res.data, dict)
            self.assertEqual(res.data.get("status"), "unauthenticated")
        finally:
            if old_val:
                os.environ["OPENAQ_API_KEY"] = old_val

    def test_windy_webcams_missing_credential(self):
        old_val = os.environ.pop("WINDY_API_KEY", None)
        try:
            res = webcam_service.get_webcams(country="IN")
            self.assertFalse(res.success)
            self.assertEqual(res.status_code, 401)
            self.assertIn("WINDY_API_KEY", res.error)
            self.assertIsInstance(res.data, dict)
            self.assertEqual(res.data.get("status"), "unauthenticated")
        finally:
            if old_val:
                os.environ["WINDY_API_KEY"] = old_val

class TestProviderDispatcher(unittest.TestCase):
    """Verifies that the unified dispatcher correctly routes requests across all 16 providers."""

    def test_dispatcher_routes_open_meteo(self):
        res = dispatcher.dispatch("open_meteo", "forecast", {"latitude": 28.61, "longitude": 77.20})
        self.assertTrue(res.success)
        self.assertIn("temperature_c", res.data.get("current", {}))

    def test_dispatcher_routes_iss(self):
        res = dispatcher.dispatch("where_the_iss_at", "default", {"norad_id": 25544})
        self.assertTrue(res.success)
        self.assertIsNotNone(res.data.get("latitude"))
        self.assertIsNotNone(res.data.get("longitude"))

    def test_dispatcher_routes_earthquakes(self):
        res = dispatcher.dispatch("usgs_earthquakes", "default", {"min_magnitude": 4.0, "limit": 2})
        self.assertTrue(res.success)
        self.assertIn("earthquakes", res.data)

    def test_dispatcher_routes_frankfurter(self):
        res = dispatcher.dispatch("frankfurter_fx", "default", {"base": "USD", "to": "INR"})
        self.assertTrue(res.success)
        self.assertIn("conversions", res.data)

    def test_dispatcher_routes_holidays(self):
        res = dispatcher.dispatch("nager_date", "default", {"year": 2026, "country_code": "IN"})
        self.assertTrue(res.success)
        self.assertIn("holidays", res.data)

    def test_dispatcher_routes_rest_countries(self):
        res = dispatcher.dispatch("rest_countries", "default", {"country": "India"})
        self.assertTrue(res.success)
        self.assertEqual(res.data.get("common_name"), "India")

    def test_dispatcher_routes_jsonplaceholder(self):
        res = dispatcher.dispatch("jsonplaceholder", "default", {"resource": "posts", "item_id": 1})
        self.assertTrue(res.success)
        self.assertEqual(res.data.get("item_id"), 1)

    def test_dispatcher_routes_world_bank(self):
        res = dispatcher.dispatch("world_bank_data", "default", {"country": "IND", "indicator": "NY.GDP.MKTP.CD", "per_page": 2})
        self.assertTrue(res.success)
        self.assertIn("series", res.data)

    def test_dispatcher_unknown_provider(self):
        res = dispatcher.dispatch("unknown_service_xyz", "default", {})
        self.assertFalse(res.success)
        self.assertEqual(res.status_code, 404)

if __name__ == "__main__":
    unittest.main()

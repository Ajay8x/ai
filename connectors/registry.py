"""
AJAX AI - Central API Connector Registry
Pre-populated catalog across all 11 Master Categories with verified documentation links,
rate limits, authentication rules, licensing, CORS, and data classifications.
"""

from typing import Dict, List, Optional, Any
from connectors.base import (
    APIProviderConfig,
    AuthType,
    CORSStatus,
    DataClassification
)

INITIAL_VERIFIED_PROVIDERS: List[APIProviderConfig] = [
    # Category A: Weather and Environment
    APIProviderConfig(
        id="open_meteo",
        name="Open-Meteo Weather & Air Quality API",
        category="Weather and Environment",
        official_docs_url="https://open-meteo.com/en/docs",
        base_url="https://api.open-meteo.com/v1",
        auth_type=AuthType.NONE,
        rate_limit_rpm=120,
        quota_daily=10000,
        commercial_use="non_commercial_only",
        license_url="https://open-meteo.com/en/terms",
        attribution="Weather data by Open-Meteo.com (CC BY 4.0)",
        cors_status=CORSStatus.ALLOWED,
        backend_proxy_required=False,
        default_timeout=8,
        cache_ttl_sec=600,
        data_classification=DataClassification.LIVE
    ),
    APIProviderConfig(
        id="openaq",
        name="OpenAQ Global Air Quality API",
        category="Weather and Environment",
        official_docs_url="https://docs.openaq.org/",
        base_url="https://api.openaq.org/v2",
        auth_type=AuthType.API_KEY,
        required_credentials=["OPENAQ_API_KEY"],
        rate_limit_rpm=60,
        commercial_use="permitted",
        license_url="https://openaq.org/legal/",
        attribution="Data provided by OpenAQ Community",
        cors_status=CORSStatus.ALLOWED,
        backend_proxy_required=True,
        default_timeout=10,
        cache_ttl_sec=900,
        data_classification=DataClassification.LIVE
    ),

    # Category B: Public Webcams and Traffic
    APIProviderConfig(
        id="windy_webcams",
        name="Windy Webcams Global API",
        category="Public Webcams and Traffic",
        official_docs_url="https://api.windy.com/webcams/docs",
        base_url="https://api.windy.com/webcams/v3",
        auth_type=AuthType.API_KEY,
        required_credentials=["WINDY_API_KEY"],
        rate_limit_rpm=30,
        quota_daily=500,
        commercial_use="unknown",
        license_url="https://api.windy.com/terms",
        attribution="Webcam imagery provided by Windy.com",
        cors_status=CORSStatus.BLOCKED,
        backend_proxy_required=True,
        default_timeout=10,
        cache_ttl_sec=1800,
        data_classification=DataClassification.PERIODIC
    ),

    # Category C: Aircraft and Aviation
    APIProviderConfig(
        id="opensky_network",
        name="OpenSky Network Live Flight Tracking",
        category="Aircraft and Aviation",
        official_docs_url="https://openskynetwork.github.io/opensky-api/rest.html",
        base_url="https://opensky-network.org/api",
        auth_type=AuthType.NONE,
        rate_limit_rpm=10,
        quota_daily=400,
        commercial_use="non_commercial_only",
        license_url="https://opensky-network.org/about/terms-of-use",
        attribution="Aircraft positions by OpenSky Network (CC BY-SA 4.0)",
        cors_status=CORSStatus.BLOCKED,
        backend_proxy_required=True,
        default_timeout=12,
        cache_ttl_sec=15,
        data_classification=DataClassification.LIVE
    ),

    # Category D: Trains and Public Transport
    APIProviderConfig(
        id="open_mobility_data",
        name="Mobility Database & GTFS Feeds Catalog",
        category="Trains and Public Transport",
        official_docs_url="https://mobilitydatabase.org/",
        base_url="https://api.mobilitydatabase.org/v1",
        auth_type=AuthType.NONE,
        rate_limit_rpm=30,
        commercial_use="permitted",
        license_url="https://mobilitydatabase.org/terms",
        attribution="GTFS Transit Schedules by MobilityData",
        cors_status=CORSStatus.ALLOWED,
        backend_proxy_required=True,
        default_timeout=10,
        cache_ttl_sec=3600,
        data_classification=DataClassification.STATIC_REFERENCE
    ),

    # Category E: Ships and Marine Data
    APIProviderConfig(
        id="noaa_marine_coops",
        name="NOAA CO-OPS Tides & Ocean Currents API",
        category="Ships and Marine Data",
        official_docs_url="https://api.tidesandcurrents.noaa.gov/api/prod/",
        base_url="https://api.tidesandcurrents.noaa.gov/api/prod",
        auth_type=AuthType.NONE,
        rate_limit_rpm=60,
        commercial_use="permitted",
        license_url="https://www.noaa.gov/protecting-and-licensing-noaa-technologies",
        attribution="National Oceanic and Atmospheric Administration (NOAA)",
        cors_status=CORSStatus.ALLOWED,
        backend_proxy_required=False,
        default_timeout=10,
        cache_ttl_sec=900,
        data_classification=DataClassification.PERIODIC
    ),

    # Category F: Satellite Tracking and Space
    APIProviderConfig(
        id="where_the_iss_at",
        name="Where the ISS At? Real-Time Satellite Tracker",
        category="Satellite Tracking and Space",
        official_docs_url="https://wheretheiss.at/w/developer",
        base_url="https://api.wheretheiss.at/v1",
        auth_type=AuthType.NONE,
        rate_limit_rpm=60,
        commercial_use="permitted",
        license_url="https://wheretheiss.at",
        attribution="ISS Telemetry via wheretheiss.at",
        cors_status=CORSStatus.ALLOWED,
        backend_proxy_required=False,
        default_timeout=5,
        cache_ttl_sec=5,
        data_classification=DataClassification.CALCULATED
    ),
    APIProviderConfig(
        id="celestrak_orbits",
        name="CelesTrak Orbital Elements (TLE / GP Data)",
        category="Satellite Tracking and Space",
        official_docs_url="https://celestrak.org/NORAD/documentation/gp-data-formats.php",
        base_url="https://celestrak.org/NORAD/elements/gp.php",
        auth_type=AuthType.NONE,
        rate_limit_rpm=30,
        commercial_use="permitted",
        license_url="https://celestrak.org/columns/v04n11.php",
        attribution="Satellite orbit data provided by Dr. T.S. Kelso / CelesTrak",
        cors_status=CORSStatus.ALLOWED,
        backend_proxy_required=True,
        default_timeout=12,
        cache_ttl_sec=7200,
        data_classification=DataClassification.CALCULATED
    ),

    # Category G: Maps and Road Data
    APIProviderConfig(
        id="osm_nominatim",
        name="OpenStreetMap Nominatim Geocoding",
        category="Maps and Road Data",
        official_docs_url="https://nominatim.org/release-docs/latest/api/Overview/",
        base_url="https://nominatim.openstreetmap.org",
        auth_type=AuthType.NONE,
        rate_limit_rpm=60, # Strict 1 req/sec max as per OSM Acceptable Use Policy
        commercial_use="permitted",
        license_url="https://www.openstreetmap.org/copyright",
        attribution="© OpenStreetMap contributors (ODbL)",
        cors_status=CORSStatus.ALLOWED,
        backend_proxy_required=True,
        default_timeout=10,
        cache_ttl_sec=86400, # Cache heavily per OSM policy
        data_classification=DataClassification.STATIC_REFERENCE,
        headers={"User-Agent": "AJAX-AI-Geocoding-Engine/3.0 (ajaysingh.dev)"}
    ),

    # Category H: Earthquakes and Natural Disasters
    APIProviderConfig(
        id="usgs_earthquakes",
        name="USGS Real-Time Earthquake Feeds",
        category="Earthquakes and Natural Disasters",
        official_docs_url="https://earthquake.usgs.gov/fdsnws/event/1/",
        base_url="https://earthquake.usgs.gov/fdsnws/event/1",
        auth_type=AuthType.NONE,
        rate_limit_rpm=60,
        commercial_use="permitted",
        license_url="https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits",
        attribution="USGS Earthquake Hazards Program (Public Domain)",
        cors_status=CORSStatus.ALLOWED,
        backend_proxy_required=False,
        default_timeout=8,
        cache_ttl_sec=120,
        data_classification=DataClassification.LIVE
    ),
    APIProviderConfig(
        id="nasa_eonet",
        name="NASA Earth Observatory Natural Event Tracker (EONET)",
        category="Earthquakes and Natural Disasters",
        official_docs_url="https://eonet.gsfc.nasa.gov/docs/v3",
        base_url="https://eonet.gsfc.nasa.gov/api/v3",
        auth_type=AuthType.NONE,
        rate_limit_rpm=60,
        commercial_use="permitted",
        license_url="https://eonet.gsfc.nasa.gov/docs/v3",
        attribution="NASA Earth Science Division EONET (Public Domain)",
        cors_status=CORSStatus.ALLOWED,
        backend_proxy_required=False,
        default_timeout=10,
        cache_ttl_sec=600,
        data_classification=DataClassification.LIVE
    ),

    # Category I: Government and Scientific Data
    APIProviderConfig(
        id="world_bank_data",
        name="World Bank Indicators & Development Data API",
        category="Government and Scientific Data",
        official_docs_url="https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation",
        base_url="https://api.worldbank.org/v2",
        auth_type=AuthType.NONE,
        rate_limit_rpm=120,
        commercial_use="permitted",
        license_url="https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets",
        attribution="World Bank Open Data (CC BY 4.0)",
        cors_status=CORSStatus.ALLOWED,
        backend_proxy_required=False,
        default_timeout=12,
        cache_ttl_sec=86400,
        data_classification=DataClassification.HISTORICAL
    ),

    # Category J: Currency, Holidays and Reference Data
    APIProviderConfig(
        id="frankfurter_fx",
        name="Frankfurter European Central Bank Exchange Rates",
        category="Currency, Holidays and Reference Data",
        official_docs_url="https://www.frankfurter.app/docs/",
        base_url="https://api.frankfurter.app",
        auth_type=AuthType.NONE,
        rate_limit_rpm=100,
        commercial_use="permitted",
        license_url="https://github.com/hakanensari/frankfurter/blob/master/LICENSE",
        attribution="Exchange rates published by European Central Bank",
        cors_status=CORSStatus.ALLOWED,
        backend_proxy_required=False,
        default_timeout=8,
        cache_ttl_sec=3600,
        data_classification=DataClassification.LIVE
    ),
    APIProviderConfig(
        id="nager_date",
        name="Nager.Date Worldwide Public Holidays API",
        category="Currency, Holidays and Reference Data",
        official_docs_url="https://date.nager.at/Api",
        base_url="https://date.nager.at/api/v3",
        auth_type=AuthType.NONE,
        rate_limit_rpm=60,
        commercial_use="permitted",
        license_url="https://date.nager.at/",
        attribution="Public holiday data by Nager.Date",
        cors_status=CORSStatus.ALLOWED,
        backend_proxy_required=False,
        default_timeout=8,
        cache_ttl_sec=86400,
        data_classification=DataClassification.STATIC_REFERENCE
    ),
    APIProviderConfig(
        id="rest_countries",
        name="REST Countries Demographic & Geographic Data",
        category="Currency, Holidays and Reference Data",
        official_docs_url="https://gitlab.com/restcountries/restcountries",
        base_url="https://restcountries.com/v3.1",
        auth_type=AuthType.NONE,
        rate_limit_rpm=60,
        commercial_use="permitted",
        license_url="https://www.mozilla.org/en-US/MPL/2.0/",
        attribution="REST Countries Open API",
        cors_status=CORSStatus.ALLOWED,
        backend_proxy_required=False,
        default_timeout=10,
        cache_ttl_sec=86400,
        data_classification=DataClassification.STATIC_REFERENCE
    ),

    # Category K: Demo and Testing APIs
    APIProviderConfig(
        id="jsonplaceholder",
        name="JSONPlaceholder Mock REST API",
        category="Demo and Testing APIs",
        official_docs_url="https://jsonplaceholder.typicode.com/",
        base_url="https://jsonplaceholder.typicode.com",
        auth_type=AuthType.NONE,
        rate_limit_rpm=120,
        commercial_use="permitted",
        license_url="https://github.com/typicode/jsonplaceholder/blob/master/LICENSE",
        attribution="Provided by typicode for mock testing",
        cors_status=CORSStatus.ALLOWED,
        backend_proxy_required=False,
        default_timeout=8,
        cache_ttl_sec=60,
        data_classification=DataClassification.SAMPLE
    )
]

class APIConnectorRegistry:
    """Manages the full lifecycle of API providers, credentials, and category lookups."""

    def __init__(self):
        self._providers: Dict[str, APIProviderConfig] = {
            p.id: p for p in INITIAL_VERIFIED_PROVIDERS
        }

    def register(self, config: APIProviderConfig) -> None:
        self._providers[config.id] = config

    def get(self, provider_id: str) -> Optional[APIProviderConfig]:
        return self._providers.get(provider_id)

    def list_all(self, category: Optional[str] = None) -> List[APIProviderConfig]:
        if category:
            return [p for p in self._providers.values() if p.category.lower() == category.lower()]
        return list(self._providers.values())

    def list_categories(self) -> List[str]:
        return sorted(list({p.category for p in self._providers.values()}))

connector_registry = APIConnectorRegistry()

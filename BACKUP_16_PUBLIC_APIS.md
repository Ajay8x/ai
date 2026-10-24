# 🔌 AJAX AI - 16 Public APIs Master Backup & Specification

> **Notice:** This document serves as a permanent backup of the 16 Public API connectors, parameters, authentication rules, and tool wrappers retired from the core codebase.

## 📑 Catalog of Retired APIs

| # | Provider ID | API Name | Category | Authentication | Rate Limit |
|---|---|---|---|---|---|
| 1 | `open_meteo` | **Open-Meteo Weather & Air Quality API** | Weather and Environment | None (Free Open Access) | 120 RPM / 10,000 daily quota |
| 2 | `openaq` | **OpenAQ Global Air Quality API** | Weather and Environment | API Key (Header: X-API-Key) | 60 RPM |
| 3 | `windy_webcams` | **Windy Webcams Global API** | Public Webcams and Traffic | API Key (Header: x-windy-api-key) | 30 RPM / 500 daily quota |
| 4 | `opensky_network` | **OpenSky Network Live Flight Tracking** | Aircraft and Aviation | None (Anonymous) / Basic Auth (Higher quota) | 10 RPM / 400 daily quota |
| 5 | `open_mobility_data` | **Mobility Database & GTFS Transit Feeds** | Trains and Public Transport | None / Optional Token | 30 RPM |
| 6 | `noaa_marine_coops` | **NOAA CO-OPS Tides & Ocean Currents API** | Ships and Marine Data | None (Public Domain) | 60 RPM |
| 7 | `where_the_iss_at` | **Where the ISS At? Real-Time Satellite Tracker** | Satellite Tracking and Space | None | 60 RPM |
| 8 | `celestrak_orbits` | **CelesTrak Orbital Elements (TLE / GP Data)** | Satellite Tracking and Space | None | 30 RPM |
| 9 | `osm_nominatim` | **OpenStreetMap Nominatim Geocoding** | Maps and Road Data | None (Requires Custom User-Agent Header) | 60 RPM (Max 1 req/sec strict policy) |
| 10 | `usgs_earthquakes` | **USGS Real-Time Earthquake Feeds** | Earthquakes and Natural Disasters | None (Public Domain) | 60 RPM |
| 11 | `nasa_eonet` | **NASA Earth Observatory Natural Event Tracker (EONET)** | Earthquakes and Natural Disasters | None (Public Domain) | 60 RPM |
| 12 | `world_bank_data` | **World Bank Indicators & Development Data API** | Government and Scientific Data | None | 120 RPM |
| 13 | `frankfurter_fx` | **Frankfurter European Central Bank Exchange Rates** | Currency, Holidays and Reference Data | None | 100 RPM |
| 14 | `nager_date` | **Nager.Date Worldwide Public Holidays API** | Currency, Holidays and Reference Data | None | 60 RPM |
| 15 | `rest_countries` | **REST Countries Demographic & Geographic Data** | Currency, Holidays and Reference Data | None | 60 RPM |
| 16 | `jsonplaceholder` | **JSONPlaceholder Mock REST API** | Demo and Testing APIs | None | Unlimited |

---

## 🔍 Deep Dive API Specifications

### 1. Open-Meteo Weather & Air Quality API (`open_meteo`)
- **Category:** Weather and Environment
- **Base URL:** `https://api.open-meteo.com/v1`
- **Official Documentation:** [https://open-meteo.com/en/docs](https://open-meteo.com/en/docs)
- **Authentication:** None (Free Open Access)
- **Rate Limit:** 120 RPM / 10,000 daily quota
- **Data Classification:** `Live`
- **Attribution / Licensing:** Weather data by Open-Meteo.com (CC BY 4.0)

#### Endpoints & Query Signatures:
- **Action:** `current_weather`
  - **Path:** `/v1/forecast`
  - **Description:** Fetch real-time weather, temperature, windspeed, and weather codes.
  - **Sample Parameters:** `{'latitude': 28.6139, 'longitude': 77.209, 'current_weather': True, 'hourly': 'temperature_2m', 'forecast_days': 3}`
- **Action:** `air_quality`
  - **Path:** `https://air-quality-api.open-meteo.com/v1/air-quality`
  - **Description:** Air quality indices including PM2.5, PM10, CO, NO2, O3, and European AQI.
  - **Sample Parameters:** `{'latitude': 28.6139, 'longitude': 77.209, 'current': 'pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,european_aqi'}`

### 2. OpenAQ Global Air Quality API (`openaq`)
- **Category:** Weather and Environment
- **Base URL:** `https://api.openaq.org/v2`
- **Official Documentation:** [https://docs.openaq.org/](https://docs.openaq.org/)
- **Authentication:** API Key (Header: X-API-Key)
- **Rate Limit:** 60 RPM
- **Data Classification:** `Live`
- **Attribution / Licensing:** Data provided by OpenAQ Community

#### Endpoints & Query Signatures:
- **Action:** `measurements`
  - **Path:** `/v2/latest`
  - **Description:** Community sensor air pollution measurements across global stations.
  - **Sample Parameters:** `{'city': 'Delhi', 'country': 'IN', 'limit': 5}`

### 3. Windy Webcams Global API (`windy_webcams`)
- **Category:** Public Webcams and Traffic
- **Base URL:** `https://api.windy.com/webcams/v3`
- **Official Documentation:** [https://api.windy.com/webcams/docs](https://api.windy.com/webcams/docs)
- **Authentication:** API Key (Header: x-windy-api-key)
- **Rate Limit:** 30 RPM / 500 daily quota
- **Data Classification:** `Periodic`
- **Attribution / Licensing:** Webcam imagery provided by Windy.com

#### Endpoints & Query Signatures:
- **Action:** `webcams`
  - **Path:** `/webcams/api/v3/webcams`
  - **Description:** Live streaming cameras, traffic webcams, and weather snapshots globally.
  - **Sample Parameters:** `{'country': 'IN', 'category': 'traffic', 'limit': 24}`

### 4. OpenSky Network Live Flight Tracking (`opensky_network`)
- **Category:** Aircraft and Aviation
- **Base URL:** `https://opensky-network.org/api`
- **Official Documentation:** [https://openskynetwork.github.io/opensky-api/rest.html](https://openskynetwork.github.io/opensky-api/rest.html)
- **Authentication:** None (Anonymous) / Basic Auth (Higher quota)
- **Rate Limit:** 10 RPM / 400 daily quota
- **Data Classification:** `Live`
- **Attribution / Licensing:** Aircraft positions by OpenSky Network (CC BY-SA 4.0)

#### Endpoints & Query Signatures:
- **Action:** `states_all`
  - **Path:** `/states/all`
  - **Description:** Live ADS-B aircraft positions, transponder icao24, altitude, velocity, and heading.
  - **Sample Parameters:** `{'lamin': 20.0, 'lamax': 30.0, 'lomin': 70.0, 'lomax': 80.0, 'icao24': '3c6674'}`

### 5. Mobility Database & GTFS Transit Feeds (`open_mobility_data`)
- **Category:** Trains and Public Transport
- **Base URL:** `https://api.mobilitydatabase.org/v1`
- **Official Documentation:** [https://mobilitydatabase.org/](https://mobilitydatabase.org/)
- **Authentication:** None / Optional Token
- **Rate Limit:** 30 RPM
- **Data Classification:** `Static Reference`
- **Attribution / Licensing:** GTFS Transit Schedules by MobilityData

#### Endpoints & Query Signatures:
- **Action:** `feeds`
  - **Path:** `/feeds`
  - **Description:** Public transit GTFS schedules, train routes, bus stops, and metropolitan feeds.
  - **Sample Parameters:** `{'limit': 10, 'status': 'active', 'provider': 'Delhi Metro'}`

### 6. NOAA CO-OPS Tides & Ocean Currents API (`noaa_marine_coops`)
- **Category:** Ships and Marine Data
- **Base URL:** `https://api.tidesandcurrents.noaa.gov/api/prod`
- **Official Documentation:** [https://api.tidesandcurrents.noaa.gov/api/prod/](https://api.tidesandcurrents.noaa.gov/api/prod/)
- **Authentication:** None (Public Domain)
- **Rate Limit:** 60 RPM
- **Data Classification:** `Periodic`
- **Attribution / Licensing:** National Oceanic and Atmospheric Administration (NOAA)

#### Endpoints & Query Signatures:
- **Action:** `datagetter`
  - **Path:** `/datagetter`
  - **Description:** Real-time water levels, ocean tides, marine currents, and barometric pressure.
  - **Sample Parameters:** `{'station': '8454000', 'product': 'water_level', 'datum': 'MLLW', 'units': 'metric', 'date': 'latest', 'format': 'json'}`

### 7. Where the ISS At? Real-Time Satellite Tracker (`where_the_iss_at`)
- **Category:** Satellite Tracking and Space
- **Base URL:** `https://api.wheretheiss.at/v1`
- **Official Documentation:** [https://wheretheiss.at/w/developer](https://wheretheiss.at/w/developer)
- **Authentication:** None
- **Rate Limit:** 60 RPM
- **Data Classification:** `Calculated Telemetry`
- **Attribution / Licensing:** ISS Telemetry via wheretheiss.at

#### Endpoints & Query Signatures:
- **Action:** `satellites`
  - **Path:** `/satellites/25544`
  - **Description:** Current coordinates (latitude, longitude, altitude, velocity, visibility) of the ISS.
  - **Sample Parameters:** `{'norad_id': 25544}`

### 8. CelesTrak Orbital Elements (TLE / GP Data) (`celestrak_orbits`)
- **Category:** Satellite Tracking and Space
- **Base URL:** `https://celestrak.org/NORAD/elements/gp.php`
- **Official Documentation:** [https://celestrak.org/NORAD/documentation/gp-data-formats.php](https://celestrak.org/NORAD/documentation/gp-data-formats.php)
- **Authentication:** None
- **Rate Limit:** 30 RPM
- **Data Classification:** `Calculated Ephemeris`
- **Attribution / Licensing:** Satellite orbit data provided by Dr. T.S. Kelso / CelesTrak

#### Endpoints & Query Signatures:
- **Action:** `gp_elements`
  - **Path:** `/NORAD/elements/gp.php`
  - **Description:** Two-Line Element sets (TLE) and general perturbation orbit data for all orbiting satellites.
  - **Sample Parameters:** `{'GROUP': 'stations', 'FORMAT': 'json', 'CATNR': 25544}`

### 9. OpenStreetMap Nominatim Geocoding (`osm_nominatim`)
- **Category:** Maps and Road Data
- **Base URL:** `https://nominatim.openstreetmap.org`
- **Official Documentation:** [https://nominatim.org/release-docs/latest/api/Overview/](https://nominatim.org/release-docs/latest/api/Overview/)
- **Authentication:** None (Requires Custom User-Agent Header)
- **Rate Limit:** 60 RPM (Max 1 req/sec strict policy)
- **Data Classification:** `Static Reference`
- **Attribution / Licensing:** © OpenStreetMap contributors (ODbL)

#### Endpoints & Query Signatures:
- **Action:** `search`
  - **Path:** `/search`
  - **Description:** Forward geocoding: converts address/place names to latitude & longitude.
  - **Sample Parameters:** `{'q': 'India Gate, New Delhi', 'format': 'json', 'limit': 3}`
- **Action:** `reverse`
  - **Path:** `/reverse`
  - **Description:** Reverse geocoding: converts GPS coordinates to street addresses.
  - **Sample Parameters:** `{'lat': 28.6129, 'lon': 77.2295, 'format': 'json'}`

### 10. USGS Real-Time Earthquake Feeds (`usgs_earthquakes`)
- **Category:** Earthquakes and Natural Disasters
- **Base URL:** `https://earthquake.usgs.gov/fdsnws/event/1`
- **Official Documentation:** [https://earthquake.usgs.gov/fdsnws/event/1/](https://earthquake.usgs.gov/fdsnws/event/1/)
- **Authentication:** None (Public Domain)
- **Rate Limit:** 60 RPM
- **Data Classification:** `Live`
- **Attribution / Licensing:** USGS Earthquake Hazards Program

#### Endpoints & Query Signatures:
- **Action:** `query`
  - **Path:** `/query`
  - **Description:** Global seismic events, rich Richter scale magnitude, hypocenter depth, tsunami alerts.
  - **Sample Parameters:** `{'format': 'geojson', 'minmagnitude': 3.0, 'limit': 10, 'orderby': 'time'}`

### 11. NASA Earth Observatory Natural Event Tracker (EONET) (`nasa_eonet`)
- **Category:** Earthquakes and Natural Disasters
- **Base URL:** `https://eonet.gsfc.nasa.gov/api/v3`
- **Official Documentation:** [https://eonet.gsfc.nasa.gov/docs/v3](https://eonet.gsfc.nasa.gov/docs/v3)
- **Authentication:** None (Public Domain)
- **Rate Limit:** 60 RPM
- **Data Classification:** `Live`
- **Attribution / Licensing:** NASA Earth Science Division EONET

#### Endpoints & Query Signatures:
- **Action:** `events`
  - **Path:** `/events`
  - **Description:** Wildfires, severe storms, volcanoes, sea ice anomalies tracked by NASA satellites.
  - **Sample Parameters:** `{'limit': 10, 'status': 'open', 'category': 'wildfires,severeStorms'}`

### 12. World Bank Indicators & Development Data API (`world_bank_data`)
- **Category:** Government and Scientific Data
- **Base URL:** `https://api.worldbank.org/v2`
- **Official Documentation:** [https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation)
- **Authentication:** None
- **Rate Limit:** 120 RPM
- **Data Classification:** `Historical`
- **Attribution / Licensing:** World Bank Open Data (CC BY 4.0)

#### Endpoints & Query Signatures:
- **Action:** `indicator`
  - **Path:** `/country/IND/indicator/NY.GDP.MKTP.CD`
  - **Description:** Macroeconomic data: GDP, inflation, population, literacy across all sovereign nations.
  - **Sample Parameters:** `{'format': 'json', 'per_page': 10}`

### 13. Frankfurter European Central Bank Exchange Rates (`frankfurter_fx`)
- **Category:** Currency, Holidays and Reference Data
- **Base URL:** `https://api.frankfurter.app`
- **Official Documentation:** [https://www.frankfurter.app/docs/](https://www.frankfurter.app/docs/)
- **Authentication:** None
- **Rate Limit:** 100 RPM
- **Data Classification:** `Live Currency`
- **Attribution / Licensing:** Exchange rates published by European Central Bank

#### Endpoints & Query Signatures:
- **Action:** `latest`
  - **Path:** `/latest`
  - **Description:** Forex conversion across 30+ fiat currencies updated daily by ECB.
  - **Sample Parameters:** `{'from': 'USD', 'to': 'INR,EUR,GBP', 'amount': 100}`

### 14. Nager.Date Worldwide Public Holidays API (`nager_date`)
- **Category:** Currency, Holidays and Reference Data
- **Base URL:** `https://date.nager.at/api/v3`
- **Official Documentation:** [https://date.nager.at/Api](https://date.nager.at/Api)
- **Authentication:** None
- **Rate Limit:** 60 RPM
- **Data Classification:** `Static Reference`
- **Attribution / Licensing:** Public holiday data by Nager.Date

#### Endpoints & Query Signatures:
- **Action:** `public_holidays`
  - **Path:** `/PublicHolidays/2026/IN`
  - **Description:** Official national, state, and statutory public holidays for 100+ countries.
  - **Sample Parameters:** `{'year': 2026, 'countryCode': 'IN'}`

### 15. REST Countries Demographic & Geographic Data (`rest_countries`)
- **Category:** Currency, Holidays and Reference Data
- **Base URL:** `https://restcountries.com/v3.1`
- **Official Documentation:** [https://gitlab.com/restcountries/restcountries](https://gitlab.com/restcountries/restcountries)
- **Authentication:** None
- **Rate Limit:** 60 RPM
- **Data Classification:** `Static Reference`
- **Attribution / Licensing:** REST Countries Open API (Mozilla Public License)

#### Endpoints & Query Signatures:
- **Action:** `country_name`
  - **Path:** `/name/india`
  - **Description:** Capitals, borders, currencies, languages, timezones, and flags for all world nations.
  - **Sample Parameters:** `{'fullText': True}`

### 16. JSONPlaceholder Mock REST API (`jsonplaceholder`)
- **Category:** Demo and Testing APIs
- **Base URL:** `https://jsonplaceholder.typicode.com`
- **Official Documentation:** [https://jsonplaceholder.typicode.com/](https://jsonplaceholder.typicode.com/)
- **Authentication:** None
- **Rate Limit:** Unlimited
- **Data Classification:** `Mock Test`
- **Attribution / Licensing:** JSONPlaceholder Free Mock Service

#### Endpoints & Query Signatures:
- **Action:** `posts`
  - **Path:** `/posts/1`
  - **Description:** Mock CRUD testing endpoint for REST integration pipelines.
  - **Sample Parameters:** `{}`

---

## 🛠️ Retired Agent Tools (Python Wrappers)

| Tool Name | Python Class | Underlying Provider | Description |
|---|---|---|---|
| `get_iss_coordinates` | `ISSTrackerTool` | `where_the_iss_at` | Real-time ISS latitude, longitude, and velocity tracking. |
| `get_recent_earthquakes` | `EarthquakeTrackerTool` | `usgs_earthquakes` | Live Richter magnitude seismic tracking. |
| `convert_currency` | `CurrencyExchangeTool` | `frankfurter_fx` | Forex fiat conversion using European Central Bank rates. |
| `geocode_location` | `GeocodeTool` | `osm_nominatim` | Address to GPS coordinates resolution via OpenStreetMap. |
| `get_public_holidays` | `PublicHolidayTool` | `nager_date` | Worldwide official calendar holidays lookup. |

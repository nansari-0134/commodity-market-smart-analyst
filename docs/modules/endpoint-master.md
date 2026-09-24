# Module: Endpoint & API Metadata Master

The **Endpoint & API Metadata Master** (`apps.endpoints`) formalizes the network routing templates, HTTP methods, transport protocols, request parameter schemas, response payload serialization, and envelope extraction rules across global commodity market data feeds.

---

## 1. Architectural Mission & Context

In a quantitative research system, decoupling **WHO** provides data, **WHAT** domain entity is populated, and **HOW** network transport occurs is essential:

```mermaid
graph LR
    P[ProviderMaster<br/>WHO: Base URL & 12-Factor Auth] --> EP[EndpointMaster<br/>HOW: Route Path, Method, Envelope]
    EP --> DS[DatasetMaster<br/>WHAT: Ingestion & Retention Target]
    DS --> VM[VariableMaster<br/>METRIC: Canonical Feature]
```

### The Lean Architectural Standard:
1. **Zero Rate Limit Duplication**: Rate limiting and credential isolation remain strictly at the `ProviderMaster` level. Endpoints do not duplicate account-level quotas.
2. **Consolidated Parameters**: Clean `default_params` and `custom_headers` JSONFields eliminate fragmented parameter schemas.
3. **Targeted Transport Protocols**: Concentrates on practical commodity transport protocols (`REST_HTTP`, `FTP_SFTP`, and `WEBSOCKET`).

---

## 2. Relational Schema & Enumerations

### 1. Transport Protocols (`ProtocolType`)
* `REST_HTTP`: Standard Web RESTful JSON/CSV endpoint.
* `FTP_SFTP`: Batch file download server (e.g. USDA reports, exchange settlement files).
* `WEBSOCKET`: Real-time bi-directional streaming feed.

### 2. HTTP Request Methods (`HttpMethod`)
* `GET`: Idempotent data retrieval.
* `POST`: Batched queries or extraction payload submission (e.g. Bloomberg B-PIPE ticker arrays, Refinitiv DataScope raw extraction).

### 3. Payload Serialization (`ResponseFormat`)
* `JSON`: Nested or tabular JSON records.
* `CSV`: Flat comma-separated records.
* `TSV`: Tab-separated exchange files.
* `XML`: Legacy government bulletins.
* `ZIP`: Compressed archives containing multi-file reports.
* `PARQUET`: Columnar high-speed analytical files.
* `EXCEL_XLSX`: Spreadsheets with multiple balance sheets.

### 4. Data Envelope Extraction (`data_envelope_path`)
External APIs wrap tabular records inside metadata envelopes. The `data_envelope_path` defines the dot-separated key hierarchy needed to reach the target observation array:
* `response.data` (EIA v2 APIs)
* `observations` (FRED Economic Series)
* `data` (USDA NASS QuickStats)
* `properties.periods` (NOAA Weather Grid Forecasts)
* `results` (Platts Market Data, CME Settlements)
* `""` (Empty string): The response root is already a flat JSON array (e.g. CFTC Socrata open data).

---

## 3. URL Resolution & Parameter Building

### Safe URL Resolution (`get_full_url`)
The model combines `provider.base_url` with `path_template` using slash normalization and keyword argument interpolation:

```python
endpoint = EndpointMaster.objects.get(code="EIA_PETROLEUM_SPOT_PRICES")
# Combines "https://api.eia.gov/v2/" + "petroleum/pri/spt/data/"
url = endpoint.get_full_url()
# Output: "https://api.eia.gov/v2/petroleum/pri/spt/data/"

# Path interpolation with keyword arguments
forecast = EndpointMaster.objects.get(code="NOAA_WEATHER_GRIDPOINTS")
# path_template: "gridpoints/{wfo}/{x},{y}/forecast"
url = forecast.get_full_url(wfo="DVN", x=32, y=64)
# Output: "https://api.weather.gov/gridpoints/DVN/32,64/forecast"
```

### Dynamic Parameter Merging (`build_request_params`)
Merges stored defaults with dynamic query overrides:

```python
endpoint = EndpointMaster.objects.get(code="FRED_SERIES_OBSERVATIONS")
# Stored defaults: {"file_type": "json", "sort_order": "desc"}
runtime = endpoint.build_request_params({"series_id": "DCOILWTICO", "limit": 100})
# Output: {"file_type": "json", "sort_order": "desc", "series_id": "DCOILWTICO", "limit": 100}
```

---

## 4. Benchmark Catalog Feeds (26 Institutional Endpoints)

The platform ships 26 institutional benchmark endpoint specifications out-of-the-box:

| Endpoint Code | Provider | Method | Format | Target Dataset | Data Envelope |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `EIA_PETROLEUM_SPOT_PRICES` | `EIA_GOV` | GET | JSON | `EIA_WPSR_PETROLEUM_STOCKS` | `response.data` |
| `EIA_CRUDE_STOCKS_WEEKLY` | `EIA_GOV` | GET | JSON | `EIA_WPSR_PETROLEUM_STOCKS` | `response.data` |
| `EIA_NATGAS_STORAGE_WEEKLY` | `EIA_GOV` | GET | JSON | `EIA_WEEKLY_NATURAL_GAS_STORAGE` | `response.data` |
| `CFTC_COT_DISAGGREGATED_FUT` | `CFTC_GOV` | GET | JSON | `CFTC_COT_DISAGGREGATED_FUT_OPT` | Root Array |
| `CFTC_COT_FINANCIAL_FUT` | `CFTC_GOV` | GET | JSON | `None` (Discovery) | Root Array |
| `FRED_SERIES_OBSERVATIONS` | `FRED_FED` | GET | JSON | `None` (Macro) | `observations` |
| `FRED_SERIES_METADATA` | `FRED_FED` | GET | JSON | `None` (Reference) | `seriess` |
| `USDA_EXPORT_SALES_COMMODITIES`| `USDA_FAS` | GET | JSON | `USDA_EXPORT_SALES_WEEKLY` | Root Array |
| `USDA_EXPORT_SALES_COUNTRIES` | `USDA_FAS` | GET | JSON | `USDA_EXPORT_SALES_WEEKLY` | Root Array |
| `USDA_QUICKSTATS_DATA` | `USDA_NASS`| GET | JSON | `USDA_CROP_PROGRESS_WEEKLY` | `data` |
| `NOAA_WEATHER_GRIDPOINTS` | `NOAA_NWS` | GET | JSON | `NOAA_CPC_ENSO_OUTLOOK` | `properties.periods` |
| `CME_DATAMINE_EOD_SETTLE` | `CME_DATAMINE` | GET | JSON | `CME_FUTURES_EOD` | `results` |
| `CME_DATAMINE_BLOCK_TRADES` | `CME_DATAMINE` | GET | JSON | `CME_FUTURES_EOD` | `trades` |
| `ICE_DATA_COMMODITIES_EOD` | `ICE_DATA_SERVICES` | GET | JSON | `ICE_BRENT_DAILY_SETTLEMENTS`| `data.settlements` |
| `LME_NONFERROUS_OFFICIAL` | `LME_DATA` | GET | JSON | `LME_DAILY_OFFICIAL_PRICES` | `prices` |
| `EEX_POWER_BENCHMARKS` | `EEX_DATA` | GET | JSON | `EEX_EUA_CARBON_AUCTION_RESULTS` | `items` |
| `MCX_INDIA_BHAVCOPY` | `MCX_INDIA` | GET | CSV | `MCX_DAILY_COMMODITY_SETTLEMENTS` | Root Stream |
| `INE_CRUDE_DAILY_REPORT` | `SHFE_INE` | GET | JSON | `SHFE_DAILY_METALS_SETTLEMENTS` | `report.data` |
| `ARGUS_DIRECT_CRUDE_PRICES` | `ARGUS_MEDIA`| GET | JSON | `ARGUS_US_GULF_CRUDE_ASSESSMENTS`| `assessments` |
| `PLATTS_COMMODITY_ASSESSMENTS` | `SP_GLOBAL_PLATTS` | GET | JSON | `PLATTS_NORTH_SEA_BRENT_ASSESSMENTS` | `results` |
| `FASTMARKETS_BATTERY_METALS` | `FASTMARKETS` | GET | JSON | `None` (Physical) | `data` |
| `OPIS_REFINED_SPOT_PRICES` | `OPIS_ENERGY` | GET | JSON | `None` (Physical) | `spot_prices` |
| `BLOOMBERG_BPIPE_REFERENCE` | `BLOOMBERG` | POST | JSON | `None` (Aggregator) | `response.securityData` |
| `REFINITIV_DATASCOPE_RAW` | `LSEG_REFINITIV`| POST | CSV | `None` (Aggregator) | Root Stream |
| `KPLER_SEABORNE_FLOWS` | `KPLER` | GET | JSON | `None` (Vessel AIS) | `flows` |
| `INTERNAL_FORWARD_CURVE_CALC` | `INTERNAL_QUANT`| GET | JSON | `None` (Synthetic) | `data.curves` |

---

## 5. Pluggable Architecture & Seeding

* **Interface**: `BaseEndpointCatalogProvider` (`apps/endpoints/providers/base.py`)
* **Default Implementation**: `StaticEndpointCatalogProvider` (`apps/endpoints/providers/static_catalog.py`)
* **Resolver**: `get_endpoint_catalog()` honors `settings.ENDPOINT_CATALOG_PROVIDER`
* **Idempotent CLI Command**:
```powershell
.\.venv\Scripts\python.exe manage.py seed_endpoints
```
Supports the `--clear` flag for database resets without risking data duplication.

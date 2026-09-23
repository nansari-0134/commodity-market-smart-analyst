# Module: Provider & Source Master

The **Provider & Source Master** (`apps.providers`) serves as the institutional catalog for external data vendors, government statistical agencies, market execution venues, 12-factor credential environment references, rate limit policies, and fallback failovers.

---

## 1. Architectural Mission & Vendor Tiers

Commodity market data is fundamentally fragmented across diverse commercial and governmental organizations:

```mermaid
graph TD
    PM[ProviderMaster<br/>apps/providers] --> GP[1. Government & Public Agencies<br/>EIA, USDA, CFTC, FRED, NOAA]
    PM --> ED[2. Exchange Direct Feeds<br/>CME Datamine, ICE, LME, EEX, MCX, INE]
    PM --> PR[3. Price Reporting Agencies (PRAs)<br/>Argus Media, Platts, Fastmarkets, OPIS]
    PM --> CA[4. Commercial Aggregators<br/>Bloomberg B-PIPE, LSEG Refinitiv]
    PM --> AD[5. Alternative & Physical Flows<br/>Kpler, Vortexa, Satellite AIS]
    PM --> IQ[6. Internal Quant Engines<br/>Forward Curve Splines, Crack Spreads]

    PM --> DS[DatasetMaster<br/>apps/datasets]
    DS --> VM[VariableMaster<br/>apps/variables]
```

### The 6 Institutional Provider Categories

| Category Code | Classification | Examples | Typical Authentication |
| :--- | :--- | :--- | :--- |
| `GOVERNMENT_PUBLIC` | Official statistical and regulatory agencies | EIA, USDA FAS, CFTC, FRED, NOAA | Open data or basic API Key (`EIA_API_KEY`, `FRED_API_KEY`) |
| `EXCHANGE_DIRECT` | Designated contract markets & clearing houses | CME Datamine, ICE Data Services, LME | OAuth 2.0 Client Credentials, Bearer Token |
| `PRICE_REPORTING_AGENCY` | Physical spot assessment publishers | Argus Media, S&P Global Platts, Fastmarkets | Bearer Token, API Key Header |
| `COMMERCIAL_AGGREGATOR` | Multi-asset financial terminals | Bloomberg (B-PIPE), LSEG Refinitiv (DataScope) | OAuth 2.0, Enterprise Session Tokens |
| `ALTERNATIVE_DATA` | Satellite, AIS vessel tracking, radar tank levels | Kpler, Vortexa, Planet Labs | Bearer Token |
| `INTERNAL_ENGINE` | Algorithmic curve fitting & spread models | Native platform quantitative calculation engine | Zero network auth (`NONE_PUBLIC`) |

---

## 2. 12-Factor Security & Zero Secret Leakage

In institutional financial engineering, storing raw API keys, passwords, or tokens in relational database rows is a critical vulnerability. If a database backup is taken or a developer views the Django Admin portal, credentials can be leaked.

### The Environment Variable Reference Standard
`ProviderMaster` strictly stores the **name of the environment variable** rather than the secret itself:

* **Database Field**: `env_var_name = "EIA_API_KEY"`
* **Runtime Resolution**: At execution time, ingestion workers resolve `os.environ.get(provider.env_var_name)`.
* **Zero Database Exposure**: Relational database dumps, migration files, and admin change pages expose zero API keys or passwords.

### Supported Authentication Protocols (`AuthType`)
1. **`NONE_PUBLIC`**: Open data requiring zero credentials (e.g. CFTC Commitments of Traders, NOAA weather API).
2. **`API_KEY_QUERY_PARAM`**: Key appended to HTTP URL parameters (e.g. `?api_key=${EIA_API_KEY}`).
3. **`API_KEY_HEADER`**: Key sent via custom HTTP header (e.g. `X-API-KEY: ${USDA_API_KEY}`).
4. **`BEARER_TOKEN`**: Standard OAuth2 / JWT token sent via `Authorization: Bearer ${TOKEN}` header.
5. **`BASIC_AUTH`**: Base64 encoded username/password credentials.
6. **`OAUTH2_CLIENT_CREDENTIALS`**: Automated client-secret token exchange flow (CME Datamine, Bloomberg).

---

## 3. Proactive Rate Limiting & Backoff Policies

External market data APIs strictly enforce quota limits and throttle aggressive scrapers. `ProviderMaster` defines embedded rate budgets:

* **`rate_limit_requests`**: Maximum request quota permitted per window (e.g. `120`).
* **`rate_limit_window_seconds`**: Rate limit time window (e.g. `60` for 120 req/min; `3600` for 5,000 req/hr).
* **`backoff_seconds`**: Exponential retry backoff delay upon encountering HTTP 429 (`Too Many Requests`).
* **`has_rate_limit`**: Property returning `False` for unmetered internal or unlimited feeds.

---

## 4. Redundancy & Fallback Chaining

When a primary vendor experiences network downtime or an exchange API experiences latency, quant systems must cleanly failover to a secondary reference source:

* **Self-Referential Fallback**: `ProviderMaster.fallback_provider` links to another `ProviderMaster` instance.
* **Benchmark Fallback Pairs**:
  - `CME_DATAMINE` ➔ Fallback: `ICE_DATA_SERVICES`
  - `ICE_DATA_SERVICES` ➔ Fallback: `CME_DATAMINE`
  - `ARGUS_MEDIA` ➔ Fallback: `SP_GLOBAL_PLATTS`
  - `SP_GLOBAL_PLATTS` ➔ Fallback: `ARGUS_MEDIA`
  - `BLOOMBERG` ➔ Fallback: `LSEG_REFINITIV`
  - `LSEG_REFINITIV` ➔ Fallback: `BLOOMBERG`

---

## 5. Pluggable Catalog Provider Architecture

In accordance with Platform Architectural Directive 1, the Provider catalog is abstracted behind the **Provider Strategy + Factory Pattern**:

```
apps/providers/providers/
├── __init__.py
├── base.py            # BaseProviderCatalogProvider & RawProviderSpec DTO
├── static_catalog.py  # StaticProviderCatalogProvider (20 benchmark global providers)
└── factory.py         # get_provider_catalog() resolver
```

### Static Benchmark Providers (20 Global Feeds)
The built-in `StaticProviderCatalogProvider` seeds:
1. **US Agencies**: `EIA_GOV`, `USDA_FAS`, `USDA_NASS`, `CFTC_GOV`, `FRED_FED`, `NOAA_NWS`.
2. **Global Venues**: `CME_DATAMINE`, `ICE_DATA_SERVICES`, `LME_DATA`, `EEX_DATA`, `MCX_INDIA`, `SHFE_INE`.
3. **PRAs & Benchmarks**: `ARGUS_MEDIA`, `SP_GLOBAL_PLATTS`, `FASTMARKETS`, `OPIS_ENERGY`.
4. **Aggregators & Alternative**: `BLOOMBERG`, `LSEG_REFINITIV`, `KPLER`, `INTERNAL_QUANT`.

---

## 6. Schema & Field Reference (`ProviderMaster`)

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `UUID` | Primary key. |
| `code` | `CharField(50)` | Unique canonical slug (e.g. `EIA_GOV`, `CME_DATAMINE`). |
| `name` | `CharField(120)` | Full institutional organization title. |
| `description` | `TextField` | Scope, methodology, and licensing notes. |
| `provider_type` | `CharField(32)` | Categorization (`GOVERNMENT_PUBLIC`, `EXCHANGE_DIRECT`, etc.). |
| `base_url` | `URLField(255)` | Root service or endpoint URL. |
| `documentation_url`| `URLField(255)` | Developer documentation portal URL. |
| `support_contact` | `CharField(150)` | Technical support contact email. |
| `auth_type` | `CharField(32)` | Authentication protocol (`NONE_PUBLIC`, `BEARER_TOKEN`, etc.). |
| `env_var_name` | `CharField(80)` | Environment variable storing the secret. |
| `auth_param_name` | `CharField(60)` | Query param or header name (`X-API-KEY`, `api_key`). |
| `rate_limit_requests`| `PositiveIntegerField` | Request quota per window (null = unmetered). |
| `rate_limit_window_seconds`| `PositiveIntegerField` | Time window in seconds (default 60s). |
| `backoff_seconds` | `PositiveIntegerField` | Retry delay upon HTTP 429. |
| `target_sla_pct` | `DecimalField(5,2)` | Uptime SLA target (e.g. 99.80%). |
| `fallback_provider`| `ForeignKey('self')` | Secondary failover vendor. |
| `is_active` | `BooleanField` | Active status in ingestion pipelines. |
| `display_order` | `PositiveIntegerField` | Sorting order in dashboards and tables. |

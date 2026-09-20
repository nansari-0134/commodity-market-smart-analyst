# REST API Architecture & Data Access

The **Commodity Market Intelligence Platform** exposes a comprehensive, high-performance REST API designed for algorithmic trading systems, quantitative research workflows, frontend user interfaces, and automated pipeline integration.

!!! warning "Disclaimer: Analytical Tool Only"
    The data and endpoints provided by this API are strictly for **analytical intelligence, data engineering, and workflow automation**. This system **does not provide trading calls, financial signals, or investment advice**.

---

## Key API Features

- **Standardized JSON Schema**: Predictable payload structures and standard HTTP response codes across all endpoints.
- **Bi-directional Identifiers**: Query venues by either canonical code (e.g. `NYMEX`, `CME`, `IFAD`) or ISO 10383 Market Identifier Code (MIC) (e.g. `XNYM`, `XCME`).
- **Rich Market State Diagnostics**: The trading calendar API evaluates trading status, settlement availability, trade date rolls, and product-specific closures in a single query.
- **Pagination & Filtering**: Built-in query parameters for tier, country, currency, year, and commodity groups.

---

## Base URL & Conventions

```http
http://127.0.0.1:8000/api/
```

### Standard HTTP Status Codes

| Status Code | Meaning | When Returned |
| :--- | :--- | :--- |
| `200 OK` | Success | Request succeeded and data returned in response body. |
| `400 Bad Request` | Validation Error | Malformed parameters (e.g., invalid date format `YYYY-MM-DD`). |
| `404 Not Found` | Entity Missing | Exchange symbol, MIC, or entity identifier does not exist. |
| `503 Unavailable` | Service Degraded | Database or cache connectivity probe failed. |

---

## Quick Start Example

=== "Python (httpx / requests)"

    ```python
    import httpx

    client = httpx.Client(base_url="http://127.0.0.1:8000/api/")

    # 1. Check system status
    health = client.get("health/").json()
    print(f"System status: {health['status']}")

    # 2. Query whether Memorial Day 2026 is a trading day on NYMEX
    calendar = client.get("exchanges/NYMEX/is-trading-day/", params={"date": "2026-05-25"}).json()
    print(f"NYMEX Trading Open: {calendar['is_trading_day']}")
    print(f"NYMEX Settlement Produced: {calendar['is_settlement_day']}")
    print(f"Market Status: {calendar['market_status']}")
    ```

=== "cURL"

    ```bash
    # Query exchange profile by ISO MIC
    curl -X GET "http://127.0.0.1:8000/api/exchanges/XNYM/" -H "Accept: application/json"

    # Query exchange trading & settlement status for a specific date
    curl -X GET "http://127.0.0.1:8000/api/exchanges/NYMEX/is-trading-day/?date=2026-05-25"
    ```

---

## API Endpoints Directory

| Resource Area | Path | Method | Description |
| :--- | :--- | :---: | :--- |
| **System Diagnostics** | [`/api/health/`](#) | `GET` | Database connectivity, version, and architecture readiness probe. |
| **Metadata Taxonomy** | [`/api/metadata/domains/`](metadata.md) | `GET` | 34 Canonical commodity data domains with parent-child hierarchy. |
| **Units of Measure** | [`/api/metadata/units/`](metadata.md) | `GET` | 45 Physical and financial measurement units with base unit conversion factors. |
| **Observation Frequencies** | [`/api/metadata/frequencies/`](metadata.md) | `GET` | 15 Canonical trading frequencies with exact intervals in seconds. |
| **Metadata Summary** | [`/api/metadata/summary/`](metadata.md) | `GET` | Aggregate counts of active domains, base units, and intervals. |
| **Exchange Venues** | [`/api/exchanges/`](exchanges.md) | `GET` | Paginated registry of 15 global commodity exchanges with filters. |
| **Exchange Detail** | [`/api/exchanges/{code_or_mic}/`](exchanges.md) | `GET` | Venue profile, timezones, operating sessions, and upcoming closures. |
| **Trading & Settlement Calendar** | [`/api/exchanges/{code_or_mic}/is-trading-day/`](exchanges.md) | `GET` | Real-time diagnostic evaluation of trading vs settlement status. |
| **Exchange Holidays** | [`/api/exchanges/{code_or_mic}/holidays/`](exchanges.md) | `GET` | Full calendar closure and early-close records for a venue. |
| **Exchange Summary** | [`/api/exchanges/summary/`](exchanges.md) | `GET` | Aggregate overview of venues, operating sessions, and tracked holidays. |

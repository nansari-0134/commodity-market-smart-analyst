# REST API: Market Data & Observation Endpoints

The Market Data REST API provides programmatic access to historical and intraday exchange price bars, prompt settlement series, government inventory/balance metrics, and CFTC Commitment of Traders (COT) institutional positioning.

---

## 1. List Market Prices

Retrieve historical and prompt exchange price bars with date range and contract filters.

* **Endpoint**: `GET /api/market-data/prices/`
* **Query Parameters**:
  - `commodity`: Filter by canonical commodity code (e.g. `CL`, `BRENT`, `NG`) or UUID.
  - `is_prompt`: `true` for benchmark prompt front-month contracts only.
  - `delivery_month`: Specific contract delivery code (e.g. `2026-11`, `2026-12`).
  - `start_date`: Earliest trade date (`YYYY-MM-DD`).
  - `end_date`: Latest trade date (`YYYY-MM-DD`).
  - `is_preliminary`: `true` or `false`.

=== "cURL"
    ```bash
    # Query front-month WTI Crude prices for September 2026
    curl -X GET "http://127.0.0.1:8000/api/market-data/prices/?commodity=CL&is_prompt=true&start_date=2026-09-01&end_date=2026-09-24" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/market-data/prices/",
        params={
            "commodity": "CL",
            "is_prompt": "true",
            "start_date": "2026-09-01",
            "end_date": "2026-09-24",
        }
    )
    prices = response.json()
    for bar in prices[:5]:
        print(f"{bar['observation_date']} | Settlement: ${bar['settlement_price']} | Vol: {bar['volume']}")
    ```

=== "JSON Response (200 OK)"
    ```json
    [
      {
        "id": "e3b0c442-98fc-1c14-9afb-4c7c88b2a1a2",
        "commodity_code": "CL",
        "commodity_name": "Light Sweet Crude Oil (WTI)",
        "contract_symbol": "CL",
        "delivery_month": "2026-11",
        "is_prompt": true,
        "observation_date": "2026-09-23",
        "open_price": "75.500000",
        "high_price": "76.700000",
        "low_price": "74.900000",
        "close_price": "75.950000",
        "settlement_price": "75.850000",
        "price": "75.850000",
        "display_settlement": "75.850000",
        "volume": 342000,
        "open_interest": 1820000,
        "quality_status": "VALID",
        "endpoint_code": "CME_SETTLE_FEED",
        "publication_time": "2026-09-23T20:30:00Z",
        "availability_time": "2026-09-23T20:30:00Z",
        "is_preliminary": false,
        "revision_number": 0,
        "created_at": "2026-09-24T06:00:00Z"
      }
    ]
    ```

---

## 2. List Fundamental Observations

Retrieve official government storage, balance, and inventory time series.

* **Endpoint**: `GET /api/market-data/fundamentals/`
* **Query Parameters**:
  - `variable`: Variable code (e.g. `CRUDE_CUSHING_STOCKS`, `CRUDE_US_TOTAL_COMMERCIAL_STOCKS`) or UUID.
  - `start_date`: Earliest survey cutoff date (`YYYY-MM-DD`).
  - `end_date`: Latest survey cutoff date (`YYYY-MM-DD`).
  - `is_preliminary`: `true` or `false`.

=== "cURL"
    ```bash
    # Query Cushing crude inventories
    curl -X GET "http://127.0.0.1:8000/api/market-data/fundamentals/?variable=CRUDE_CUSHING_STOCKS" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/market-data/fundamentals/",
        params={"variable": "CRUDE_CUSHING_STOCKS"}
    )
    records = response.json()
    for row in records[:5]:
        print(f"Date: {row['observation_date']} | Level: {row['display_value']}")
    ```

=== "JSON Response (200 OK)"
    ```json
    [
      {
        "id": "c1f7b764-4bf8-466d-9654-e0b82f05634b",
        "variable_code": "CRUDE_CUSHING_STOCKS",
        "variable_name": "Cushing, OK Ending Stocks of Crude Oil",
        "observation_date": "2026-09-18",
        "value": "24500.500000",
        "display_value": "24500.5 MBBL",
        "unit_code": "MBBL",
        "period_start": "2026-09-12",
        "period_end": "2026-09-18",
        "quality_status": "VALID",
        "endpoint_code": "EIA_V2_PETROLEUM",
        "publication_time": "2026-09-23T14:30:00Z",
        "availability_time": "2026-09-23T14:30:00Z",
        "is_preliminary": false,
        "revision_number": 0,
        "created_at": "2026-09-24T06:00:00Z"
      }
    ]
    ```

---

## 3. List Commitment of Traders (COT) Positioning

Retrieve CFTC institutional positioning reports with computed speculative and commercial net metrics.

* **Endpoint**: `GET /api/market-data/cot/`
* **Query Parameters**:
  - `commodity`: Canonical commodity code (e.g. `CL`, `BRENT`, `GOLD`, `CORN`).
  - `report_type`: `DISAGGREGATED` (default), `LEGACY`, or `FINANCIAL`.
  - `start_date`: Earliest survey Tuesday cutoff date.
  - `end_date`: Latest survey Tuesday cutoff date.

=== "cURL"
    ```bash
    # Query WTI COT disaggregated positioning
    curl -X GET "http://127.0.0.1:8000/api/market-data/cot/?commodity=CL" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/market-data/cot/",
        params={"commodity": "CL"}
    )
    cot_data = response.json()
    for row in cot_data[:3]:
        print(
            f"COT {row['observation_date']} | "
            f"Managed Money Net: {row['money_manager_net']:+d} ({row['money_manager_net_pct_oi']}%) | "
            f"Commercial Net: {row['commercial_net']:+d}"
        )
    ```

=== "JSON Response (200 OK)"
    ```json
    [
      {
        "id": "fa48c3b1-a67b-4177-bc60-d667c29be026",
        "commodity_code": "CL",
        "commodity_name": "Light Sweet Crude Oil (WTI)",
        "observation_date": "2026-09-22",
        "report_type": "DISAGGREGATED",
        "open_interest": 1850000,
        "prod_merc_long": 380000,
        "prod_merc_short": 540000,
        "swap_long": 180000,
        "swap_short": 220000,
        "swap_spread": 42000,
        "money_manager_long": 240000,
        "money_manager_short": 85000,
        "money_manager_spread": 48000,
        "other_rept_long": 88000,
        "other_rept_short": 52000,
        "non_rept_long": 68000,
        "non_rept_short": 44000,
        "money_manager_net": 155000,
        "commercial_net": -200000,
        "money_manager_net_pct_oi": 8.38,
        "commercial_net_pct_oi": -10.81,
        "quality_status": "VALID",
        "endpoint_code": "CFTC_SODA_FEED",
        "publication_time": "2026-09-25T20:30:00Z",
        "availability_time": "2026-09-25T20:30:00Z",
        "created_at": "2026-09-24T06:00:00Z"
      }
    ]
    ```

---

## 4. Market Data Summary & Telemetry

Get a high-level statistical overview of the observation store coverage and freshness.

* **Endpoint**: `GET /api/market-data/summary/`

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/market-data/summary/" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get("http://127.0.0.1:8000/api/market-data/summary/")
    print(response.json())
    ```

=== "JSON Response (200 OK)"
    ```json
    {
      "total_price_observations": 455,
      "total_prompt_observations": 325,
      "total_fundamental_observations": 52,
      "total_cot_observations": 65,
      "covered_commodities_count": 5,
      "covered_variables_count": 4,
      "latest_price_date": "2026-09-24",
      "latest_fundamental_date": "2026-09-18",
      "latest_cot_date": "2026-09-22"
    }
    ```

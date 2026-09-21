# Dataset Master Catalog API Reference

The Dataset Master API provides programmatic access to the canonical dataset registry, multi-asset commodity linkages, release schedules, update cadences, and pipeline service level agreements (SLAs).

---

## 1. List Dataset Catalog

`GET /api/datasets/`

Retrieves registered dataset catalog entries with multi-dimensional filtering across categories, cadences, linked commodities, and domains.

### Query Parameters

| Parameter | Type | Required | Description |
| :--- | :---: | :---: | :--- |
| `category` | `string` | No | Filter by data category (e.g. `MARKET_PRICES`, `INVENTORIES_STOCKS`, `SUPPLY_DEMAND`, `POSITIONING`, `WEATHER_CLIMATE`). |
| `cadence` | `string` | No | Filter by update cadence (e.g. `DAILY_EOD`, `WEEKLY_FIXED_DAY`, `MONTHLY_CALENDAR_DAY`, `SEASONAL_CROP_CYCLE`). |
| `commodity` | `string` | No | Filter by commodity code (e.g. `CL`, `CORN`, `BRENT`, `COPPER`). Evaluates both primary and multi-asset relationships. |
| `domain` | `string` | No | Filter by data domain code (e.g. `ENERGY`, `AGRICULTURE`, `METALS`). |
| `exchange` | `string` | No | Filter by exchange code or MIC (e.g. `CME`, `NYMEX`, `XCBT`). |
| `is_point_in_time` | `boolean` | No | Filter by point-in-time enforcement (`true` or `false`). |
| `search` | `string` | No | Text search across code, title, description, or source authority. |

=== "cURL"
    ```bash
    # Filter datasets relevant to Corn fundamentals
    curl -X GET "http://127.0.0.1:8000/api/datasets/?commodity=CORN" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/datasets/",
        params={"category": "SUPPLY_DEMAND"},
    )
    datasets = response.json()
    for ds in datasets:
        print(f"{ds['code']} - {ds['name']} (Authority: {ds['source_authority']}, Cadence: {ds['update_cadence']})")
    ```

### Response Payload (`200 OK`)

```json
[
  {
    "id": "7b8c9d01-e234-5f67-8901-abcdef123456",
    "code": "USDA_WASDE",
    "name": "World Agricultural Supply and Demand Estimates (WASDE)",
    "description": "Monthly comprehensive global and US supply, consumption, exports, and ending stocks projections for major agricultural crops.",
    "domain_code": "AGRICULTURE",
    "domain_name": "Agricultural Fundamentals",
    "primary_commodity_code": null,
    "primary_commodity_name": null,
    "commodities": ["CORN", "SOYBEANS", "WHEAT"],
    "exchange_code": null,
    "frequency_code": "MONTHLY",
    "data_category": "SUPPLY_DEMAND",
    "update_cadence": "MONTHLY_CALENDAR_DAY",
    "ingestion_mode": "PULL_SCHEDULED_BATCH",
    "release_schedule": {
      "day_range": "9-12",
      "release_time": "12:00",
      "timezone": "America/New_York"
    },
    "retention_policy": "INDEFINITE_POINT_IN_TIME",
    "license_type": "PUBLIC_DOMAIN",
    "point_in_time_enabled": true,
    "supports_revisions": true,
    "sla_max_delay_minutes": 30,
    "source_authority": "USDA World Agricultural Outlook Board",
    "documentation_url": "https://www.usda.gov/oce/commodity/wasde",
    "is_active": true,
    "display_order": 10
  }
]
```

---

## 2. Retrieve Dataset by Code or ID

`GET /api/datasets/{code_or_uuid}/`

Retrieves comprehensive catalog metadata for a single dataset identified by its canonical code (e.g. `EIA_WPSR_PETROLEUM`) or its UUID.

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/datasets/EIA_WPSR_PETROLEUM/" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get("http://127.0.0.1:8000/api/datasets/EIA_WPSR_PETROLEUM/")
    dataset = response.json()
    print(f"Dataset: {dataset['name']}")
    print(f"SLA Delay Max: {dataset['sla_max_delay_minutes']} minutes")
    print(f"Cadence: {dataset['update_cadence']}")
    ```

### Response Payload (`200 OK`)

```json
{
  "id": "8c9d0e12-f345-6a78-9012-bcdef1234567",
  "code": "EIA_WPSR_PETROLEUM",
  "name": "EIA Weekly Petroleum Status Report (WPSR)",
  "description": "Weekly US crude oil, gasoline, and distillate inventory estimates, refinery runs, and production metrics.",
  "domain_code": "ENERGY",
  "domain_name": "Energy Fundamentals",
  "primary_commodity_code": "CL",
  "primary_commodity_name": "Light Sweet Crude Oil (WTI)",
  "commodities": ["CL", "BRENT"],
  "exchange_code": null,
  "frequency_code": "WEEKLY",
  "data_category": "INVENTORIES_STOCKS",
  "update_cadence": "WEEKLY_FIXED_DAY",
  "ingestion_mode": "PULL_SCHEDULED_BATCH",
  "release_schedule": {
    "day_of_week": "Wednesday",
    "release_time": "10:30",
    "timezone": "America/New_York"
  },
  "retention_policy": "INDEFINITE_POINT_IN_TIME",
  "license_type": "PUBLIC_DOMAIN",
  "point_in_time_enabled": true,
  "supports_revisions": true,
  "sla_max_delay_minutes": 15,
  "source_authority": "US Energy Information Administration (EIA)",
  "documentation_url": "https://www.eia.gov/petroleum/supply/weekly/",
  "is_active": true,
  "display_order": 20
}
```

---

## 3. Dataset Summary Metrics

`GET /api/datasets/summary/`

Returns high-level platform telemetry regarding catalog distribution, cadence breakdown, and acquisition modes.

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/datasets/summary/" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get("http://127.0.0.1:8000/api/datasets/summary/")
    summary = response.json()
    print(f"Total Datasets: {summary['total_datasets']}")
    print(f"Breakdown by Cadence: {summary['by_cadence']}")
    ```

### Response Payload (`200 OK`)

```json
{
  "total_datasets": 23,
  "active_datasets": 23,
  "point_in_time_datasets": 23,
  "by_category": {
    "MARKET_PRICES": 4,
    "INVENTORIES_STOCKS": 4,
    "SUPPLY_DEMAND": 5,
    "TRADE_FLOWS": 2,
    "POSITIONING": 2,
    "WEATHER_CLIMATE": 2,
    "MACROECONOMIC": 2,
    "PRODUCTION_CAPACITY": 2
  },
  "by_cadence": {
    "DAILY_EOD": 6,
    "WEEKLY_FIXED_DAY": 9,
    "MONTHLY_CALENDAR_DAY": 6,
    "SEASONAL_CROP_CYCLE": 2
  },
  "by_ingestion_mode": {
    "PULL_SCHEDULED_BATCH": 23
  },
  "by_license": {
    "PUBLIC_DOMAIN": 19,
    "EXCHANGE_LICENSED": 4
  }
}
```

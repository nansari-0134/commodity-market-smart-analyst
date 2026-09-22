# Variable Master Catalog API Reference

The Variable Master API provides programmatic access to the canonical dictionary of standardized commodity market variables, dimensional units, stock vs. flow aggregation behaviors, and analytical transformation hints.

---

## 1. List Variable Catalog

`GET /api/variables/`

Retrieves registered metrics and variables with multi-dimensional filtering across datasets, physical commodities, taxonomy domains, units, and aggregation methods.

### Query Parameters

| Parameter | Type | Required | Description |
| :--- | :---: | :---: | :--- |
| `commodity` | `string` | No | Filter by physical commodity code (e.g. `CL`, `CORN`, `SOYBEANS`, `GOLD`, `COPPER`). |
| `dataset` | `string` | No | Filter by parent dataset code (e.g. `EIA_WPSR_PETROLEUM_STOCKS`, `USDA_WASDE_WORLD_GRAINS`). |
| `domain` | `string` | No | Filter by data domain code (e.g. `INVENTORIES`, `SUPPLY_DEMAND_BALANCES`, `CFTC_COT`). |
| `unit` | `string` | No | Filter by unit of measure (e.g. `MBBL`, `BU`, `MT`, `PERCENT`, `COUNT`). |
| `data_type` | `string` | No | Filter by data type (`DECIMAL`, `INTEGER`, `PERCENTAGE_RATIO`). |
| `aggregation_method` | `string` | No | Filter by temporal aggregation method (`LAST` for stocks, `SUM` for flows, `AVG` for rates). |
| `is_benchmark` | `boolean` | No | Filter headline benchmark metrics (`true` or `false`). |
| `search` | `string` | No | Text search across code, title, or methodology description. |

=== "cURL"
    ```bash
    # Filter benchmark inventory variables for Crude Oil
    curl -X GET "http://127.0.0.1:8000/api/variables/?commodity=CL&is_benchmark=true" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/variables/",
        params={"dataset": "USDA_WASDE_WORLD_GRAINS"},
    )
    variables = response.json()
    for v in variables:
        print(f"{v['code']} - {v['name']} ({v['unit_code']}, Agg: {v['aggregation_method']})")
    ```

### Response Payload (`200 OK`)

```json
[
  {
    "id": "2e3f4a56-b789-0123-4567-890123abcdef",
    "code": "CRUDE_CUSHING_STOCKS",
    "name": "Cushing Oklahoma Ending Crude Oil Stocks",
    "dataset_code": "EIA_WPSR_PETROLEUM_STOCKS",
    "dataset_name": "EIA Weekly Petroleum Status Report (WPSR)",
    "domain_code": "INVENTORIES",
    "domain_name": "Inventories & Stocks",
    "commodity_code": "CL",
    "commodity_name": "Light Sweet Crude Oil (WTI)",
    "unit_code": "MBBL",
    "unit_name": "Thousand Barrels",
    "data_type": "DECIMAL",
    "aggregation_method": "LAST",
    "seasonal_adjustment": "UNADJUSTED",
    "default_transformation": "DIFF_1W",
    "is_benchmark": true,
    "is_active": true,
    "display_order": 10
  }
]
```

---

## 2. Retrieve Variable by Code or ID

`GET /api/variables/{code_or_uuid}/`

Retrieves comprehensive specification details for a single variable identified by its canonical code (e.g. `CRUDE_CUSHING_STOCKS`) or UUID.

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/variables/WASDE_CORN_US_ENDING_STOCKS/" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get("http://127.0.0.1:8000/api/variables/WASDE_CORN_US_ENDING_STOCKS/")
    var = response.json()
    print(f"Metric: {var['name']}")
    print(f"Unit: {var['unit_code']} ({var['unit_name']})")
    print(f"Aggregation: {var['aggregation_method']} (Stock Snapshot)")
    ```

### Response Payload (`200 OK`)

```json
{
  "id": "3f4a5b67-c890-1234-5678-901234bcdef1",
  "code": "WASDE_CORN_US_ENDING_STOCKS",
  "name": "US Corn Projected Marketing Year Ending Stocks",
  "description": "USDA World Agricultural Outlook Board projected carryover stocks of Corn at the end of the marketing year (August 31).",
  "dataset_code": "USDA_WASDE_WORLD_GRAINS",
  "dataset_name": "World Agricultural Supply and Demand Estimates (WASDE)",
  "domain_code": "SUPPLY_DEMAND_BALANCES",
  "domain_name": "Supply & Demand Balances",
  "commodity_code": "CORN",
  "commodity_name": "Corn No. 2 Yellow",
  "unit_code": "BU",
  "unit_name": "Bushels",
  "data_type": "DECIMAL",
  "aggregation_method": "LAST",
  "seasonal_adjustment": "UNADJUSTED",
  "default_transformation": "DIFF_1M",
  "is_benchmark": true,
  "is_active": true,
  "display_order": 100,
  "created_at": "2026-09-22T12:00:00Z",
  "updated_at": "2026-09-22T12:00:00Z"
}
```

---

## 3. Variable Summary Metrics

`GET /api/variables/summary/`

Returns high-level catalog distribution metrics across data types, aggregation methods, and parent datasets.

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/variables/summary/" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get("http://127.0.0.1:8000/api/variables/summary/")
    summary = response.json()
    print(f"Total Variables: {summary['total_variables']}")
    print(f"Benchmark Metrics: {summary['benchmark_variables']}")
    print(f"Stock vs Flow Breakdown: {summary['by_aggregation_method']}")
    ```

### Response Payload (`200 OK`)

```json
{
  "total_variables": 40,
  "active_variables": 40,
  "benchmark_variables": 26,
  "by_data_type": {
    "DECIMAL": 33,
    "INTEGER": 7
  },
  "by_aggregation_method": {
    "LAST": 26,
    "SUM": 9,
    "AVG": 5
  },
  "by_domain": {
    "INVENTORIES": 10,
    "SUPPLY_DEMAND_BALANCES": 12,
    "TRADE_FLOWS": 3,
    "CFTC_COT": 5,
    "EXCHANGE_MARKET_DATA": 5,
    "WEATHER": 1,
    "FX": 2,
    "PHYSICAL_MARKET": 2
  },
  "by_dataset": {
    "EIA_WPSR_PETROLEUM_STOCKS": 5,
    "EIA_WPSR_REFINERY_UTILIZATION": 2,
    "EIA_WEEKLY_NATURAL_GAS_STORAGE": 2,
    "USDA_WASDE_WORLD_GRAINS": 8,
    "USDA_EXPORT_SALES_WEEKLY": 2,
    "USDA_CROP_PROGRESS_WEEKLY": 3,
    "CFTC_COT_DISAGGREGATED_FUT_OPT": 5,
    "LME_DAILY_WAREHOUSE_STOCKS": 3,
    "BAKER_HUGHES_ROTARY_RIG_COUNT": 2,
    "NOAA_CPC_ENSO_OUTLOOK": 1,
    "FEDERAL_RESERVE_H10_FX_RATES": 2,
    "CONAB_BRAZIL_GRAIN_HARVEST_SURVEY": 1,
    "MPOB_PALM_OIL_MONTHLY_BALANCE": 1,
    "EEX_EUA_CARBON_AUCTION_RESULTS": 1,
    "ARGUS_US_GULF_CRUDE_ASSESSMENTS": 1,
    "PLATTS_NORTH_SEA_BRENT_ASSESSMENTS": 1
  }
}
```

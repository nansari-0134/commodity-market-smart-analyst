# Commodity Master & Listings API Reference

The Commodities API provides programmatic access to canonical physical commodity specifications, deliverable grade chemistry parameters, delivery hubs, crop year seasonality profiles, and multi-venue exchange listings.

---

## 1. List Commodities

`GET /api/commodities/`

Retrieves a paginated or full list of canonical commodities with multi-dimensional filtering.

### Query Parameters

| Parameter | Type | Required | Description |
| :--- | :---: | :---: | :--- |
| `sector` | `string` | No | Filter by sector: `ENERGY`, `AGRICULTURE`, `METALS_BASE`, `METALS_PRECIOUS`, `LIVESTOCK`, `FREIGHT_BULK`, `ENVIRONMENTAL`. |
| `group` | `string` | No | Filter by industry group: `CRUDE_OIL`, `GRAINS`, `OILSEEDS`, `SOFTS`, `PRECIOUS_METALS`, `BASE_METALS`, `LIVESTOCK`. |
| `exchange` | `string` | No | Filter commodities trading on a specific venue (e.g. `MCX`, `NYMEX`, `COMEX`, `LME`, `CBOT`). Matches primary or secondary listings. |
| `settlement` | `string` | No | Filter by settlement mechanism: `PHYSICAL` or `CASH`. |
| `search` | `string` | No | Case-insensitive text search across code, name, deliverable grade standard, and delivery hub. |

=== "cURL"
    ```bash
    # Filter commodities trading on MCX India
    curl -X GET "http://127.0.0.1:8000/api/commodities/?exchange=MCX" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/commodities/",
        params={"sector": "ENERGY", "settlement": "PHYSICAL"},
    )
    commodities = response.json()
    for c in commodities:
        print(f"{c['code']}: {c['name']} ({c['primary_exchange_code']}) — {c['exchange_count']} venues")
    ```

### Response Payload (`200 OK`)
```json
[
  {
    "id": "8f3b23c1-7a6b-4e12-8e3d-091a2b3c4d5e",
    "code": "CL",
    "name": "Light Sweet Crude Oil (WTI)",
    "sector": "ENERGY",
    "group": "CRUDE_OIL",
    "primary_exchange_code": "NYMEX",
    "primary_exchange_name": "New York Mercantile Exchange",
    "base_unit_code": "BBL",
    "base_unit_symbol": "bbl",
    "pricing_unit_code": "USD_BBL",
    "pricing_unit_symbol": "$/bbl",
    "standard_lot_size": "1000.0000",
    "minimum_tick_size": "0.010000",
    "tick_value": "10.0000",
    "tick_currency": "USD",
    "settlement_method": "PHYSICAL",
    "deliverable_grade_standard": "Light Sweet Crude (API Gravity: 37° - 42°, Sulfur <= 0.42%)",
    "primary_delivery_hub": "Cushing, Oklahoma",
    "crop_year_start_month": null,
    "exchange_count": 2,
    "is_active": true,
    "display_order": 10
  }
]
```

---

## 2. Retrieve Commodity Profile

`GET /api/commodities/{identifier}/`

Retrieves the complete profile for a single commodity by canonical code (e.g. `CL`, `BRENT`, `GOLD`) or UUID. Inlines chemistry parameters, delivery hub details, crop cycle months, and all active exchange listings.

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/commodities/CL/" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get("http://127.0.0.1:8000/api/commodities/GOLD/")
    gold = response.json()
    print(f"Standard: {gold['deliverable_grade_standard']}")
    print(f"Listings:")
    for listing in gold["exchange_listings"]:
        print(f"  - {listing['exchange_code']} ({listing['ticker_symbol']}): {listing['contract_size']} {listing['contract_unit_code']} [{listing['trading_currency']}]")
    ```

### Response Payload (`200 OK`)
```json
{
  "id": "8f3b23c1-7a6b-4e12-8e3d-091a2b3c4d5e",
  "code": "CL",
  "name": "Light Sweet Crude Oil (WTI)",
  "sector": "ENERGY",
  "group": "CRUDE_OIL",
  "primary_exchange_code": "NYMEX",
  "primary_exchange_name": "New York Mercantile Exchange",
  "primary_exchange_mic": "XNYM",
  "primary_exchange_timezone": "America/New_York",
  "base_unit_code": "BBL",
  "base_unit_symbol": "bbl",
  "pricing_unit_code": "USD_BBL",
  "pricing_unit_symbol": "$/bbl",
  "standard_lot_size": "1000.0000",
  "standard_lot_unit_code": "BBL",
  "minimum_tick_size": "0.010000",
  "tick_value": "10.0000",
  "tick_currency": "USD",
  "settlement_method": "PHYSICAL",
  "hs_code": "2709.00",
  "deliverable_grade_standard": "Light Sweet Crude (API Gravity: 37° - 42°, Sulfur <= 0.42%)",
  "quality_specifications": {
    "api_gravity_min": 37.0,
    "api_gravity_max": 42.0,
    "sulfur_pct_max": 0.42,
    "bs_w_pct_max": 1.0,
    "pour_point_max_c": -1.0,
    "viscosity_max_cst": 3.0
  },
  "primary_delivery_hub": "Cushing, Oklahoma",
  "delivery_hub_details": {
    "hub_name": "Cushing Pipeline & Storage Hub",
    "state": "OK",
    "country": "US",
    "interconnects": ["Enterprise", "Enbridge", "Plains All American", "Magellan"],
    "delivery_mechanism": "F.O.B. pipeline or storage terminal"
  },
  "crop_year_start_month": null,
  "peak_production_months": [5, 6, 7, 8, 9, 10],
  "peak_demand_months": [6, 7, 8],
  "seasonality_notes": "Summer US driving season increases refinery runs and crude drawdowns June through August.",
  "description": "Global benchmark for light sweet crude oil. Physical delivery at Cushing, Oklahoma.",
  "is_active": true,
  "display_order": 10,
  "metadata": {},
  "exchange_listings": [
    {
      "id": "e5c4a102-1234-4567-89ab-cdef01234567",
      "exchange_code": "NYMEX",
      "exchange_name": "New York Mercantile Exchange",
      "exchange_mic": "XNYM",
      "exchange_country": "US",
      "ticker_symbol": "CL",
      "contract_size": "1000.0000",
      "contract_unit_code": "BBL",
      "contract_unit_symbol": "bbl",
      "settlement_method": "PHYSICAL",
      "is_primary_benchmark": true,
      "liquidity_tier": "BENCHMARK",
      "typical_daily_volume": 950000,
      "typical_open_interest": 1850000,
      "trading_currency": "USD",
      "is_active": true
    },
    {
      "id": "f6d5b213-2345-5678-90bc-def012345678",
      "exchange_code": "MCX",
      "exchange_name": "Multi Commodity Exchange of India",
      "exchange_mic": "XMCX",
      "exchange_country": "IN",
      "ticker_symbol": "CRUDEOIL",
      "contract_size": "100.0000",
      "contract_unit_code": "BBL",
      "contract_unit_symbol": "bbl",
      "settlement_method": "CASH",
      "is_primary_benchmark": false,
      "liquidity_tier": "HIGH",
      "typical_daily_volume": 85000,
      "typical_open_interest": 16000,
      "trading_currency": "INR",
      "is_active": true
    }
  ]
}
```

---

## 3. Retrieve Commodity Exchange Listings

`GET /api/commodities/{identifier}/listings/`

Returns only the multi-venue exchange listings for the given commodity.

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/commodities/COPPER/listings/" \
         -H "Accept: application/json"
    ```

### Response Payload (`200 OK`)
```json
{
  "commodity_code": "COPPER",
  "commodity_name": "High Grade Copper Cathode",
  "listing_count": 4,
  "listings": [
    {
      "exchange_code": "LME",
      "ticker_symbol": "CA",
      "contract_size": "25.0000",
      "contract_unit_code": "MT",
      "settlement_method": "PHYSICAL",
      "is_primary_benchmark": true,
      "liquidity_tier": "BENCHMARK",
      "typical_daily_volume": 145000,
      "typical_open_interest": 330000,
      "trading_currency": "USD"
    },
    {
      "exchange_code": "COMEX",
      "ticker_symbol": "HG",
      "contract_size": "11.3398",
      "contract_unit_code": "MT",
      "settlement_method": "PHYSICAL",
      "is_primary_benchmark": false,
      "liquidity_tier": "BENCHMARK",
      "typical_daily_volume": 115000,
      "typical_open_interest": 270000,
      "trading_currency": "USD"
    },
    {
      "exchange_code": "SHFE",
      "ticker_symbol": "CU",
      "contract_size": "5.0000",
      "contract_unit_code": "MT",
      "settlement_method": "PHYSICAL",
      "is_primary_benchmark": false,
      "liquidity_tier": "HIGH",
      "typical_daily_volume": 230000,
      "typical_open_interest": 390000,
      "trading_currency": "CNY"
    },
    {
      "exchange_code": "MCX",
      "ticker_symbol": "COPPER",
      "contract_size": "2.5000",
      "contract_unit_code": "MT",
      "settlement_method": "PHYSICAL",
      "is_primary_benchmark": false,
      "liquidity_tier": "ACTIVE",
      "typical_daily_volume": 15000,
      "typical_open_interest": 8200,
      "trading_currency": "INR"
    }
  ]
}
```

---

## 4. Commodity Summary & Health Metrics

`GET /api/commodities/summary/`

Returns platform-wide commodity metrics, sector breakdown, physical vs. cash split, and active exchange venue rankings.

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/commodities/summary/" \
         -H "Accept: application/json"
    ```

### Response Payload (`200 OK`)
```json
{
  "total_commodities": 23,
  "total_exchange_listings": 44,
  "sectors": {
    "ENERGY": {"label": "Energy (Crude, Gas, Power, Refined)", "count": 6},
    "AGRICULTURE": {"label": "Agriculture (Grains, Oilseeds, Softs)", "count": 9},
    "METALS_PRECIOUS": {"label": "Precious Metals", "count": 2},
    "METALS_BASE": {"label": "Industrial / Base Metals", "count": 2},
    "LIVESTOCK": {"label": "Livestock & Dairy", "count": 2},
    "FREIGHT_BULK": {"label": "Bulk Freight & Shipping", "count": 1},
    "ENVIRONMENTAL": {"label": "Environmental & Carbon Allowances", "count": 1}
  },
  "settlement_methods": {
    "PHYSICAL": 18,
    "CASH": 5
  },
  "venues": [
    {"exchange__code": "NYMEX", "exchange__name": "New York Mercantile Exchange", "exchange__country": "US", "contract_count": 6},
    {"exchange__code": "MCX", "exchange__name": "Multi Commodity Exchange of India", "exchange__country": "IN", "contract_count": 6},
    {"exchange__code": "CBOT", "exchange__name": "Chicago Board of Trade", "exchange__country": "US", "contract_count": 5},
    {"exchange__code": "ICE_EU", "exchange__name": "ICE Futures Europe", "exchange__country": "GB", "contract_count": 5},
    {"exchange__code": "SHFE", "exchange__name": "Shanghai Futures Exchange", "exchange__country": "CN", "contract_count": 4}
  ]
}
```

---

## 5. Sectors & Groups Directory

`GET /api/commodities/sectors/`

Lists all 7 supported sectors with their canonical industry groups and active commodity counts.

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/commodities/sectors/" \
         -H "Accept: application/json"
    ```

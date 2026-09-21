# Contracts & Derivatives API Reference

The Contracts API provides programmatic access to institutional derivative contract specifications, standard month codes (F–Z), prompt delivery contract expiries, and terminal maturity diagnostics.

---

## 1. List Contract Specifications

`GET /api/contracts/specifications/`

Retrieves contract specifications with multi-dimensional filtering across commodities, exchange venues, instruments, and settlement methods.

### Query Parameters

| Parameter | Type | Required | Description |
| :--- | :---: | :---: | :--- |
| `commodity` | `string` | No | Filter by commodity code (e.g. `CL`, `BRENT`, `CORN`, `GOLD`). |
| `exchange` | `string` | No | Filter by venue code or MIC (e.g. `NYMEX`, `IFEU`, `XCBT`, `XLME`, `XMCX`). |
| `instrument_type` | `string` | No | Filter by instrument: `FUTURES`, `OPTIONS_AMERICAN`, etc. |
| `settlement_method` | `string` | No | Filter by settlement: `PHYSICAL` or `CASH`. |
| `search` | `string` | No | Text search across ticker root, contract name, or commodity name. |

=== "cURL"
    ```bash
    # Filter physical futures specifications on NYMEX
    curl -X GET "http://127.0.0.1:8000/api/contracts/specifications/?exchange=NYMEX&settlement_method=PHYSICAL" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/contracts/specifications/",
        params={"commodity": "CL"},
    )
    specs = response.json()
    for s in specs:
        print(f"{s['exchange_code']}:{s['symbol_root']} - {s['name']} (Size: {s['contract_size']} {s['contract_unit_code']})")
    ```

### Response Payload (`200 OK`)

```json
[
  {
    "id": "e4a71b28-5c12-4d89-9e12-345678abcdef",
    "symbol_root": "CL",
    "name": "Light Sweet Crude Oil (WTI) Futures",
    "commodity_code": "CL",
    "commodity_name": "Light Sweet Crude Oil (WTI)",
    "exchange_code": "NYMEX",
    "exchange_mic": "XNYM",
    "instrument_type": "FUTURES",
    "contract_size": "1000.0000",
    "contract_unit_code": "BBL",
    "price_quote_unit_code": "USD_BBL",
    "minimum_tick_size": "0.010000",
    "tick_value": "10.0000",
    "trading_currency": "USD",
    "settlement_method": "PHYSICAL",
    "trading_months": "ALL_12",
    "expiry_rule": "DAY_OF_PRIOR_MONTH_WITH_BUS_OFFSET",
    "default_roll_rule": "GSCI_5_TO_9_BUS_DAY",
    "active_expiries_count": 12,
    "is_active": true,
    "display_order": 10
  }
]
```

---

## 2. Retrieve Contract Specification Details

`GET /api/contracts/specifications/<lookup>/`

Retrieves a single specification with nested prompt delivery contract expiries. Lookup supports UUID, ticker root (e.g. `CL`, `B`), or MIC-prefixed symbol (e.g. `XNYM:CL`).

=== "cURL"
    ```bash
    # Retrieve NYMEX WTI Crude specification with active prompt expiries
    curl -X GET "http://127.0.0.1:8000/api/contracts/specifications/CL/" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get("http://127.0.0.1:8000/api/contracts/specifications/CL/")
    spec = response.json()
    print(f"Contract: {spec['name']} ({spec['symbol_root']})")
    print(f"Prompt forward months ({len(spec['expiries'])}):")
    for exp in spec["expiries"]:
        print(f"  • {exp['contract_symbol']}: Last Trading Day = {exp['last_trading_day']}")
    ```

### Response Payload (`200 OK`)

```json
{
  "id": "e4a71b28-5c12-4d89-9e12-345678abcdef",
  "symbol_root": "CL",
  "name": "Light Sweet Crude Oil (WTI) Futures",
  "commodity_code": "CL",
  "commodity_name": "Light Sweet Crude Oil (WTI)",
  "exchange_code": "NYMEX",
  "exchange_mic": "XNYM",
  "instrument_type": "FUTURES",
  "contract_size": "1000.0000",
  "contract_unit_code": "BBL",
  "price_quote_unit_code": "USD_BBL",
  "minimum_tick_size": "0.010000",
  "tick_value": "10.0000",
  "trading_currency": "USD",
  "settlement_method": "PHYSICAL",
  "trading_months": "ALL_12",
  "expiry_rule": "DAY_OF_PRIOR_MONTH_WITH_BUS_OFFSET",
  "expiry_rule_parameter": 25,
  "notice_rule": "First notice day is the last business day of the month preceding the delivery month.",
  "default_roll_rule": "GSCI_5_TO_9_BUS_DAY",
  "active_expiries_count": 12,
  "expiries": [
    {
      "id": "9a12c45e-6789-4bc3-9012-def345678901",
      "contract_symbol": "CLZ26",
      "specification_symbol": "CL",
      "exchange_mic": "XNYM",
      "exchange_code": "NYMEX",
      "contract_year": 2026,
      "contract_month": 12,
      "contract_month_code": "Z",
      "last_trading_day": "2026-11-25",
      "first_notice_day": "2026-11-30",
      "last_delivery_day": "2026-12-31",
      "final_settlement_date": "2026-11-27",
      "is_expired": false,
      "is_active": true
    }
  ],
  "is_active": true,
  "display_order": 10
}
```

---

## 3. List Delivery Contract Expiries

`GET /api/contracts/expiries/`

Retrieves tradable forward delivery contracts across specifications, filterable by root symbol, calendar year, month, or expiration status.

### Query Parameters

| Parameter | Type | Required | Description |
| :--- | :---: | :---: | :--- |
| `symbol_root` | `string` | No | Filter by root ticker (e.g. `CL`, `B`, `ZC`). |
| `exchange` | `string` | No | Filter by venue code or MIC (e.g. `NYMEX`, `XCBT`). |
| `year` | `integer` | No | Filter by 4-digit delivery year (e.g. `2026`, `2027`). |
| `month` | `integer` | No | Filter by delivery month number (1–12). |
| `month_code` | `string` | No | Filter by letter code (`F` through `Z`). |
| `is_expired` | `boolean` | No | Filter by settlement status (`true` or `false`). |

=== "cURL"
    ```bash
    # Retrieve all active 2026 delivery contracts for WTI
    curl -X GET "http://127.0.0.1:8000/api/contracts/expiries/?symbol_root=CL&year=2026&is_expired=false" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/contracts/expiries/",
        params={"symbol_root": "ZC", "year": 2027},
    )
    expiries = response.json()
    for exp in expiries:
        print(f"{exp['contract_symbol']} (Exp: {exp['last_trading_day']})")
    ```

---

## 4. Retrieve Single Delivery Expiry

`GET /api/contracts/expiries/<lookup>/`

Retrieves a single delivery contract by its standardized ticker symbol (e.g. `CLZ26`, `ZCH27`, `BF27`) or UUID.

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/contracts/expiries/CLZ26/" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get("http://127.0.0.1:8000/api/contracts/expiries/CLZ26/")
    exp = response.json()
    print(f"Contract: {exp['contract_symbol']}")
    print(f"Last Trading Day: {exp['last_trading_day']}")
    print(f"Final Settlement: {exp['final_settlement_date']}")
    ```

---

## 5. Statistical Diagnostics & Summary

`GET /api/contracts/summary/`

Returns aggregate system telemetry across derivative contracts, forward curve maturities, and venues.

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/contracts/summary/" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get("http://127.0.0.1:8000/api/contracts/summary/")
    summary = response.json()
    print(f"Total Specs: {summary['total_specifications']}")
    print(f"Active Forward Expiries: {summary['active_expiries']}")
    print("Settlement Breakdown:", summary["settlement_method_breakdown"])
    ```

### Response Payload (`200 OK`)

```json
{
  "total_specifications": 25,
  "total_expiries": 212,
  "active_expiries": 209,
  "expired_contracts": 3,
  "settlement_method_breakdown": {
    "PHYSICAL": 22,
    "CASH": 3
  },
  "instrument_type_breakdown": {
    "FUTURES": 25
  },
  "exchange_breakdown": {
    "NYMEX": 4,
    "ICE_US": 4,
    "CBOT": 4,
    "COMEX": 3,
    "ICE_EU": 2,
    "LME": 2,
    "CME": 2,
    "MCX": 2,
    "BMD": 1,
    "EEX": 1
  }
}
```

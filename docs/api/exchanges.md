# Exchanges & Trading Calendars REST API

The Exchanges API provides access to canonical commodity exchange execution venues, trading session operating hours, daily settlement windows, and calendar rules.

---

## 1. List Exchanges

`GET /api/exchanges/`

Returns a list of supported global commodity exchanges.

### Query Parameters
| Parameter | Type | Example | Description |
| :--- | :--- | :--- | :--- |
| `country` | `string` | `?country=US` | Filter by ISO 3166-1 alpha-2 country code (`US`, `GB`, `BR`, `MY`, `AE`, `SG`, `CN`, `DE`, `IN`). |
| `tier` | `string` | `?tier=GLOBAL_BENCHMARK` | Filter by tier: `GLOBAL_BENCHMARK`, `REGIONAL_PRIMARY`, `DOMESTIC`. |
| `currency` | `string` | `?currency=USD` | Filter by quote currency (`USD`, `EUR`, `GBP`, `BRL`, `MYR`, `INR`, `CNY`). |

### Example Request & Response

=== "cURL"

    ```bash
    curl -X GET "http://127.0.0.1:8000/api/exchanges/?tier=GLOBAL_BENCHMARK"
    ```

=== "JSON Response"

    ```json
    [
      {
        "id": "7b3b47f0-a245-42d4-9d10-85f29910d511",
        "code": "CME",
        "name": "Chicago Mercantile Exchange",
        "mic": "XCME",
        "operating_mic": "XCME",
        "country": "US",
        "city": "Chicago",
        "timezone": "America/Chicago",
        "currency": "USD",
        "tier": "GLOBAL_BENCHMARK",
        "website_url": "https://www.cmegroup.com",
        "is_active": true
      },
      {
        "id": "7b3b47f0-a245-42d4-9d10-85f29910d512",
        "code": "NYMEX",
        "name": "New York Mercantile Exchange",
        "mic": "XNYM",
        "operating_mic": "XCME",
        "country": "US",
        "city": "New York",
        "timezone": "America/New_York",
        "currency": "USD",
        "tier": "GLOBAL_BENCHMARK",
        "website_url": "https://www.cmegroup.com/markets/energy.html",
        "is_active": true
      }
    ]
    ```

---

## 2. Get Exchange Profile (By Code or MIC)

`GET /api/exchanges/{identifier}/`

Retrieves a complete venue profile including operating sessions and calendar holidays. The `{identifier}` can be either the canonical exchange symbol (e.g. `NYMEX`, `IFAD`, `BMD`, `B3`) or its official ISO 10383 MIC (e.g. `XNYM`, `IFAD`, `XKLS`, `BVMF`).

### Example Request & Response

=== "cURL (Lookup by MIC)"

    ```bash
    curl -X GET "http://127.0.0.1:8000/api/exchanges/XNYM/"
    ```

=== "JSON Response"

    ```json
    {
      "id": "7b3b47f0-a245-42d4-9d10-85f29910d512",
      "code": "NYMEX",
      "name": "New York Mercantile Exchange",
      "mic": "XNYM",
      "operating_mic": "XCME",
      "country": "US",
      "city": "New York",
      "timezone": "America/New_York",
      "currency": "USD",
      "tier": "GLOBAL_BENCHMARK",
      "website_url": "https://www.cmegroup.com/markets/energy.html",
      "is_active": true,
      "sessions": [
        {
          "id": "993a47f0-a245-42d4-9d10-85f29910d520",
          "session_type": "ELECTRONIC",
          "name": "CME Globex Electronic Continuous Trading",
          "start_time_local": "18:00:00",
          "end_time_local": "17:00:00",
          "days_of_week": "SUN,MON,TUE,WED,THU,FRI",
          "is_active": true
        },
        {
          "id": "993a47f0-a245-42d4-9d10-85f29910d521",
          "session_type": "SETTLEMENT_WINDOW",
          "name": "WTI Crude Oil Daily Settlement Calculation Window",
          "start_time_local": "14:28:00",
          "end_time_local": "14:30:00",
          "days_of_week": "MON,TUE,WED,THU,FRI",
          "is_active": true
        }
      ],
      "holidays": [
        {
          "id": "113a47f0-a245-42d4-9d10-85f29910d601",
          "date": "2026-05-25",
          "name": "Memorial Day (Electronic Trading / Rolled Settlement)",
          "is_full_day_closure": false,
          "has_trading": true,
          "has_settlement": false,
          "settlement_rolled_to_next_day": true,
          "affected_product_groups": "ENERGY,METALS",
          "early_close_time_local": "12:30:00",
          "source_api": "EXCHANGE_CALENDAR_RULE",
          "is_active": true
        }
      ]
    }
    ```

---

## 3. Trading & Settlement Calendar Evaluator

`GET /api/exchanges/{identifier}/is-trading-day/`

An institutional diagnostic endpoint that determines whether an exchange is open for electronic trading, whether an official daily settlement price is established, or whether volume and settlement roll into the next business day.

### Query Parameters
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `date` | `string` | *Today's UTC Date* | Calendar date in `YYYY-MM-DD` format (e.g. `2026-05-25`). |
| `require_settlement` | `boolean` | `false` | When `true`, returns `result=false` on holiday trading sessions that do not produce daily settlement prices. |
| `product_group` | `string` | `null` | Filter by commodity group: `ENERGY`, `METALS`, `AGRICULTURE`, `SOFTS`. |

---

### Real-World Use Case Scenarios

#### Scenario A: Holiday Trading WITHOUT Settlement (Memorial Day on NYMEX)
On US Memorial Day, Globex trades Monday morning until 12:30 CT, but **no official daily settlement price** is calculated (trades roll to Tuesday):

=== "Request"

    ```bash
    curl -X GET "http://127.0.0.1:8000/api/exchanges/NYMEX/is-trading-day/?date=2026-05-25"
    ```

=== "Response"

    ```json
    {
      "exchange": "NYMEX",
      "mic": "XNYM",
      "date": "2026-05-25",
      "weekday": "Monday",
      "is_weekend": false,
      "is_trading_day": true,
      "is_settlement_day": false,
      "require_settlement": false,
      "product_group": null,
      "result": true,
      "market_status": "TRADING_WITHOUT_SETTLEMENT",
      "settlement_rolled_to_next_day": true,
      "early_close_time": "12:30:00",
      "holiday": {
        "name": "Memorial Day (Electronic Trading / Rolled Settlement)",
        "has_trading": true,
        "has_settlement": false,
        "affected_product_groups": "ENERGY,METALS"
      }
    }
    ```

#### Scenario B: Early Close WITH Settlement (Black Friday)
On the day after Thanksgiving, markets close early at 12:30 CT, but **the exchange DOES calculate an official early settlement price**:

=== "Request"

    ```bash
    curl -X GET "http://127.0.0.1:8000/api/exchanges/NYMEX/is-trading-day/?date=2026-11-27"
    ```

=== "Response"

    ```json
    {
      "exchange": "NYMEX",
      "mic": "XNYM",
      "date": "2026-11-27",
      "weekday": "Friday",
      "is_weekend": false,
      "is_trading_day": true,
      "is_settlement_day": true,
      "require_settlement": false,
      "product_group": null,
      "result": true,
      "market_status": "EARLY_CLOSE_WITH_SETTLEMENT",
      "settlement_rolled_to_next_day": false,
      "early_close_time": "12:30:00",
      "holiday": {
        "name": "Day After Thanksgiving (Black Friday Early Close)",
        "has_trading": true,
        "has_settlement": true,
        "affected_product_groups": "ALL"
      }
    }
    ```

#### Scenario C: Public Holiday where Exchange is OPEN (Columbus Day on CME)
US banks and government offices are closed, but **CME commodity futures remain fully open**:

=== "Request"

    ```bash
    curl -X GET "http://127.0.0.1:8000/api/exchanges/CME/is-trading-day/?date=2026-10-12"
    ```

=== "Response"

    ```json
    {
      "exchange": "CME",
      "mic": "XCME",
      "date": "2026-10-12",
      "weekday": "Monday",
      "is_weekend": false,
      "is_trading_day": true,
      "is_settlement_day": true,
      "require_settlement": false,
      "product_group": null,
      "result": true,
      "market_status": "REGULAR_TRADING",
      "settlement_rolled_to_next_day": false,
      "early_close_time": null,
      "holiday": null
    }
    ```

---

## 4. Exchange Summary

`GET /api/exchanges/summary/`

Returns aggregate counts across the global venue network.

=== "Request"

    ```bash
    curl -X GET "http://127.0.0.1:8000/api/exchanges/summary/"
    ```

=== "Response"

    ```json
    {
      "phase": "Phase 3: Exchange Master",
      "exchanges": {
        "total": 15,
        "active": 15,
        "global_benchmarks": 8
      },
      "trading_sessions": 18,
      "holidays_tracked": 372
    }
    ```

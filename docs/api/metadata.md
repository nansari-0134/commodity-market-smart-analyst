# Metadata & Taxonomy REST API

The Metadata API exposes the canonical taxonomy, units of measurement, and observation frequencies used across all financial and physical commodity datasets.

---

## 1. List Data Domains

`GET /api/metadata/domains/`

Retrieves the 34 canonical commodity data domains (Section 12), organized as a hierarchical tree with parent-child relationships.

### Query Parameters
| Parameter | Type | Description |
| :--- | :--- | :--- |
| `top_level_only` | `boolean` | When `true`, returns only root domains (e.g. `FUNDAMENTALS`, `EXCHANGE_MARKET_DATA`). |

### Example Request & Response

=== "cURL"

    ```bash
    curl -X GET "http://127.0.0.1:8000/api/metadata/domains/" -H "Accept: application/json"
    ```

=== "JSON Response"

    ```json
    [
      {
        "id": "e4b10b0a-7411-4a11-b011-b280145c1111",
        "code": "FUNDAMENTALS",
        "name": "Physical Fundamentals",
        "parent": null,
        "description": "Physical supply, demand, inventory, and flow metrics.",
        "display_order": 20,
        "subdomain_count": 4,
        "is_active": true
      },
      {
        "id": "f5c21c1b-8522-5b22-c122-c391256d2222",
        "code": "INVENTORIES",
        "name": "Commercial & Strategic Inventories",
        "parent": "FUNDAMENTALS",
        "description": "Stock levels (e.g. EIA crude stocks, LME warehouse stocks).",
        "display_order": 23,
        "subdomain_count": 0,
        "is_active": true
      }
    ]
    ```

---

## 2. List Units of Measure

`GET /api/metadata/units/`

Lists all 45 registered commodity industry measurement units across volume, mass, energy, power, time, and pricing conventions.

### Query Parameters
| Parameter | Type | Description |
| :--- | :--- | :--- |
| `unit_type` | `string` | Filter by physical dimension: `VOLUME`, `MASS`, `ENERGY`, `CURRENCY`, `TIME`, `RATIO`. |

### Example Request & Response

=== "cURL"

    ```bash
    curl -X GET "http://127.0.0.1:8000/api/metadata/units/?unit_type=VOLUME"
    ```

=== "JSON Response"

    ```json
    [
      {
        "id": "a1b2c3d4-0001-4000-8000-000000000001",
        "code": "BBL",
        "name": "Barrels",
        "unit_type": "VOLUME",
        "symbol": "bbl",
        "base_unit": null,
        "conversion_factor": "1.0000000000",
        "is_base_unit": true,
        "description": "42 US gallons of petroleum liquid"
      },
      {
        "id": "a1b2c3d4-0002-4000-8000-000000000002",
        "code": "MBBL",
        "name": "Thousand Barrels",
        "unit_type": "VOLUME",
        "symbol": "kbbl",
        "base_unit": "BBL",
        "conversion_factor": "1000.0000000000",
        "is_base_unit": false,
        "description": "One thousand standard petroleum barrels"
      },
      {
        "id": "a1b2c3d4-0003-4000-8000-000000000003",
        "code": "BCF",
        "name": "Billion Cubic Feet",
        "unit_type": "VOLUME",
        "symbol": "Bcf",
        "base_unit": "M3",
        "conversion_factor": "28316846.5920000000",
        "is_base_unit": false,
        "description": "Standard measure of natural gas volume (EIA storage standard)"
      }
    ]
    ```

---

## 3. List Observation Frequencies

`GET /api/metadata/frequencies/`

Lists 15 canonical observation frequencies with their standardized ticker codes, durations in seconds, and regular vs. event-driven classification.

### Example Request & Response

=== "cURL"

    ```bash
    curl -X GET "http://127.0.0.1:8000/api/metadata/frequencies/"
    ```

=== "JSON Response"

    ```json
    [
      {
        "id": "f1a2b3c4-1111-4000-8000-000000000001",
        "code": "1M",
        "name": "1 Minute",
        "interval_seconds": 60,
        "is_regular": true
      },
      {
        "id": "f1a2b3c4-1111-4000-8000-000000000002",
        "code": "30M",
        "name": "30 Minutes",
        "interval_seconds": 1800,
        "is_regular": true
      },
      {
        "id": "f1a2b3c4-1111-4000-8000-000000000003",
        "code": "DAILY",
        "name": "Daily",
        "interval_seconds": 86400,
        "is_regular": true
      },
      {
        "id": "f1a2b3c4-1111-4000-8000-000000000004",
        "code": "EVENT_DRIVEN",
        "name": "Event Driven",
        "interval_seconds": null,
        "is_regular": false
      }
    ]
    ```

---

## 4. Metadata Catalog Summary

`GET /api/metadata/summary/`

High-level metrics for dashboard cards and architectural verification.

### Example Request & Response

=== "cURL"

    ```bash
    curl -X GET "http://127.0.0.1:8000/api/metadata/summary/"
    ```

=== "JSON Response"

    ```json
    {
      "phase": "Phase 2: Metadata Schema",
      "data_domains": {
        "total": 34,
        "top_level": 21,
        "subdomains": 13
      },
      "units_of_measure": {
        "total": 45,
        "base_units": 9
      },
      "frequencies": {
        "total": 15,
        "regular": 13,
        "irregular_event": 2
      }
    }
    ```

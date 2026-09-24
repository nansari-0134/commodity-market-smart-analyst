# REST API: Endpoint Master Endpoints

The Endpoint Master API provides programmatic access to registered external vendor API routes, path templates, HTTP methods, parameter schemas, payload formats, and data envelope extraction selectors.

---

## 1. List Endpoints

Retrieve all registered vendor routes and endpoint templates with multi-dimensional filtering.

* **Endpoint**: `GET /api/endpoints/`
* **Query Parameters**:
  - `provider`: Filter by provider code (e.g. `EIA_GOV`, `CME_DATAMINE`) or UUID.
  - `dataset`: Filter by linked dataset code (e.g. `EIA_WPSR_PETROLEUM_STOCKS`) or UUID.
  - `protocol`: Filter by transport protocol (`REST_HTTP`, `FTP_SFTP`, `WEBSOCKET`).
  - `http_method`: Filter by HTTP method (`GET`, `POST`).
  - `response_format`: Filter by payload format (`JSON`, `CSV`, `TSV`, `XML`, `ZIP`, `PARQUET`, `EXCEL_XLSX`).
  - `is_active`: `true` or `false`.
  - `is_deprecated`: `true` or `false`.
  - `search`: Fuzzy search across `code`, `name`, `path_template`, and `description`.

=== "cURL"
    ```bash
    # List all active EIA endpoints returning JSON
    curl -X GET "http://127.0.0.1:8000/api/endpoints/?provider=EIA_GOV&response_format=JSON" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/endpoints/",
        params={"provider": "EIA_GOV", "response_format": "JSON"}
    )
    endpoints = response.json()
    for ep in endpoints:
        print(f"[{ep['http_method']}] {ep['code']} -> {ep['full_url']}")
    ```

=== "JSON Response (200 OK)"
    ```json
    [
      {
        "id": "76495df0-562a-4dfd-a89e-21ef65b93d39",
        "code": "EIA_PETROLEUM_SPOT_PRICES",
        "name": "EIA v2 Petroleum Spot Prices API",
        "provider_code": "EIA_GOV",
        "provider_name": "U.S. Energy Information Administration",
        "dataset_code": "EIA_WPSR_PETROLEUM_STOCKS",
        "dataset_name": "EIA Weekly Petroleum Status Report - Commercial Stocks",
        "protocol": "REST_HTTP",
        "protocol_display": "REST / HTTP API",
        "http_method": "GET",
        "path_template": "petroleum/pri/spt/data/",
        "full_url": "https://api.eia.gov/v2/petroleum/pri/spt/data/",
        "response_format": "JSON",
        "response_format_display": "JSON Object/Array",
        "cache_ttl_seconds": 3600,
        "is_active": true,
        "is_deprecated": false
      }
    ]
    ```

---

## 2. Retrieve Endpoint Specification

Retrieve detailed metadata for a single endpoint, including parameter schemas, custom headers, and data envelope selectors.

* **Endpoint**: `GET /api/endpoints/<code_or_uuid>/`

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/endpoints/EIA_PETROLEUM_SPOT_PRICES/" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get("http://127.0.0.1:8000/api/endpoints/EIA_PETROLEUM_SPOT_PRICES/")
    spec = response.json()
    print("Full URL:", spec["full_url"])
    print("Data Envelope:", spec["data_envelope_path"])
    print("Default Query Params:", spec["default_params"])
    ```

=== "JSON Response (200 OK)"
    ```json
    {
      "id": "76495df0-562a-4dfd-a89e-21ef65b93d39",
      "code": "EIA_PETROLEUM_SPOT_PRICES",
      "name": "EIA v2 Petroleum Spot Prices API",
      "provider_code": "EIA_GOV",
      "provider_name": "U.S. Energy Information Administration",
      "dataset_code": "EIA_WPSR_PETROLEUM_STOCKS",
      "dataset_name": "EIA Weekly Petroleum Status Report - Commercial Stocks",
      "protocol": "REST_HTTP",
      "protocol_display": "REST / HTTP API",
      "http_method": "GET",
      "path_template": "petroleum/pri/spt/data/",
      "full_url": "https://api.eia.gov/v2/petroleum/pri/spt/data/",
      "response_format": "JSON",
      "response_format_display": "JSON Object/Array",
      "cache_ttl_seconds": 3600,
      "is_active": true,
      "is_deprecated": false,
      "description": "Daily spot prices for WTI crude at Cushing, Brent crude, heating oil, and gasoline.",
      "data_envelope_path": "response.data",
      "default_params": {
        "frequency": "daily",
        "data[]": "value",
        "length": 5000
      },
      "custom_headers": {
        "Accept": "application/json"
      },
      "notes": "Requires api_key query param. Frequency choices: daily, weekly, monthly.",
      "created_at": "2026-09-23T18:55:08Z",
      "updated_at": "2026-09-23T18:55:08Z"
    }
    ```

---

## 3. Catalog Telemetry & Summary

Retrieve statistical aggregation of all registered API endpoints grouped by protocol, HTTP method, response format, and provider.

* **Endpoint**: `GET /api/endpoints/summary/`

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/endpoints/summary/" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get("http://127.0.0.1:8000/api/endpoints/summary/")
    data = response.json()
    print("Total Endpoints:", data["total_endpoints"])
    print("Protocols:", data["by_protocol"])
    print("Formats:", data["by_response_format"])
    ```

=== "JSON Response (200 OK)"
    ```json
    {
      "total_endpoints": 26,
      "active_endpoints": 26,
      "by_protocol": {
        "REST_HTTP": 26
      },
      "by_http_method": {
        "GET": 24,
        "POST": 2
      },
      "by_response_format": {
        "JSON": 24,
        "CSV": 2
      },
      "by_provider": {
        "EIA_GOV": 3,
        "CFTC_GOV": 2,
        "FRED_FED": 2,
        "USDA_FAS": 2,
        "CME_DATAMINE": 2
      }
    }
    ```

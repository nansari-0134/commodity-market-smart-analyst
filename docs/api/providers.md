# REST API: Provider Master Endpoints

The Provider Master API provides program access to registered external data vendors, government agencies, exchange data feeds, rate limit policies, and 12-factor credential references.

---

## 1. List Providers

Retrieve all registered external data sources and internal calculation engines with multi-dimensional filtering.

* **Endpoint**: `GET /api/providers/`
* **Query Parameters**:
  - `provider_type`: Filter by provider category (`GOVERNMENT_PUBLIC`, `EXCHANGE_DIRECT`, `PRICE_REPORTING_AGENCY`, `COMMERCIAL_AGGREGATOR`, `ALTERNATIVE_DATA`, `INTERNAL_ENGINE`).
  - `auth_type`: Filter by authentication protocol (`NONE_PUBLIC`, `API_KEY_QUERY_PARAM`, `API_KEY_HEADER`, `BEARER_TOKEN`, `BASIC_AUTH`, `OAUTH2_CLIENT_CREDENTIALS`).
  - `has_rate_limit`: `true` or `false`.
  - `is_active`: `true` or `false`.
  - `search`: Fuzzy search on `code`, `name`, and `description`.

=== "cURL"
    ```bash
    # List all government public statistical agencies
    curl -X GET "http://127.0.0.1:8000/api/providers/?provider_type=GOVERNMENT_PUBLIC" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/providers/",
        params={"provider_type": "GOVERNMENT_PUBLIC"}
    )
    providers = response.json()
    for provider in providers:
        print(f"[{provider['code']}] {provider['name']} - Auth: {provider['auth_type']}")
    ```

=== "JSON Response (200 OK)"
    ```json
    [
      {
        "id": "e58fa2f4-8a43-41bb-b85f-eb5a9a46328a",
        "code": "EIA_GOV",
        "name": "U.S. Energy Information Administration",
        "provider_type": "GOVERNMENT_PUBLIC",
        "provider_type_display": "Government / Public Statistical Agency",
        "base_url": "https://api.eia.gov/v2/",
        "auth_type": "API_KEY_QUERY_PARAM",
        "auth_type_display": "API Key (URL Query Parameter)",
        "env_var_name": "EIA_API_KEY",
        "rate_limit_requests": 5000,
        "rate_limit_window_seconds": 3600,
        "target_sla_pct": "99.80",
        "fallback_provider_code": null,
        "fallback_provider_name": null,
        "is_active": true,
        "display_order": 10
      }
    ]
    ```

---

## 2. Retrieve Provider by Code or UUID

Retrieve full institutional specification, developer portal link, and rate limit backoff parameters for a single provider.

* **Endpoint**: `GET /api/providers/{code_or_uuid}/`

=== "cURL"
    ```bash
    # Retrieve CME Datamine specifications
    curl -X GET "http://127.0.0.1:8000/api/providers/CME_DATAMINE/" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get("http://127.0.0.1:8000/api/providers/CME_DATAMINE/")
    data = response.json()
    print(f"Provider: {data['name']}")
    print(f"Auth Protocol: {data['auth_type']} -> Read env var: {data['env_var_name']}")
    print(f"Failover Target: {data['fallback_provider_code']}")
    ```

=== "JSON Response (200 OK)"
    ```json
    {
      "id": "8a31e84a-fa13-41cd-a5eb-3fa70c4bc81d",
      "code": "CME_DATAMINE",
      "name": "CME Group Datamine",
      "provider_type": "EXCHANGE_DIRECT",
      "provider_type_display": "Exchange Direct Market Data",
      "base_url": "https://datamine.cmegroup.com/api/v1/",
      "documentation_url": "https://www.cmegroup.com/market-data/datamine-api.html",
      "support_contact": "dataminesupport@cmegroup.com",
      "auth_type": "OAUTH2_CLIENT_CREDENTIALS",
      "auth_type_display": "OAuth 2.0 (Client Credentials Grant)",
      "env_var_name": "CME_DATAMINE_CLIENT_SECRET",
      "auth_param_name": "Authorization",
      "rate_limit_requests": 100,
      "rate_limit_window_seconds": 60,
      "backoff_seconds": 60,
      "target_sla_pct": "99.95",
      "fallback_provider_code": "ICE_DATA_SERVICES",
      "fallback_provider_name": "Intercontinental Exchange Data Services",
      "is_active": true,
      "display_order": 70,
      "description": "Official institutional market data service for NYMEX, COMEX, CBOT, and CME futures, options, and end-of-day settlement curves.",
      "notes": "Primary benchmark settlement provider for WTI (CL), Henry Hub (NG), Corn (ZC), and Gold (GC).",
      "created_at": "2026-09-22T18:58:10.123456Z",
      "updated_at": "2026-09-22T18:58:10.123456Z"
    }
    ```

---

## 3. Provider Telemetry Summary

Retrieve aggregate distribution and operational health telemetry across all registered providers.

* **Endpoint**: `GET /api/providers/summary/`

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/providers/summary/" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get("http://127.0.0.1:8000/api/providers/summary/")
    summary = response.json()
    print(f"Total Sources: {summary['total_providers']}")
    print(f"Breakdown by Vendor Type: {summary['by_provider_type']}")
    ```

=== "JSON Response (200 OK)"
    ```json
    {
      "total_providers": 20,
      "active_providers": 20,
      "with_rate_limits": 19,
      "with_fallbacks": 6,
      "by_provider_type": {
        "GOVERNMENT_PUBLIC": 6,
        "EXCHANGE_DIRECT": 6,
        "PRICE_REPORTING_AGENCY": 4,
        "COMMERCIAL_AGGREGATOR": 2,
        "ALTERNATIVE_DATA": 1,
        "INTERNAL_ENGINE": 1
      },
      "by_auth_type": {
        "BEARER_TOKEN": 9,
        "API_KEY_HEADER": 3,
        "API_KEY_QUERY_PARAM": 3,
        "NONE_PUBLIC": 3,
        "OAUTH2_CLIENT_CREDENTIALS": 2
      }
    }
    ```

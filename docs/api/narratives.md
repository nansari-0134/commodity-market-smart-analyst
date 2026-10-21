# AI Market Narratives REST API Reference (`/api/intelligence/`)

---

## 1. Overview & Base URL

The **Narratives REST API** exposes point-in-time AI market research briefings, executive flash alerts, and on-demand synthesis services.

* **Base Endpoint**: `/api/intelligence/narratives/`
* **Authentication**: Open in Development / Bearer Token in Production
* **Content-Type**: `application/json`

---

## 2. API Endpoints Catalog

| Method | Endpoint | Description |
| :---: | :--- | :--- |
| `GET` | `/api/intelligence/narratives/` | List historical market narratives with rich query filtering. |
| `GET` | `/api/intelligence/narratives/<id>/` | Retrieve complete details of a specific narrative by UUID. |
| `GET` | `/api/intelligence/narratives/latest/` | Retrieve the latest published narrative for a commodity. |
| `POST` | `/api/intelligence/narratives/generate/` | Trigger on-demand evidence-grounded AI narrative generation. |
| `GET` | `/api/intelligence/narratives/summary/` | Aggregate telemetry metrics by type, provider, and publication volume. |

---

## 3. Detailed Endpoint Documentation

### 3.1 List Market Narratives (`GET /api/intelligence/narratives/`)

Query Parameters:
- `commodity` (string): Canonical commodity code (e.g. `CL`, `BRENT`, `NG`, `GOLD`, `CORN`).
- `type` (string): Categorical narrative type (`MORNING_BRIEF`, `EXECUTIVE_FLASH`, `SUPPLY_DEMAND`, `RISK_ALERT`, `OUTLIER_DIVERGENCE`).
- `provider` (string): Filter by LLM provider (`static`, `gemini`, `claude`, `openai`, `ollama`).
- `status` (string): Filter by status (`PUBLISHED`, `DRAFT`, `ARCHIVED`).
- `search` (string): Keyword search across headlines and executive summaries.

=== "cURL"

    ```bash
    curl -X GET "http://127.0.0.1:8000/api/intelligence/narratives/?commodity=CL&type=MORNING_BRIEF" \
      -H "Accept: application/json"
    ```

=== "Python"

    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/intelligence/narratives/",
        params={"commodity": "CL", "type": "MORNING_BRIEF"}
    )
    narratives = response.json()
    for item in narratives:
        print(f"[{item['commodity_code']}] {item['headline']}")
    ```

=== "Example Response (200 OK)"

    ```json
    [
      {
        "id": "bf20c856-b804-405a-8a5c-8c00d10a29be",
        "commodity": "f8a7e0c4-912b-4d56-a19e-4b68db4c5b12",
        "commodity_code": "CL",
        "commodity_name": "Light Sweet Crude Oil (WTI)",
        "narrative_type": "MORNING_BRIEF",
        "narrative_type_display": "Morning Executive Briefing",
        "headline": "Light Sweet Crude Oil (WTI) (CL): Rangebound Equilibrium with MILD_BACKWARDATION Term Structure",
        "executive_summary": "Light Sweet Crude Oil (WTI) is trading at $92.53 (-1.29%), characterized by a BULLISH_EXTREME_VOLATILITY regime with an overall multi-factor score of +0.30...",
        "market_context_body": "## Market Structure & Quantitative State\nThe asset maintains an ADX(14) reading of 28.5...",
        "key_bullet_points": [
          "Price / Return: Spot reference at $92.53 (-1.29% on the session).",
          "Curve Regime: Forward curve in MILD_BACKWARDATION with M1-M2 prompt spread at $+0.463.",
          "Quant Posture: Composite rating +0.30 with RSI(14) at 54.2 and RVOL 1.25x."
        ],
        "risk_factors": [
          "Macro Factor Volatility: Shift in broader macroeconomic indicators or US Dollar index.",
          "Storage Rebalancing Risk: Deviation from seasonal normal could trigger prompt curve inversion."
        ],
        "evidence_snapshot": {
          "commodity_code": "CL",
          "last_price": 92.53,
          "return_1d": -0.0129,
          "curve_state": "MILD_BACKWARDATION"
        },
        "llm_provider": "static",
        "llm_model": "deterministic-rule-synthesizer-v1",
        "prompt_tokens": 420,
        "completion_tokens": 285,
        "status": "PUBLISHED",
        "compliance_disclaimer": "STANDARD REGULATORY COMPLIANCE NOTICE: This automated market briefing is strictly an analytical research...",
        "availability_time": "2026-10-21T05:08:46.691Z",
        "ingestion_time": "2026-10-21T05:08:46.691Z"
      }
    ]
    ```

---

### 3.2 Retrieve Latest Narrative (`GET /api/intelligence/narratives/latest/`)

=== "cURL"

    ```bash
    curl -X GET "http://127.0.0.1:8000/api/intelligence/narratives/latest/?commodity=CL" \
      -H "Accept: application/json"
    ```

=== "Python"

    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/intelligence/narratives/latest/",
        params={"commodity": "CL"}
    )
    latest = response.json()
    print("Latest Headline:", latest["headline"])
    print("Summary:", latest["executive_summary"])
    ```

---

### 3.3 Trigger On-Demand AI Generation (`POST /api/intelligence/narratives/generate/`)

Payload Parameters:
- `commodity` (string, optional): Commodity symbol (`CL`, `BRENT`, `NG`, `GOLD`, `CORN`). Default: `CL`.
- `narrative_type` (string, optional): `MORNING_BRIEF`, `EXECUTIVE_FLASH`, `SUPPLY_DEMAND`, `RISK_ALERT`, `OUTLIER_DIVERGENCE`. Default: `MORNING_BRIEF`.
- `provider` (string, optional): Override provider adapter (`static`, `gemini`, `claude`, `openai`, `ollama`). Default: system configured.

=== "cURL"

    ```bash
    curl -X POST "http://127.0.0.1:8000/api/intelligence/narratives/generate/" \
      -H "Content-Type: application/json" \
      -d '{
        "commodity": "NG",
        "narrative_type": "RISK_ALERT",
        "provider": "static"
      }'
    ```

=== "Python"

    ```python
    import requests

    payload = {
        "commodity": "NG",
        "narrative_type": "RISK_ALERT",
        "provider": "static"
    }
    response = requests.post(
        "http://127.0.0.1:8000/api/intelligence/narratives/generate/",
        json=payload
    )
    brief = response.json()
    print("Generated Narrative ID:", brief["id"])
    print("Headline:", brief["headline"])
    ```

=== "Example Response (201 Created)"

    ```json
    {
      "id": "e3f1ae34-ed68-4dce-a298-99347ede914a",
      "commodity_code": "NG",
      "commodity_name": "Henry Hub Natural Gas",
      "narrative_type": "RISK_ALERT",
      "narrative_type_display": "Systemic Risk & Divergence Alert",
      "headline": "Henry Hub Natural Gas (NG): Quantitative Divergence Alert Amid STRONG_CONTANGO Regime",
      "executive_summary": "Henry Hub Natural Gas is trading at $2.84 (+3.15%), characterized by a NEUTRAL regime...",
      "key_bullet_points": [
        "Price / Return: Spot reference at $2.84 (+3.15% on the session).",
        "Curve Regime: Forward curve in STRONG_CONTANGO with M1-M2 prompt spread at $-0.125."
      ],
      "risk_factors": [
        "Storage Rebalancing Risk: Deviation from seasonal normal could trigger prompt curve inversion."
      ],
      "status": "PUBLISHED",
      "llm_provider": "static"
    }
    ```

---

### 3.4 Telemetry Summary Metrics (`GET /api/intelligence/narratives/summary/`)

=== "cURL"

    ```bash
    curl -X GET "http://127.0.0.1:8000/api/intelligence/narratives/summary/" \
      -H "Accept: application/json"
    ```

=== "Python"

    ```python
    import requests

    response = requests.get("http://127.0.0.1:8000/api/intelligence/narratives/summary/")
    print(response.json())
    ```

=== "Example Response (200 OK)"

    ```json
    {
      "total_narratives": 16,
      "by_type": {
        "MORNING_BRIEF": 6,
        "SUPPLY_DEMAND": 5,
        "RISK_ALERT": 5
      },
      "by_provider": {
        "static": 16
      },
      "latest_publication": "2026-10-21T05:08:49.744Z"
    }
    ```

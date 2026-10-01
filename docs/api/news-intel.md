# News & Macroeconomic Catalyst REST API Reference

The News Intelligence API exposes scheduled macroeconomic releases, point-in-time consensus surprises, real-time news wire dispatches, and multi-commodity tagged sentiment breakdowns.

Base URL: `http://localhost:8000/api/news/`

---

## 1. Macroeconomic Catalyst Events (`/api/news/catalysts/`)

### List Catalyst Events
Returns scheduled and historical macroeconomic calendar events, survey consensus expectations, and economic surprise interpretations.

=== "cURL"
    ```bash
    curl -X GET "http://localhost:8000/api/news/catalysts/?commodity=CL" \
      -H "Accept: application/json"
    ```

=== "Python"
    ```python
    import requests

    response = requests.get(
        "http://localhost:8000/api/news/catalysts/",
        params={"commodity": "CL"},
        headers={"Accept": "application/json"},
    )
    catalysts = response.json()
    print(f"Retrieved {len(catalysts)} catalysts")
    ```

**Query Parameters:**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `commodity` | `string` | Filter where commodity is primary or affected (e.g. `CL`, `BRENT`, `CORN`) |
| `event_type` | `string` | `POLICY_OPEC`, `GOVERNMENT_WASDE`, `MACRO_CENTRAL_BANK`, `INVENTORY_EIA` |
| `impact_level` | `string` | `HIGH`, `MEDIUM`, `LOW` |
| `status` | `string` | `SCHEDULED`, `OCCURRED`, `POSTPONED`, `CANCELLED` |
| `start_date` | `string (YYYY-MM-DD)` | Filter scheduled datetime on or after date |
| `end_date` | `string (YYYY-MM-DD)` | Filter scheduled datetime on or before date |
| `search` | `string` | Search event name, notes, or agency |

**Sample Response (`200 OK`):**
```json
[
  {
    "id": "e4a781b0-13f9-4d22-8321-4f114c000101",
    "name": "EIA Weekly Petroleum Status Report (Crude Oil Inventories)",
    "event_type": "INVENTORY_EIA",
    "impact_level": "HIGH",
    "scheduled_datetime_utc": "2026-09-30T14:30:00Z",
    "status": "OCCURRED",
    "source_agency": "Energy Information Administration (EIA)",
    "period_covered": "Week Ended Sep 25, 2026",
    "primary_commodity_code": "CL",
    "primary_commodity_name": "Light Sweet Crude Oil (WTI)",
    "affected_commodities": [
      {"code": "CL", "name": "Light Sweet Crude Oil (WTI)", "sector": "ENERGY"},
      {"code": "BRENT", "name": "Brent Crude Oil", "sector": "ENERGY"},
      {"code": "RB", "name": "RBOB Gasoline", "sector": "ENERGY"},
      {"code": "HO", "name": "Heating Oil", "sector": "ENERGY"}
    ],
    "consensus_expectation": "-1.2000",
    "actual_value": "-4.5000",
    "prior_value": "-1.6000",
    "unit_symbol": "MMbbl",
    "surprise_magnitude": "-3.3000",
    "surprise_direction": "BULLISH_SURPRISE",
    "notes": "Massive 4.5M barrel draw in US commercial crude oil stockpiles exceeding consensus."
  }
]
```

---

### Upcoming Catalyst Releases (`/api/news/catalysts/upcoming/`)
Retrieves high-priority upcoming scheduled releases within the next $N$ calendar days.

=== "cURL"
    ```bash
    curl -X GET "http://localhost:8000/api/news/catalysts/upcoming/?days=14&commodity=CORN" \
      -H "Accept: application/json"
    ```

=== "Python"
    ```python
    import requests

    response = requests.get(
        "http://localhost:8000/api/news/catalysts/upcoming/",
        params={"days": 14, "commodity": "CORN"},
    )
    upcoming_events = response.json()
    ```

---

## 2. Multi-Commodity News Articles (`/api/news/articles/`)

### List News Articles
Retrieves news articles and headlines with SHA-256 deduplication and nested multi-commodity tags.

=== "cURL"
    ```bash
    curl -X GET "http://localhost:8000/api/news/articles/?commodity=BRENT" \
      -H "Accept: application/json"
    ```

=== "Python"
    ```python
    import requests

    response = requests.get(
        "http://localhost:8000/api/news/articles/",
        params={"commodity": "BRENT"},
    )
    articles = response.json()
    for art in articles:
        print(art["title"], art["overall_sentiment_label"])
    ```

**Sample Response (`200 OK`):**
```json
[
  {
    "id": "c7112028-090e-4ab8-86d1-4db81fa21004",
    "title": "OPEC+ Extends Voluntary Output Cuts of 2.2M Barrels per Day Through Q4",
    "summary": "OPEC+ energy ministers confirmed the extension of voluntary production curbs...",
    "source_name": "Reuters Energy Wire",
    "source_url": "https://www.reuters.com/business/energy/opec-output-cuts-extended-2026-09-30/",
    "published_at_utc": "2026-09-30T08:30:00Z",
    "author": "Amena Bakr & Alex Lawler",
    "overall_sentiment_score": "0.780",
    "overall_sentiment_label": "STRONG_BULLISH",
    "confidence_score": "0.920",
    "is_breaking": true,
    "primary_commodity_code": "CL",
    "primary_commodity_name": "Light Sweet Crude Oil (WTI)",
    "catalyst_event_name": "OPEC+ Joint Ministerial Monitoring Committee (JMMC) Meeting",
    "commodity_tags": [
      {
        "commodity_code": "CL",
        "commodity_name": "Light Sweet Crude Oil (WTI)",
        "commodity_sector": "ENERGY",
        "relevance_score": "1.000",
        "is_primary": true,
        "commodity_sentiment": "STRONG_BULLISH",
        "commodity_sentiment_score": "0.820",
        "matched_keywords": ["opec", "crude", "output cuts"]
      },
      {
        "commodity_code": "BRENT",
        "commodity_name": "Brent Crude Oil",
        "commodity_sector": "ENERGY",
        "relevance_score": "0.950",
        "is_primary": false,
        "commodity_sentiment": "STRONG_BULLISH",
        "commodity_sentiment_score": "0.800",
        "matched_keywords": ["opec", "crude", "brent"]
      },
      {
        "commodity_code": "HO",
        "commodity_name": "Heating Oil (ULSD)",
        "commodity_sector": "ENERGY",
        "relevance_score": "0.700",
        "is_primary": false,
        "commodity_sentiment": "MODERATE_BULLISH",
        "commodity_sentiment_score": "0.450",
        "matched_keywords": ["distillates", "heating oil"]
      },
      {
        "commodity_code": "SUGAR_11",
        "commodity_name": "Raw Sugar #11",
        "commodity_sector": "AGRICULTURE",
        "relevance_score": "0.400",
        "is_primary": false,
        "commodity_sentiment": "MODERATE_BULLISH",
        "commodity_sentiment_score": "0.300",
        "matched_keywords": ["ethanol parity"]
      }
    ]
  }
]
```

---

### Breaking News Stream (`/api/news/articles/breaking/`)
Filters the latest high-urgency breaking news wire alerts.

=== "cURL"
    ```bash
    curl -X GET "http://localhost:8000/api/news/articles/breaking/" \
      -H "Accept: application/json"
    ```

---

## 3. Cross-Commodity Sentiment Summary (`/api/news/summary/`)

Aggregates tagged news volume, average sentiment scores, and upcoming macroeconomic catalysts across physical commodities.

=== "cURL"
    ```bash
    curl -X GET "http://localhost:8000/api/news/summary/" \
      -H "Accept: application/json"
    ```

=== "Python"
    ```python
    import requests

    response = requests.get("http://localhost:8000/api/news/summary/")
    summary = response.json()
    for row in summary:
        print(f"{row['commodity_code']}: {row['dominant_sentiment_label']} (Score: {row['average_sentiment_score']})")
    ```

**Sample Response (`200 OK`):**
```json
[
  {
    "commodity_code": "CL",
    "commodity_name": "Light Sweet Crude Oil (WTI)",
    "article_count": 6,
    "average_sentiment_score": 0.465,
    "dominant_sentiment_label": "STRONG_BULLISH",
    "bullish_count": 5,
    "bearish_count": 0,
    "neutral_count": 1,
    "upcoming_catalysts_count": 2
  },
  {
    "commodity_code": "BRENT",
    "commodity_name": "Brent Crude Oil",
    "article_count": 3,
    "average_sentiment_score": 0.707,
    "dominant_sentiment_label": "STRONG_BULLISH",
    "bullish_count": 3,
    "bearish_count": 0,
    "neutral_count": 0,
    "upcoming_catalysts_count": 1
  }
]
```

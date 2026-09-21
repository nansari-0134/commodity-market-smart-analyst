<p align="center">
  <img src="logo.webp" alt="Commodity Market Intelligence System" width="130" />
</p>

<h1 align="center">Commodity Market Intelligence & Quantitative Platform</h1>

<p align="center">
  <strong>Institutional Quantitative Research, Forward Curve Analytics, Multi-Exchange Arbitrage & AI Market Narratives</strong>
</p>

<p align="center">
  <a href="https://nansari-0134.github.io/commodity-market-smart-analyst/">
    <img src="https://img.shields.io/badge/Documentation-Live%20MkDocs%20Site-2563eb?style=for-the-badge&logo=materialformkdocs&logoColor=white" alt="Live Documentation" />
  </a>
</p>

<p align="center">
  <a href="https://nansari-0134.github.io/commodity-market-smart-analyst/">
    <strong>📖 Open Full Documentation & Interactive REST API Reference →</strong>
  </a>
</p>

---

> [!WARNING]
> **Regulatory Notice & Standard Disclaimer**:
> This platform is strictly an analytical research, quantitative workflow, and market surveillance tool. It does **NOT** provide financial advice, investment recommendations, buy/sell signals, or "trading calls." All market models, forward curves, balance sheets, and LLM-generated narratives are for institutional informational and workflow automation purposes only. Trading physical commodities, futures, and derivatives involves substantial risk of loss.

---

## Features of the System

### 1. Pluggable & Source-Agnostic Provider Architecture
* **Strategy + Factory Pattern**: Core database schemas, business logic, REST APIs, and quant models are strictly decoupled from external data vendors.
* **Normalized Data Transfer Objects (DTOs)**: All feeds return strongly-typed dataclasses, eliminating vendor dictionary leaks across the application.
* **Zero-Friction Provider Swapping**: Change or plug in external data providers (e.g. CME Datamine, Bloomberg, Refinitiv, Argus, Platts, ICE) by updating `.env` configuration without modifying downstream code.
* **Deterministic Fallback Engine**: Built-in offline caches ensure zero downtime during network failures and provide 100% offline testing capabilities.

### 2. Point-in-Time Correctness & Anti-Lookahead Bias
* **Availability Tracking**: Every market observation, agency report, and balance sheet tracks `as_of_date`, `published_at`, and `ingested_at` via `PointInTimeModel`.
* **Revision History Preservation**: Preserves preliminary, revised, and superseded states for government releases (USDA WASDE, EIA Weekly Petroleum, CFTC Commitments of Traders).
* **Backtesting Integrity**: Eliminates hindsight bias by guaranteeing quantitative models only access data that was factually available at the exact historical decision timestamp.

### 3. Deterministic Mathematics & Strict Unit Conversion Engine
* **45 Canonical Units of Measure**: Comprehensive catalog covering volume (BBL, MCF, BCF, GAL), mass (MT, KG, LB, BU, CWT, TOZ, BALES), energy (MMBTU, MWH, THERM, BOE), currencies, and pricing conventions (USD/bbl, USC/bu, USC/lb, USD/t, USD/oz t).
* **Strict Dimensional Math**: Mathematical conversion engine (`UnitMaster.convert_to()`) enforces dimensional compatibility and raises exceptions on invalid conversions (e.g. mass to energy without conversion factors).
* **Quantitative Precedence**: Spreads, forward curves, carrying charges, and supply/demand balances are computed deterministically before any qualitative LLM reasoning occurs.

### 4. Institutional Exchange Venues & Trading Calendars
* **15 Global Execution Venues**: Canonical modeling across 9 jurisdictions including CME, NYMEX, COMEX, CBOT, ICE Futures U.S., ICE Futures Europe, LME, EEX, Bursa Malaysia (BMD), B3 Brasil, MCX India, SGX Singapore, SHFE, DCE, and ICE Abu Dhabi (IFAD).
* **ISO Standards Compliance**: Fully validated ISO 10383 Market Identifier Codes (MICs), IANA standard timezones, and ISO 3166-1 country codes.
* **Operational Sessions & Settlement Windows**: Models 18 distinct operating sessions, open outcry rings, electronic trading hours, and official daily settlement windows.
* **Sophisticated Holiday Calendar Engine**:
  * Distinguishes civic bank holidays from market trading operations (e.g., US futures trade normally on Columbus Day and Veterans Day).
  * Implements astronomical algorithms (Meeus/Jones/Butcher) for Good Friday dark days.
  * Models electronic trading without settlement (trade dates rolling into next business day), early close sessions (Black Friday, Christmas Eve), and split-session markets (MCX morning closed, evening open).

### 5. Canonical Physical Commodity Master
* **23 Benchmark Assets Across 7 Sectors**: Complete physical specifications spanning Energy, Grains & Oilseeds, Soft Commodities, Base Metals, Precious Metals, Livestock, and Environmental Carbon Allowances.
* **Deliverable Grade Chemistry Standards**: Detailed chemical and physical quality thresholds (API gravity ranges, maximum sulfur content, grain moisture limits, minimum test weights, and precious metal purity standards).
* **Delivery Infrastructure & Hubs**: Benchmark physical delivery points, pipeline interconnects, seaport marine terminals, and exchange-licensed vault networks (e.g., Cushing OK, Henry Hub LA, ARA Ports, New York Vaults).
* **Crop & Production Seasonality**: Tracks crop marketing year start months, peak harvest windows, seasonal demand surges, and structural basis tendencies.

### 6. Multi-Exchange Fungibility & Liquidity Surveillance
* **Cross-Market Asset Mapping**: Tracks the same physical commodity trading across multiple global exchanges (e.g. Gold on COMEX, MCX India, and SHFE Shanghai; WTI Crude on NYMEX and MCX; Copper on LME, COMEX, SHFE, and MCX).
* **Venue-Specific Contract Specifications**: Models localized contract lot sizes, trading currencies (USD, INR, CNY, EUR, MYR, BRL), and settlement mechanisms (Physical delivery vs. Cash index settlement).
* **Active Liquidity Filtering**: Incorporates Average Daily Volume (ADV) and Open Interest (OI) metrics to track meaningful liquidity and filter out dormant or illiquid contracts.

### 7. High-Performance REST API Suite
* **Filterable Endpoints**: Fully structured endpoints for commodities, exchange listings, trading calendars, data domains, and units of measure.
* **Multi-Dimensional Querying**: Query by sector, commodity group, exchange venue, settlement method, or free-text search.
* **Diagnostics & Summaries**: High-level statistical summaries providing sector distributions, settlement splits, and venue contract rankings.

### 8. Real-Time Terminal Dashboard Console
* **Institutional Aesthetics**: Dark-mode Bloomberg/Refinitiv-inspired interface optimized for high-density market surveillance.
* **Operational Telemetry**: Live indicators for database connectivity, point-in-time integrity status, active roadmap progress, and venue/asset counters.
* **10-Stage Quantitative Pipeline Flow**: Visual representation of the end-to-end data pipeline from raw ingestion to LLM market narrative generation.

### 9. Evidence-Linked LLM Market Narrative Engine (Architecture)
* **Fact-Anchored Intelligence**: The LLM operates strictly on top of verified mathematical features, forward curve slopes, and point-in-time balance sheets.
* **Audit Trail & Citation**: Every narrative claim or market commentary links directly to underlying quantitative data, normalized sources, and timestamped releases.
* **Deterministic Guardrails**: Replaces hallucination-prone financial LLM reasoning with deterministic feature extraction and scenario modeling.

### 10. Comprehensive Documentation Suite
* **MkDocs Material Architecture**: Production-grade documentation site deployed to GitHub Pages with clean typography and corporate branding.
* **Interactive Code Examples**: Every REST endpoint includes interactive tabs with copyable cURL commands and Python `requests` code snippets.
* **Developer Integration Guides**: Comprehensive tutorials explaining how to add new data providers, execute database migrations, and run automated test suites.

---

<p align="center">
  <a href="https://nansari-0134.github.io/commodity-market-smart-analyst/">
    <strong>Explore the Complete Architecture & Live Interactive API Documentation →</strong>
  </a>
</p>

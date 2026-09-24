<p align="center">
  <img src="logo.png" alt="Commodity Market Intelligence System" width="130" />
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

## System Description

The **Commodity Market Intelligence & Quantitative Platform** is an enterprise-grade quantitative research, physical commodity surveillance, forward curve analytics, and AI-driven narrative intelligence platform. Built on strict institutional principles, the system models global physical commodities, derivative contract specifications, multi-venue exchange liquidity, and macroeconomic supply/demand fundamentals. 

The architecture enforces a strict mathematical pipeline where deterministic domain logic, dimensional unit conversion, and calendar math strictly precede any qualitative AI reasoning. External data vendor independence is guaranteed through pluggable provider adapters, and point-in-time publication tracking eliminates hindsight and lookahead bias across all research and backtesting workflows.

---

## What It Is Capable Of

* **Multi-Asset & Multi-Venue Normalization**: Harmonizing heterogeneous physical commodity specifications, delivery hubs, chemical grade thresholds, and trading units across major global exchanges (CME, NYMEX, CBOT, ICE, LME, BMD, MCX, SGX, SHFE).
* **Deterministic Forward Curve & Term Structure Modeling**: Generating continuous forward curves, term structure spreads, calendar rolls, and seasonal basis analysis without lookahead bias.
* **Complex Expiry & Calendar Arithmetic**: Computing exact contract last trading days, notice days, and physical/cash settlement dates based on exchange holiday rules and astro-financial dark days (e.g. Good Friday, holiday shifts).
* **Multi-Exchange Fungibility & Arbitrage Surveillance**: Tracking cross-listed physical assets, pricing unit conversions, and monitoring liquid vs illiquid contracts using ADV (Average Daily Volume) and Open Interest (OI) metrics.
* **Strict Dimensional Unit Conversion**: Deterministically executing mathematical transformations across mass, volume, energy, and currency dimensions before data feeds into analytics models.
* **Evidence-Linked AI Narrative Generation**: Generating macroeconomic market summaries and executive briefings where every qualitative LLM claim is linked to verifiable quantitative metrics, historical releases, and audit trails.
* **Vendor-Agnostic Extensibility**: Ingesting market and fundamental data from any vendor (CME Datamine, ICE, Bloomberg, Refinitiv, USDA, EIA) via swappable provider contracts without changing database schemas or analytical engines.

---

## Features of the System

* **Pluggable Provider Architecture**: Implements Strategy + Factory patterns with strongly-typed Data Transfer Objects (DTOs), enabling zero-friction data vendor swapping and offline resilience.
* **Point-in-Time Correctness**: Tracks observation timestamps, publication dates, and ingestion audit trails via `PointInTimeModel` to guarantee zero lookahead bias in quantitative research.
* **Deterministic Unit Conversion Engine**: Provides 45 canonical units of measure (energy, mass, volume, currency) with strict dimensional validation (`UnitMaster.convert_to()`) prior to AI reasoning.
* **Global Exchange & Calendar Engine**: Canonical modeling for 15 global commodity exchanges, 18 operating sessions, civic vs trading holidays, and astronomical settlement date roll rules.
* **Physical Commodity Master**: Canonical specifications for 23 physical benchmark commodities across 7 sectors, including chemical grade standards, delivery hubs, and crop seasonality.
* **Multi-Venue Fungibility & Liquidity Filtering**: Maps cross-exchange listings with localized lot sizes and currency quotes, tracking ADV and Open Interest to isolate active liquidity.
* **Futures & Contract Master (Phase 5)**: Canonical derivative specifications, standard commodity month codes (F-Z), institutional expiry date calculation, and benchmark index roll schedules (GSCI, BCOM).
* **Dataset Master & Catalog (Phase 6)**: Canonical registry of 23 benchmark datasets, multi-asset commodity linkages, update cadences, ingestion modes, and pipeline SLAs.
* **Variable Master & Metrics Catalog (Phase 7)**: Standardized dictionary of 40 canonical commodity variables, stock vs. flow aggregation behaviors, and display transformation hints.
* **Provider Master & Source Catalog (Phase 8)**: Canonical directory of 20 institutional data vendors and agencies, 12-factor credential environment mapping, proactive rate limit budgets, and fallback failover chaining.
* **Endpoint & API Metadata (Phase 9)**: Canonical registry of 26 institutional benchmark API route templates, consolidated request schemas, payload envelope selectors, and dynamic URL builders.
* **Real-Time Intelligence Terminal**: High-density dark-theme surveillance dashboard displaying operational telemetry, database health, pipeline metrics, and system diagnostics.
* **High-Performance REST API Suite**: Production-grade endpoints for metadata, exchanges, commodities, contracts, datasets, variables, providers, and endpoints with rich filtering.
* **Fact-Anchored LLM Market Narratives**: Evidence-linked commentary engine anchoring generative narrative synthesis directly to quantitative features and official data releases.
* **Production MkDocs Documentation Suite**: Interactive documentation site deployed to GitHub Pages with interactive cURL/Python API consoles and provider integration guides.

---

<p align="center">
  <a href="https://nansari-0134.github.io/commodity-market-smart-analyst/">
    <strong>Explore the Complete Architecture & Live Interactive API Documentation →</strong>
  </a>
</p>

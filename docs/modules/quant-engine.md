# Module Architecture: Quantitative Research & Forward Curves Engine (`apps/quant_engine`)

The **Quantitative Research & Forward Curves Engine** is the deterministic analytical core of the Commodity Market Intelligence Platform. It sits directly between the raw point-in-time observation store (`apps/market_data`) and the LLM narrative synthesis layer (`apps/narratives`).

In strict alignment with the platform's **Deterministic Math Directive**, this module performs all multi-horizon volatility, forward curve spline interpolation, crack/crush spread modeling, cross-commodity cointegration, macro sensitivity tracking, and seasonality pattern recognition using pure vectorized NumPy and SciPy routines before any language model is invoked.

---

## 1. Architectural Pipeline & Data Flow

```mermaid
graph TD
    subgraph DataStore ["apps/market_data (Point-in-Time Store)"]
        P["MarketPriceObservation<br/>OHLCV, Settlements, Volume, Open Interest"]
        F["FundamentalObservation<br/>EIA Stocks, Refinery Utilization, Storage"]
        C["CommitmentOfTradersObservation<br/>Managed Money, Commercial Net"]
    end

    subgraph QuantCore ["apps/quant_engine/core (Pure Vectorized Zero-ORM)"]
        MS["market_state.py<br/>Returns, Realized Vol, Garman-Klass, ATR, RVOL, Shock-Z"]
        SP["spline.py & curve.py<br/>SciPy PCHIP Monotone Spline, Roll Yield, Curvature"]
        CR["spreads.py<br/>3:2:1 Crack Spread, Soybean Crush, Spark Spread"]
        XC["cross_commodity.py<br/>All-Pairs (253) Correlation, Engle-Granger Cointegration, OU Half-Life"]
        SN["seasonality.py<br/>5Y/10Y Envelopes, Directional Windows, 1M Vol Peak Expectation"]
        DV["divergence.py<br/>Price vs OI, Price vs COT, Price vs Curve, Robust MAD-Z"]
    end

    subgraph Service ["apps/quant_engine/services"]
        EB["QuantitativeEvidencePackageBuilder<br/>Bridge ORM to NumPy -> Strict Pydantic Schema"]
    end

    subgraph Persistence ["apps/quant_engine/models"]
        DR["DiscoveryRegistry<br/>Systematic Catalog of Significant Anomaly Findings"]
        EPS["EvidencePackageSnapshot<br/>Point-in-Time Immutable Snapshots"]
    end

    subgraph Downstream ["Downstream Execution & Reporting"]
        API["REST API Endpoints<br/>/api/quant/..."]
        LLM["apps/narratives (Phase 13)<br/>Prompt Synthesis Grounded in Deterministic Evidence"]
    end

    P --> EB
    F --> EB
    C --> EB

    EB --> MS
    EB --> SP
    EB --> CR
    EB --> XC
    EB --> SN
    EB --> DV

    MS --> EB
    SP --> EB
    CR --> EB
    XC --> EB
    SN --> EB
    DV --> EB

    EB --> EPS
    EB --> DR
    EB --> API
    EB --> LLM
```

---

## 2. Core Mathematical Principles & Design Directives

### 1. Vectorized Zero-ORM Architecture
All statistical and mathematical calculations inside `apps/quant_engine/core/` are decoupled from Django models and database queries. Core functions take pure `numpy.ndarray` arrays and scalar floats:
- **Sub-Millisecond Speed**: Vectorized linear algebra and spline evaluations execute in `< 1.5 ms`.
- **Source Independence**: Core mathematical routines can be unit-tested without a database or swapped into standalone Celery/Ray compute workers.
- **Robust Numerical Stability**: Zero third-party C-extension fragility. Cointegration Engle-Granger tests use pure NumPy linear algebra OLS regressions and augmented Dickey-Fuller (ADF) Dickey-Fuller critical tau polynomial expansions.

### 2. Zero LLM Mental Math
Language models are notorious for arithmetic drift, hallucinated percentages, and inability to calculate log returns or monotone spline derivatives.
- The Quant Engine computes every metric (returns, annualized volatility, crack spreads, roll yields, ADF $t$-statistics, $p$-values, half-lives, seasonal win rates) deterministically.
- Downstream narrative models receive a fully populated and validated Pydantic v2 `QuantitativeEvidencePackage` containing structured, immutable numeric values.

### 3. Point-in-Time Historical Honesty
When building an evidence package for a given `as_of_date`:
- Market prices, inventory levels, and COT positioning are strictly filtered by `publication_time <= point_in_time_query`.
- Forward curves only ingest contract settlements that traded on or prior to the evaluation date, preventing future lookahead leakage into backtests or LLM briefings.

---

## 3. Core Engine Components

### A. Market State & Volatility (`market_state.py`)
Calculates high-fidelity volatility and liquidity metrics across multiple lookback windows:
* **Log Returns**: $r_t = \ln(P_t / P_{t-1})$ evaluated across 1D, 5D, 21D (1M), 63D (3M), and 252D (1Y).
* **Close-to-Close Realized Volatility**: Annualized historical volatility:
  $$\sigma_{realized} = \sqrt{252 \times \frac{1}{N-1} \sum_{i=1}^{N} (r_i - \bar{r})^2}$$
* **Garman-Klass Extreme-Value Volatility**: Ingests intraday High, Low, Open, and Close to reduce variance by ~8x relative to close-to-close estimators:
  $$\sigma_{GK}^2 = \frac{252}{N} \sum_{i=1}^{N} \left[ 0.5 \left(\ln \frac{H_i}{L_i}\right)^2 - (2\ln 2 - 1) \left(\ln \frac{C_i}{O_i}\right)^2 \right]$$
* **Parkinson High-Low Volatility**: Continuous Brownian-motion based dispersion.
* **Average True Range (ATR)**: 14-period Wilder standard measuring price range expansion.
* **Volume Metrics**:
  - Relative Volume (RVOL): $\text{RVOL} = \text{Volume}_t / \overline{\text{Volume}}_{20D}$.
  - Volume Shock Z-Score: Standardized deviation of log volume relative to historical mean.
* **Open Interest (OI) Regime**: Identifies structural positioning flows:
  - `ACCUMULATION`: Price $\uparrow$, Open Interest $\uparrow$ (Aggressive long buying).
  - `SHORT_BUILD`: Price $\downarrow$, Open Interest $\uparrow$ (Aggressive short initiation).
  - `LIQUIDATION`: Price $\downarrow$, Open Interest $\downarrow$ (Longs exiting positions).
  - `SHORT_COVERING`: Price $\uparrow$, Open Interest $\downarrow$ (Shorts forced to buy to cover).

---

### B. Forward Curves & Monotone Splines (`spline.py` & `curve.py`)
Commodity futures term structures often exhibit localized supply stress (backwardation) or storage gluts (contango). Standard cubic splines introduce artificial oscillations (Runge phenomenon).
* **PCHIP Monotone Hermite Splines**: Uses SciPy's Piecewise Cubic Hermite Interpolating Polynomial (`scipy.interpolate.PchipInterpolator`) to preserve shape monotonicity between discrete contract maturities.
* **Term Structure Sampling**: Interpolates daily points from Day 0 (Spot) through Month 24, providing continuous forward curves for any maturity.
* **Roll Yield & Annualized Slope**:
  $$\text{Roll Yield}_{1Y} = \frac{P_{M1} - P_{M12}}{P_{M1}} \times 100\%$$
* **Curvature (Butterfly Spread)**: $2 \times P_{M2} - (P_{M1} + P_{M3})$, quantifying kinks in prompt physical delivery.

---

### C. Physical Processing Spreads (`spreads.py`)
Computes real-time refining and processing margins with automated volumetric unit conversions:

| Processing Complex | Formula | Units | Physical Interpretation |
| :--- | :--- | :--- | :--- |
| **Refinery 3:2:1 Crack Spread** | $\frac{2 \times P_{\text{RBOB}} \times 42 + 1 \times P_{\text{HO}} \times 42 - 3 \times P_{\text{WTI}}}{3}$ | \$/barrel | Economic incentive for refineries to process light sweet crude into gasoline and distillates. |
| **Soybean Crush Margin** | $(P_{\text{Meal}} \times 0.022) + (P_{\text{Oil}} \times 0.11) - P_{\text{Beans}}$ | \$/bushel | Economic profitability of crushing raw soybeans into soybean meal (protein feed) and soybean oil (food/biodiesel). |
| **Natural Gas Spark Spread** | $P_{\text{Power}} - (\text{Heat Rate} \times P_{\text{NG}})$ | \$/MWh | Margin earned by gas-fired power plants burning natural gas to generate electricity. |

---

### D. Cross-Commodity & Macro Sensitivity Engine (`cross_commodity.py`)

#### 1. All-Pairs Correlation & Cointegration
- Computes pairwise return correlation matrix across all 253 commodity pairs ($N \times (N-1) / 2$).
- **Engle-Granger Two-Step Cointegration**:
  1. OLS regression of $Y_t$ on $X_t$ to establish dynamic hedge ratio $\beta$:
     $$Y_t = \alpha + \beta X_t + \epsilon_t$$
  2. Augmented Dickey-Fuller (ADF) unit root test on residuals $\epsilon_t$ to verify stationarity ($I(0)$).
  3. Continuous Ornstein-Uhlenbeck (OU) mean-reversion modeling to compute equilibrium half-life in days:
     $$\Delta \epsilon_t = \theta (\mu - \epsilon_{t-1}) \Delta t + \sigma dW_t \implies \text{Half-Life} = \frac{\ln 2}{\theta}$$
  4. Residual Z-score: Standardized deviation of current spread from equilibrium mean, highlighting statistical arbitrage opportunities.

#### 2. Curated Logical Commodity Complexes
To complement brute-force all-pairs statistical search, the engine maintains 8 curated physical/economic complexes with explicit structural rationales:

| Complex Code | Logical Name | Commodities | Economic / Physical Relationship Rationale |
| :--- | :--- | :--- | :--- |
| `REFINERY_ENERGY` | Refinery Energy Complex | WTI, Brent, RBOB Gasoline, Heating Oil, Gasoil | Direct physical refining inputs and output products. High cointegration governed by cracking margins and crude runs. |
| `OILSEED_CRUSH` | Oilseed Crush Complex | Soybeans, Soybean Oil, Soybean Meal | Structural input-output processing relationship. Cointegration maintained by soybean crush plants and feed demand. |
| `BIOFUEL_SUGAR` | Biofuel & Sugar Feedstock Complex | Sugar #11, Ethanol, WTI Crude Oil | Brazilian flex-fuel vehicle fleet creates structural parity: Mills toggle between cane-for-sugar and cane-for-ethanol based on crude parity. |
| `GRAIN_FEED` | Feedgrain & Starch Complex | Corn, Chicago Wheat, Kansas Wheat | Direct substitutability in livestock feed rations and shared midwestern growing acres. |
| `LIVESTOCK_FEEDING` | Livestock Feeding Complex | Live Cattle, Feeder Cattle, Corn | Feedlot economics: Corn is the primary input cost to fatten feeder cattle into market-ready live cattle. |
| `POWER_SPARK` | Natural Gas & Power Generation | Natural Gas, Electricity | Natural gas is the marginal fuel source for peak power generation via combined-cycle turbines. |
| `PRECIOUS_MONETARY` | Precious Monetary Complex | Gold, Silver, Platinum | Monetary metals with store-of-value dynamics, real interest rate sensitivity, and central bank reserve allocations. |
| `BASE_METALS` | Base Industrial Metals | Copper, Aluminum, Zinc, Nickel | Global macroeconomic, construction, and green energy transition industrial barometers. |

#### 3. Macro Factor Sensitivities
Tracks direct correlation and sensitivity between physical commodities and exogenous macro drivers:
- **US Dollar Index (DXY)**: Inversely correlated with dollar-denominated globally traded commodities.
- **US 10-Year Real Yields**: Primary opportunity-cost driver for non-yielding store-of-value assets (Gold, Silver).
- **WTI Crude Oil**: Macro energy bellwether driving transportation and chemical input costs for agricultural softs (Sugar, Corn).

---

### E. Seasonality & Directional Pattern Recognition (`seasonality.py`)
Agricultural and energy commodities follow distinct seasonal patterns driven by crop planting/harvest schedules, summer driving demand, and winter heating inventory drawdowns:
* **Day-of-Year 5Y & 10Y Envelopes**: Computes normalized seasonal trajectories with median, 10th percentile, and 90th percentile bounds.
* **Directional Tenure Windows**: Evaluates 10-day, 30-day, and 63-day historical forward performance over the past 5 to 10 years:
  - Historical win rate (% of years with positive forward return over window).
  - Student's $t$-statistic and directional move conviction score.
* **Forward 1-Month Volatility Peak Expectation**: Pinpoints historical calendar months with recurring volatility expansion (e.g. August Midwest weather market for corn/soybeans).
* **Physical Commodity Lifecycle Integration**: Encodes official agronomic and consumption cycles:
  - `CORN`: US planting (Apr-May), pollination window (Jul), harvest pressure (Sep-Nov).
  - `WTI`: Refinery spring maintenance (Mar-Apr), summer driving peak (Jun-Aug), winter diesel build (Oct-Nov).
  - `NG`: Shoulder injection season (Apr-Oct), peak heating withdrawal (Dec-Feb).

---

### F. Multi-Dimensional Divergence Detection (`divergence.py`)
Detects quantitative anomalies where price action conflicts with institutional positioning or fundamental indicators:
- **Price vs Open Interest**: Price making 20-day new highs on deteriorating open interest signals exhaustion / short-squeeze ending.
- **Price vs Commercial COT**: Price reaching multi-month highs while commercial hedgers hold near-record net short positions indicates institutional distribution into retail buying.
- **Price vs Forward Curve**: Spot price rallying while front-month calendar spreads collapse into contango signals prompt physical oversupply.
- **Robust Outlier Scoring**: Utilizes Median Absolute Deviation (MAD-Z):
  $$\text{MAD-Z} = \frac{0.6745 \times (x_i - \text{median}(X))}{\text{median}(|x_i - \text{median}(X)|)}$$
  Ensures resilience against extreme black-swan outliers.

---

## 4. Intermediate Evidence Schema (`QuantitativeEvidencePackage`)

The ultimate deliverable of `apps/quant_engine` is a strictly-typed Pydantic v2 `QuantitativeEvidencePackage` matching Section 5.12 of the Master Architecture PDF.

```json
{
  "commodity_code": "CL",
  "as_of_date": "2026-09-24",
  "market_state": {
    "settlement_price": 75.85,
    "returns_1d": 0.0125,
    "returns_5d": -0.0084,
    "returns_21d": 0.0412,
    "returns_63d": 0.0789,
    "realized_vol_21d": 0.2450,
    "realized_vol_63d": 0.2280,
    "garman_klass_vol_21d": 0.2310,
    "atr_14": 1.65,
    "rvol_20d": 1.34,
    "volume_shock_zscore": 1.82,
    "oi_regime": "ACCUMULATION"
  },
  "forward_curve": {
    "prompt_spread_m1_m2": 0.45,
    "roll_yield_1y_pct": 5.82,
    "term_structure_slope": "BACKWARDATION",
    "butterfly_curvature": -0.12,
    "interpolated_nodes": [
      {"month": 0, "days": 0, "price": 75.85},
      {"month": 1, "days": 30, "price": 75.40},
      {"month": 12, "days": 365, "price": 71.43}
    ]
  },
  "spreads": {
    "crack_321": 24.50,
    "crush_margin": null,
    "spark_spread": null
  },
  "cross_commodity": {
    "logical_complex": "REFINERY_ENERGY",
    "logical_complex_name": "Refinery Energy Complex",
    "economic_rationale": "Direct physical refining inputs and output products. High cointegration governed by cracking margins and crude runs.",
    "cointegration_pairs": [
      {
        "pair": "CL-XB",
        "hedge_ratio_beta": 0.84,
        "adf_t_statistic": -3.85,
        "p_value": 0.0024,
        "is_cointegrated": true,
        "half_life_days": 4.2,
        "residual_zscore": -1.45
      }
    ],
    "macro_factor_sensitivities": {
      "US_DOLLAR_INDEX": -0.68,
      "CRUDE_OIL_WTI": 1.00
    }
  },
  "seasonality": {
    "directional_patterns": [
      {
        "tenure_days": 30,
        "direction": "BULLISH",
        "historical_win_rate": 0.80,
        "mean_return": 0.042,
        "t_statistic": 2.65,
        "significance": "HIGH"
      }
    ],
    "forward_vol_peak": {
      "historical_peak_month": 10,
      "peak_month_name": "October",
      "expected_vol_ratio": 1.25,
      "narrative": "Historical volatility expands into October due to heating oil inventory repositioning and shoulder season refinery maintenance."
    }
  },
  "divergences": [
    {
      "type": "PRICE_OI_DIVERGENCE",
      "severity": "MODERATE",
      "description": "Price pushing new 20-day high with open interest declining (potential short covering exhaustion)."
    }
  ]
}
```

---

## 5. Persistence Models (`apps/quant_engine/models.py`)

### `DiscoveryRegistry`
An auditable discovery catalog that logs statistically significant anomalies, cointegration breaks, and regime transitions.
* `discovery_type`: `COINTEGRATION_BREAK`, `SEASONAL_ANOMALY`, `OI_DIVERGENCE`, `SPREAD_EXTREME`, `CURVE_INVERSION`.
* `commodity`: Related commodity foreign key.
* `metrics`: JSON dictionary storing exact $z$-scores, $p$-values, and beta ratios.
* `is_active`: Flag indicating whether the anomaly currently persists.

### `EvidencePackageSnapshot`
Immutable point-in-time snapshot of the generated `QuantitativeEvidencePackage`. Ensures historical research queries, audit trails, and narrative briefings can be reproduced verbatim.

---

## 6. Regulatory & Analytical Disclaimers
All outputs of the Quantitative Research Engine are computed strictly for analytical and research workflow automation. They do not constitute financial advice, trading signals, or investment recommendations under SEC, CFTC, or FCA regulations.

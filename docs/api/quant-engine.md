# REST API: Quantitative Research & Forward Curves Endpoints

The Quantitative Research REST API provides high-performance access to deterministic quantitative calculations, forward curve splines, transformation spreads, cross-commodity cointegration findings, seasonality pattern recognition, and the full Section 5.12 `QuantitativeEvidencePackage`.

All endpoints are served under `/api/quant/`.

---

## 1. Full Quantitative Evidence Package

Retrieve the complete, validated quantitative evidence package for a target commodity matching Section 5.12 of the Master Architecture.

* **Endpoint**: `GET /api/quant/evidence-package/`
* **Query Parameters**:
  - `commodity`: Canonical commodity code (e.g. `CL`, `BRENT`, `NG`, `ZC`, `ZS`). Default: `CL`.
  - `persist`: `true` to store an immutable snapshot in `EvidencePackageSnapshot` and log anomalies to `DiscoveryRegistry`. Default: `false`.

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/quant/evidence-package/?commodity=CL&persist=true" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/quant/evidence-package/",
        params={"commodity": "CL", "persist": "true"}
    )
    package = response.json()
    print(f"Evidence Package for {package['market']} as of {package['as_of']}")
    print(f"Prompt Spot Price: ${package['market_state']['spot_price']:.2f}")
    print(f"20D Realized Volatility: {package['market_state']['realized_vol_20d']:.2%}")
    print(f"Curve Regime: {package['market_state']['curve_state']}")
    ```

=== "JSON Response (200 OK)"
    ```json
    {
      "market": "CL",
      "as_of": "2026-09-24",
      "market_state": {
        "spot_price": 75.85,
        "returns_1d": 0.0125,
        "returns_5d": -0.0084,
        "returns_20d": 0.0412,
        "returns_60d": 0.0789,
        "realized_vol_20d": 0.2450,
        "realized_vol_60d": 0.2280,
        "garman_klass_vol_20d": 0.2310,
        "parkinson_vol_20d": 0.2295,
        "atr_14": 1.65,
        "volume_shock_z": 1.82,
        "rvol_20d": 1.34,
        "oi_regime": "ACCUMULATION",
        "curve_state": "BACKWARDATION",
        "prompt_spread_1m_2m": 0.45,
        "roll_yield_1y": 5.82,
        "butterfly_curvature": -0.12
      },
      "positioning_state": {
        "cot_available": true,
        "managed_money_net": 185420,
        "managed_money_percentile_3y": 72.4,
        "commercial_net": -210500,
        "total_open_interest": 1845000,
        "cot_report_date": "2026-09-22"
      },
      "spreads": {
        "crack_321": 24.50,
        "crush_margin": null,
        "spark_spread": null
      },
      "cross_commodity": {
        "primary_complex": "REFINERY_ENERGY_COMPLEX",
        "complex_members": ["CL", "BRENT", "RB", "HO", "LGO"],
        "key_spreads": {
          "prompt_spread": 0.45
        },
        "cointegration_pairs": [
          {
            "pair": "CL-XB",
            "hedge_ratio_beta": 0.84,
            "adf_t_statistic": -3.85,
            "p_value": 0.0024,
            "is_cointegrated": true,
            "half_life_days": 4.2,
            "residual_zscore": -1.45,
            "status": "MEAN_REVERSION_CANDIDATE"
          }
        ],
        "rolling_correlations": {
          "BRENT": 0.88,
          "RB": 0.82
        },
        "macro_factor_sensitivities": {
          "dxy_corr_60d": -0.65,
          "real_rates_corr_60d": -0.25
        }
      },
      "seasonality": {
        "day_of_year": 267,
        "current_seasonal_z_score": 0.45,
        "percentiles_5y": {
          "min": 68.2,
          "p25": 72.4,
          "median": 75.1,
          "p75": 78.9,
          "max": 84.5
        },
        "directional_tendency": {
          "tenure_window": "FORWARD_30D",
          "win_rate": 0.80,
          "median_return": 0.038,
          "mean_return": 0.042,
          "t_statistic": 2.65,
          "pattern_classification": "BULLISH_SEASONAL_BIAS"
        },
        "forward_volatility_expectation": {
          "forward_expected_vol_30d": 26.5,
          "percentile_vs_annual": 78.0,
          "is_peak_volatility_window": true,
          "seasonal_catalyst": "Refinery Autumn Turnaround"
        }
      },
      "divergences": [],
      "provenance": {
        "price_source": "NYMEX",
        "curve_interpolation": "SciPy PCHIP Monotone Spline",
        "generated_at": "2026-09-24T18:00:00Z"
      }
    }
    ```

---

## 1.1 Live Quantitative Feature Engine (LLM-Ready State)

Retrieve real-time normalized, relative, and interpretable quantitative features matching Section 21 of the platform specification. Optimized directly for downstream Financial Research LLMs.

* **Endpoint**: `GET /api/quant/live-features/`
* **Query Parameters**:
  - `commodity`: Canonical commodity code (e.g. `CL`, `BRENT`, `NG`, `CORN`, `GOLD`). Default: `CL`.
  - `timeframe`: Evaluation horizon (`1D`, `1h`, `15m`, `5m`, `1m`). Default: `1D`.
  - `refresh`: `true` to fetch the latest tick from market data provider before computing features. Default: `false`.
  - `output`: `json` (Section 21 JSON schema) or `prompt` (high-density Markdown for LLM prompt context). Default: `json`.

=== "cURL (JSON)"
    ```bash
    # Retrieve normalized quantitative features for WTI Crude
    curl -X GET "http://127.0.0.1:8000/api/quant/live-features/?commodity=CL" \
         -H "Accept: application/json"
    ```

=== "cURL (LLM Prompt Context)"
    ```bash
    # Retrieve high-density Markdown prompt context for LLM injection
    curl -X GET "http://127.0.0.1:8000/api/quant/live-features/?commodity=CL&output=prompt" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/quant/live-features/",
        params={"commodity": "CL", "output": "json"}
    )
    features = response.json()

    print(f"Instrument: {features['instrument']} ({features['name']})")
    print(f"Price: ${features['price']['last']} | 20D Percentile: {features['price']['percentile_20d']}% | Z: {features['price']['zscore_20d']:+}σ")
    print(f"Trend: {features['trend']['trend_state']} | ADX: {features['trend']['adx']}")
    print(f"Momentum: {features['momentum']['momentum_state']} | RSI: {features['momentum']['rsi']}")
    print(f"Composite Quant Rating: {features['scores']['overall_composite_score']:+}")
    ```

=== "JSON Response (200 OK)"
    ```json
    {
      "instrument": "CL",
      "name": "Light Sweet Crude Oil (WTI)",
      "sector": "ENERGY",
      "timestamp": "2026-10-08T13:20:00Z",
      "timeframe": "1D",
      "data_quality": "VALID",
      "price": {
        "last": 75.85,
        "return_1d": 0.0125,
        "log_return_1d": 0.0124,
        "return_acceleration_1d": 0.0035,
        "percentile_20d": 96.0,
        "zscore_20d": 2.01
      },
      "trend": {
        "ema_structure": "bullish",
        "ema_slope": "positive",
        "adx": 31.4,
        "trend_state": "strong_bullish",
        "dist_ema20_pct": 2.1,
        "dist_ema50_pct": 4.5,
        "dist_ema200_pct": 8.9
      },
      "momentum": {
        "rsi": 72.0,
        "rsi_percentile": 91.0,
        "rsi_direction": "rising",
        "macd": 1.25,
        "macd_signal": 0.94,
        "macd_histogram": 0.31,
        "histogram_direction": "increasing",
        "momentum_state": "strengthening"
      },
      "volatility": {
        "atr": 1.42,
        "atr_pct": 1.55,
        "atr_percentile": 93.0,
        "realized_volatility": 41.0,
        "vol_percentile": 94.0,
        "regime": "high"
      },
      "volume": {
        "volume": 284100,
        "relative_volume": 1.50,
        "zscore": 2.2,
        "state": "high"
      },
      "structure": {
        "state": "bullish_breakout",
        "range_position_20d": 94.0,
        "range_position_60d": 88.0,
        "nearest_resistance_distance_pct": 0.35,
        "nearest_support_distance_pct": -0.46,
        "nearest_resistance": 76.12,
        "nearest_support": 75.50,
        "swing_structure": "higher_highs_higher_lows",
        "breakout_confirmed": true
      },
      "vwap": {
        "vwap": 75.30,
        "vwap_deviation_pct": 0.73
      },
      "curve": {
        "spread_f1_f2": 0.45,
        "spread_f2_f3": 0.30,
        "spread_f1_f3": 0.75,
        "spread_zscore": 1.4,
        "spread_percentile": 82.0,
        "curve_state": "backwardation",
        "curve_slope_annualized": -0.052
      },
      "relative_value": {
        "benchmark_pair": "CL-BRENT",
        "rolling_correlation": 0.88,
        "spread_zscore": 0.65
      },
      "order_flow": {
        "imbalance": null,
        "cumulative_delta": null,
        "delta_direction": "unavailable",
        "is_available": false
      },
      "liquidity": {
        "bid_ask_spread": 0.02,
        "bid_ask_spread_ticks": 2.0,
        "spread_percentile": 35.0,
        "depth_imbalance": null,
        "is_available": false
      },
      "fundamentals": {
        "primary_variable": "CRUDE_CUSHING_STOCKS",
        "latest_value": 24.5,
        "normal_reference": 32.0,
        "deviation_abs": -7.5,
        "deviation_pct": -23.4,
        "inventory_zscore": -2.1,
        "fundamental_momentum": "tightening"
      },
      "events": {
        "latest_event": "EIA Weekly Petroleum",
        "surprise": -1.8,
        "standardized_surprise": -1.4,
        "immediate_reaction_1h_pct": 0.85,
        "reaction_volatility_pct": 1.2
      },
      "regime": {
        "trend": "strong_bullish",
        "volatility": "high",
        "overall": "bullish_high_volatility"
      },
      "divergence": {
        "has_divergence": false,
        "active_divergences": []
      },
      "scores": {
        "trend_score": 0.85,
        "momentum_score": 0.72,
        "volatility_score": 0.65,
        "volume_score": 0.60,
        "structure_score": 0.80,
        "curve_score": 0.75,
        "relative_value_score": 0.45,
        "fundamentals_score": 0.70,
        "event_score": 0.50,
        "overall_composite_score": 0.74
      }
    }
    ```

---

## 2. Market State & Volatility Analytics


Retrieve multi-horizon log returns, Garman-Klass volatility, Average True Range (ATR), volume shocks, and institutional Open Interest regimes.

* **Endpoint**: `GET /api/quant/market-state/`
* **Query Parameters**:
  - `commodity`: Canonical commodity code (e.g. `CL`, `BRENT`, `NG`).

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/quant/market-state/?commodity=CL" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/quant/market-state/",
        params={"commodity": "CL"}
    )
    data = response.json()
    state = data["market_state"]
    print(f"RVOL: {state['rvol_20d']}x | OI Regime: {state['oi_regime']}")
    ```

=== "JSON Response (200 OK)"
    ```json
    {
      "commodity": "CL",
      "as_of": "2026-09-24",
      "market_state": {
        "spot_price": 75.85,
        "returns_1d": 0.0125,
        "returns_5d": -0.0084,
        "returns_20d": 0.0412,
        "returns_60d": 0.0789,
        "realized_vol_20d": 0.2450,
        "realized_vol_60d": 0.2280,
        "garman_klass_vol_20d": 0.2310,
        "parkinson_vol_20d": 0.2295,
        "atr_14": 1.65,
        "volume_shock_z": 1.82,
        "rvol_20d": 1.34,
        "oi_regime": "ACCUMULATION",
        "curve_state": "BACKWARDATION",
        "prompt_spread_1m_2m": 0.45,
        "roll_yield_1y": 5.82,
        "butterfly_curvature": -0.12
      },
      "positioning": {
        "cot_available": true,
        "managed_money_net": 185420,
        "managed_money_percentile_3y": 72.4,
        "commercial_net": -210500,
        "total_open_interest": 1845000,
        "cot_report_date": "2026-09-22"
      },
      "divergences": []
    }
    ```

---

## 3. Forward Curve Term Structure & Splines

Retrieve forward curve analytics, prompt spreads, roll yield, and curvature.

* **Endpoint**: `GET /api/quant/curve/`
* **Query Parameters**:
  - `commodity`: Canonical commodity code (e.g. `CL`, `BRENT`, `NG`).

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/quant/curve/?commodity=CL" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/quant/curve/",
        params={"commodity": "CL"}
    )
    curve = response.json()
    print(f"Curve Structure: {curve['curve_state']}")
    print(f"Prompt M1-M2 Spread: ${curve['prompt_spread']:.2f}")
    print(f"1-Year Roll Yield: {curve['roll_yield_1y']:.2f}%")
    ```

=== "JSON Response (200 OK)"
    ```json
    {
      "commodity": "CL",
      "as_of": "2026-09-30",
      "spot_price": 90.4,
      "curve_state": "STRONG_BACKWARDATION",
      "prompt_spread": 2.2247,
      "roll_yield_1y": -29.53,
      "butterfly": -4.1347,
      "contract_count": 24,
      "contracts": [
        {
          "tenor": "M1",
          "settlement_price": 92.6247,
          "spread_to_prompt": 2.2247,
          "annualized_roll_yield_pct": -29.53,
          "volume": 284500,
          "is_preliminary": false,
          "options": {
            "atm_implied_volatility": 32.5,
            "skew_25d": 2.8,
            "put_call_volume_ratio": 0.85,
            "put_call_oi_ratio": 0.90
          }
        },
        {
          "tenor": "M2",
          "settlement_price": 90.4000,
          "spread_to_prompt": 0.0,
          "annualized_roll_yield_pct": 0.0,
          "volume": 195000,
          "is_preliminary": false,
          "options": {
            "atm_implied_volatility": 32.059,
            "skew_25d": 2.637,
            "put_call_volume_ratio": 0.85,
            "put_call_oi_ratio": 0.90
          }
        },
        {
          "tenor": "M3",
          "settlement_price": 88.4900,
          "spread_to_prompt": -1.9100,
          "annualized_roll_yield_pct": 8.45,
          "volume": 142000,
          "is_preliminary": false,
          "options": {
            "atm_implied_volatility": 31.668,
            "skew_25d": 2.484,
            "put_call_volume_ratio": 0.85,
            "put_call_oi_ratio": 0.90
          }
        },
        {
          "tenor": "M24",
          "settlement_price": 71.2400,
          "spread_to_prompt": -19.1600,
          "annualized_roll_yield_pct": 10.60,
          "volume": 18500,
          "is_preliminary": false,
          "options": {
            "atm_implied_volatility": 28.847,
            "skew_25d": 0.704,
            "put_call_volume_ratio": 0.85,
            "put_call_oi_ratio": 0.90
          }
        }
      ]
    }
    ```

---

## 4. Physical Processing Spreads

Retrieve real-time processing margins including 3:2:1 crack spreads, soybean crush margins, and power spark spreads.

* **Endpoint**: `GET /api/quant/spreads/`
* **Query Parameters**:
  - `commodity`: Canonical commodity code (`CL`, `ZS`, `NG`).

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/quant/spreads/?commodity=CL" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/quant/spreads/",
        params={"commodity": "CL"}
    )
    data = response.json()
    print(f"3:2:1 Crack Margin: ${data['spreads']['crack_321']:.2f}/bbl")
    ```

=== "JSON Response (200 OK)"
    ```json
    {
      "commodity": "CL",
      "as_of": "2026-09-24",
      "spreads": {
        "crack_321": 24.50,
        "crush_margin": null,
        "spark_spread": null
      }
    }
    ```

---

## 5. Cross-Commodity & Cointegration Findings

Retrieve curated logical complex groupings, Engle-Granger cointegration statistics, Ornstein-Uhlenbeck mean-reversion half-lives, and macro factor sensitivities.

* **Endpoint**: `GET /api/quant/cross-commodity/`
* **Query Parameters**:
  - `commodity`: Canonical commodity code (`CL`, `ZS`, `GC`).

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/quant/cross-commodity/?commodity=CL" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/quant/cross-commodity/",
        params={"commodity": "CL"}
    )
    xc = response.json()["cross_commodity"]
    print(f"Complex: {xc['logical_complex_name']}")
    print(f"Economic Rationale: {xc['economic_rationale']}")
    for pair in xc["cointegration_findings"]:
        print(f"Pair: {pair['pair']} | Half-Life: {pair['half_life_days']} days | Cointegrated: {pair['is_cointegrated']}")
    ```

=== "JSON Response (200 OK)"
    ```json
    {
      "commodity": "CL",
      "as_of": "2026-09-24",
      "cross_commodity": {
        "primary_complex": "REFINERY_ENERGY_COMPLEX",
        "complex_members": ["CL", "BRENT", "RB", "HO", "LGO"],
        "key_spreads": {
          "prompt_spread": 0.45
        },
        "cointegration_pairs": [
          {
            "pair": "CL-XB",
            "hedge_ratio_beta": 0.84,
            "adf_t_statistic": -3.85,
            "p_value": 0.0024,
            "is_cointegrated": true,
            "half_life_days": 4.2,
            "residual_zscore": -1.45,
            "status": "MEAN_REVERSION_CANDIDATE"
          }
        ],
        "rolling_correlations": {
          "BRENT": 0.88,
          "RB": 0.82
        },
        "macro_factor_sensitivities": {
          "dxy_corr_60d": -0.65,
          "real_rates_corr_60d": -0.25
        }
      }
    }
    ```

---

## 6. Seasonality & Directional Pattern Analytics

Retrieve historical seasonal envelopes, forward tenure directional move win rates (10D, 30D, 60D, 90D), forward 1-month volatility peak expectations, and complete 20-year Day-of-Year normalized trajectories + 2005–2026 monthly return matrices.

* **Endpoint**: `GET /api/quant/seasonality/`
* **Query Parameters**:
  - `commodity`: Canonical commodity code (`CL`, `ZC`, `NG`, `CORN`, `GOLD`). Default: `CL`.

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/quant/seasonality/?commodity=CL" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/quant/seasonality/",
        params={"commodity": "CL"}
    )
    data = response.json()
    sn = data["seasonality"]
    p20 = data.get("profile_20y", {})
    
    # 20-Year Monthly Matrix Summary
    best_m = p20.get("monthly_matrix", {}).get("best_month", {})
    print(f"Best Seasonal Month: {best_m.get('month_name')} with {best_m.get('win_rate')}% Win Rate (avg {best_m.get('avg_return')}%)")
    
    # Forward Calendar Tenures
    for pat in p20.get("tenure_patterns", []):
        print(f"{pat['label']}: {pat['win_rate']}% Win Rate (median {pat['median_return']}%)")
    ```

=== "JSON Response (200 OK)"
    ```json
    {
      "commodity": "CL",
      "as_of": "2026-09-30T12:00:00Z",
      "seasonality": {
        "day_of_year": 273,
        "current_seasonal_z_score": 0.45,
        "percentiles_5y": {
          "min": 68.2,
          "p25": 72.4,
          "median": 75.1,
          "p75": 78.9,
          "max": 84.5
        },
        "directional_tendency": {
          "tenure_window": "FORWARD_30D",
          "win_rate": 0.80,
          "median_return": 0.038,
          "mean_return": 0.042,
          "t_statistic": 2.65,
          "pattern_classification": "STRONG_BULLISH_SEASONAL_WINDOW"
        },
        "forward_volatility_expectation": {
          "forward_expected_vol_30d": 26.5,
          "percentile_vs_annual": 78.0,
          "is_peak_volatility_window": true,
          "seasonal_catalyst": "Fall Refinery Turnaround Window"
        }
      },
      "profile_20y": {
        "doy_points": [
          {"doy": 1, "label": "Jan 01", "med20": 100.0, "med10": 100.0, "med5": 100.0, "p25": 97.5, "p75": 102.5, "curr": 100.0}
        ],
        "monthly_matrix": {
          "years": [2006, 2007, 2025, 2026],
          "best_month": {"month_num": 2, "month_name": "Feb", "win_rate": 80.0, "avg_return": 4.27},
          "worst_month": {"month_num": 11, "month_name": "Nov", "win_rate": 35.0, "avg_return": -2.89}
        },
        "tenure_patterns": [
          {"tenure_window": "FORWARD_10D", "label": "Next 10 Trading Days (2 Weeks)", "win_rate": 65.0, "median_return": 1.25, "t_statistic": 1.45},
          {"tenure_window": "FORWARD_30D", "label": "Next 30 Calendar Days (1 Month)", "win_rate": 80.0, "median_return": 3.82, "t_statistic": 2.65}
        ],
        "physical_catalyst": "Fall Refinery Turnaround Window (Planned facility maintenance reduces crude runs; inventory accumulates)",
        "volatility_forecast": {
          "forward_expected_vol_30d": 26.5,
          "percentile_vs_annual": 78.0,
          "is_peak_volatility_window": true
        }
      }
    }
    ```


---

## 7. List Discovery Registry

Query the systematic catalog of statistically validated anomalies, cointegration breaks, and regime shifts.

* **Endpoint**: `GET /api/quant/discoveries/`
* **Query Parameters**:
  - `commodity`: Filter by canonical commodity code (e.g. `CL`).
  - `type`: Filter by discovery type (`COINTEGRATION_BREAK`, `SEASONAL_ANOMALY`, `OI_DIVERGENCE`, `SPREAD_EXTREME`, `CURVE_INVERSION`).
  - `active`: Filter by active status (`true` or `false`).

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/quant/discoveries/?commodity=CL&active=true" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/quant/discoveries/",
        params={"commodity": "CL", "active": "true"}
    )
    discoveries = response.json()
    for d in discoveries:
        print(f"[{d['discovery_type']}] {d['summary']} (Z: {d['metrics'].get('residual_zscore')})")
    ```

=== "JSON Response (200 OK)"
    ```json
    [
      {
        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "commodity_code": "CL",
        "commodity_name": "Light Sweet Crude Oil (WTI)",
        "related_commodity_code": "XB",
        "discovery_type": "COINTEGRATION_BREAK",
        "severity": "HIGH",
        "summary": "Spread divergence: CL-XB residual Z-score at -1.45 indicates prompt gasoline outperforming crude beyond 1 standard deviation.",
        "metrics": {
          "residual_zscore": -1.45,
          "half_life_days": 4.2,
          "p_value": 0.0024
        },
        "is_active": true,
        "discovered_at": "2026-09-24T18:00:00Z"
      }
    ]
    ```

---

## 8. 40-Method Institutional Seasonality Matrix

Retrieve the complete 40-method institutional seasonality taxonomy and live quantitative evaluations across 14 analytical lenses for a target commodity.

* **Endpoint**: `GET /api/quant/seasonality/methods/`
* **Query Parameters**:
  - `commodity`: Canonical commodity code (e.g. `CL`, `BRENT`, `NG`, `ZC`, `ZS`). Default: `CL`.

=== "cURL"
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/quant/seasonality/methods/?commodity=CL" \
         -H "Accept: application/json"
    ```

=== "Python (requests)"
    ```python
    import requests

    response = requests.get(
        "http://127.0.0.1:8000/api/quant/seasonality/methods/",
        params={"commodity": "CL"}
    )
    data = response.json()
    print(f"Total Evaluated Methods: {data['total_methods']} across {len(data['sections'])} lenses")
    for method in data["methods"][:5]:
        print(f"#{method['number']} [{method['section']}] {method['name']}: {method['headline_metric']} ({method['status']})")
    ```

=== "JSON Response (200 OK)"
    ```json
    {
      "commodity": "CL",
      "as_of": "2026-09-24",
      "total_methods": 40,
      "sections": [
        {"section": "Calendar", "count": 3, "icon": "📅"},
        {"section": "Price/Return", "count": 3, "icon": "📈"},
        {"section": "Volatility", "count": 2, "icon": "⚡"},
        {"section": "Intraday", "count": 2, "icon": "⏱️"},
        {"section": "Volume/Liquidity", "count": 2, "icon": "💧"},
        {"section": "Futures Curve", "count": 3, "icon": "🔄"},
        {"section": "Fundamentals", "count": 4, "icon": "🏭"},
        {"section": "Events", "count": 2, "icon": "📢"},
        {"section": "Statistical", "count": 4, "icon": "📐"},
        {"section": "Dynamic", "count": 2, "icon": "🔁"},
        {"section": "Regime", "count": 3, "icon": "🎛️"},
        {"section": "Cross-market", "count": 2, "icon": "🔀"},
        {"section": "Trading", "count": 4, "icon": "🎯"},
        {"section": "Visualization", "count": 4, "icon": "📊"}
      ],
      "methods": [
        {
          "id": "method_01",
          "number": 1,
          "section": "Calendar",
          "icon": "📅",
          "name": "Month-of-year seasonality",
          "why_it_matters": "Captures annual seasonal cycles across the 12 calendar months.",
          "formula_summary": "R_m = (P_last(m) - P_first(m)) / P_first(m) across historical years 2005–2026.",
          "metric_type": "CALENDAR_TABLE",
          "headline_metric": "Best: Oct (+5.9% | 90% WR)",
          "headline_label": "Current Month: 65% Win Rate (+1.8% avg return)",
          "status": "ACTIVE / HIGH CONVICTION",
          "parameters": {
            "best_month": {"month_name": "Oct", "win_rate": 90, "avg_return": 5.9}
          }
        },
        {
          "id": "method_02",
          "number": 2,
          "section": "Calendar",
          "icon": "📆",
          "name": "Day-of-week seasonality",
          "why_it_matters": "Captures weekly effects, weekend inventory risk adjustments, and Monday/Friday positioning.",
          "formula_summary": "R_dow = mean(ln(P_t / P_t-1)) for DOW in [Mon, Tue, Wed, Thu, Fri].",
          "metric_type": "DOW_PROFILE",
          "headline_metric": "Top: Wednesday (68.4% WR, +0.42%)",
          "headline_label": "Toughest session: Monday (41.2% WR, -0.28%). Weekly inventory positioning bias.",
          "status": "VALIDATED",
          "parameters": {
            "dow_stats": [
              {"dow_idx": 0, "name": "Mon", "win_rate": 41.2, "avg_return": -0.28},
              {"dow_idx": 2, "name": "Wed", "win_rate": 68.4, "avg_return": 0.42}
            ]
          }
        }
      ],
      "analytical_payloads": {
        "stability_score": 0.84,
        "range_ratio": 1.18,
        "autocorrelations": {
          "lag_5": 0.082,
          "lag_21": 0.145,
          "lag_252": 0.228
        },
        "backtest": {
          "win_rate": 78.9,
          "profit_factor": 2.34,
          "expectancy_pct": 4.12,
          "max_drawdown_pct": -6.45
        }
      }
    }
    ```

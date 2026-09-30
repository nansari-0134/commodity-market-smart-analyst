"""
Advanced Seasonality & Temporal Pattern Recognition Core.

Pure Python + NumPy implementation (Zero Pandas/DLL dependencies).
Implements:
1. 5-Year and 10-Year normalized Day-of-Year (DOY) percentile envelopes.
2. Tenure-specific directional seasonal patterns (10D, 30D, 63D forward win-rates & t-stats).
3. Forward 1-Month Volatility Peak Engine (identifying maximum volatility calendar windows).
4. Physical commodity structural calendar cycles (Planting, Harvest, Driving, Heating).
"""
from collections import defaultdict
from datetime import date
import numpy as np


# -----------------------------------------------------------------------------
# Commodity Structural Lifecycle Calendar Regimes
# -----------------------------------------------------------------------------
COMMODITY_CALENDAR_CYCLES = {
    "GRAINS": {
        "commodities": ["ZC", "ZW", "KW", "ZS", "ZM", "ZL"],
        "regimes": [
            {"start_doy": 135, "end_doy": 215, "name": "Planting & Summer Weather Risk Market", "catalyst": "Midwest temperature/precipitation anomalies"},
            {"start_doy": 255, "end_doy": 320, "name": "Harvest Supply Pressure Window", "catalyst": "Massive seasonal physical grain arrivals at elevators/ports"},
            {"start_doy": 335, "end_doy": 60, "name": "South American Crop Progress", "catalyst": "Brazilian/Argentine soybean/corn weather monitoring"},
        ],
    },
    "ENERGY_PETROLEUM": {
        "commodities": ["CL", "BRENT", "RB", "HO", "LGO"],
        "regimes": [
            {"start_doy": 45, "end_doy": 125, "name": "Spring Driving Season Build", "catalyst": "Refineries transition to summer-grade gasoline, crack spreads surge"},
            {"start_doy": 255, "end_doy": 305, "name": "Fall Refinery Turnaround Window", "catalyst": "Planned facility maintenance reduces crude runs; inventory accumulates"},
            {"start_doy": 335, "end_doy": 50, "name": "Peak Winter Distillate Heating Demand", "catalyst": "Northeast US & European cold snaps deplete diesel/heating oil stocks"},
        ],
    },
    "NATURAL_GAS": {
        "commodities": ["NG"],
        "regimes": [
            {"start_doy": 305, "end_doy": 80, "name": "Winter Peak Storage Depletion", "catalyst": "Massive weekly storage draws; high freeze-off volatility risk"},
            {"start_doy": 170, "end_doy": 240, "name": "Summer Power Generation Cooling Burn", "catalyst": "Air-conditioning power burn drives strong gas-to-power generation"},
            {"start_doy": 241, "end_doy": 304, "name": "Fall Injection Shoulder Season", "catalyst": "Weak seasonal demand; max storage fill capacity tests"},
        ],
    },
}


def compute_seasonal_envelopes(
    dates: list[date],
    prices: np.ndarray,
    current_date: date,
    lookback_years: int = 5,
) -> dict:
    """
    Compute 5-Year / 10-Year historical Day-of-Year (DOY) envelopes and current z-score.
    
    Returns:
        Dictionary with day_of_year, percentiles_5y (min, p25, median, p75, max), and current_seasonal_z_score.
    """
    current_doy = current_date.timetuple().tm_yday
    current_price = float(prices[-1]) if len(prices) > 0 else 0.0
    
    if len(dates) != len(prices) or len(prices) < 252:
        return {
            "day_of_year": current_doy,
            "current_seasonal_z_score": 0.0,
            "percentiles_5y": {"min": current_price, "p25": current_price, "median": current_price, "p75": current_price, "max": current_price},
        }
        
    cutoff_year = current_date.year - lookback_years
    
    # Collect historical prices within +/- 7 calendar days of current DOY
    window_prices = [
        float(p) for d, p in zip(dates, prices)
        if d.year >= cutoff_year and abs(d.timetuple().tm_yday - current_doy) <= 7 and p > 0
    ]
    
    if len(window_prices) >= 5:
        p_arr = np.array(window_prices)
        p_min = float(np.min(p_arr))
        p_25 = float(np.percentile(p_arr, 25))
        p_med = float(np.median(p_arr))
        p_75 = float(np.percentile(p_arr, 75))
        p_max = float(np.max(p_arr))
        p_std = float(np.std(p_arr, ddof=1))
        z_score = float((current_price - p_med) / p_std) if p_std > 0 else 0.0
    else:
        p_min = p_25 = p_med = p_75 = p_max = current_price
        z_score = 0.0
        
    return {
        "day_of_year": current_doy,
        "current_seasonal_z_score": round(z_score, 2),
        "percentiles_5y": {
            "min": round(p_min, 2),
            "p25": round(p_25, 2),
            "median": round(p_med, 2),
            "p75": round(p_75, 2),
            "max": round(p_max, 2),
        },
    }


def find_directional_tenure_patterns(
    dates: list[date],
    prices: np.ndarray,
    current_date: date,
    forward_days: int = 30,
) -> dict:
    """
    Evaluate forward calendar window performance across historical years:
    - Calculates Win Rate (% positive forward return)
    - Median return
    - t-statistic of the seasonal directional tendency
    """
    if len(dates) != len(prices) or len(prices) < 252:
        return {
            "tenure_window": f"FORWARD_{forward_days}D",
            "win_rate": 0.50,
            "median_return": 0.0,
            "mean_return": 0.0,
            "t_statistic": 0.0,
            "pattern_classification": "INSUFFICIENT_HISTORY",
        }
        
    current_doy = current_date.timetuple().tm_yday
    
    # Group observations by calendar year: dict[year, list of (doy, price)]
    by_year: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for d, p in zip(dates, prices):
        if d.year != current_date.year and p > 0:
            by_year[d.year].append((d.timetuple().tm_yday, float(p)))
            
    historical_returns = []
    target_doy = current_doy + forward_days
    
    for yr, pairs in by_year.items():
        if not pairs:
            continue
        # Sort by DOY
        pairs.sort(key=lambda x: x[0])
        
        # Closest start pair to current_doy
        start_pair = min(pairs, key=lambda x: abs(x[0] - current_doy))
        
        # End candidates must occur after start_pair
        end_candidates = [x for x in pairs if x[0] > start_pair[0]]
        if end_candidates:
            end_pair = min(end_candidates, key=lambda x: abs(x[0] - target_doy))
            if start_pair[1] > 0:
                ret = (end_pair[1] - start_pair[1]) / start_pair[1]
                historical_returns.append(ret)
                
    if len(historical_returns) >= 3:
        arr_ret = np.array(historical_returns)
        win_rate = float(np.mean(arr_ret > 0))
        med_ret = float(np.median(arr_ret))
        mean_ret = float(np.mean(arr_ret))
        std_ret = float(np.std(arr_ret, ddof=1)) if len(arr_ret) > 1 else 0.0
        t_stat = float(mean_ret / (std_ret / np.sqrt(len(arr_ret)))) if std_ret > 0 else 0.0
        
        if win_rate >= 0.75 and t_stat >= 1.96:
            classification = "STRONG_BULLISH_SEASONAL_WINDOW"
        elif win_rate <= 0.25 and t_stat <= -1.96:
            classification = "STRONG_BEARISH_SEASONAL_WINDOW"
        elif win_rate >= 0.65:
            classification = "MODERATE_BULLISH_BIAS"
        elif win_rate <= 0.35:
            classification = "MODERATE_BEARISH_BIAS"
        else:
            classification = "BALANCED_SEASONAL_RANGE"
    else:
        win_rate = 0.50
        med_ret = mean_ret = t_stat = 0.0
        classification = "NEUTRAL"
        
    return {
        "tenure_window": f"FORWARD_{forward_days}D",
        "win_rate": round(win_rate, 2),
        "median_return": round(med_ret, 4),
        "mean_return": round(mean_ret, 4),
        "t_statistic": round(t_stat, 2),
        "pattern_classification": classification,
    }


def compute_forward_volatility_expectation(
    dates: list[date],
    prices: np.ndarray,
    current_date: date,
    commodity_code: str,
) -> dict:
    """
    Compute forward 30-day realized volatility expectation by calendar date.
    Flags whether the upcoming month historically experiences peak volatility regimes.
    """
    current_doy = current_date.timetuple().tm_yday
    
    # Identify associated physical lifecycle catalyst if any
    commodity_upper = commodity_code.upper()
    active_catalyst = ""
    for category, cat_data in COMMODITY_CALENDAR_CYCLES.items():
        if commodity_upper in cat_data["commodities"]:
            for regime in cat_data["regimes"]:
                s = regime["start_doy"]
                e = regime["end_doy"]
                is_active = (s <= current_doy <= e) if s <= e else (current_doy >= s or current_doy <= e)
                if is_active:
                    active_catalyst = f"{regime['name']} ({regime['catalyst']})"
                    break
                    
    if len(dates) != len(prices) or len(prices) < 252:
        return {
            "forward_expected_vol_30d": 25.0,
            "percentile_vs_annual": 50.0,
            "is_peak_volatility_window": False,
            "seasonal_catalyst": active_catalyst or "Normal Seasonality",
        }
        
    # Log returns
    log_ret = np.diff(np.log(prices))
    n = len(log_ret)
    window = 21  # 21 trading days ~ 30 calendar days
    
    forward_vols = []
    doy_vols = []
    
    for i in range(n - window):
        chunk = log_ret[i : i + window]
        vol = float(np.std(chunk, ddof=1) * np.sqrt(252) * 100)
        forward_vols.append(vol)
        doy = dates[i + 1].timetuple().tm_yday
        doy_vols.append((doy, vol))
        
    if not forward_vols:
        return {
            "forward_expected_vol_30d": 25.0,
            "percentile_vs_annual": 50.0,
            "is_peak_volatility_window": False,
            "seasonal_catalyst": active_catalyst or "Normal Seasonality",
        }
        
    all_vols_arr = np.array(forward_vols)
    
    # Filter within +/- 10 days of current DOY
    matching = [v for doy, v in doy_vols if abs(doy - current_doy) <= 10]
    
    if len(matching) >= 5:
        expected_vol = float(np.median(matching))
        pct_rank = float(np.mean(all_vols_arr <= expected_vol) * 100)
    else:
        expected_vol = float(np.median(all_vols_arr))
        pct_rank = 50.0
        
    is_peak = bool(pct_rank >= 80.0)
    
    return {
        "forward_expected_vol_30d": round(expected_vol, 1),
        "percentile_vs_annual": round(pct_rank, 1),
        "is_peak_volatility_window": is_peak,
        "seasonal_catalyst": active_catalyst or ("Peak Volatility Window" if is_peak else "Baseline Seasonal Volatility"),
    }


def compute_comprehensive_seasonality_profile(
    dates: list[date],
    prices: np.ndarray,
    current_date: date,
    commodity_code: str = "",
) -> dict:
    """
    Computes a complete 20-year seasonality intelligence profile for institutional visualization:
    1. Day-of-Year (DOY 1-365) normalized multi-year envelopes (20Y, 10Y, 5Y median, p10, p25, p75, p90)
       and current year's actual realized trajectory (base 100 on Jan 1).
    2. 20-Year Monthly Return Matrix (Jan - Dec, 2005-2026) with win rates, average returns, and historical extremes.
    3. Multi-tenure forward directional windows (10D, 30D, 60D, 90D win rates & t-statistics).
    4. Active physical structural lifecycle calendar catalyst.
    5. Forward 30-day volatility peak expectation.
    """
    current_doy = current_date.timetuple().tm_yday
    curr_yr = current_date.year
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    if len(dates) != len(prices) or len(prices) < 252:
        return {
            "doy_points": [],
            "monthly_matrix": {"years": [], "returns": {}, "summary": []},
            "tenure_patterns": [],
            "physical_catalyst": "Normal Seasonality",
            "volatility_forecast": {
                "forward_expected_vol_30d": 25.0,
                "percentile_vs_annual": 50.0,
                "is_peak_volatility_window": False,
            },
        }

    # Group price observations by year and DOY / month
    by_year_doy: dict[int, dict[int, float]] = defaultdict(dict)
    by_year_month: dict[int, dict[int, dict[str, float]]] = defaultdict(dict)

    for d, p in zip(dates, prices):
        if p > 0:
            doy = d.timetuple().tm_yday
            by_year_doy[d.year][doy] = float(p)
            m = d.month
            if m not in by_year_month[d.year]:
                by_year_month[d.year][m] = {"first": float(p), "last": float(p)}
            else:
                by_year_month[d.year][m]["last"] = float(p)

    # 1. Normalized yearly series (base 100 on first available DOY of each calendar year)
    norm_series: dict[int, dict[int, float]] = {}
    for yr, doys in by_year_doy.items():
        if not doys:
            continue
        min_d = min(doys.keys())
        b_val = doys[min_d]
        if b_val > 0:
            norm_series[yr] = {d: (val / b_val) * 100.0 for d, val in doys.items()}

    hist_years = sorted([y for y in norm_series.keys() if y < curr_yr])

    # Sample DOY points every 5 days across the year (DOY 1 to 365)
    sample_doys = list(range(1, 366, 5))
    if 365 not in sample_doys:
        sample_doys.append(365)

    doy_points = []
    base_ref_date = date(2025, 1, 1)

    for doy in sample_doys:
        # Approximate month and day label
        ref_d = base_ref_date.fromordinal(base_ref_date.toordinal() + doy - 1)
        lbl = ref_d.strftime("%b %d")

        y20_vals = []
        y10_vals = []
        y5_vals = []
        for yr in hist_years:
            matches = [norm_series[yr][d] for d in norm_series[yr] if abs(d - doy) <= 4]
            if matches:
                avg_m = float(np.mean(matches))
                y20_vals.append(avg_m)
                if yr >= curr_yr - 10:
                    y10_vals.append(avg_m)
                if yr >= curr_yr - 5:
                    y5_vals.append(avg_m)

        curr_val = None
        if curr_yr in norm_series:
            c_matches = [norm_series[curr_yr][d] for d in norm_series[curr_yr] if abs(d - doy) <= 4 and d <= current_doy]
            if c_matches:
                curr_val = round(float(np.mean(c_matches)), 2)

        if y20_vals:
            m20 = float(np.median(y20_vals))
            p25 = float(np.percentile(y20_vals, 25))
            p75 = float(np.percentile(y20_vals, 75))
            p10 = float(np.percentile(y20_vals, 10))
            p90 = float(np.percentile(y20_vals, 90))
            m10 = float(np.median(y10_vals)) if y10_vals else m20
            m5 = float(np.median(y5_vals)) if y5_vals else m20
            doy_points.append({
                "doy": doy,
                "label": lbl,
                "med20": round(m20, 2),
                "med10": round(m10, 2),
                "med5": round(m5, 2),
                "p25": round(p25, 2),
                "p75": round(p75, 2),
                "p10": round(p10, 2),
                "p90": round(p90, 2),
                "curr": curr_val,
            })

    # 2. Monthly Returns Matrix (historical years 2005 - present)
    matrix_years = sorted([y for y in by_year_month.keys() if y >= 2005])
    monthly_data: dict[int, dict[int, float]] = {}
    for yr in matrix_years:
        monthly_data[yr] = {}
        for m in range(1, 13):
            if m in by_year_month[yr]:
                f = by_year_month[yr][m]["first"]
                l = by_year_month[yr][m]["last"]
                ret = ((l - f) / f) * 100.0 if f > 0 else 0.0
                monthly_data[yr][m] = round(ret, 2)

    month_stats = []
    for m in range(1, 13):
        m_name = month_names[m - 1]
        rets = [monthly_data[yr][m] for yr in matrix_years if m in monthly_data[yr]]
        if rets:
            pos_cnt = sum(1 for r in rets if r > 0)
            win_r = round((pos_cnt / len(rets)) * 100.0, 1)
            avg_r = round(float(np.mean(rets)), 2)
            med_r = round(float(np.median(rets)), 2)
            std_r = round(float(np.std(rets, ddof=1)), 2) if len(rets) > 1 else 0.0
            best_idx = int(np.argmax(rets))
            worst_idx = int(np.argmin(rets))
            yr_keys = [yr for yr in matrix_years if m in monthly_data[yr]]
            best_yr = {"year": yr_keys[best_idx], "return": rets[best_idx]}
            worst_yr = {"year": yr_keys[worst_idx], "return": rets[worst_idx]}
        else:
            win_r = 50.0
            avg_r = med_r = std_r = 0.0
            pos_cnt = 0
            best_yr = worst_yr = {"year": curr_yr, "return": 0.0}

        month_stats.append({
            "month_num": m,
            "month_name": m_name,
            "win_rate": win_r,
            "avg_return": avg_r,
            "median_return": med_r,
            "std_dev": std_r,
            "positive_years": pos_cnt,
            "total_years": len(rets),
            "best_year": best_yr,
            "worst_year": worst_yr,
        })

    # Identify best and worst overall seasonal months
    best_month_overall = max(month_stats, key=lambda s: s["win_rate"]) if month_stats else None
    worst_month_overall = min(month_stats, key=lambda s: s["win_rate"]) if month_stats else None

    # Pre-formatted matrix rows for HTML/Django template rendering (most recent year first)
    matrix_rows = []
    for yr in reversed(matrix_years):
        m_cells = []
        for m in range(1, 13):
            val = monthly_data.get(yr, {}).get(m)
            if val is not None:
                is_pos = val > 0
                is_neg = val < 0
                val_str = f"+{val:.1f}%" if is_pos else f"{val:.1f}%"
                alpha = min(0.12 + abs(val) / 25.0, 0.45)
                bg_style = (
                    f"background: rgba(16, 185, 129, {alpha:.2f}); color: #34d399;"
                    if is_pos
                    else (
                        f"background: rgba(244, 63, 94, {alpha:.2f}); color: #f87171;"
                        if is_neg
                        else "background: rgba(255,255,255,0.02); color: #64748b;"
                    )
                )
                m_cells.append({
                    "month": m,
                    "val": val,
                    "val_str": val_str,
                    "bg_style": bg_style,
                })
            else:
                m_cells.append({
                    "month": m,
                    "val": None,
                    "val_str": "-",
                    "bg_style": "background: rgba(255,255,255,0.02); color: #64748b;",
                })
        matrix_rows.append({"year": yr, "cells": m_cells})

    # 3. Tenure Patterns across key forward windows
    tenure_windows = [
        (10, "Next 10 Trading Days (2 Weeks)"),
        (30, "Next 30 Calendar Days (1 Month)"),
        (60, "Next 60 Calendar Days (2 Months)"),
        (90, "Next 90 Calendar Days (1 Quarter)"),
    ]
    tenure_patterns = []
    for days, lbl in tenure_windows:
        res = find_directional_tenure_patterns(dates, prices, current_date, forward_days=days)
        tenure_patterns.append({
            "tenure_window": res["tenure_window"],
            "label": lbl,
            "win_rate": round(res["win_rate"] * 100, 1),
            "median_return": round(res["median_return"] * 100, 2),
            "mean_return": round(res["mean_return"] * 100, 2),
            "t_statistic": res["t_statistic"],
            "pattern_classification": res["pattern_classification"],
        })

    # 4. Volatility peak forecast and active physical catalyst
    vol_expectation = compute_forward_volatility_expectation(dates, prices, current_date, commodity_code)

    return {
        "doy_points": doy_points,
        "monthly_matrix": {
            "years": matrix_years,
            "returns": monthly_data,
            "rows": matrix_rows,
            "summary": month_stats,
            "best_month": best_month_overall,
            "worst_month": worst_month_overall,
        },
        "tenure_patterns": tenure_patterns,
        "physical_catalyst": vol_expectation.get("seasonal_catalyst", "Normal Seasonality"),
        "volatility_forecast": vol_expectation,
    }

